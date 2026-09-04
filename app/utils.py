import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, APIKeyHeader

from app.config import jwtSettings, mailSettings
from app.interfaces import StorageInterface, YdbInterface

token_header = APIKeyHeader(name="X-Auth-Token", auto_error=False)


# STORAGE


EMAIL_TRANSLATIONS = {
    "ru": {
        "subject": "Вход в приложение Al-Qari",
        "body": """Здравствуйте!

Для входа в аккаунт нажмите на ссылку ниже:
{magic_link}

Ссылка действительна 15 минут. Если вы не запрашивали вход, просто проигнорируйте это письмо."""
    },
    "en": {
        "subject": "Login to Al-Qari",
        "body": """Hello!

Click the link below to log into your account:
{magic_link}

The link is valid for 15 minutes. If you did not request this login, please ignore this email."""
    }
}


def fetch_from_storage(storage: StorageInterface, file_key: str):
    try:
        return storage.fetch_json(file_key)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# MAGIC LINK


def send_magic_link_email(to_email: str, token: str, lang: str = "en"):
    magic_link = f"{mailSettings.FRONTEND_BASE_URL}/auth/verify?token={token}"
    
    t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["en"])
    
    msg = MIMEMultipart()
    msg["From"] = mailSettings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = t["subject"]
    
    body = t["body"].format(magic_link=magic_link)
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    try:
        with smtplib.SMTP_SSL(mailSettings.SMTP_HOST, mailSettings.SMTP_PORT) as server:
            server.login(mailSettings.SMTP_USER, mailSettings.SMTP_PASSWORD)
            server.sendmail(mailSettings.SMTP_USER, to_email, msg.as_string())
    except smtplib.SMTPException as e:
        print(e)


# JWT


def create_access_token(user_id: str):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, jwtSettings.JWT_SECRET_KEY, algorithm=jwtSettings.ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, jwtSettings.JWT_SECRET_KEY, algorithms=[jwtSettings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# COMMON ROUTES


def ensure_str(v, encoding="utf-8"):
    return v.decode(encoding) if isinstance(v, bytes) else v


async def get_current_user(
    token: str | None = Depends(token_header),
) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    return decode_access_token(token)


async def get_optional_current_user(
    token: str | None = Depends(token_header),
) -> str | None:
    if not token:
        return None
    return decode_access_token(token)
  
  
# PLAYLIST ROUTES
    
def verify_playlist_access(
    db: YdbInterface, 
    playlist_id: str, 
    user_id: str, 
    require_owner: bool = False, 
    require_editor: bool = False
) -> str:
    playlist_query = "DECLARE $id AS Utf8; SELECT owner_id FROM playlists WHERE id = $id;"
    playlist_res = db.execute(playlist_query, {"$id": playlist_id})
    
    if not playlist_res:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    owner_id = ensure_str(playlist_res[0]["owner_id"])
    
    if user_id == owner_id:
        return "owner"
        
    if require_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the playlist owner can perform this action")
        
    member_query = """
    DECLARE $playlist_id AS Utf8;
    DECLARE $user_id AS Utf8;
    SELECT role FROM playlist_members 
    WHERE playlist_id = $playlist_id AND user_id = $user_id;
    """
    member_res = db.execute(member_query, {"$playlist_id": playlist_id, "$user_id": user_id})
    
    if not member_res:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    role = ensure_str(member_res[0]["role"])
    
    if require_editor and role != "editor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners or editors can perform this action")
        
    return role


def map_playlist_response(row: dict) -> dict:
    playlist = {
        "id": ensure_str(row.get("p.id", "")),
        "title": ensure_str(row.get("p.title", "")),
        "data": ensure_str(row.get("p.data", "")),
        "is_public": row.get("p.is_public", False),
        "forked_from_id": ensure_str(row.get("p.forked_from_id", "")),
        "created_at": row.get("p.created_at"),
        "updated_at": row.get("p.updated_at"),
        "owner": {
            "id": ensure_str(row.get("p.owner_id", "")),
            "username": ensure_str(row.get("u.username", "")),
            "avatar_url": ensure_str(row.get("u.avatar_url", ""))
        }
    }
    
    if "p.role" in row:
        playlist["role"] = ensure_str(row["p.role"])
    if "p.added_at" in row:
        playlist["added_at"] = row["p.added_at"]
        
    return playlist
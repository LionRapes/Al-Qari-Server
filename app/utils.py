import jwt
import smtplib
from app.interfaces import StorageInterface
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import mailSettings, jwtSettings
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer(auto_error=False)

def fetch_from_storage(storage: StorageInterface, file_key: str):
    """Internal helper to fetch and parse JSON with proper HTTP error handling."""
    try:
        return storage.fetch_json(file_key)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
def ensure_str(v, encoding="utf-8"):
    return v.decode(encoding) if isinstance(v, bytes) else v


def send_magic_link_email(to_email: str, token: str):
    magic_link = f"{mailSettings.FRONTEND_URL}/auth/verify?token={token}"
    
    msg = MIMEMultipart()
    msg["From"] = mailSettings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = "Вход в приложение Al-Qari"
    
    body = f"""
    Здравствуйте!
    
    Для входа в аккаунт нажмите на ссылку ниже:
    {magic_link}
    
    Ссылка действительна 15 минут. Если вы не запрашивали вход, просто проигнорируйте это письмо.
    """
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    try:
        with smtplib.SMTP_SSL(mailSettings.SMTP_HOST, mailSettings.SMTP_PORT) as server:
            server.login(mailSettings.SMTP_USER, mailSettings.SMTP_PASSWORD)
            server.sendmail(mailSettings.SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        print(e)
        

def create_access_token(user_id: str):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, jwtSettings.JWT_SECRET_KEY, algorithm=jwtSettings.ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, jwtSettings.JWT_SECRET_KEY, algorithms=[jwtSettings.ALGORITHM]
        )
        user_id: Optional[str] = payload.get("sub")

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


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    if not credentials:
        return None
    return decode_access_token(credentials.credentials)
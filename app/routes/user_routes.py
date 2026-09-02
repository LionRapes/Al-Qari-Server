import io
import uuid
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, UploadFile, File
from pydantic import BaseModel, EmailStr
from app.interfaces import YdbInterface, StorageInterface
from app.dependencies import get_ydb, get_storage
from app.utils import ensure_str, send_magic_link_email, create_access_token
from app.config import storageSettings

router = APIRouter(prefix="/users", tags=["Users"])

class EmailRequest(BaseModel):
    email: EmailStr

class TokenVerify(BaseModel):
    token: str
    
class UserUpdate(BaseModel):
    username: str

@router.post("/auth/magic-link", summary="Request magic link for email")
async def request_magic_link(req: EmailRequest, background_tasks: BackgroundTasks, db: YdbInterface = Depends(get_ydb)):
    token = str(uuid.uuid4())
    query = """
    DECLARE $token AS Utf8;
    DECLARE $email AS Utf8;
    
    INSERT INTO magic_links (token, email, expires_at) 
    VALUES ($token, $email, CurrentUtcTimestamp() + Interval("PT15M"));
    """
    
    try:
        db.execute(query, {"$token": token, "$email": str(req.email)})
    except Exception as e:
        print(e)
    
    background_tasks.add_task(send_magic_link_email, req.email, token)
    
    return {"message": "Magic link sent"}


@router.post("/auth/verify", summary="Verify magic link and login/register")
async def verify_magic_link(req: TokenVerify, db: YdbInterface = Depends(get_ydb)):
    token = req.token
    
    verify_query = """
    DECLARE $token AS Utf8;
    SELECT email FROM magic_links 
    WHERE token = $token AND expires_at > CurrentUtcTimestamp();
    """
    link_result = db.execute(verify_query, {"$token": token})
    
    if not link_result:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    user_email = ensure_str(link_result[0]["email"])
    
    find_user_query = "DECLARE $email AS Utf8; SELECT id, username FROM users WHERE email = $email;"
    user_result = db.execute(find_user_query, {"$email": user_email})

    if user_result:
        user_id = ensure_str(user_result[0]["id"])
        is_new = False
    else:
        user_id = str(uuid.uuid4())
        default_username = f"user_{user_id[:8]}"
        
        create_user_query = """
        DECLARE $id AS Utf8; DECLARE $email AS Utf8; DECLARE $username AS Utf8;
        INSERT INTO users (id, email, username, created_at) 
        VALUES ($id, $email, $username, CurrentUtcTimestamp());
        """
        db.execute(create_user_query, {
            "$id": user_id,
            "$email": user_email,
            "$username": default_username
        })
        is_new = True

    delete_token_query = "DECLARE $token AS Utf8; DELETE FROM magic_links WHERE token = $token;"
    db.execute(delete_token_query, {"$token": token})

    access_token = create_access_token(user_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id, 
        "is_new": is_new
    }

@router.get("/{user_id}", summary="Get user profile")
async def get_user(user_id: str, db: YdbInterface = Depends(get_ydb)):
    query = """
    DECLARE $id AS Utf8;
    SELECT id, email, username, created_at, avatar_url FROM users WHERE id = $id;
    """
    result = db.execute(query, {"$id": user_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = result[0]
    return {
        "id": user["id"],
        "email": ensure_str(user["email"]),
        "username": ensure_str(user["username"]),
        "avatar_url": ensure_str(user.get("avatar_url", "")),
        "created_at": user["created_at"]
    }

@router.patch("/{user_id}", summary="Update user profile")
async def update_user(user_id: str, data: UserUpdate, db: YdbInterface = Depends(get_ydb)):
    check_query = "DECLARE $username AS Utf8; SELECT id FROM users WHERE username = $username;"
    existing = db.execute(check_query, {"$username": data.username})
    
    if existing and ensure_str(existing[0]["id"]) != user_id:
        raise HTTPException(status_code=400, detail="Username already taken")

    update_query = """
    DECLARE $id AS Utf8;
    DECLARE $username AS Utf8;
    UPDATE users SET username = $username WHERE id = $id;
    """
    db.execute(update_query, {
        "$id": user_id,
        "$username": data.username
    })
    
    return {"message": "Profile updated successfully"}


@router.post("/{user_id}/avatar", summary="Upload user avatar")
async def upload_avatar(
    user_id: str,
    file: UploadFile = File(...),
    db: YdbInterface = Depends(get_ydb),
    storage: StorageInterface = Depends(get_storage)
):
    file_content = await file.read()

    try:
        img = Image.open(io.BytesIO(file_content))

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail((400, 400))

        output = io.BytesIO()
        img.save(output, format="WEBP", quality=85)
        optimized_content = output.getvalue()

        file_path = f"users/avatars/{user_id}.webp"
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file format")

    await storage.upload(file_path, optimized_content, content_type="image/webp")

    public_url = f"{storageSettings.S3_ENDPOINT}/{storageSettings.BUCKET_NAME}/{file_path}"

    update_query = """
    DECLARE $id AS Utf8;
    DECLARE $avatar_url AS Utf8;
    UPDATE users SET avatar_url = $avatar_url WHERE id = $id;
    """
    db.execute(update_query, {"$id": user_id, "$avatar_url": public_url})

    return {"message": "Avatar updated", "avatar_url": public_url}


@router.delete("/{user_id}", summary="Delete user profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: YdbInterface = Depends(get_ydb)):
    query = "DECLARE $id AS Utf8; DELETE FROM users WHERE id = $id;"
    db.execute(query, {"$id": user_id})
    return None
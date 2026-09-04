import io
import uuid
from datetime import datetime, timezone

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import BackgroundTasks, HTTPException, status
from PIL import Image

from app.config import storageSettings
from app.interfaces import StorageInterface
from app.repositories.user_repository import UserRepository
from app.utils import create_access_token, ensure_str, send_magic_link_email


class UserService:
    def __init__(self, repo: UserRepository, storage: StorageInterface):
        self.repo = repo
        self.storage = storage

    def request_magic_link(self, email: str, lang: str) -> dict:
        token = str(uuid.uuid4())
        self.repo.create_magic_link(token, email)
        send_magic_link_email(email, token, lang)
        return {"message": "Magic link sent"}

    def verify_magic_link(self, token: str) -> dict:
        link_result = self.repo.get_magic_link(token)
        
        if not link_result:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
            
        user_email = ensure_str(link_result["email"])
        user_result = self.repo.get_user_by_email(user_email)

        if user_result:
            user_id = ensure_str(user_result["id"])
            is_new = False
        else:
            user_id = str(uuid.uuid4())
            default_username = f"user_{user_id[:8]}"
            self.repo.create_user(user_id, user_email, default_username)
            is_new = True

        self.repo.delete_magic_link(token)
        access_token = create_access_token(user_id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id, 
            "is_new": is_new
        }

    def get_user_profile(self, user_id: str) -> dict:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {
            "id": user["id"],
            "email": ensure_str(user["email"]),
            "username": ensure_str(user["username"]),
            "avatar_url": ensure_str(user.get("avatar_url", "")),
            "created_at": user["created_at"]
        }

    def update_user_profile(self, user_id: str, current_user_id: str, username: str) -> dict:
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only update your own profile"
            )

        existing = self.repo.get_user_by_username(username)
        if existing and ensure_str(existing["id"]) != user_id:
            raise HTTPException(status_code=400, detail="Username already taken")

        self.repo.update_username(user_id, username.strip()[:24])
        return {"message": "Profile updated successfully"}

    async def upload_user_avatar(self, user_id: str, current_user_id: str, file_content: bytes) -> dict:
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own avatar"
            )

        try:
            img = Image.open(io.BytesIO(file_content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail((400, 400))
            output = io.BytesIO()
            img.save(output, format="WEBP", quality=85)
            optimized_content = output.getvalue()

            file_path = f"users/avatars/{user_id}_{int(datetime.now(timezone.utc).timestamp())}.webp"
        except (BotoCoreError, ClientError):
            raise HTTPException(status_code=400, detail="Invalid image file format")

        await self.storage.upload(file_path, optimized_content, content_type="image/webp")
        public_url = f"{storageSettings.S3_ENDPOINT}/{storageSettings.BUCKET_NAME}/{file_path}"
        
        self.repo.update_avatar(user_id, public_url)

        return {"message": "Avatar updated", "avatar_url": public_url}

    def delete_user_profile(self, user_id: str, current_user_id: str) -> None:
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own account"
            )

        self.repo.delete_user(user_id)
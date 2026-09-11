"""User management service implementation for authentication, profiles, and avatars."""

import io
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.config import STORAGE_SETTINGS
from app.core.interfaces import StorageInterface
from app.core.security import create_access_token
from app.core.utils import is_uuid, validate_optional
from app.models.user import MagicLink, User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import *
from app.services.email_service import EmailService


class UserService:
    """Service layer for handling user registration, authentication via magic links, profile updates, and avatars."""

    def __init__(self, repo: UserRepository, storage: StorageInterface):
        """Initialize user service with repository and cloud storage dependencies."""
        self.repo = repo
        self.storage = storage

    def request_magic_link(self, email: str, lang: str) -> None:
        """Request a magic link token for email-based authentication."""
        token = str(uuid.uuid4())
        self.repo.create_magic_link(token, email)
        EmailService.send_magic_link_email(email, token, lang)

    def verify_magic_link(self, token: str) -> TokenVerifyResponse:
        """Verify a magic link token, authenticate or register the user, and issue a JWT access token."""
        magic_link = validate_optional(MagicLink, self.repo.get_magic_link(token))

        if not magic_link:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        user = validate_optional(User, self.repo.get_user_by_email(magic_link.email))

        if user:
            user_id = user.id
            is_new = False
        else:
            user_id = str(uuid.uuid4())
            self.repo.create_user(user_id, magic_link.email, f"user_{user_id[:8]}")
            is_new = True

        self.repo.delete_magic_link(token)
        access_token = create_access_token(user_id)

        return TokenVerifyResponse(
            access_token=access_token,
            token_type="X-Auth-Token",
            user_id=user_id,
            is_new=is_new,
        )

    def get_user_profile(self, current_user_id, user_id: str) -> UserResponse:
        """Retrieve user profile information by user ID."""
        user = validate_optional(User,
            self.repo.get_user_by_id(user_id) if is_uuid(user_id) else self.repo.get_user_by_username(user_id)
        )

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        data = user.model_dump()
        
        if current_user_id != user_id:
                data.pop("email", None)

        return UserResponse.model_validate(data)

    def update_user_profile(self, current_user_id: str, username: str) -> None:
        """Update a user's profile username after verifying ownership and uniqueness."""
        user = validate_optional(User, self.repo.get_user_by_username(username))
        
        if user and user.id != current_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

        self.repo.update_username(current_user_id, username.strip()[:24])

    async def upload_user_avatar(self, current_user_id: str, file_content: bytes) -> AvatarUploadResponse:
        """Process, optimize, and upload a user's avatar image to object storage."""
        now = int(datetime.now(timezone.utc).timestamp())
        
        try:
            img = Image.open(io.BytesIO(file_content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail((400, 400))
            output = io.BytesIO()
            img.save(output, format="WEBP", quality=85)
            optimized_content = output.getvalue()

            file_path = f"users/avatars/{current_user_id}_{now}.webp"
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file format") from exc

        await self.storage.upload(file_path, optimized_content, content_type="image/webp")
        public_url = f"{STORAGE_SETTINGS.s3_endpoint}/{STORAGE_SETTINGS.bucket_name}/{file_path}"

        self.repo.update_avatar(current_user_id, public_url)

        return AvatarUploadResponse(avatar_url=public_url)

    def delete_user_profile(self, current_user_id: str) -> None:
        """Delete a user account and profile after verifying ownership."""
        self.repo.delete_user(current_user_id)

    def ban_user(self, current_moderator: User, target_user_id: str, reason: str | None = None) -> None:
        """Block a user account. After this he will not be able to write forum messages."""
        ban_reason = reason or "User banned by moderator"
        self.repo.set_ban_status(target_user_id, True, current_moderator.id, ban_reason, "ban")

    def unban_user(self, current_moderator: User, target_user_id: str) -> None:
        """Unblock a user account."""
        self.repo.set_ban_status(target_user_id, False, current_moderator.id, "Unbanned by moderator", "unban")

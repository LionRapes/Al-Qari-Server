"""Schemas for managing user authentication and profile updates."""

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole

# REQUEST BODY


class EmailRequest(BaseModel):
    """
    Schema for requesting a magic link via email.

    Attributes:
        email: User's email address for receiving the magic link.
        lang: Language code used for localized email templates.
    """

    email: EmailStr
    lang: str


class UserUpdateRequest(BaseModel):
    """
    Schema for updating a user's profile details.

    Attributes:
        username: New username to assign to the user.
    """

    username: str
    

# RESPONSES


class TokenVerifyResponse(BaseModel):
    """Schema returned after a successful magic link verification."""

    access_token: str
    token_type: str
    user_id: str
    is_new: bool


class UserResponse(BaseModel):
    """Schema for public/private user profile viewing."""

    id: str
    email: EmailStr | None = None
    username: str
    created_at: int
    avatar_url: str | None = None
    role: UserRole
    is_banned: bool


class AvatarUploadResponse(BaseModel):
    """Schema for returning the uploaded image URL."""

    avatar_url: str

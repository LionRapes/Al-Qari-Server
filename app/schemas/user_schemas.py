"""Schemas for managing user authentication and profile updates."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

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


class TokenVerifyRequest(BaseModel):
    """
    Schema for verifying an authentication token.

    Attributes:
        token: One-time authentication token issued during login.
    """

    token: str


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
    email: EmailStr
    username: str
    avatar_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AvatarUploadResponse(BaseModel):
    """Schema for returning the uploaded image URL."""

    avatar_url: str

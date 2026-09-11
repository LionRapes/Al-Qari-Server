"""Schemas for managing user entities within the forum platform."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRole(str, Enum):
    """
    Enumeration of permission levels available to users.

    Roles define access rights across the forum:
    - user: regular participant with basic posting privileges.
    - moderator: elevated permissions for content review and moderation.
    - admin: full administrative control over the platform.
    """

    user = "user"
    premium = "premium"
    moderator = "moderator"
    admin = "admin"
    
    @classmethod
    def staff(cls) -> set["UserRole"]:
        return {cls.admin, cls.moderator}


class User(BaseModel):
    """
    Core user schema used throughout the application.

    Attributes:
        id: Unique identifier of the user.
        username: Public display name used across the forum.
        email: Validated email address for login and notifications.
        created_at: Timestamp of account creation.
        avatar_url: Optional URL to the user's profile avatar.
        role: Permission level defined by `UserRole`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: EmailStr
    created_at: int
    avatar_url: str | None = None
    role: UserRole
    is_banned: bool
    
class MagicLink(BaseModel):
    """
    Core magic link schema used throughout the application.

    Attributes:
        token: Unique identifier of the link.
        email: Email linked to the user.
        expires_at: The date by which the link will expire.
    """

    model_config = ConfigDict(from_attributes=True)

    token: str
    email: EmailStr
    expires_at: int

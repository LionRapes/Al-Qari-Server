"""Schemas for managing user entities within the forum platform."""

from datetime import datetime
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
    moderator = "moderator"
    admin = "admin"


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
    created_at: datetime
    avatar_url: str | None = None
    role: UserRole = UserRole.user

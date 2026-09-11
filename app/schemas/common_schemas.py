# COMPONENTS

from pydantic import BaseModel


class Owner(BaseModel):
    """Schema representing lightweight owner information."""

    id: str
    username: str
    avatar_url: str | None = None
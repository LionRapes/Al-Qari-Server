# COMPONENTS

from pydantic import BaseModel


class Owner(BaseModel):
    """Schema representing lightweight owner information."""

    owner_id: str
    username: str
    avatar_url: str
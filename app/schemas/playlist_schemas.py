"""Schemas for managing playlist creation, updates, and share links."""

from pydantic import BaseModel

from app.models.playlist import PlaylistRole
from app.schemas.common_schemas import Owner

# REQUEST BODY


class PlaylistCreateRequest(BaseModel):
    """Schema for creating a new playlist."""

    title: str
    data: str
    is_public: bool = False


class PlaylistUpdateRequest(BaseModel):
    """Schema for updating an existing playlist."""

    title: str | None = None
    data: str | None = None
    is_public: bool | None = None


class ShareLinkCreateRequest(BaseModel):
    """Schema for creating a playlist share link."""

    role: PlaylistRole = PlaylistRole.viewer
    expires_in_hours: int = 24


# RESPONSES


class PlaylistCreateResponse(BaseModel):
    """Schema for returning the result of a playlist creation request."""

    playlist_id: str


class PlaylistResponse(BaseModel):
    """Schema for returning a playlist to the client."""

    id: str
    title: str
    data: str
    is_public: bool
    forked_from_id: str | None = None
    created_at: int
    updated_at: int
    
    owner: Owner | None = None
    role: PlaylistRole | None = None
    added_at: int | None = None


class PaginatedPlaylistResponse(BaseModel):
    """Schema for returning a paginated list of playlists."""

    limit: int
    offset: int | None = None
    query: str | None = None
    playlists: list[PlaylistResponse]


class UserPlaylistsResponse(BaseModel):
    """Schema for lists of playlists tied to a specific user."""

    user_id: str
    playlists: list[PlaylistResponse]


class ShareLinkResponse(BaseModel):
    """Schema for returning a generated playlist share link."""

    share_token: str


class JoinPlaylistResponse(BaseModel):
    """Schema for returning the result of joining a playlist."""

    playlist_id: str
    role: PlaylistRole


class PlaylistMemberResponse(BaseModel):
    """Detailed member view including user profile data."""
    
    playlist_id: str
    role: PlaylistRole
    added_at: str

    user: Owner | None = None


class PlaylistMembersListResponse(BaseModel):
    """Schema for returning a list of members of a playlist."""

    playlist_id: str
    members: list[PlaylistMemberResponse]


class PlaylistRelationResponse(BaseModel):
    """Schema describing a user's relation to a playlist."""

    playlist_id: str
    user_id: str
    role: PlaylistRole
    added_at: str | None = None

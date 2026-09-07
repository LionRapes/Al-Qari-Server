"""Schemas for managing playlist creation, updates, and share links."""

from datetime import datetime

from pydantic import BaseModel

from app.models.playlist import PlaylistRole

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


# COMPONENTS


class MemberDetail(BaseModel):
    """Detailed member view including user profile data."""

    user_id: str
    role: PlaylistRole
    username: str
    avatar_url: str
    added_at: str | None = None


class PlaylistOwner(BaseModel):
    """Schema representing lightweight owner information for a playlist."""

    id: str
    username: str
    avatar_url: str


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
    owner: PlaylistOwner
    created_at: datetime


class PaginatedPlaylistResponse(BaseModel):
    """Schema for returning a paginated list of playlists."""

    limit: int
    offset: int | None = None
    query: str | None = None
    playlists: list


class UserPlaylistsResponse(BaseModel):
    """Schema for lists of playlists tied to a specific user."""

    user_id: str
    playlists: list[PlaylistResponse]


class ShareLinkResponse(BaseModel):
    """Schema for returning a generated playlist share link."""

    share_token: str
    expires_in_hours: int


class JoinPlaylistResponse(BaseModel):
    """Schema for returning the result of joining a playlist."""

    playlist_id: str
    role: PlaylistRole


class PlaylistMembersListResponse(BaseModel):
    """Schema for returning a list of members of a playlist."""

    playlist_id: str
    members: list[MemberDetail]


class PlaylistRelationResponse(BaseModel):
    """Schema describing a user's relation to a playlist."""

    playlist_id: str
    user_id: str
    role: PlaylistRole
    added_at: str | None = None


"""Schemas for representing playlist entities and related membership/share-link
metadata within the application."""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class PlaylistRole(str, Enum):
    """
    Enumeration of permission levels available to users.

    Roles define access rights across the forum:
    - viewer: regular participant that can only read playlists track.
    - editor: special participant that can edit playlists track.
    """

    viewer = "viewer"
    editor = "editor"


class Playlist(BaseModel):
    """
    Core playlist schema.

    Attributes:
        id: Unique identifier of the playlist.
        owner_id: ID of the user who owns the playlist.
        title: Human-readable name of the playlist.
        data: Data of the playlist that contains all info about tracks
        is_public: Visibility flag indicating whether the playlist is public or private
        created_at: Timestamp when the playlist was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    data: str
    is_public: bool
    forked_from_id: str
    created_at: int
    updated_at: int


class PlaylistMember(BaseModel):
    """
    Schema representing a user's membership in a playlist.

    Attributes:
        playlist_id: ID of the playlist the user is part of.
        user_id: ID of the user who joined the playlist.
        joined_at: Timestamp when the user was added.
        role: Access level granted to the user (default: viewer).
    """

    model_config = ConfigDict(from_attributes=True)

    playlist_id: str
    user_id: str
    added_at: int
    role: PlaylistRole = PlaylistRole.viewer


class PlaylistShareLink(BaseModel):
    """
    Schema representing a temporary share link for a playlist.

    Attributes:
        id: Unique identifier of the share link.
        playlist_id: ID of the playlist being shared.
        expires_at: Optional expiration timestamp for the link.
        created_at: Timestamp when the link was generated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    playlist_id: str
    role: PlaylistRole = "viewer"
    expires_at: int | None = None
    created_at: int

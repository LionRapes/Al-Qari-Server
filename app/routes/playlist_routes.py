"""API routes for managing playlists, including creation, sharing, member management, and search."""

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.api.deps import (
    get_current_user,
    get_optional_current_user,
    get_playlist_service,
)
from app.services.playlist_service import PlaylistService

router = APIRouter(prefix="/playlists", tags=["Playlists"])

CURRENT_USER = Depends(get_current_user)
OPTIONAL_CURRENT_USER = Depends(get_optional_current_user)
PLAYLIST_SERVICE = Depends(get_playlist_service)


class PlaylistCreate(BaseModel):
    """Schema for creating a new playlist."""

    title: str
    data: str
    is_public: bool = False


class PlaylistUpdate(BaseModel):
    """Schema for updating an existing playlist."""

    title: str | None = None
    data: str | None = None
    is_public: bool | None = None


class ShareLinkCreate(BaseModel):
    """Schema for creating a playlist share link."""

    role: str
    expires_in_hours: int = 24


@router.post("/", summary="Create a new playlist", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist: PlaylistCreate,
    user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Creates a new playlist for the authenticated user."""
    return service.create_playlist(user_id, playlist)


@router.get("/public", summary="Get paginated list of public playlists")
async def get_public_playlists(
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves a paginated list of public playlists."""
    return service.get_public_playlists(limit, offset)


@router.get("/search", summary="Search public playlists by title")
async def search_public_playlists(
    q: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Searches public playlists by title query."""
    return service.search_public_playlists(q, limit)


@router.get("/{playlist_id}", summary="Get a playlist by ID with owner data")
async def get_playlist(
    playlist_id: str,
    current_user_id: str | None = OPTIONAL_CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves a specific playlist by ID with owner data."""
    return service.get_playlist(playlist_id, current_user_id)


@router.get("/user/{user_id}/shared", summary="Get all playlists shared with a user")
async def get_user_shared_playlists(
    user_id: str,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves all playlists shared with the specified user."""
    return service.get_user_shared_playlists(user_id, current_user_id)


@router.get("/user/{user_id}/owned", summary="Get all playlists owned by a user")
async def get_user_owned_playlists(
    user_id: str,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves all playlists owned by the specified user."""
    return service.get_user_owned_playlists(user_id)


@router.patch("/{playlist_id}", summary="Update a playlist")
async def update_playlist(
    playlist_id: str,
    updates: PlaylistUpdate,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Updates an existing playlist by ID."""
    return service.update_playlist(playlist_id, updates, current_user_id)


@router.delete(
    "/{playlist_id}",
    summary="Delete a playlist",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_playlist(
    playlist_id: str,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Deletes a playlist by ID."""
    service.delete_playlist(playlist_id, current_user_id)


@router.post("/{playlist_id}/fork", summary="Fork a playlist")
async def fork_playlist(
    playlist_id: str,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Forks an existing playlist for the authenticated user."""
    return service.fork_playlist(playlist_id, current_user_id)


@router.post("/{playlist_id}/share", summary="Generate a shareable link")
async def share_playlist(
    playlist_id: str,
    req: ShareLinkCreate,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Generates a shareable link for a playlist."""
    return service.share_playlist(playlist_id, req, current_user_id)


@router.delete("/{playlist_id}/members/{target_user_id}", summary="Remove a member from a playlist")
async def remove_playlist_member(
    playlist_id: str,
    target_user_id: str,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Removes a member from a playlist."""
    return service.remove_playlist_member(playlist_id, target_user_id, current_user_id)


@router.post("/join/{token}", summary="Join a playlist via share token")
async def join_playlist_via_token(token: str, user_id: str = CURRENT_USER, service: PlaylistService = PLAYLIST_SERVICE):
    """Allows a user to join a playlist via a share token."""
    return service.join_playlist_via_token(token, user_id)


@router.get("/{playlist_id}/members", summary="Get all members of a playlist")
async def get_playlist_members(playlist_id: str, service: PlaylistService = PLAYLIST_SERVICE):
    """Retrieves all members of a playlist."""
    return service.get_playlist_members(playlist_id)


@router.get("/{playlist_id}/members/{user_id}", summary="Get user's relation to a playlist")
async def get_playlist_relation(playlist_id: str, user_id: str, service: PlaylistService = PLAYLIST_SERVICE):
    """Retrieves a user's specific relation/membership to a playlist."""
    return service.get_playlist_relation(playlist_id, user_id)

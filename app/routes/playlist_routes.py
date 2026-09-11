"""API routes for managing playlists, including creation, sharing, member management, and search."""

from fastapi import APIRouter, Query, status

from app.api.deps.auth import CURRENT_USER, OPTIONAL_CURRENT_USER
from app.api.deps.services import PLAYLIST_SERVICE
from app.schemas.playlist_schemas import (
    JoinPlaylistResponse,
    PaginatedPlaylistResponse,
    PlaylistCreateRequest,
    PlaylistCreateResponse,
    PlaylistMembersListResponse,
    PlaylistRelationResponse,
    PlaylistResponse,
    PlaylistUpdateRequest,
    ShareLinkCreateRequest,
    ShareLinkResponse,
    UserPlaylistsResponse,
)
from app.services.playlist_service import PlaylistService

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.post(
    "/", summary="Create a new playlist", response_model=PlaylistCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_playlist(
    req: PlaylistCreateRequest,
    user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Creates a new playlist for the authenticated user."""
    return service.create_playlist(user_id, req)


@router.get("/public", summary="Get paginated list of public playlists", response_model=PaginatedPlaylistResponse)
async def get_public_playlists(
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves a paginated list of public playlists."""
    return service.get_public_playlists(limit, offset)


@router.get(
    "/shared", summary="Get all playlists shared with a user", response_model=UserPlaylistsResponse
)
async def get_user_shared_playlists(
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves all playlists shared with the specified user."""
    return service.get_user_shared_playlists(current_user_id)


@router.get("/owned", summary="Get all playlists owned by a user", response_model=UserPlaylistsResponse)
async def get_user_owned_playlists(
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves all playlists owned by the user."""
    return service.get_user_owned_playlists(current_user_id)


@router.get("/search", summary="Search public playlists by title", response_model=PaginatedPlaylistResponse)
async def search_public_playlists(
    q: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Searches public playlists by title query."""
    return service.search_public_playlists(q, limit)


@router.get("/{playlist_id}", summary="Get a playlist by ID with owner data", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: str,
    current_user_id: str | None = OPTIONAL_CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Retrieves a specific playlist by ID with owner data."""
    return service.get_playlist(playlist_id, current_user_id)


@router.patch("/{playlist_id}", summary="Update a playlist", status_code=status.HTTP_204_NO_CONTENT)
async def update_playlist(
    playlist_id: str,
    req: PlaylistUpdateRequest,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Updates an existing playlist by ID."""
    service.update_playlist(playlist_id, req, current_user_id)


@router.delete("/{playlist_id}", summary="Delete a playlist", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: str,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Deletes a playlist by ID."""
    service.delete_playlist(playlist_id, current_user_id)


@router.post("/{playlist_id}/fork", summary="Fork a playlist", response_model=PlaylistCreateResponse)
async def fork_playlist(
    playlist_id: str,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Forks an existing playlist for the authenticated user."""
    return service.fork_playlist(playlist_id, current_user_id)


@router.post("/{playlist_id}/share", summary="Generate a shareable link", response_model=ShareLinkResponse)
async def share_playlist(
    playlist_id: str,
    req: ShareLinkCreateRequest,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Generates a shareable link for a playlist."""
    return service.share_playlist(playlist_id, req, current_user_id)


@router.post("/join/{token}", summary="Join a playlist via share token", response_model=JoinPlaylistResponse)
async def join_playlist_via_token(token: str, user_id: str = CURRENT_USER, service: PlaylistService = PLAYLIST_SERVICE):
    """Allows a user to join a playlist via a share token."""
    return service.join_playlist_via_token(token, user_id)


@router.delete(
    "/{playlist_id}/members/{target_user_id}",
    summary="Remove a member from a playlist",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_playlist_member(
    playlist_id: str,
    target_user_id: str,
    current_user_id: str = CURRENT_USER,
    service: PlaylistService = PLAYLIST_SERVICE,
):
    """Removes a member from a playlist."""
    service.remove_playlist_member(playlist_id, target_user_id, current_user_id)


@router.get(
    "/{playlist_id}/members", summary="Get all members of a playlist", response_model=PlaylistMembersListResponse
)
async def get_playlist_members(playlist_id: str, service: PlaylistService = PLAYLIST_SERVICE):
    """Retrieves all members of a playlist."""
    return service.get_playlist_members(playlist_id)


@router.get(
    "/{playlist_id}/members/{user_id}",
    summary="Get user's relation to a playlist",
    response_model=PlaylistRelationResponse,
)
async def get_playlist_relation(playlist_id: str, user_id: str, service: PlaylistService = PLAYLIST_SERVICE):
    """Retrieves a user's specific relation/membership to a playlist."""
    return service.get_playlist_relation(playlist_id, user_id)

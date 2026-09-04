
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.dependencies import get_playlist_service
from app.services.playlist_service import PlaylistService
from app.utils import get_current_user, get_optional_current_user

router = APIRouter(prefix="/playlists", tags=["Playlists"])


class PlaylistCreate(BaseModel):
    title: str
    data: str
    is_public: bool = False

class PlaylistUpdate(BaseModel):
    title: str | None = None
    data: str | None = None
    is_public: bool | None = None

class ShareLinkCreate(BaseModel):
    role: str
    expires_in_hours: int = 24


@router.post("/", summary="Create a new playlist", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist: PlaylistCreate, 
    user_id: str = Depends(get_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.create_playlist(user_id, playlist)


@router.get("/public", summary="Get paginated list of public playlists")
async def get_public_playlists(
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.get_public_playlists(limit, offset)


@router.get("/{playlist_id}", summary="Get a playlist by ID with owner data")
async def get_playlist(
    playlist_id: str, 
    current_user_id: str | None = Depends(get_optional_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.get_playlist(playlist_id, current_user_id)


@router.get("/user/{user_id}/shared", summary="Get all playlists shared with a user")
async def get_user_shared_playlists(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.get_user_shared_playlists(user_id, current_user_id)


@router.get("/user/{user_id}/owned", summary="Get all playlists owned by a user")
async def get_user_owned_playlists(
    user_id: str,
    current_user_id: str | None = Depends(get_optional_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.get_user_owned_playlists(user_id)


@router.get("/search", summary="Search public playlists by title")
async def search_public_playlists(
    q: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.search_public_playlists(q, limit)


@router.patch("/{playlist_id}", summary="Update a playlist")
async def update_playlist(
    playlist_id: str, 
    updates: PlaylistUpdate, 
    current_user_id: str = Depends(get_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.update_playlist(playlist_id, updates, current_user_id)


@router.delete("/{playlist_id}", summary="Delete a playlist", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: str, 
    current_user_id: str = Depends(get_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    service.delete_playlist(playlist_id, current_user_id)


@router.post("/{playlist_id}/fork", summary="Fork a playlist")
async def fork_playlist(
    playlist_id: str, 
    current_user_id: str = Depends(get_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.fork_playlist(playlist_id, current_user_id)


@router.post("/{playlist_id}/share", summary="Generate a shareable link")
async def share_playlist(
    playlist_id: str, 
    req: ShareLinkCreate, 
    current_user_id: str = Depends(get_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.share_playlist(playlist_id, req, current_user_id)


@router.delete("/{playlist_id}/members/{target_user_id}", summary="Remove a member from a playlist")
async def remove_playlist_member(
    playlist_id: str,
    target_user_id: str,
    current_user_id: str = Depends(get_current_user),
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.remove_playlist_member(playlist_id, target_user_id, current_user_id)


@router.post("/join/{token}", summary="Join a playlist via share token")
async def join_playlist_via_token(
    token: str, 
    user_id: str = Depends(get_current_user), 
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.join_playlist_via_token(token, user_id)


@router.get("/{playlist_id}/members", summary="Get all members of a playlist")
async def get_playlist_members(
    playlist_id: str, 
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.get_playlist_members(playlist_id)


@router.get("/{playlist_id}/members/{user_id}", summary="Get user's relation to a playlist")
async def get_playlist_relation(
    playlist_id: str,
    user_id: str,
    service: PlaylistService = Depends(get_playlist_service)
):
    return service.get_playlist_relation(playlist_id, user_id)
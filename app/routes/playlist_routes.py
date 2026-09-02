import uuid
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/playlists", tags=["Playlists"])

@router.post("/", summary="Create a new playlist")
async def create_playlist(title: str, data: str, is_public: bool = False):
    playlist_id = str(uuid.uuid4())
    return {"playlist_id": playlist_id, "message": "Playlist created"}

@router.post("/{playlist_id}/fork", summary="Fork a playlist")
async def fork_playlist(playlist_id: str):
    new_id = str(uuid.uuid4())
    return {"new_playlist_id": new_id}
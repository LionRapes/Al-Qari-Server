"""Playlist management service implementation."""

import uuid

from fastapi import HTTPException, status

from app.core.interfaces import YdbInterface
from app.core.utils import ensure_str
from app.repositories.playlist_repository import PlaylistRepository


class PlaylistService:
    """Service layer for managing playlists, user access rights, and sharing features."""

    def __init__(self, repo: PlaylistRepository, db: YdbInterface):
        self.repo = repo
        self.db = db

    def create_playlist(self, user_id: str, playlist_data) -> dict:
        """Create a new playlist owned by the specified user."""
        playlist_id = str(uuid.uuid4())
        self.repo.create_playlist(
            playlist_id=playlist_id,
            owner_id=user_id,
            title=playlist_data.title.strip()[:32],
            data=playlist_data.data,
            is_public=playlist_data.is_public,
        )
        return {"playlist_id": playlist_id, "message": "Playlist created"}

    def get_playlist(self, playlist_id: str, current_user_id: str | None) -> dict:
        """Retrieve a playlist by ID, verifying access permissions if private."""
        playlist = self.repo.get_playlist_by_id(playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")

        if not playlist["p.is_public"]:
            if not current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for private playlists",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            verify_playlist_access(self.db, playlist_id, current_user_id)

        return map_playlist_response(playlist)

    def get_public_playlists(self, limit: int, offset: int) -> dict:
        """Fetch a paginated list of public playlists."""
        result = self.repo.get_public_playlists(limit, offset)

        return {
            "limit": limit,
            "offset": offset,
            "playlists": [map_playlist_response(row) for row in result],
        }

    def get_user_shared_playlists(self, user_id: str, current_user_id: str) -> dict:
        """Fetch playlists shared with a specific user."""
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot view another user's shared playlists")

        result = self.repo.get_user_shared_playlists(user_id)
        return {"user_id": user_id, "playlists": [map_playlist_response(row) for row in result]}

    def get_user_owned_playlists(self, user_id: str) -> dict:
        """Fetch playlists owned by a specific user."""
        result = self.repo.get_user_owned_playlists(user_id)
        return {"user_id": user_id, "playlists": [map_playlist_response(row) for row in result]}

    def search_public_playlists(self, q: str, limit: int) -> dict:
        """Search through public playlists using query terms."""
        words = list({word.strip() for word in q.split() if word.strip()})[:10]
        if not words:
            return {"query": q, "limit": limit, "playlists": []}

        result = self.repo.search_public_playlists(words, limit)
        return {
            "query": q,
            "limit": limit,
            "playlists": [map_playlist_response(row) for row in result],
        }

    def update_playlist(self, playlist_id: str, updates, current_user_id: str) -> dict:
        """Update an existing playlist after validating editor permissions."""
        verify_playlist_access(self.db, playlist_id, current_user_id, require_editor=True)

        current = self.repo.get_raw_playlist(playlist_id)
        if not current:
            raise HTTPException(status_code=404, detail="Playlist not found")

        new_title = updates.title if updates.title is not None else ensure_str(current["title"])
        new_data = updates.data if updates.data is not None else ensure_str(current["data"])
        new_is_public = updates.is_public if updates.is_public is not None else current["is_public"]

        self.repo.update_playlist(playlist_id, new_title, new_data, new_is_public)
        return {"message": "Playlist updated successfully"}

    def delete_playlist(self, playlist_id: str, current_user_id: str) -> None:
        """Delete a playlist after verifying owner permissions."""
        verify_playlist_access(self.db, playlist_id, current_user_id, require_owner=True)
        self.repo.delete_playlist(playlist_id)

    def fork_playlist(self, playlist_id: str, current_user_id: str) -> dict:
        """Create a private copy (fork) of an existing playlist."""
        original = self.repo.get_raw_playlist(playlist_id)
        if not original:
            raise HTTPException(status_code=404, detail="Source playlist not found")

        new_id = str(uuid.uuid4())
        self.repo.insert_forked_playlist(
            new_id=new_id,
            owner_id=current_user_id,
            title=f"Copy of {ensure_str(original['title'])}",
            data=ensure_str(original["data"]),
            is_public=False,
            forked_from=playlist_id,
        )
        return {"new_playlist_id": new_id, "message": "Playlist forked"}

    def share_playlist(self, playlist_id: str, req, current_user_id: str) -> dict:
        """Generate a shareable invitation token for a playlist."""
        verify_playlist_access(self.db, playlist_id, current_user_id, require_owner=True)

        token = str(uuid.uuid4())
        self.repo.create_share_link(token, playlist_id, req.role, req.expires_in_hours)
        return {"share_token": token, "expires_in_hours": req.expires_in_hours}

    def remove_playlist_member(self, playlist_id: str, target_user_id: str, current_user_id: str) -> dict:
        """Remove a collaborator member from a playlist."""
        verify_playlist_access(self.db, playlist_id, current_user_id, require_owner=True)
        self.repo.remove_playlist_member(playlist_id, target_user_id)
        return {"message": f"User {target_user_id} successfully removed from the playlist"}

    def join_playlist_via_token(self, token: str, user_id: str) -> dict:
        """Add a user to a playlist using an active share link token."""
        token_data = self.repo.get_active_share_link(token)
        if not token_data:
            raise HTTPException(status_code=400, detail="Invalid or expired invite link")

        playlist_id = ensure_str(token_data["playlist_id"])
        token_role = ensure_str(token_data["role"])

        existing_member = self.repo.get_playlist_member(playlist_id, user_id)
        if existing_member:
            current_role = ensure_str(existing_member["role"])
            if current_role == token_role:
                return {
                    "message": "You are already a member of this playlist with this role",
                    "playlist_id": playlist_id,
                    "role": current_role,
                }
            self.repo.update_member_role(playlist_id, user_id, token_role)
            return {
                "message": f"Your role was updated from {current_role} to {token_role}",
                "playlist_id": playlist_id,
                "role": token_role,
            }

        self.repo.add_playlist_member(playlist_id, user_id, token_role)
        self.repo.delete_share_link(token)

        return {
            "message": "Successfully joined the playlist",
            "playlist_id": playlist_id,
            "role": token_role,
        }

    def get_playlist_members(self, playlist_id: str) -> dict:
        """Retrieve the list of members collaborating on a playlist."""
        result = self.repo.get_playlist_members_list(playlist_id)
        members = [
            {
                "user_id": ensure_str(row["m.user_id"]),
                "role": ensure_str(row["m.role"]),
                "username": ensure_str(row.get("u.username", "")),
                "avatar_url": ensure_str(row.get("u.avatar_url", "")),
                "added_at": row["added_at"],
            }
            for row in result
        ]

        return {"playlist_id": playlist_id, "members": members}

    def get_playlist_relation(self, playlist_id: str, user_id: str) -> dict:
        """Determine a specific user's permission level relative to a playlist."""
        playlist = self.repo.get_raw_playlist(playlist_id)
        if playlist and ensure_str(playlist["owner_id"]) == user_id:
            return {"playlist_id": playlist_id, "user_id": user_id, "role": "owner"}

        member = self.repo.get_playlist_member(playlist_id, user_id)
        if not member:
            raise HTTPException(status_code=404, detail="User has no relation to this playlist")

        return {
            "playlist_id": playlist_id,
            "user_id": user_id,
            "role": ensure_str(member["role"]),
            "added_at": member["added_at"],
        }


def verify_playlist_access(
    db: YdbInterface,
    playlist_id: str,
    user_id: str,
    require_owner: bool = False,
    require_editor: bool = False,
) -> str:
    """Verify if a user has sufficient permissions for a given playlist."""
    playlist_query = "DECLARE $id AS Utf8; SELECT owner_id FROM playlists WHERE id = $id;"
    playlist_res = db.execute(playlist_query, {"$id": playlist_id})

    if not playlist_res:
        raise HTTPException(status_code=404, detail="Playlist not found")

    owner_id = ensure_str(playlist_res[0]["owner_id"])

    if user_id == owner_id:
        return "owner"

    if require_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the playlist owner can perform this action",
        )

    member_query = """
    DECLARE $playlist_id AS Utf8;
    DECLARE $user_id AS Utf8;
    SELECT role FROM playlist_members 
    WHERE playlist_id = $playlist_id AND user_id = $user_id;
    """
    member_res = db.execute(member_query, {"$playlist_id": playlist_id, "$user_id": user_id})

    if not member_res:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    role = ensure_str(member_res[0]["role"])

    if require_editor and role != "editor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners or editors can perform this action",
        )

    return role


def map_playlist_response(row: dict) -> dict:
    """Map raw database rows into a structured dictionary response for playlists."""
    playlist = {
        "id": ensure_str(row.get("p.id", "")),
        "title": ensure_str(row.get("p.title", "")),
        "data": ensure_str(row.get("p.data", "")),
        "is_public": row.get("p.is_public", False),
        "forked_from_id": ensure_str(row.get("p.forked_from_id", "")),
        "created_at": row.get("p.created_at"),
        "updated_at": row.get("p.updated_at"),
        "owner": {
            "id": ensure_str(row.get("p.owner_id", "")),
            "username": ensure_str(row.get("u.username", "")),
            "avatar_url": ensure_str(row.get("u.avatar_url", "")),
        },
    }

    if "p.role" in row:
        playlist["role"] = ensure_str(row["p.role"])
    if "p.added_at" in row:
        playlist["added_at"] = row["p.added_at"]

    return playlist

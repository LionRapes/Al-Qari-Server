"""Playlist management service implementation."""

import uuid

from fastapi import HTTPException, status

from app.core.interfaces import YdbInterface
from app.core.utils import validate_optional
from app.models.playlist import Playlist, PlaylistDetails, PlaylistMember, PlaylistShareLink
from app.repositories.playlist_repository import PlaylistRepository
from app.schemas.playlist_schemas import *


class PlaylistService:
    """Service layer for managing playlists, user access rights, and sharing features."""

    def __init__(self, repo: PlaylistRepository, db: YdbInterface):
        self.repo = repo
        self.db = db

    def create_playlist(self, user_id: str, req: PlaylistCreateRequest) -> PlaylistCreateResponse:
        """Create a new playlist owned by the specified user."""
        playlist_id = str(uuid.uuid4())
        self.repo.create_playlist(
            playlist_id,
            user_id,
            req.title.strip()[:32],
            req.data,
            req.is_public,
        )
        return PlaylistCreateResponse(playlist_id=playlist_id)

    def get_public_playlists(self, limit: int, offset: int) -> PaginatedPlaylistResponse:
        """Fetch a paginated list of public playlists."""
        return PaginatedPlaylistResponse(
            limit=limit,
            offset=offset,
            playlists=[PlaylistResponse.model_validate(row) for row in self.repo.get_public_playlists(limit, offset)],
        )

    def get_user_shared_playlists(self, current_user_id: str) -> UserPlaylistsResponse:
        """Fetch playlists shared with a current user."""
        return UserPlaylistsResponse(
            user_id=current_user_id,
            playlists=[
                PlaylistResponse.model_validate(row) for row in self.repo.get_user_shared_playlists(current_user_id)
            ],
        )

    def get_user_owned_playlists(self, current_user_id: str) -> UserPlaylistsResponse:
        """Fetch playlists owned by a current user."""
        return UserPlaylistsResponse(
            user_id=current_user_id,
            playlists=[
                PlaylistResponse.model_validate(row) for row in self.repo.get_user_owned_playlists(current_user_id)
            ],
        )

    def search_public_playlists(self, q: str, limit: int) -> PaginatedPlaylistResponse:
        """Search through public playlists using query terms."""
        words = list({word.strip() for word in q.split() if word.strip()})[:10]
        if not words:
            return PaginatedPlaylistResponse(
                query=q,
                limit=limit,
                playlists=[],
            )

        return PaginatedPlaylistResponse(
            query=q,
            limit=limit,
            playlists=[PlaylistResponse.model_validate(row) for row in self.repo.search_public_playlists(words, limit)],
        )

    def get_playlist(self, playlist_id: str, current_user_id: str | None) -> PlaylistResponse:
        """Retrieve a playlist by ID, verifying access permissions if private."""
        playlist = validate_optional(PlaylistDetails, self.repo.get_playlist_by_id(playlist_id))

        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

        if not playlist.is_public:
            if not current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for private playlists",
                )
            verify_playlist_access(self.repo, playlist_id, current_user_id)

        return PlaylistResponse.model_validate(playlist.model_dump())

    def update_playlist(self, playlist_id: str, req: PlaylistUpdateRequest, current_user_id: str) -> None:
        """Update an existing playlist after validating editor permissions."""
        verify_playlist_access(self.repo, playlist_id, current_user_id, require_editor=True)

        playlist = validate_optional(Playlist, self.repo.get_raw_playlist(playlist_id))
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

        new_title = req.title if req.title is not None else playlist.title
        new_data = req.data if req.data is not None else playlist.data
        new_is_public = req.is_public if req.is_public is not None else playlist.is_public

        self.repo.update_playlist(playlist_id, new_title, new_data, new_is_public)

    def delete_playlist(self, playlist_id: str, current_user_id: str) -> None:
        """Delete a playlist after verifying owner permissions."""
        verify_playlist_access(self.repo, playlist_id, current_user_id, require_owner=True)
        self.repo.delete_playlist(playlist_id)

    def fork_playlist(self, playlist_id: str, current_user_id: str) -> PlaylistCreateResponse:
        """Create a private copy (fork) of an existing playlist."""
        playlist = validate_optional(Playlist, self.repo.get_raw_playlist(playlist_id))
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source playlist not found")

        new_id = str(uuid.uuid4())
        self.repo.create_playlist(
            new_id,
            current_user_id,
            f"Copy of {playlist.title}",
            playlist.data,
            False,
            playlist_id,
        )
        return PlaylistCreateResponse(playlist_id=new_id)

    def share_playlist(self, playlist_id: str, req: ShareLinkCreateRequest, current_user_id: str) -> ShareLinkResponse:
        """Generate a shareable invitation token for a playlist."""
        verify_playlist_access(self.repo, playlist_id, current_user_id, require_owner=True)

        token = str(uuid.uuid4())
        self.repo.create_share_link(token, playlist_id, req.role, req.expires_in_hours)
        return ShareLinkResponse(share_token=token)

    
    def join_playlist_via_token(self, token: str, user_id: str) -> JoinPlaylistResponse:
        """Add a user to a playlist using an active share link token."""
        share_link = validate_optional(PlaylistShareLink, self.repo.get_active_share_link(token))
        if not share_link:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invite link")

        playlist = validate_optional(Playlist, self.repo.get_raw_playlist(share_link.playlist_id))
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist is undefined")
            
        member = validate_optional(PlaylistMember, self.repo.get_playlist_member(playlist.id, user_id))
        if member:
            if member.role == share_link.role:
                return JoinPlaylistResponse(playlist_id=playlist.id, role=member.role)

            self.repo.update_member_role(playlist.id, user_id, share_link.role)
            return JoinPlaylistResponse(playlist_id=playlist.id, role=share_link.role)

        if playlist.owner_id == user_id:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="You can't join your own playlist")
        
        self.repo.add_playlist_member(playlist.id, user_id, share_link.role)
        self.repo.delete_share_link(token)

        return JoinPlaylistResponse(playlist_id=playlist.id, role=share_link.role)
    

    def remove_playlist_member(self, playlist_id: str, target_user_id: str, current_user_id: str) -> None:
        """Remove a collaborator member from a playlist."""
        verify_playlist_access(self.repo, playlist_id, current_user_id, require_owner=True)
        self.repo.remove_playlist_member(playlist_id, target_user_id)


    def get_playlist_members(self, playlist_id: str) -> PlaylistMembersListResponse:
        """Retrieve the list of members collaborating on a playlist."""
        return PlaylistMembersListResponse(
            playlist_id=playlist_id,
            members=[
                PlaylistMemberResponse.model_validate(row) for row in self.repo.get_playlist_members_list(playlist_id)
            ],
        )
        

    def get_playlist_relation(self, playlist_id: str, user_id: str) -> PlaylistRelationResponse:
        """Determine a specific user's permission level relative to a playlist."""
        playlist = validate_optional(Playlist, self.repo.get_raw_playlist(playlist_id))
        if playlist and playlist.owner_id == user_id:
            return PlaylistRelationResponse(playlist_id=playlist_id, user_id=user_id, role=PlaylistRole.owner)

        member = validate_optional(PlaylistMember, self.repo.get_playlist_member(playlist_id, user_id))
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no relation to this playlist")

        return PlaylistRelationResponse(
            playlist_id=playlist_id, user_id=user_id, role=member.role, added_at=member.added_at
        )


def verify_playlist_access(
    repo: PlaylistRepository,
    playlist_id: str,
    user_id: str,
    require_owner: bool = False,
    require_editor: bool = False,
) -> PlaylistRole:
    """Verify if a user has sufficient permissions for a given playlist."""
    playlist = validate_optional(Playlist, repo.get_raw_playlist(playlist_id))

    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    if user_id == playlist.owner_id:
        return PlaylistRole.owner
    elif require_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the playlist owner can perform this action",
        )

    member = validate_optional(PlaylistMember, repo.get_playlist_member(playlist_id, user_id))

    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if require_editor and member.role != PlaylistRole.editor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners or editors can perform this action",
        )

    return member.role

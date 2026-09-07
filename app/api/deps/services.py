"""
Dependency injection providers for API routes.

This module provides FastAPI dependencies to handle service layer instantiation.
"""

from fastapi import Depends

from app.api.deps.core import STORAGE, YDB
from app.api.deps.repositories import FORUM_REPOSITORY, PLAYLIST_REPOSITORY, USER_REPOSITORY
from app.core.interfaces import StorageInterface, YdbInterface
from app.repositories.forum_repository import ForumRepository
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.user_repository import UserRepository
from app.services.forum_service import ForumService
from app.services.playlist_service import PlaylistService
from app.services.user_service import UserService


def get_user_service(repo: UserRepository = USER_REPOSITORY, storage: StorageInterface = STORAGE) -> UserService:
    """
    Dependency provider for the User Service.

    Args:
        repo (UserRepository): The user repository dependency.
        storage (StorageInterface): The storage interface dependency.

    Returns:
        UserService: An instance of the User service.
    """
    return UserService(repo, storage)


def get_playlist_service(repo: PlaylistRepository = PLAYLIST_REPOSITORY, db: YdbInterface = YDB) -> PlaylistService:
    """
    Dependency provider for the Playlist Service.

    Args:
        repo (UserRepository): The playlist repository dependency.
        db (YdbInterface): The database interface dependency.

    Returns:
        PlaylistService: An instance of the Playlist service.
    """

    return PlaylistService(repo, db)


def get_forum_service(repo: ForumRepository = FORUM_REPOSITORY) -> ForumService:
    """
    Dependency provider for the Forum Service.

    Args:
        repo (ForumRepository): The forum repository dependency.
        db (YdbInterface): The database interface dependency.

    Returns:
        ForumRepository: An instance of the Forum service.
    """

    return ForumService(repo)


USER_SERVICE = Depends(get_user_service)
PLAYLIST_SERVICE = Depends(get_playlist_service)
FORUM_SERVICE = Depends(get_forum_service)


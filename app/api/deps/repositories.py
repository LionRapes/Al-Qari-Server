"""
Dependency injection providers for API routes.

This module provides FastAPI dependencies to handle repository layer instantiation.
"""

from fastapi import Depends

from app.api.deps.core import YDB
from app.core.interfaces import YdbInterface
from app.repositories.forum_repository import ForumRepository
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.user_repository import UserRepository


def get_user_repository(db: YdbInterface = YDB) -> UserRepository:
    """
    Dependency provider for the User Repository.

    Args:
        db (YdbInterface): The database interface dependency.

    Returns:
        UserRepository: An instance of the User repository.
    """
    return UserRepository(db)


def get_playlist_repository(db: YdbInterface = YDB) -> PlaylistRepository:
    """
    Dependency provider for the Playlist Repository.

    Args:
        db (YdbInterface): The database interface dependency.

    Returns:
        PlaylistRepository: An instance of the Playlist repository.
    """
    return PlaylistRepository(db)


def get_forum_repository(db: YdbInterface = YDB) -> ForumRepository:
    """
    Dependency provider for the Forum Repository.

    Args:
        db (YdbInterface): The database interface dependency.

    Returns:
        ForumRepository: An instance of the Forum repository.
    """
    return ForumRepository(db)


USER_REPOSITORY = Depends(get_user_repository)
PLAYLIST_REPOSITORY = Depends(get_playlist_repository)
FORUM_REPOSITORY = Depends(get_forum_repository)
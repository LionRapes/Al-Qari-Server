"""
Dependency injection providers for API routes.

This module provides FastAPI dependencies to handle authentication,
database, and service layer instantiation.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.interfaces import StorageInterface, YdbInterface
from app.core.security import decode_access_token
from app.db.s3 import YandexS3Storage
from app.db.ydb_storage import YandexYdbStorage
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.user_repository import UserRepository
from app.services.playlist_service import PlaylistService
from app.services.user_service import UserService

token_header = APIKeyHeader(name="X-Auth-Token", auto_error=False)
storage_service = YandexS3Storage()
ydb_client = YandexYdbStorage()


async def get_current_user(
    token: str | None = Depends(token_header),
) -> str:
    """
    Dependency to retrieve the current authenticated user ID from the request header.

    Args:
        token (str | None): The authentication token extracted from the request headers.

    Returns:
        str: The user ID associated with the token.

    Raises:
        HTTPException: If the token is missing or invalid (401 Unauthorized).
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return decode_access_token(token)


async def get_optional_current_user(
    token: str | None = Depends(token_header),
) -> str | None:
    """
    Dependency to optionally retrieve the current user ID if present in the header.

    Args:
        token (str | None): The authentication token extracted from the request headers.

    Returns:
        str | None: The user ID if authenticated, or None if unauthenticated.
    """
    if not token:
        return None
    return decode_access_token(token)


def get_storage() -> StorageInterface:
    """
    Dependency provider for the storage interface.

    Returns:
        StorageInterface: An implementation of the storage service (S3).
    """
    return storage_service


def get_ydb() -> YdbInterface:
    """
    Dependency provider for the YDB interface.

    Returns:
        YdbInterface: An implementation of the YDB database client.
    """
    return ydb_client


YDB = Depends(get_ydb)
STORAGE = Depends(get_storage)


def get_user_repository(db: YdbInterface = YDB) -> UserRepository:
    """
    Dependency provider for the User Repository.

    Args:
        db (YdbInterface): The database interface dependency.

    Returns:
        UserRepository: An instance of the User repository.
    """
    return UserRepository(db)


USER_REPOSITORY = Depends(get_user_repository)


def get_user_service(repo: UserRepository = USER_REPOSITORY, storage: StorageInterface = STORAGE) -> UserService:
    """
    Dependency provider for the User Service.

    Args:
        repo (UserRepository): The user repository dependency.
        storage (StorageInterface): The storage service dependency.

    Returns:
        UserService: An instance of the User service.
    """
    return UserService(repo, storage)


def get_playlist_service(db: YdbInterface = YDB) -> PlaylistService:
    """
    Dependency provider for the Playlist Service.

    Args:
        db (YdbInterface): The database interface dependency.

    Returns:
        PlaylistService: An instance of the Playlist service.
    """
    repo = PlaylistRepository(db)
    return PlaylistService(repo, db)

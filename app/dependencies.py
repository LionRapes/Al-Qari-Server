from fastapi import Depends

from app.interfaces import StorageInterface, YdbInterface
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.user_repository import UserRepository
from app.services.playlist_service import PlaylistService
from app.services.user_service import UserService
from app.storage import YandexS3Storage, YandexYdbStorage

_storage_service = YandexS3Storage()
_ydb_client = YandexYdbStorage()


def get_storage() -> StorageInterface:
    return _storage_service


def get_ydb() -> YdbInterface:
    return _ydb_client


def get_user_repository(db: YdbInterface = Depends(get_ydb)) -> UserRepository:
    return UserRepository(db)

def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    storage: StorageInterface = Depends(get_storage)
) -> UserService:
    return UserService(repo, storage)


def get_playlist_service(db: YdbInterface = Depends(get_ydb)) -> PlaylistService:
    repo = PlaylistRepository(db)
    return PlaylistService(repo, db)
from app.interfaces import StorageInterface, YdbInterface
from app.storage import YandexS3Storage, YandexYdbStorage
from fastapi import Request

_storage_service = YandexS3Storage()
_ydb_client = YandexYdbStorage()


def get_storage() -> StorageInterface:
    """FastAPI Dependency that yields the current storage implementation."""
    return _storage_service


def get_ydb() -> YdbInterface:
    return _ydb_client
"""
Dependency injection providers for API routes.

This module provides FastAPI dependencies to handle database.
"""

from fastapi import Depends

from app.core.interfaces import StorageInterface, YdbInterface
from app.db.s3 import YandexS3Storage
from app.db.ydb_storage import YandexYdbStorage

storage_service = YandexS3Storage()
ydb_client = YandexYdbStorage()

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
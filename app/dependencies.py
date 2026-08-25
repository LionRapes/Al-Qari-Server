from app.interfaces import StorageInterface
from app.storage import YandexS3Storage

_storage_service = YandexS3Storage()

def get_storage() -> StorageInterface:
    """FastAPI Dependency that yields the current storage implementation."""
    return _storage_service
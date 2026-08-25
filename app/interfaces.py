from abc import ABC, abstractmethod
from typing import Any

class StorageInterface(ABC):
    """Abstract interface for fetching data from storage."""
    
    @abstractmethod
    def fetch_json(self, file_path: str) -> str:
        pass
    
    @abstractmethod
    async def create_presigned_url(self, key: str, expires_in: int) -> str:
        pass
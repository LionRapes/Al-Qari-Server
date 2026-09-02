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
    
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        pass
    
class YdbInterface(ABC):
    @abstractmethod
    def execute(self, query: str, parameters: Dict[str, Any] = None) -> List[Any]:
        pass
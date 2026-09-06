"""Core interface definitions for database and storage abstractions used across repositories and services."""

from abc import ABC, abstractmethod
from typing import Any


class StorageInterface(ABC):
    """Interface for cloud object storage operations (fetching, presigned URLs, uploading)."""

    @abstractmethod
    def fetch_json(self, file_path: str) -> str:
        """Fetch a JSON file from storage and return its content as a string."""

    @abstractmethod
    async def create_presigned_url(self, key: str, expires_in: int) -> str:
        """Generate a presigned URL for a given storage key with a specific expiration time."""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Upload binary data to storage at the specified key."""


class YdbInterface(ABC):
    """Interface for interacting with YDB database."""

    @abstractmethod
    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> list[Any]:
        """
        Executes a YQL query against the database.

        Args:
            query (str): The YQL query string to execute.
            parameters (dict[str, Any] | None, optional): A dictionary of query parameters.

        Returns:
            list[Any]: A list of rows returned by the query.
        """

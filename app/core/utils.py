"""Utility functions for application logic."""

import uuid
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.interfaces import StorageInterface


def fetch_from_storage(storage: StorageInterface, file_key: str):
    """Fetches and returns JSON content from storage, handling common storage-related errors."""
    try:
        return storage.fetch_json(file_key)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


def ensure_str(v, encoding="utf-8"):
    """Converts a bytes object to a string using the specified encoding, or returns the input as is."""
    return v.decode(encoding) if isinstance(v, bytes) else v


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


T = TypeVar("T", bound=BaseModel)

def validate_optional(model: type[T], data: Any) -> T | None:
    """Validate date for Pydantic or return None, if data is None."""
    return model.model_validate(data) if data is not None else None


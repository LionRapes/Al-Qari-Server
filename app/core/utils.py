"""Utility functions for application logic."""

from fastapi import HTTPException

from app.core.interfaces import StorageInterface


def fetch_from_storage(storage: StorageInterface, file_key: str):
    """Fetches and returns JSON content from storage, handling common storage-related errors."""
    try:
        return storage.fetch_json(file_key)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def ensure_str(v, encoding="utf-8"):
    """Converts a bytes object to a string using the specified encoding, or returns the input as is."""
    return v.decode(encoding) if isinstance(v, bytes) else v

from fastapi import HTTPException
from app.interfaces import StorageInterface

def fetch_from_storage(storage: StorageInterface, file_key: str):
    """Internal helper to fetch and parse JSON with proper HTTP error handling."""
    try:
        return storage.fetch_json(file_key)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
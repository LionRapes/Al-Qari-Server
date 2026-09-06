"""API routes for fetching various application metadata files from storage."""

from fastapi import APIRouter, Depends

from app.api.deps import get_storage
from app.core.interfaces import StorageInterface
from app.core.utils import fetch_from_storage

router = APIRouter(prefix="/metadata", tags=["Metadata"])

STORAGE = Depends(get_storage)


@router.get("/", summary="Get all combined metadata")
async def get_all_metadata(storage: StorageInterface = STORAGE):
    """Retrieves all combined metadata."""
    return fetch_from_storage(storage, "metadata/metadata.json")


@router.get("/reciters")
async def get_reciters(storage: StorageInterface = STORAGE):
    """Retrieves reciters metadata."""
    return fetch_from_storage(storage, "metadata/reciters.json")


@router.get("/riwayah")
async def get_riwayah(storage: StorageInterface = STORAGE):
    """Retrieves riwayah metadata."""
    return fetch_from_storage(storage, "metadata/riwayah.json")


@router.get("/tafsir")
async def get_tafsir(storage: StorageInterface = STORAGE):
    """Retrieves tafsir metadata."""
    return fetch_from_storage(storage, "metadata/tafsir.json")


@router.get("/transcription")
async def get_transcription(storage: StorageInterface = STORAGE):
    """Retrieves transcription metadata."""
    return fetch_from_storage(storage, "metadata/transcription.json")


@router.get("/translation")
async def get_translation(storage: StorageInterface = STORAGE):
    """Retrieves translation metadata."""
    return fetch_from_storage(storage, "metadata/translation.json")


@router.get("/{filename}", summary="Get dynamic metadata file")
async def get_any_metadata(filename: str, storage: StorageInterface = STORAGE):
    """Fallback route: fetches any .json file requested in the metadata folder."""
    if not filename.endswith(".json"):
        filename += ".json"
    return fetch_from_storage(storage, f"metadata/{filename}")

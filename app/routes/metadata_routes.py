from fastapi import APIRouter, Depends, HTTPException
from app.interfaces import StorageInterface
from app.dependencies import get_storage
from app.utils import fetch_from_storage

router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.get("/", summary="Get all combined metadata")
async def get_all_metadata(storage: StorageInterface = Depends(get_storage)):
    return fetch_from_storage(storage, "metadata/metadata.json")


@router.get("/reciters")
async def get_reciters(storage: StorageInterface = Depends(get_storage)):
    return fetch_from_storage(storage, "metadata/reciters.json")


@router.get("/riwayah")
async def get_riwayah(storage: StorageInterface = Depends(get_storage)):
    return fetch_from_storage(storage, "metadata/riwayah.json")


@router.get("/tafsir")
async def get_tafsir(storage: StorageInterface = Depends(get_storage)):
    return fetch_from_storage(storage, "metadata/tafsir.json")


@router.get("/transcription")
async def get_transcription(storage: StorageInterface = Depends(get_storage)):
    return fetch_from_storage(storage, "metadata/transcription.json")


@router.get("/translation")
async def get_translation(storage: StorageInterface = Depends(get_storage)):
    return fetch_from_storage(storage, "metadata/translation.json")


@router.get("/{filename}", summary="Get dynamic metadata file")
async def get_any_metadata(filename: str, storage: StorageInterface = Depends(get_storage)):
    """Fallback route: fetches any .json file requested in the metadata folder."""
    if not filename.endswith(".json"):
        filename += ".json"
    return fetch_from_storage(storage, f"metadata/{filename}")
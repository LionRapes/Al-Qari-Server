"""API routes for fetching Quran content, including riwayah, tafsir, transcription, translation, quotes, and audio files."""

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import get_storage
from app.core.interfaces import StorageInterface
from app.core.utils import fetch_from_storage

router = APIRouter(prefix="/quran", tags=["Quran Content"])

STORAGE = Depends(get_storage)


@router.get("/riwayah/{riwayah_type}", summary="Get riwayah")
async def get_riwayah(
    riwayah_type: str,
    storage: StorageInterface = STORAGE,
):
    """Retrieves riwayah content by type."""
    return fetch_from_storage(storage, f"quran/riwayah/{riwayah_type}.json")


@router.get("/quote/{lang}", summary="Get quotes")
async def get_quotes(
    lang: str,
    storage: StorageInterface = STORAGE,
):
    """Retrieves quotes in the specified language."""
    return fetch_from_storage(storage, f"quran/quote/quotes.{lang}.json")


@router.get("/riwayah/{riwayah_type}/{surah_id}", summary="Get Surah by riwayah")
async def get_surah(
    riwayah_type: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = STORAGE,
):
    """Retrieves a specific Surah by riwayah type and Surah ID."""
    return fetch_from_storage(storage, f"quran/riwayah/{riwayah_type}/{surah_id:03d}.json")


@router.get("/tafsir/{edition}", summary="Get tafsir")
async def get_tafsir(
    edition: str,
    storage: StorageInterface = STORAGE,
):
    """Retrieves tafsir content for a specific edition."""
    return fetch_from_storage(storage, f"quran/tafsir/{edition}.json")


@router.get("/tafsir/{edition}/{surah_id}", summary="Get Surah tafsir")
async def get_surah_tafsir(
    edition: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = STORAGE,
):
    """Retrieves Surah tafsir for a specific edition and Surah ID."""
    return fetch_from_storage(storage, f"quran/tafsir/{edition}/{surah_id:03d}.json")


@router.get(
    "/transcription/{riwayah_type}/{lang}",
    summary="Get transcription by riwayah and lang",
)
async def get_transcription(
    riwayah_type: str,
    lang: str,
    storage: StorageInterface = STORAGE,
):
    """Retrieves transcription content by riwayah type and language."""
    return fetch_from_storage(storage, f"quran/transcription/{riwayah_type}/{lang}.json")


@router.get(
    "/transcription/{riwayah_type}/{lang}/{surah_id}",
    summary="Get Surah transcription by riwayah and lang",
)
async def get_surah_transcription(
    riwayah_type: str,
    lang: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = STORAGE,
):
    """Retrieves Surah transcription by riwayah type, language, and Surah ID."""
    return fetch_from_storage(storage, f"quran/transcription/{riwayah_type}/{lang}/{surah_id:03d}.json")


@router.get("/translation/{lang}", summary="Get translation")
async def get_translation(
    lang: str,
    storage: StorageInterface = STORAGE,
):
    """Retrieves translation content for a specified language."""
    return fetch_from_storage(storage, f"quran/translation/{lang}.json")


@router.get("/translation/{lang}/{surah_id}", summary="Get Surah translation")
async def get_surah_translation(
    lang: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = STORAGE,
):
    """Retrieves Surah translation for a specified language and Surah ID."""
    return fetch_from_storage(storage, f"quran/translation/{lang}/{surah_id:03d}.json")


@router.get(
    "/audio/{riwayah_type}/{reciter_name}_{bitrate}/timestamps",
    summary="Get reciter timestamps by riwayah type, reciter name and bitrate",
)
def get_timestamps(
    riwayah_type: str,
    reciter_name: str,
    bitrate: str,
    storage: StorageInterface = STORAGE,
):
    """Retrieves reciter timestamps by riwayah type, reciter name, and bitrate."""
    return fetch_from_storage(storage, f"quran/audio/{riwayah_type}/{reciter_name}_{bitrate}/timestamps.json")


@router.get(
    "/audio/{riwayah_type}/{reciter_name}_{bitrate}/{surah_id}",
    summary="Get Surah audio by riwayah type, reciter name and bitrate",
)
async def get_surah_audio(
    riwayah_type: str,
    reciter_name: str,
    bitrate: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = STORAGE,
):
    """Retrieves a presigned URL for Surah audio by riwayah type, reciter name, bitrate, and Surah ID."""
    file_path = f"quran/audio/{riwayah_type}/{reciter_name}_{bitrate}/{surah_id:03d}.mp3"

    url = await storage.create_presigned_url(file_path, expires_in=900)
    if url is None:
        raise HTTPException(404, "Audio not found")

    return {"url": url}

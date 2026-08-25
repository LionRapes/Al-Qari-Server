from fastapi import APIRouter, Depends, HTTPException, Path
from app.interfaces import StorageInterface
from app.dependencies import get_storage
from app.utils import fetch_from_storage

router = APIRouter(prefix="/quran", tags=["Quran Content"])


@router.get("/riwayah/{riwayah_type}", summary="Get riwayah")
async def get_riwayah(
    riwayah_type: str,
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/riwayah/{riwayah_type}.json")


@router.get("/riwayah/{riwayah_type}/{surah_id}", summary="Get Surah by riwayah")
async def get_surah(
    riwayah_type: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/riwayah/{riwayah_type}/{surah_id:03d}.json")


@router.get("/tafsir/{edition}", summary="Get tafsir")
async def get_tafsir(
    edition: str,
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/tafsir/{edition}.json")


@router.get("/tafsir/{edition}/{surah_id}", summary="Get Surah tafsir")
async def get_surah_tafsir(
    edition: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/tafsir/{edition}/{surah_id:03d}.json")


@router.get("/transcription/{riwayah_type}/{lang}", summary="Get transcription by riwayah and lang")
async def get_transcription(
    riwayah_type: str,
    lang: str,
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/transcription/{riwayah_type}/{lang}.json")


@router.get("/transcription/{riwayah_type}/{lang}/{surah_id}", summary="Get Surah transcription by riwayah and lang")
async def get_surah_transcription(
    riwayah_type: str,
    lang: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/transcription/{riwayah_type}/{lang}/{surah_id:03d}.json")


@router.get("/translation/{lang}", summary="Get translation")
async def get_translation(
    lang: str,
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/translation/{lang}.json")


@router.get("/translation/{lang}/{surah_id}", summary="Get Surah translation")
async def get_surah_translation(
    lang: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/translation/{lang}/{surah_id:03d}.json")


@router.get("/audio/{riwayah_type}/{reciter_name}_{bitrate}/timestamps", summary="Get reciter timestamps by riwayah type, reciter name and bitrate")
def get_timestamps(
    riwayah_type: str,
    reciter_name: str,
    bitrate: str,
    storage: StorageInterface = Depends(get_storage),
):
    return fetch_from_storage(storage, f"quran/audio/{riwayah_type}/{reciter_name}_{bitrate}/timestamps.json")


@router.get("/audio/{riwayah_type}/{reciter_name}_{bitrate}/{surah_id}", summary="Get Surah audio by riwayah type, reciter name and bitrate")
async def get_surah_audio(
    riwayah_type: str,
    reciter_name: str,
    bitrate: str,
    surah_id: int = Path(..., ge=1, le=114, description="Surah number from 1 to 114"),
    storage: StorageInterface = Depends(get_storage),
):
    file_path = f"quran/audio/{riwayah_type}/{reciter_name}_{bitrate}/{surah_id:03d}.mp3"
    print(file_path)
    
    url = await storage.create_presigned_url(file_path, expires_in=900)
    if url is None:
        raise HTTPException(404, "Audio not found")
    
    return {"url": url}

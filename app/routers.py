from fastapi import APIRouter

from app.routes.metadata_routes import router as metadata_router
from app.routes.playlist_routes import router as playlist_router
from app.routes.quran_routes import router as quran_router
from app.routes.user_routes import router as user_router

api_router = APIRouter()

api_router.include_router(metadata_router)
api_router.include_router(quran_router)
api_router.include_router(playlist_router)
api_router.include_router(user_router)
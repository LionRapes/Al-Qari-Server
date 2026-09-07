"""Main entry point and application configuration for the Al-Qari server."""

import os

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORE_SETTINGS
from app.routes.forum_routes import router as forum_router
from app.routes.metadata_routes import router as metadata_router
from app.routes.playlist_routes import router as playlist_router
from app.routes.quran_routes import router as quran_router
from app.routes.user_routes import router as user_router

app = FastAPI(title="Al-Qari Server")

api_router = APIRouter()
api_router.include_router(metadata_router)
api_router.include_router(quran_router)
api_router.include_router(playlist_router)
api_router.include_router(user_router)
api_router.include_router(forum_router)

app.include_router(api_router)

cors = CORE_SETTINGS.cors_origins
cors_headers = ["*", "X-Auth-Token", "Content-Type", "Accept"]

if cors.startswith("^"):
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=cors,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=cors_headers,
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cors],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=cors_headers,
    )


def dev():
    """Runs the application in development mode with hot-reloading enabled."""
    os.environ["APP_ENV"] = "development"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)


def prod():
    """Runs the application in production mode without hot-reloading."""
    os.environ["APP_ENV"] = "production"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)

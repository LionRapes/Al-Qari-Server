"""Main entry point and application configuration for the Al-Qari server."""

import os

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(api_router)

FRONTEND_URL = os.getenv("CORS_ORIGINS")
cors_headers = ["*", "X-Auth-Token", "Content-Type", "Accept"]

if FRONTEND_URL.startswith("^"):
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=FRONTEND_URL,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=cors_headers,
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=cors_headers,
    )


def dev():
    """Runs the application in development mode with hot-reloading enabled."""
    os.environ["FRONTEND_URL"] = "http://127.0.0.1:5173"
    os.environ["CORS_ORIGINS"] = "http://127.0.0.1:5173"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)


def prod():
    """Runs the application in production mode without hot-reloading."""
    os.environ["FRONTEND_URL"] = "http://127.0.0.1:5173"
    os.environ["CORS_ORIGINS"] = "http://127.0.0.1:5173"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import api_router

app = FastAPI(title="Al-Qari Server")

app.include_router(api_router)

frontend_url = os.getenv("CORS_ORIGINS", r"^https?://([a-zA-Z0-9-]+\.)*al-qari\.ru$")
cors_headers = ["*", "X-Auth-Token", "Content-Type", "Accept"]

if frontend_url.startswith("^"):
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=frontend_url,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=cors_headers
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=cors_headers
    )

def dev():
    os.environ["FRONTEND_URL"] = "http://127.0.0.1:5173"
    os.environ["CORS_ORIGINS"] = "http://127.0.0.1:5173"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
    
def prod():
    os.environ["FRONTEND_URL"] = "http://127.0.0.1:5173"
    os.environ["CORS_ORIGINS"] = "http://127.0.0.1:5173"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)
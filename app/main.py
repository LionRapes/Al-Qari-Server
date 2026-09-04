import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import api_router

app = FastAPI(title="Al-Qari Server")

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def dev():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
    
def prod():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)

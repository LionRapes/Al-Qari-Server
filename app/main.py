import uvicorn
from fastapi import FastAPI
from app.routers import api_router

app = FastAPI(title="Al-Qari Server")

app.include_router(api_router)

def start():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    start()
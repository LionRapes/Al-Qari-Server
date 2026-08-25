import uvicorn
from fastapi import FastAPI
from app.routers import api_router

app = FastAPI(title="Al-Qari Server")

app.include_router(api_router)

def dev():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
    
def prod():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)

import uvicorn
from fastapi import FastAPI
from apps.movies.routers import router as movies_router
from apps.vinyl.routers import router as vinyl_router
from apps.storage.routers import router as storage_router

app = FastAPI()

app.include_router(movies_router, tags=["movies"], prefix="/movies")
app.include_router(vinyl_router, tags=["vinyl"], prefix="/vinyl")
app.include_router(storage_router, tags=["storage"], prefix="/storage")

import asyncio
import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from apps.movies.routers import router as movies_router
from apps.movies.routers import router_config as movies_router_config
from apps.vinyl.routers import router as vinyl_router
from apps.vinyl.routers import router_config as vinyl_router_config
from apps.storage.routers import router as storage_router
from apps.storage.routers import router_config as storage_router_config

from config import settings
from database import db

logging.basicConfig(
    filename="/logs/application.log",
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI()

app.include_router(movies_router, tags=["movies"], prefix="/movies")
app.include_router(vinyl_router, tags=["vinyl"], prefix="/vinyl")
app.include_router(storage_router, tags=["storage"], prefix="/storage")


@app.on_event("startup")
async def startup_db_client():
    movie_task = asyncio.create_task(movies_router_config.setup(mongodb=db.mongodb))
    storage_task = asyncio.create_task(storage_router_config.setup(mongodb=db.mongodb))
    vinyl_task = asyncio.create_task(vinyl_router_config.setup(mongodb=db.mongodb))
    await asyncio.gather(movie_task, storage_task, vinyl_task)


@app.on_event("shutdown")
async def shutdown_db_client():
    db.mongodb_client.close()


@app.get("/config")
async def get_settings():
    if settings.DEBUG_MODE:
        return JSONResponse(status_code=200, content=settings.json())
    log.warning("Attempt to access configuration settings has been rejected.")
    return HTTPException(
        status_code=403,
        detail="DEBUG_MODE is set to False, this is only avaiable while set to True",
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=settings.DEBUG_MODE,
        port=8000,
    )

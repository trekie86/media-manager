import asyncio

import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from apps.movies.routers import router as movies_router
from apps.movies.routers import router_config as movies_router_config
from apps.vinyl.routers import router as vinyl_router
from apps.vinyl.routers import router_config as vinyl_router_config
from apps.storage.routers import router as storage_router
from apps.storage.routers import router_config as storage_router_config
import logging

from config import settings

app = FastAPI()
log = logging.getLogger(__name__)

app.include_router(movies_router, tags=["movies"], prefix="/movies")
app.include_router(vinyl_router, tags=["vinyl"], prefix="/vinyl")
app.include_router(storage_router, tags=["storage"], prefix="/storage")


@app.on_event("startup")
async def startup_db_client():
    log.info("In startup event method")
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
    app.mongodb = app.mongodb_client[settings.DB_NAME]
    movie_task = asyncio.create_task(movies_router_config.setup(mongodb=app.mongodb))
    await movie_task
    storage_router_config.setup(mongodb=app.mongodb)
    vinyl_router_config.setup(mongodb=app.mongodb)


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


@app.get("/config")
async def get_settings(request: Request):
    if settings.DEBUG_MODE:
        return JSONResponse(status_code=200, content=settings.json())
    else:
        return HTTPException(status_code=403,
                             detail="DEBUG_MODE is set to False, this is only avaiable while set to True")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=settings.DEBUG_MODE,
        port=8000,
    )

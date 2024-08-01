from fastapi import APIRouter, Request
from motor.motor_asyncio import AsyncIOMotorClient

from apps.setup import Setup

router = APIRouter()


class Config(Setup):
    def __init__(self):
        pass

    async def setup(self, mongodb: AsyncIOMotorClient) -> None:
        # TODO: Setup vinyl db
        pass


router_config = Config()


@router.get("/", summary="Get all of the vinyl records")
async def get_all_vinyl(request: Request):
    return {"message": "All of the vinyl"}


@router.get("/{id}", summary="Get a specific vincyl record")
async def get_vinyl(id: str, request: Request):
    return {"message": f"A vinyl record identified by {id}"}


@router.post("/", summary="Create a new vinyl record")
async def create_vinyl(request: Request):
    return {"message": "A new id"}


@router.put("/{id}", summary="Update a specific vinyl record")
async def update_vinyl(id: str, request: Request):
    return {"message": f"Update a vinyl record identified by {id}"}


@router.delete("/{id}", summary="Delete a vinyl record identified")
async def delete_vinyl(id: str, request: Request):
    return {"message": f"Deleted a vinyl record identified by {id}"}


@router.get("/search", summary="Search for vinyl records")
async def search_vinyl(request: Request):
    return {"message": "The search results for the vinyl records"}


@router.get("/cover/{id}", summary="Get the vinyl record's album cover")
async def get_album_cover(id: str, request: Request):
    return {"message": f"The album cover for the album identified by {id}"}

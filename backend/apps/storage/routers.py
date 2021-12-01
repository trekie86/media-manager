from fastapi import APIRouter, Request
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()


class Config:
    def __init__(self):
        pass

    async def setup(self, mongodb: AsyncIOMotorClient) -> None:
        # TODO: Setup storage db
        pass


router_config = Config()


@router.get("/", summary="Get all of the storage containers")
async def get_containers(request: Request):
    return {"message": "All of the container"}


@router.get("/{id}", summary="Get a specific storage container")
async def get_container(id: str, request: Request):
    return {"message": f"The container identified by {id}"}


@router.post("/", summary="Create a new storage container")
async def create_container(request: Request):
    return {"message": "A new id"}


@router.put("/{id}", summary="Updates an existing container")
async def update_container(id: str, request: Request):
    return {"message": f"Updated container identified by {id}"}


@router.delete("/{id}", summary="Delete a storage container")
async def delete_container(id: str, request: Request):
    return {"message": f"Storage container identified by {id} has been deleted"}

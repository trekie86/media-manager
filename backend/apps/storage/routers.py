from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/", summary="Get all of the storage containers")
async def get_containers(request: Request):
    return {"message": "All of the container"}

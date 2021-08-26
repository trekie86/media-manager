from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/", summary="Get all of the vinyl records")
async def get_all_vinyl(request: Request):
    return {"message": "All of the vinyl"}

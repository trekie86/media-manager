from fastapi import APIRouter, Request, HTTPException, Body, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from .models.movie import Movie, UpdateMovie

router = APIRouter()


@router.get("/", summary="Get all of the movies", response_model=list[Movie], status_code=status.HTTP_200_OK)
async def get_movies(request: Request):
    """
    Retrieve all of the movies in the database.
    :return: The list of movies
    """
    mongodb = request.app.mongodb
    results = []
    for doc in await mongodb["movies"].find().to_list(length=1000):
        results.append(Movie(**doc))

    return results


@router.get("/{id}", summary="Get a specific movie", response_model=Movie, status_code=status.HTTP_200_OK)
async def get_movie(id: str, request: Request):
    """
    Retrieve a specific movie.
    :param id: The id of the movie.
    :return: The movie information.
    """
    doc = await request.app.mongodb["movies"].find_one({"_id": id})
    if doc is not None:
        return Movie(**doc)

    raise HTTPException(status_code=404, detail=f"Movie {id} not found")


@router.post("/", summary="Add a movie", status_code=status.HTTP_201_CREATED)
async def add_movie(request: Request, movie: Movie = Body(...)):
    """
    Add a movie with the given input.
    :return: The id of the movie.
    """
    movie = jsonable_encoder(movie)
    new_movie = await request.app.mongodb["movies"].insert_one(movie)
    created_movie = await request.app.mongodb["movies"].find_one(
        {"_id": new_movie.inserted_id}
    )
    return JSONResponse(content=created_movie["_id"])


@router.put("/{id}", summary="Updete a movie")
async def update_movie(id: str, request: Request, movie: UpdateMovie):
    """
    Update a movie identified by the given id.
    :param id: The id of the movie.
    :return: Return the updated movie object.
    """
    return {"message": f"The updated movie identified by {id}"}


@router.delete("/{id}", summary="Delete a movie", status_code=status.HTTP_204_NO_CONTENT)
async def delete_move(id: str, request: Request):
    """
    Delete the movie identified by the given id.
    :param id: The id of the movie.
    :param request:
    :return: A confirmation message if deleted successfully.
    """
    delete_result = await request.app.mongodb["movies"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return

    raise HTTPException(status_code=404, detail=f"Moive {id} not found.")


@router.get(
    "/search",
    summary="Search for a movie the given params, either within the database or via an external movie database.",
)
async def movie_search(request: Request):
    """
    Search for a movie via the given parameters.
    :param request:
    :return: The movie object.
    """
    return {"message": "Movie not found."}


@router.get("/poster/{id}", summary="Get the URI of the movie poster.")
async def get_movie_poster(id: str, request: Request):
    """
    Retrieve the URI of the poster identified by the movie id.
    :param id: The movie id.
    :param request:
    :return: The poster's URI
    """
    return {
        "message": f"Here is the poster for the movie identified by {id}",
        "path": "www.eatmyshorts.com/poster.png",
    }

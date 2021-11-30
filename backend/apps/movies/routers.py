from typing import Optional

import pymongo
from fastapi import APIRouter, Request, HTTPException, Body, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from .models.movie import Movie, UpdateMovie

router = APIRouter()
log = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.indexCreated = False

    async def setup(self, mongodb: AsyncIOMotorClient) -> None:
        # TODO: Implement setup method that will configure DB needs (e.g. indices)
        log.info("In Movies router setup method")
        if not self.indexCreated:
            index_information = await mongodb["movies"].index_information()
            log.info(f"Retrieved indices: {index_information}")
            if "title_index" not in index_information.keys():
                # Create the index on title as a TEXT index.
                log.info(f"Creating index on title for collection movies")
                await mongodb["movies"].create_index([("title", pymongo.TEXT)],
                                                                       background=True, name="title_index")
                log.info(f"Index creation request successfully submitted")
            self.indexCreated = True


router_config = Config()


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
    :param request: The request object.
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


@router.put("/{id}", summary="Update a movie", response_model=Movie, status_code=status.HTTP_202_ACCEPTED)
async def update_movie(id: str, request: Request, movie: UpdateMovie = Body(...)) -> Movie:
    """
    Update a movie identified by the given id.
    :param id: The id of the movie.
    :param request: The API request object.
    :param movie: The body of the request.
    :return: The updated movie.
    """
    movie = jsonable_encoder(movie)
    result = await request.app.mongodb["movies"].update_one({"_id": id}, {"$set": movie})
    if result.modified_count == 1:
        updated_movie = await request.app.mongodb["movies"].find_one(
            {"_id": id}
        )
        return Movie(**updated_movie)

    raise HTTPException(status_code=404, detail=f"Movie {id} was not available to update")


@router.delete("/{id}", summary="Delete a movie", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(id: str, request: Request):
    """
    Delete the movie identified by the given id.
    :param id: The id of the movie.
    :param request:
    :return: A confirmation message if deleted successfully.
    """
    delete_result = await request.app.mongodb["movies"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return

    raise HTTPException(status_code=404, detail=f"Movie {id} not found.")


@router.get("/search/",
    summary="Search for a movie the given params, either within the database or via an external movie database.",
    status_code=status.HTTP_200_OK,
    response_model=list[Movie]
)
async def movie_search(request: Request, q: str = None):
    """
    Search for a movie via the given parameters.
    :param q: The query parameter, in this case right now it's only the title.
    :param request: The request object
    :return: The movie object.
    """

    if not q:
        raise HTTPException(status_code=400, detail="No search conditions provided.")

    # Using regex for a free-form search and applying the case insensitive option
    results = await request.app.mongodb["movies"].find({"title": {"$regex": q, "$options": "i"}}).to_list(None)
    if results:
        movie_list = [Movie(**x) for x in results]
        return movie_list
    return HTTPException(status_code=404, detail=f"There were no movies found for search parameter of {q}")


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

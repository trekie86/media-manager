from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/", summary="Get all of the movies")
async def get_movies(request: Request):
    """
    Retrieve all of the movies in the database.
    :return: The list of movies
    """
    return {"message": "All the movies."}


@router.get("/{id}", summary="Get a specific movie")
async def get_movie(id: str, request: Request):
    """
    Retrieve a specific movie.
    :param id: The id of the movie.
    :return: The movie information.
    """
    return {"message": f"The movie identified by {id}"}


@router.post("/", summary="Add a movie")
async def add_movie(request: Request):
    """
    Add a movie with the given input.
    :return: The id of the movie.
    """
    return {"message": "A new id"}


@router.put("/{id}", summary="Updete a movie")
async def update_movie(id: str, request: Request):
    """
    Update a movie identified by the given id.
    :param id: The id of the movie.
    :return: Return the updated movie object.
    """
    return {"message": f"The updated movie identified by {id}"}


@router.delete("/{id}", summary="Delete a movie")
async def delete_move(id: str, request: Request):
    """
    Delete the movie identified by the given id.
    :param id: The id of the movie.
    :param request:
    :return: A confirmation message if deleted successfully.
    """
    return {"deleted": True, "message": f"Movie identified by {id} has been deleted."}


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
    return {"message": f"Here is the poster for the movie identified by {id}", "path": "www.eatmyshorts.com/poster.png"}

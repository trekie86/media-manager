"""Integration tests for movie routes."""

import pytest
from bson import ObjectId
from unittest.mock import AsyncMock

from app.models.movie import MediaFormat

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def sample_storage(test_db):
    """Create a sample storage location for testing."""
    storage_data = {
        "name": "Test Cabinet",
        "description": "Test storage cabinet",
        "type": "cabinet",
        "parent_id": None,
        "path": [],
        "metadata": {},
    }
    result = await test_db.storage.insert_one(storage_data)
    return str(result.inserted_id)


@pytest.fixture
async def sample_movie_data(sample_storage):
    """Create sample movie data for testing."""
    return {
        "title": "The Matrix",
        "year": 1999,
        "format": MediaFormat.BLURAY.value,
        "storage_id": sample_storage,
        "tmdb_id": 603,
        "genre_ids": [28, 878],
        "runtime": 136,
        "cover_image": "https://example.com/matrix.jpg",
    }


async def test_create_movie_success(client, sample_movie_data, test_db):
    """Test successful movie creation."""
    response = await client.post("/api/movies/", json=sample_movie_data)

    assert response.status_code == 201
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert data["title"] == sample_movie_data["title"]
    assert data["year"] == sample_movie_data["year"]
    assert data["format"] == sample_movie_data["format"]
    assert data["storage_id"] == sample_movie_data["storage_id"]
    assert data["tmdb_id"] == sample_movie_data["tmdb_id"]
    assert data["genre_ids"] == sample_movie_data["genre_ids"]
    assert data["runtime"] == sample_movie_data["runtime"]
    assert data["cover_image"] == sample_movie_data["cover_image"]

    # Verify movie was created in database
    movie_id = ObjectId(data["id"])
    db_movie = await test_db.movies.find_one({"_id": movie_id})
    assert db_movie is not None
    assert db_movie["title"] == sample_movie_data["title"]


async def test_create_movie_invalid_storage_id(client, sample_movie_data):
    """Test movie creation with invalid storage ID."""
    sample_movie_data["storage_id"] = "invalid_id"
    response = await client.post("/api/movies/", json=sample_movie_data)

    assert response.status_code == 400
    assert "Invalid storage_id format" in response.json()["detail"]


async def test_create_movie_nonexistent_storage(client, sample_movie_data):
    """Test movie creation with non-existent storage ID."""
    sample_movie_data["storage_id"] = str(ObjectId())
    response = await client.post("/api/movies/", json=sample_movie_data)

    assert response.status_code == 404
    assert "Storage location not found" in response.json()["detail"]


async def test_create_movie_minimal_data(client, sample_storage):
    """Test movie creation with minimal required data."""
    minimal_data = {
        "title": "Minimal Movie",
        "year": 2020,
        "format": MediaFormat.DVD.value,
        "storage_id": sample_storage,
    }

    response = await client.post("/api/movies/", json=minimal_data)

    if response.status_code != 201:
        print(f"Error response: {response.status_code}")
        print(f"Error detail: {response.text}")

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == minimal_data["title"]
    assert data["tmdb_id"] is None
    assert data["genre_ids"] is None
    assert data["runtime"] is None
    assert data["cover_image"] is None


async def test_list_movies_empty(client):
    """Test listing movies when none exist."""
    response = await client.get("/api/movies/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_movies_with_data(client, test_db, sample_storage):
    """Test listing movies with existing data."""
    # Create test movies
    movies = [
        {
            "title": "Movie 1",
            "year": 2020,
            "format": "DVD",
            "storage_id": ObjectId(sample_storage),
            "genre_ids": [28],
        },
        {
            "title": "Movie 2",
            "year": 2021,
            "format": "Blu-ray",
            "storage_id": ObjectId(sample_storage),
            "genre_ids": [35],
        },
    ]

    for movie in movies:
        await test_db.movies.insert_one(movie)

    response = await client.get("/api/movies/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("id" in movie for movie in data)
    assert all("title" in movie for movie in data)


async def test_list_movies_with_pagination(client, test_db, sample_storage):
    """Test movie listing with pagination."""
    # Create multiple test movies
    movies = []
    for i in range(5):
        movie = {
            "title": f"Movie {i}",
            "year": 2020 + i,
            "format": "DVD",
            "storage_id": ObjectId(sample_storage),
        }
        result = await test_db.movies.insert_one(movie)
        movies.append(result.inserted_id)

    # Test pagination
    response = await client.get("/api/movies/?skip=2&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_list_movies_filter_by_storage(client, test_db):
    """Test filtering movies by storage location."""
    # Create two storage locations
    storage1_result = await test_db.storage.insert_one(
        {"name": "Storage 1", "type": "cabinet", "path": []}
    )
    storage2_result = await test_db.storage.insert_one(
        {"name": "Storage 2", "type": "cabinet", "path": []}
    )

    storage1_id = storage1_result.inserted_id
    storage2_id = storage2_result.inserted_id

    # Create movies in different storage locations
    await test_db.movies.insert_one(
        {
            "title": "Movie in Storage 1",
            "year": 2020,
            "format": "DVD",
            "storage_id": storage1_id,
        }
    )
    await test_db.movies.insert_one(
        {
            "title": "Movie in Storage 2",
            "year": 2021,
            "format": "Blu-ray",
            "storage_id": storage2_id,
        }
    )

    # Filter by storage1
    response = await client.get(f"/api/movies/?storage_id={str(storage1_id)}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Movie in Storage 1"


async def test_list_movies_filter_by_format(client, test_db, sample_storage):
    """Test filtering movies by format."""
    # Create movies with different formats
    movies = [
        {
            "title": "DVD Movie",
            "year": 2020,
            "format": "DVD",
            "storage_id": ObjectId(sample_storage),
        },
        {
            "title": "Blu-ray Movie",
            "year": 2021,
            "format": "Blu-ray",
            "storage_id": ObjectId(sample_storage),
        },
    ]

    for movie in movies:
        await test_db.movies.insert_one(movie)

    # Filter by DVD format
    response = await client.get("/api/movies/?format=DVD")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "DVD Movie"


async def test_list_movies_filter_by_genre(client, test_db, sample_storage):
    """Test filtering movies by genre."""
    # Create movies with different genres
    movies = [
        {
            "title": "Action Movie",
            "year": 2020,
            "format": "DVD",
            "storage_id": ObjectId(sample_storage),
            "genre_ids": [28, 53],
        },
        {
            "title": "Comedy Movie",
            "year": 2021,
            "format": "Blu-ray",
            "storage_id": ObjectId(sample_storage),
            "genre_ids": [35],
        },
    ]

    for movie in movies:
        await test_db.movies.insert_one(movie)

    # Filter by Action genre
    response = await client.get("/api/movies/?genre_id=28")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Action Movie"


async def test_get_movie_success(client, test_db, sample_storage):
    """Test successful movie retrieval."""
    # Create a test movie
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": ObjectId(sample_storage),
        "tmdb_id": 123,
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)

    response = await client.get(f"/api/movies/{movie_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == movie_id
    assert data["title"] == "Test Movie"
    assert data["tmdb_id"] == 123


async def test_get_movie_not_found(client):
    """Test retrieving non-existent movie."""
    movie_id = str(ObjectId())
    response = await client.get(f"/api/movies/{movie_id}")

    assert response.status_code == 404
    assert "Movie not found" in response.json()["detail"]


async def test_get_movie_invalid_id(client):
    """Test retrieving movie with invalid ID format."""
    response = await client.get("/api/movies/invalid_id")

    assert response.status_code == 400
    assert "Invalid movie ID format" in response.json()["detail"]


async def test_update_movie_success(client, test_db, sample_storage):
    """Test successful movie update."""
    # Create a test movie
    movie_data = {
        "title": "Original Title",
        "year": 2020,
        "format": "DVD",
        "storage_id": ObjectId(sample_storage),
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)

    # Update the movie
    update_data = {"title": "Updated Title", "year": 2021, "tmdb_id": 456}

    response = await client.put(f"/api/movies/{movie_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["year"] == 2021
    assert data["tmdb_id"] == 456
    assert data["format"] == "DVD"  # Unchanged field


async def test_update_movie_clear_genres(client, test_db, sample_storage):
    """Test that updating a movie with an empty genre list clears all genres."""
    # Create a movie with genres
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": ObjectId(sample_storage),
        "genre_ids": [28, 53],
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)

    # Clear all genres by sending an empty list
    response = await client.put(f"/api/movies/{movie_id}", json={"genre_ids": []})

    assert response.status_code == 200
    data = response.json()
    assert data["genre_ids"] == [] or data["genre_ids"] is None


async def test_update_movie_storage_location(client, test_db):
    """Test updating movie storage location."""
    # Create two storage locations
    storage1_result = await test_db.storage.insert_one(
        {"name": "Storage 1", "type": "cabinet", "path": []}
    )
    storage2_result = await test_db.storage.insert_one(
        {"name": "Storage 2", "type": "cabinet", "path": []}
    )

    storage1_id = str(storage1_result.inserted_id)
    storage2_id = str(storage2_result.inserted_id)

    # Create movie in storage1
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": storage1_result.inserted_id,
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)

    # Move to storage2
    update_data = {"storage_id": storage2_id}
    response = await client.put(f"/api/movies/{movie_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["storage_id"] == storage2_id


async def test_update_movie_invalid_storage(client, test_db, sample_storage):
    """Test updating movie with invalid storage ID."""
    # Create a test movie
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": ObjectId(sample_storage),
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)

    # Try to update with non-existent storage
    update_data = {"storage_id": str(ObjectId())}
    response = await client.put(f"/api/movies/{movie_id}", json=update_data)

    assert response.status_code == 404
    assert "Storage location not found" in response.json()["detail"]


async def test_update_movie_not_found(client):
    """Test updating non-existent movie."""
    movie_id = str(ObjectId())
    update_data = {"title": "New Title"}

    response = await client.put(f"/api/movies/{movie_id}", json=update_data)

    assert response.status_code == 404
    assert "Movie not found" in response.json()["detail"]


async def test_update_movie_no_fields(client, test_db, sample_storage):
    """Test updating movie with no valid fields."""
    # Create a test movie
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": ObjectId(sample_storage),
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)

    # Try to update with empty data
    response = await client.put(f"/api/movies/{movie_id}", json={})

    assert response.status_code == 400
    assert "No valid fields to update" in response.json()["detail"]


async def test_delete_movie_success(client, test_db, sample_storage):
    """Test successful movie deletion."""
    # Create a test movie
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": ObjectId(sample_storage),
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)

    response = await client.delete(f"/api/movies/{movie_id}")

    assert response.status_code == 204

    # Verify movie was deleted
    db_movie = await test_db.movies.find_one({"_id": result.inserted_id})
    assert db_movie is None


async def test_delete_movie_not_found(client):
    """Test deleting non-existent movie."""
    movie_id = str(ObjectId())
    response = await client.delete(f"/api/movies/{movie_id}")

    assert response.status_code == 404
    assert "Movie not found" in response.json()["detail"]


async def test_delete_movie_invalid_id(client):
    """Test deleting movie with invalid ID format."""
    response = await client.delete("/api/movies/invalid_id")

    assert response.status_code == 400
    assert "Invalid movie ID format" in response.json()["detail"]


# ── TMDB auto-enrichment tests ─────────────────────────────────────────────


async def test_create_movie_auto_enriches_from_tmdb(
    client, sample_storage, mock_tmdb_service
):
    """Movie with tmdb_id and no genre/runtime/cover gets auto-enriched from TMDB."""
    mock_tmdb_service.get_movie_details = AsyncMock(
        return_value={
            "genre_ids": [28, 878],
            "runtime": 136,
            "poster_url": "https://tmdb.example.com/poster.jpg",
        }
    )

    payload = {
        "title": "The Matrix",
        "year": 1999,
        "format": MediaFormat.BLURAY.value,
        "storage_id": sample_storage,
        "tmdb_id": 603,
    }
    response = await client.post("/api/movies/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["genre_ids"] == [28, 878]
    assert data["runtime"] == 136
    assert data["cover_image"] == "https://tmdb.example.com/poster.jpg"
    mock_tmdb_service.get_movie_details.assert_called_once_with(603)


async def test_create_movie_tmdb_does_not_overwrite_manual_fields(
    client, sample_storage, mock_tmdb_service
):
    """Manually supplied fields are preserved even when TMDB returns data."""
    mock_tmdb_service.get_movie_details = AsyncMock(
        return_value={
            "genre_ids": [28, 878],
            "runtime": 136,
            "poster_url": "https://tmdb.example.com/poster.jpg",
        }
    )

    payload = {
        "title": "The Matrix",
        "year": 1999,
        "format": MediaFormat.BLURAY.value,
        "storage_id": sample_storage,
        "tmdb_id": 603,
        "genre_ids": [18],
        "runtime": 200,
        "cover_image": "https://manual.example.com/poster.jpg",
    }
    response = await client.post("/api/movies/", json=payload)

    assert response.status_code == 201
    data = response.json()
    # Manual values should be preserved
    assert data["genre_ids"] == [18]
    assert data["runtime"] == 200
    assert data["cover_image"] == "https://manual.example.com/poster.jpg"
    # TMDB should not be called because all enrichable fields are already set
    mock_tmdb_service.get_movie_details.assert_not_called()


async def test_create_movie_succeeds_when_tmdb_fails(
    client, sample_storage, mock_tmdb_service
):
    """Movie creation succeeds gracefully even when TMDB raises an exception."""
    mock_tmdb_service.get_movie_details = AsyncMock(
        side_effect=Exception("TMDB API down")
    )

    payload = {
        "title": "The Matrix",
        "year": 1999,
        "format": MediaFormat.BLURAY.value,
        "storage_id": sample_storage,
        "tmdb_id": 603,
    }
    response = await client.post("/api/movies/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "The Matrix"
    # Enrichable fields absent because TMDB failed
    assert data["genre_ids"] is None
    assert data["runtime"] is None
    assert data["cover_image"] is None


async def test_create_movie_without_tmdb_id_skips_enrichment(
    client, sample_storage, mock_tmdb_service
):
    """TMDB is never called when no tmdb_id is provided."""
    payload = {
        "title": "Minimal Movie",
        "year": 2020,
        "format": MediaFormat.DVD.value,
        "storage_id": sample_storage,
    }
    response = await client.post("/api/movies/", json=payload)

    assert response.status_code == 201
    mock_tmdb_service.get_movie_details.assert_not_called()


async def test_create_movie_all_fields_set_skips_tmdb(
    client, sample_storage, mock_tmdb_service
):
    """TMDB is not called when genre, runtime, and cover_image are all already provided."""
    payload = {
        "title": "The Matrix",
        "year": 1999,
        "format": MediaFormat.BLURAY.value,
        "storage_id": sample_storage,
        "tmdb_id": 603,
        "genre_ids": [28],
        "runtime": 136,
        "cover_image": "https://example.com/poster.jpg",
    }
    response = await client.post("/api/movies/", json=payload)

    assert response.status_code == 201
    mock_tmdb_service.get_movie_details.assert_not_called()


# ---------------------------------------------------------------------------
# MovieUpdate field validator coverage
# ---------------------------------------------------------------------------


@pytest.fixture
async def existing_movie(client, sample_movie_data):
    """Create a movie via the API and return its ID string."""
    response = await client.post("/api/movies/", json=sample_movie_data)
    assert response.status_code == 201
    return response.json()["id"]


async def test_update_movie_invalid_year_too_early(client, existing_movie):
    """year < 1900 must be rejected with 422."""
    response = await client.put(f"/api/movies/{existing_movie}", json={"year": 1800})
    assert response.status_code == 422


async def test_update_movie_invalid_year_too_late(client, existing_movie):
    """year > 2100 must be rejected with 422."""
    response = await client.put(f"/api/movies/{existing_movie}", json={"year": 2200})
    assert response.status_code == 422


async def test_update_movie_negative_runtime_rejected(client, existing_movie):
    """runtime < 0 must be rejected with 422."""
    response = await client.put(f"/api/movies/{existing_movie}", json={"runtime": -5})
    assert response.status_code == 422


async def test_update_movie_invalid_format_rejected(client, existing_movie):
    """An unknown format string must be rejected with 422."""
    response = await client.put(f"/api/movies/{existing_movie}", json={"format": "VHS"})
    assert response.status_code == 422


async def test_update_movie_valid_boundary_year(client, existing_movie):
    """year == 1900 is the lower boundary and must be accepted."""
    response = await client.put(f"/api/movies/{existing_movie}", json={"year": 1900})
    assert response.status_code == 200
    assert response.json()["year"] == 1900


async def test_update_movie_zero_runtime_accepted(client, existing_movie):
    """runtime == 0 is the lower boundary (ge=0) and must be accepted."""
    response = await client.put(f"/api/movies/{existing_movie}", json={"runtime": 0})
    assert response.status_code == 200
    assert response.json()["runtime"] == 0

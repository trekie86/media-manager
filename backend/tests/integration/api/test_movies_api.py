"""Integration tests for movie routes."""
import pytest
from bson import ObjectId

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
        "metadata": {}
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
        "genre": ["Action", "Science Fiction"],
        "runtime": 136,
        "cover_image": "https://example.com/matrix.jpg"
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
    assert data["genre"] == sample_movie_data["genre"]
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
        "storage_id": sample_storage
    }
    
    response = await client.post("/api/movies/", json=minimal_data)
    
    if response.status_code != 201:
        print(f"Error response: {response.status_code}")
        print(f"Error detail: {response.text}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == minimal_data["title"]
    assert data["tmdb_id"] is None
    assert data["genre"] is None
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
            "genre": ["Action"]
        },
        {
            "title": "Movie 2",
            "year": 2021,
            "format": "Blu-ray",
            "storage_id": ObjectId(sample_storage),
            "genre": ["Comedy"]
        }
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
            "storage_id": ObjectId(sample_storage)
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
    storage1_result = await test_db.storage.insert_one({
        "name": "Storage 1", "type": "cabinet", "path": []
    })
    storage2_result = await test_db.storage.insert_one({
        "name": "Storage 2", "type": "cabinet", "path": []
    })
    
    storage1_id = storage1_result.inserted_id
    storage2_id = storage2_result.inserted_id
    
    # Create movies in different storage locations
    await test_db.movies.insert_one({
        "title": "Movie in Storage 1",
        "year": 2020,
        "format": "DVD",
        "storage_id": storage1_id
    })
    await test_db.movies.insert_one({
        "title": "Movie in Storage 2",
        "year": 2021,
        "format": "Blu-ray",
        "storage_id": storage2_id
    })
    
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
        {"title": "DVD Movie", "year": 2020, "format": "DVD", "storage_id": ObjectId(sample_storage)},
        {"title": "Blu-ray Movie", "year": 2021, "format": "Blu-ray", "storage_id": ObjectId(sample_storage)}
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
        {"title": "Action Movie", "year": 2020, "format": "DVD", "storage_id": ObjectId(sample_storage), "genre": ["Action", "Thriller"]},
        {"title": "Comedy Movie", "year": 2021, "format": "Blu-ray", "storage_id": ObjectId(sample_storage), "genre": ["Comedy"]}
    ]
    
    for movie in movies:
        await test_db.movies.insert_one(movie)
    
    # Filter by Action genre
    response = await client.get("/api/movies/?genre=Action")
    
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
        "tmdb_id": 123
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
        "storage_id": ObjectId(sample_storage)
    }
    result = await test_db.movies.insert_one(movie_data)
    movie_id = str(result.inserted_id)
    
    # Update the movie
    update_data = {
        "title": "Updated Title",
        "year": 2021,
        "tmdb_id": 456
    }
    
    response = await client.put(f"/api/movies/{movie_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["year"] == 2021
    assert data["tmdb_id"] == 456
    assert data["format"] == "DVD"  # Unchanged field


async def test_update_movie_storage_location(client, test_db):
    """Test updating movie storage location."""
    # Create two storage locations
    storage1_result = await test_db.storage.insert_one({
        "name": "Storage 1", "type": "cabinet", "path": []
    })
    storage2_result = await test_db.storage.insert_one({
        "name": "Storage 2", "type": "cabinet", "path": []
    })
    
    storage1_id = str(storage1_result.inserted_id)
    storage2_id = str(storage2_result.inserted_id)
    
    # Create movie in storage1
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": storage1_result.inserted_id
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
        "storage_id": ObjectId(sample_storage)
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
        "storage_id": ObjectId(sample_storage)
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
        "storage_id": ObjectId(sample_storage)
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

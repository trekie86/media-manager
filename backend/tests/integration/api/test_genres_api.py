"""Integration tests for genre routes."""
import pytest

pytestmark = pytest.mark.asyncio


async def test_list_genres_returns_seeded_list(client, test_db):
    """GET /api/genres/ returns all seeded TMDB genres sorted by name."""
    # Seed a few genres directly
    await test_db.genres.insert_many([
        {"id": 28, "name": "Action"},
        {"id": 35, "name": "Comedy"},
        {"id": 18, "name": "Drama"},
    ])

    response = await client.get("/api/genres/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Verify sorted alphabetically
    names = [g["name"] for g in data]
    assert names == sorted(names)

    # Verify structure
    for genre in data:
        assert "id" in genre
        assert "name" in genre
        assert isinstance(genre["id"], int)
        assert isinstance(genre["name"], str)


async def test_list_genres_empty(client):
    """GET /api/genres/ returns empty list when no genres exist."""
    response = await client.get("/api/genres/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_genres_sorted_alphabetically(client, test_db):
    """Genres are returned in alphabetical order by name."""
    await test_db.genres.insert_many([
        {"id": 37, "name": "Western"},
        {"id": 28, "name": "Action"},
        {"id": 53, "name": "Thriller"},
    ])

    response = await client.get("/api/genres/")

    assert response.status_code == 200
    names = [g["name"] for g in response.json()]
    assert names == ["Action", "Thriller", "Western"]

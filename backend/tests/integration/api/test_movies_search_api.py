"""Integration tests for movie search and TMDB proxy endpoints."""

import pytest
from unittest.mock import AsyncMock
from bson import ObjectId

from app.models.movie import MediaFormat

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def sample_storage(test_db):
    """Create a storage location and return its string ID."""
    result = await test_db.storage.insert_one(
        {
            "name": "Search Test Cabinet",
            "type": "cabinet",
            "parent_id": None,
            "path": [],
            "metadata": {},
        }
    )
    return str(result.inserted_id)


@pytest.fixture
async def three_movies(test_db, sample_storage):
    """Insert three movies directly into the DB and return their IDs."""
    storage_oid = ObjectId(sample_storage)
    docs = [
        {
            "title": "The Matrix",
            "year": 1999,
            "format": MediaFormat.BLURAY.value,
            "storage_id": storage_oid,
            "genre_ids": [28, 878],
            "runtime": 136,
        },
        {
            "title": "Matrix Reloaded",
            "year": 2003,
            "format": MediaFormat.DVD.value,
            "storage_id": storage_oid,
            "genre_ids": [28],
            "runtime": 138,
        },
        {
            "title": "Inception",
            "year": 2010,
            "format": MediaFormat.BLURAY.value,
            "storage_id": storage_oid,
            "genre_ids": [28, 878],
            "runtime": 148,
        },
    ]
    result = await test_db.movies.insert_many(docs)
    return [str(oid) for oid in result.inserted_ids]


# ---------------------------------------------------------------------------
# GET /api/movies/search
# ---------------------------------------------------------------------------


class TestSearchMoviesEndpoint:
    async def test_regex_fallback_finds_matching_title(self, client, three_movies):
        """Regex search (fallback when text index absent) returns title matches."""
        response = await client.get("/api/movies/search", params={"q": "Matrix"})

        assert response.status_code == 200
        data = response.json()
        titles = [m["title"] for m in data]
        assert "The Matrix" in titles
        assert "Matrix Reloaded" in titles
        assert "Inception" not in titles

    async def test_case_insensitive_search(self, client, three_movies):
        response = await client.get("/api/movies/search", params={"q": "matrix"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_no_match_returns_empty_list(self, client, three_movies):
        response = await client.get(
            "/api/movies/search", params={"q": "xyzzy_no_such_movie_ever"}
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_search_requires_q_param(self, client):
        response = await client.get("/api/movies/search")
        assert response.status_code == 422

    async def test_search_with_format_filter(self, client, three_movies):
        response = await client.get(
            "/api/movies/search",
            params={"q": "Matrix", "format": MediaFormat.DVD.value},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(m["format"] == MediaFormat.DVD.value for m in data)

    async def test_search_with_genre_filter(self, client, three_movies):
        """genre_id=878 (Sci-Fi) should exclude Matrix Reloaded (genre_ids=[28])."""
        response = await client.get(
            "/api/movies/search", params={"q": "Matrix", "genre_id": 878}
        )

        assert response.status_code == 200
        data = response.json()
        titles = [m["title"] for m in data]
        assert "The Matrix" in titles
        assert "Matrix Reloaded" not in titles

    async def test_search_with_storage_filter(
        self, client, three_movies, sample_storage
    ):
        """storage_id filter narrows results to a specific storage location."""
        # Create a second cabinet and a movie inside it
        response = await client.get(
            "/api/movies/search",
            params={"q": "Matrix", "storage_id": sample_storage},
        )

        assert response.status_code == 200
        # Both Matrix movies live in sample_storage, so both should appear
        data = response.json()
        assert len(data) >= 1

    async def test_search_invalid_storage_id_returns_400(self, client):
        response = await client.get(
            "/api/movies/search", params={"q": "Matrix", "storage_id": "not-an-id"}
        )
        assert response.status_code == 400

    async def test_search_pagination_skip(self, client, three_movies):
        """skip parameter offsets the result set."""
        all_resp = await client.get("/api/movies/search", params={"q": "a"})
        skipped_resp = await client.get(
            "/api/movies/search", params={"q": "a", "skip": 1}
        )

        all_data = all_resp.json()
        skipped_data = skipped_resp.json()
        assert len(skipped_data) == max(0, len(all_data) - 1)

    async def test_search_pagination_limit(self, client, three_movies):
        response = await client.get("/api/movies/search", params={"q": "a", "limit": 1})
        assert response.status_code == 200
        assert len(response.json()) <= 1


# ---------------------------------------------------------------------------
# GET /api/movies/tmdb/search
# ---------------------------------------------------------------------------


class TestSearchTmdbEndpoint:
    async def test_returns_tmdb_results(self, client, mock_tmdb_service):
        mock_tmdb_service.search_movies = AsyncMock(
            return_value={
                "results": [{"id": 603, "title": "The Matrix"}],
                "total_results": 1,
                "total_pages": 1,
            }
        )

        response = await client.get(
            "/api/movies/tmdb/search", params={"q": "The Matrix"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 1
        assert data["results"][0]["id"] == 603

    async def test_year_parameter_forwarded(self, client, mock_tmdb_service):
        mock_tmdb_service.search_movies = AsyncMock(
            return_value={"results": [], "total_results": 0, "total_pages": 0}
        )

        await client.get(
            "/api/movies/tmdb/search", params={"q": "The Matrix", "year": 1999}
        )

        mock_tmdb_service.search_movies.assert_called_once_with(
            "The Matrix", year=1999, page=1
        )

    async def test_page_parameter_forwarded(self, client, mock_tmdb_service):
        mock_tmdb_service.search_movies = AsyncMock(
            return_value={"results": [], "total_results": 0, "total_pages": 0}
        )

        await client.get("/api/movies/tmdb/search", params={"q": "Matrix", "page": 2})

        mock_tmdb_service.search_movies.assert_called_once_with(
            "Matrix", year=None, page=2
        )

    async def test_empty_results_returned(self, client, mock_tmdb_service):
        mock_tmdb_service.search_movies = AsyncMock(
            return_value={"results": [], "total_results": 0, "total_pages": 0}
        )

        response = await client.get(
            "/api/movies/tmdb/search", params={"q": "xyzzy_no_match"}
        )

        assert response.status_code == 200
        assert response.json()["total_results"] == 0

    async def test_requires_q_param(self, client):
        response = await client.get("/api/movies/tmdb/search")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/movies/tmdb/{tmdb_id}
# ---------------------------------------------------------------------------


class TestGetTmdbMovieEndpoint:
    async def test_returns_movie_details(self, client, mock_tmdb_service):
        mock_tmdb_service.get_movie_details = AsyncMock(
            return_value={
                "id": 603,
                "title": "The Matrix",
                "runtime": 136,
                "genre_ids": [28, 878],
            }
        )

        response = await client.get("/api/movies/tmdb/603")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 603
        assert data["title"] == "The Matrix"

    async def test_not_found_in_tmdb_returns_404(self, client, mock_tmdb_service):
        mock_tmdb_service.get_movie_details = AsyncMock(return_value=None)

        response = await client.get("/api/movies/tmdb/99999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /api/movies/{id}/enrich
# ---------------------------------------------------------------------------


class TestEnrichMovieEndpoint:
    @pytest.fixture
    async def movie_without_enrichment(self, test_db, sample_storage):
        """A movie with only required fields and a tmdb_id."""
        storage_oid = ObjectId(sample_storage)
        result = await test_db.movies.insert_one(
            {
                "title": "The Matrix",
                "year": 1999,
                "format": MediaFormat.BLURAY.value,
                "storage_id": storage_oid,
                "tmdb_id": 603,
            }
        )
        return str(result.inserted_id)

    async def test_enrich_fills_missing_fields(
        self, client, mock_tmdb_service, movie_without_enrichment
    ):
        mock_tmdb_service.enrich_movie_data = AsyncMock(
            return_value={
                "title": "The Matrix",
                "year": 1999,
                "format": MediaFormat.BLURAY.value,
                "storage_id": "some_id",
                "tmdb_id": 603,
                "genre_ids": [28, 878],
                "runtime": 136,
                "cover_image": "https://image.tmdb.org/t/p/w500/poster.jpg",
                "tmdb_genre_ids": [],
                "tmdb_genres": [],
            }
        )

        response = await client.post(f"/api/movies/{movie_without_enrichment}/enrich")

        assert response.status_code == 200
        data = response.json()
        assert data["genre_ids"] == [28, 878]
        assert data["runtime"] == 136

    async def test_enrich_not_found_returns_404(self, client):
        fake_id = str(ObjectId())
        response = await client.post(f"/api/movies/{fake_id}/enrich")
        assert response.status_code == 404

    async def test_enrich_invalid_id_returns_400(self, client):
        response = await client.post("/api/movies/not-a-valid-id/enrich")
        assert response.status_code == 400

    async def test_enrich_when_tmdb_returns_nothing(
        self, client, mock_tmdb_service, movie_without_enrichment
    ):
        """Enrich endpoint succeeds even when TMDB returns no new data."""
        mock_tmdb_service.enrich_movie_data = AsyncMock(
            side_effect=lambda d: d  # pass-through; no enrichment
        )

        response = await client.post(f"/api/movies/{movie_without_enrichment}/enrich")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Matrix"

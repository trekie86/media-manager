"""Unit tests for the TMDB service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx

from app.services.tmdb import TMDBService, TMDBServiceManager

TEST_API_KEY = "test_api_key_unit"


@pytest.fixture(autouse=True)
async def reset_singleton():
    """Reset TMDBServiceManager singleton state between tests."""
    yield
    if TMDBServiceManager._instance is not None:
        await TMDBServiceManager._instance.close()
    TMDBServiceManager._instance = None


@pytest.fixture
async def tmdb_service():
    """Create a TMDBService instance with a mocked HTTP client."""
    service = TMDBService(api_key=TEST_API_KEY)
    yield service
    await service.close()


# ---------------------------------------------------------------------------
# get_image_url
# ---------------------------------------------------------------------------


class TestGetImageUrl:
    def test_valid_path_returns_full_url(self, tmdb_service):
        url = tmdb_service.get_image_url("/poster.jpg")
        assert url == "https://image.tmdb.org/t/p/w500/poster.jpg"

    def test_custom_size_is_used(self, tmdb_service):
        url = tmdb_service.get_image_url("/backdrop.jpg", size="w1280")
        assert url == "https://image.tmdb.org/t/p/w1280/backdrop.jpg"

    def test_original_size(self, tmdb_service):
        url = tmdb_service.get_image_url("/poster.jpg", size="original")
        assert url == "https://image.tmdb.org/t/p/original/poster.jpg"

    def test_none_path_returns_none(self, tmdb_service):
        assert tmdb_service.get_image_url(None) is None

    def test_empty_string_returns_none(self, tmdb_service):
        assert tmdb_service.get_image_url("") is None


# ---------------------------------------------------------------------------
# search_movies
# ---------------------------------------------------------------------------


def _make_response(json_data):
    """Build a mock httpx response."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = json_data
    return mock_resp


@pytest.mark.asyncio
class TestSearchMovies:
    async def test_success_returns_results_with_image_urls(self, tmdb_service):
        """Successful search injects poster_url and backdrop_url into results."""
        tmdb_service.client.get = AsyncMock(
            return_value=_make_response(
                {
                    "results": [
                        {
                            "id": 603,
                            "title": "The Matrix",
                            "poster_path": "/poster.jpg",
                            "backdrop_path": "/backdrop.jpg",
                        }
                    ],
                    "total_results": 1,
                    "total_pages": 1,
                }
            )
        )

        result = await tmdb_service.search_movies("The Matrix")

        assert len(result["results"]) == 1
        movie = result["results"][0]
        assert movie["poster_url"] == "https://image.tmdb.org/t/p/w500/poster.jpg"
        assert movie["backdrop_url"] == "https://image.tmdb.org/t/p/w1280/backdrop.jpg"

    async def test_no_poster_does_not_set_poster_url(self, tmdb_service):
        """Results without poster_path do not get a poster_url key."""
        tmdb_service.client.get = AsyncMock(
            return_value=_make_response(
                {
                    "results": [{"id": 1, "title": "No Poster"}],
                    "total_results": 1,
                    "total_pages": 1,
                }
            )
        )

        result = await tmdb_service.search_movies("No Poster")

        assert "poster_url" not in result["results"][0]

    async def test_empty_results(self, tmdb_service):
        tmdb_service.client.get = AsyncMock(
            return_value=_make_response(
                {"results": [], "total_results": 0, "total_pages": 0}
            )
        )

        result = await tmdb_service.search_movies("xyzzy_no_match")

        assert result["results"] == []
        assert result["total_results"] == 0

    async def test_no_api_key_returns_empty_without_http_call(self):
        """Service without an API key short-circuits and returns empty results."""
        service = TMDBService(api_key=None)
        service.api_key = None  # ensure it's unset
        service.client.get = AsyncMock()  # should never be called

        result = await service.search_movies("The Matrix")

        service.client.get.assert_not_called()
        assert result == {"results": [], "total_results": 0, "total_pages": 0}
        await service.close()

    async def test_http_error_returns_empty_gracefully(self, tmdb_service):
        tmdb_service.client.get = AsyncMock(
            side_effect=httpx.HTTPError("Connection timed out")
        )

        result = await tmdb_service.search_movies("The Matrix")

        assert result == {"results": [], "total_results": 0, "total_pages": 0}

    async def test_year_parameter_forwarded_in_request(self, tmdb_service):
        tmdb_service.client.get = AsyncMock(
            return_value=_make_response(
                {"results": [], "total_results": 0, "total_pages": 0}
            )
        )

        await tmdb_service.search_movies("The Matrix", year=1999)

        params = tmdb_service.client.get.call_args[1]["params"]
        assert params["year"] == 1999

    async def test_page_parameter_forwarded_in_request(self, tmdb_service):
        tmdb_service.client.get = AsyncMock(
            return_value=_make_response(
                {"results": [], "total_results": 0, "total_pages": 0}
            )
        )

        await tmdb_service.search_movies("The Matrix", page=3)

        params = tmdb_service.client.get.call_args[1]["params"]
        assert params["page"] == 3


# ---------------------------------------------------------------------------
# get_movie_details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetMovieDetails:
    async def test_success_enriches_genres_and_images(self, tmdb_service):
        """get_movie_details extracts genre lists and builds image URLs."""
        tmdb_service.client.get = AsyncMock(
            return_value=_make_response(
                {
                    "id": 603,
                    "title": "The Matrix",
                    "poster_path": "/poster.jpg",
                    "backdrop_path": "/backdrop.jpg",
                    "genres": [
                        {"id": 28, "name": "Action"},
                        {"id": 878, "name": "Science Fiction"},
                    ],
                    "runtime": 136,
                    "production_companies": [{"name": "Warner Bros."}],
                }
            )
        )

        result = await tmdb_service.get_movie_details(603)

        assert result is not None
        assert result["poster_url"] == "https://image.tmdb.org/t/p/w500/poster.jpg"
        assert result["backdrop_url"] == "https://image.tmdb.org/t/p/w1280/backdrop.jpg"
        assert result["genre_ids"] == [28, 878]
        assert result["genre_names"] == ["Action", "Science Fiction"]
        assert result["production_company_names"] == ["Warner Bros."]

    async def test_404_returns_none(self, tmdb_service):
        """HTTP 404 from TMDB returns None without raising."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        error = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_resp
        )
        tmdb_service.client.get = AsyncMock(side_effect=error)

        result = await tmdb_service.get_movie_details(99999)

        assert result is None

    async def test_http_error_returns_none(self, tmdb_service):
        tmdb_service.client.get = AsyncMock(
            side_effect=httpx.HTTPError("Connection refused")
        )

        result = await tmdb_service.get_movie_details(603)

        assert result is None

    async def test_no_api_key_returns_none_without_http_call(self):
        service = TMDBService(api_key=None)
        service.api_key = None
        service.client.get = AsyncMock()

        result = await service.get_movie_details(603)

        service.client.get.assert_not_called()
        assert result is None
        await service.close()

    async def test_no_genres_in_response(self, tmdb_service):
        """Response without genres field does not set genre_ids."""
        tmdb_service.client.get = AsyncMock(
            return_value=_make_response(
                {"id": 1, "title": "Arthouse Film", "runtime": 90}
            )
        )

        result = await tmdb_service.get_movie_details(1)

        assert result is not None
        assert "genre_ids" not in result


# ---------------------------------------------------------------------------
# enrich_movie_data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestEnrichMovieData:
    async def test_enriches_missing_genre_ids_runtime_cover(self, tmdb_service):
        """enrich_movie_data fills in missing genre_ids, runtime, and cover_image."""
        tmdb_service.get_movie_details = AsyncMock(
            return_value={
                "genre_ids": [28, 878],
                "runtime": 136,
                "poster_url": "https://image.tmdb.org/t/p/w500/poster.jpg",
                "overview": "A sci-fi classic",
                "release_date": "1999-03-31",
                "vote_average": 8.7,
                "vote_count": 20000,
                "title": "The Matrix",
                "backdrop_url": None,
                "genre_names": ["Action", "Science Fiction"],
                "production_company_names": [],
            }
        )

        movie_data = {"title": "The Matrix", "tmdb_id": 603}
        result = await tmdb_service.enrich_movie_data(movie_data)

        assert result["genre_ids"] == [28, 878]
        assert result["runtime"] == 136
        assert result["cover_image"] == "https://image.tmdb.org/t/p/w500/poster.jpg"
        assert result["tmdb_title"] == "The Matrix"
        assert result["tmdb_rating"] == 8.7

    async def test_preserves_existing_user_values(self, tmdb_service):
        """Fields already set by the user are not overwritten."""
        tmdb_service.get_movie_details = AsyncMock(
            return_value={
                "genre_ids": [28],
                "runtime": 136,
                "poster_url": "https://image.tmdb.org/t/p/w500/tmdb.jpg",
                "overview": "...",
                "release_date": "1999-03-31",
                "vote_average": 8.0,
                "vote_count": 5000,
                "title": "The Matrix (TMDB)",
                "backdrop_url": None,
                "genre_names": ["Action"],
                "production_company_names": [],
            }
        )

        movie_data = {
            "title": "The Matrix",
            "tmdb_id": 603,
            "genre_ids": [99],
            "runtime": 200,
            "cover_image": "http://my.custom/poster.jpg",
        }
        result = await tmdb_service.enrich_movie_data(movie_data)

        assert result["genre_ids"] == [99]
        assert result["runtime"] == 200
        assert result["cover_image"] == "http://my.custom/poster.jpg"

    async def test_tmdb_returns_none_leaves_data_unchanged(self, tmdb_service):
        tmdb_service.get_movie_details = AsyncMock(return_value=None)

        movie_data = {"title": "Unknown Movie", "tmdb_id": 9999}
        result = await tmdb_service.enrich_movie_data(movie_data)

        assert result == movie_data

    async def test_no_tmdb_id_searches_by_title(self, tmdb_service):
        """Without tmdb_id, a title search is attempted."""
        tmdb_service.search_movies = AsyncMock(
            return_value={
                "results": [
                    {
                        "id": 603,
                        "title": "The Matrix",
                        "poster_url": None,
                        "overview": "A sci-fi movie",
                    }
                ],
                "total_results": 1,
            }
        )

        movie_data = {"title": "The Matrix"}
        result = await tmdb_service.enrich_movie_data(movie_data)

        assert result["suggested_tmdb_id"] == 603
        assert result["suggested_tmdb_title"] == "The Matrix"

    async def test_no_api_key_returns_data_unchanged(self):
        service = TMDBService(api_key=None)
        service.api_key = None

        movie_data = {"title": "The Matrix", "tmdb_id": 603}
        result = await service.enrich_movie_data(movie_data)

        assert result == movie_data
        await service.close()


# ---------------------------------------------------------------------------
# TMDBServiceManager singleton lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSingletonManager:
    async def test_initialize_creates_and_returns_instance(self):
        instance = await TMDBServiceManager.initialize(api_key=TEST_API_KEY)
        assert TMDBServiceManager._instance is instance
        assert isinstance(instance, TMDBService)

    async def test_get_instance_before_initialize_raises(self):
        assert TMDBServiceManager._instance is None
        with pytest.raises(RuntimeError, match="not initialized"):
            TMDBServiceManager.get_instance()

    async def test_get_instance_after_initialize_returns_same_object(self):
        instance = await TMDBServiceManager.initialize(api_key=TEST_API_KEY)
        assert TMDBServiceManager.get_instance() is instance

    async def test_cleanup_sets_instance_to_none(self):
        await TMDBServiceManager.initialize(api_key=TEST_API_KEY)
        await TMDBServiceManager.cleanup()
        assert TMDBServiceManager._instance is None

    async def test_reinitialize_closes_previous_instance(self):
        first = await TMDBServiceManager.initialize(api_key=TEST_API_KEY)
        first.close = AsyncMock()

        second = await TMDBServiceManager.initialize(api_key=TEST_API_KEY)

        first.close.assert_called_once()
        assert second is not first

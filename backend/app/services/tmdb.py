"""
TMDB (The Movie Database) API service for movie metadata enrichment.
"""

from typing import Optional, Dict, Any
import httpx
from loguru import logger

from ..core.config import settings


class TMDBService:
    """Service for interacting with The Movie Database API."""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize TMDB service with API key."""
        self.api_key = api_key or getattr(settings, "TMDB_API_KEY", None)
        if not self.api_key:
            logger.warning(
                "TMDB API key not configured. TMDB features will be disabled."
            )

        # Create a persistent HTTP client for better performance
        self.client = httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": "MediaManager/1.0"}
        )

    async def close(self):
        """Close the HTTP client. Call this when shutting down the application."""
        await self.client.aclose()

    def _build_url(self, endpoint: str) -> str:
        """Build full API URL with endpoint."""
        return f"{self.BASE_URL}/{endpoint.lstrip('/')}"

    def _build_params(self, **kwargs) -> Dict[str, Any]:
        """Build request parameters with API key."""
        params = {"api_key": self.api_key}
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return params

    def get_image_url(self, path: str, size: str = "w500") -> Optional[str]:
        """Get full image URL from TMDB image path."""
        if not path:
            return None
        return f"{self.IMAGE_BASE_URL}/{size}{path}"

    async def search_movies(
        self,
        query: str,
        year: Optional[int] = None,
        page: int = 1,
        include_adult: bool = False,
    ) -> Dict[str, Any]:
        """
        Search for movies by title.

        Args:
            query: Movie title to search for
            year: Optional release year to filter by
            page: Page number for pagination (default: 1)
            include_adult: Whether to include adult content (default: False)

        Returns:
            Dictionary containing search results and metadata
        """
        if not self.api_key:
            return {"results": [], "total_results": 0, "total_pages": 0}

        try:
            params = self._build_params(
                query=query, year=year, page=page, include_adult=include_adult
            )

            response = await self.client.get(
                self._build_url("/search/movie"), params=params
            )
            response.raise_for_status()

            data = response.json()

            # Enhance results with full image URLs
            for movie in data.get("results", []):
                if movie.get("poster_path"):
                    movie["poster_url"] = self.get_image_url(movie["poster_path"])
                if movie.get("backdrop_path"):
                    movie["backdrop_url"] = self.get_image_url(
                        movie["backdrop_path"], "w1280"
                    )

            return data

        except httpx.HTTPError as e:
            logger.error(f"TMDB API error during search: {e}")
            return {"results": [], "total_results": 0, "total_pages": 0}
        except Exception as e:
            logger.error(f"Unexpected error during TMDB search: {e}")
            return {"results": [], "total_results": 0, "total_pages": 0}

    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed movie information by TMDB ID.

        Args:
            tmdb_id: TMDB movie ID

        Returns:
            Dictionary containing detailed movie information or None if not found
        """
        if not self.api_key:
            return None

        try:
            params = self._build_params(
                append_to_response="credits,keywords,release_dates"
            )

            response = await self.client.get(
                self._build_url(f"/movie/{tmdb_id}"), params=params
            )
            response.raise_for_status()

            data = response.json()

            # Enhance with full image URLs
            if data.get("poster_path"):
                data["poster_url"] = self.get_image_url(data["poster_path"])
            if data.get("backdrop_path"):
                data["backdrop_url"] = self.get_image_url(
                    data["backdrop_path"], "w1280"
                )

            # Process genres into IDs and names
            if data.get("genres"):
                data["genre_ids"] = [genre["id"] for genre in data["genres"]]
                data["genre_names"] = [genre["name"] for genre in data["genres"]]

            # Process production companies
            if data.get("production_companies"):
                data["production_company_names"] = [
                    company["name"] for company in data["production_companies"]
                ]

            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"Movie with TMDB ID {tmdb_id} not found")
                return None
            logger.error(f"TMDB API error getting movie details: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"TMDB API error getting movie details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting TMDB movie details: {e}")
            return None

    async def enrich_movie_data(self, movie_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich movie data with TMDB information.

        Args:
            movie_data: Existing movie data dictionary

        Returns:
            Enhanced movie data with TMDB information
        """
        if not self.api_key:
            return movie_data

        enriched_data = movie_data.copy()

        # If we already have a TMDB ID, get detailed information
        if movie_data.get("tmdb_id"):
            details = await self.get_movie_details(movie_data["tmdb_id"])
            if details:
                # Update with TMDB data, preserving existing user data
                enriched_data.update(
                    {
                        "tmdb_title": details.get("title"),
                        "tmdb_overview": details.get("overview"),
                        "tmdb_release_date": details.get("release_date"),
                        "tmdb_runtime": details.get("runtime"),
                        "tmdb_rating": details.get("vote_average"),
                        "tmdb_vote_count": details.get("vote_count"),
                        "tmdb_poster_url": details.get("poster_url"),
                        "tmdb_backdrop_url": details.get("backdrop_url"),
                        "tmdb_genre_ids": details.get("genre_ids", []),
                        "tmdb_genres": details.get("genre_names", []),
                        "tmdb_production_companies": details.get(
                            "production_company_names", []
                        ),
                    }
                )

                # Update existing fields if they're empty
                if not enriched_data.get("genre_ids") and details.get("genre_ids"):
                    enriched_data["genre_ids"] = details["genre_ids"]

                if not enriched_data.get("runtime") and details.get("runtime"):
                    enriched_data["runtime"] = details["runtime"]

                if not enriched_data.get("cover_image") and details.get("poster_url"):
                    enriched_data["cover_image"] = details["poster_url"]

        # If no TMDB ID, try to find the movie by title
        elif movie_data.get("title"):
            search_results = await self.search_movies(movie_data["title"])
            if search_results.get("results"):
                # Take the first result as the best match
                best_match = search_results["results"][0]
                enriched_data["suggested_tmdb_id"] = best_match.get("id")
                enriched_data["suggested_tmdb_title"] = best_match.get("title")
                enriched_data["suggested_tmdb_poster"] = best_match.get("poster_url")
                enriched_data["suggested_tmdb_overview"] = best_match.get("overview")

        return enriched_data


class TMDBServiceManager:
    """Singleton manager for TMDB service instance."""

    _instance: Optional[TMDBService] = None

    @classmethod
    async def initialize(cls, api_key: Optional[str] = None) -> TMDBService:
        """Initialize the TMDB service. Call this during app startup."""
        if cls._instance is not None:
            await cls._instance.close()

        cls._instance = TMDBService(api_key)
        return cls._instance

    @classmethod
    async def cleanup(cls):
        """Cleanup TMDB service. Call this during app shutdown."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

    @classmethod
    def get_instance(cls) -> TMDBService:
        """Get the current TMDB service instance."""
        if cls._instance is None:
            raise RuntimeError(
                "TMDB service not initialized. "
                "Call TMDBServiceManager.initialize() first."
            )
        return cls._instance


def get_tmdb_service() -> TMDBService:
    """
    FastAPI dependency for TMDB service.

    Usage in API endpoints:
    @app.get("/movies/search-tmdb")
    async def search_tmdb(query: str, tmdb: TMDBService = Depends(get_tmdb_service)):
        return await tmdb.search_movies(query)
    """
    return TMDBServiceManager.get_instance()


# Convenience functions for backward compatibility
async def init_tmdb_service(api_key: Optional[str] = None) -> TMDBService:
    """Initialize the TMDB service. Call this during app startup."""
    return await TMDBServiceManager.initialize(api_key)


async def cleanup_tmdb_service():
    """Cleanup TMDB service. Call this during app shutdown."""
    await TMDBServiceManager.cleanup()

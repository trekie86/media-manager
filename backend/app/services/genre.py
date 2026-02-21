"""
Genre seeding and migration service.

Maintains the genres collection in sync with TMDB's canonical genre list
and migrates legacy string-based genre fields to integer IDs.
"""

from loguru import logger

# Canonical TMDB movie genre list (id → name).
# Source: https://api.themoviedb.org/3/genre/movie/list
TMDB_GENRES = [
    {"id": 28, "name": "Action"},
    {"id": 12, "name": "Adventure"},
    {"id": 16, "name": "Animation"},
    {"id": 35, "name": "Comedy"},
    {"id": 80, "name": "Crime"},
    {"id": 99, "name": "Documentary"},
    {"id": 18, "name": "Drama"},
    {"id": 10751, "name": "Family"},
    {"id": 14, "name": "Fantasy"},
    {"id": 36, "name": "History"},
    {"id": 27, "name": "Horror"},
    {"id": 10402, "name": "Music"},
    {"id": 9648, "name": "Mystery"},
    {"id": 10749, "name": "Romance"},
    {"id": 878, "name": "Science Fiction"},
    {"id": 10770, "name": "TV Movie"},
    {"id": 53, "name": "Thriller"},
    {"id": 10752, "name": "War"},
    {"id": 37, "name": "Western"},
]

# Case-insensitive lookup: lowercase name → id
_NAME_TO_ID = {g["name"].lower(): g["id"] for g in TMDB_GENRES}


async def seed_genres(db) -> None:
    """Upsert the canonical TMDB genre list into the genres collection."""
    for genre in TMDB_GENRES:
        await db.genres.update_one(
            {"id": genre["id"]},
            {"$setOnInsert": genre},
            upsert=True,
        )
    logger.info(f"Seeded {len(TMDB_GENRES)} TMDB genres into genres collection")


async def upsert_genres(db, genres: list[dict]) -> None:
    """
    Upsert a list of {id, name} genre dicts discovered from a TMDB response.
    Used during movie enrichment to auto-discover any new genres.
    """
    for genre in genres:
        await db.genres.update_one(
            {"id": genre["id"]},
            {"$setOnInsert": genre},
            upsert=True,
        )


async def migrate_string_genres(db) -> None:
    """
    One-time migration: convert movies with genre: [str] to genre_ids: [int].

    Movies that already have genre_ids set are skipped. After conversion the
    legacy 'genre' field is removed from each document.
    """
    migrated = 0
    skipped = 0

    cursor = db.movies.find({"genre": {"$exists": True}})
    async for movie in cursor:
        # Already migrated
        if "genre_ids" in movie:
            skipped += 1
            continue

        genre_list = movie.get("genre") or []

        # If the list is empty just clean up the old field
        if not genre_list:
            await db.movies.update_one(
                {"_id": movie["_id"]},
                {"$unset": {"genre": ""}},
            )
            migrated += 1
            continue

        # Guard: if items are already ints the field was written by new code
        if isinstance(genre_list[0], int):
            skipped += 1
            continue

        genre_ids = []
        for name in genre_list:
            matched_id = _NAME_TO_ID.get(name.lower())
            if matched_id is not None:
                genre_ids.append(matched_id)
            else:
                logger.warning(
                    f"Could not map genre name '{name}' to a TMDB ID "
                    f"(movie _id={movie['_id']}); skipping that genre"
                )

        await db.movies.update_one(
            {"_id": movie["_id"]},
            {
                "$set": {"genre_ids": genre_ids},
                "$unset": {"genre": ""},
            },
        )
        migrated += 1

    logger.info(
        f"Genre migration complete: {migrated} movies updated, {skipped} skipped"
    )

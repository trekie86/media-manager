"""Unit tests for the genre seeding and migration service."""

import pytest

from app.services.genre import (
    TMDB_GENRES,
    seed_genres,
    upsert_genres,
    migrate_string_genres,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# seed_genres
# ---------------------------------------------------------------------------


class TestSeedGenres:
    async def test_inserts_all_canonical_genres(self, test_db):
        await seed_genres(test_db)

        count = await test_db.genres.count_documents({})
        assert count == len(TMDB_GENRES)

    async def test_seeded_genres_have_correct_fields(self, test_db):
        await seed_genres(test_db)

        action = await test_db.genres.find_one({"id": 28})
        assert action is not None
        assert action["name"] == "Action"

    async def test_seed_is_idempotent(self, test_db):
        """Running seed twice must not create duplicate documents."""
        await seed_genres(test_db)
        await seed_genres(test_db)

        count = await test_db.genres.count_documents({})
        assert count == len(TMDB_GENRES)

    async def test_seed_does_not_overwrite_existing_names(self, test_db):
        """$setOnInsert means a pre-existing document is untouched."""
        await test_db.genres.insert_one({"id": 28, "name": "CustomName"})

        await seed_genres(test_db)

        doc = await test_db.genres.find_one({"id": 28})
        assert doc["name"] == "CustomName"


# ---------------------------------------------------------------------------
# upsert_genres
# ---------------------------------------------------------------------------


class TestUpsertGenres:
    async def test_inserts_new_genres(self, test_db):
        genres = [{"id": 9001, "name": "Test Genre"}]
        await upsert_genres(test_db, genres)

        doc = await test_db.genres.find_one({"id": 9001})
        assert doc is not None
        assert doc["name"] == "Test Genre"

    async def test_skips_existing_genres(self, test_db):
        """Upserting a genre that already exists does not change the name."""
        await test_db.genres.insert_one({"id": 28, "name": "Action"})

        await upsert_genres(test_db, [{"id": 28, "name": "ShouldNotReplace"}])

        doc = await test_db.genres.find_one({"id": 28})
        assert doc["name"] == "Action"

    async def test_empty_list_is_a_noop(self, test_db):
        await upsert_genres(test_db, [])
        count = await test_db.genres.count_documents({})
        assert count == 0

    async def test_multiple_genres_inserted(self, test_db):
        genres = [{"id": 9001, "name": "Genre A"}, {"id": 9002, "name": "Genre B"}]
        await upsert_genres(test_db, genres)

        count = await test_db.genres.count_documents({"id": {"$in": [9001, 9002]}})
        assert count == 2


# ---------------------------------------------------------------------------
# migrate_string_genres
# ---------------------------------------------------------------------------


class TestMigrateStringGenres:
    async def test_migrates_known_genres_to_ids(self, test_db):
        """String genre names are converted to TMDB integer IDs."""
        await test_db.movies.insert_one(
            {"title": "Test Movie", "genre": ["Action", "Comedy"]}
        )

        await migrate_string_genres(test_db)

        movie = await test_db.movies.find_one({"title": "Test Movie"})
        assert movie["genre_ids"] == [28, 35]
        assert "genre" not in movie

    async def test_removes_legacy_genre_field(self, test_db):
        await test_db.movies.insert_one(
            {"title": "Clean Me", "genre": ["Drama"]}
        )

        await migrate_string_genres(test_db)

        movie = await test_db.movies.find_one({"title": "Clean Me"})
        assert "genre" not in movie

    async def test_skips_movies_already_having_genre_ids(self, test_db):
        """Movies with genre_ids set are not re-processed."""
        await test_db.movies.insert_one(
            {"title": "Already Migrated", "genre": ["Drama"], "genre_ids": [18]}
        )

        await migrate_string_genres(test_db)

        movie = await test_db.movies.find_one({"title": "Already Migrated"})
        # genre_ids must remain as originally set
        assert movie["genre_ids"] == [18]
        # genre field is kept (the doc was skipped, not modified)
        assert "genre" in movie

    async def test_skips_movies_with_int_genres(self, test_db):
        """Movies whose genre list already contains ints are skipped."""
        await test_db.movies.insert_one(
            {"title": "New Code Movie", "genre": [28, 35]}
        )

        await migrate_string_genres(test_db)

        movie = await test_db.movies.find_one({"title": "New Code Movie"})
        # genre field must not be removed (document was skipped)
        assert "genre" in movie

    async def test_empty_genre_list_removes_field_only(self, test_db):
        """Movies with an empty genre list get the field removed without setting genre_ids."""
        await test_db.movies.insert_one({"title": "No Genres", "genre": []})

        await migrate_string_genres(test_db)

        movie = await test_db.movies.find_one({"title": "No Genres"})
        assert "genre" not in movie
        assert "genre_ids" not in movie

    async def test_unknown_genre_name_is_skipped_gracefully(self, test_db):
        """Unknown genre names do not crash the migration; they are omitted."""
        await test_db.movies.insert_one(
            {"title": "Weird Movie", "genre": ["Action", "MadeUpGenre"]}
        )

        await migrate_string_genres(test_db)

        movie = await test_db.movies.find_one({"title": "Weird Movie"})
        # Action (28) is mapped; MadeUpGenre is silently dropped
        assert movie["genre_ids"] == [28]

    async def test_no_genre_field_movies_are_ignored(self, test_db):
        """Movies without the legacy genre field are completely unaffected."""
        await test_db.movies.insert_one(
            {"title": "Modern Movie", "genre_ids": [28]}
        )

        await migrate_string_genres(test_db)

        movie = await test_db.movies.find_one({"title": "Modern Movie"})
        assert movie["genre_ids"] == [28]

"""Unit tests for the BaseRepository generic CRUD layer."""

import pytest
import inspect
from bson import ObjectId

from app.db.base import BaseRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def repo(test_db):
    """Return a BaseRepository wired to an isolated test collection."""
    return BaseRepository(test_db["test_base_repo"])


# ---------------------------------------------------------------------------
# find_one
# ---------------------------------------------------------------------------


class TestFindOne:
    async def test_returns_matching_document(self, repo):
        await repo.collection.insert_one({"name": "alpha", "value": 1})

        result = await repo.find_one({"name": "alpha"})

        assert result is not None
        assert result["value"] == 1

    async def test_returns_none_when_no_match(self, repo):
        result = await repo.find_one({"name": "nonexistent"})
        assert result is None


# ---------------------------------------------------------------------------
# find_many
# ---------------------------------------------------------------------------


class TestFindMany:
    async def test_returns_all_matching_documents(self, repo):
        await repo.collection.insert_many([{"cat": "a"}, {"cat": "a"}, {"cat": "b"}])

        results = await repo.find_many({"cat": "a"})

        assert len(results) == 2

    async def test_skip_offsets_results(self, repo):
        await repo.collection.insert_many([{"seq": 1}, {"seq": 2}, {"seq": 3}])

        results = await repo.find_many({}, skip=1, limit=10)

        assert len(results) == 2

    async def test_limit_caps_results(self, repo):
        await repo.collection.insert_many([{"n": i} for i in range(10)])

        results = await repo.find_many({}, limit=3)

        assert len(results) == 3

    async def test_sort_orders_results(self, repo):
        await repo.collection.insert_many([{"val": 3}, {"val": 1}, {"val": 2}])

        results = await repo.find_many({}, sort=[("val", 1)])

        values = [r["val"] for r in results]
        assert values == [1, 2, 3]

    async def test_returns_empty_list_when_no_match(self, repo):
        results = await repo.find_many({"nonexistent_key": True})
        assert results == []


# ---------------------------------------------------------------------------
# insert_one
# ---------------------------------------------------------------------------


class TestInsertOne:
    async def test_returns_string_id(self, repo):
        inserted_id = await repo.insert_one({"name": "beta"})

        assert isinstance(inserted_id, str)
        # Must be a valid ObjectId string
        assert ObjectId.is_valid(inserted_id)

    async def test_document_is_persisted(self, repo):
        inserted_id = await repo.insert_one({"name": "gamma"})

        doc = await repo.collection.find_one({"_id": ObjectId(inserted_id)})
        assert doc is not None
        assert doc["name"] == "gamma"


# ---------------------------------------------------------------------------
# insert_many
# ---------------------------------------------------------------------------


class TestInsertMany:
    async def test_returns_list_of_string_ids(self, repo):
        ids = await repo.insert_many([{"x": 1}, {"x": 2}, {"x": 3}])

        assert len(ids) == 3
        assert all(isinstance(i, str) for i in ids)
        assert all(ObjectId.is_valid(i) for i in ids)

    async def test_all_documents_persisted(self, repo):
        ids = await repo.insert_many([{"tag": "bulk"}, {"tag": "bulk"}])

        count = await repo.collection.count_documents({"tag": "bulk"})
        assert count == 2


# ---------------------------------------------------------------------------
# update_one
# ---------------------------------------------------------------------------


class TestUpdateOne:
    async def test_updates_matching_document(self, repo):
        await repo.collection.insert_one({"k": "original"})

        await repo.update_one({"k": "original"}, {"k": "updated"})

        doc = await repo.find_one({"k": "updated"})
        assert doc is not None

    async def test_upsert_creates_document_when_missing(self, repo):
        await repo.update_one({"k": "new_key"}, {"k": "new_key", "v": 42}, upsert=True)

        doc = await repo.find_one({"k": "new_key"})
        assert doc is not None
        assert doc["v"] == 42

    async def test_no_upsert_does_not_create_document(self, repo):
        await repo.update_one({"k": "ghost"}, {"k": "ghost"}, upsert=False)

        doc = await repo.find_one({"k": "ghost"})
        assert doc is None


# ---------------------------------------------------------------------------
# delete_one / delete_many
# ---------------------------------------------------------------------------


class TestDeleteOne:
    async def test_deletes_single_matching_document(self, repo):
        await repo.collection.insert_many([{"tag": "del"}, {"tag": "del"}])

        result = await repo.delete_one({"tag": "del"})

        assert result.deleted_count == 1
        remaining = await repo.collection.count_documents({"tag": "del"})
        assert remaining == 1

    async def test_returns_zero_when_no_match(self, repo):
        result = await repo.delete_one({"tag": "ghost"})
        assert result.deleted_count == 0


class TestDeleteMany:
    async def test_deletes_all_matching_documents(self, repo):
        await repo.collection.insert_many(
            [{"tag": "batch"}, {"tag": "batch"}, {"tag": "keep"}]
        )

        result = await repo.delete_many({"tag": "batch"})

        assert result.deleted_count == 2
        assert await repo.collection.count_documents({"tag": "keep"}) == 1


# ---------------------------------------------------------------------------
# count
# ---------------------------------------------------------------------------


class TestCount:
    async def test_returns_correct_count(self, repo):
        await repo.collection.insert_many([{"grp": "x"}, {"grp": "x"}, {"grp": "y"}])

        count = await repo.count({"grp": "x"})

        assert count == 2

    async def test_returns_zero_for_empty_collection(self, repo):
        assert await repo.count({}) == 0


# ---------------------------------------------------------------------------
# get_by_id — known defect documentation
# ---------------------------------------------------------------------------


class TestGetById:
    def test_get_by_id_is_synchronous_and_returns_coroutine(self, repo):
        """
        Known defect: BaseRepository.get_by_id() is declared as a plain (sync)
        method but internally calls the async find_one().  The result is an
        unawaited coroutine, not the actual document.

        This test documents the current (incorrect) behaviour so that any future
        fix that makes the method properly async will also update this test.
        """
        fake_id = str(ObjectId())
        result = repo.get_by_id(fake_id)

        # The returned value is a coroutine, not None or a dict
        assert inspect.iscoroutine(result), (
            "get_by_id() should be 'async def' — it currently returns a coroutine "
            "instead of awaiting find_one(). Fix: change to 'async def get_by_id' "
            "and 'return await self.find_one(...)'"
        )
        # Close the coroutine to avoid ResourceWarning
        result.close()

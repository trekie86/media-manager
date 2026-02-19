"""
Unit tests for the _build_storage_filter helper in movies API.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.api.movies import _build_storage_filter, _MAX_STORAGE_DESCENDANTS

pytestmark = pytest.mark.unit


@pytest.fixture
def storage_oid():
    return ObjectId()


def _make_db(descendants: list) -> MagicMock:
    """Return a minimal mock db whose storage.find().to_list() returns *descendants*."""
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=descendants)
    db = MagicMock()
    db.storage.find.return_value = cursor
    return db


# ── include_descendants=False ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_descendants_returns_exact_match(storage_oid):
    """Without include_descendants, filter is a simple equality on storage_id."""
    db = MagicMock()
    result = await _build_storage_filter(db, storage_oid, include_descendants=False)

    assert result == {"storage_id": storage_oid}
    db.storage.find.assert_not_called()


# ── include_descendants=True ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_with_descendants_includes_self_and_children(storage_oid):
    """With include_descendants, result contains the node and all descendants."""
    child1 = ObjectId()
    child2 = ObjectId()
    db = _make_db([{"_id": child1}, {"_id": child2}])

    result = await _build_storage_filter(db, storage_oid, include_descendants=True)

    assert result == {"storage_id": {"$in": [storage_oid, child1, child2]}}
    db.storage.find.assert_called_once_with({"path": storage_oid}, {"_id": 1})
    db.storage.find.return_value.to_list.assert_called_once_with(
        length=_MAX_STORAGE_DESCENDANTS
    )


@pytest.mark.asyncio
async def test_with_descendants_leaf_node_includes_only_self(storage_oid):
    """A leaf node with no descendants returns $in with just itself."""
    db = _make_db([])

    result = await _build_storage_filter(db, storage_oid, include_descendants=True)

    assert result == {"storage_id": {"$in": [storage_oid]}}


@pytest.mark.asyncio
async def test_descendant_query_uses_materialized_path(storage_oid):
    """Descendant lookup queries the materialized path field, not parent_id."""
    db = _make_db([])

    await _build_storage_filter(db, storage_oid, include_descendants=True)

    # Must query {"path": storage_oid} — the materialized path index
    db.storage.find.assert_called_once_with({"path": storage_oid}, {"_id": 1})

"""Integration tests for storage routes."""

import pytest
from fastapi import status
from bson import ObjectId

from tests.helpers import assert_response, assert_error_response

pytestmark = pytest.mark.asyncio


async def test_create_storage_success(client, sample_storage_data):
    """Test successful storage creation."""
    # Make request
    response = await client.post("/api/storage", json=sample_storage_data)

    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_201_CREATED,
    )

    # Verify response data
    data = response.json()
    assert data["name"] == sample_storage_data["name"]
    assert data["type"] == sample_storage_data["type"]
    assert data["description"] == sample_storage_data["description"]
    assert "id" in data
    assert data["path"] == []
    assert data["parent_id"] is None


async def test_create_storage_duplicate_name(client, sample_storage_data):
    """Test creating storage with duplicate name fails."""
    # Create first storage
    response = await client.post("/api/storage", json=sample_storage_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Try to create duplicate
    response = await client.post("/api/storage", json=sample_storage_data)

    # Assert error response
    assert_error_response(
        response,
        expected_status_code=status.HTTP_400_BAD_REQUEST,
        expected_detail="Storage name already exists",
    )


async def test_create_storage_with_parent(client, sample_storage_data):
    """Test creating storage with a parent reference."""
    # Create parent storage
    parent_response = await client.post("/api/storage", json=sample_storage_data)
    assert parent_response.status_code == status.HTTP_201_CREATED
    parent_id = parent_response.json()["id"]

    # Create child storage
    child_data = {
        "name": "Child Storage",
        "description": "A child storage",
        "type": "shelf",
        "parent_id": parent_id,
        "metadata": {"capacity": 50},
    }

    response = await client.post("/api/storage", json=child_data)

    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_201_CREATED,
    )

    # Verify response data
    data = response.json()
    assert data["name"] == child_data["name"]
    assert data["parent_id"] == parent_id
    assert data["path"] == [parent_id]


async def test_create_storage_invalid_parent(client, sample_storage_data):
    """Test creating storage with invalid parent ID fails."""
    # Create data with non-existent parent
    invalid_parent_data = {
        **sample_storage_data,
        "parent_id": str(ObjectId()),  # Random ObjectId
    }

    response = await client.post("/api/storage", json=invalid_parent_data)

    # Assert error response
    assert_error_response(
        response,
        expected_status_code=status.HTTP_404_NOT_FOUND,
        expected_detail="Parent storage location not found",
    )


async def test_list_storage(client, sample_storage_data):
    """Test listing storage locations."""
    # Create multiple storage items
    storage_items = [
        sample_storage_data,
        {
            "name": "Second Cabinet",
            "description": "Another cabinet",
            "type": "cabinet",
            "metadata": {"capacity": 200},
        },
        {
            "name": "Drawer Unit",
            "description": "A drawer unit",
            "type": "drawer",
            "metadata": {"capacity": 50},
        },
    ]

    for item in storage_items:
        response = await client.post("/api/storage", json=item)
        assert response.status_code == status.HTTP_201_CREATED

    # Test listing all storage
    response = await client.get("/api/storage")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3

    # Test filtering by type
    response = await client.get("/api/storage?type=cabinet")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(item["type"] == "cabinet" for item in data)

    # Test filtering by parent_id
    # First, create a child storage
    parent_id = data[0]["id"]
    child_data = {
        "name": "Child Shelf",
        "description": "A shelf in cabinet",
        "type": "shelf",
        "parent_id": parent_id,
    }
    response = await client.post("/api/storage", json=child_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Now filter by parent_id
    response = await client.get(f"/api/storage?parent_id={parent_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Child Shelf"
    assert data[0]["parent_id"] == parent_id


async def test_get_storage_by_id(client, sample_storage_data):
    """Test getting a specific storage location by ID."""
    # Create a storage item
    response = await client.post("/api/storage", json=sample_storage_data)
    assert response.status_code == status.HTTP_201_CREATED
    storage_id = response.json()["id"]

    # Get the storage by ID
    response = await client.get(f"/api/storage/{storage_id}")

    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_200_OK,
    )

    # Verify response data
    data = response.json()
    assert data["id"] == storage_id
    assert data["name"] == sample_storage_data["name"]
    assert "movies" in data
    assert "children" in data


async def test_get_storage_not_found(client):
    """Test getting a non-existent storage returns 404."""
    non_existent_id = str(ObjectId())
    response = await client.get(f"/api/storage/{non_existent_id}")

    # Assert error response
    assert_error_response(
        response,
        expected_status_code=status.HTTP_404_NOT_FOUND,
        expected_detail="Storage location not found",
    )


async def test_get_storage_tree(client, sample_storage_data):
    """Test getting a storage tree with ancestors and descendants."""
    # Create a root storage
    root_response = await client.post("/api/storage", json=sample_storage_data)
    assert root_response.status_code == status.HTTP_201_CREATED
    root_id = root_response.json()["id"]

    # Create a child storage
    child_data = {
        "name": "Child Shelf",
        "description": "A shelf in cabinet",
        "type": "shelf",
        "parent_id": root_id,
    }
    child_response = await client.post("/api/storage", json=child_data)
    assert child_response.status_code == status.HTTP_201_CREATED
    child_id = child_response.json()["id"]

    # Create a grandchild storage
    grandchild_data = {
        "name": "Grandchild Bin",
        "description": "A bin on the shelf",
        "type": "bin",
        "parent_id": child_id,
    }
    grandchild_response = await client.post("/api/storage", json=grandchild_data)
    assert grandchild_response.status_code == status.HTTP_201_CREATED
    grandchild_id = grandchild_response.json()["id"]

    # Get the tree for the child
    response = await client.get(f"/api/storage/{child_id}/tree")

    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_200_OK,
    )

    # Verify tree structure
    data = response.json()
    assert data["id"] == child_id
    assert len(data["ancestors"]) == 1
    assert data["ancestors"][0]["id"] == root_id
    assert len(data["descendants"]) == 1
    assert data["descendants"][0]["id"] == grandchild_id
    assert len(data["children"]) == 1
    assert data["children"][0]["id"] == grandchild_id


async def test_update_storage(client, sample_storage_data):
    """Test updating a storage location."""
    # Create a storage item
    response = await client.post("/api/storage", json=sample_storage_data)
    assert response.status_code == status.HTTP_201_CREATED
    storage_id = response.json()["id"]

    # Update data
    update_data = {
        "name": "Updated Cabinet",
        "description": "Updated description",
        "metadata": {
            "capacity": 150,
            "dimensions": "150x75x250cm",
            "location": "Bedroom",
        },
    }

    # Update the storage
    response = await client.put(f"/api/storage/{storage_id}", json=update_data)

    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_200_OK,
    )

    # Verify updated data
    data = response.json()
    assert data["id"] == storage_id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["metadata"]["capacity"] == update_data["metadata"]["capacity"]
    assert data["metadata"]["dimensions"] == update_data["metadata"]["dimensions"]
    assert data["metadata"]["location"] == update_data["metadata"]["location"]


async def test_update_storage_parent(client, sample_storage_data):
    """Test updating a storage location's parent."""
    # Create two root storage items
    root1_response = await client.post("/api/storage", json=sample_storage_data)
    assert root1_response.status_code == status.HTTP_201_CREATED
    root1_id = root1_response.json()["id"]

    root2_data = {
        "name": "Second Cabinet",
        "description": "Another cabinet",
        "type": "cabinet",
    }
    root2_response = await client.post("/api/storage", json=root2_data)
    assert root2_response.status_code == status.HTTP_201_CREATED
    root2_id = root2_response.json()["id"]

    # Create a child under root1
    child_data = {
        "name": "Child Shelf",
        "description": "A shelf in cabinet",
        "type": "shelf",
        "parent_id": root1_id,
    }
    child_response = await client.post("/api/storage", json=child_data)
    assert child_response.status_code == status.HTTP_201_CREATED
    child_id = child_response.json()["id"]

    # Move child from root1 to root2
    update_data = {"parent_id": root2_id}
    response = await client.put(f"/api/storage/{child_id}", json=update_data)

    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_200_OK,
    )

    # Verify updated parent and path
    data = response.json()
    assert data["parent_id"] == root2_id
    assert data["path"] == [root2_id]

    # Verify child is now under root2
    response = await client.get(f"/api/storage?parent_id={root2_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == child_id


async def test_update_storage_invalid_parent_cycle(client, sample_storage_data):
    """Test updating a storage with invalid parent (would create cycle)."""
    # Create a root storage
    root_response = await client.post("/api/storage", json=sample_storage_data)
    assert root_response.status_code == status.HTTP_201_CREATED
    root_id = root_response.json()["id"]

    # Create a child storage
    child_data = {
        "name": "Child Shelf",
        "description": "A shelf in cabinet",
        "type": "shelf",
        "parent_id": root_id,
    }
    child_response = await client.post("/api/storage", json=child_data)
    assert child_response.status_code == status.HTTP_201_CREATED
    child_id = child_response.json()["id"]

    # Try to set child as parent of root (would create cycle)
    update_data = {"parent_id": child_id}
    response = await client.put(f"/api/storage/{root_id}", json=update_data)

    # Assert error response
    assert_error_response(
        response,
        expected_status_code=status.HTTP_400_BAD_REQUEST,
        expected_detail="Cannot set a descendant as parent (would create a cycle)",
    )


async def test_delete_storage(client, sample_storage_data):
    """Test deleting a storage location."""
    # Create a storage item
    response = await client.post("/api/storage", json=sample_storage_data)
    assert response.status_code == status.HTTP_201_CREATED
    storage_id = response.json()["id"]

    # Delete the storage
    response = await client.delete(f"/api/storage/{storage_id}")

    # Assert response
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify storage is deleted
    response = await client.get(f"/api/storage/{storage_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_storage_with_children(client, sample_storage_data):
    """Test deleting a storage with children fails."""
    # Create a root storage
    root_response = await client.post("/api/storage", json=sample_storage_data)
    assert root_response.status_code == status.HTTP_201_CREATED
    root_id = root_response.json()["id"]

    # Create a child storage
    child_data = {
        "name": "Child Shelf",
        "description": "A shelf in cabinet",
        "type": "shelf",
        "parent_id": root_id,
    }
    child_response = await client.post("/api/storage", json=child_data)
    assert child_response.status_code == status.HTTP_201_CREATED

    # Try to delete the root
    response = await client.delete(f"/api/storage/{root_id}")

    # Assert error response
    assert_error_response(
        response,
        expected_status_code=status.HTTP_400_BAD_REQUEST,
        expected_detail="Cannot delete storage with children. Delete children first.",
    )


# ---------------------------------------------------------------------------
# Cascading path updates when a node is moved to a new parent
# ---------------------------------------------------------------------------


async def test_move_node_updates_immediate_children_tree(client, sample_storage_data):
    """
    Moving a storage node to a new parent must be reflected in the tree view
    of the new parent — its descendants must include the moved node.
    """
    root_a = (
        await client.post(
            "/api/storage", json={**sample_storage_data, "name": "Root A"}
        )
    ).json()
    root_b = (
        await client.post(
            "/api/storage", json={**sample_storage_data, "name": "Root B"}
        )
    ).json()
    child = (
        await client.post(
            "/api/storage",
            json={
                "name": "Child Shelf",
                "type": "shelf",
                "parent_id": root_a["id"],
            },
        )
    ).json()

    # Move Child from Root A → Root B
    move_response = await client.put(
        f"/api/storage/{child['id']}", json={"parent_id": root_b["id"]}
    )
    assert move_response.status_code == status.HTTP_200_OK

    # Root B's tree must now contain Child as a descendant
    tree_b = (await client.get(f"/api/storage/{root_b['id']}/tree")).json()
    descendant_ids = [d["id"] for d in tree_b.get("descendants", [])]
    assert child["id"] in descendant_ids

    # Root A's tree must no longer contain Child
    tree_a = (await client.get(f"/api/storage/{root_a['id']}/tree")).json()
    descendant_ids_a = [d["id"] for d in tree_a.get("descendants", [])]
    assert child["id"] not in descendant_ids_a


async def test_move_node_deep_descendant_path_updated(client, sample_storage_data):
    """
    When a node with children is moved, all grandchildren must appear under
    the new location in the tree — verifying multi-level cascading path updates.
    """
    root_a = (
        await client.post(
            "/api/storage", json={**sample_storage_data, "name": "GrandRoot A"}
        )
    ).json()
    root_b = (
        await client.post(
            "/api/storage", json={**sample_storage_data, "name": "GrandRoot B"}
        )
    ).json()
    parent = (
        await client.post(
            "/api/storage",
            json={
                "name": "Parent Shelf",
                "type": "shelf",
                "parent_id": root_a["id"],
            },
        )
    ).json()
    grandchild = (
        await client.post(
            "/api/storage",
            json={
                "name": "Grandchild Bin",
                "type": "bin",
                "parent_id": parent["id"],
            },
        )
    ).json()

    # Move Parent (and implicitly Grandchild) from Root A → Root B
    move_response = await client.put(
        f"/api/storage/{parent['id']}", json={"parent_id": root_b["id"]}
    )
    assert move_response.status_code == status.HTTP_200_OK

    # Root B's tree must contain both Parent and Grandchild
    tree_b = (await client.get(f"/api/storage/{root_b['id']}/tree")).json()
    descendant_ids = [d["id"] for d in tree_b.get("descendants", [])]
    assert parent["id"] in descendant_ids
    assert grandchild["id"] in descendant_ids

    # Root A's tree must contain neither
    tree_a = (await client.get(f"/api/storage/{root_a['id']}/tree")).json()
    descendant_ids_a = [d["id"] for d in tree_a.get("descendants", [])]
    assert parent["id"] not in descendant_ids_a
    assert grandchild["id"] not in descendant_ids_a

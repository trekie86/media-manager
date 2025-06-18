"""
Unit tests for the Storage model.

This module tests the storage model's validation rules, including:
1. Basic field validation
2. Storage type enumeration
3. Tree structure validation (parent/path relationships)
4. Metadata validation for different storage types
5. Update model validation
6. Response model structure
"""
import pytest
from pydantic import ValidationError

from app.models.storage import (
    StorageBase, StorageType, StorageMetadata, StorageUpdate,
    StorageResponse, StorageTreeResponse
)

pytestmark = pytest.mark.unit

def test_create_storage_success(sample_storage_data):
    """Test creating a storage item with valid data."""
    storage = StorageBase(**sample_storage_data)
    assert storage.name == sample_storage_data["name"]
    assert storage.description == sample_storage_data["description"]
    assert storage.type == sample_storage_data["type"]
    # Compare metadata fields individually since we're comparing Pydantic model to dict
    assert storage.metadata.capacity == sample_storage_data["metadata"]["capacity"]
    assert storage.metadata.dimensions == sample_storage_data["metadata"]["dimensions"]
    assert storage.metadata.location == sample_storage_data["metadata"]["location"]

def test_storage_type_values():
    """Test that StorageType enum has the expected values."""
    assert StorageType.CABINET.value == "cabinet"
    assert StorageType.SHELF.value == "shelf"
    assert StorageType.BIN.value == "bin"
    assert StorageType.DRAWER.value == "drawer"
    
    # Test that these are the only valid values
    assert len(StorageType.__members__) == 4
    assert set(StorageType.__members__.keys()) == {"CABINET", "SHELF", "BIN", "DRAWER"}

def test_create_storage_invalid_type():
    """Test creating a storage with an invalid type."""
    invalid_data = {
        "name": "Test Storage",
        "description": "A test storage",
        "type": "invalid_type",  # Invalid type
        "metadata": {
            "capacity": 100,
            "dimensions": "100x50x200cm"
        }
    }
    with pytest.raises(ValidationError) as exc_info:
        StorageBase(**invalid_data)
    assert "type" in str(exc_info.value)

def test_create_storage_missing_required():
    """Test creating a storage with missing required fields."""
    invalid_data = {
        "description": "A test storage",
        "type": "cabinet"
        # Missing name field
    }
    with pytest.raises(ValidationError) as exc_info:
        StorageBase(**invalid_data)
    assert "name" in str(exc_info.value)

def test_create_storage_invalid_metadata():
    """Test creating a storage with invalid metadata."""
    invalid_data = {
        "name": "Test Storage",
        "description": "A test storage",
        "type": "cabinet",
        "metadata": {
            "capacity": -100,  # Invalid negative capacity
            "dimensions": "100x50x200cm"
        }
    }
    with pytest.raises(ValidationError) as exc_info:
        StorageBase(**invalid_data)
    assert "metadata" in str(exc_info.value)

def test_create_storage_with_parent():
    """Test creating a storage with a parent reference."""
    data = {
        "name": "Test Shelf",
        "description": "A test shelf",
        "type": "shelf",
        "parent_id": "507f1f77bcf86cd799439011",  # Example ObjectId
        "path": ["507f1f77bcf86cd799439011"],  # Path should include parent
        "metadata": {
            "capacity": 50
        }
    }
    storage = StorageBase(**data)
    assert storage.parent_id == data["parent_id"]
    assert storage.path == data["path"]

def test_create_storage_invalid_path():
    """Test creating a storage with an invalid path."""
    # Test empty path with parent_id
    invalid_data = {
        "name": "Test Shelf",
        "description": "A test shelf",
        "type": "shelf",
        "parent_id": "507f1f77bcf86cd799439011",
        "path": [],  # Empty path with parent_id is invalid
        "metadata": {
            "capacity": 50
        }
    }
    with pytest.raises(ValueError) as exc_info:
        StorageBase(**invalid_data)
    assert "Path cannot be empty when parent_id is set" in str(exc_info.value)

    # Test path without parent_id
    invalid_data = {
        "name": "Test Shelf",
        "description": "A test shelf",
        "type": "shelf",
        "parent_id": "507f1f77bcf86cd799439011",
        "path": ["different_id"],  # Path doesn't contain parent_id
        "metadata": {
            "capacity": 50
        }
    }
    with pytest.raises(ValueError) as exc_info:
        StorageBase(**invalid_data)
    assert "Path must contain parent_id" in str(exc_info.value)

def test_storage_type_validation():
    """Test that StorageBase only accepts valid StorageType values."""
    # Test each valid type
    for storage_type in StorageType:
        data = {
            "name": "Test Storage",
            "description": "Test description",
            "type": storage_type.value,
            "metadata": {
                "capacity": 100
            }
        }
        storage = StorageBase(**data)
        assert storage.type == storage_type
        assert storage.type.value == storage_type.value

def test_storage_metadata_validation():
    """Test StorageMetadata validation rules."""
    # Test valid metadata
    valid_metadata = StorageMetadata(
        capacity=100,
        dimensions="100x50x200cm",
        location="Living Room",
        custom={"color": "brown"}
    )
    assert valid_metadata.capacity == 100
    assert valid_metadata.dimensions == "100x50x200cm"
    assert valid_metadata.location == "Living Room"
    assert valid_metadata.custom == {"color": "brown"}

    # Test optional fields
    minimal_metadata = StorageMetadata()
    assert minimal_metadata.capacity is None
    assert minimal_metadata.dimensions is None
    assert minimal_metadata.location is None
    assert minimal_metadata.custom == {}

def test_storage_metadata_custom_fields():
    """Test custom metadata fields handling."""
    metadata = StorageMetadata(
        custom={
            "color": "brown",
            "material": "wood",
            "weight_capacity": 500
        }
    )
    assert metadata.custom["color"] == "brown"
    assert metadata.custom["material"] == "wood"
    assert metadata.custom["weight_capacity"] == 500

def test_storage_update_validation():
    """Test StorageUpdate model validation."""
    # Test partial update
    update_data = {
        "name": "Updated Name",
        "description": "Updated description"
    }
    update = StorageUpdate(**update_data)
    assert update.name == "Updated Name"
    assert update.description == "Updated description"
    assert update.type is None
    assert update.parent_id is None
    assert update.metadata is None

    # Test full update
    full_update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "type": StorageType.CABINET.value,
        "parent_id": "507f1f77bcf86cd799439011",
        "metadata": {
            "capacity": 200,
            "dimensions": "200x100x300cm"
        }
    }
    full_update = StorageUpdate(**full_update_data)
    assert full_update.name == "Updated Name"
    assert full_update.type == StorageType.CABINET
    assert full_update.parent_id == "507f1f77bcf86cd799439011"
    assert full_update.metadata.capacity == 200

def test_storage_update_self_parent():
    """Test that storage cannot be its own parent."""
    update_data = {
        "id": "507f1f77bcf86cd799439011",
        "parent_id": "507f1f77bcf86cd799439011"  # Same as id
    }
    with pytest.raises(ValueError) as exc_info:
        StorageUpdate(**update_data)
    assert "cannot be its own parent" in str(exc_info.value)

def test_storage_response_structure():
    """Test StorageResponse model structure."""
    response_data = {
        "id": "507f1f77bcf86cd799439011",
        "name": "Main Cabinet",
        "type": StorageType.CABINET.value,
        "movies": [
            {
                "id": "507f1f77bcf86cd799439012",
                "title": "Test Movie",
                "year": 2025,
                "format": "DVD",
                "storage_id": "507f1f77bcf86cd799439011",
                "tmdb_id": 12345
            }
        ],
        "children": [
            {
                "id": "507f1f77bcf86cd799439013",
                "name": "Shelf 1",
                "type": StorageType.SHELF.value,
                "metadata": {}
            }
        ]
    }
    response = StorageResponse(**response_data)
    assert response.id == response_data["id"]
    assert response.name == response_data["name"]
    assert response.type == StorageType.CABINET
    assert len(response.movies) == 1
    assert len(response.children) == 1
    assert response.movies[0].title == "Test Movie"
    assert response.children[0].name == "Shelf 1"

def test_storage_tree_response():
    """Test StorageTreeResponse model structure."""
    tree_data = {
        "id": "507f1f77bcf86cd799439011",
        "name": "Main Cabinet",
        "type": StorageType.CABINET.value,
        "ancestors": [
            {
                "id": "507f1f77bcf86cd799439010",
                "name": "Storage Room",
                "type": StorageType.CABINET.value
            }
        ],
        "descendants": [
            {
                "id": "507f1f77bcf86cd799439012",
                "name": "Shelf 1",
                "type": StorageType.SHELF.value
            }
        ]
    }
    tree = StorageTreeResponse(**tree_data)
    assert tree.id == tree_data["id"]
    assert len(tree.ancestors) == 1
    assert len(tree.descendants) == 1
    assert tree.ancestors[0].name == "Storage Room"
    assert tree.descendants[0].name == "Shelf 1"

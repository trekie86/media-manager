"""
Unit tests for the Movie model.

This module demonstrates how pytest fixtures work:
1. Fixtures defined in conftest.py are automatically discovered
2. When a test function includes a fixture name as a parameter,
   pytest automatically injects the fixture's return value
3. The sample_movie_data fixture provides test data that can be
   reused across multiple tests
"""
import pytest
from pydantic import ValidationError

from app.models.movie import MovieBase, MediaFormat

pytestmark = pytest.mark.unit

def test_fixture_explanation(sample_movie_data):
    """
    This test demonstrates how fixtures work.
    
    The sample_movie_data fixture is defined in conftest.py and contains:
    {
        "title": "Test Movie",
        "year": 2025,
        "format": MediaFormat.DVD.value,  # Using enum value for type safety
        "tmdb_id": 12345,
        "genre_ids": [28, 878],
        "runtime": 120,
        "cover_image": "http://example.com/poster.jpg"
    }
    
    By including sample_movie_data as a parameter, pytest automatically:
    1. Finds the fixture in conftest.py
    2. Executes the fixture function
    3. Passes the returned data to our test
    """
    # Show what's in the fixture
    print("\nFixture data:", sample_movie_data)
    
    # Verify the fixture contains what we expect
    assert "title" in sample_movie_data
    assert "year" in sample_movie_data
    assert "format" in sample_movie_data
    
    # Use the fixture data to create a model
    movie = MovieBase(**sample_movie_data)
    assert movie.title == "Test Movie"

def test_create_movie_success(sample_movie_data):
    """Test creating a movie with valid data."""
    movie = MovieBase(**sample_movie_data)
    assert movie.title == sample_movie_data["title"]
    assert movie.year == sample_movie_data["year"]
    assert movie.format == sample_movie_data["format"]
    assert movie.tmdb_id == sample_movie_data["tmdb_id"]
    assert movie.genre_ids == sample_movie_data["genre_ids"]
    assert movie.runtime == sample_movie_data["runtime"]
    assert movie.cover_image == sample_movie_data["cover_image"]

def test_create_movie_invalid_year():
    """Test creating a movie with an invalid year."""
    invalid_data = {
        "title": "Test Movie",
        "year": 1800,  # Too old
        "format": MediaFormat.DVD.value,
        "tmdb_id": 12345,
        "genre_ids": [28],
        "runtime": 120,
        "cover_image": "http://example.com/poster.jpg"
    }
    with pytest.raises(ValidationError) as exc_info:
        MovieBase(**invalid_data)
    assert "year" in str(exc_info.value)

def test_create_movie_invalid_format():
    """Test creating a movie with an invalid format."""
    invalid_data = {
        "title": "Test Movie",
        "year": 2025,
        "format": "VHS",  # Invalid format
        "tmdb_id": 12345,
        "genre_ids": [28],
        "runtime": 120,
        "cover_image": "http://example.com/poster.jpg"
    }
    with pytest.raises(ValidationError) as exc_info:
        MovieBase(**invalid_data)
    assert "format" in str(exc_info.value)

def test_create_movie_missing_required():
    """Test creating a movie with missing required fields."""
    invalid_data = {
        "year": 2025,
        "format": MediaFormat.DVD.value
        # Missing title and other required fields
    }
    with pytest.raises(ValidationError) as exc_info:
        MovieBase(**invalid_data)
    assert "title" in str(exc_info.value)

def test_create_movie_invalid_runtime():
    """Test creating a movie with an invalid runtime."""
    invalid_data = {
        "title": "Test Movie",
        "year": 2025,
        "format": MediaFormat.DVD.value,
        "tmdb_id": 12345,
        "genre_ids": [28],
        "runtime": -120,  # Negative runtime
        "cover_image": "http://example.com/poster.jpg"
    }
    with pytest.raises(ValidationError) as exc_info:
        MovieBase(**invalid_data)
    assert "runtime" in str(exc_info.value)

def test_media_format_values():
    """Test that MediaFormat enum has the expected values."""
    assert MediaFormat.DVD.value == "DVD"
    assert MediaFormat.BLURAY.value == "Blu-ray"
    assert MediaFormat.DIGITAL.value == "Digital"
    
    # Test that these are the only valid values
    assert len(MediaFormat.__members__) == 3
    assert set(MediaFormat.__members__.keys()) == {"DVD", "BLURAY", "DIGITAL"}

def test_media_format_validation():
    """Test that MovieBase only accepts valid MediaFormat values."""
    # Test each valid format
    for format_value in MediaFormat:
        data = {
            "title": "Test Movie",
            "year": 2025,
            "format": format_value.value,
            "tmdb_id": 12345
        }
        movie = MovieBase(**data)
        assert movie.format == format_value
        assert movie.format.value == format_value.value

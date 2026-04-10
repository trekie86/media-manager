"""API test helpers for FastAPI route testing.

This module provides utilities for testing FastAPI routes including:
- Test client setup
- Authentication helpers
- Response validation
"""

from typing import Any, Dict, Optional
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app


def get_test_client() -> TestClient:
    """Create a TestClient instance for making API requests.

    Returns:
        TestClient: Configured FastAPI test client
    """
    return TestClient(app)


def assert_response(
    response: Response,
    expected_status_code: int = 200,
    expected_content: Optional[Dict[str, Any]] = None,
) -> None:
    """Assert that a response matches expected status code and content.

    Args:
        response: The response to validate
        expected_status_code: Expected HTTP status code (default: 200)
        expected_content: Expected response content (optional)

    Raises:
        AssertionError: If response doesn't match expectations
    """
    assert response.status_code == expected_status_code, (
        f"Expected status code {expected_status_code}, got {response.status_code}\n"
        f"Response: {response.text}"
    )

    if expected_content is not None:
        assert (
            response.json() == expected_content
        ), f"Expected content {expected_content}, got {response.json()}"


def assert_error_response(
    response: Response, expected_status_code: int, expected_detail: str
) -> None:
    """Assert that an error response matches expected status and detail.

    Args:
        response: The error response to validate
        expected_status_code: Expected HTTP status code
        expected_detail: Expected error detail message

    Raises:
        AssertionError: If error response doesn't match expectations
    """
    assert response.status_code == expected_status_code
    data = response.json()

    # Handle FastAPI validation errors (422 responses)
    if expected_status_code == 422:
        assert "detail" in data, f"Error response missing 'detail' field: {data}"
        assert isinstance(
            data["detail"], list
        ), "Expected validation error list in 'detail' field"
        error_messages = [error["msg"] for error in data["detail"]]
        assert any(
            expected_detail in msg for msg in error_messages
        ), f"Expected error detail '{expected_detail}' not found in {error_messages}"
    else:
        # Handle regular error responses
        assert "detail" in data, f"Error response missing 'detail' field: {data}"
        assert (
            data["detail"] == expected_detail
        ), f"Expected error detail '{expected_detail}', got '{data['detail']}'"

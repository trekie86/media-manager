"""
Standardized response models for OpenAPI documentation and client generation.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

# Generic type for paginated data
T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Individual error detail."""

    type: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(
        None, description="Field name if error is field-specific"
    )


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error category or type")
    message: str = Field(..., description="Primary error message")
    details: Optional[List[ErrorDetail]] = Field(
        None, description="Detailed error information"
    )
    request_id: Optional[str] = Field(
        None, description="Request identifier for debugging"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": "validation_error",
                    "message": "Invalid input data",
                    "details": [
                        {
                            "type": "missing_field",
                            "message": "Title is required",
                            "field": "title",
                        }
                    ],
                },
                {
                    "success": False,
                    "error": "not_found",
                    "message": "Movie not found",
                    "request_id": "req_123456",
                },
            ]
        }


class SuccessResponse(BaseModel, Generic[T]):
    """Standardized success response format."""

    success: bool = Field(True, description="Always true for success responses")
    data: T = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "data": {"id": "507f1f77bcf86cd799439011", "title": "The Matrix"},
                    "message": "Movie created successfully",
                }
            ]
        }


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_prev": False,
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response format."""

    success: bool = Field(True, description="Always true for success responses")
    data: List[T] = Field(..., description="Array of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    message: Optional[str] = Field(None, description="Optional success message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {"id": "507f1f77bcf86cd799439011", "title": "The Matrix"},
                    {"id": "507f1f77bcf86cd799439012", "title": "Inception"},
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total_items": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_prev": False,
                },
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    env: str = Field(..., description="Environment name")
    timestamp: Optional[str] = Field(None, description="Response timestamp")
    checks: Optional[Dict[str, Any]] = Field(
        None, description="Individual health check results"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class MessageResponse(BaseModel):
    """Simple message response."""

    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {"success": True, "message": "Operation completed successfully"}
        }


# Common HTTP status code responses for OpenAPI documentation
COMMON_RESPONSES = {
    400: {
        "description": "Bad Request - Invalid input data",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "validation_error",
                    "message": "Invalid input data",
                    "details": [
                        {
                            "type": "missing_field",
                            "message": "Title is required",
                            "field": "title",
                        }
                    ],
                }
            }
        },
    },
    401: {
        "description": "Unauthorized - Authentication required",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "unauthorized",
                    "message": "Authentication required",
                }
            }
        },
    },
    403: {
        "description": "Forbidden - Insufficient permissions",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "forbidden",
                    "message": "Insufficient permissions",
                }
            }
        },
    },
    404: {
        "description": "Not Found - Resource not found",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "not_found",
                    "message": "Resource not found",
                }
            }
        },
    },
    422: {
        "description": "Unprocessable Entity - Validation error",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "validation_error",
                    "message": "Validation failed",
                    "details": [
                        {
                            "type": "invalid_format",
                            "message": "Invalid email format",
                            "field": "email",
                        }
                    ],
                }
            }
        },
    },
    500: {
        "description": "Internal Server Error - Unexpected server error",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "internal_error",
                    "message": "An unexpected error occurred",
                }
            }
        },
    },
}

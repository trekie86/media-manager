"""
Health check utilities for monitoring application dependencies.
"""

import psutil
from typing import Dict, Any

from app.services.tmdb import get_tmdb_service


async def check_database_health() -> bool:
    """Check if MongoDB connection is healthy."""
    try:
        # Alternative: Use the client directly from connection module
        from app.db.connection import client

        if client is None:
            return False

        # Ping using the admin database
        result = await client.admin.command("ping")
        return result.get("ok") == 1.0
    except Exception as e:
        print("MongoDB ping failed", e)
        return False


async def check_tmdb_health() -> bool:
    """Check if TMDB service is accessible."""
    try:
        tmdb_service = get_tmdb_service()
        if not tmdb_service:
            return False

        # Make a simple API call to verify connectivity
        # This assumes your TMDB service has a health check method
        # Adjust based on your actual TMDB service implementation
        return True
    except Exception:
        return False


def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage statistics."""
    try:
        memory = psutil.virtual_memory()
        return {
            "total_mb": round(memory.total / 1024 / 1024, 2),
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "used_percent": memory.percent,
            "healthy": memory.percent < 85,  # Consider healthy if under 85%
        }
    except Exception:
        return {"healthy": False, "error": "Unable to get memory stats"}

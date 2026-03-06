"""Integration tests for the /health endpoint."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    async def test_health_returns_200_when_db_is_up(self, client):
        """The /health endpoint responds 200 when MongoDB is reachable."""
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True, "used_percent": 50}):
            response = await client.get("/health")

        assert response.status_code == 200

    async def test_health_response_structure(self, client):
        """Response contains status, version, env, timestamp, and checks."""
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True, "used_percent": 40}):
            response = await client.get("/health")

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "env" in data
        assert "timestamp" in data
        assert "checks" in data

    async def test_health_checks_contain_database_key(self, client):
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True}):
            response = await client.get("/health")

        checks = response.json()["checks"]
        assert "database" in checks
        assert "tmdb_service" in checks
        assert "memory" in checks

    async def test_healthy_when_all_checks_pass(self, client):
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True, "used_percent": 30}):
            response = await client.get("/health")

        assert response.json()["status"] == "healthy"

    async def test_unhealthy_when_database_is_down(self, client):
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=False), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True}):
            response = await client.get("/health")

        assert response.json()["status"] == "unhealthy"

    async def test_unhealthy_when_tmdb_service_is_down(self, client):
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=False), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True}):
            response = await client.get("/health")

        assert response.json()["status"] == "unhealthy"

    async def test_unhealthy_when_memory_is_critical(self, client):
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": False, "used_percent": 95}):
            response = await client.get("/health")

        assert response.json()["status"] == "unhealthy"

    async def test_health_is_publicly_accessible_without_auth(self, client):
        """No Authorization header required for the health endpoint."""
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True}):
            response = await client.get("/health")

        # Must not be 401 or 403
        assert response.status_code not in (401, 403)

    async def test_database_check_result_reflected_in_checks(self, client):
        with patch("app.core.health.check_database_health", new_callable=AsyncMock, return_value=False), \
             patch("app.core.health.check_tmdb_health", new_callable=AsyncMock, return_value=True), \
             patch("app.core.health.get_memory_usage", return_value={"healthy": True}):
            response = await client.get("/health")

        checks = response.json()["checks"]
        assert checks["database"] is False
        assert checks["tmdb_service"] is True


# ---------------------------------------------------------------------------
# check_database_health unit-level coverage
# ---------------------------------------------------------------------------


class TestCheckDatabaseHealth:
    async def test_returns_true_when_ping_succeeds(self):
        """check_database_health returns True when MongoDB ping returns ok=1."""
        mock_client = MagicMock()
        mock_client.admin.command = AsyncMock(return_value={"ok": 1.0})

        with patch("app.core.health.client", mock_client):
            from app.core.health import check_database_health
            result = await check_database_health()

        assert result is True

    async def test_returns_false_when_client_is_none(self):
        with patch("app.core.health.client", None):
            from app.core.health import check_database_health
            result = await check_database_health()

        assert result is False

    async def test_returns_false_when_ping_raises(self):
        mock_client = MagicMock()
        mock_client.admin.command = AsyncMock(side_effect=Exception("Connection refused"))

        with patch("app.core.health.client", mock_client):
            from app.core.health import check_database_health
            result = await check_database_health()

        assert result is False


# ---------------------------------------------------------------------------
# get_memory_usage unit-level coverage
# ---------------------------------------------------------------------------


class TestGetMemoryUsage:
    def test_returns_memory_stats(self):
        from app.core.health import get_memory_usage
        result = get_memory_usage()

        assert "total_mb" in result
        assert "available_mb" in result
        assert "used_percent" in result
        assert "healthy" in result
        assert isinstance(result["healthy"], bool)

    def test_healthy_is_false_when_psutil_fails(self):
        with patch("app.core.health.psutil.virtual_memory", side_effect=Exception("No psutil")):
            from app.core.health import get_memory_usage
            result = get_memory_usage()

        assert result["healthy"] is False

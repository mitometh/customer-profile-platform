"""Integration tests for the health check endpoint."""

import pytest

pytestmark = pytest.mark.asyncio


class TestHealthCheck:
    async def test_health_returns_200(self, client, seeded_roles):
        """Health endpoint should be publicly accessible (no auth)."""
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data
        assert "checks" in data
        assert data["checks"]["database"] in ("up", "down")

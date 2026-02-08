"""Integration tests for source management endpoints."""

from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


class TestListSources:
    async def test_list_sources_admin(self, client, admin_user):
        """Admin can list sources."""
        _, token, _ = admin_user
        resp = await client.get("/api/sources", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data

    async def test_list_sources_sales_forbidden(self, client, sales_user):
        """Sales user lacks sources.read → 403."""
        _, token, _ = sales_user
        resp = await client.get("/api/sources", headers=auth_headers(token))
        assert resp.status_code == 403


class TestCreateSource:
    async def test_create_source_admin(self, client, admin_user):
        """Admin can create a source and receives the raw API token."""
        _, token, _ = admin_user

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.api.routes.sources.get_redis", return_value=mock_redis):
            resp = await client.post(
                "/api/sources",
                json={"name": "test-jira", "description": "Jira integration"},
                headers=auth_headers(token),
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-jira"
        assert "api_token" in data
        assert len(data["api_token"]) > 20  # token_urlsafe(32) produces ~43 chars
        assert data["is_active"] is True

    async def test_create_source_sales_forbidden(self, client, sales_user):
        """Sales user lacks sources.manage → 403."""
        _, token, _ = sales_user
        resp = await client.post(
            "/api/sources",
            json={"name": "test-source"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    async def test_create_source_duplicate_name(self, client, admin_user):
        """Duplicate source name → 409."""
        _, token, _ = admin_user

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.api.routes.sources.get_redis", return_value=mock_redis):
            # First create
            resp1 = await client.post(
                "/api/sources",
                json={"name": "dup-source"},
                headers=auth_headers(token),
            )
            assert resp1.status_code == 201

            # Duplicate
            resp2 = await client.post(
                "/api/sources",
                json={"name": "dup-source"},
                headers=auth_headers(token),
            )
            assert resp2.status_code == 409


class TestGetSource:
    async def test_get_source_detail(self, client, admin_user):
        """Admin can get source detail."""
        _, token, _ = admin_user

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.api.routes.sources.get_redis", return_value=mock_redis):
            # Create first
            create_resp = await client.post(
                "/api/sources",
                json={"name": "detail-source", "description": "For detail test"},
                headers=auth_headers(token),
            )
            assert create_resp.status_code == 201
            source_id = create_resp.json()["id"]

            # Get detail
            resp = await client.get(
                f"/api/sources/{source_id}",
                headers=auth_headers(token),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "detail-source"
            assert data["description"] == "For detail test"
            # api_token should NOT appear in detail
            assert "api_token" not in data
            assert "api_token_hash" not in data

    async def test_get_source_not_found(self, client, admin_user):
        """Non-existent source → 404."""
        _, token, _ = admin_user

        mock_redis = AsyncMock()
        with patch("app.api.routes.sources.get_redis", return_value=mock_redis):
            resp = await client.get(
                "/api/sources/00000000-0000-0000-0000-000000000000",
                headers=auth_headers(token),
            )
            assert resp.status_code == 404


class TestUpdateSource:
    async def test_update_source_deactivate(self, client, admin_user):
        """Admin can deactivate a source."""
        _, token, _ = admin_user

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.api.routes.sources.get_redis", return_value=mock_redis):
            # Create
            create_resp = await client.post(
                "/api/sources",
                json={"name": "update-source"},
                headers=auth_headers(token),
            )
            source_id = create_resp.json()["id"]

            # Deactivate
            resp = await client.patch(
                f"/api/sources/{source_id}",
                json={"is_active": False},
                headers=auth_headers(token),
            )
            assert resp.status_code == 200
            assert resp.json()["is_active"] is False

    async def test_update_source_rename(self, client, admin_user):
        """Admin can rename a source."""
        _, token, _ = admin_user

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.api.routes.sources.get_redis", return_value=mock_redis):
            create_resp = await client.post(
                "/api/sources",
                json={"name": "rename-me"},
                headers=auth_headers(token),
            )
            source_id = create_resp.json()["id"]

            resp = await client.patch(
                f"/api/sources/{source_id}",
                json={"name": "renamed-source"},
                headers=auth_headers(token),
            )
            assert resp.status_code == 200
            assert resp.json()["name"] == "renamed-source"


class TestDeleteSource:
    async def test_delete_source(self, client, admin_user):
        """Admin can soft-delete a source."""
        _, token, _ = admin_user

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.api.routes.sources.get_redis", return_value=mock_redis):
            # Create
            create_resp = await client.post(
                "/api/sources",
                json={"name": "delete-me"},
                headers=auth_headers(token),
            )
            source_id = create_resp.json()["id"]

            # Delete
            resp = await client.delete(
                f"/api/sources/{source_id}",
                headers=auth_headers(token),
            )
            assert resp.status_code == 204

            # Verify it's gone from list
            list_resp = await client.get(
                "/api/sources",
                headers=auth_headers(token),
            )
            source_names = [s["name"] for s in list_resp.json()["data"]]
            assert "delete-me" not in source_names

    async def test_delete_source_sales_forbidden(self, client, sales_user):
        """Sales user cannot delete sources."""
        _, token, _ = sales_user
        resp = await client.delete(
            "/api/sources/00000000-0000-0000-0000-000000000000",
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

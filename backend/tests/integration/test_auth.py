"""Integration tests for auth endpoints (login, /me, user CRUD)."""

from uuid import uuid4

import pytest
import pytest_asyncio

from app.infrastructure.security import hash_password

pytestmark = pytest.mark.asyncio


class TestLogin:
    async def test_login_success(self, client, admin_user):
        user, _, _ = admin_user
        resp = await client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": "Password123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == user.email
        assert isinstance(data["user"]["permissions"], list)

    async def test_login_wrong_password(self, client, admin_user):
        user, _, _ = admin_user
        resp = await client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client, seeded_roles):
        resp = await client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "Password123",
            },
        )
        assert resp.status_code == 401


class TestGetMe:
    async def test_get_me_success(self, client, admin_user):
        user, token, _ = admin_user
        from tests.conftest import auth_headers

        resp = await client.get("/api/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == user.email
        assert data["role"] == "admin"

    async def test_get_me_no_token(self, client, seeded_roles):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_get_me_invalid_token(self, client, seeded_roles):
        resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401


class TestUserCRUD:
    async def test_create_user(self, client, admin_user, seeded_roles):
        _, token, _ = admin_user
        from tests.conftest import auth_headers

        resp = await client.post(
            "/api/users",
            json={
                "email": "newuser@test.com",
                "full_name": "New User",
                "role": "sales",
                "password": "newpass123",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "sales"

    async def test_create_user_forbidden_for_sales(self, client, sales_user):
        _, token, _ = sales_user
        from tests.conftest import auth_headers

        resp = await client.post(
            "/api/users",
            json={
                "email": "another@test.com",
                "full_name": "Another",
                "role": "sales",
                "password": "pass",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    async def test_list_users(self, client, admin_user):
        _, token, _ = admin_user
        from tests.conftest import auth_headers

        resp = await client.get("/api/users", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data

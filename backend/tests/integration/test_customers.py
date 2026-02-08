"""Integration tests for customer endpoints."""

from uuid import uuid4

import pytest

from tests.conftest import auth_headers, make_token

pytestmark = pytest.mark.asyncio


class TestListCustomers:
    async def test_list_customers_success(self, client, admin_user, sample_customer):
        _, token, _ = admin_user
        resp = await client.get("/api/customers", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) >= 1

    async def test_list_customers_with_search(self, client, admin_user, sample_customer):
        _, token, _ = admin_user
        resp = await client.get("/api/customers?search=Acme", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1
        assert "Acme" in data["data"][0]["company_name"]

    async def test_list_customers_no_results(self, client, admin_user, sample_customer):
        _, token, _ = admin_user
        resp = await client.get("/api/customers?search=NonExistent", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 0

    async def test_list_customers_pagination(self, client, admin_user, sample_customer):
        _, token, _ = admin_user
        resp = await client.get("/api/customers?limit=1", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["limit"] == 1

    async def test_list_customers_unauthorized(self, client, seeded_roles):
        resp = await client.get("/api/customers")
        assert resp.status_code == 401


class TestGetCustomer:
    async def test_get_customer_detail(self, client, admin_user, sample_customer):
        _, token, _ = admin_user
        resp = await client.get(f"/api/customers/{sample_customer.id}", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "Acme Corp"
        assert data["contact_name"] == "John Doe"
        assert "recent_events" in data
        assert "metrics" in data

    async def test_get_customer_not_found(self, client, admin_user):
        from uuid import uuid4

        _, token, _ = admin_user
        resp = await client.get(f"/api/customers/{uuid4()}", headers=auth_headers(token))
        assert resp.status_code == 404

    async def test_get_customer_forbidden_no_permission(self, client, seeded_roles, db):
        """User with no customers.read permission should get 403."""
        from uuid import uuid4

        from app.infrastructure.models.role import RoleModel, RolePermissionModel
        from app.infrastructure.models.user import UserModel

        # Create a role with no permissions
        empty_role = RoleModel(id=uuid4(), name="empty", display_name="Empty")
        db.add(empty_role)
        await db.flush()

        user = UserModel(
            id=uuid4(),
            email="empty@test.com",
            full_name="Empty User",
            password_hash="$2b$12$fake",
            role_id=empty_role.id,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        from tests.conftest import make_token

        token = make_token(user.id)
        resp = await client.get(f"/api/customers/{uuid4()}", headers=auth_headers(token))
        assert resp.status_code == 403


class TestCreateCustomer:
    async def test_create_customer_success(self, client, admin_user):
        _, token, _ = admin_user
        resp = await client.post(
            "/api/customers",
            headers=auth_headers(token),
            json={
                "company_name": "New Corp",
                "contact_name": "Jane Smith",
                "email": "jane@newcorp.com",
                "phone": "+1-555-0200",
                "industry": "Finance",
                "contract_value": 75000.00,
                "currency_code": "USD",
                "signup_date": "2024-06-01",
                "notes": "Important client",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["company_name"] == "New Corp"
        assert data["contact_name"] == "Jane Smith"
        assert data["email"] == "jane@newcorp.com"
        assert data["phone"] == "+1-555-0200"
        assert data["industry"] == "Finance"
        assert data["notes"] == "Important client"
        assert "id" in data
        assert "created_at" in data

    async def test_create_customer_minimal(self, client, admin_user):
        """Only company_name is required."""
        _, token, _ = admin_user
        resp = await client.post(
            "/api/customers",
            headers=auth_headers(token),
            json={"company_name": "Minimal Corp"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["company_name"] == "Minimal Corp"

    async def test_create_customer_missing_company_name(self, client, admin_user):
        _, token, _ = admin_user
        resp = await client.post(
            "/api/customers",
            headers=auth_headers(token),
            json={"contact_name": "No Company"},
        )
        assert resp.status_code == 422

    async def test_create_customer_forbidden(self, client, sales_user):
        """Sales user should not be able to create customers."""
        _, token, _ = sales_user
        resp = await client.post(
            "/api/customers",
            headers=auth_headers(token),
            json={"company_name": "Forbidden Corp"},
        )
        assert resp.status_code == 403

    async def test_create_customer_unauthorized(self, client, seeded_roles):
        resp = await client.post(
            "/api/customers",
            json={"company_name": "Unauthorized Corp"},
        )
        assert resp.status_code in (401, 403)


class TestUpdateCustomer:
    async def test_update_customer_success(self, client, admin_user, sample_customer):
        _, token, _ = admin_user
        resp = await client.patch(
            f"/api/customers/{sample_customer.id}",
            headers=auth_headers(token),
            json={"company_name": "Acme Corp Updated", "industry": "Healthcare"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "Acme Corp Updated"
        assert data["industry"] == "Healthcare"
        # Unchanged fields should remain
        assert data["contact_name"] == "John Doe"

    async def test_update_customer_not_found(self, client, admin_user):
        _, token, _ = admin_user
        resp = await client.patch(
            f"/api/customers/{uuid4()}",
            headers=auth_headers(token),
            json={"company_name": "Ghost Corp"},
        )
        assert resp.status_code == 404

    async def test_update_customer_forbidden(self, client, sales_user, sample_customer):
        """Sales user should not be able to update customers."""
        _, token, _ = sales_user
        resp = await client.patch(
            f"/api/customers/{sample_customer.id}",
            headers=auth_headers(token),
            json={"company_name": "Hacked Corp"},
        )
        assert resp.status_code == 403

    async def test_update_customer_no_body(self, client, admin_user, sample_customer):
        """Empty update should still succeed (no-op)."""
        _, token, _ = admin_user
        resp = await client.patch(
            f"/api/customers/{sample_customer.id}",
            headers=auth_headers(token),
            json={},
        )
        assert resp.status_code == 200


class TestDeleteCustomer:
    async def test_delete_customer_success(self, client, admin_user, sample_customer):
        _, token, _ = admin_user
        resp = await client.delete(
            f"/api/customers/{sample_customer.id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 204

        # Verify soft-deleted: GET should return 404
        resp = await client.get(
            f"/api/customers/{sample_customer.id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    async def test_delete_customer_not_found(self, client, admin_user):
        _, token, _ = admin_user
        resp = await client.delete(
            f"/api/customers/{uuid4()}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    async def test_delete_customer_forbidden(self, client, sales_user, sample_customer):
        """Sales user should not be able to delete customers."""
        _, token, _ = sales_user
        resp = await client.delete(
            f"/api/customers/{sample_customer.id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    async def test_delete_customer_unauthorized(self, client, seeded_roles, sample_customer):
        resp = await client.delete(
            f"/api/customers/{sample_customer.id}",
        )
        assert resp.status_code in (401, 403)

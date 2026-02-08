"""Integration tests for metrics endpoints (catalog + customer metrics + manage)."""

import pytest

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


class TestMetricCatalog:
    async def test_get_catalog_success(self, client, admin_user, sample_metrics):
        _, token, _ = admin_user
        resp = await client.get("/api/metrics/catalog", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data
        assert len(data["metrics"]) == 3
        names = {m["name"] for m in data["metrics"]}
        assert "support_tickets_last_30d" in names
        assert "health_score" in names
        assert "days_since_last_contact" in names

    async def test_catalog_unauthorized(self, client, seeded_roles):
        resp = await client.get("/api/metrics/catalog")
        assert resp.status_code == 401


class TestMetricDefinitionManage:
    """Tests for POST, PATCH, DELETE /api/metrics/catalog."""

    async def test_create_metric_definition(self, client, admin_user):
        _, token, _ = admin_user
        resp = await client.post(
            "/api/metrics/catalog",
            json={
                "name": "churn_risk",
                "display_name": "Churn Risk Score",
                "description": "Likelihood of customer churning",
                "unit": "percentage",
                "value_type": "decimal",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "churn_risk"
        assert data["display_name"] == "Churn Risk Score"
        assert data["unit"] == "percentage"
        assert data["value_type"] == "decimal"
        assert "id" in data

    async def test_create_metric_definition_conflict(self, client, admin_user, sample_metrics):
        """Creating a metric with a duplicate name returns 409."""
        _, token, _ = admin_user
        resp = await client.post(
            "/api/metrics/catalog",
            json={
                "name": "health_score",
                "display_name": "Duplicate Health Score",
                "value_type": "integer",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 409

    async def test_create_metric_definition_forbidden(self, client, sales_user):
        """Sales user lacks metrics.catalog.manage, gets 403."""
        _, token, _ = sales_user
        resp = await client.post(
            "/api/metrics/catalog",
            json={
                "name": "test_metric",
                "display_name": "Test",
                "value_type": "integer",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    async def test_update_metric_definition(self, client, admin_user, sample_metrics):
        _, token, _ = admin_user
        metric_id = sample_metrics["definitions"]["health_score"].id
        resp = await client.patch(
            f"/api/metrics/catalog/{metric_id}",
            json={
                "display_name": "Updated Health Score",
                "unit": "points",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Updated Health Score"
        assert data["unit"] == "points"
        assert data["name"] == "health_score"

    async def test_update_metric_definition_not_found(self, client, admin_user):
        from uuid import uuid4

        _, token, _ = admin_user
        resp = await client.patch(
            f"/api/metrics/catalog/{uuid4()}",
            json={"display_name": "Nope"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    async def test_update_metric_definition_forbidden(self, client, sales_user, sample_metrics):
        _, token, _ = sales_user
        metric_id = sample_metrics["definitions"]["health_score"].id
        resp = await client.patch(
            f"/api/metrics/catalog/{metric_id}",
            json={"display_name": "Hacked"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    async def test_delete_metric_definition(self, client, admin_user, sample_metrics):
        _, token, _ = admin_user
        metric_id = sample_metrics["definitions"]["days_since"].id
        resp = await client.delete(
            f"/api/metrics/catalog/{metric_id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 204

        # Verify it's gone from catalog
        resp = await client.get("/api/metrics/catalog", headers=auth_headers(token))
        assert resp.status_code == 200
        names = {m["name"] for m in resp.json()["metrics"]}
        assert "days_since_last_contact" not in names

    async def test_delete_metric_definition_not_found(self, client, admin_user):
        from uuid import uuid4

        _, token, _ = admin_user
        resp = await client.delete(
            f"/api/metrics/catalog/{uuid4()}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    async def test_delete_metric_definition_forbidden(self, client, sales_user, sample_metrics):
        _, token, _ = sales_user
        metric_id = sample_metrics["definitions"]["health_score"].id
        resp = await client.delete(
            f"/api/metrics/catalog/{metric_id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    async def test_delete_then_get_returns_not_found_on_second_delete(self, client, admin_user, sample_metrics):
        """Deleting an already-deleted metric returns 404."""
        _, token, _ = admin_user
        metric_id = sample_metrics["definitions"]["support_tickets"].id
        resp = await client.delete(
            f"/api/metrics/catalog/{metric_id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 204

        resp = await client.delete(
            f"/api/metrics/catalog/{metric_id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404


class TestCustomerMetrics:
    async def test_get_customer_metrics(self, client, admin_user, sample_customer, sample_metrics):
        _, token, _ = admin_user
        resp = await client.get(
            f"/api/customers/{sample_customer.id}/metrics",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == str(sample_customer.id)
        assert len(data["metrics"]) == 3

    async def test_customer_metrics_empty(self, client, admin_user, sample_metrics):
        """Non-existent customer returns 404."""
        from uuid import uuid4

        _, token, _ = admin_user
        fake_id = uuid4()
        resp = await client.get(
            f"/api/customers/{fake_id}/metrics",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    async def test_customer_metrics_forbidden(self, client, seeded_roles, db):
        """User without metrics.read gets 403."""
        from uuid import uuid4

        from app.infrastructure.models.role import RoleModel
        from app.infrastructure.models.user import UserModel

        empty_role = RoleModel(id=uuid4(), name="nometrics", display_name="No Metrics")
        db.add(empty_role)
        await db.flush()

        user = UserModel(
            id=uuid4(),
            email="nometrics@test.com",
            full_name="No Metrics User",
            password_hash="$2b$12$fake",
            role_id=empty_role.id,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        from tests.conftest import make_token

        token = make_token(user.id)
        resp = await client.get(
            f"/api/customers/{uuid4()}/metrics",
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

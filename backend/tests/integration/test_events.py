"""Integration tests for event timeline endpoints."""

import pytest

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


class TestListEvents:
    async def test_list_events_success(self, client, admin_user, sample_customer, sample_events):
        _, token, _ = admin_user
        resp = await client.get(
            f"/api/customers/{sample_customer.id}/events",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert len(data["data"]) == 5  # 5 sample events

    async def test_list_events_filter_by_type(self, client, admin_user, sample_customer, sample_events):
        _, token, _ = admin_user
        resp = await client.get(
            f"/api/customers/{sample_customer.id}/events?event_type=support_ticket",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        for event in data["data"]:
            assert event["event_type"] == "support_ticket"

    async def test_list_events_filter_by_date(self, client, admin_user, sample_customer, sample_events):
        _, token, _ = admin_user
        resp = await client.get(
            f"/api/customers/{sample_customer.id}/events?since=2024-06-17T00:00:00Z",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        # Events 2,3,4 have occurred_at >= June 17
        assert len(data["data"]) >= 1

    async def test_list_events_customer_not_found(self, client, admin_user):
        from uuid import uuid4

        _, token, _ = admin_user
        resp = await client.get(
            f"/api/customers/{uuid4()}/events",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    async def test_list_events_unauthorized(self, client, sample_customer, seeded_roles):
        resp = await client.get(f"/api/customers/{sample_customer.id}/events")
        assert resp.status_code == 401

    async def test_list_events_pagination(self, client, admin_user, sample_customer, sample_events):
        _, token, _ = admin_user
        resp = await client.get(
            f"/api/customers/{sample_customer.id}/events?limit=2",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["has_next"] is True

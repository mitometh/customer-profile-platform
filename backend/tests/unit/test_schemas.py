"""Unit tests for Pydantic API schemas — validation and serialization."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.schemas.auth import CurrentUserSchema, LoginRequest, UserCreateRequest
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.api.schemas.common import PaginatedResponse, PaginationMeta
from app.api.schemas.customer import CustomerSummarySchema
from app.api.schemas.ingestion import IngestRequest, IngestResponse


class TestLoginRequest:
    def test_valid(self):
        req = LoginRequest(email="user@test.com", password="secret")
        assert req.email == "user@test.com"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            LoginRequest()


class TestCurrentUserSchema:
    def test_valid(self):
        uid = uuid4()
        schema = CurrentUserSchema(id=uid, email="a@b.com", full_name="Test", role="admin", permissions=["chat.use"])
        assert schema.id == uid
        assert schema.permissions == ["chat.use"]


class TestUserCreateRequest:
    def test_valid(self):
        req = UserCreateRequest(email="new@test.com", full_name="New User", role="sales", password="Pass1234")
        assert req.role == "sales"


class TestChatRequest:
    def test_valid(self):
        req = ChatRequest(message="Hello")
        assert req.session_id is None

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_too_long_message_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 2001)

    def test_with_session_id(self):
        sid = uuid4()
        req = ChatRequest(message="Hi", session_id=sid)
        assert req.session_id == sid


class TestIngestRequest:
    def test_valid(self):
        req = IngestRequest(
            event_type="support_ticket",
            customer_identifier="Acme Corp",
            title="Test ticket",
            occurred_at=datetime(2024, 6, 15),
        )
        assert req.event_type == "support_ticket"
        assert req.occurred_at == datetime(2024, 6, 15)

    def test_with_all_fields(self):
        req = IngestRequest(
            event_type="meeting",
            customer_identifier="Acme",
            title="Sync",
            description="Weekly sync",
            occurred_at=datetime(2024, 6, 15),
            data={"attendees": 3},
        )
        assert req.data == {"attendees": 3}


class TestIngestResponse:
    def test_defaults(self):
        resp = IngestResponse(event_id="abc-123")
        assert resp.status == "accepted"
        assert resp.event_id == "abc-123"


class TestPaginatedResponse:
    def test_with_customer_data(self):
        uid = uuid4()
        resp = PaginatedResponse[CustomerSummarySchema](
            data=[CustomerSummarySchema(id=uid, company_name="Test Co", currency_code="USD")],
            pagination=PaginationMeta(total=1, limit=20, has_next=False, next_cursor=None),
        )
        assert len(resp.data) == 1
        assert resp.pagination.total == 1

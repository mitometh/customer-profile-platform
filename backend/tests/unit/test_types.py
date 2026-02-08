"""Unit tests for core value types and cursor encoding."""

from datetime import UTC, datetime, timezone
from uuid import uuid4

import pytest

from app.core.types import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MIN_LIMIT,
    PaginatedResult,
    Pagination,
    decode_cursor,
    encode_cursor,
)


class TestPagination:
    def test_defaults(self):
        p = Pagination()
        assert p.cursor is None
        assert p.limit == DEFAULT_LIMIT

    def test_clamp_min(self):
        p = Pagination(limit=0)
        assert p.limit == MIN_LIMIT

    def test_clamp_max(self):
        p = Pagination(limit=999)
        assert p.limit == MAX_LIMIT

    def test_frozen(self):
        p = Pagination()
        with pytest.raises(AttributeError):
            p.limit = 50


class TestCursorEncoding:
    def test_round_trip(self):
        uid = uuid4()
        ts = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        cursor = encode_cursor(uid, ts)
        decoded = decode_cursor(cursor)
        assert decoded["id"] == uid
        assert decoded["created_at"] == ts

    def test_invalid_cursor_raises_value_error(self):
        with pytest.raises(ValueError):
            decode_cursor("not-valid-base64-json")

    def test_cursor_is_url_safe_base64(self):
        uid = uuid4()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        cursor = encode_cursor(uid, ts)
        # URL-safe base64 should not contain + or /
        assert "+" not in cursor
        assert "/" not in cursor


class TestPaginatedResult:
    def test_defaults(self):
        result = PaginatedResult()
        assert result.data == []
        assert result.total is None
        assert result.has_next is False
        assert result.next_cursor is None

    def test_with_data(self):
        result = PaginatedResult(data=[1, 2, 3], total=10, has_next=True, next_cursor="abc")
        assert len(result.data) == 3
        assert result.total == 10
        assert result.has_next is True

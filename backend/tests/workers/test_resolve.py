"""Unit tests for the customer resolution utility used by workers."""

from uuid import uuid4

import pytest
import pytest_asyncio

from workers._resolve import resolve_customer

pytestmark = pytest.mark.asyncio


class TestResolveCustomer:
    async def test_resolve_by_company_name(self, db, sample_customer):
        result = await resolve_customer(db, "Acme Corp")
        assert result == sample_customer.id

    async def test_resolve_by_company_name_case_insensitive(self, db, sample_customer):
        result = await resolve_customer(db, "acme corp")
        assert result == sample_customer.id

    async def test_resolve_by_email(self, db, sample_customer):
        result = await resolve_customer(db, "john@acme.com")
        assert result == sample_customer.id

    async def test_resolve_empty_string(self, db, sample_customer):
        result = await resolve_customer(db, "")
        assert result is None

    async def test_resolve_nonexistent(self, db, sample_customer):
        result = await resolve_customer(db, "NonExistent Company")
        assert result is None

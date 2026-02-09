"""Unit tests for Gate 1 RBAC — tool filtering and capabilities summary."""

from uuid import UUID

from app.agent.rbac import (
    TOOL_PERMISSION_MAP,
    filter_tools_by_permissions,
    get_capabilities_summary,
)
from app.agent.tools import RETRIEVER_TOOL_DEFINITIONS
from app.core.context import CallerContext

# Helper to build a CallerContext with given permissions
_TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_ctx(permissions: list[str]) -> CallerContext:
    return CallerContext(
        user_id=_TEST_USER_ID,
        email="test@example.com",
        full_name="Test User",
        role="tester",
        permissions=frozenset(permissions),
    )


class TestFilterToolsByPermissions:
    def test_admin_gets_all_tools(self):
        all_perms = list(set(TOOL_PERMISSION_MAP.values()))
        ctx = _make_ctx(all_perms)
        filtered = filter_tools_by_permissions(RETRIEVER_TOOL_DEFINITIONS, ctx)
        assert len(filtered) == len(RETRIEVER_TOOL_DEFINITIONS)

    def test_no_permissions_gets_no_tools(self):
        ctx = _make_ctx([])
        filtered = filter_tools_by_permissions(RETRIEVER_TOOL_DEFINITIONS, ctx)
        assert filtered == []

    def test_sales_gets_customer_tools(self):
        sales_perms = ["customers.read", "events.read", "metrics.read", "metrics.catalog.read"]
        ctx = _make_ctx(sales_perms)
        filtered = filter_tools_by_permissions(RETRIEVER_TOOL_DEFINITIONS, ctx)
        names = {t["name"] for t in filtered}
        assert "lookup_customer" in names
        assert "list_customers" in names
        assert "get_customer_detail" in names
        assert "query_events" in names
        assert "get_metric" in names
        assert "get_metrics_catalog" in names

    def test_only_customers_read(self):
        ctx = _make_ctx(["customers.read"])
        filtered = filter_tools_by_permissions(RETRIEVER_TOOL_DEFINITIONS, ctx)
        names = {t["name"] for t in filtered}
        assert names == {"lookup_customer", "list_customers", "get_customer_detail"}

    def test_unknown_tool_excluded(self):
        fake_tools = [{"name": "unknown_tool", "description": "test", "input_schema": {}}]
        ctx = _make_ctx(["customers.read"])
        filtered = filter_tools_by_permissions(fake_tools, ctx)
        assert filtered == []


class TestGetCapabilitiesSummary:
    def test_full_permissions(self):
        perms = ["customers.read", "events.read", "metrics.read", "metrics.catalog.read"]
        ctx = _make_ctx(perms)
        summary = get_capabilities_summary(ctx)
        assert "customer data" in summary
        assert "events" in summary
        assert "metrics" in summary

    def test_no_permissions(self):
        ctx = _make_ctx([])
        summary = get_capabilities_summary(ctx)
        assert "no data access" in summary

    def test_partial_permissions(self):
        ctx = _make_ctx(["customers.read"])
        summary = get_capabilities_summary(ctx)
        assert "customer data" in summary
        assert "events" not in summary


class TestToolPermissionMap:
    def test_all_tool_definitions_have_mapping(self):
        for tool_def in RETRIEVER_TOOL_DEFINITIONS:
            assert tool_def["name"] in TOOL_PERMISSION_MAP, (
                f"Tool '{tool_def['name']}' is missing from TOOL_PERMISSION_MAP"
            )

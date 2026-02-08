"""Unit tests for Gate 1 RBAC — tool filtering and capabilities summary."""

from app.agent.rbac import (
    TOOL_PERMISSION_MAP,
    filter_tools_by_permissions,
    get_capabilities_summary,
)
from app.agent.tools import TOOL_DEFINITIONS


class TestFilterToolsByPermissions:
    def test_admin_gets_all_tools(self):
        all_perms = list(TOOL_PERMISSION_MAP.values())
        filtered = filter_tools_by_permissions(TOOL_DEFINITIONS, all_perms)
        assert len(filtered) == len(TOOL_DEFINITIONS)

    def test_no_permissions_gets_no_tools(self):
        filtered = filter_tools_by_permissions(TOOL_DEFINITIONS, [])
        assert filtered == []

    def test_sales_gets_customer_tools(self):
        sales_perms = ["customers.read", "events.read", "metrics.read", "metrics.catalog.read"]
        filtered = filter_tools_by_permissions(TOOL_DEFINITIONS, sales_perms)
        names = {t["name"] for t in filtered}
        assert "lookup_customer" in names
        assert "list_customers" in names
        assert "get_customer_detail" in names
        assert "query_events" in names
        assert "get_metric" in names
        assert "get_metrics_catalog" in names

    def test_only_customers_read(self):
        filtered = filter_tools_by_permissions(TOOL_DEFINITIONS, ["customers.read"])
        names = {t["name"] for t in filtered}
        assert names == {"lookup_customer", "list_customers", "get_customer_detail"}

    def test_unknown_tool_excluded(self):
        fake_tools = [{"name": "unknown_tool", "description": "test", "input_schema": {}}]
        filtered = filter_tools_by_permissions(fake_tools, ["customers.read"])
        assert filtered == []


class TestGetCapabilitiesSummary:
    def test_full_permissions(self):
        perms = ["customers.read", "events.read", "metrics.read", "metrics.catalog.read"]
        summary = get_capabilities_summary(perms)
        assert "customer data" in summary
        assert "events" in summary
        assert "metrics" in summary

    def test_no_permissions(self):
        summary = get_capabilities_summary([])
        assert "no data access" in summary

    def test_partial_permissions(self):
        summary = get_capabilities_summary(["customers.read"])
        assert "customer data" in summary
        assert "events" not in summary


class TestToolPermissionMap:
    def test_all_tool_definitions_have_mapping(self):
        for tool_def in TOOL_DEFINITIONS:
            assert tool_def["name"] in TOOL_PERMISSION_MAP, (
                f"Tool '{tool_def['name']}' is missing from TOOL_PERMISSION_MAP"
            )

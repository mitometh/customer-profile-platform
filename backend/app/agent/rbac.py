"""Gate 1: Tool filtering by user permissions.

Before each LLM call the tool definitions list is pruned to contain only
tools the current user is allowed to invoke, based on the permission set
loaded from the database via ``CurrentUserDTO.permissions``.

The authoritative mapping lives here (in code) because the tool definitions
themselves are defined in code (``app/agent/tools.py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.context import CallerContext

# Maps each tool name to the permission required to invoke it.
TOOL_PERMISSION_MAP: dict[str, str] = {
    "lookup_customer": "customers.read",
    "list_customers": "customers.read",
    "get_customer_detail": "customers.read",
    "query_events": "events.read",
    "get_metric": "metrics.read",
    "get_metrics_catalog": "metrics.catalog.read",
    "get_sources_list": "sources.read",
    "get_source_status": "sources.read",
}


def filter_tools_by_permissions(tools: list[dict], ctx: CallerContext) -> list[dict]:
    """Gate 1: Return only tools whose required permission the user holds.

    Tools whose name is not present in ``TOOL_PERMISSION_MAP`` are excluded
    as a safety default.
    """
    return [t for t in tools if ctx.has_permission(TOOL_PERMISSION_MAP.get(t["name"], ""))]


def get_capabilities_summary(ctx: CallerContext) -> str:
    """Generate a human-readable summary of user capabilities for the system prompt.

    The summary is injected into the orchestrator system prompt so the LLM
    knows what the user can do without ever seeing raw permission strings.
    """
    capabilities: list[str] = []
    if ctx.has_permission("customers.read"):
        capabilities.append("look up and browse customer data")
    if ctx.has_permission("events.read"):
        capabilities.append("view customer activity and events")
    if ctx.has_permission("metrics.read"):
        capabilities.append("view customer metrics and health scores")
    if ctx.has_permission("metrics.catalog.read"):
        capabilities.append("browse the full metrics catalog")
    if ctx.has_permission("sources.read"):
        capabilities.append("view registered data sources and their status")
    if not capabilities:
        return "You have no data access capabilities."
    return "You can " + ", ".join(capabilities) + "."

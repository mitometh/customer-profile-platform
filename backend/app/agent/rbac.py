"""Gate 1: Tool filtering by user permissions.

Before each LLM call the tool definitions list is pruned to contain only
tools the current user is allowed to invoke, based on the permission set
loaded from the database via ``CurrentUserDTO.permissions``.

The authoritative mapping lives here (in code) because the tool definitions
themselves are defined in code (``app/agent/tools.py``).
"""

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


def filter_tools_by_permissions(tools: list[dict], permissions: list[str]) -> list[dict]:
    """Gate 1: Return only tools whose required permission the user holds.

    Tools whose name is not present in ``TOOL_PERMISSION_MAP`` are excluded
    as a safety default.
    """
    return [t for t in tools if TOOL_PERMISSION_MAP.get(t["name"], "") in permissions]


def get_capabilities_summary(permissions: list[str]) -> str:
    """Generate a human-readable summary of user capabilities for the system prompt.

    The summary is injected into the orchestrator system prompt so the LLM
    knows what the user can do without ever seeing raw permission strings.
    """
    capabilities: list[str] = []
    if "customers.read" in permissions:
        capabilities.append("look up and browse customer data")
    if "events.read" in permissions:
        capabilities.append("view customer activity and events")
    if "metrics.read" in permissions:
        capabilities.append("view customer metrics and health scores")
    if "metrics.catalog.read" in permissions:
        capabilities.append("browse the full metrics catalog")
    if "sources.read" in permissions:
        capabilities.append("view registered data sources and their status")
    if not capabilities:
        return "You have no data access capabilities."
    return "You can " + ", ".join(capabilities) + "."

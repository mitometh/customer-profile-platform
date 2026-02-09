"""Tool definitions and execution for the retriever agent.

Each tool wraps a call to an application-layer service method. The tool
definitions follow the Anthropic tool-calling JSON Schema format.

Gate 2 enforcement happens inside the service methods themselves — this
module simply routes tool calls and translates domain exceptions into
structured error dicts the LLM can interpret.
"""

import logging
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.customer import CustomerService
from app.application.services.event import EventService
from app.application.services.metric import MetricQueryService
from app.application.services.source import SourceService
from app.core.context import CallerContext
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.types import Pagination
from app.infrastructure.cache import get_redis
from app.infrastructure.repositories.customer import SqlAlchemyCustomerRepository
from app.infrastructure.repositories.event import SqlAlchemyEventRepository
from app.infrastructure.repositories.metric import (
    SqlAlchemyCustomerMetricHistoryRepository,
    SqlAlchemyCustomerMetricRepository,
    SqlAlchemyMetricDefinitionRepository,
)
from app.infrastructure.repositories.source import (
    RedisTokenCache,
    SqlAlchemySourceRepository,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retriever tool definitions (Anthropic JSON Schema format)
#
# These tools are ONLY used by the RetrieverAgent. The OrchestratorAgent
# has its own meta-tool (``request_data``) defined in orchestrator.py.
# Gate 1 (rbac.py) filters this list by user permissions before passing
# it to the retriever.
# ---------------------------------------------------------------------------

RETRIEVER_TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "lookup_customer",
        "description": (
            "Look up a customer by name (partial, case-insensitive match). "
            "Returns a list of matching customers with summary info."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full or partial company name to search for.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "list_customers",
        "description": (
            "List all customers with optional search filtering. Returns a paginated list of customer summaries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Optional search query to filter by company name.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 10).",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_customer_detail",
        "description": (
            "Get a full customer profile including contact info, contract details, "
            "and recent events. Requires the customer's UUID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer's UUID.",
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "query_events",
        "description": (
            "Query the activity timeline for a specific customer. Can filter by event type and date range."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer's UUID.",
                },
                "event_type": {
                    "type": "string",
                    "description": ("Optional event type filter (e.g., 'support_ticket', 'meeting', 'usage_event')."),
                },
                "since": {
                    "type": "string",
                    "description": "Optional ISO 8601 start date filter (inclusive).",
                },
                "until": {
                    "type": "string",
                    "description": "Optional ISO 8601 end date filter (inclusive).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of events to return (default 20).",
                    "default": 20,
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_metric",
        "description": (
            "Get all pre-computed metric values (health score, support tickets, "
            "days since contact, etc.) for a specific customer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer's UUID.",
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_metrics_catalog",
        "description": (
            "List all available metric definitions in the system, including display names, units, and descriptions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_sources_list",
        "description": (
            "List all registered data sources and their status "
            "(active/inactive). Useful for checking ingestion pipeline health."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_source_status",
        "description": (
            "Get the status of a specific data source by name or ID. "
            "Returns whether the source is active and when it was created."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source_name": {
                    "type": "string",
                    "description": "The name of the source to look up.",
                },
                "source_id": {
                    "type": "string",
                    "description": "The UUID of the source to look up.",
                },
            },
            "required": [],
        },
    },
]


# ---------------------------------------------------------------------------
# JSON serialisation helper
# ---------------------------------------------------------------------------


def _make_serializable(obj: object) -> object:
    """Recursively convert non-JSON-serializable types."""
    if obj is None:
        return obj
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    # Fallback: convert to string representation
    return str(obj)


# ---------------------------------------------------------------------------
# Individual tool executors
# ---------------------------------------------------------------------------


async def _exec_lookup_customer(session: AsyncSession, ctx: CallerContext, tool_input: dict) -> dict:
    """Execute lookup_customer tool."""
    customer_repo = SqlAlchemyCustomerRepository(session)
    event_repo = SqlAlchemyEventRepository(session)
    service = CustomerService(customer_repo=customer_repo, event_repo=event_repo)

    name = tool_input.get("name", "")
    result = await service.list_customers(
        search=name,
        pagination=Pagination(limit=10),
        ctx=ctx,
    )

    customers = [_make_serializable(dto.__dict__) for dto in result.data]
    return {"customers": customers, "total_found": len(customers)}


async def _exec_list_customers(session: AsyncSession, ctx: CallerContext, tool_input: dict) -> dict:
    """Execute list_customers tool."""
    customer_repo = SqlAlchemyCustomerRepository(session)
    event_repo = SqlAlchemyEventRepository(session)
    service = CustomerService(customer_repo=customer_repo, event_repo=event_repo)

    search = tool_input.get("search")
    limit = tool_input.get("limit", 10)
    result = await service.list_customers(
        search=search,
        pagination=Pagination(limit=limit),
        ctx=ctx,
    )

    customers = [_make_serializable(dto.__dict__) for dto in result.data]
    return {
        "customers": customers,
        "total_found": len(customers),
        "has_next": result.has_next,
    }


async def _exec_get_customer_detail(session: AsyncSession, ctx: CallerContext, tool_input: dict) -> dict:
    """Execute get_customer_detail tool."""
    try:
        customer_id = UUID(tool_input["customer_id"])
    except (ValueError, KeyError) as exc:
        return {"error": "INVALID_INPUT", "message": f"Invalid customer_id: {exc}"}

    customer_repo = SqlAlchemyCustomerRepository(session)
    event_repo = SqlAlchemyEventRepository(session)
    service = CustomerService(customer_repo=customer_repo, event_repo=event_repo)

    detail = await service.get_customer_detail(customer_id, ctx=ctx)

    return _make_serializable(detail.__dict__)


async def _exec_query_events(session: AsyncSession, ctx: CallerContext, tool_input: dict) -> dict:
    """Execute query_events tool."""
    try:
        customer_id = UUID(tool_input["customer_id"])
    except (ValueError, KeyError) as exc:
        return {"error": "INVALID_INPUT", "message": f"Invalid customer_id: {exc}"}

    event_repo = SqlAlchemyEventRepository(session)
    customer_repo = SqlAlchemyCustomerRepository(session)
    service = EventService(event_repo=event_repo, customer_repo=customer_repo)
    event_type = tool_input.get("event_type")
    since_str = tool_input.get("since")
    until_str = tool_input.get("until")
    limit = tool_input.get("limit", 20)

    since = datetime.fromisoformat(since_str) if since_str else None
    until = datetime.fromisoformat(until_str) if until_str else None

    result = await service.list_events(
        customer_id=customer_id,
        event_type=event_type,
        since=since,
        until=until,
        pagination=Pagination(limit=limit),
        ctx=ctx,
    )

    events = [_make_serializable(dto.__dict__) for dto in result.data]
    return {
        "events": events,
        "total_found": len(events),
        "has_next": result.has_next,
    }


async def _exec_get_metric(session: AsyncSession, ctx: CallerContext, tool_input: dict) -> dict:
    """Execute get_metric tool."""
    try:
        customer_id = UUID(tool_input["customer_id"])
    except (ValueError, KeyError) as exc:
        return {"error": "INVALID_INPUT", "message": f"Invalid customer_id: {exc}"}

    customer_repo = SqlAlchemyCustomerRepository(session)
    definition_repo = SqlAlchemyMetricDefinitionRepository(session)
    metric_repo = SqlAlchemyCustomerMetricRepository(session)
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(session)
    service = MetricQueryService(
        definition_repo=definition_repo,
        metric_repo=metric_repo,
        history_repo=history_repo,
        customer_repo=customer_repo,
    )
    metrics = await service.get_customer_metrics(customer_id, ctx=ctx)

    return {
        "customer_id": str(customer_id),
        "metrics": [_make_serializable(m.__dict__) for m in metrics],
    }


async def _exec_get_metrics_catalog(session: AsyncSession, ctx: CallerContext, tool_input: dict | None = None) -> dict:
    """Execute get_metrics_catalog tool."""
    customer_repo = SqlAlchemyCustomerRepository(session)
    definition_repo = SqlAlchemyMetricDefinitionRepository(session)
    metric_repo = SqlAlchemyCustomerMetricRepository(session)
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(session)
    service = MetricQueryService(
        definition_repo=definition_repo,
        metric_repo=metric_repo,
        history_repo=history_repo,
        customer_repo=customer_repo,
    )

    catalog = await service.get_catalog(ctx=ctx)
    return {"metrics": [_make_serializable(c.__dict__) for c in catalog]}


async def _exec_get_sources_list(session: AsyncSession, ctx: CallerContext, tool_input: dict | None = None) -> dict:
    """Execute get_sources_list tool."""
    source_repo = SqlAlchemySourceRepository(session)
    token_cache = RedisTokenCache(get_redis())
    service = SourceService(source_repo=source_repo, token_cache=token_cache)

    sources = await service.get_active_sources(ctx=ctx)
    return {
        "sources": [_make_serializable(s.__dict__) for s in sources],
        "total": len(sources),
    }


async def _exec_get_source_status(session: AsyncSession, ctx: CallerContext, tool_input: dict) -> dict:
    """Execute get_source_status tool."""
    source_repo = SqlAlchemySourceRepository(session)
    token_cache = RedisTokenCache(get_redis())
    service = SourceService(source_repo=source_repo, token_cache=token_cache)

    source_name = tool_input.get("source_name")
    source_id_str = tool_input.get("source_id")

    if source_id_str:
        try:
            source_id = UUID(source_id_str)
        except ValueError:
            return {"error": "INVALID_INPUT", "message": f"Invalid source_id: {source_id_str}"}
        detail = await service.get_source(source_id, ctx=ctx)
        return _make_serializable(detail.__dict__)

    if source_name:
        # Look up by name via the repo directly, then build DTO through service
        source = await source_repo.get_by_name(source_name)
        if source is None:
            return {"error": "NOT_FOUND", "message": f"Source '{source_name}' not found"}
        detail = await service.get_source(source.id, ctx=ctx)
        return _make_serializable(detail.__dict__)

    return {"error": "INVALID_INPUT", "message": "Provide source_name or source_id"}


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

_TOOL_REGISTRY: dict[str, Callable] = {
    "lookup_customer": _exec_lookup_customer,
    "list_customers": _exec_list_customers,
    "get_customer_detail": _exec_get_customer_detail,
    "query_events": _exec_query_events,
    "get_metric": _exec_get_metric,
    "get_metrics_catalog": _exec_get_metrics_catalog,
    "get_sources_list": _exec_get_sources_list,
    "get_source_status": _exec_get_source_status,
}


# ---------------------------------------------------------------------------
# Tool execution dispatcher
# ---------------------------------------------------------------------------


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    session: AsyncSession,
    ctx: CallerContext,
) -> dict:
    """Execute a tool call and return the result as a JSON-serializable dict."""
    try:
        handler = _TOOL_REGISTRY.get(tool_name)
        if handler is None:
            return {"error": "UNKNOWN_TOOL", "message": f"Unknown tool: {tool_name}"}
        return await handler(session, ctx, tool_input)
    except ForbiddenError as exc:
        return {"error": "FORBIDDEN", "message": str(exc.message)}
    except NotFoundError as exc:
        return {"error": "NOT_FOUND", "message": str(exc.message)}
    except Exception as exc:
        logger.exception("Unexpected error executing tool %s", tool_name)
        return {"error": "INTERNAL_ERROR", "message": "An unexpected error occurred during tool execution"}

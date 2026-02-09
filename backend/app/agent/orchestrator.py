"""Orchestrator agent — user-facing conversational agent.

The orchestrator is the primary AI agent that:
1. Receives user messages plus conversation history.
2. Decides whether to respond directly (casual/AB-5) or request data (data questions).
3. Delegates data retrieval to the RetrieverAgent via the ``request_data`` meta-tool.
4. Synthesises the final human-readable response with source attribution (AB-4).
5. Applies sliding-window truncation for long conversations (AB-9).
"""

import json
import logging
from datetime import date, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.client import AnthropicClient
from app.agent.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from app.agent.retriever import RetrieverAgent
from app.core.context import CallerContext

logger = logging.getLogger(__name__)

# AB-9: Maximum number of messages to keep in the sliding window.
MAX_CONVERSATION_MESSAGES = 20
# Maximum data-request iterations to prevent infinite loops.
MAX_DATA_REQUEST_ITERATIONS = 5

# ---------------------------------------------------------------------------
# Meta-tool: the only tool the orchestrator LLM sees.
# When the LLM calls this, the orchestrator delegates to the RetrieverAgent.
# ---------------------------------------------------------------------------

REQUEST_DATA_TOOL: dict = {
    "name": "request_data",
    "description": (
        "Request data from the Customer 360 platform. Describe what data you "
        "need in natural language and the data retrieval system will fetch it "
        "using the appropriate database queries. You can request customer info, "
        "events, metrics, data source status, and more. Be specific about what "
        "you need (e.g., customer names, IDs, date ranges, metric types)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": (
                    "A clear, specific description of the data you need. "
                    "Include any known identifiers (customer IDs, names), "
                    "filters (date ranges, event types), and what fields "
                    "you want returned."
                ),
            },
        },
        "required": ["description"],
    },
}


class OrchestratorAgent:
    """User-facing conversational agent for Customer 360 insights."""

    def __init__(self, client: AnthropicClient) -> None:
        self._client = client
        self._retriever = RetrieverAgent(client)

    async def process_message(
        self,
        user_message: str,
        conversation_history: list[dict],
        user_context: dict,
        session: AsyncSession,
        ctx: CallerContext,
    ) -> dict:
        """Process a user message and return the response with sources.

        Args:
            user_message: The new message from the user.
            conversation_history: Prior messages in [{role, content}, ...] format.
            user_context: Dict with user_name, role, capabilities_summary,
                          and available_tools (Gate-1-filtered tool defs).
            session: Active database session for tool execution.
            ctx: Caller context for Gate 2 permission checks in tools.

        Returns:
            A dict with ``message`` (str), ``sources`` (list of source dicts),
            and ``tool_calls`` (list of tool call dicts).
        """
        # Build system prompt with user context
        system = ORCHESTRATOR_SYSTEM_PROMPT.format(
            user_name=user_context["user_name"],
            role=user_context["role"],
            capabilities_summary=user_context["capabilities_summary"],
        )

        # Build messages: conversation history + new user message
        messages = [*conversation_history, {"role": "user", "content": user_message}]

        # AB-9: Sliding-window truncation — keep the last N messages.
        # Always keep an even number so we don't split a user/assistant pair.
        if len(messages) > MAX_CONVERSATION_MESSAGES:
            messages = messages[-MAX_CONVERSATION_MESSAGES:]
            # Ensure the first message is from the user (required by API)
            if messages and messages[0]["role"] != "user":
                messages = messages[1:]

        # Gate 1 filtered tools — passed to the retriever, not the orchestrator LLM
        available_tools = user_context.get("available_tools", [])

        # The orchestrator LLM only sees the request_data meta-tool
        orchestrator_tools = [REQUEST_DATA_TOOL] if available_tools else []

        # --- Data-request loop ---
        # The orchestrator LLM may request data multiple times before it has
        # enough information to synthesise a final response.
        sources: list[dict] = []
        tool_calls: list[dict] = []

        for _ in range(MAX_DATA_REQUEST_ITERATIONS):
            response = await self._client.create_message(
                system=system,
                messages=messages,
                tools=orchestrator_tools if orchestrator_tools else None,
            )

            # Separate content blocks by type
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            text_blocks = [block for block in response.content if block.type == "text"]

            if not tool_use_blocks:
                # No data request — extract final text and return (AB-5 casual or synthesis)
                final_text = "".join(block.text for block in text_blocks)
                return {
                    "message": final_text,
                    "sources": sources,
                    "tool_calls": tool_calls,
                }

            # Process request_data calls: delegate each to the RetrieverAgent
            assistant_content: list[dict] = []
            tool_result_contents: list[dict] = []

            # Include any text blocks first
            for text_block in text_blocks:
                assistant_content.append(
                    {
                        "type": "text",
                        "text": text_block.text,
                    }
                )

            for tool_block in tool_use_blocks:
                if tool_block.name != "request_data":
                    # Safety: ignore unexpected tool calls
                    logger.warning("Orchestrator called unexpected tool: %s", tool_block.name)
                    continue

                data_request = tool_block.input.get("description", "")
                logger.info("Orchestrator requesting data: %s", data_request[:200])

                # Delegate to the RetrieverAgent
                retriever_result = await self._retriever.fetch_data(
                    data_request=data_request,
                    tools=available_tools,
                    session=session,
                    ctx=ctx,
                )

                # Extract source attribution and tool call metadata from retriever results
                retriever_tool_results = retriever_result.get("tool_results", [])
                for tr in retriever_tool_results:
                    result_data = tr.get("result", {})
                    tool_name = tr.get("tool", "")
                    tool_input = tr.get("input", {})

                    # Track tool calls for metadata (AB-4)
                    result_count = _count_results(result_data)
                    tool_calls.append(
                        {
                            "tool": tool_name,
                            "input": tool_input,
                            "result_count": result_count,
                        }
                    )

                    # Build source attribution from actual data records
                    if "error" not in result_data:
                        sources.extend(_extract_sources(tool_name, result_data))

                # Build the tool result to feed back to the orchestrator LLM
                # Serialize the retriever's raw results so the orchestrator can synthesise
                retriever_data = json.dumps(
                    [tr.get("result", {}) for tr in retriever_tool_results],
                    default=str,
                )

                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tool_block.id,
                        "name": tool_block.name,
                        "input": tool_block.input,
                    }
                )

                tool_result_contents.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": retriever_data,
                    }
                )

            # Append the assistant turn and the tool result turn to the conversation
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_result_contents})

            # If the LLM stopped for end_turn, break
            if response.stop_reason == "end_turn":
                final_text = "".join(block.text for block in text_blocks)
                return {
                    "message": final_text,
                    "sources": sources,
                    "tool_calls": tool_calls,
                }

        # Safety fallback if max iterations reached
        logger.warning("Orchestrator hit max data-request iterations (%d)", MAX_DATA_REQUEST_ITERATIONS)
        return {
            "message": (
                "I gathered some data but need to summarise. Please try rephrasing your question more specifically."
            ),
            "sources": sources,
            "tool_calls": tool_calls,
        }


def _count_results(result: dict) -> int:
    """Count the number of data items in a tool result for source attribution."""
    # Check common result shapes from our tools
    for key in ("customers", "events", "metrics"):
        if key in result and isinstance(result[key], list):
            return len(result[key])
    # Single-object results (e.g., customer detail)
    if "error" not in result and "id" in result:
        return 1
    return 0


def _json_safe(obj: object) -> object:
    """Recursively convert non-JSON-serializable values to strings."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    return obj


def _extract_sources(tool_name: str, result: dict) -> list[dict]:
    """Extract source attribution records from a tool result.

    Maps tool results to ``{table, record_id, fields_used}`` entries that
    reference the actual data records used to build the answer.
    """
    sources: list[dict] = []

    # Tools that return a list of customers
    if "customers" in result and isinstance(result["customers"], list):
        for c in result["customers"]:
            if "id" in c:
                sources.append(
                    {
                        "table": "customers",
                        "record_id": str(c["id"]),
                        "fields_used": _json_safe({k: v for k, v in c.items() if k != "id"}),
                    }
                )

    # Tools that return a list of events
    elif "events" in result and isinstance(result["events"], list):
        for e in result["events"]:
            if "id" in e:
                sources.append(
                    {
                        "table": "events",
                        "record_id": str(e["id"]),
                        "fields_used": _json_safe({k: v for k, v in e.items() if k != "id"}),
                    }
                )

    # Tools that return a list of metrics
    elif "metrics" in result and isinstance(result["metrics"], list):
        for m in result["metrics"]:
            record_id = str(m.get("id", m.get("metric_key", "")))
            sources.append(
                {
                    "table": "metrics",
                    "record_id": record_id,
                    "fields_used": _json_safe({k: v for k, v in m.items() if k not in ("id", "metric_key")}),
                }
            )

    # Single-object results (e.g., get_customer_detail)
    elif "id" in result:
        # Determine table from tool name
        table = "customers" if "customer" in tool_name else "records"
        sources.append(
            {
                "table": table,
                "record_id": str(result["id"]),
                "fields_used": _json_safe({k: v for k, v in result.items() if k != "id"}),
            }
        )

    return sources

"""Orchestrator agent — user-facing conversational agent.

The orchestrator is the primary AI agent that:
1. Receives user messages plus conversation history.
2. Decides whether to respond directly (casual/AB-5) or call tools (data questions).
3. Executes the full tool-call loop when the LLM requests tool use.
4. Synthesises the final human-readable response with source attribution (AB-4).
5. Applies sliding-window truncation for long conversations (AB-9).
"""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.client import AnthropicClient
from app.agent.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from app.agent.tools import execute_tool

logger = logging.getLogger(__name__)

# AB-9: Maximum number of messages to keep in the sliding window.
MAX_CONVERSATION_MESSAGES = 20
# Maximum tool-call iterations to prevent infinite loops.
MAX_TOOL_ITERATIONS = 10


class OrchestratorAgent:
    """User-facing conversational agent for Customer 360 insights."""

    def __init__(self, client: AnthropicClient) -> None:
        self._client = client

    async def process_message(
        self,
        user_message: str,
        conversation_history: list[dict],
        user_context: dict,
        session: AsyncSession,
        permissions: list[str],
    ) -> dict:
        """Process a user message and return the response with sources.

        Args:
            user_message: The new message from the user.
            conversation_history: Prior messages in [{role, content}, ...] format.
            user_context: Dict with user_name, role, capabilities_summary,
                          and available_tools (Gate-1-filtered tool defs).
            session: Active database session for tool execution.
            permissions: User's permission list for Gate 2 checks in tools.

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

        # Gate 1 filtered tools
        available_tools = user_context.get("available_tools", [])

        # --- Full tool-call loop ---
        # The orchestrator LLM may request tool calls. We execute them and
        # feed the results back until the LLM produces a final text response.
        sources: list[dict] = []
        tool_calls: list[dict] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await self._client.create_message(
                system=system,
                messages=messages,
                tools=available_tools if available_tools else None,
            )

            # Separate content blocks by type
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            text_blocks = [block for block in response.content if block.type == "text"]

            if not tool_use_blocks:
                # No tool calls — extract final text and return
                final_text = "".join(block.text for block in text_blocks)
                return {
                    "message": final_text,
                    "sources": sources,
                    "tool_calls": tool_calls,
                }

            # Process tool calls: execute each, collect results
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
                tool_name = tool_block.name
                tool_input = tool_block.input

                # Execute the tool via service layer (Gate 2 inside)
                result = await execute_tool(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    session=session,
                    permissions=permissions,
                )

                # Track for tool call metadata (AB-4)
                result_count = _count_results(result)
                tool_calls.append(
                    {
                        "tool": tool_name,
                        "input": tool_input,
                        "result_count": result_count,
                    }
                )

                # Build source attribution from actual data records
                if "error" not in result:
                    sources.extend(_extract_sources(tool_name, result))

                # Add tool_use block for the assistant message
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tool_block.id,
                        "name": tool_name,
                        "input": tool_input,
                    }
                )

                # Add tool result for the next user turn
                tool_result_contents.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps(result),
                    }
                )

            # Append the assistant turn (with tool_use blocks) and the
            # user turn (with tool_result blocks) to the conversation
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_result_contents})

            # If stop_reason is end_turn, the LLM is done even if it made tool calls
            if response.stop_reason == "end_turn":
                final_text = "".join(block.text for block in text_blocks)
                return {
                    "message": final_text,
                    "sources": sources,
                    "tool_calls": tool_calls,
                }

        # Safety fallback if max iterations reached
        logger.warning("Orchestrator hit max tool-call iterations (%d)", MAX_TOOL_ITERATIONS)
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
                        "fields_used": {k: v for k, v in c.items() if k != "id"},
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
                        "fields_used": {k: v for k, v in e.items() if k != "id"},
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
                    "fields_used": {k: v for k, v in m.items() if k not in ("id", "metric_key")},
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
                "fields_used": {k: v for k, v in result.items() if k != "id"},
            }
        )

    return sources

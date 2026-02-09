"""Retriever agent — tool-calling subsystem that never speaks to the user.

The retriever receives a data request (natural language description of what
data is needed), a set of tool definitions, and executes tool calls via the
LLM to fulfil the request. It returns raw structured data to the orchestrator.
"""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.client import AnthropicClient
from app.agent.prompts import RETRIEVER_SYSTEM_PROMPT
from app.agent.tools import execute_tool
from app.core.context import CallerContext

logger = logging.getLogger(__name__)


class RetrieverAgent:
    """Internal data-fetching agent. Calls tools and returns raw results."""

    def __init__(self, client: AnthropicClient) -> None:
        self._client = client

    async def fetch_data(
        self,
        data_request: str,
        tools: list[dict],
        session: AsyncSession,
        ctx: CallerContext,
    ) -> dict:
        """Execute tools to fetch requested data.

        Args:
            data_request: Natural language description of needed data.
            tools: Gate-1-filtered tool definitions.
            session: Active database session.
            ctx: Caller context for Gate 2 permission checks in tools.

        Returns:
            A dict with ``tool_results`` (list of {tool, input, result} dicts)
            and ``text`` (any text the retriever LLM emitted, usually empty).
        """
        messages = [{"role": "user", "content": data_request}]
        all_tool_results: list[dict] = []
        accumulated_text = ""

        # Iterative tool-call loop: the LLM may request multiple rounds of
        # tool calls before it considers the data request fulfilled.
        max_iterations = 5
        for _ in range(max_iterations):
            response = await self._client.create_message(
                system=RETRIEVER_SYSTEM_PROMPT,
                messages=messages,
                tools=tools if tools else None,
            )

            # Check stop reason
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            text_blocks = [block for block in response.content if block.type == "text"]

            for text_block in text_blocks:
                accumulated_text += text_block.text

            if not tool_use_blocks:
                # No more tool calls — retriever is done
                break

            # Build the assistant message and tool results for the next turn
            assistant_content = []
            tool_result_contents = []

            for tool_block in tool_use_blocks:
                # Execute the tool
                result = await execute_tool(
                    tool_name=tool_block.name,
                    tool_input=tool_block.input,
                    session=session,
                    ctx=ctx,
                )

                all_tool_results.append(
                    {
                        "tool": tool_block.name,
                        "input": tool_block.input,
                        "result": result,
                    }
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
                        "content": json.dumps(result),
                    }
                )

            # Also include any text blocks from the assistant
            for text_block in text_blocks:
                assistant_content.insert(
                    0,
                    {
                        "type": "text",
                        "text": text_block.text,
                    },
                )

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_result_contents})

            # If the LLM stopped for end_turn (not tool_use), break
            if response.stop_reason == "end_turn":
                break

        return {
            "tool_results": all_tool_results,
            "text": accumulated_text,
        }

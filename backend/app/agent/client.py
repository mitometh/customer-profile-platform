"""Anthropic API client wrapper for the conversational agent."""

import anthropic

from app.core.exceptions import LLMUnavailableError


class AnthropicClient:
    """Wrapper around the Anthropic async API client.

    Provides a single ``create_message`` method that maps cleanly to the
    Claude Messages API while converting SDK errors into application-layer
    ``LLMUnavailableError`` exceptions.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def create_message(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> anthropic.types.Message:
        """Send a message to Claude and return the raw response object.

        Args:
            system: The system prompt.
            messages: Conversation message list (role + content dicts).
            tools: Optional tool definitions for function calling.
            max_tokens: Maximum tokens in the response.

        Returns:
            The Anthropic ``Message`` response object.

        Raises:
            LLMUnavailableError: On any Anthropic API / network error.
        """
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        try:
            response = await self._client.messages.create(**kwargs)
            return response
        except anthropic.APIError as e:
            raise LLMUnavailableError(f"Anthropic API error: {e}") from e
        except anthropic.APIConnectionError as e:
            raise LLMUnavailableError(f"Anthropic connection error: {e}") from e

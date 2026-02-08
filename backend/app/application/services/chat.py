"""Chat service for the conversational agent context.

Orchestrates chat session management, bridges to the AI agent orchestrator,
and persists messages. Gate 2 check on ``chat.use`` happens here.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.client import AnthropicClient
from app.agent.orchestrator import OrchestratorAgent
from app.agent.rbac import filter_tools_by_permissions, get_capabilities_summary
from app.agent.tools import TOOL_DEFINITIONS
from app.application.dtos.chat import ChatResponseDTO, SourceAttribution, ToolCallAttribution
from app.core.exceptions import ForbiddenError, LLMUnavailableError, NotFoundError
from app.infrastructure.models.chat import ChatSessionModel
from app.infrastructure.repositories.chat import SqlAlchemyChatSessionRepository

logger = logging.getLogger(__name__)


class ChatService:
    """Use-case orchestration for chat messages.

    Manages session lifecycle, delegates to the AI orchestrator, and
    persists the conversation to the database.
    """

    def __init__(
        self,
        chat_repo: SqlAlchemyChatSessionRepository,
        client: AnthropicClient,
    ) -> None:
        self._chat_repo = chat_repo
        self._client = client

    async def process_message(
        self,
        user_id: UUID,
        session_id: UUID | None,
        message: str,
        permissions: list[str],
        user_name: str,
        role_name: str,
        db: AsyncSession,
    ) -> ChatResponseDTO:
        """Process a chat message end-to-end.

        Steps:
        1. Gate 2: verify ``chat.use`` permission.
        2. Get or create a chat session.
        3. Load conversation history from the database.
        4. Build user context with Gate 1 tool filtering.
        5. Delegate to the orchestrator agent.
        6. Persist both user message and assistant response.
        7. Return a ``ChatResponseDTO``.

        Raises:
            ForbiddenError: If the user lacks ``chat.use`` permission.
            NotFoundError: If the specified session_id does not exist.
            LLMUnavailableError: If the LLM provider is unreachable.
        """
        # Gate 2: check chat.use permission
        if "chat.use" not in permissions:
            raise ForbiddenError("chat.use")

        # Get or create session
        chat_session = await self._resolve_session(user_id, session_id)

        # Load conversation history from existing messages
        conversation_history = self._build_conversation_history(chat_session)

        # Gate 1: filter tools by user permissions
        available_tools = filter_tools_by_permissions(TOOL_DEFINITIONS, permissions)
        capabilities_summary = get_capabilities_summary(permissions)

        # Build user context for the orchestrator
        user_context = {
            "user_name": user_name,
            "role": role_name,
            "capabilities_summary": capabilities_summary,
            "available_tools": available_tools,
        }

        # Call the orchestrator agent
        try:
            orchestrator = OrchestratorAgent(self._client)
            result = await orchestrator.process_message(
                user_message=message,
                conversation_history=conversation_history,
                user_context=user_context,
                session=db,
                permissions=permissions,
            )
        except LLMUnavailableError:
            # Re-raise so the global error handler returns 503
            raise
        except Exception as exc:
            logger.exception("Unexpected error in orchestrator agent")
            raise LLMUnavailableError(
                "I'm having trouble processing your request right now. Please try again in a moment."
            ) from exc

        # Persist user message
        await self._chat_repo.add_message(
            session_id=chat_session.id,
            role="user",
            content=message,
        )

        # Build sources / tool_calls for persistence
        sources_json = result.get("sources", [])
        tool_calls_json = result.get("tool_calls", [])

        # Persist assistant response
        await self._chat_repo.add_message(
            session_id=chat_session.id,
            role="assistant",
            content=result.get("message", ""),
            sources=sources_json if sources_json else None,
            tool_calls=tool_calls_json if tool_calls_json else None,
        )

        # Update session metadata (message count, last_message_at)
        await self._chat_repo.update_session_metadata(chat_session.id)

        # Build response DTOs
        source_dtos = [
            SourceAttribution(
                table=s["table"],
                record_id=s["record_id"],
                fields_used=s.get("fields_used", {}),
            )
            for s in sources_json
        ]

        tool_call_dtos = [
            ToolCallAttribution(
                tool=tc["tool"],
                input=tc["input"],
                result_count=tc.get("result_count"),
            )
            for tc in tool_calls_json
        ]

        return ChatResponseDTO(
            session_id=chat_session.id,
            message=result.get("message", ""),
            sources=source_dtos,
            tool_calls=tool_call_dtos,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_session(self, user_id: UUID, session_id: UUID | None) -> ChatSessionModel:
        """Get an existing session or create a new one.

        Raises:
            NotFoundError: If the given session_id does not exist or
                           belongs to a different user.
        """
        if session_id is not None:
            chat_session = await self._chat_repo.get_with_messages(session_id)
            if chat_session is None:
                raise NotFoundError("ChatSession", session_id)
            if chat_session.user_id != user_id:
                raise NotFoundError("ChatSession", session_id)
            return chat_session

        # Create a new session
        new_session = ChatSessionModel(
            user_id=user_id,
            is_active=True,
            message_count=0,
        )
        return await self._chat_repo.create(new_session)

    @staticmethod
    def _build_conversation_history(
        chat_session: ChatSessionModel,
    ) -> list[dict]:
        """Convert persisted ChatMessageModels to the format expected by the LLM.

        Returns a list of ``{"role": "user"|"assistant", "content": "..."}``
        dicts ordered chronologically (oldest first).
        """
        if not chat_session.messages:
            return []

        # Sort by created_at ascending (chronological)
        sorted_messages = sorted(chat_session.messages, key=lambda m: m.created_at)

        history: list[dict] = []
        for msg in sorted_messages:
            history.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                }
            )

        return history

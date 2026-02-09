"""Chat route for the conversational agent context."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageSchema,
    SessionDetailSchema,
    SessionMessageSchema,
    SessionSummarySchema,
    SourceAttributionSchema,
    ToolCallSchema,
)
from app.api.service_factories import get_chat_service
from app.application.services.chat import ChatService
from app.core.context import CallerContext
from app.core.exceptions import NotFoundError, RateLimitedError
from app.infrastructure.cache import get_redis

router = APIRouter()

# Rate limit: 10 requests per 60 seconds per user
_CHAT_RATE_LIMIT = 10
_CHAT_RATE_WINDOW = 60


async def _check_chat_rate_limit(user_id: str) -> None:
    """Raise RateLimitedError if the user exceeds the chat rate limit."""
    redis = get_redis()
    key = f"rate_limit:chat:{user_id}"
    # Atomic increment -- returns the new count after incrementing
    count = await redis.incr(key)
    if count == 1:
        # First request in window -- set the TTL
        await redis.expire(key, _CHAT_RATE_WINDOW)
    if count > _CHAT_RATE_LIMIT:
        raise RateLimitedError(f"Chat rate limit exceeded. Try again in {_CHAT_RATE_WINDOW} seconds.")


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    ctx: CallerContext = Depends(require_permission("chat.use")),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Process a chat message through the AI agent.

    Creates or continues a conversation session. The agent may call data
    retrieval tools and returns a synthesised response with source
    attribution.
    """
    await _check_chat_rate_limit(str(ctx.user_id))

    dto = await service.process_message(
        ctx=ctx,
        session_id=body.session_id,
        message=body.message,
    )

    return ChatResponse(
        session_id=dto.session_id,
        message=MessageSchema(role=dto.role, content=dto.message),
        sources=[
            SourceAttributionSchema(
                table=s.table,
                record_id=s.record_id,
                fields_used=s.fields_used,
            )
            for s in dto.sources
        ],
        tool_calls=[
            ToolCallSchema(
                tool=tc.tool,
                input=tc.input,
                result_count=tc.result_count,
            )
            for tc in dto.tool_calls
        ],
    )


@router.get("/sessions", response_model=list[SessionSummarySchema])
async def list_sessions(
    ctx: CallerContext = Depends(require_permission("chat.use")),
    service: ChatService = Depends(get_chat_service),
) -> list[SessionSummarySchema]:
    """List the current user's chat sessions, most recent first."""
    sessions = await service._chat_repo.get_user_sessions(ctx.user_id, limit=50)
    return [
        SessionSummarySchema(
            id=s.id,
            title=s.title,
            message_count=s.message_count,
            last_message_at=s.last_message_at,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionDetailSchema)
async def get_session(
    session_id: UUID,
    ctx: CallerContext = Depends(require_permission("chat.use")),
    service: ChatService = Depends(get_chat_service),
) -> SessionDetailSchema:
    """Get a specific chat session with all messages. Only the owning user can access it."""
    session = await service._chat_repo.get_with_messages(session_id)
    if session is None or session.user_id != ctx.user_id:
        raise NotFoundError("ChatSession", session_id)

    sorted_messages = sorted(session.messages, key=lambda m: m.created_at)

    def _parse_sources(raw: list | dict | None) -> list[SourceAttributionSchema]:
        if not raw:
            return []
        items = raw if isinstance(raw, list) else [raw]
        return [
            SourceAttributionSchema(
                table=s.get("table", ""),
                record_id=s.get("record_id", ""),
                fields_used=s.get("fields_used", {}),
            )
            for s in items
        ]

    def _parse_tool_calls(raw: list | dict | None) -> list[ToolCallSchema]:
        if not raw:
            return []
        items = raw if isinstance(raw, list) else [raw]
        return [
            ToolCallSchema(
                tool=tc.get("tool", ""),
                input=tc.get("input", {}),
                result_count=tc.get("result_count"),
            )
            for tc in items
        ]

    return SessionDetailSchema(
        id=session.id,
        title=session.title,
        message_count=session.message_count,
        last_message_at=session.last_message_at,
        created_at=session.created_at,
        messages=[
            SessionMessageSchema(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=_parse_sources(m.sources),
                tool_calls=_parse_tool_calls(m.tool_calls),
                created_at=m.created_at,
            )
            for m in sorted_messages
        ],
    )

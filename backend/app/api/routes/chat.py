"""Chat route for the conversational agent context."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.client import AnthropicClient
from app.api.dependencies import CurrentUserDTO, get_db, require_permission
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageSchema,
    SourceAttributionSchema,
    ToolCallSchema,
)
from app.application.services.chat import ChatService
from app.config import get_settings
from app.core.exceptions import RateLimitedError
from app.infrastructure.cache import get_redis
from app.infrastructure.repositories.chat import SqlAlchemyChatSessionRepository

router = APIRouter()

# Rate limit: 10 requests per 60 seconds per user
_CHAT_RATE_LIMIT = 10
_CHAT_RATE_WINDOW = 60


async def _check_chat_rate_limit(user_id: str) -> None:
    """Raise RateLimitedError if the user exceeds the chat rate limit."""
    redis = get_redis()
    key = f"rate_limit:chat:{user_id}"
    current = await redis.get(key)
    if current is not None and int(current) >= _CHAT_RATE_LIMIT:
        raise RateLimitedError(f"Chat rate limit exceeded. Try again in {_CHAT_RATE_WINDOW} seconds.")
    # Increment counter; set TTL on first request in window
    await redis._client.incr(key)
    if current is None:
        await redis._client.expire(key, _CHAT_RATE_WINDOW)


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: CurrentUserDTO = Depends(require_permission("chat.use")),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Process a chat message through the AI agent.

    Creates or continues a conversation session. The agent may call data
    retrieval tools and returns a synthesised response with source
    attribution.
    """
    await _check_chat_rate_limit(str(user.id))

    settings = get_settings()
    client = AnthropicClient(
        api_key=settings.ANTHROPIC_API_KEY,
        model=settings.ANTHROPIC_MODEL,
    )
    chat_repo = SqlAlchemyChatSessionRepository(db)
    service = ChatService(chat_repo=chat_repo, client=client)

    dto = await service.process_message(
        user_id=user.id,
        session_id=body.session_id,
        message=body.message,
        permissions=user.permissions,
        user_name=user.full_name,
        role_name=user.role,
        db=db,
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

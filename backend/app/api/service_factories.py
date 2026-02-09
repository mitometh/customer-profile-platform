"""FastAPI dependency factories for application services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.application.services.auth import AuthService
from app.application.services.chat import ChatService
from app.application.services.customer import CustomerService
from app.application.services.event import EventService
from app.application.services.ingestion import IngestionService
from app.application.services.metric import MetricQueryService
from app.application.services.role import RoleService
from app.application.services.source import SourceService
from app.application.services.user import UserService
from app.infrastructure.repositories.chat import SqlAlchemyChatSessionRepository
from app.infrastructure.repositories.customer import SqlAlchemyCustomerRepository
from app.infrastructure.repositories.event import SqlAlchemyEventRepository
from app.infrastructure.repositories.metric import (
    SqlAlchemyCustomerMetricHistoryRepository,
    SqlAlchemyCustomerMetricRepository,
    SqlAlchemyMetricDefinitionRepository,
)
from app.infrastructure.repositories.role import SqlAlchemyRoleRepository
from app.infrastructure.repositories.source import (
    RedisTokenCache,
    SqlAlchemySourceRepository,
)
from app.infrastructure.repositories.user import SqlAlchemyUserRepository


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """Build an AuthService with its repository dependencies."""
    user_repo = SqlAlchemyUserRepository(db)
    role_repo = SqlAlchemyRoleRepository(db)
    return AuthService(user_repo=user_repo, role_repo=role_repo)


async def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    """Build a UserService with its repository dependencies."""
    user_repo = SqlAlchemyUserRepository(db)
    role_repo = SqlAlchemyRoleRepository(db)
    return UserService(user_repo=user_repo, role_repo=role_repo)


async def get_customer_service(
    db: AsyncSession = Depends(get_db),
) -> CustomerService:
    """Build a CustomerService with its repository dependencies."""
    customer_repo = SqlAlchemyCustomerRepository(db)
    event_repo = SqlAlchemyEventRepository(db)
    metric_repo = SqlAlchemyCustomerMetricRepository(db)
    return CustomerService(customer_repo=customer_repo, event_repo=event_repo, metric_repo=metric_repo)


async def get_chat_service(
    db: AsyncSession = Depends(get_db),
) -> ChatService:
    """Build a ChatService with its repository and LLM client dependencies."""
    from app.agent.client import AnthropicClient
    from app.config import get_settings

    settings = get_settings()
    client = AnthropicClient(api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_MODEL)
    chat_repo = SqlAlchemyChatSessionRepository(db)
    return ChatService(chat_repo=chat_repo, client=client, session=db)


async def get_event_service(
    db: AsyncSession = Depends(get_db),
) -> EventService:
    """Build an EventService with its repository dependencies."""
    event_repo = SqlAlchemyEventRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    return EventService(event_repo=event_repo, customer_repo=customer_repo)


async def get_metric_query_service(
    db: AsyncSession = Depends(get_db),
) -> MetricQueryService:
    """Build a MetricQueryService with its repository dependencies."""
    definition_repo = SqlAlchemyMetricDefinitionRepository(db)
    metric_repo = SqlAlchemyCustomerMetricRepository(db)
    history_repo = SqlAlchemyCustomerMetricHistoryRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    return MetricQueryService(
        definition_repo=definition_repo,
        metric_repo=metric_repo,
        history_repo=history_repo,
        customer_repo=customer_repo,
    )


async def get_role_service(
    db: AsyncSession = Depends(get_db),
) -> RoleService:
    """Build a RoleService with its repository dependencies."""
    role_repo = SqlAlchemyRoleRepository(db)
    return RoleService(role_repo=role_repo)


async def get_source_service(
    db: AsyncSession = Depends(get_db),
) -> SourceService:
    """Build a SourceService with its repository dependencies."""
    from app.infrastructure.cache import get_redis

    source_repo = SqlAlchemySourceRepository(db)
    token_cache = RedisTokenCache(get_redis())
    return SourceService(source_repo=source_repo, token_cache=token_cache)


async def get_ingestion_service(
    db: AsyncSession = Depends(get_db),
) -> IngestionService:
    """Build an IngestionService with its repository, cache, and broker dependencies."""
    from app.infrastructure.broker import get_publisher
    from app.infrastructure.cache import get_redis

    source_repo = SqlAlchemySourceRepository(db)
    token_cache = RedisTokenCache(get_redis())
    broker = get_publisher()
    return IngestionService(source_repo=source_repo, token_cache=token_cache, broker=broker)

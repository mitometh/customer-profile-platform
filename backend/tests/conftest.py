"""Shared test fixtures for the Customer 360 backend test suite.

Provides:
- Async SQLite in-memory database engine + session
- FastAPI TestClient wired to the test database
- Auth helpers (JWT generation, authenticated clients)
- Factory imports
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles

from app.config import Settings
from app.infrastructure.models.base import Base
from app.infrastructure.security import create_access_token, hash_password

# ---------------------------------------------------------------------------
# Make PostgreSQL JSONB work with SQLite in tests
# ---------------------------------------------------------------------------


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return compiler.visit_JSON(JSON(), **kw)


# ---------------------------------------------------------------------------
# Override settings for tests
# ---------------------------------------------------------------------------

_test_settings = Settings(
    DATABASE_URL="sqlite+aiosqlite:///",
    REDIS_URL="redis://localhost:6379/15",
    RABBITMQ_URL="amqp://guest:guest@localhost:5672/",
    JWT_SECRET="test-secret-key",
    JWT_ALGORITHM="HS256",
    JWT_EXPIRY_MINUTES=60,
    ANTHROPIC_API_KEY="test-key",
    ANTHROPIC_MODEL="claude-sonnet-4-20250514",
    LOG_LEVEL="WARNING",
    LOG_FORMAT="console",
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test async engine using SQLite in-memory."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///",
        echo=False,
    )
    # Import all models so Base.metadata is populated
    import app.infrastructure.models

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional test session that rolls back after each test."""
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# App + client fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def app(db):
    """Create a FastAPI app wired to the test database session."""
    from unittest.mock import patch

    from app.main import create_app

    test_app = create_app()

    # Override database dependency
    async def override_get_db():
        yield db

    from app.api.dependencies import get_db

    test_app.dependency_overrides[get_db] = override_get_db

    # Patch settings
    with patch("app.config.get_settings", return_value=_test_settings):
        yield test_app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def make_token(user_id: UUID | None = None) -> str:
    """Generate a JWT for testing."""
    from unittest.mock import patch

    with patch("app.config.get_settings", return_value=_test_settings):
        uid = user_id or uuid4()
        return create_access_token(data={"sub": str(uid)})


def auth_headers(token: str) -> dict[str, str]:
    """Return Authorization headers dict for a given token."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def seeded_roles(db: AsyncSession):
    """Insert basic roles and permissions for tests."""
    from app.infrastructure.models.role import (
        PermissionModel,
        RoleModel,
        RolePermissionModel,
    )

    # Permissions
    perms = {}
    for code in [
        "customers.read",
        "customers.manage",
        "events.read",
        "metrics.read",
        "metrics.catalog.read",
        "metrics.catalog.manage",
        "chat.use",
        "users.read",
        "users.manage",
        "sources.read",
        "sources.manage",
        "ingestion.write",
        "admin.all",
        "alerts.read",
        "reports.read",
    ]:
        p = PermissionModel(id=uuid4(), code=code, description=f"Test {code}")
        db.add(p)
        perms[code] = p

    await db.flush()

    # Roles
    admin_role = RoleModel(id=uuid4(), name="admin",
                           display_name="Admin", description="Full access")
    sales_role = RoleModel(id=uuid4(), name="sales",
                           display_name="Sales", description="Sales team")
    db.add_all([admin_role, sales_role])
    await db.flush()

    # Admin gets all permissions
    for perm in perms.values():
        db.add(RolePermissionModel(role_id=admin_role.id, permission_id=perm.id))

    # Sales gets limited permissions
    for code in ["customers.read", "events.read", "metrics.read", "metrics.catalog.read", "chat.use"]:
        db.add(RolePermissionModel(
            role_id=sales_role.id, permission_id=perms[code].id))

    await db.flush()

    return {"admin": admin_role, "sales": sales_role, "perms": perms}


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession, seeded_roles):
    """Create an admin user and return (user_model, token, permissions)."""
    from app.infrastructure.models.user import UserModel

    user = UserModel(
        id=uuid4(),
        email="admin@test.com",
        full_name="Test Admin",
        password_hash=hash_password("Password123"),
        role_id=seeded_roles["admin"].id,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    token = make_token(user.id)
    all_perms = list(seeded_roles["perms"].keys())
    return user, token, all_perms


@pytest_asyncio.fixture
async def sales_user(db: AsyncSession, seeded_roles):
    """Create a sales user and return (user_model, token, permissions)."""
    from app.infrastructure.models.user import UserModel

    user = UserModel(
        id=uuid4(),
        email="sales@test.com",
        full_name="Test Sales",
        password_hash=hash_password("Password123"),
        role_id=seeded_roles["sales"].id,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    token = make_token(user.id)
    sales_perms = [
        "customers.read",
        "events.read",
        "metrics.read",
        "metrics.catalog.read",
        "chat.use",
    ]
    return user, token, sales_perms


@pytest_asyncio.fixture
async def sample_customer(db: AsyncSession):
    """Insert a sample customer for tests."""
    from decimal import Decimal

    from app.infrastructure.models.customer import CustomerModel

    customer = CustomerModel(
        id=uuid4(),
        company_name="Acme Corp",
        contact_name="John Doe",
        email="john@acme.com",
        phone="+1-555-0100",
        industry="Technology",
        contract_value=Decimal("50000.00"),
        currency_code="USD",
        signup_date=datetime(2024, 1, 15).date(),
    )
    db.add(customer)
    await db.flush()
    return customer


@pytest_asyncio.fixture
async def sample_events(db: AsyncSession, sample_customer):
    """Insert sample events for the sample customer."""
    from app.infrastructure.models.event import EventModel

    events = []
    for i in range(5):
        event = EventModel(
            id=uuid4(),
            customer_id=sample_customer.id,
            event_type="support_ticket" if i % 2 == 0 else "meeting",
            title=f"Event {i}",
            description=f"Description for event {i}",
            occurred_at=datetime(2024, 6, 15 + i, tzinfo=UTC),
            data={"priority": "high" if i == 0 else "normal"},
        )
        db.add(event)
        events.append(event)

    await db.flush()
    return events


@pytest_asyncio.fixture
async def sample_metrics(db: AsyncSession, sample_customer):
    """Insert sample metric definitions and customer metrics."""
    from decimal import Decimal

    from app.infrastructure.models.metric import (
        CustomerMetricModel,
        MetricDefinitionModel,
    )

    # Metric definitions
    support_tickets_def = MetricDefinitionModel(
        id=uuid4(),
        name="support_tickets_last_30d",
        display_name="Support Tickets (30d)",
        description="Number of support tickets in last 30 days",
        unit="count",
        value_type="integer",
    )
    health_score_def = MetricDefinitionModel(
        id=uuid4(),
        name="health_score",
        display_name="Health Score",
        description="Composite health score 0-100",
        unit="score",
        value_type="integer",
    )
    days_since_def = MetricDefinitionModel(
        id=uuid4(),
        name="days_since_last_contact",
        display_name="Days Since Contact",
        description="Days since last customer interaction",
        unit="days",
        value_type="integer",
    )
    db.add_all([support_tickets_def, health_score_def, days_since_def])
    await db.flush()

    # Customer metrics
    metrics = [
        CustomerMetricModel(
            id=uuid4(),
            customer_id=sample_customer.id,
            metric_definition_id=support_tickets_def.id,
            metric_value=Decimal("3"),
        ),
        CustomerMetricModel(
            id=uuid4(),
            customer_id=sample_customer.id,
            metric_definition_id=health_score_def.id,
            metric_value=Decimal("75"),
        ),
        CustomerMetricModel(
            id=uuid4(),
            customer_id=sample_customer.id,
            metric_definition_id=days_since_def.id,
            metric_value=Decimal("5"),
        ),
    ]
    db.add_all(metrics)
    await db.flush()

    return {
        "definitions": {
            "support_tickets": support_tickets_def,
            "health_score": health_score_def,
            "days_since": days_since_def,
        },
        "customer_metrics": metrics,
    }

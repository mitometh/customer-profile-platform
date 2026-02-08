# Coding Standards & Conventions

**Source of truth**: `contracts/v1/` (26 YAML files)
**Stack**: Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Redis, RabbitMQ, Anthropic Claude

---

## 1. Architecture — Layer-First

Four layers plus one standalone agent package. Each layer exists **once** at the top level. Bounded context separation is by **file naming**, not by repeated folder trees.

```
┌───────────────────────────────────────────────────────────┐
│  API Layer (app/api/)                                     │
│  FastAPI routes, Pydantic schemas, middleware, deps       │
├───────────────────────────────────────────────────────────┤
│  Application Layer (app/application/)                     │
│  Services, DTOs, scheduled jobs                           │
├───────────────────────────────────────────────────────────┤
│  Infrastructure Layer (app/infrastructure/)                │
│  SQLAlchemy models & repos, Redis, RabbitMQ, JWT, bcrypt  │
├───────────────────────────────────────────────────────────┤
│  Core Layer (app/core/)                                   │
│  Exceptions, value types, enums, event protocols          │
└───────────────────────────────────────────────────────────┘
  + Agent Package (app/agent/) — LLM integration
```

**Dependency rule**: imports flow downward only.

```
api/ → application/ → infrastructure/ → core/
api/ → agent/ → application/
```

Core has zero external dependencies. Infrastructure implements core protocols. Application orchestrates infrastructure directly (no Protocol indirection between application and infrastructure). API is the composition root.

---

## 2. Layer Rules

| Layer | Owns | Does NOT |
|-------|------|----------|
| **Core** (`app/core/`) | Exceptions, value types, enums, `DomainEvent` base, `EventBus` protocol, `UnitOfWork` protocol | Import any external library |
| **Infrastructure** (`app/infrastructure/`) | SQLAlchemy models, repositories, Redis client, RabbitMQ broker, JWT/bcrypt, structlog, event bus impl | Contain business rules or validation logic |
| **Application** (`app/application/`) | Services (use-case orchestration), DTOs (where transformation needed), scheduled jobs, Gate 2 permission checks | Know about HTTP, SQL, or any I/O implementation details |
| **API** (`app/api/`) | HTTP routing, request parsing, response serialization, middleware, dependency injection wiring | Contain business logic or call repositories directly |
| **Agent** (`app/agent/`) | LLM client, orchestrator, retriever, tool definitions, system prompts, Gate 1 tool filtering | Bypass application services for data access |

---

## 3. Bounded Contexts

Six bounded contexts from `contracts/v1/domain/context-map.yaml`. Context boundaries are maintained by **consistent file naming** across layers (e.g., `customer.py` in models/, repositories/, services/, schemas/, routes/).

| Bounded Context | File Prefix | Aggregate Roots |
|----------------|-------------|-----------------|
| Identity & Access | `user`, `auth`, `role` | User, Role, Permission, RolePermission |
| Customer Management | `customer` | Customer |
| Activity Tracking | `event` | Event |
| Metrics Engine | `metric` | MetricDefinition, CustomerMetric |
| Source Integration | `source`, `ingestion` | Source |
| Conversational Agent | `chat` + `agent/` | ChatSession |

**Rules**:
- No cross-context domain imports. Contexts reference each other by UUID only.
- Cross-context communication uses **direct service imports** at the application layer. No DI injection or Protocol indirection between contexts.
- Shared kernel lives in `app/core/` (exceptions, types, events).

---

## 4. Coding Patterns

### Models (Infrastructure)

```python
# app/infrastructure/models/customer.py
from app.infrastructure.models.base import Base, TimestampMixin, AuditMixin, SoftDeleteMixin

class CustomerModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "customers"
    id: Mapped[UUID] = mapped_column(pg.UUID, primary_key=True, default=uuid4)
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    contract_value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # ... remaining fields per contracts/v1/models/customer.yaml
```

Services work with SQLAlchemy models directly for simple contexts. No separate domain entity classes or ORM-to-entity mapping.

### Repositories (Infrastructure)

```python
# app/infrastructure/repositories/customer.py
class SqlAlchemyCustomerRepository(BaseRepository[CustomerModel]):
    async def search(self, query: str, pagination: Pagination) -> PaginatedResult[CustomerModel]:
        stmt = select(CustomerModel).where(CustomerModel.deleted_at.is_(None))
        if query:
            stmt = stmt.where(CustomerModel.company_name.ilike(f"%{query}%"))
        return await self._paginate(stmt, pagination)
```

Repositories are concrete SQLAlchemy classes inheriting from `BaseRepository`. No Protocol interfaces.

### Services (Application)

```python
# app/application/services/customer.py
class CustomerService:
    def __init__(self, repo: SqlAlchemyCustomerRepository, event_bus: EventBus) -> None:
        self._repo = repo
        self._event_bus = event_bus

    async def get_customer_detail(self, customer_id: UUID, permissions: list[str]) -> CustomerDetailDTO:
        if "customers.read" not in permissions:
            raise ForbiddenError("customers.read")
        customer = await self._repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError("Customer", customer_id)
        return CustomerDetailDTO.from_model(customer)
```

Gate 2 permission checks happen at the top of every service method. DTOs exist only for multi-source aggregation (customer detail, chat response, metric catalog).

### Routes (API)

```python
# app/api/routes/customers.py
@router.get("/{customer_id}", response_model=CustomerDetailSchema)
async def get_customer(
    customer_id: UUID,
    user: CurrentUserDTO = Depends(require_permission("customers.read")),
    db: AsyncSession = Depends(get_db),
) -> CustomerDetailSchema:
    service = CustomerService(repo=SqlAlchemyCustomerRepository(db), event_bus=InMemoryEventBus())
    result = await service.get_customer_detail(customer_id, user.permissions)
    return CustomerDetailSchema.from_dto(result)
```

Route handlers are thin: validate, inject, call service, return. Max 15 lines.

### Schemas (API)

```python
# app/api/schemas/customer.py
class CustomerSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_name: str
    contract_value: Decimal
    # ... remaining fields per contracts/v1/models/customer.yaml#CustomerSummary
```

Schemas are Pydantic models at the HTTP boundary. Separate from DTOs. Suffix with `Schema` for response/request models at the API layer.

---

## 5. Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files & modules | `snake_case.py` | `customer.py`, `auth.py` |
| Classes | `PascalCase` | `CustomerService` |
| ORM models | `PascalCase` + `Model` | `CustomerModel` |
| Value objects | `PascalCase` | `Email`, `Money` |
| Domain events | `PascalCase`, past tense | `UserCreated`, `EventRecorded` |
| DTOs | `PascalCase` + `DTO` | `CustomerDetailDTO`, `LoginResultDTO` |
| API schemas | `PascalCase` + `Schema` | `CustomerSummarySchema` |
| Repositories | `SqlAlchemy` + entity + `Repository` | `SqlAlchemyCustomerRepository` |
| Services | entity + `Service` | `CustomerService`, `AuthService` |
| Functions | `snake_case` | `get_by_id()`, `list_customers()` |
| Constants | `UPPER_SNAKE` | `MAX_PAGE_SIZE`, `DEFAULT_LIMIT` |
| Private | `_leading_underscore` | `_resolve_customer()` |
| Env vars | `UPPER_SNAKE` | `DATABASE_URL` |
| API paths | `kebab-case`, plural nouns | `/api/customers/{customer_id}/events` |
| DB tables | `snake_case`, plural | `customers`, `chat_messages` |
| DB columns | `snake_case` | `company_name`, `contract_value` |

---

## 6. Error Handling

### Exception Hierarchy

All exceptions live in `app/core/exceptions.py`.

```python
class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500): ...

class NotFoundError(AppError):       # 404 NOT_FOUND
class ValidationError(AppError):     # 400 VALIDATION_ERROR
class UnauthorizedError(AppError):   # 401 UNAUTHORIZED
class ForbiddenError(AppError):      # 403 FORBIDDEN
class ConflictError(AppError):       # 409 CONFLICT
class RateLimitedError(AppError):    # 429 RATE_LIMITED
class LLMUnavailableError(AppError): # 503 LLM_UNAVAILABLE
```

### Error Response Shape

Every error returns this JSON structure (per `contracts/v1/models/common.yaml`):

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Customer with id '550e8400...' not found",
    "details": {}
  }
}
```

| HTTP Status | Code |
|-------------|------|
| 400 | VALIDATION_ERROR |
| 401 | UNAUTHORIZED |
| 403 | FORBIDDEN |
| 404 | NOT_FOUND |
| 409 | CONFLICT |
| 429 | RATE_LIMITED |
| 500 | INTERNAL_ERROR |
| 503 | LLM_UNAVAILABLE |

Global `ErrorHandlerMiddleware` in `app/api/middleware.py` converts all `AppError` exceptions to HTTP responses. Routes never catch exceptions manually.

---

## 7. Database Conventions

### Soft Deletes

All deletes are soft. No physical deletes. Every query excludes `deleted_at IS NOT NULL` records, enforced in `BaseRepository`.

### Cursor-Based Pagination

All list endpoints use keyset (cursor-based) pagination. No offset. Exception: `GET /api/metrics/catalog` returns the full catalog with no pagination (small, bounded dataset).

```
Cursor = base64(json({"id": "...", "created_at": "..."}))
Decode → WHERE (created_at, id) < (cursor_ts, cursor_id)
ORDER BY created_at DESC, id DESC
Fetch limit + 1 → has_next = len(results) > limit
```

### ORM Mixins

Defined in `app/infrastructure/models/base.py`:

| Mixin | Provides | Used by |
|-------|----------|---------|
| `TimestampMixin` | `created_at`, `updated_at` | UserModel, CustomerModel, SourceModel, MetricDefinitionModel, CustomerMetricModel, ChatSessionModel |
| `AuditMixin` | `created_by`, `updated_by` | UserModel, CustomerModel, SourceModel, MetricDefinitionModel, CustomerMetricModel |
| `SoftDeleteMixin` | `deleted_at`, `deleted_by` | UserModel, CustomerModel, SourceModel, MetricDefinitionModel, CustomerMetricModel, EventModel, ChatSessionModel |

**Not applied to**: EventModel (append-only, uses `created_by` only, no `updated_at/updated_by`; uses `SoftDeleteMixin` for logical deletes), ChatMessageModel (append-only, no audit or soft delete), CustomerMetricHistoryModel (append-only, no audit or soft delete).

### Migrations

- One initial migration for all 9 tables.
- Format: `YYYY_MM_DD_HHMM_description`.
- Never edit an applied migration; create a new one.
- All PKs are UUIDv4. All timestamps are `TIMESTAMP WITH TIME ZONE` in UTC.
- `created_at`/`updated_at` set by server defaults. Never client-supplied.
- SQLAlchemy 2.0 style only (`select()`, never legacy `session.query()`).

---

## 8. API Conventions

### Request/Response

- All bodies are JSON. Field names use `snake_case`.
- Dates: ISO 8601 (`2025-01-15T10:30:00Z`).
- UUIDs: lowercase with hyphens.
- Path params: `{customer_id}`, `{metric_id}` (descriptive, not `{id}` or `{mid}`).

### Pagination Response Shape

Per `contracts/v1/models/common.yaml#pagination`:

```json
{
  "data": [...],
  "pagination": {
    "total": 42,
    "limit": 20,
    "has_next": true,
    "next_cursor": "eyJpZCI6Ii..."
  }
}
```

Exceptions to standard response wrappers (per contract):
- `GET /api/metrics/catalog` returns `{ "metrics": [...] }` — no pagination.
- `GET /api/customers/{customer_id}/metrics` returns `{ "customer_id": "...", "metrics": [...] }` — no pagination.

### HTTP Methods

- `GET` — read (idempotent)
- `POST` — create or action
- `PATCH` — partial update
- No `PUT` or `DELETE` — soft deletes via PATCH.

---

## 9. Testing Standards

### Structure

```
tests/
├── conftest.py        # DB session, test client, auth helpers
├── factories.py       # Test entity factories (one per aggregate)
├── unit/              # Service + domain logic tests (no DB, no HTTP)
│   ├── test_auth.py
│   ├── test_user.py
│   ├── test_customer.py
│   ├── test_event.py
│   ├── test_metric.py
│   ├── test_ingestion.py
│   └── test_chat.py
├── integration/       # API endpoint tests (real DB, real HTTP)
│   ├── test_auth.py
│   ├── test_customers.py
│   ├── test_events.py
│   ├── test_metrics.py
│   ├── test_chat.py
│   ├── test_ingestion.py
│   └── test_health.py
└── workers/           # Worker processing tests
    ├── test_data_store.py
    └── test_metrics.py
```

### Rules

- `pytest` + `pytest-asyncio`. All tests are async.
- **Unit tests**: service + domain logic. Mock infrastructure dependencies.
- **Integration tests**: full HTTP request/response with real database.
- Test naming: `test_<action>_<scenario>` (e.g., `test_login_invalid_credentials`).
- Factory functions for test data. No raw dict construction.
- Each test is independent. No shared state.
- Test happy path first, then edge cases, then error paths.
- Test event bus publishing in workers tests.

| Layer | Test Type | What to Assert |
|-------|-----------|----------------|
| Value objects | Unit | Validation, equality, immutability |
| Services | Unit (mocked repos) | Business logic, permission checks, DTO mapping |
| Routes | Integration | Status codes, response shapes, auth enforcement |
| Workers | Integration | Message processing, DB side effects |

---

## 10. Environment Variables

All config via `pydantic-settings` in `app/config.py` with `.env` file support.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | Yes | — | `redis://localhost:6379/0` |
| `RABBITMQ_URL` | Yes | — | `amqp://guest:guest@localhost:5672/` |
| `JWT_SECRET` | Yes | — | Secret key for JWT signing |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_MINUTES` | No | `480` | Token expiry (8 hours) |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-20250514` | Model identifier |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `LOG_FORMAT` | No | `json` | `json` for production, `console` for local dev |

---

## 11. Key Principles

- **Single Responsibility**: One class = one reason to change. Repo does data access. Service does business logic. Route does HTTP.
- **Open/Closed**: Add new metric jobs as new files. Add new event types without changing processing logic.
- **Liskov Substitution**: `InMemoryEventBus` and `RabbitMQEventBus` are interchangeable behind the `EventBus` protocol.
- **Interface Segregation**: Keep protocols focused; split only when a protocol exceeds 5-6 methods.
- **Dependency Inversion**: Core defines protocols (`EventBus`, `UnitOfWork`). Infrastructure implements them. Application imports infrastructure directly.
- **YAGNI**: No abstract factories, no plugin systems, no event sourcing. Build what contracts specify.
- **Fail Fast**: Validate at boundaries (Pydantic schemas, value object constructors). Raise exceptions early.
- **Defense in Depth**: Two-gate RBAC. LLM never sees JWT, raw permissions, or role mappings.

### Things We Never Do

- Put business logic in routes or repositories.
- Use the legacy SQLAlchemy Query API or offset pagination.
- Hard delete records or bypass soft-delete filters.
- Log credentials, tokens, or JWT payloads.
- Import one context's internals in another context's code (use UUIDs for cross-references).
- Create abstractions without a second use case.

---

## 12. Infrastructure Concerns

- **RBAC**: Roles and permissions stored in DB (`roles` + `permissions` + `role_permissions` tables). FK constraints enforce only valid permissions can be assigned. `get_current_user` loads permissions via user's `role_id` (JOIN through `role_permissions` → `permissions`), cached in Redis (TTL 5min). `require_permission` checks against loaded permissions. See `IMPLEMENTATION_PLAN.md` section 7.
- **Rate Limiting**: Chat endpoint (`POST /api/chat`) enforces rate limits. Returns 429 with `RateLimitedError`.
- **CORS**: Configured in `app/api/middleware.py`. Allow frontend origin (`http://localhost:3000` in dev).
- **Connection Pools**: Async engine uses SQLAlchemy connection pool. Redis uses connection pool. Configure pool sizes via environment.
- **Graceful Shutdown**: Workers handle SIGTERM by finishing current message before stopping. Configured in `workers/entrypoint.py`.
- **Logging**: Structured JSON via `structlog`. Every request gets a `request_id`. Never log passwords, tokens, or full credentials.

### Log Levels

| Level | When |
|-------|------|
| DEBUG | SQL queries (dev only), cache hits/misses |
| INFO | Request lifecycle, business operations, worker processing |
| WARNING | Permission denied, entity not found, degraded service |
| ERROR | Unhandled exceptions, LLM failures, worker processing failures |

---

## 13. Git Conventions

```
<type>(<context>): <short summary>

Types: feat, fix, refactor, test, docs, chore
Branch: feature/<context>-<description>, fix/<context>-<description>
```

### File Organization

- One class per file for services, repositories, models.
- Import order: stdlib, third-party, local (separated by blank lines).
- Keep files under 300 lines. Split by responsibility if longer.
- Every package has `__init__.py`.
- All type hints required (params + return). Use Python 3.12 builtins: `list[str]`, `str | None`. Never `Optional`, `List`, `Dict`.

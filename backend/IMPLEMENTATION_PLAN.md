# Backend Implementation Plan

**Contract source**: `contracts/v1/` (26 YAML files)
**Scope**: Assignment phases 1 & 2 only (phase 3 = production upgrades, out of scope)
**Standards**: See `CODING_STANDARDS.md` for patterns, naming, and conventions

---

## 1. Architecture Overview

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

**Dependency rule**: Each layer may only import from layers below it. Core has zero external dependencies. Application imports infrastructure directly (no Protocol indirection). API is the composition root.

---

## 2. Project Structure

```
backend/
├── alembic/
│   ├── versions/
│   └── env.py
│
├── app/
│   ├── main.py                              # FastAPI app factory, lifespan
│   ├── config.py                            # pydantic-settings
│   │
│   ├── core/                                # ── Domain primitives ──
│   │   ├── __init__.py
│   │   ├── exceptions.py                    # AppError, NotFoundError, ValidationError, ForbiddenError,
│   │   │                                    # UnauthorizedError, ConflictError, RateLimitedError, LLMUnavailableError
│   │   ├── types.py                         # Email, Money, Cursor, Pagination, PaginatedResult[T],
│   │   │                                    # Permission, EventType, MetricValueType, MessageRole
│   │   └── events.py                        # DomainEvent base class, EventBus protocol, UnitOfWork protocol
│   │
│   ├── infrastructure/                      # ── External integrations + persistence ──
│   │   ├── __init__.py
│   │   ├── database.py                      # Async engine, session factory, get_session()
│   │   ├── security.py                      # JWT encode/decode (python-jose), bcrypt hash/verify
│   │   ├── cache.py                         # Async Redis wrapper
│   │   ├── broker.py                        # RabbitMQ fanout publisher + base consumer
│   │   ├── event_bus.py                     # InMemoryEventBus, RabbitMQEventBus
│   │   ├── logging.py                       # structlog factory, RequestContext, RequestLoggingMiddleware
│   │   │
│   │   ├── models/                          # ALL SQLAlchemy table definitions
│   │   │   ├── __init__.py                  # Re-exports all models (Alembic auto-discovery)
│   │   │   ├── base.py                      # Base, TimestampMixin, AuditMixin, SoftDeleteMixin
│   │   │   ├── user.py                      # UserModel
│   │   │   ├── role.py                      # RoleModel, PermissionModel, RolePermissionModel
│   │   │   ├── customer.py                  # CustomerModel
│   │   │   ├── event.py                     # EventModel
│   │   │   ├── metric.py                    # MetricDefinitionModel, CustomerMetricModel,
│   │   │   │                                # CustomerMetricHistoryModel
│   │   │   ├── source.py                    # SourceModel
│   │   │   └── chat.py                      # ChatSessionModel, ChatMessageModel
│   │   │
│   │   └── repositories/                    # ALL data access implementations
│   │       ├── __init__.py
│   │       ├── base.py                      # Generic CRUD, soft-delete filtering, cursor pagination
│   │       ├── user.py                      # SqlAlchemyUserRepository
│   │       ├── role.py                      # SqlAlchemyRoleRepository (with Redis-cached permission lookup)
│   │       ├── customer.py                  # SqlAlchemyCustomerRepository (trigram search)
│   │       ├── event.py                     # SqlAlchemyEventRepository
│   │       ├── metric.py                    # SqlAlchemyMetricDefinitionRepository,
│   │       │                                # SqlAlchemyCustomerMetricRepository
│   │       ├── source.py                    # SqlAlchemySourceRepository + RedisTokenCache
│   │       └── chat.py                      # SqlAlchemyChatSessionRepository
│   │
│   ├── application/                         # ── Business logic layer ──
│   │   ├── __init__.py
│   │   │
│   │   ├── dtos/                            # DTOs only where transformation needed
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                      # LoginResultDTO, CurrentUserDTO
│   │   │   ├── customer.py                  # CustomerSummaryDTO, CustomerDetailDTO
│   │   │   ├── metric.py                    # CatalogEntryDTO, CustomerMetricDTO, TrendDTO
│   │   │   └── chat.py                      # ChatResponseDTO, SourceAttributionDTO
│   │   │
│   │   ├── services/                        # Use-case orchestration (Gate 2 checks here)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                      # AuthService (login → JWT, get_current_user)
│   │   │   ├── user.py                      # UserService (CRUD, role assignment, RBAC map)
│   │   │   ├── customer.py                  # CustomerService (list, search, 360 detail)
│   │   │   ├── event.py                     # EventService (filtered timeline queries)
│   │   │   ├── metric.py                    # MetricQueryService (catalog, customer metrics, history)
│   │   │   ├── ingestion.py                 # IngestionService (validate → publish → 202)
│   │   │   └── chat.py                      # ChatService (session mgmt, orchestration bridge)
│   │   │
│   │   └── jobs/                            # Scheduled computation
│   │       ├── __init__.py
│   │       ├── metric_recompute.py          # Recompute support_tickets_last_30d
│   │       ├── health_score.py              # Composite health score 0-100
│   │       └── days_since_contact.py        # now - max(occurred_at)
│   │
│   ├── api/                                 # ── HTTP interface layer ──
│   │   ├── __init__.py                      # Root router aggregation
│   │   ├── dependencies.py                  # get_db, get_current_user, require_permission
│   │   ├── middleware.py                     # ErrorHandlerMiddleware, CORS config, rate limiting
│   │   │
│   │   ├── schemas/                         # Pydantic request/response models
│   │   │   ├── __init__.py
│   │   │   ├── common.py                    # ErrorResponse, PaginatedResponse, PaginationParams
│   │   │   ├── auth.py                      # LoginRequest/Response, UserCreate/Update/Response
│   │   │   ├── customer.py                  # CustomerSummary/Detail response
│   │   │   ├── event.py                     # EventSummary, filter query params
│   │   │   ├── metric.py                    # Catalog, metric value, trend responses
│   │   │   ├── ingestion.py                 # IngestRequest/Response
│   │   │   └── chat.py                      # ChatRequest/Response
│   │   │
│   │   └── routes/                          # Thin route handlers
│   │       ├── __init__.py
│   │       ├── auth.py                      # POST /auth/login, GET /auth/me, CRUD /users
│   │       ├── customers.py                 # GET /customers, GET /customers/{customer_id}
│   │       ├── events.py                    # GET /customers/{customer_id}/events
│   │       ├── metrics.py                   # GET /metrics/catalog, GET /customers/{customer_id}/metrics,
│   │       │                                # GET /customers/{customer_id}/metrics/{metric_id}/history
│   │       ├── ingestion.py                 # POST /hooks/ingest
│   │       ├── chat.py                      # POST /chat
│   │       └── health.py                    # GET /health
│   │
│   └── agent/                               # ── LLM integration ──
│       ├── __init__.py
│       ├── client.py                        # AnthropicClient wrapper
│       ├── orchestrator.py                  # Orchestrator agent (user-facing, synthesizes, AB-9 context mgmt)
│       ├── retriever.py                     # Retriever agent (tool-calling, never speaks to user)
│       ├── tools.py                         # Tool definitions (calls services, does NOT enforce permissions)
│       ├── prompts.py                       # System prompt templates
│       └── rbac.py                          # Gate 1: tool filtering by role/permissions
│
├── workers/                                 # ── Worker processes ──
│   ├── __init__.py
│   ├── entrypoint.py                        # Shared worker bootstrap (connection, signal handling, graceful shutdown)
│   ├── data_store.py                        # Consumer: persist events, resolve customer
│   ├── metrics.py                           # Consumer: recalculate affected metrics
│   └── alerts.py                            # Consumer: threshold checks, log warnings
│
├── scheduler/                               # ── Scheduler process ──
│   ├── __init__.py
│   └── runner.py                            # APScheduler entry point, registers jobs
│
├── seeds/
│   └── seed.py                              # Default admin, sources, customers, events, metrics
│
├── tests/
│   ├── conftest.py                          # DB fixtures, test client, auth helpers
│   ├── factories.py                         # Test entity factories
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_user.py
│   │   ├── test_customer.py
│   │   ├── test_event.py
│   │   ├── test_metric.py
│   │   ├── test_ingestion.py
│   │   └── test_chat.py
│   ├── integration/
│   │   ├── test_auth.py
│   │   ├── test_customers.py
│   │   ├── test_events.py
│   │   ├── test_metrics.py
│   │   ├── test_chat.py
│   │   ├── test_ingestion.py
│   │   └── test_health.py
│   └── workers/
│       ├── test_data_store.py
│       └── test_metrics.py
│
├── alembic.ini
├── pyproject.toml
├── Dockerfile
└── docker-compose.yaml
```

---

## 3. Domain Model

### Aggregates

| Context | Aggregate | Key Fields | Invariants |
|---------|-----------|------------|------------|
| Identity | **User** | id, email (unique, max 255), full_name (max 255), password_hash (write-only), role_id (FK → roles), is_active, last_login_at? | Email unique across active users; cannot deactivate last admin |
| Identity | **Role** | id, name (unique, max 50), display_name (max 100), description (max 255) | name is unique natural key; seeded with 5 default roles |
| Identity | **Permission** | id, code (unique, max 50), description (max 255) | code is unique natural key (e.g. `customers.read`); seeded with 12 defaults |
| Identity | **RolePermission** (junction) | role_id (FK → roles), permission_id (FK → permissions) | (role_id, permission_id) composite PK; FK constraints enforce valid permissions only |
| Customer | **Customer** | id, company_name (max 255, trigram), contact_name (max 255), email (max 255), contract_value (decimal 12,2), currency_code (max 3), signup_date, source_id? | company_name searchable via trigram |
| Activity | **Event** (append-only) | id, customer_id, source_id, event_type (enum), title (max 255), description?, occurred_at, data? (JSONB) | Immutable after creation (no updated_at); event_type extensible |
| Metrics | **MetricDefinition** | id, name (unique, max 100), display_name (max 255), description, unit (max 50), value_type (enum) | name is unique natural key |
| Metrics | **CustomerMetric** | id, customer_id, metric_definition_id, metric_value (decimal precision 4), note? | (customer_id, metric_definition_id) unique |
| Metrics | **CustomerMetricHistory** (append-only) | id, customer_id, metric_definition_id, metric_value (decimal precision 4), recorded_at | No audit, no soft delete |
| Ingestion | **Source** | id, name (unique, max 100), description?, api_token_hash (write-only), is_active | api_token_hash never in any response; deactivated source rejects ingests |
| Agent | **ChatSession** | id, user_id, last_message_at, message_count, is_active | Session belongs to one user; message_count in sync |
| Agent | **ChatMessage** (append-only, owned by session) | id, session_id, role (enum), content, sources? (JSONB), tool_calls? (JSONB), created_at | Append-only, never modified |

**EventType extensibility**: The contract specifies `extensible: true`. Use a string column (not a Python enum) to allow new event types without code changes. Validate known types at ingestion but accept unknown types.

### Value Objects

All defined in `app/core/types.py` as frozen dataclasses or enums.

| Value Object | Fields | Validation |
|-------------|--------|------------|
| `Email` | address: str | Format validation, max 255 |
| `Money` | amount: Decimal, currency: str | amount >= 0, ISO 4217 |
| `Cursor` | value: str | Base64-encoded keyset pointer |
| `Pagination` | cursor: str \| None, limit: int | 1 <= limit <= 100 |
| `PaginatedResult[T]` | data: list[T], total: int \| None, has_next: bool, next_cursor: str \| None | — |
| `Permission` | value: str | Format: `resource.action` |
| `EventType` | value: str | Known: support_ticket, meeting, usage_event (extensible) |
| `MetricValueType` | value: str | Enum: integer, decimal, percentage |
| `MessageRole` | value: str | Enum: user, assistant |
| `UserContext` | user_name, role, capabilities_summary, available_tools | Injected per-request, never in LLM channel |

**UserContext note**: Contains `capabilities_summary` (human-readable string for system prompt) and `available_tools` (filtered tool list). Does NOT contain raw `permissions` — permissions stay on the app channel only.

### Domain Events

| Event | Context | Raised When | Consumed By |
|-------|---------|-------------|-------------|
| `UserCreated` | Identity | New user registered | Logging |
| `UserDeactivated` | Identity | User deactivated | Agent (invalidate sessions) |
| `UserLoggedIn` | Identity | Successful login | Logging (audit trail) |
| `CustomerCreated` | Customer | Customer added | Metrics (initial compute) |
| `CustomerUpdated` | Customer | Customer modified | — |
| `EventRecorded` | Activity | Event persisted to DB | Metrics (recompute) |
| `MetricRecomputed` | Metrics | Metric value updated | Alerts (threshold check) |
| `EventIngested` | Ingestion | Webhook accepted, published to broker | Workers (data_store, metrics, alerts) |
| `SourceDeactivated` | Ingestion | Source set inactive | Cache (invalidate token) |
| `MessageSent` | Agent | Chat message stored | Logging |
| `SessionCreated` | Agent | New chat session | Logging |

---

## 4. Database Tables

All models in one initial migration. All SQLAlchemy models in `app/infrastructure/models/`.

| Table | Mixins | Write Pattern | Indexes |
|-------|--------|--------------|---------|
| `roles` | Timestamp + SoftDelete | Seed + CRUD | (name) unique |
| `permissions` | None | Seed only | (code) unique |
| `role_permissions` | None | Seed + CRUD | (role_id, permission_id) composite PK |
| `users` | Timestamp + Audit + SoftDelete | CRUD | (email) unique, (role_id) FK |
| `customers` | Timestamp + Audit + SoftDelete | CRUD | (company_name) trigram |
| `events` | created_at + created_by + SoftDelete | Append + logical delete | (customer_id, occurred_at DESC), (customer_id, event_type, occurred_at DESC) |
| `sources` | Timestamp + Audit + SoftDelete | CRUD | (name) unique |
| `metric_definitions` | Timestamp + Audit + SoftDelete | CRUD | (name) unique |
| `customer_metrics` | Timestamp + Audit + SoftDelete | Upsert | (customer_id, metric_definition_id) unique |
| `customer_metric_history` | None (recorded_at only) | Append-only | (customer_id, metric_definition_id, recorded_at) |
| `chat_sessions` | Timestamp + SoftDelete | CRUD | (user_id) |
| `chat_messages` | None (created_at only) | Append-only | (session_id) |

---

## 5. API Endpoints

| Method | Path | Auth | Permission | Query Params | Response Notes | Phase |
|--------|------|------|-----------|--------------|----------------|-------|
| POST | `/api/auth/login` | No | — | — | `{ access_token, token_type, user: CurrentUser }` | 1 |
| GET | `/api/auth/me` | JWT | — | — | `CurrentUser` | 1 |
| POST | `/api/users` | JWT | `users.manage` | — | `UserSummary` (201) | 2 |
| PATCH | `/api/users/{id}` | JWT | `users.manage` | — | `UserSummary` | 2 |
| GET | `/api/users` | JWT | `users.read` | cursor, limit | `{ data: UserSummary[], pagination }` | 2 |
| GET | `/api/customers` | JWT | `customers.read` | search?, cursor, limit | `{ data: CustomerSummary[], pagination }` | 1 |
| GET | `/api/customers/{customer_id}` | JWT | `customers.read` | — | `CustomerDetail` (profile + recent_events + metrics) | 1 |
| GET | `/api/customers/{customer_id}/events` | JWT | `events.read` | event_type?, since?, until?, order? (default desc), cursor, limit | `{ data: EventSummary[], pagination }` | 1 |
| POST | `/api/chat` | JWT | `chat.use` | — | `{ session_id, message, sources?, tool_calls? }` | 1 |
| GET | `/api/health` | No | — | — | `{ status, version, checks: { database, llm_provider, redis, message_broker } }` | 1 |
| POST | `/hooks/ingest` | Token | — | — | `{ status: "accepted", event_id }` (202) | 2 |
| GET | `/api/metrics/catalog` | JWT | `metrics.catalog.read` | — | `{ metrics: MetricCatalogEntry[] }` (no pagination) | 2 |
| GET | `/api/customers/{customer_id}/metrics` | JWT | `metrics.read` | — | `{ customer_id, metrics: CustomerMetricValue[] }` (no pagination) | 2 |
| GET | `/api/customers/{customer_id}/metrics/{metric_id}/history` | JWT | `metrics.read` | since?, until?, limit? (default 90, max 365) | `CustomerMetricTrend` | 2 |

---

## 6. Infrastructure Components

### Event Bus

Two implementations behind `EventBus` protocol (defined in `app/core/events.py`):
- **InMemoryEventBus**: Within-process domain events (e.g., `EventRecorded` triggers metric recompute).
- **RabbitMQEventBus**: Cross-process ingestion fan-out to workers.

### Message Broker (RabbitMQ)

- **Exchange**: `events.fanout` (fanout type)
- **Queues**: `q.data-store`, `q.metrics`, `q.alerts` — each bound to the exchange
- **Message format**: JSON-serialized `EventEnvelope`
- **Implementation**: `app/infrastructure/broker.py`

### Cache (Redis)

- **Purpose**: Source token validation cache (TTL 5min)
- **Pattern**: Cache-aside (check Redis first, DB fallback on miss, write to Redis)
- **Implementation**: `app/infrastructure/cache.py` (async redis-py wrapper)
- **Usage**: `app/infrastructure/repositories/source.py` (RedisTokenCache)

### Logging

- Structured JSON via `structlog` in `app/infrastructure/logging.py`
- `RequestLoggingMiddleware`: generates `request_id` (UUID) per request, binds to structlog context
- Sanitizes: passwords, tokens, authorization headers
- Never log: JWT payloads, API tokens, password hashes

---

## 7. RBAC — DB-Driven, Two-Gate Architecture

Roles and permissions are stored in the database (`roles` + `permissions` + `role_permissions` tables), not hardcoded. FK constraints on `role_permissions` ensure only valid permissions can be assigned. This allows adding/modifying roles and permissions without code changes.

### Default Seed Data (5 roles, 12 permissions)

| Role | Display Name | Description |
|------|-------------|-------------|
| sales | Sales | Customer contracts, activity, and health scores for deals/renewals |
| support | Support | Tickets and customer context for better service |
| cs_manager | Customer Success Manager | Full read access to all customer data. Can export |
| ops | Operations | System health, data quality, and ingestion pipeline monitoring |
| admin | Administrator | Full platform access. Only role that can manage users and sources |

Default role-to-permission mapping (seeded via `seeds/seed.py`):

| Permission | sales | support | cs_manager | ops | admin |
|-----------|-------|---------|------------|-----|-------|
| customers.read | Y | Y | Y | Y | Y |
| customers.export | | | Y | | Y |
| events.read | Y | Y | Y | Y | Y |
| metrics.read | Y | Y | Y | Y | Y |
| metrics.catalog.read | | | Y | Y | Y |
| metrics.catalog.manage | | | | | Y |
| sources.read | | | | Y | Y |
| sources.manage | | | | | Y |
| users.read | | | | | Y |
| users.manage | | | | | Y |
| chat.use | Y | Y | Y | Y | Y |
| system.health.read | | | | Y | Y |

### Permission Resolution Flow

```
JWT (contains user_id)
  → get_current_user dependency: load user from DB → get user.role_id
  → load permissions via role_permissions JOIN permissions (cached in Redis, TTL 5min)
  → return CurrentUserDTO { id, email, role_name, permissions: ["customers.read", ...] }
  → require_permission("X") checks if "X" in permissions[]
```

### Two Gates

**Gate 1** (Soft — `app/agent/rbac.py`): Filter tool definitions by user's loaded permissions before LLM call. Unpermitted tools do not exist in the tool set. Tool-to-permission mapping lives in `app/agent/rbac.py` (code, since tools are defined in code).

**Gate 2** (Hard — `app/application/services/*.py`): Every service method checks permissions at the top. Deterministic, immune to prompt injection. This is the real security boundary.

### Redis Cache for Permissions

- Key: `role_permissions:{role_id}` → JSON array of permission strings
- TTL: 5 minutes (same Redis instance as source token cache)
- Invalidation: clear on role/permission update (if admin CRUD is added later)

---

## 8. Agent — Behavioral Rules

9 rules from `contracts/v1/behavior/agent-rules.yaml` (AB-1 through AB-9):

| Rule | Summary | Enforcement |
|------|---------|-------------|
| AB-1 | Always call a tool before answering data questions | System prompt + tool architecture |
| AB-2 | Never fabricate data when tools return no results | System prompt |
| AB-3 | List all matches for ambiguous queries | System prompt |
| AB-4 | Include source attribution in every data response | Response format |
| AB-5 | Casual messages bypass the retriever | Orchestrator logic |
| AB-6 | Agent only sees tools the user is permitted to use | Gate 1 tool injection |
| AB-7 | Service layer enforces permissions on every tool execution | Gate 2 service checks |
| AB-8 | Permission denial communicated gracefully | Orchestrator logic |
| AB-9 | Gracefully handle context window limits (sliding-window truncation) | Orchestrator logic |

---

## 9. Implementation Phases

### Phase 1 — Foundation + Core APIs

**Goal**: Auth working, customer data readable, basic chat functional.
**Stories**: US-5.1, US-1.1, US-1.2, US-1.3, US-2.1, US-2.3

#### Step 1.1: Core + Infrastructure Foundation

| Task | Location |
|------|----------|
| Project init (`pyproject.toml`) | FastAPI, SQLAlchemy 2.0, asyncpg, alembic, pydantic-settings, python-jose, bcrypt, structlog, aio-pika, redis |
| Config | `app/config.py` |
| Exceptions | `app/core/exceptions.py` — AppError, NotFoundError, ValidationError, ForbiddenError, UnauthorizedError, ConflictError, RateLimitedError, LLMUnavailableError |
| Value objects | `app/core/types.py` — Email, Money, Cursor, Pagination, PaginatedResult[T], Permission, EventType, MetricValueType, MessageRole |
| Domain events | `app/core/events.py` — DomainEvent, EventBus protocol, UnitOfWork protocol |
| DB setup | `app/infrastructure/database.py` — async engine with connection pool, session factory |
| ORM base | `app/infrastructure/models/base.py` — Base, TimestampMixin, AuditMixin, SoftDeleteMixin |
| Base repo | `app/infrastructure/repositories/base.py` — generic CRUD, soft-delete filtering, cursor pagination |
| Security | `app/infrastructure/security.py` — JWT encode/decode, bcrypt hash/verify |
| Event bus | `app/infrastructure/event_bus.py` — InMemoryEventBus |
| Logging | `app/infrastructure/logging.py` — structlog factory, RequestLoggingMiddleware |
| API deps | `app/api/dependencies.py` — get_db, get_current_user, require_permission |
| Middleware | `app/api/middleware.py` — ErrorHandlerMiddleware, CORS config, rate limiting setup |
| Common schemas | `app/api/schemas/common.py` — ErrorResponse, PaginatedResponse, PaginationParams |
| Alembic | `alembic/` — async migration environment |
| Initial migration | `alembic/versions/` — all 12 tables |

#### Step 1.2: Identity & Access

| Task | Location |
|------|----------|
| Role models | `app/infrastructure/models/role.py` — RoleModel, PermissionModel, RolePermissionModel |
| Role repo | `app/infrastructure/repositories/role.py` — SqlAlchemyRoleRepository + Redis-cached permission lookup |
| User model | `app/infrastructure/models/user.py` — UserModel (role_id FK → roles) |
| User repo | `app/infrastructure/repositories/user.py` |
| Auth DTOs | `app/application/dtos/auth.py` — LoginResultDTO, CurrentUserDTO |
| Auth service | `app/application/services/auth.py` — login, get_current_user, load permissions from DB via role repo |
| User service | `app/application/services/user.py` — CRUD, role assignment |
| Auth schemas | `app/api/schemas/auth.py` |
| Auth routes | `app/api/routes/auth.py` — POST /auth/login, GET /auth/me, POST /users, PATCH /users/{id}, GET /users |

#### Step 1.3: Customer & Activity

| Task | Location |
|------|----------|
| Customer model | `app/infrastructure/models/customer.py` |
| Customer repo | `app/infrastructure/repositories/customer.py` — trigram search |
| Customer DTOs | `app/application/dtos/customer.py` — CustomerSummaryDTO, CustomerDetailDTO |
| Customer service | `app/application/services/customer.py` — list, search, 360 detail |
| Customer schemas + routes | `app/api/schemas/customer.py`, `app/api/routes/customers.py` |
| Event model | `app/infrastructure/models/event.py` |
| Event repo | `app/infrastructure/repositories/event.py` |
| Event service | `app/application/services/event.py` — filtered timeline (event_type, since, until, order) |
| Event schemas + routes | `app/api/schemas/event.py`, `app/api/routes/events.py` |

#### Step 1.4: Conversational Agent

| Task | Location |
|------|----------|
| Chat models | `app/infrastructure/models/chat.py` — ChatSessionModel, ChatMessageModel |
| Chat repo | `app/infrastructure/repositories/chat.py` |
| Chat DTOs | `app/application/dtos/chat.py` — ChatResponseDTO, SourceAttributionDTO |
| Chat service | `app/application/services/chat.py` — session mgmt, orchestration bridge |
| LLM client | `app/agent/client.py` |
| Orchestrator | `app/agent/orchestrator.py` — user-facing agent, AB-5 casual bypass, AB-9 context window mgmt |
| Retriever | `app/agent/retriever.py` — tool-calling agent, never speaks to user |
| Tool defs | `app/agent/tools.py` — tool definitions, calls services |
| Prompts | `app/agent/prompts.py` — system prompt templates with UserContext (capabilities_summary) |
| Gate 1 | `app/agent/rbac.py` — tool filtering by role/permissions |
| Chat schemas + routes | `app/api/schemas/chat.py`, `app/api/routes/chat.py` |

#### Step 1.5: System Health

| Task | Location |
|------|----------|
| Health route | `app/api/routes/health.py` — GET /health, ping DB, Redis, RabbitMQ, LLM (no auth) |

#### Step 1.6: Seed Data

| Task | Location |
|------|----------|
| Seed script | `seeds/seed.py` — 12 permissions, 5 roles with role-permission mappings, admin user, 5 users (one per role), 2 sources, 10-15 customers, 50+ events, 3 metric definitions, initial metrics |

---

### Phase 2 — Ingestion + Workers + Scheduler + RBAC

**Goal**: Webhook ingestion end-to-end, workers processing events, scheduler computing metrics daily, full RBAC.
**Stories**: US-2.2, US-2.4, US-1.4, US-1.5, US-3.1, US-3.2, US-3.3, US-4.1, US-5.2, US-5.3, US-5.4, US-5.5, US-5.6, US-5.7, US-5.8

#### Step 2.1: Ingestion + Message Broker

| Task | Location |
|------|----------|
| Source model | `app/infrastructure/models/source.py` |
| Source repo | `app/infrastructure/repositories/source.py` — SqlAlchemySourceRepository + RedisTokenCache (TTL 5min) |
| Redis client | `app/infrastructure/cache.py` |
| Message broker | `app/infrastructure/broker.py` — RabbitMQPublisher (fanout), BaseConsumer |
| Ingestion service | `app/application/services/ingestion.py` — validate token, build EventEnvelope, publish, return 202 |
| Ingestion schemas + routes | `app/api/schemas/ingestion.py`, `app/api/routes/ingestion.py` — POST /hooks/ingest (X-Source-Token, no JWT) |

#### Step 2.2: Workers

All workers share backend Docker image, differentiated by entrypoint.

| Worker | File | Queue | Behavior |
|--------|------|-------|----------|
| data-store | `workers/data_store.py` | `q.data-store` | Resolve customer_identifier (case-insensitive company_name, then email). Persist event. No match: store with customer_id=NULL, log warning. Raise `EventRecorded`. |
| metrics | `workers/metrics.py` | `q.metrics` | Recompute affected customer metrics. Upsert customer_metrics + append customer_metric_history. Raise `MetricRecomputed`. |
| alerts | `workers/alerts.py` | `q.alerts` | Check thresholds (health_score < 40 = at-risk). Assignment scope: logging only. |

#### Step 2.3: Scheduler

| Task | Location |
|------|----------|
| Runner | `scheduler/runner.py` — APScheduler, daily cron trigger |
| Metric recompute | `app/application/jobs/metric_recompute.py` — support_tickets_last_30d |
| Health score | `app/application/jobs/health_score.py` — composite 0-100 |
| Days since contact | `app/application/jobs/days_since_contact.py` — now - max(occurred_at) |

Each job writes snapshots to `customer_metric_history`.

#### Step 2.4: Metrics API

| Task | Location |
|------|----------|
| Metric models | `app/infrastructure/models/metric.py` |
| Metric repos | `app/infrastructure/repositories/metric.py` |
| Metric DTOs | `app/application/dtos/metric.py` — CatalogEntryDTO, CustomerMetricDTO, TrendDTO |
| Metric service | `app/application/services/metric.py` — catalog (no pagination), customer metrics, history trend |
| Metric schemas + routes | `app/api/schemas/metric.py`, `app/api/routes/metrics.py` |

---

## 10. Docker Services

```yaml
services:
  postgres:        # Port 5432
  redis:           # Port 6379
  rabbitmq:        # Ports 5672 (AMQP), 15672 (management)
  backend:         # Port 8000 — uvicorn app.main:create_app
  worker-data:     # Same image — python -m workers.entrypoint data_store
  worker-metrics:  # Same image — python -m workers.entrypoint metrics
  worker-alerts:   # Same image — python -m workers.entrypoint alerts
  scheduler:       # Same image — python -m scheduler.runner
  frontend:        # Port 3000 — Preact app
```

---

## 11. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Folder structure | Layer-first (core, infrastructure, application, api) | Bounded contexts by file naming, not folder trees |
| Domain model | No separate entity classes; services use SQLAlchemy models + DTOs | Pragmatic — avoids ORM-to-entity mapping boilerplate |
| Shared kernel | `app/core/` | Exceptions, types, event protocols in one place |
| Dependency direction | Application imports infrastructure directly | No Protocol indirection between app and infra layers |
| Cross-context calls | Direct service import | No artificial injection; `chat.py` imports `customer.py` service |
| DTOs | Only where needed (4 of 7 contexts) | Simple contexts return models directly to schema layer |
| Agent package | Separate `app/agent/` at app level | LLM integration has 6+ files with internal complexity |
| Gate 2 location | Application services (`app/application/services/`) | Deterministic permission checks, immune to prompt injection |
| EventType storage | String column (not Python enum) | Contract says `extensible: true`; allows new types without deploy |
| Pagination | Cursor-based (keyset), no offset | O(1) seeks, no drift |
| Metrics catalog | No pagination | Small, bounded dataset; contract returns `{ metrics: [...] }` |
| Soft deletes | `deleted_at IS NOT NULL` filter in BaseRepository | Data preservation, enforced at infrastructure level |
| UserContext | Contains `capabilities_summary`, not raw `permissions` | Permissions stay on app channel; LLM gets human-readable summary |
| Roles & permissions | DB tables (`roles` + `permissions` + `role_permissions`) with Redis cache | Flexible — add/modify roles and permissions without code changes; FK constraints enforce valid permissions only |
| Tool-permission map | Code dict in `app/agent/rbac.py` | Tools are defined in code, so their permission mapping stays in code; reads user's DB-loaded permissions |
| Agent rules | AB-1 through AB-9 (9 rules) | AB-9 handles context window limits via sliding-window truncation |
| Permission count | 12 permissions across 5 roles | Per `contracts/v1/rbac/permissions.yaml` |

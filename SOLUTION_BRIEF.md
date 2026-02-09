## My Solution Thinking

### Webhook Ingestion
- Single webhook endpoint (`POST /hooks/ingest`) for all sources to push data into.
- Each source gets a registered name + API token. Easy to add, disconnect, or rotate keys without affecting other sources.
- Token validation is Redis-cached (TTL 5min) — avoids DB round-trip on every webhook.
- Endpoint does minimal work: validate token → publish to broker → return 202 Accepted.

### Fan-Out Processing
- **Assignment:** RabbitMQ fanout exchange → per-consumer queues. **Production:** SNS → SQS. Same 1-publish-N-consume pattern, different broker.
- Webhook publishes to the broker immediately, returns 202 — non-blocking.
- Fans out to 3 independent worker queues (data storage, metrics recalculation, alert threshold checks), so consumers process independently.

### Data Model (12 Tables)
- **Sources table** — registry of integrated sources with token auth and active/inactive status. Redis-cached for fast validation.
- **Customers table** — core profile data from CRM.
- **Events table** — dimension columns (source, type, timestamp) for filtering + single JSONB `data` field for the full payload. Flexible for any event type without schema changes. Append-only (no updates after creation).
- **Customer metrics table** — pre-computed per-customer KPIs via metric_definitions FK. Scales to any number of metrics without adding columns.
- **Metric definitions table** — self-describing catalog (name, display_name, description, unit, value_type). Agent discovers metrics dynamically — no hardcoded names in prompts.
- **Customer metric history** — append-only snapshots per recomputation for trend analysis.
- **Chat sessions + chat messages** — DB-persisted conversation history for multi-turn context. Sessions belong to a user, messages are append-only.
- **Users, roles, permissions, role_permissions** — full RBAC with 5 roles and 15 permissions.
- All mutable entities use soft delete (`deleted_at IS NOT NULL`), no physical deletes.

### Background Jobs
- **3 event-driven workers** (Docker containers sharing backend image, different entrypoints):
  - **Data Store worker** — transforms raw webhook payload, resolves customer, writes event to DB.
  - **Metrics worker** — recalculates affected customer metrics on new events.
  - **Alerts worker** — checks thresholds (e.g., 5+ tickets/week), logs warnings.
- **1 scheduler service** (APScheduler, configurable interval — default 1min in dev):
  - Daily metric recalculation (full recompute across all customers).
  - Health score computation.
  - Days-since-last-contact calculation.
- Results written to the customer metrics table via upsert + snapshot to metric history.
- For production: Lambda for SQS-triggered event processing (scales to zero), EventBridge Scheduler for daily recalculations, Fargate for long-running compute.

### AI Agent — Two-Agent Design
- **Orchestrator agent** — the primary conversational interface. Receives all user messages, maintains chat context. For data questions, it decides what data is needed and delegates to the retriever. For casual messages ("Hello", "Thanks"), it responds directly. It owns the final response — takes raw data from the retriever and synthesizes a user-facing answer with source citations.
- **Retriever agent** — pure data-fetching utility. Takes a structured data request, calls tools against the service layer (parameterized queries, not raw SQL), returns raw structured results. Never speaks to the user directly.
- The orchestrator owns the conversation; the retriever owns the data. Clear boundary, easy to debug.

### Metrics Catalog API (MCP-style)
- Backend exposes a `/api/metrics/catalog` endpoint that returns all available metrics with descriptions — like an MCP resource/tool listing.
- The orchestrator calls this before planning, so it always knows what metrics exist and what they mean. No hardcoded metric names in the prompt.
- When a new metric is added (new background job deployed), it registers itself in the catalog. The agent discovers it automatically — zero prompt changes.
- Each metric entry is self-describing: name, human-readable description, unit, value type, how to interpret it. The LLM reads this to understand what it can query.

### Conversation History
- Needed for multi-turn context — e.g., user asks about Acme Corp, then says "What about their tickets?" The agent needs to know "their" = Acme Corp.
- **DB-persisted sessions** — `chat_sessions` and `chat_messages` tables. Each session belongs to a single authenticated user. Messages are append-only (no updates, no deletes). The orchestrator receives the full message history on every call for follow-ups, pronoun resolution, and context-aware answers.
- Sessions persist across server restarts and follow the global soft-delete convention.
- For production: add streaming responses, TTL-based cleanup of old sessions, analytics on common question patterns.

### Frontend
- **Preact + TypeScript + Tailwind CSS + Vite** — lightweight, fast SPA.
- Role-adaptive UI — navigation and features adjust based on the authenticated user's permissions.
- Chat interface with session management (create, switch, view history).
- Customer browsing with list/search/detail/timeline views.
- Admin panels for user management, role viewing, and source management.

### Docker Compose (9 Services)
All services start with a single `docker compose up`:
1. **postgres** (5432) — single source of truth
2. **redis** (6379) — token cache + role-permission cache
3. **rabbitmq** (5672/15672) — fanout exchange for event processing
4. **backend** (8000) — FastAPI: REST API + Agent + Ingestion + Auth
5. **worker-data** — transforms + writes events to DB
6. **worker-metrics** — recalculates customer metrics
7. **worker-alerts** — checks thresholds + logs warnings
8. **scheduler** — periodic metric recomp, health scores, days-since-contact
9. **frontend** (3000) — Preact SPA

Workers + scheduler share the same backend image with different entrypoints.

---

### Scalability Thinking
- **Ingestion scales horizontally** — webhook endpoint is stateless, sits behind a load balancer. SNS/SQS absorbs any burst; consumers scale independently.
- **Read vs write paths are separated** — events table is append-only (write-optimized), customer_metrics table is pre-computed (read-optimized). Heavy writes don't slow down agent queries.
- **Metrics table avoids N+1 aggregation** — agent reads a single row instead of scanning millions of events. Query time stays constant as event volume grows.
- **DB can scale incrementally** — read replicas for the query/agent path, partition the events table by time range, PgBouncer for connection pooling. No application code changes.
- **Lambdas scale per-message** — each SQS message gets its own invocation. Burst of 1000 events = 1000 concurrent Lambdas, then back to zero. No idle servers.

### Cost Effectiveness Thinking
- **Lambda + SQS = pay only for what you process** — no idle compute. Low-traffic sources cost almost nothing.
- **Pre-computed metrics save LLM tokens** — the agent gets a single value lookup instead of raw event dumps. Fewer tokens in the tool result = cheaper LLM calls.
- **Orchestrator skips retriever for casual messages** — "Hello" and "Thanks" don't trigger tool calls or DB queries. Only data questions incur LLM + DB cost.
- **Redis caching on token validation** — avoids a DB round-trip per webhook. At high ingest volume, this saves significant DB load and cost.
- **Postgres over managed AI/vector DBs** — no need for expensive specialized databases when the data is structured and SQL works perfectly.
- **Conversation history TTL** — auto-expire old sessions to avoid unbounded storage growth.

### Security Thinking
- **Per-source API tokens** — each source authenticates independently. Compromised token affects only one source; revoke instantly without touching others.
- **No raw SQL from LLM** — agent uses predefined tools with typed parameters. Eliminates SQL injection and prompt injection risks on the data layer.
- **Parameterized queries only** — service layer never interpolates user input into SQL strings.
- **Source isolation** — `is_active` flag on sources table acts as a kill switch. Disable a source and all its future data is rejected at the edge.
- **Redis TTL on tokens** — even if Redis is stale, worst case is a 5-minute window before revocation takes effect. Active invalidation reduces this to near-zero.
- **JSONB for event data** — flexible schema, but sensitive fields (PII) can be encrypted at the field level before storage.
- **Two-gate RBAC** — LLM is never the security boundary. Gate 1 filters tools before the LLM sees them; Gate 2 enforces permissions in deterministic service-layer code. Even prompt injection can't bypass Gate 2.

### Auth & RBAC (Fully Implemented)
Built-in JWT auth with email+password login. Production would swap to SSO/OAuth2 — the authorization logic (two-gate enforcement) is identical.

- **Team-based roles** — 5 roles (sales, support, cs_manager, ops, admin) with 15 granular permissions in `resource.action` format.
- **LLM permission enforcement via two-channel architecture** — the hard problem: how do you enforce RBAC when users interact through an AI agent? Solution:
  - **Gate 1 (Soft/UX):** Filter the LLM's tool definitions by user permissions *before* calling the LLM. A sales user's agent literally cannot see source management tools — the LLM can't call what it doesn't know exists.
  - **Gate 2 (Hard/Security):** Service layer checks permissions on every tool execution using the user context from the JWT (passed via application memory, never through the LLM). Even if Gate 1 fails (prompt injection, bug), Gate 2 blocks unauthorized access with deterministic code.
  - **Two channels:** The user's auth token and the LLM's data travel on separate code paths. They converge only at the service layer. The LLM cannot read, forge, or manipulate the user context.
- **Role-adaptive UI** — frontend adapts navigation and available features based on the user's role/permissions.
- **Full contract references:** `contracts/v1/models/user.yaml` (roles, permissions, AgentUserContext), `contracts/v1/api/chat.yaml` (permission_enforcement, two_channel_architecture, tool_permission_map).

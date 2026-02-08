## My Solution Thinking

### Webhook Ingestion
- Single webhook endpoint for all sources to push data into.
- Each source gets a registered name + API token. Easy to add, disconnect, or rotate keys without affecting other sources.

### Fan-Out Processing (SNS → SQS)
- Webhook publishes to SNS immediately, returns 202 — non-blocking.
- SNS fans out to multiple SQS queues (data storage, metrics, alerts, etc.), so consumers process independently.

### Data Model
- **Sources table** — registry of integrated sources with token auth and active/inactive status. Redis-cached for fast validation.
- **Customers table** — core profile data from CRM.
- **Events table** — dimension columns (source, type, timestamp) for filtering + single JSONB `data` field for the full payload. Flexible for any event type without schema changes.
- **Customer metrics table** — key-value style (customer_id, metric_name, metric_value, note). Scales to any number of metrics without adding columns.

### Background Jobs
- Workers consume events and compute metrics (support ticket count, days since last contact, health score, etc.).
- Results written to the customer metrics table via upsert.
- Two modes: event-driven (near real-time) + scheduled (daily full recalculation).
- For assignment: simple in-process tasks or Celery workers.
- For production: Lambda for SQS-triggered event processing (scales to zero, pay-per-invocation), EventBridge scheduled rules for daily recalculations, ECS/Fargate for long-running or heavy compute jobs.

### AI Agent — Two-Agent Design
- **Orchestrator agent** — the primary conversational interface. Receives all user messages, maintains chat context. For data questions, it decides what data is needed and delegates to the retriever. For casual messages ("Hello", "Thanks"), it responds directly. It owns the final response — takes raw data from the retriever and synthesizes a user-facing answer with source citations.
- **Retriever agent** — pure data-fetching utility. Takes a structured data request, calls tools against the service layer (parameterized queries, not raw SQL), returns raw structured results. No conversation logic.
- The orchestrator owns the conversation; the retriever owns the data. Clear boundary, easy to debug.

### Metrics Catalog API (MCP-style)
- Backend exposes a `/api/metrics/catalog` endpoint that returns all available metrics with descriptions — like an MCP resource/tool listing.
- The orchestrator calls this before planning, so it always knows what metrics exist and what they mean. No hardcoded metric names in the prompt.
- When a new metric is added (new background job deployed), it registers itself in the catalog. The agent discovers it automatically — zero prompt changes.
- Each metric entry is self-describing: name, human-readable description, unit, value type, how to interpret it. The LLM reads this to understand what it can query.

### Conversation History
- Needed for multi-turn context — e.g., user asks about Acme Corp, then says "What about their tickets?" The agent needs to know "their" = Acme Corp.
- For the assignment: in-memory per session (dict of session_id → messages). Simple, no extra table, good enough for demo.
- For production: persist to DB (conversations table with session_id, role, content, timestamp). Enables history recall, audit trail, analytics on common questions.

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
- **Production additions** — OAuth2/JWT for API consumers, RBAC for data access, TLS everywhere, PII encryption at rest, audit logging on all data access.

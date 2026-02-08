# Customer 360 Insights Agent

A small-scale "Customer 360" system that aggregates data from multiple sources and exposes it through an AI-powered conversational interface. Ask natural language questions about your customers and get answers grounded in real data — with source citations.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An [Anthropic API key](https://console.anthropic.com/)

### Setup

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd assignment

# 2. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start everything (DB + backend + frontend + seed data)
docker compose up --build

# 4. Open the chat UI
open http://localhost:3000
```

That's it. The seed job populates the database with 5 realistic customers and their activity history on first run.

### Without Docker

```bash
# Terminal 1: Start Postgres (or use an existing instance)
docker compose up db

# Terminal 2: Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 3: Seed data
cd jobs
python seed.py

# Terminal 4: Frontend
cd frontend
npm install && npm run dev
```

## Project Structure

```
assignment/
├── ARCHITECTURE.md         # Detailed design decisions
├── SOLUTION_BRIEF.md       # Solution thinking summary
├── EFFORT_LOG.md           # Time tracking
├── README.md               # You are here
├── docker-compose.yml
├── .env.example
│
├── backend/                # Python / FastAPI
│   └── ...
│
├── frontend/               # Chat UI
│   └── ...
│
└── jobs/                   # Data ingestion & background tasks
    └── ...
```

## Example Queries

Try these in the chat interface to see the agent in action:

### Basic Lookups

```
What's the contract value for Acme Corp?
Show me the contact info for DataFlow Inc.
List all customers and their signup dates.
```

### Activity & Events

```
Show me recent activity for Acme Corp.
Which customers have had support tickets in the last 30 days?
What meetings were held with CloudNine Solutions this month?
```

### Aggregation & Comparison

```
Which customer has the highest contract value?
Show me customers who signed up in 2024.
Compare support ticket volume across all customers.
```

### Multi-Turn Conversations

```
User: Tell me about Acme Corp.
Agent: [responds with overview]
User: What about their recent tickets?
       ← agent resolves "their" = Acme Corp from context
```

### Edge Cases

```
What's the contract value for NonExistent Corp?
       → "I couldn't find a customer named 'NonExistent Corp' in the database."

Tell me a joke.
       → "I can only answer questions about customer data in our system."
```

## Architecture Overview

The system uses a **two-agent design** (Orchestrator + Retriever) with tool-calling against a PostgreSQL database:

```
User ──> Orchestrator Agent ──> Retriever Agent ──> DB Tools ──> PostgreSQL
              │                       │
              │ (conversation          │ (data fetching
              │  + planning)           │  + tool calls)
              │                       │
              └── Final Answer ◄──────┘
                  + Sources
```

**Key design choices:**

- **Tool-calling over RAG** — customer data is structured and tabular. SQL queries give exact answers, not approximate similarity matches.
- **Two agents, not one** — the orchestrator owns the conversation (greetings, follow-ups, answer synthesis). The retriever owns data fetching (tool calls, query execution). Clean separation, easier to debug.
- **Pre-defined tools, not raw SQL** — the agent calls typed functions with validated parameters. No SQL injection risk, no hallucinated queries.
- **Source attribution** — every response includes which tables/records the answer came from.

For the full design document, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Technical Choices

| Choice | Why |
|---|---|
| **Python + FastAPI** | Async support, auto-generated OpenAPI docs, excellent ecosystem for AI/ML |
| **PostgreSQL** | Robust relational DB with JSONB for flexible event payloads, trigram indexes for fuzzy name search |
| **Anthropic Claude** | Strong tool-calling support, reliable structured output, good at following system constraints |
| **Docker Compose** | Single command to run the full stack — DB, backend, frontend, seed job |

## Data Model

Five tables, each with a clear purpose:

| Table | Purpose |
|---|---|
| `sources` | Registry of integrated data sources (CRM, activity tracker, etc.) |
| `customers` | Core profile: company name, contact, email, contract value, signup date |
| `events` | Activity log: support tickets, meetings, usage events (append-only) |
| `customer_metrics` | Pre-computed KPIs: ticket count, health score, days since contact |
| `metric_definitions` | Self-describing catalog so the agent discovers metrics dynamically |

See [ARCHITECTURE.md](./ARCHITECTURE.md) for schema diagrams, index strategy, and design rationale.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/api/chat` | Send a message to the AI agent |
| `GET` | `/v1/api/customers` | List all customers |
| `GET` | `/v1/api/customers/:id` | Get customer details |
| `GET` | `/v1/api/customers/:id/events` | Get customer activity |
| `GET` | `/v1/api/metrics/catalog` | List available metrics |

## Trade-offs (Assignment vs Production)

| Area | This Assignment | Production |
|---|---|---|
| Data ingestion | Seed script | Webhook endpoint + SNS/SQS fan-out |
| Metrics | Computed on-the-fly | Pre-computed by background jobs |
| Auth | None | OAuth2/JWT + RBAC |
| Conversation history | In-memory | Persisted to DB |
| Deployment | Docker Compose | Kubernetes + auto-scaling |

Full trade-off analysis in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Bonus Features

- [x] Metrics catalog API (MCP-style dynamic discovery)
- [x] Multi-turn conversation support with session context
- [x] Source attribution on every agent response
- [ ] RAG pipeline with document embeddings (described in architecture)
- [ ] Dashboard with customer metrics (described in architecture)
- [x] New data source integration path (documented in architecture)
- [ ] Tests for data retrieval logic

## Development

```bash
# Run backend tests
cd backend && pytest

# Run with hot reload
cd backend && uvicorn main:app --reload

# Reset database and re-seed
docker compose down -v && docker compose up --build
```

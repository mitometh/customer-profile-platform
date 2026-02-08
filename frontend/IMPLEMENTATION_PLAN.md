# Frontend Implementation Plan

**Contract source**: `contracts/v1/` (26 YAML files)
**Scope**: Assignment phases 1 & 2 only (phase 3 = production upgrades, out of scope)
**Standards**: See `CODING_STANDARDS.md` for patterns, naming, and conventions
**Design system**: See `DESIGN_SYSTEM.md` for tokens, components, and visual guidelines

---

## 1. Architecture Overview

```
┌───────────────────────────────────────────────────────────────┐
│  Pages (src/pages/)                                           │
│  Route-level components, data fetching, layout composition    │
├───────────────────────────────────────────────────────────────┤
│  Features (src/features/)                                     │
│  Domain-specific UI: chat, customers, metrics, admin          │
├───────────────────────────────────────────────────────────────┤
│  Components (src/components/)                                 │
│  Shared UI primitives: buttons, inputs, tables, modals        │
├───────────────────────────────────────────────────────────────┤
│  Hooks (src/hooks/)                                           │
│  Shared state & side effects: useAuth, usePagination, useApi  │
├───────────────────────────────────────────────────────────────┤
│  API Layer (src/api/)                                         │
│  HTTP client, endpoint functions, typed request/response      │
├───────────────────────────────────────────────────────────────┤
│  Types (src/types/)                                           │
│  Shared TypeScript interfaces, API shapes, enums              │
└───────────────────────────────────────────────────────────────┘
```

**Dependency rule**: Pages import features and components. Features import components, hooks, and API. Components are self-contained primitives. Hooks import API and types. API imports types only.

```
pages/ → features/ → components/
                   → hooks/ → api/ → types/
```

---

## 2. Project Structure

```
frontend/
├── index.html                          # Vite entry point
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── .env.example
├── Dockerfile
│
├── public/
│   └── favicon.svg
│
└── src/
    ├── main.tsx                        # Preact render entry
    ├── app.tsx                         # Root component, router, providers
    │
    ├── types/                          # ── Shared TypeScript types ──
    │   ├── index.ts                    # Re-exports all types
    │   ├── api.ts                      # API response wrappers: PaginatedResponse, ErrorResponse
    │   ├── auth.ts                     # LoginRequest, LoginResponse, CurrentUser
    │   ├── customer.ts                 # CustomerSummary, CustomerDetail
    │   ├── event.ts                    # EventSummary, EventType, EventFilters
    │   ├── metric.ts                   # MetricCatalogEntry, CustomerMetricValue, MetricTrend
    │   ├── chat.ts                     # ChatRequest, ChatResponse, Source, ToolCall
    │   ├── user.ts                     # UserSummary, UserCreateRequest, UserUpdateRequest
    │   ├── source.ts                   # SourceSummary, SourceDetail, SourceCreateResponse
    │   └── role.ts                     # RoleSummary, RoleDetail, Permission
    │
    ├── api/                            # ── HTTP client layer ──
    │   ├── client.ts                   # Fetch wrapper: base URL, JWT injection, error handling
    │   ├── auth.ts                     # login(), getMe()
    │   ├── customers.ts                # listCustomers(), getCustomer()
    │   ├── events.ts                   # getCustomerEvents()
    │   ├── metrics.ts                  # getCatalog(), getCustomerMetrics(), getMetricHistory()
    │   ├── chat.ts                     # sendMessage()
    │   ├── users.ts                    # listUsers(), createUser(), updateUser()
    │   ├── sources.ts                  # listSources(), createSource(), updateSource(), deleteSource()
    │   ├── roles.ts                    # listRoles(), getRoleDetail()
    │   └── health.ts                   # getHealth()
    │
    ├── hooks/                          # ── Shared hooks ──
    │   ├── use-auth.ts                 # Auth state, login/logout, token management
    │   ├── use-api.ts                  # Generic async data fetching with loading/error states
    │   ├── use-pagination.ts           # Cursor-based pagination state
    │   ├── use-permission.ts           # Permission checking: hasPermission(), canAccess()
    │   └── use-debounce.ts             # Input debouncing for search
    │
    ├── components/                     # ── Shared UI primitives ──
    │   ├── ui/                         # Base design system components
    │   │   ├── button.tsx
    │   │   ├── input.tsx
    │   │   ├── badge.tsx
    │   │   ├── card.tsx
    │   │   ├── modal.tsx
    │   │   ├── dropdown.tsx
    │   │   ├── spinner.tsx
    │   │   ├── skeleton.tsx
    │   │   ├── toast.tsx
    │   │   ├── avatar.tsx
    │   │   └── tooltip.tsx
    │   │
    │   ├── data/                       # Data display components
    │   │   ├── data-table.tsx          # Sortable table with pagination
    │   │   ├── key-value.tsx           # Label-value pairs for detail views
    │   │   ├── empty-state.tsx         # No-data placeholder
    │   │   ├── error-state.tsx         # Error display with retry
    │   │   └── pagination-controls.tsx # Cursor-based prev/next
    │   │
    │   ├── layout/                     # Layout components
    │   │   ├── app-shell.tsx           # Sidebar + header + main content
    │   │   ├── sidebar.tsx             # Navigation sidebar (role-adaptive)
    │   │   ├── header.tsx              # Top bar: user info, search, logout
    │   │   ├── page-header.tsx         # Page title + breadcrumbs + actions
    │   │   └── auth-guard.tsx          # Redirect to login if unauthenticated
    │   │
    │   └── feedback/                   # User feedback components
    │       ├── loading-overlay.tsx
    │       ├── confirmation-dialog.tsx
    │       └── status-indicator.tsx    # Health status dots (up/down)
    │
    ├── features/                       # ── Domain feature modules ──
    │   │
    │   ├── auth/                       # Login + session
    │   │   ├── login-form.tsx
    │   │   └── user-menu.tsx           # Avatar + role + logout dropdown
    │   │
    │   ├── chat/                       # AI chat interface
    │   │   ├── chat-container.tsx      # Full chat layout: messages + input
    │   │   ├── message-list.tsx        # Scrollable message history
    │   │   ├── message-bubble.tsx      # Single message (user or assistant)
    │   │   ├── chat-input.tsx          # Message input with send button
    │   │   ├── source-citation.tsx     # Source attribution display
    │   │   └── tool-call-detail.tsx    # Expandable tool call info
    │   │
    │   ├── customers/                  # Customer management
    │   │   ├── customer-list.tsx       # Table with search + pagination
    │   │   ├── customer-card.tsx       # Summary card for grid/list view
    │   │   ├── customer-form.tsx       # Create/edit customer form (modal)
    │   │   ├── customer-profile.tsx    # Detail header: name, contact, contract
    │   │   ├── customer-timeline.tsx   # Activity event timeline
    │   │   ├── customer-metrics.tsx    # Metrics grid with values
    │   │   ├── event-filter-bar.tsx    # Type/date filter controls
    │   │   └── metric-trend-chart.tsx  # Simple line chart for metric history
    │   │
    │   ├── metrics/                    # Metrics catalog
    │   │   └── metrics-catalog.tsx     # Full catalog list with descriptions
    │   │
    │   ├── admin/                      # Admin-only features
    │   │   ├── user-list.tsx           # User management table
    │   │   ├── user-form.tsx           # Create/edit user form
    │   │   ├── source-list.tsx         # Source management table
    │   │   ├── source-form.tsx         # Register/edit source form
    │   │   ├── source-token-modal.tsx  # One-time API token display after source creation
    │   │   ├── role-list.tsx           # Role management table
    │   │   ├── role-detail.tsx         # Role permissions view
    │   │   └── role-form.tsx           # Create/edit role form with permission checkboxes
    │   │
    │   └── system/                     # System monitoring
    │       └── health-dashboard.tsx    # Service health status grid
    │
    ├── pages/                          # ── Route-level components ──
    │   ├── login.tsx                   # /login
    │   ├── chat.tsx                    # / (default landing page)
    │   ├── customers.tsx               # /customers
    │   ├── customer-detail.tsx         # /customers/:id
    │   ├── metrics-catalog.tsx         # /metrics
    │   ├── users.tsx                   # /admin/users
    │   ├── sources.tsx                 # /admin/sources
    │   ├── roles.tsx                   # /admin/roles
    │   ├── health.tsx                  # /system/health
    │   └── not-found.tsx              # 404 page
    │
    ├── lib/                            # ── Utilities ──
    │   ├── constants.ts                # API base URL, storage keys, pagination defaults
    │   ├── format.ts                   # Date, currency, number formatters
    │   ├── cn.ts                       # Tailwind class merge utility
    │   └── storage.ts                  # localStorage wrapper for JWT
    │
    └── styles/
        └── globals.css                 # Tailwind directives + custom properties
```

---

## 3. TypeScript Types

All types derived from `contracts/v1/models/` and `contracts/v1/api/`. Types mirror backend response shapes exactly.

### API Response Wrappers

```typescript
// src/types/api.ts

interface PaginationMeta {
  total: number | null;
  limit: number;
  has_next: boolean;
  next_cursor: string | null;
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

interface ErrorDetail {
  code: string;       // NOT_FOUND, VALIDATION_ERROR, FORBIDDEN, etc.
  message: string;
  details?: Record<string, unknown>;
}

interface ErrorResponse {
  error: ErrorDetail;
}
```

### Domain Types

| Type File | Types | Source Contract |
|-----------|-------|----------------|
| `auth.ts` | `LoginRequest`, `LoginResponse`, `CurrentUser` | `api/auth.yaml`, `models/user.yaml#CurrentUser` |
| `customer.ts` | `CustomerSummary`, `CustomerDetail`, `CustomerCreateRequest`, `CustomerUpdateRequest` | `models/customer.yaml` |
| `event.ts` | `EventSummary`, `EventType`, `EventFilters` | `models/event.yaml`, `models/common.yaml#event_type` |
| `metric.ts` | `MetricCatalogEntry`, `CustomerMetricValue`, `CustomerMetricTrend`, `MetricDataPoint` | `models/metric.yaml` |
| `chat.ts` | `ChatRequest`, `ChatResponse`, `ChatMessage`, `Source`, `ToolCall` | `api/chat.yaml` |
| `user.ts` | `UserSummary`, `UserCreateRequest`, `UserUpdateRequest` (uses `role_id: string` UUID, not role name) | `models/user.yaml`, `api/auth.yaml` |
| `source.ts` | `SourceSummary`, `SourceDetail`, `SourceCreateRequest`, `SourceCreateResponse` (includes one-time `api_token`) | `models/source.yaml`, `api/sources.yaml` |
| `role.ts` | `RoleSummary`, `RoleDetail`, `RoleCreateRequest`, `RoleUpdateRequest`, `Permission` | `models/role.yaml`, `api/roles.yaml` |

### Key Type Definitions

```typescript
// src/types/auth.ts
interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  permissions: string[];
}

// src/types/customer.ts
interface CustomerSummary {
  id: string;
  company_name: string;
  contact_name: string;
  email: string;
  contract_value: number;
  currency_code: string;
  signup_date: string;
  source_name?: string | null;
}

interface CustomerDetail {
  id: string;
  company_name: string;
  contact_name: string;
  email: string;
  contract_value: number;
  currency_code: string;
  signup_date: string;
  source_name: string | null;
  created_at: string;
  updated_at: string;
  recent_events: EventSummary[];
  metrics: CustomerMetricValue[];
}

interface CustomerCreateRequest {
  company_name: string;
  contact_name: string;
  email: string;
  contract_value: number;
  currency_code: string;
  signup_date: string;
}

interface CustomerUpdateRequest {
  company_name?: string;
  contact_name?: string;
  email?: string;
  contract_value?: number;
  currency_code?: string;
}

// src/types/chat.ts
interface ChatRequest {
  message: string;
  session_id?: string;
}

interface ChatResponse {
  session_id: string;
  message: {
    role: "assistant";
    content: string;
  };
  sources?: Source[];
  tool_calls?: ToolCall[];
}

interface Source {
  table: string;
  record_id: string;
  fields_used: Record<string, unknown>;
}

interface ToolCall {
  tool: string;
  input: Record<string, unknown>;
  result_count: number;
}

// src/types/user.ts
interface UserUpdateRequest {
  full_name?: string;
  email?: string;
  role_id?: string;       // UUID — backend expects role_id, NOT role name string
  is_active?: boolean;
}

// src/types/metric.ts
interface MetricCatalogEntry {
  id: string;
  name: string;
  display_name: string;
  description: string;
  unit: string;
  value_type: "integer" | "decimal" | "percentage";
}

interface CustomerMetricValue {
  metric_definition_id: string;
  metric_name: string;
  display_name: string;
  metric_value: number;
  unit: string;
  description: string;
  note?: string | null;
  updated_at: string;
}
```

---

## 4. API Client

### HTTP Client Pattern

```typescript
// src/api/client.ts
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const error = await res.json();
    throw new ApiError(res.status, error.error);
  }

  return res.json();
}
```

### Endpoint Functions

| Module | Functions | Backend Endpoint |
|--------|-----------|-----------------|
| `auth.ts` | `login(email, password)`, `getMe()` | `POST /api/auth/login`, `GET /api/auth/me` |
| `customers.ts` | `listCustomers(search?, cursor?, limit?)`, `getCustomer(id)`, `createCustomer(data)`, `updateCustomer(id, data)`, `deleteCustomer(id)` | Customers CRUD |
| `events.ts` | `getCustomerEvents(customerId, filters?)` | `GET /api/customers/{id}/events` |
| `metrics.ts` | `getCatalog()`, `getCustomerMetrics(customerId)`, `getMetricHistory(customerId, metricId, params?)` | `GET /api/metrics/catalog`, `GET /api/customers/{id}/metrics`, `GET /api/customers/{id}/metrics/{mid}/history` |
| `chat.ts` | `sendMessage(message, sessionId?)` | `POST /api/chat` |
| `users.ts` | `listUsers(cursor?, limit?)`, `createUser(data)`, `updateUser(id, data)` | `GET /api/users`, `POST /api/users`, `PATCH /api/users/{id}` |
| `sources.ts` | `listSources(cursor?, limit?)`, `getSource(id)`, `createSource(data)`, `updateSource(id, data)`, `deleteSource(id)` | Sources CRUD |
| `roles.ts` | `listRoles(cursor?, limit?)`, `getRoleDetail(id)`, `createRole(data)`, `updateRole(id, data)`, `deleteRole(id)`, `getPermissions()` | Roles CRUD + `GET /api/permissions` |
| `health.ts` | `getHealth()` | `GET /api/health` |

---

## 5. Routing

```
/login                          → LoginPage          (public)
/                               → ChatPage           (auth, chat.use)
/customers                      → CustomersPage       (auth, customers.read)
/customers/:id                  → CustomerDetailPage  (auth, customers.read)
/metrics                        → MetricsCatalogPage   (auth, metrics.catalog.read)
/admin/users                    → UsersPage           (auth, users.read)
/admin/sources                  → SourcesPage         (auth, sources.read)
/admin/roles                    → RolesPage           (auth, roles.read)
/system/health                  → HealthPage          (auth, system.health.read)
*                               → NotFoundPage
```

**Routing library**: `preact-router` (lightweight, Preact-native).

**Auth guard**: `AuthGuard` component wraps protected routes. Redirects to `/login` if no valid JWT. Checks permission for each route and shows 403 state if insufficient.

**Role-adaptive navigation**: Sidebar renders only the navigation items the user has permission to access. The `usePermission` hook provides `hasPermission(code)` to conditionally render UI.

---

## 6. State Management

No external state library. Context + `useReducer` for minimal global state. No Preact signals — standardize on React-compatible patterns.

### Auth Context

```
AuthProvider (wraps entire app)
├── user: CurrentUser | null
├── token: string | null
├── isAuthenticated: boolean
├── login(email, password) → sets token + user
├── logout() → clears token + user
└── hasPermission(code: string) → boolean
```

### Chat State

Local to chat page. Managed via `useReducer`:

```
chatState
├── sessionId: string | null
├── messages: ChatMessage[]
├── isLoading: boolean
└── error: string | null
```

### Pagination State

Reusable hook for any list page:

```
usePagination<T>(fetchFn)
├── data: T[]
├── isLoading: boolean
├── hasNext: boolean
├── total: number | null
├── loadMore() → fetches next page via cursor
└── refresh() → resets and refetches from start
```

---

## 7. RBAC — Frontend Enforcement (Gate 0)

Frontend RBAC is **cosmetic only** — it improves UX by hiding inaccessible features. Security enforcement happens at Gate 1 (tool filtering) and Gate 2 (service layer) on the backend.

### Permission-to-UI Mapping

| Permission | UI Elements Shown |
|------------|-------------------|
| `customers.read` | Customers nav item, customer list/detail pages |
| `customers.manage` | Create/edit/delete buttons on customers page and customer detail |
| `events.read` | Activity timeline tab on customer detail |
| `metrics.read` | Metrics section on customer detail |
| `metrics.catalog.read` | Metrics catalog nav item + page |
| `sources.read` | Sources nav item (admin section) |
| `sources.manage` | Create/edit/delete buttons on sources page |
| `users.read` | Users nav item (admin section) |
| `users.manage` | Create/edit buttons on users page |
| `roles.read` | Roles nav item (admin section) |
| `roles.manage` | Create/edit/delete buttons on roles page |
| `chat.use` | Chat nav item + page |
| `system.health.read` | System health nav item + page |

### Navigation by Role

| Role | Sidebar Sections |
|------|-----------------|
| **sales** | Chat, Customers |
| **support** | Chat, Customers |
| **cs_manager** | Chat, Customers, Metrics Catalog |
| **ops** | Chat, Customers, Metrics Catalog, Sources (read), System Health |
| **admin** | All sections including Admin (Users, Sources, Roles) |

### Implementation

```typescript
// src/hooks/use-permission.ts
function usePermission() {
  const { user } = useAuth();

  const hasPermission = (code: string): boolean =>
    user?.permissions.includes(code) ?? false;

  const canAccess = (codes: string[]): boolean =>
    codes.some(code => hasPermission(code));

  return { hasPermission, canAccess };
}
```

Sidebar, page guards, and action buttons all use `hasPermission()` to conditionally render.

---

## 8. Pages & Features

### Page Specifications

| Page | Route | Data Sources | Key Components | Permission |
|------|-------|-------------|----------------|------------|
| **Login** | `/login` | `POST /api/auth/login` | `LoginForm` | Public |
| **Chat** | `/` | `POST /api/chat` | `ChatContainer`, `MessageList`, `ChatInput`, `SourceCitation` | `chat.use` |
| **Customers** | `/customers` | `GET /api/customers` | `CustomerList`, `CustomerForm`, `DataTable`, `PaginationControls` | `customers.read`, `customers.manage` for CUD |
| **Customer Detail** | `/customers/:id` | `GET /api/customers/{id}`, `GET /api/customers/{id}/events`, `GET /api/customers/{id}/metrics` | `CustomerProfile`, `CustomerForm`, `CustomerTimeline`, `CustomerMetrics`, `EventFilterBar` | `customers.read`, `customers.manage` for edit/delete |
| **Metrics Catalog** | `/metrics` | `GET /api/metrics/catalog` | `MetricsCatalog` | `metrics.catalog.read` |
| **Users** | `/admin/users` | `GET /api/users` | `UserList`, `UserForm`, `Modal` | `users.read` |
| **Sources** | `/admin/sources` | `GET /api/sources` | `SourceList`, `SourceForm`, `SourceTokenModal`, `Modal` | `sources.read`, `sources.manage` for CUD |
| **Roles** | `/admin/roles` | `GET /api/roles`, `GET /api/permissions` | `RoleList`, `RoleDetail`, `RoleForm` | `roles.read`, `roles.manage` for CUD |
| **Health** | `/system/health` | `GET /api/health` | `HealthDashboard`, `StatusIndicator` | `system.health.read` |
| **Not Found** | `*` | None | `EmptyState` | Public |

### Chat Page Behavior

Per agent behavior rules (AB-1 through AB-9):

1. **Message display**: User messages right-aligned, assistant messages left-aligned
2. **Source attribution** (AB-4): Show collapsible source section under assistant messages when `sources[]` is non-empty
3. **Tool call transparency**: Optional expandable section showing which tools were invoked
4. **Loading state**: Typing indicator while waiting for agent response
5. **Error handling** (AB-2, UC-1-E1, UC-1-E2): Display error messages inline, never crash
6. **Multi-turn** (AB-9): Send `session_id` on subsequent messages for conversation context
7. **New conversation**: Button to start fresh session (omit `session_id`)

### Customer Detail Page

Aggregated 360-degree view:

```
┌─────────────────────────────────────────────────┐
│ Page Header: Company Name + Back to List        │
├────────────────────┬────────────────────────────┤
│ Profile Card       │ Metrics Grid               │
│ - Contact name     │ - Health Score (gauge)     │
│ - Email            │ - Support Tickets (count)  │
│ - Contract value   │ - Days Since Contact       │
│ - Signup date      │ - Other computed metrics   │
│ - Source           │                            │
├────────────────────┴────────────────────────────┤
│ Activity Timeline                               │
│ [Filter: Type ▾] [Since ▾] [Until ▾]           │
│                                                 │
│ ● Jan 25 — Support Ticket: SSO failing (Jira)  │
│ ● Jan 20 — Meeting: Quarterly review (Manual)  │
│ ● Jan 15 — Usage: Dashboard export (Product)   │
│                                                 │
│ [Load More →]                                   │
└─────────────────────────────────────────────────┘
```

---

## 9. Implementation Phases

### Phase 1 — Foundation + Core UI

**Goal**: Login working, chat functional, customer list and detail pages rendered.
**Stories**: US-5.1, US-1.1, US-1.2, US-1.3, US-2.1, US-2.3

#### Step 1.1: Project Setup

| Task | Files |
|------|-------|
| Initialize Preact + TypeScript + Vite | `package.json`, `vite.config.ts`, `tsconfig.json` |
| Tailwind CSS setup | `tailwind.config.ts`, `postcss.config.js`, `src/styles/globals.css` |
| HTML entry | `index.html` |
| App entry + router skeleton | `src/main.tsx`, `src/app.tsx` |
| Utility: class merge | `src/lib/cn.ts` |
| Constants | `src/lib/constants.ts` |
| Dockerfile | `Dockerfile` |

#### Step 1.2: Types + API Client

| Task | Files |
|------|-------|
| Shared types | `src/types/api.ts`, `src/types/auth.ts`, `src/types/customer.ts`, `src/types/event.ts`, `src/types/chat.ts`, `src/types/index.ts` |
| HTTP client with JWT injection | `src/api/client.ts` |
| Auth API | `src/api/auth.ts` |
| Customer API | `src/api/customers.ts` |
| Chat API | `src/api/chat.ts` |
| Formatters | `src/lib/format.ts` |
| Storage util | `src/lib/storage.ts` |

#### Step 1.3: Auth + Layout

| Task | Files |
|------|-------|
| Auth hook + context | `src/hooks/use-auth.ts` |
| Permission hook | `src/hooks/use-permission.ts` |
| Auth guard | `src/components/layout/auth-guard.tsx` |
| App shell (sidebar + header + content) | `src/components/layout/app-shell.tsx` |
| Sidebar (role-adaptive nav) | `src/components/layout/sidebar.tsx` |
| Header (user info + logout) | `src/components/layout/header.tsx` |
| Login page + form | `src/pages/login.tsx`, `src/features/auth/login-form.tsx` |

#### Step 1.4: UI Primitives

| Task | Files |
|------|-------|
| Button, Input, Badge, Card, Spinner, Skeleton | `src/components/ui/*.tsx` |
| Empty state, Error state | `src/components/data/empty-state.tsx`, `src/components/data/error-state.tsx` |
| Page header | `src/components/layout/page-header.tsx` |

#### Step 1.5: Chat Page

| Task | Files |
|------|-------|
| Chat container | `src/features/chat/chat-container.tsx` |
| Message list + bubbles | `src/features/chat/message-list.tsx`, `src/features/chat/message-bubble.tsx` |
| Chat input | `src/features/chat/chat-input.tsx` |
| Source citation | `src/features/chat/source-citation.tsx` |
| Chat page | `src/pages/chat.tsx` |

#### Step 1.6: Customer Pages

| Task | Files |
|------|-------|
| Pagination hook | `src/hooks/use-pagination.ts` |
| Data table + pagination controls | `src/components/data/data-table.tsx`, `src/components/data/pagination-controls.tsx` |
| Customer list (with create button if `customers.manage`) | `src/features/customers/customer-list.tsx` |
| Customer form (create/edit modal) | `src/features/customers/customer-form.tsx` |
| Customer profile (with edit/delete buttons if `customers.manage`) | `src/features/customers/customer-profile.tsx` |
| Customers page | `src/pages/customers.tsx` |
| Customer detail page | `src/pages/customer-detail.tsx` |

---

### Phase 2 — Full Features + Admin + RBAC

**Goal**: Search, timeline, metrics, admin pages, role-adaptive UI complete.
**Stories**: US-2.2, US-2.4, US-1.4, US-1.5, US-3.1, US-3.2, US-5.2, US-5.3, US-5.4, US-5.5, US-5.6, US-5.7, US-5.8

#### Step 2.1: Search + Timeline + Filters

| Task | Files |
|------|-------|
| Debounce hook | `src/hooks/use-debounce.ts` |
| Search in customer list | Update `src/features/customers/customer-list.tsx` |
| Event API | `src/api/events.ts` |
| Event types | `src/types/event.ts` |
| Event filter bar | `src/features/customers/event-filter-bar.tsx` |
| Customer timeline | `src/features/customers/customer-timeline.tsx` |
| Tool call detail (expandable) | `src/features/chat/tool-call-detail.tsx` |

#### Step 2.2: Metrics

| Task | Files |
|------|-------|
| Metric types | `src/types/metric.ts` |
| Metrics API: `getCatalog()`, `getCustomerMetrics()`, `getMetricHistory()` | `src/api/metrics.ts` |
| Customer metrics display | `src/features/customers/customer-metrics.tsx` |
| Metric trend chart (calls `getMetricHistory()`) | `src/features/customers/metric-trend-chart.tsx` |
| Metrics catalog page | `src/features/metrics/metrics-catalog.tsx`, `src/pages/metrics-catalog.tsx` |

#### Step 2.3: Admin — User Management

| Task | Files |
|------|-------|
| User types | `src/types/user.ts` |
| Users API | `src/api/users.ts` |
| User list | `src/features/admin/user-list.tsx` |
| User form (create/edit modal) | `src/features/admin/user-form.tsx` |
| Modal, Dropdown, Toast | `src/components/ui/modal.tsx`, `src/components/ui/dropdown.tsx`, `src/components/ui/toast.tsx` |
| Users page | `src/pages/users.tsx` |

#### Step 2.4: Admin — Source Management

| Task | Files |
|------|-------|
| Source types | `src/types/source.ts` |
| Sources API | `src/api/sources.ts` |
| Source list | `src/features/admin/source-list.tsx` |
| Source form (register/edit) | `src/features/admin/source-form.tsx` |
| Source token modal (one-time display after creation) | `src/features/admin/source-token-modal.tsx` |
| Confirmation dialog | `src/components/feedback/confirmation-dialog.tsx` |
| Sources page | `src/pages/sources.tsx` |

After `POST /api/sources`, the API returns the raw `api_token` **once** — it cannot be retrieved again. The `SourceTokenModal` must:
- Display the token in a monospace, read-only input field
- Provide a "Copy to clipboard" button
- Show a warning: "This token will not be shown again. Copy it now."
- Block dismissal until the user explicitly clicks "I've copied the token"

#### Step 2.5: Admin — Roles + System Health

| Task | Files |
|------|-------|
| Roles API | `src/api/roles.ts` |
| Role list + detail | `src/features/admin/role-list.tsx`, `src/features/admin/role-detail.tsx` |
| Role form (create/edit with permission checkboxes) | `src/features/admin/role-form.tsx` |
| Permissions API: `getPermissions()` | `src/api/roles.ts` (added to existing file) |
| Health API | `src/api/health.ts` |
| Health dashboard | `src/features/system/health-dashboard.tsx` |
| Status indicator | `src/components/feedback/status-indicator.tsx` |
| Roles page + Health page | `src/pages/roles.tsx`, `src/pages/health.tsx` |

#### Step 2.6: Polish

| Task | Files |
|------|-------|
| User menu (avatar + role badge + logout) | `src/features/auth/user-menu.tsx` |
| Key-value display component | `src/components/data/key-value.tsx` |
| Avatar component | `src/components/ui/avatar.tsx` |
| Tooltip component | `src/components/ui/tooltip.tsx` |
| Loading overlay | `src/components/feedback/loading-overlay.tsx` |
| 404 page | `src/pages/not-found.tsx` |
| Error boundaries | Update `src/app.tsx` |

---

## 10. Docker Service

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  ports:
    - "3000:3000"
  environment:
    - VITE_API_BASE_URL=http://backend:8000
  depends_on:
    - backend
```

### Dockerfile

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

For dev: use Vite dev server directly (port 3000) with proxy to backend.

---

## 11. Dependencies

### Runtime

| Package | Purpose |
|---------|---------|
| `preact` | UI framework (~3KB) |
| `preact-router` | Client-side routing |
| `clsx` | Conditional class names |
| `tailwind-merge` | Merge Tailwind classes without conflicts |

### Dev

| Package | Purpose |
|---------|---------|
| `typescript` | Type checking |
| `vite` | Build tool |
| `@preact/preset-vite` | Preact plugin for Vite |
| `tailwindcss` | Utility CSS |
| `postcss` | CSS processing |
| `autoprefixer` | Vendor prefixes |
| `@tailwindcss/forms` | Form element styling |

**Zero additional UI libraries.** All components are built with Tailwind CSS classes. No shadcn, no Material UI, no headless UI. Keep the bundle small and the design consistent.

---

## 12. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Preact (not React) | ~3KB vs ~40KB, API-compatible, contract specifies it |
| Routing | preact-router | Native Preact integration, tiny bundle |
| State | Context + useReducer | No Redux/Zustand — app state is minimal (auth + chat session) |
| Styling | Tailwind CSS only | Utility-first, no CSS-in-JS, no component library dependency |
| Component library | Custom components | Full control over design system, no external dependency |
| Charts | Canvas/SVG inline | Minimal chart needs (metric trends). No chart library to avoid bundle bloat |
| API client | Native fetch | No axios — fetch is sufficient, reduces dependencies |
| Form handling | Controlled inputs | No form library — forms are simple (login, create user, create source) |
| Pagination | Cursor-based | Matches backend keyset pagination, no offset |
| Date formatting | `Intl.DateTimeFormat` | Native browser API, no moment/dayjs |
| Auth storage | localStorage | JWT stored in localStorage with key from constants |
| Error handling | Error boundaries + toast | Catch render errors at boundary, show API errors via toast |
| Build output | Static files (Nginx) | Production: static assets served by Nginx in Docker |

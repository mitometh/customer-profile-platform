# Frontend Coding Standards & Conventions

**Source of truth**: `contracts/v1/` (26 YAML files)
**Stack**: Preact, TypeScript, Tailwind CSS, Vite
**Design system**: See `DESIGN_SYSTEM.md`

---

## 1. Architecture — Feature-First

Six directories under `src/` with clear responsibilities. Feature modules encapsulate domain-specific UI. Shared primitives live in `components/`.

```
┌───────────────────────────────────────────────────────┐
│  Pages (src/pages/)                                   │
│  Route-level: data fetching, layout, page composition │
├───────────────────────────────────────────────────────┤
│  Features (src/features/)                             │
│  Domain UI: chat, customers, metrics, admin           │
├───────────────────────────────────────────────────────┤
│  Components (src/components/)                         │
│  Shared primitives: button, input, table, modal       │
├───────────────────────────────────────────────────────┤
│  Hooks (src/hooks/)                                   │
│  Shared logic: auth, pagination, permissions          │
├───────────────────────────────────────────────────────┤
│  API (src/api/)                                       │
│  HTTP client, typed endpoint functions                │
├───────────────────────────────────────────────────────┤
│  Types (src/types/)                                   │
│  TypeScript interfaces, API shapes, enums             │
└───────────────────────────────────────────────────────┘
```

**Dependency rule**: imports flow downward only.

```
pages/ → features/ → components/
                   → hooks/ → api/ → types/
```

- Pages import features and components. Never import API directly — delegate to features.
- Features import components, hooks, and API.
- Components are generic — they must not import features, hooks, or API.
- Hooks import API and types. Never import components.
- API imports types only.

---

## 2. Layer Rules

| Layer | Owns | Does NOT |
|-------|------|----------|
| **Pages** (`src/pages/`) | Route composition, page-level layout, data fetching orchestration, auth/permission guards | Contain complex UI logic, direct API calls (delegate to features) |
| **Features** (`src/features/`) | Domain-specific components, feature state, API calls, business display logic | Own shared primitives, know about routing |
| **Components** (`src/components/`) | Generic UI primitives, layout shells, data display patterns | Import domain types, call API, contain business logic |
| **Hooks** (`src/hooks/`) | Shared stateful logic, side effects, API integration patterns | Render UI, import components |
| **API** (`src/api/`) | HTTP client, endpoint functions, request/response typing | Contain UI logic, state management, caching |
| **Types** (`src/types/`) | TypeScript interfaces, type unions, enums | Contain runtime code, side effects |

---

## 3. Component Architecture

### Component Pattern

All components are **functional components** using Preact's `h` function (via JSX). No class components.

```tsx
// src/components/ui/button.tsx
import { type ComponentChildren } from "preact";
import { cn } from "@/lib/cn";

interface ButtonProps {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  children: ComponentChildren;
  class?: string;
}

export function Button({
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  onClick,
  children,
  class: className,
}: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      onClick={onClick}
      class={cn(
        "inline-flex items-center justify-center font-medium rounded-lg transition-colors",
        variants[variant],
        sizes[size],
        (disabled || loading) && "opacity-50 cursor-not-allowed",
        className,
      )}
    >
      {loading && <Spinner class="mr-2 h-4 w-4" />}
      {children}
    </button>
  );
}
```

### Rules

- One component per file. File name matches component name in `kebab-case`.
- Props interface defined in the same file, named `{ComponentName}Props`.
- Default exports are **never used**. Always named exports.
- Use `class` attribute (not `className`) — Preact convention.
- Destructure props in the function signature.
- Use `ComponentChildren` (from Preact) for child content typing.
- Compose with Tailwind classes. No inline styles. No CSS modules.

### Component Categories

| Category | Location | Examples | Rules |
|----------|----------|---------|-------|
| **UI Primitives** | `src/components/ui/` | Button, Input, Badge, Card, Modal | Zero domain knowledge, fully configurable via props |
| **Data Display** | `src/components/data/` | DataTable, KeyValue, EmptyState, PaginationControls | Accept generic data via props, no API calls |
| **Layout** | `src/components/layout/` | AppShell, Sidebar, Header, PageHeader, AuthGuard | App structure, navigation, auth boundaries |
| **Feedback** | `src/components/feedback/` | LoadingOverlay, ConfirmationDialog, StatusIndicator | User feedback patterns |
| **Features** | `src/features/{domain}/` | ChatContainer, CustomerList, UserForm | Domain-specific, may call API and use hooks |

---

## 4. Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files & folders | `kebab-case` | `customer-list.tsx`, `use-auth.ts` |
| Components | `PascalCase` | `CustomerList`, `ChatInput` |
| Hooks | `camelCase` with `use` prefix | `useAuth`, `usePagination` |
| Types/Interfaces | `PascalCase` | `CustomerSummary`, `ChatResponse` |
| Props interfaces | `PascalCase` + `Props` | `ButtonProps`, `CustomerListProps` |
| API functions | `camelCase`, verb-first | `listCustomers()`, `getCustomer()`, `sendMessage()` |
| Constants | `UPPER_SNAKE_CASE` | `API_BASE_URL`, `DEFAULT_PAGE_SIZE` |
| CSS classes | Tailwind utilities | `text-sm text-gray-600 font-medium` |
| Route paths | `kebab-case`, plural nouns | `/customers`, `/admin/users` |
| Event handlers | `on` + `PascalCase` | `onSubmit`, `onClick`, `onSearch` |
| Boolean props | `is` / `has` / `can` prefix | `isLoading`, `hasNext`, `canEdit` |
| Enum values | `snake_case` (matching backend) | `support_ticket`, `cs_manager` |

---

## 5. TypeScript Standards

### Strict Configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": false
  }
}
```

### Type Rules

- All function parameters and return types must be explicitly typed.
- Use `interface` for object shapes that represent API data. Use `type` for unions and utility types.
- Never use `any`. Use `unknown` when the type is truly not known, then narrow it.
- Use `Record<string, unknown>` instead of `object` for arbitrary key-value pairs.
- Nullable fields from the API use `T | null`, not `T | undefined`. Match backend JSON behavior.
- Optional props use `?` syntax: `name?: string`.
- Prefer union types over enums: `type EventType = "support_ticket" | "meeting" | "usage_event"`.

### Import Conventions

```tsx
// 1. Preact imports
import { h } from "preact";
import { useState, useEffect } from "preact/hooks";

// 2. Third-party imports
import { Router, Route } from "preact-router";

// 3. Internal imports — types
import type { CustomerSummary } from "@/types";

// 4. Internal imports — API, hooks, components
import { listCustomers } from "@/api/customers";
import { usePagination } from "@/hooks/use-pagination";
import { DataTable } from "@/components/data/data-table";
```

- Use `import type` for type-only imports.
- Group imports with blank lines between groups.
- Sort alphabetically within each group.
- Use the `@/` path alias for all internal imports (maps to `src/`). Requires config in two files:
  - `vite.config.ts`: `resolve: { alias: { "@": path.resolve(__dirname, "./src") } }`
  - `tsconfig.json` compilerOptions: `"baseUrl": ".", "paths": { "@/*": ["src/*"] }`

---

## 6. Styling with Tailwind CSS

### Rules

- **All styling via Tailwind utility classes.** No custom CSS except Tailwind directives in `globals.css`.
- **No inline `style` attributes.** Exception: dynamic values that can't be expressed as Tailwind classes (e.g., chart dimensions).
- **No CSS modules, no styled-components, no CSS-in-JS.**
- Use the `cn()` utility (clsx + tailwind-merge) for conditional classes.
- Design system tokens defined in `tailwind.config.ts` — see `DESIGN_SYSTEM.md`.

### Class Ordering Convention

Follow the "outside-in" ordering:

```
1. Layout       → flex, grid, block, hidden
2. Position     → relative, absolute, fixed
3. Box model    → w-*, h-*, p-*, m-*, gap-*
4. Typography   → text-*, font-*, leading-*
5. Visual       → bg-*, border-*, rounded-*, shadow-*
6. Interactive  → hover:*, focus:*, transition-*
```

Example:
```tsx
<div class="flex items-center gap-3 px-4 py-3 text-sm text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
```

### Responsive Design

Mobile-first. Breakpoints follow Tailwind defaults:

| Prefix | Min Width | Target |
|--------|-----------|--------|
| (none) | 0px | Mobile |
| `sm:` | 640px | Small tablet |
| `md:` | 768px | Tablet |
| `lg:` | 1024px | Desktop |
| `xl:` | 1280px | Wide desktop |

The app is primarily a desktop tool (internal team use), but layout should not break on tablet-width viewports. Sidebar collapses on `< lg`.

---

## 7. API Integration Patterns

### Error Handling

```typescript
// src/api/client.ts
class ApiError extends Error {
  constructor(
    public status: number,
    public error: { code: string; message: string; details?: Record<string, unknown> },
  ) {
    super(error.message);
  }
}
```

API errors are caught in feature components or hooks and displayed via:
- **Toast notifications** for transient errors (network, 500s, rate limits)
- **Inline messages** for validation errors (400) and not-found (404)
- **Redirect to login** for authentication errors (401)
- **Permission denied state** for forbidden errors (403)

### Pagination Pattern

```typescript
// Usage in a feature component
const { data, isLoading, hasNext, loadMore, refresh } = usePagination(
  (cursor, limit) => listCustomers({ search, cursor, limit })
);
```

- All list endpoints use cursor-based pagination.
- The `usePagination` hook manages cursor state, data accumulation, and loading states.
- "Load more" button pattern, not infinite scroll (explicit user control).
- `total` from backend may be `null` — UI shows count only when available.

### Loading States

Every data-fetching component has three visual states:

| State | What to Show |
|-------|-------------|
| **Loading (initial)** | Skeleton placeholders matching expected content shape |
| **Loading (more)** | Spinner at bottom, existing data visible |
| **Error** | Error state component with retry button |
| **Empty** | Empty state component with contextual message |
| **Data** | Rendered content |

---

## 8. Component Communication

### Props Down, Events Up

- Parent → Child: data via props
- Child → Parent: callbacks via `onX` props
- No prop drilling deeper than 2 levels — extract into context or restructure

### Context Usage

Only two contexts in the app:

| Context | Provides | Scope |
|---------|----------|-------|
| `AuthContext` | `user`, `token`, `login()`, `logout()`, `hasPermission()` | Entire app |
| `ToastContext` | `showToast()`, toast queue | Entire app |

Everything else is local component state or prop-passing.

### No Global State Library

- **Auth state**: `AuthContext` wrapping the app
- **Chat state**: local to chat page (useReducer)
- **List state**: local to each list page (usePagination hook)
- **Form state**: local to each form (useState)
- **Toast notifications**: `ToastContext` wrapping the app

---

## 9. File Organization Rules

- One component per file. File exports exactly one component function.
- Component files: `kebab-case.tsx`
- Hook files: `use-{name}.ts`
- Type files: `{domain}.ts`
- API files: `{domain}.ts`
- Keep files under 200 lines. Split large components into smaller sub-components.
- Every directory has an `index.ts` only when re-exporting is needed (types/).
- Feature directories group by domain: `features/chat/`, `features/customers/`, `features/admin/`.

---

## 10. Error Handling

### Error Boundary

A top-level error boundary catches unhandled render errors and shows a fallback UI.

### API Error Flow

```
API call → catch ApiError
  → 401: redirect to /login (token expired)
  → 403: show permission denied state
  → 404: show not found state
  → 400: show validation errors inline
  → 429: show rate limit toast with retry-after
  → 500/503: show error toast with retry button
```

### Error Handling Implementation Pattern

Feature components delegate error handling to the `useApi` hook. Components never wrap API calls in try/catch directly — the hook centralizes error routing.

```tsx
// src/hooks/use-api.ts — centralized error handler
function useApi<T>(apiFn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();
  const { logout } = useAuth();

  const execute = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiFn();
      setData(result);
      return result;
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) { logout(); return; }
        if (err.status >= 500 || err.status === 429) {
          showToast({ type: "error", message: err.error.message });
        }
        setError(err);
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { data, error, isLoading, execute };
}
```

Error routing rules:
- **401**: Handled globally — auto-redirect to login (never shown inline)
- **400/404/403**: Set in `error` state — component renders inline error UI
- **429/500/503**: Shown as toast notification (transient, user can retry)
- **Mutations** (POST/PATCH/DELETE): Show success toast on completion

### User-Facing Error Messages

Map error codes to human-readable messages:

| Code | User Message |
|------|-------------|
| `UNAUTHORIZED` | "Your session has expired. Please log in again." |
| `FORBIDDEN` | "You don't have permission to access this resource." |
| `NOT_FOUND` | "The requested {resource} could not be found." |
| `VALIDATION_ERROR` | Show field-level errors from `details` |
| `CONFLICT` | "{Resource} already exists." |
| `RATE_LIMITED` | "Too many requests. Please wait a moment." |
| `LLM_UNAVAILABLE` | "The AI assistant is temporarily unavailable. Please try again." |
| `INTERNAL_ERROR` | "Something went wrong. Please try again." |

---

## 11. Accessibility Standards

- All interactive elements have visible focus indicators (Tailwind `focus:ring-*`).
- Form inputs have associated `<label>` elements.
- Buttons have descriptive text or `aria-label`.
- Color is not the sole indicator of state — use icons + text alongside colors.
- Modal dialogs trap focus and close on Escape.
- Loading states announced via `aria-live="polite"`.
- Sufficient color contrast (WCAG AA minimum — 4.5:1 for text).

---

## 12. Performance Guidelines

- **No unnecessary re-renders**: use `memo()` only when profiling shows a problem. Don't pre-optimize.
- **Lazy load pages**: use dynamic `import()` for route-level code splitting.
- **Debounce search inputs**: 300ms delay before API call (via `useDebounce` hook).
- **Pagination over full loads**: never load entire datasets. Always paginate.
- **Image optimization**: SVG for icons, no raster images (internal tool, not a marketing site).
- **Bundle size discipline**: no heavy libraries. Every `npm install` must justify its weight.

### Bundle Budget

| Category | Max Size (gzipped) |
|----------|-------------------|
| Framework (Preact) | ~4KB |
| App code | ~100KB |
| Tailwind CSS | ~15KB (purged) |
| Total | < 125KB |

---

## 13. Environment Variables

All env vars prefixed with `VITE_` for Vite exposure to client code.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | Backend API base URL |

Access via `import.meta.env.VITE_API_BASE_URL`.

Never store secrets in frontend env vars — they are visible to the browser.

---

## 14. Git Conventions

```
<type>(<context>): <short summary>

Types: feat, fix, refactor, test, docs, chore, style
Branch: feature/<context>-<description>, fix/<context>-<description>
```

Examples:
```
feat(chat): add source citation display
feat(customers): implement search with debounce
fix(auth): handle expired token redirect
style(ui): adjust button hover states
```

---

## 15. Key Principles

- **Composition over configuration**: Build complex UI by composing small, focused components.
- **Colocation**: Keep related code together. Feature components, their types, and their API calls live close.
- **Explicit over implicit**: No magic. Props are typed. Side effects are in hooks. State is visible.
- **Progressive enhancement**: Show skeleton → load data → render. Never flash empty states.
- **Minimal dependencies**: Every npm package must justify its bundle cost. Prefer native APIs.
- **Backend is the authority**: Frontend RBAC is cosmetic. Never trust client-side permission checks for security.
- **Match backend shapes**: TypeScript types mirror backend response schemas exactly. No transformation layer.

### Things We Never Do

- Import a UI component library (shadcn, MUI, Ant Design, Chakra).
- Use CSS-in-JS, CSS modules, or inline styles.
- Store secrets or sensitive data in frontend code or env vars.
- Use `any` type or disable TypeScript strict mode.
- Use class components or legacy lifecycle methods.
- Make direct DOM manipulations outside Preact's rendering.
- Use `default export`. Always named exports.
- Import domain-specific code into generic components.
- Cache API responses in frontend (backend controls freshness).
- Use `window.location` for navigation (use router).

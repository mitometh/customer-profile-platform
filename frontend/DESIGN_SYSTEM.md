# Design System — Customer 360 Insights Agent

An enterprise-grade, clean design system for internal team use. Optimized for data density, clarity, and professional aesthetics. No decorative elements, no unnecessary animation, no visual noise.

---

## 1. Design Principles

| Principle | Description |
|-----------|-------------|
| **Clarity first** | Every element communicates information. Remove anything that doesn't serve the user's task. |
| **Consistent density** | Internal tools benefit from compact, information-rich layouts. White space is intentional, not wasteful. |
| **Quiet confidence** | Neutral palette with purposeful color accents. The UI stays out of the way and lets the data speak. |
| **Progressive disclosure** | Show summary first, detail on demand. Collapsible sections, expandable rows, modal overlays. |
| **Accessible by default** | WCAG AA contrast ratios, keyboard navigation, screen reader support baked in — not bolted on. |

---

## 2. Color System

### Core Palette

A neutral-first palette with a single primary accent. Semantic colors for status communication.

```
┌─────────────────────────────────────────────────────────────────────┐
│  NEUTRALS (Gray-cool)       Used for text, borders, backgrounds    │
├─────────────────────────────────────────────────────────────────────┤
│  gray-950  #0b0f19           Body text, headings                   │
│  gray-800  #1e293b           Secondary text                        │
│  gray-700  #334155           Muted text, labels (WCAG AA: 5.91:1)  │
│  gray-600  #475569           Interactive secondary (ghost buttons)  │
│  gray-500  #64748b           Placeholder text (WCAG AA: 4.68:1)    │
│  gray-400  #94a3b8           Disabled text (decorative only)       │
│  gray-300  #cbd5e1           Borders                               │
│  gray-200  #e2e8f0           Dividers, subtle borders              │
│  gray-100  #f1f5f9           Hover backgrounds, zebra rows         │
│  gray-50   #f8fafc           Page background, card background      │
│  white     #ffffff           Card surfaces, inputs                 │
├─────────────────────────────────────────────────────────────────────┤
│  PRIMARY (Indigo)           Brand accent, interactive elements     │
├─────────────────────────────────────────────────────────────────────┤
│  indigo-700  #4338ca         Primary button hover, active links    │
│  indigo-600  #4f46e5         Primary button, active nav, links     │
│  indigo-500  #6366f1         Focus rings                           │
│  indigo-100  #e0e7ff         Selected row, active badge bg         │
│  indigo-50   #eef2ff         Hover state for primary elements      │
├─────────────────────────────────────────────────────────────────────┤
│  SEMANTIC                   Status communication                   │
├─────────────────────────────────────────────────────────────────────┤
│  green-700   #15803d         Success text                          │
│  green-100   #dcfce7         Success background                    │
│  green-500   #22c55e         Health indicator (healthy)            │
│                                                                     │
│  amber-700   #b45309         Warning text                          │
│  amber-100   #fef3c7         Warning background                    │
│  amber-500   #f59e0b         Health indicator (needs attention)    │
│                                                                     │
│  red-700     #b91c1c         Error/danger text                     │
│  red-100     #fee2e2         Error background                      │
│  red-500     #ef4444         Health indicator (at-risk), delete     │
│                                                                     │
│  blue-700    #1d4ed8         Info text                              │
│  blue-100    #dbeafe         Info background                        │
│  blue-500    #3b82f6         Links, info indicator                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Tailwind Config

```typescript
// tailwind.config.ts — extend section
colors: {
  // Use Tailwind's default gray (slate) and indigo
  // Custom semantic aliases in component classes, not config
  // This keeps the config minimal and portable
}
```

We use Tailwind's built-in `slate` (as gray) and `indigo` palettes. No custom color definitions needed in config — the design system maps usage to existing Tailwind classes.

### Color Usage Rules

| Context | Color | Tailwind Class |
|---------|-------|---------------|
| Body text | gray-950 | `text-gray-950` |
| Secondary text | gray-700 | `text-gray-700` |
| Muted text, labels | gray-600 | `text-gray-600` |
| Placeholder text | gray-500 | `placeholder:text-gray-500` |
| Disabled text | gray-400 | `text-gray-400` |
| Page background | gray-50 | `bg-gray-50` |
| Card/surface | white | `bg-white` |
| Borders | gray-200 | `border-gray-200` |
| Primary action | indigo-600 | `bg-indigo-600 text-white` |
| Primary hover | indigo-700 | `hover:bg-indigo-700` |
| Danger action | red-600 | `bg-red-600 text-white` |
| Success state | green-600/green-50 | `text-green-700 bg-green-100` |
| Warning state | amber-600/amber-50 | `text-amber-700 bg-amber-100` |
| Error state | red-600/red-50 | `text-red-700 bg-red-100` |

---

## 3. Typography

### Type Scale

System font stack for maximum performance and native feel:

```css
font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

font-family-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo,
  Consolas, "Liberation Mono", monospace;
```

| Level | Size | Weight | Line Height | Tailwind | Usage |
|-------|------|--------|-------------|----------|-------|
| **Page title** | 24px | 700 | 32px | `text-2xl font-bold leading-8` | Page headers |
| **Section title** | 18px | 600 | 28px | `text-lg font-semibold leading-7` | Card titles, section headers |
| **Subtitle** | 16px | 600 | 24px | `text-base font-semibold leading-6` | Subsections, table headers |
| **Body** | 14px | 400 | 20px | `text-sm leading-5` | Default text, descriptions |
| **Body strong** | 14px | 500 | 20px | `text-sm font-medium leading-5` | Labels, nav items |
| **Small** | 12px | 400 | 16px | `text-xs leading-4` | Timestamps, metadata, badges |
| **Mono** | 13px | 400 | 20px | `text-[13px] font-mono leading-5` | Code, IDs, JSON |

### Typography Rules

- **14px (`text-sm`) is the default body size.** Internal tools prioritize density over readability at arm's length.
- **Never use text larger than 24px.** This is a data tool, not a marketing page.
- **Headings use `font-semibold` or `font-bold`**, never `font-black` or `font-extrabold`.
- **Monospace for technical data**: UUIDs, API tokens, JSON, metric names.
- **Truncate long text** with `truncate` class + tooltip on hover. Never wrap table cells.

---

## 4. Spacing & Layout

### Spacing Scale

Follow Tailwind's 4px base unit. The most-used values:

| Token | Value | Usage |
|-------|-------|-------|
| `1` | 4px | Icon-to-text gap |
| `2` | 8px | Tight padding (badges, small pills) |
| `3` | 12px | Compact padding (table cells) |
| `4` | 16px | Standard padding (cards, inputs) |
| `5` | 20px | Section padding |
| `6` | 24px | Card body padding, page gutters |
| `8` | 32px | Between sections |

### Layout System

```
┌──────────────────────────────────────────────────────────────────┐
│                          APP SHELL                               │
│  ┌──────────┬───────────────────────────────────────────────┐   │
│  │          │  Header (h-14)                                │   │
│  │          │  ─────────────────────────────────────────────│   │
│  │ Sidebar  │                                               │   │
│  │ (w-64)   │  Page Content                                │   │
│  │          │  (max-w-7xl mx-auto px-6 py-6)               │   │
│  │          │                                               │   │
│  │          │                                               │   │
│  │          │                                               │   │
│  └──────────┴───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

| Element | Dimensions | Tailwind |
|---------|-----------|----------|
| Sidebar | 256px width | `w-64` |
| Header | 56px height | `h-14` |
| Content max width | 1280px | `max-w-7xl` |
| Content padding | 24px horizontal, 24px vertical | `px-6 py-6` |
| Card padding | 24px | `p-6` |
| Card gap (grid) | 24px | `gap-6` |
| Section gap | 32px | `space-y-8` |

### Grid Patterns

| Layout | Columns | Tailwind |
|--------|---------|----------|
| Metric cards | 4 cols (desktop), 2 cols (tablet), 1 col (mobile) | `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4` |
| Detail layout | 3+9 (sidebar+main) | `grid grid-cols-12 gap-6` → `col-span-4` + `col-span-8` |
| Form layout | Single column, max 480px | `max-w-md` |
| Health checks | 2 cols | `grid grid-cols-1 sm:grid-cols-2 gap-4` |

---

## 5. Component Specifications

### Button

```
┌─────────────────────────────────────────────────────────┐
│  Variants                                               │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Primary  │  │Secondary │  │  Ghost   │  │ Danger │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│                                                         │
│  Sizes                                                  │
│  ┌────┐  ┌──────┐  ┌────────┐                          │
│  │ SM │  │  MD  │  │   LG   │                          │
│  └────┘  └──────┘  └────────┘                          │
└─────────────────────────────────────────────────────────┘
```

| Variant | Resting | Hover | Tailwind |
|---------|---------|-------|----------|
| **Primary** | indigo-600 bg, white text | indigo-700 bg | `bg-indigo-600 text-white hover:bg-indigo-700` |
| **Secondary** | white bg, gray-300 border, gray-700 text | gray-50 bg | `bg-white border border-gray-300 text-gray-700 hover:bg-gray-50` |
| **Ghost** | transparent bg, gray-600 text | gray-100 bg | `text-gray-600 hover:bg-gray-100` |
| **Danger** | red-600 bg, white text | red-700 bg | `bg-red-600 text-white hover:bg-red-700` |

| Size | Height | Padding | Font | Tailwind |
|------|--------|---------|------|----------|
| **sm** | 32px | 12px H, 6px V | 12px | `h-8 px-3 text-xs` |
| **md** | 36px | 16px H, 8px V | 14px | `h-9 px-4 text-sm` |
| **lg** | 40px | 20px H, 10px V | 14px | `h-10 px-5 text-sm` |

All buttons: `rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`

Disabled: `opacity-50 cursor-not-allowed`

#### Loading State

| Size | Spinner Size | Tailwind |
|------|-------------|----------|
| **sm** | 14px | `h-3.5 w-3.5` |
| **md** | 16px | `h-4 w-4` |
| **lg** | 16px | `h-4 w-4` |

- Spinner inherits text color of the variant (white for primary/danger, gray-600 for secondary/ghost)
- Spinner is prepended before children with `mr-2` gap
- Button text remains visible during loading (no hide/show swap)
- Button is `disabled` during loading — receives `opacity-50 cursor-not-allowed`

### Input

| State | Border | Background | Tailwind |
|-------|--------|------------|----------|
| Default | gray-300 | white | `border-gray-300 bg-white` |
| Focus | indigo-500 | white | `focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500` |
| Error | red-500 | white | `border-red-500 focus:border-red-500 focus:ring-red-500` |
| Disabled | gray-200 | gray-50 | `border-gray-200 bg-gray-50 cursor-not-allowed` |

Base: `block w-full rounded-lg border px-3 h-9 text-sm text-gray-950 placeholder:text-gray-500 transition-colors`

Height: 36px (`h-9`) — use explicit `h-9` instead of vertical padding to align with buttons in side-by-side layouts (search bars, inline forms)

### Badge

Status and category indicators.

| Variant | Background | Text | Border | Tailwind |
|---------|-----------|------|--------|----------|
| **Default** | gray-100 | gray-700 | none | `bg-gray-100 text-gray-700` |
| **Primary** | indigo-100 | indigo-700 | none | `bg-indigo-100 text-indigo-700` |
| **Success** | green-100 | green-700 | none | `bg-green-100 text-green-700` |
| **Warning** | amber-100 | amber-700 | none | `bg-amber-100 text-amber-700` |
| **Danger** | red-100 | red-700 | none | `bg-red-100 text-red-700` |

Base: `inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium`

Usage:
- Role badges: `admin` → primary, `ops` → default, `cs_manager` → default
- Event type: `support_ticket` → warning, `meeting` → primary, `usage_event` → default
- Health status: `healthy` → success, `degraded` → warning, `unhealthy` → danger
- Source status: `active` → success, `inactive` → danger

### Card

```
┌─────────────────────────────────────────┐
│  Card Header (optional)                 │   border-b border-gray-200
│  Title              Action Button       │   px-6 py-4
├─────────────────────────────────────────┤
│                                         │
│  Card Body                              │   px-6 py-5
│                                         │
│  Content goes here with standard        │
│  padding and text styling.              │
│                                         │
├─────────────────────────────────────────┤
│  Card Footer (optional)                 │   border-t border-gray-200
│                                         │   px-6 py-3
└─────────────────────────────────────────┘
```

Base: `bg-white rounded-xl border border-gray-200 shadow-sm`

No `shadow-md` or `shadow-lg` for cards — keep shadows subtle. Only modals use elevated shadows.

### Data Table

```
┌───────────────────────────────────────────────────────────────┐
│  Company Name ▾    Contact        Contract    Signup    Source │
├───────────────────────────────────────────────────────────────┤
│  Acme Corp         John Smith     $150,000    Mar 2024  SF   │
│  DataFlow Inc      Sarah Lee      $85,000     Jan 2024  Hub  │
│  CloudNine         Mike Chen      $220,000    Jun 2024  SF   │
│  TechStart         Anna Kim       $45,000     Aug 2024  —    │
│  Apex Systems      Tom Brown      $180,000    Feb 2024  Jira │
├───────────────────────────────────────────────────────────────┤
│  Showing 5 of 42                              [Load More →]  │
└───────────────────────────────────────────────────────────────┘
```

| Element | Style |
|---------|-------|
| Table header | `bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider` |
| Header cell | `px-6 py-3 text-left` |
| Body row | `border-b border-gray-100` |
| Body row hover | `hover:bg-gray-50` |
| Body cell | `px-6 py-4 text-sm text-gray-900` |
| Muted cell | `text-gray-500` |
| Footer | `bg-gray-50 px-6 py-3 text-sm text-gray-500` |

Table container: `overflow-hidden rounded-xl border border-gray-200`

### Modal

```
┌─ Overlay ────────────────────────────────────────────┐
│                                                       │
│    ┌─────────────────────────────────────────────┐   │
│    │  Modal Header                          [X]  │   │
│    │─────────────────────────────────────────────│   │
│    │                                             │   │
│    │  Modal Body                                 │   │
│    │  Content, forms, details                    │   │
│    │                                             │   │
│    │─────────────────────────────────────────────│   │
│    │  Modal Footer          [Cancel] [Confirm]   │   │
│    └─────────────────────────────────────────────┘   │
│                                                       │
└───────────────────────────────────────────────────────┘
```

| Element | Style |
|---------|-------|
| Overlay | `fixed inset-0 bg-gray-950/50 backdrop-blur-sm` |
| Dialog | `bg-white rounded-2xl shadow-xl max-w-lg w-full mx-4` |
| Header | `px-6 py-4 border-b border-gray-200` |
| Body | `px-6 py-5` |
| Footer | `px-6 py-4 border-t border-gray-200 flex justify-end gap-3` |

Width: `max-w-sm` (alert), `max-w-lg` (form), `max-w-2xl` (detail view)

#### Accessibility

| Behavior | Implementation |
|----------|---------------|
| **Focus trap** | Tab cycles within modal. Focus does not escape to background content. |
| **Initial focus** | First focusable element in modal body, or the primary action button. |
| **ESC to close** | `keydown` listener on `Escape` key dismisses the modal. |
| **Scroll lock** | `overflow: hidden` on `<body>` while modal is open. Restore on close. |
| **Overlay click** | Clicking the overlay (outside dialog) dismisses the modal. |
| **Focus restore** | On close, focus returns to the element that triggered the modal. |
| **ARIA** | Dialog uses `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to header. |
| **z-index** | Overlay and dialog: `z-50`. Toasts sit above at `z-[60]`. |

---

## 6. Page Layouts

### Login Page

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│              ┌─────────────────────────────────┐              │
│              │                                 │              │
│              │  ◆ Customer 360                 │              │
│              │                                 │              │
│              │  Email                          │              │
│              │  ┌───────────────────────────┐  │              │
│              │  │ you@company.com           │  │              │
│              │  └───────────────────────────┘  │              │
│              │                                 │              │
│              │  Password                       │              │
│              │  ┌───────────────────────────┐  │              │
│              │  │ ••••••••                  │  │              │
│              │  └───────────────────────────┘  │              │
│              │                                 │              │
│              │  ┌───────────────────────────┐  │              │
│              │  │       Sign in →           │  │              │
│              │  └───────────────────────────┘  │              │
│              │                                 │              │
│              └─────────────────────────────────┘              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

Centered on page. `bg-gray-50` background. Card: `max-w-sm w-full`.

### Chat Page

```
┌──────────┬──────────────────────────────────────────────────────┐
│          │  ◆ Customer 360 Chat          [+ New Conversation]  │
│ Sidebar  ├──────────────────────────────────────────────────────┤
│          │                                                      │
│          │     ┌──────────────────────────────────────┐        │
│          │     │ What's the contract value for Acme?  │  You   │
│          │     └──────────────────────────────────────┘        │
│          │                                                      │
│          │  ┌──────────────────────────────────────────┐        │
│          │  │ Acme Corp has a contract value of        │  AI    │
│          │  │ $150,000 (USD). They signed up on        │        │
│          │  │ March 15, 2024.                          │        │
│          │  │                                          │        │
│          │  │  📎 Source: customers table               │        │
│          │  │     record: 550e8400...                   │        │
│          │  │     fields: company_name, contract_value  │        │
│          │  └──────────────────────────────────────────┘        │
│          │                                                      │
│          ├──────────────────────────────────────────────────────┤
│          │  ┌──────────────────────────────────────┐  ┌─────┐  │
│          │  │ Ask about your customers...          │  │ Send│  │
│          │  └──────────────────────────────────────┘  └─────┘  │
└──────────┴──────────────────────────────────────────────────────┘
```

Chat layout: `flex flex-col h-full` — messages scroll, input stays at bottom.

Message bubbles:
- **User**: `bg-indigo-600 text-white rounded-2xl rounded-br-md ml-auto max-w-[80%]`
- **Assistant**: `bg-white border border-gray-200 rounded-2xl rounded-bl-md mr-auto max-w-[80%]`

Source citation: collapsible section, `bg-gray-50 rounded-lg p-3 mt-2 text-xs font-mono`

### Customer Detail Page

```
┌──────────┬──────────────────────────────────────────────────────┐
│          │  ← Back to Customers                                │
│ Sidebar  │  Acme Corp                                          │
│          ├────────────────────────┬─────────────────────────────┤
│          │                        │                             │
│          │  Profile               │  Metrics                   │
│          │  ┌──────────────────┐  │  ┌────────┐ ┌────────┐    │
│          │  │ Contact: John    │  │  │Health  │ │Tickets │    │
│          │  │ Email: john@...  │  │  │Score   │ │(30d)   │    │
│          │  │ Contract: $150K  │  │  │ 78.5   │ │  3     │    │
│          │  │ Signed: Mar 2024 │  │  └────────┘ └────────┘    │
│          │  │ Source: SF       │  │  ┌────────┐ ┌────────┐    │
│          │  └──────────────────┘  │  │Days    │ │ MAU    │    │
│          │                        │  │Contact │ │        │    │
│          │                        │  │  5     │ │  245   │    │
│          │                        │  └────────┘ └────────┘    │
│          ├────────────────────────┴─────────────────────────────┤
│          │  Activity Timeline                                   │
│          │  [All Types ▾] [Last 30 days ▾]                     │
│          │                                                      │
│          │  ● Jan 25  Support Ticket                            │
│          │    SSO integration failing                [jira]     │
│          │    Priority: high · Status: open                     │
│          │                                                      │
│          │  ● Jan 20  Meeting                                   │
│          │    Quarterly business review              [manual]   │
│          │    Attendees: 3 · Action items: 2                    │
│          │                                                      │
│          │  [Load More →]                                       │
└──────────┴──────────────────────────────────────────────────────┘
```

---

## 7. Iconography

**No icon library.** Use inline SVGs for the ~15 icons the app needs. Keep them as simple Preact components.

| Icon | Context | Style |
|------|---------|-------|
| Chat bubble | Sidebar nav | `w-5 h-5 text-current` |
| Users | Sidebar nav (customers) | `w-5 h-5 text-current` |
| Chart bar | Sidebar nav (metrics) | `w-5 h-5 text-current` |
| Shield | Sidebar nav (admin) | `w-5 h-5 text-current` |
| Server | Sidebar nav (sources) | `w-5 h-5 text-current` |
| Heart pulse | Sidebar nav (health) | `w-5 h-5 text-current` |
| Search | Search input | `w-4 h-4 text-gray-400` |
| Chevron right | Pagination, breadcrumb | `w-4 h-4 text-gray-400` |
| X (close) | Modal close, dismiss | `w-5 h-5 text-gray-500` |
| Plus | Create button | `w-4 h-4 text-current` |
| Check circle | Success state | `w-5 h-5 text-green-500` |
| Alert triangle | Warning state | `w-5 h-5 text-amber-500` |
| X circle | Error state | `w-5 h-5 text-red-500` |
| Logout | User menu | `w-4 h-4 text-current` |
| Spinner | Loading states | `w-4 h-4 animate-spin` |

All icons: `stroke-width="1.5"`, `stroke="currentColor"`, `fill="none"`. Consistent with Heroicons outline style.

---

## 8. Elevation & Shadows

Minimal shadow usage. Flat is the default.

| Level | Shadow | Usage |
|-------|--------|-------|
| **Level 0** | none | Default for all elements |
| **Level 1** | `shadow-sm` | Cards, dropdowns on hover |
| **Level 2** | `shadow-lg` | Modals, floating elements |

No `shadow-md`. The jump from `sm` to `lg` is intentional — intermediate shadow creates visual clutter.

---

## 9. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-md` | 6px | Badges, small pills |
| `rounded-lg` | 8px | Inputs, buttons, table containers |
| `rounded-xl` | 12px | Cards |
| `rounded-2xl` | 16px | Modals, chat bubbles |
| `rounded-full` | 9999px | Avatars, status dots |

---

## 10. Animation & Transitions

Minimal, purposeful animation. Never decorative.

| Interaction | Transition | Tailwind |
|-------------|-----------|----------|
| Button hover | Color change | `transition-colors duration-150` |
| Input focus | Border color | `transition-colors duration-150` |
| Modal open | Fade + scale | `transition-all duration-200` |
| Modal overlay | Fade in | `transition-opacity duration-200` |
| Sidebar collapse | Width slide | `transition-[width] duration-200` |
| Skeleton pulse | Opacity pulse | `animate-pulse` |
| Spinner | Rotate | `animate-spin` |
| Toast enter | Slide up + fade | `transition-all duration-300` |

**Never animate**: layout shifts, scroll positions, table rows appearing, page transitions.

---

## 11. Sidebar Navigation

```
┌──────────────────────────┐
│  ◆ Customer 360          │  Logo + app name
│                          │
│  MAIN                    │  Section label
│  ▸ Chat                  │  Active: bg-indigo-100 text-indigo-700
│    Customers             │  Default: text-gray-600 hover:bg-gray-100
│                          │
│  ANALYTICS               │  (cs_manager, ops, admin)
│    Metrics Catalog       │
│                          │
│  ADMINISTRATION          │  (admin only)
│    Users                 │
│    Sources               │
│    Roles                 │
│                          │
│  SYSTEM                  │  (ops, admin)
│    Health                │
│                          │
│  ────────────────────    │  Divider
│  SC  Sarah Chen          │  Avatar + name
│      cs_manager          │  Role badge
│      [Logout]            │
└──────────────────────────┘
```

| Element | Style |
|---------|-------|
| Section label | `text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-1` |
| Nav item (default) | `flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-100 transition-colors` |
| Nav item (active) | `bg-indigo-100 text-indigo-700` |
| Nav icon | `w-5 h-5` (inherits text color) |
| User section | `border-t border-gray-200 p-4 mt-auto` |

The sidebar renders navigation sections conditionally based on user permissions. Sections with no visible items are hidden entirely (including the section label).

---

## 12. Empty & Error States

### Empty State

```
┌─────────────────────────────────────────┐
│                                         │
│              [Icon: Inbox]              │
│                                         │
│         No customers found              │
│                                         │
│   Try adjusting your search filters     │
│   or create a new customer.             │
│                                         │
│        [Create Customer]                │
│                                         │
└─────────────────────────────────────────┘
```

Centered in content area. Icon: `w-12 h-12 text-gray-300`. Title: `text-sm font-medium text-gray-900`. Description: `text-sm text-gray-500`.

### Error State

```
┌─────────────────────────────────────────┐
│                                         │
│           [Icon: Alert]                 │
│                                         │
│       Something went wrong              │
│                                         │
│  We couldn't load the customer data.    │
│  Please try again.                      │
│                                         │
│           [Retry]                       │
│                                         │
└─────────────────────────────────────────┘
```

Same layout as empty state. Icon: `text-red-400`.

---

## 13. Health Score Visualization

Health scores (0-100) use color coding:

| Range | Status | Color | Badge |
|-------|--------|-------|-------|
| 70-100 | Healthy | green | `bg-green-100 text-green-700` |
| 40-69 | Needs attention | amber | `bg-amber-100 text-amber-700` |
| 0-39 | At risk | red | `bg-red-100 text-red-700` |

Metric card for health score:

```
┌──────────────────────┐
│  Customer Health     │   text-xs text-gray-500
│                      │
│  78.5                │   text-2xl font-bold text-green-700
│  ━━━━━━━━━━━━━━━━░░ │   Progress bar (green)
│                      │
│  Healthy             │   Badge: bg-green-100 text-green-700
└──────────────────────┘
```

---

## 14. Event Timeline Styling

Each event type has a distinct visual:

| Event Type | Icon Color | Accent | Badge |
|-----------|-----------|--------|-------|
| `support_ticket` | amber-500 | Left border amber-300 | `bg-amber-100 text-amber-700` |
| `meeting` | indigo-500 | Left border indigo-300 | `bg-indigo-100 text-indigo-700` |
| `usage_event` | gray-500 | Left border gray-300 | `bg-gray-100 text-gray-700` |

Timeline item:

```
┌──────────────────────────────────────────────────────────────┐
│  ●  Jan 25, 2025 · 2:30 PM                                  │
│  │                                                            │
│  │  ┌────────────────────────────────────────────────────┐   │
│  │  │ ▎ Support Ticket          [support_ticket] [jira]  │   │
│  │  │ ▎ API rate limiting issue                          │   │
│  │  │ ▎                                                  │   │
│  │  │ ▎ Customer reports hitting rate limits on /search  │   │
│  │  │ ▎ during peak hours.                               │   │
│  │  │ ▎                                                  │   │
│  │  │ ▎ priority: high · status: open                    │   │
│  │  └────────────────────────────────────────────────────┘   │
│  │                                                            │
│  ●  Jan 20, 2025 · 10:00 AM                                 │
│     ...                                                       │
└──────────────────────────────────────────────────────────────┘
```

Timeline line: `border-l-2 border-gray-200` with dots at each event.
Event card: `border-l-3 border-{type-color}-300 bg-white rounded-lg p-4`.

---

## 15. Toast Notifications

Appear in the top-right corner, stack downward. Auto-dismiss after 5 seconds.

| Variant | Icon | Left border | Background |
|---------|------|-------------|------------|
| **Success** | Check circle (green) | `border-l-4 border-green-500` | `bg-white` |
| **Error** | X circle (red) | `border-l-4 border-red-500` | `bg-white` |
| **Warning** | Alert triangle (amber) | `border-l-4 border-amber-500` | `bg-white` |
| **Info** | Info circle (blue) | `border-l-4 border-blue-500` | `bg-white` |

Toast container: `fixed top-4 right-4 z-[60] flex flex-col gap-3 w-full max-w-sm sm:max-w-96 px-4 sm:px-0`
Toast item: `bg-white rounded-lg shadow-lg border border-gray-200 border-l-4 p-4`

Toast rules:
- **z-index**: `z-[60]` — above modals (`z-50`) to remain visible during modal flows
- **Max stack**: 3 toasts visible at once. Oldest auto-dismissed when 4th arrives.
- **Auto-dismiss timing**: Success/info = 5s, warning = 8s, error = manual dismiss only (user must click X)
- **Mobile**: Full-width with `px-4` gutter below `sm` breakpoint

---

## 16. Responsive Behavior

| Breakpoint | Sidebar | Layout | Tables |
|-----------|---------|--------|--------|
| `< 768px` | Hidden (hamburger toggle) | Single column | Horizontal scroll |
| `768-1024px` | Collapsed (icons only, `w-16`) | Full width | Full table |
| `> 1024px` | Expanded (`w-64`) | Constrained (`max-w-7xl`) | Full table |

Chat page is the exception: it uses full available width at all breakpoints. No `max-w-7xl` constraint.

---

## 17. Dark Mode

**Not implemented.** The app uses a light theme only. The design system is structured to support dark mode in the future by swapping Tailwind color classes via the `dark:` prefix, but this is out of scope for the assignment.

---

## 18. Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";
import forms from "@tailwindcss/forms";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont",
          '"Segoe UI"', "Roboto", '"Helvetica Neue"', "Arial", "sans-serif",
        ],
        mono: [
          "ui-monospace", "SFMono-Regular", '"SF Mono"', "Menlo",
          "Consolas", '"Liberation Mono"', "monospace",
        ],
      },
      maxWidth: {
        "8xl": "88rem",
      },
    },
  },
  plugins: [forms],
} satisfies Config;
```

Minimal config. We use Tailwind's default color palette (`slate` for grays, `indigo` for primary). No custom colors needed — the design system maps usage to existing Tailwind classes through component conventions.

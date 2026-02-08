# Contract Review — Final Consolidated Report

**Reviewed by**: 5 Independent BA Senior Reviewers
**Scope**: 22 YAML files in `contracts/v1/`
**Date**: 2026-02-08

---

## Methodology

Each reviewer independently analyzed the contracts from their specialty:
- **BA#1**: API Contract Consistency
- **BA#2**: RBAC & Permissions
- **BA#3**: Data Models & Entities
- **BA#4**: Behavior, Specs & Implementation Order
- **BA#5**: Cross-Cutting Concerns

Issues found by **multiple reviewers independently** are marked with the reviewer consensus count. These carry the highest confidence.

---

## CRITICAL (Must fix before implementation)

### 1. Missing Source Model — Phantom Entity Referenced Everywhere
**Consensus: 3/5 reviewers** (BA#1, BA#3, BA#5)

No `models/source.yaml` exists, yet `Source` is referenced across 6+ files:
- `customer.source_id` and `event.source_id` (foreign keys with no ref target)
- `CustomerSummary.source_name` and `EventSummary.source_name` (join on undefined table)
- Context map declares `Source` aggregate
- Glossary defines "source" but with **no `model_ref`**
- Tools `get_sources_list` and `get_source_status` exist but no entity defines the shape
- Ingestion webhook validates tokens against an unspecified table

**Fix**: Create `models/source.yaml` with fields: `id`, `name`, `api_token_hash`, `is_active`, `description`, plus standard audit/soft-delete fields.

---

### 2. `events.read.filter_by_type` — Dead Permission Causing Hierarchy Violation
**Consensus: 3/5 reviewers** (BA#2, BA#4, BA#5)

This permission is:
- Defined in `permissions.yaml`
- Assigned **only** to `support` role (hierarchy violation: cs_manager/admin don't have it)
- **Never enforced** — no API endpoint, no tool mapping, no acceptance criteria requires it
- Missing from the permission matrix comment in `roles.yaml`
- US-2.4 treats event-type filtering as universally available

**Fix**: Either remove it entirely (if filtering is universal) or define enforcement (separate tool, parameter-level permission) and add it to cs_manager/ops/admin roles.

---

### 3. Phase 1 Cannot Function Without Phase 2 Authentication
**Found by**: BA#4

Phase 1 stories (US-1.1, US-1.2, US-1.3, US-2.1, US-2.3) all require `auth_required: true` endpoints. But US-5.1 (JWT login) is in Phase 2. **Phase 1 is undeliverable as specified.**

**Fix**: Move US-5.1 to Phase 1 as the first story, or explicitly document that Phase 1 endpoints run unprotected during development.

---

### 4. Event Entity: Append-Only vs Soft-Delete Contradiction
**Consensus: 2/5 reviewers** (BA#1, BA#3)

Event declares `write_pattern: append-only` and glossary says "never modified after creation." Yet it has `deleted_at`/`deleted_by` fields (mutation). Additionally missing `updated_at`/`updated_by` that all other entities have.

**Fix**: Decide one pattern: (a) truly append-only → remove soft-delete fields, or (b) allow soft-delete → change to `append-with-logical-delete` and add `updated_at`/`updated_by`.

---

### 5. Missing ChatSession Model
**Consensus: 2/5 reviewers** (BA#3, BA#5)

Context map declares `ChatSession` aggregate with `get_session_history` operation. Chat API uses `session_id`. But no model file exists defining session entity, message storage, TTL, or cleanup strategy. `common.yaml#message_role` enum is defined but never referenced.

**Fix**: Create `models/session.yaml` or document that sessions are ephemeral with no model needed (and remove `ChatSession` from context map).

---

### 6. Health Check Endpoint — Contractually Stranded
**Consensus: 2/5 reviewers** (BA#1, BA#5)

`GET /api/health` is defined inside `models/common.yaml` (wrong file type), has no API contract file, no user story, no use case, and isn't in `_index.yaml`'s file map. The `system.health.read` permission exists but it's unclear if health check should be public (load balancers) or protected.

**Fix**: Create `api/health.yaml` or `api/system.yaml`. Add a user story. Decide on auth requirements.

---

### 7. `GET /auth/me` and Login Response Inline — Triple Source of Truth
**Found by**: BA#1

Login response embeds a `user` object inline, `GET /auth/me` defines its response inline, and `models/user.yaml` defines `CurrentUser`. Three definitions of the same shape = guaranteed drift.

**Fix**: Both should `$ref` to `models/user.yaml#CurrentUser`.

---

## MAJOR (Should fix before implementation)

### 8. Missing `GET /api/users` Endpoint
**Consensus: 2/5 reviewers** (BA#2, BA#5)

`users.read` permission is defined and assigned to admin, but no listing endpoint exists. Admin cannot browse users before updating/deactivating them.

**Fix**: Add `GET /api/users` with `required_permission: users.read`.

---

### 9. 4 out of 13 Permissions (31%) Are Orphans
**Consensus: 2/5 reviewers** (BA#2, BA#5)

| Permission | Assigned To | Has Endpoint? | Has Tool? |
|---|---|---|---|
| `events.read.filter_by_type` | support | No | No |
| `system.config.manage` | admin | No | No |
| `customers.export` | cs_manager, admin | No | No |
| `metrics.catalog.manage` | admin | No | No |

**Fix**: Remove orphans or define their enforcement points. Each represents either dead contract or a missing feature.

---

### 10. `customer_identifier` Resolution Undocumented
**Consensus: 2/5 reviewers** (BA#1, BA#3)

Ingestion uses `customer_identifier: string` but events store `customer_id: uuid`. No contract specifies: which Customer field is matched, what happens on no match, or whether it's case-sensitive.

**Fix**: Document the resolution strategy in ingestion.yaml or a behavior rule.

---

### 11. US-2.4 Uses Wrong Priority Vocabulary
**Consensus: 2/5 reviewers** (BA#4, BA#5)

All stories use `must-have | should-have | nice-to-have`. US-2.4 uses `priority: high`, which isn't in the defined set.

**Fix**: Change to the correct value from the defined vocabulary.

---

### 12. Permission Matrix Comment Typo
**Found by**: BA#2

`roles.yaml` matrix uses `metrics.catalog.mgmt` but actual permission is `metrics.catalog.manage`.

**Fix**: Correct the matrix label.

---

### 13. `ingestion.yaml` Missing `base_path` + Inline Responses
**Found by**: BA#1, BA#5

Only API file without `base_path`. Source CRUD paths hardcode `/api`. Response bodies are inline instead of using model refs.

**Fix**: Add explicit `base_path` or clarify divergence. Refactor responses to use refs after creating Source model.

---

### 14. 403 Missing from `error_response.http_status_mapping`
**Found by**: BA#1

Multiple endpoints define 403 responses, but `common.yaml` mapping only covers 400/401/404/429/500/503. No `FORBIDDEN` error code.

**Fix**: Add `403: FORBIDDEN` to the mapping.

---

### 15. Missing Foreign Key `ref` Declarations
**Found by**: BA#3

| Field | Missing `ref:` |
|---|---|
| `customer.source_id` | `sources.id` |
| `event.source_id` | `sources.id` |
| `event.customer_id` | `customers.id` |
| `customer_metrics.customer_id` | `customers.id` |
| `customer_metrics.metric_name` | `metric_definitions.name` |

**Fix**: Add `ref:` declarations to match the pattern used by audit fields.

---

### 16. `CustomerMetric.updated_at` Missing `auto: true`
**Found by**: BA#3

All other entities mark `updated_at` with `auto: true`. This one doesn't.

**Fix**: Add `auto: true`.

---

### 17. No Agent Rule for Conversation History Limits
**Found by**: BA#4

No behavioral rule addresses what happens when chat history exceeds the LLM context window. Long conversations will hit token limits with undefined behavior.

**Fix**: Add AB-9 defining truncation/summarization strategy.

---

### 18. UC-8-C Leaks Account Existence
**Found by**: BA#4

Deactivated user login returns "401 — account deactivated" (distinct from invalid credentials), contradicting the anti-enumeration principle established by UC-8-B.

**Fix**: Return the same generic error for all 401 cases.

---

### 19. No User Story for Scheduler Service
**Found by**: BA#4

Three scheduled jobs (metric recomputation, health scores, days-since-contact) are in scope but have zero stories, zero acceptance criteria, and undefined formulas.

**Fix**: Add US-3.3 or equivalent with acceptance criteria for each job.

---

### 20. UC-2 through UC-5 Missing Error/Alternative Flows
**Found by**: BA#4

Only UC-1, UC-6, UC-8, UC-9 have alternative flows. UC-2–UC-5 have none despite obvious failure modes (404, 403, empty results).

**Fix**: Add alternative flows for at least: not found, permission denied, empty results.

---

### 21. `chat.yaml` Endpoint `story_refs` Omits US-1.4 and US-1.5
**Found by**: BA#5

File-level header correctly lists all 5 stories, but the endpoint's machine-readable `story_refs` array only has [US-1.1, US-1.2, US-1.3].

**Fix**: Add US-1.4 and US-1.5 to the endpoint `story_refs`.

---

### 22. Context Map Actors Missing Interactions
**Consensus: 2/5 reviewers** (BA#4, BA#5)

- `admin` actor missing `customer-management`, `activity-tracking`, `conversational-agent`
- `internal_user` actor missing `activity-tracking`, `metrics-engine`

**Fix**: Update `interacts_with` lists to reflect actual permission-based access.

---

### 23. Scope Tags Applied Inconsistently
**Found by**: BA#5

Some files explicitly say `scope: both`, others rely on "implicit both" convention. `user.yaml` says `scope: both` explicitly while `customer.yaml` says nothing. Login endpoint = `scope: assignment` but US-5.1 = `scope: both` (semantic contradiction).

**Fix**: Either add explicit scope to all files or document the convention more clearly.

---

## MINOR (Fix when convenient)

| # | Issue | Found by |
|---|---|---|
| 24 | Missing `password_hash` field in User entity | BA#3 |
| 25 | Missing `user` glossary term | BA#3 |
| 26 | Role enum hardcoded inline instead of using common.yaml ref | BA#3 |
| 27 | `optional` vs `nullable` vs `?` suffix semantics undefined | BA#1, BA#3 |
| 28 | `CustomerMetricValue` joined fields lack `notes:` block | BA#1, BA#3 |
| 29 | Request body fields as arrays instead of objects (unusual style) | BA#1 |
| 30 | Login `password min: 1` vs create user `min: 8` (needs comment) | BA#1 |
| 31 | `POST /chat` has redundant `Authorization` header | BA#1 |
| 32 | Missing `429` on chat endpoint despite being most expensive | BA#1 |
| 33 | `total` in cursor pagination may be expensive | BA#1 |
| 34 | `tool-permission-map.yaml` `available_to` is redundant/derivable | BA#2 |
| 35 | No deactivated-user handling in RBAC enforcement flow | BA#2 |
| 36 | Missing traceability (`story_ref`) on AB-1, AB-2, AB-5..AB-8 | BA#4 |
| 37 | UC-6 steps 5-8 are async processing, not main flow | BA#4 |
| 38 | Phase 2 story dependencies not explicitly declared | BA#4 |
| 39 | `_index.yaml` file list doesn't include models/ directory | BA#1 |
| 40 | `message_role` enum defined but never referenced | BA#3, BA#5 |
| 41 | `order` param in events.yaml uses inline values instead of ref | BA#5 |
| 42 | Soft-delete filter unclear for cross-context embedded queries | BA#5 |
| 43 | Workers/scheduler lack bounded context mapping | BA#5 |
| 44 | `event_type` extensibility has no extension mechanism | BA#5 |
| 45 | Inconsistent error response coverage across endpoints | BA#5 |

---

## Summary Statistics

| Severity | Count |
|---|---|
| **CRITICAL** | 7 |
| **MAJOR** | 16 |
| **MINOR** | 22 |
| **Total** | **45** |

**High-consensus issues** (found by 2+ reviewers independently): **12 issues**

---

## Top 5 Priority Actions

1. **Create `models/source.yaml`** — Unblocks 5+ files, 2 tools, FK references, and ingestion pipeline (3 reviewers agree)
2. **Resolve `events.read.filter_by_type`** — Dead permission + hierarchy violation (3 reviewers agree)
3. **Move US-5.1 to Phase 1** — Phase 1 is undeliverable without auth
4. **Resolve Event append-only contradiction** — Foundational design decision affecting audit trail design
5. **Clean up orphan permissions** — 31% of permissions (4/13) have no enforcement point; reduces contract noise

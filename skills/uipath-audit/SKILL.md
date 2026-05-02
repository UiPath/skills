---
name: uipath-audit
description: "[PREVIEW] UiPath audit events — list sources, query events with cursor pagination, and export ZIPs from the long-term store via `uip admin audit org|tenant {sources|events|export}`. For governance policies→uipath-gov-aops-policy."
allowed-tools: Bash, Read, Write, Grep, Glob
---

# UiPath Audit

Skill for querying and exporting UiPath audit events via `uip admin audit`. Covers six commands across two scopes (`org` and `tenant`) and three verbs (`sources`, `events`, `export`). Use when an admin asks "who did X to Y", "show me logins last week", or "give me an audit dump for January".

## When to Use This Skill

Activate on both **explicit audit requests** and **natural-language investigation intent** — users rarely say "audit events" by name.

**Explicit requests:**

- User asks about `uip admin audit` commands.
- User asks to list audit event sources / targets / types.
- User asks to query, filter, paginate, or export audit events.
- User wants a CSV/ZIP dump of audit history for a window.

**Investigation intent (rule/policy patterns without naming the product):**

- "Who deleted the X folder last Tuesday?"
- "Show me failed logins for user Y this month."
- "What changed on tenant Z between Jan 1 and Feb 1?"
- "Give me the audit log for the last 30 days."
- "Was the API key rotated by someone in our org?"
- "Export everything for compliance for Q4."

## Recognize Audit Intent → Pick a Scope

The `org` vs `tenant` choice matters — they hit different basePaths and surface different events.

| User says... | Likely scope | Why |
|---|---|---|
| "who joined / left the organization", "who was made an admin", "license changes", "cross-tenant audit" | **org** | Org-level admin events (memberships, license, tenant lifecycle) live under `/orgaudit_`. |
| "what happened on tenant X", "logins on this tenant", "policy changes within a tenant", "asset/queue/folder edits" | **tenant** | Tenant-scoped events (Orchestrator, AOps, AI Trust, etc.) live under `/{tenantId}/tenantaudit_`. |
| "everything everywhere" | **both** — run the same flow once per scope and present combined results. |

### Disambiguation rule — never silently default

If the user's prompt is **vague about scope** (e.g. "export the audit log", "show me events", "give me sources") AND the conversation has **no prior turn that established scope or tenant**, **stop and ask** before running any command. Do not assume `tenant` just because it's the more common case — silently picking the wrong scope means the user gets data they didn't intend (org events when they wanted tenant, or vice versa) and they may not realize it for hours.

Wording template (use one yes/no question, two clarifications max):

> Quick check before I run this — should this be at:
>
> - **`org` scope** (organization-level admin events: memberships, license, tenant lifecycle), or
> - **`tenant` scope** (events scoped to a specific tenant)?
>
> If `tenant`, which tenant? (I see `<tenantA>`, `<tenantB>` in your login context — or pass an explicit GUID.)

When to **skip the question** and proceed:

1. **Scope is explicit in the current prompt** — the user wrote "tenant", "org", a tenant name, or a clear org-level phrase from the table above. Use it directly.
2. **Scope was established earlier in this conversation** — e.g. the user said "let's investigate tenant Acme-Prod" three turns ago and is now asking "and now export it." Reuse that scope and tenant; don't re-ask. Do mention which scope you're using in the response so the user can correct if they meant to switch.
3. **The login context disambiguates trivially** — only one tenant is selected AND the intent table strongly matches tenant. Even then, name the tenant in your response so the user can catch a mismatch.

If you ask and the user names a tenant by display name (not GUID), resolve it via the login context before passing `--tenant-id`. If you can't resolve it, ask for the GUID rather than guessing.

## Critical Rules

1. **Always run `uip login status --output json` first.** If `loginStatus !== "Logged in"`, surface the hint and stop. Never auto-`uip login` — interactive OAuth blocks an automation.
2. **Pick scope before any other call — and don't silently default.** Use the [Disambiguation rule](#disambiguation-rule--never-silently-default) above: if the prompt is vague AND there's no prior conversational context, **ask** which scope (and which tenant if `tenant`). Only proceed without asking when scope is explicit in the prompt, established earlier in the conversation, or unambiguously implied by login context AND intent. `tenant` requires either a tenant in the login context or `--tenant-id <guid>`. `org` ignores `--tenant-id`.
3. **Discover source IDs with `sources` before filtering `events` by `--source/--target/--type`.** Never invent GUIDs — the SDK won't help you guess.
4. **`events` returns `{ auditEvents, next, previous }` — NOT a bare array.** Do not assume `Data` is iterable directly. The cursor naming is **chronological**: `next` = newer, `previous` = older. Walking newest-backward (the default) follows `previous`.
5. **`events` server-clamps `maxCount` to `[10, 200]`.** When the user wants more than 200, the tool paginates internally — pass `--limit N` and the tool fetches `ceil(N/200)` pages. Do not re-implement pagination in the agent.
6. **`export` writes a ZIP from the long-term store.** `--from-date` and `--to-date` are required and ISO 8601. Always use `--output-file <path>`. Never overwrite a path the user did not explicitly approve.
7. **Pass `--output json` on every `sources` and `events` call** when the response is being parsed. `export` does not need it (the JSON envelope is just metadata; the ZIP goes to `--output-file`).
8. **Stop and surface the error if any command fails.** Do not retry on auth errors — `Audit.Read` scope must already be on the bearer token; retrying does nothing useful.
9. **Use ISO 8601 for time bounds.** Date-only (`2026-04-01`) or with time (`2026-04-01T14:30:00Z`). Always UTC when in doubt — the audit service stores and returns UTC.

## Quick Start

These steps are for the canonical "find events in a window then export" flow. For specific scenarios jump to the [Task Navigation](#task-navigation) table.

### Step 0 — Verify the `uip` CLI

```bash
which uip && uip --version
```

If not installed:

```bash
npm install -g @uipath/cli
```

### Step 1 — Check login status

```bash
uip login status --output json
```

If `loginStatus !== "Logged in"`, instruct the user to run `uip login` and stop. The audit service rejects calls in 5ms at the gateway when the token's `aud` claim is missing `Audit`.

### Step 1.5 — Confirm scope (skip only if already explicit or established earlier in the conversation)

If the prompt didn't specify `org` vs `tenant` (and which tenant), pause and ask once before running anything. See the [Disambiguation rule](#disambiguation-rule--never-silently-default) for the canonical wording. Stating the scope in your reply (e.g. "Running tenant export against `Acme-Prod`…") gives the user one last chance to correct the assumption even when it was clearly implied.

### Step 2 — Discover sources at the right scope

Run **once** at the start of an investigation; cache the result for this session.

```bash
# Tenant-scoped (most common)
uip admin audit tenant sources --output json > sources.json

# Org-scoped (admin events: tenant lifecycle, license, memberships)
uip admin audit org sources --output json > sources-org.json
```

Each entry has `id` (a GUID — pass to `events --source`), `name` (human-readable), and `eventTargets[]` (each with their own GUIDs and `eventTypes[]`).

### Step 3 — Query events with filters

```bash
# Filter by source ID + 7-day window, limit 50
uip admin audit tenant events \
  --source <SOURCE_GUID_FROM_STEP_2> \
  --from-date 2026-04-22T00:00:00Z \
  --to-date   2026-04-29T00:00:00Z \
  --limit 50 \
  --output json
```

The response shape:

```json
{
  "Result": "Success",
  "Code": "AuditTenantEvents",
  "Data": {
    "auditEvents": [ ... ],
    "next":     null,                       // chronologically newer (often null at "now")
    "previous": "/...?before=...&beforeId=..."   // chronologically older — the next page going back in time
  }
}
```

For more than 200 events, just pass `--limit 500` (or larger) — the tool paginates internally. Do not write a manual loop on `--from-date`/`--to-date` in the agent.

### Step 4 — Export for compliance / sharing

```bash
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date   2026-02-01 \
  --output-file ./audit-jan.zip
```

The tool issues one HTTP call per UTC day inside the window and aggregates the responses into a single flat ZIP at `--output-file`. The result envelope reports `{Path, Bytes, Format: "zip", Days, NonEmptyDays}`. On any chunk failure (e.g. HTTP 504), no file is written and the error identifies which day failed.

## Anti-patterns

- **Do NOT** assume `events` returns a bare array. It's `{auditEvents, next, previous}`.
- **Do NOT** loop on `--from-date`/`--to-date` to "paginate" — that's not what those flags do. Just bump `--limit` and the CLI handles cursor pagination internally.
- **Do NOT** silently default to `tenant` (or `org`) when the user's prompt is ambiguous about scope. Ask which scope, and for tenant scope which tenant, **before** running anything. The exception is when the conversation already established scope on a prior turn.
- **Do NOT** invent source/target/type GUIDs. Always discover via `sources` first.
- **Do NOT** call `events` with no time bound on a noisy tenant — the response will be huge and unanchored. Default to a bounded window.
- **Do NOT** pass `--tenant-id` to `org`-scoped commands — it's silently ignored. If you find yourself doing this, you probably meant `tenant` scope.
- **Do NOT** retry on 401 auth errors. The token is missing the `Audit.Read` scope; retrying produces the same failure. Tell the user to `uip logout && uip login` so the new scope is included.
- **Do NOT** export into a directory that doesn't exist without confirming with the user. The tool will create parent dirs but the path itself must be one the user approved.
- **Do NOT** assume per-day files inside the export ZIP are CSV — they are JSON arrays with PascalCase keys (`Id`, `CreatedOn`, `EventType`…). The CLI does not currently re-format them. If a CSV is needed, that's a post-processing step on the agent's side.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Find who did X to resource Y** | Quick Start — Steps 1–3, with `--source` and `--target` from the `sources` discovery output |
| **Show login history for user X** | [audit-workflow-guide.md — Investigation 2](./references/audit-workflow-guide.md) |
| **Export a date-range dump** | Quick Start — Step 4, or [audit-workflow-guide.md — Investigation 3](./references/audit-workflow-guide.md) |
| **Compare org-level vs tenant-level activity** | [audit-workflow-guide.md — Investigation 4](./references/audit-workflow-guide.md) |
| **Look up command flags / output shapes** | [audit-commands.md](./references/audit-commands.md) |
| **Paginate beyond 200 events** | [audit-commands.md — events flag table](./references/audit-commands.md), Critical Rule #5 |
| **Recognize a scope from natural-language intent** | Intent table at the top of this SKILL.md |

## Key Concepts

### Scope determines basePath, not query params

- `org`    → `{baseUrl}/{orgId}/orgaudit_/api/Query/...`
- `tenant` → `{baseUrl}/{orgId}/{tenantId}/tenantaudit_/api/Query/...`

Same `QueryApi` underneath; the only difference is which segment the SDK puts in the URL.

### Cursor pagination is chronological, not pagination-order

| Cursor | Direction | When you'd follow it |
|---|---|---|
| `next` | events **newer** than the current page | rare — only useful when starting from a historical anchor and walking forward |
| `previous` | events **older** than the current page | common — paginating from "now" backwards through history |

The CLI tool follows `previous` automatically when `--limit > 200`. If you're driving cursor-by-cursor manually, follow `previous` for "load more older."

### `events` `Data` shape vs `sources`/`export`

| Verb | `Data` shape |
|---|---|
| `sources` | array of `AuditEventSourceDto` |
| `events` | object `{auditEvents, next, previous}` |
| `export` | object `{Path, Bytes, Format, Days, NonEmptyDays}` |

`events` is the one verb that legitimately returns an object — pagination cursors live alongside the rows. Make sure consumers handle that, not a bare array.

### Status codes

`AuditEventStatus` is a 0/1 enum on the wire. Use the labels at the CLI surface:

- `--status Success` (or `0`) — successful operations
- `--status Failure` (or `1`) — failed operations

Case-insensitive, validated client-side before any API call.

## Completion Output

When you finish a query or export, report:

1. **Operation & result** — e.g. `Found 47 audit events on tenant T in the last 7 days` or `Wrote 123,456 bytes to /path/to/audit.zip (3 days, 2 non-empty)`.
2. **Scope used** (`org` or `tenant`) and any `--tenant-id` override.
3. **Time window** — explicit ISO bounds, even if they came from a relative phrase ("last 7 days").
4. **Filters applied** — sources, types, users, status. Important for reproducibility.
5. **Cursor state** — for `events`, mention whether `previous` is null (the user has reached the start of audit history for the filter) or populated (more older events available — re-run with a larger `--limit` to fetch more; the CLI paginates internally).
6. **Next step** — "Want me to widen the window?", "Want me to export this slice?", "Want me to filter by user X?". Wait for the user's choice; do not chain mutations.

## References

- **[audit-commands.md](./references/audit-commands.md)** — Single source of truth for every `uip admin audit` subcommand: signature, every flag with required/optional, the `Code` value, and the exact `Data` shape returned. Cross-reference this when writing scripts that parse audit output.
- **[audit-workflow-guide.md](./references/audit-workflow-guide.md)** — Narrative playbook for the four canonical investigations: who-did-X, login-history, date-range-dump, and org-vs-tenant comparison. Each scenario has a worked example with literal flag values.

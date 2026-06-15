# `uip admin audit` — CLI Command Reference

Single source of truth for every `uip admin audit` subcommand, its flags, and its output shape. All commands return `{ "Result": "Success"|"Failure", "Code": "...", "Data": ... }`. Use `--output json` for programmatic parsing — every command in this skill should pass it.

> For task workflows (investigate → query → export), see [audit-workflow-guide.md](./audit-workflow-guide.md). This file only documents the command surface.

The command tree:

```
uip admin audit
├── org
│   ├── sources
│   ├── events
│   └── export
└── tenant
    ├── sources
    ├── events
    └── export
```

`org` and `tenant` are **subject subgroups** — pass scope as this **positional segment** (`uip admin audit org sources`, `uip admin audit tenant export`), **never as a `--scope` flag** (there is no `--scope` option; `audit sources --scope organization` is invalid). Same three verbs under each. The two trees are 100% verb-symmetric — any flag valid on `tenant events` is also valid on `org events` (except `--tenant-id`, which is tenant-only).

## Output `Data` shape varies by verb — quick reference

| Verb | `Data` shape |
|---|---|
| `audit <scope> sources` | array of `AuditEventSourceDto` |
| `audit <scope> events` | object `{auditEvents, next, previous}` |
| `audit <scope> export` | object `{Path, Bytes, Format, Days, NonEmptyDays}` (+ `Events` when `--file-format csv`) |

`events` is the one verb that legitimately returns an object — pagination cursors live alongside the rows. Full shape detail per verb in the sections below.

---

## uip admin audit `<scope>` sources

List the audit event sources visible at this scope. Each source is a top-level event category (Identity, Tenant, Robot, Governance, …) with nested `eventTargets[]` and `eventTypes[]`.

```bash
uip admin audit org sources --output json
uip admin audit tenant sources --output json
```

**Flags:**

| Flag | Required | Description |
|---|---|---|
| `--login-validity <minutes>` | no | Refresh the bearer if its remaining lifetime is below this threshold. Rarely needed. |
| `--tenant-id <guid>` | no | **Tenant scope only.** Override the tenant from login context. Silently rejected on `org`. |

**Output `Code`:** `AuditOrgSources` / `AuditTenantSources`.

**Output `Data`:** Array of `AuditEventSourceDto`:

```json
[
  {
    "id": "692a7634-bdfc-4c77-a7ee-a8c7eef10457",
    "name": "Organization Management",
    "eventTargets": [
      {
        "id": "355b521a-4384-4d1b-8f39-e2769840d2d5",
        "name": "Org Membership",
        "eventTypes": [
          { "id": "7fb44323-cb87-40ea-bee6-8dd14f5b2c06", "name": "User Manually Joined An Org Through Invite" }
        ]
      }
    ]
  }
]
```

`Data` is **always** an array, even when empty. Pass the inner `id` GUIDs to `events --source/--target/--type`.

---

## uip admin audit `<scope>` events

Query audit events with filters and cursor pagination.

```bash
uip admin audit tenant events --from-date 2026-04-22T00:00:00Z --to-date 2026-04-29T00:00:00Z --limit 50 --output json
```

**Flags:**

| Flag | Required | Description |
|---|---|---|
| `--from-date <iso>` | no | Start of time interval, ISO 8601. Inclusive. Recommended on any non-trivial query. |
| `--to-date <iso>` | no | End of time interval, ISO 8601. Inclusive **of the exact instant** — pass the start of the next day (e.g. `2026-02-01`) or `T23:59:59.999Z` to capture a full final day. See [workflow-guide gotchas](./audit-workflow-guide.md#common-gotchas). |
| `--source <guid...>` | no | Filter by event source IDs. Repeatable. Discover with `sources`. |
| `--target <guid...>` | no | Filter by event target IDs. Repeatable. |
| `--type <guid...>` | no | Filter by event type IDs. Repeatable. |
| `--user-id <guid...>` | no | Filter by acting user IDs. Repeatable. |
| `--search <term>` | no | Server-side substring search across event content. |
| `--status <Success\|Failure\|0\|1>` | no | Case-insensitive labels or the raw `AuditEventStatus` enum values. |
| `--limit <n>` | no | Total events to return. Server clamps each individual API call to **200**; values >200 trigger client-side pagination automatically (cursor handled internally). Omitted = single call with the server's default page size (typically up to 200 events). |
| `--login-validity <minutes>` | no | Token-refresh hint. |
| `--tenant-id <guid>` | no | **Tenant scope only.** Override the active tenant. |

**Output `Code`:** `AuditOrgEvents` / `AuditTenantEvents`.

**Output `Data`:** Object — NOT a bare array — with three fields:

```json
{
  "auditEvents": [
    {
      "id": "...",
      "createdOn": "2026-04-29T17:46:07.123Z",
      "organizationId": "...",
      "organizationName": "Acme Corp",
      "tenantId": "...",          // null on org-scope events
      "tenantName": "Acme-Prod",  // null on org-scope events
      "actorId": "...",
      "actorName": "Jane Doe",
      "actorEmail": "jane@example.com",
      "eventType": "Edited policy",
      "eventSource": "Governance",
      "eventTarget": "Policy management",
      "eventDetails": "{...}",     // JSON-encoded string with type-specific fields
      "eventSummary": "...",
      "status": 0,                 // 0=Success, 1=Failure
      "clientInfo": {              // optional; absent on server-originated events
        "ipAddress": "203.0.113.42",
        "ipCountry": "US"
      }
    }
  ],
  "next":     null,                // cursor URL — events newer than this page
  "previous": "/{org}/{tenant}/tenantaudit_/api/query/events?to=...&before=...&beforeId=...&maxCount=...&qw=..."
}
```

**Cursor naming is chronological.** `next` = newer (often null when the page is anchored at "now"); `previous` = older (typically the one you follow to scroll backwards through history).

---

## uip admin audit `<scope>` export

Export the long-term audit store covering `[--from-date, --to-date]` — as a ZIP of day-wise JSON files (default) or a single merged CSV.

```bash
# Default — ZIP of one JSON file per UTC day
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date 2026-02-01 \
  --output-file ./audit-jan.zip \
  --output json

# Single merged CSV of every event
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date 2026-02-01 \
  --file-format csv \
  --output-file ./audit-jan.csv \
  --output json
```

**Flags:**

| Flag | Required | Description |
|---|---|---|
| `--output-file <path>` | **yes** | Where to write the export. Parent dir is created if missing; existing file is overwritten. Resolved to absolute internally. Match the extension to `--file-format` (`.zip` / `.csv`). |
| `--from-date <iso>` | **yes** | Start of time interval. Both bounds are required by Commander before any HTTP call. |
| `--to-date <iso>` | **yes** | End of time interval. |
| `--file-format <zip\|csv>` | no | Output shape. `zip` (default) = one JSON file per UTC day inside a ZIP. `csv` = every event merged into a single RFC 4180 CSV under a shared header. Invalid values fail before any HTTP call with `Invalid --file-format '<v>'. Use 'zip' or 'csv'.` |
| `--login-validity <minutes>` | no | Token-refresh hint. |
| `--tenant-id <guid>` | no | **Tenant scope only.** Override the active tenant. |

**Output `Code`:** `AuditOrgExport` / `AuditTenantExport`.

**Output `Data`:** `Format` echoes the chosen `--file-format`. The CSV path adds `Events` (total rows written, excluding the header); the ZIP path omits it.

```json
// --file-format zip (default)
{
  "Path": "C:\\absolute\\path\\to\\audit-jan.zip",
  "Bytes": 1841,
  "Format": "zip",
  "Days": 31,
  "NonEmptyDays": 27
}

// --file-format csv
{
  "Path": "C:\\absolute\\path\\to\\audit-jan.csv",
  "Bytes": 98765,
  "Format": "csv",
  "Days": 31,
  "NonEmptyDays": 27,
  "Events": 1234
}
```

**Implementation notes (worth knowing for diagnostic conversations):**

- Both formats share the same fetch: the CLI issues **one HTTP call per UTC day** inside `[from, to]` and aggregates the per-day responses. Mirrors the `audit-dowload-from-longterm-store.sh` pattern in the AuditService repo.
- **ZIP (default):** per-day entries land at the **root of the output ZIP** named `<YYYY-MM-DD>.txt` (no folder prefix). Each `.txt` is a JSON array of events with PascalCase keys (`Id`, `CreatedOn`, `EventType`, …).
- **CSV:** the same per-day JSON arrays are parsed and merged into **one** RFC 4180 CSV (CRLF line endings, header row first). Columns follow the long-term-store field order — `Id, CreatedOn, OrganizationId, TenantId, ActorId, ActorName, ActorEmail, ActorDetails, EventType, EventSource, EventTarget, EventDetails, Status, ClientInfo` — with any extra server fields appended (union across events) so no data is dropped. `Status` is the numeric enum (`0`=Success, `1`=Failure); nested objects (e.g. `ClientInfo`) are JSON-stringified into the cell. String cells beginning with `= + - @` (or TAB/CR) are prefixed with a single quote to neutralize spreadsheet formula injection.
- On any single-day HTTP failure (or, for CSV, a day whose payload is not valid JSON), **no file is written** and the error message identifies which day failed. Earlier successful chunks are not preserved (atomic export).
- `Days` reports the total number of UTC days requested; `NonEmptyDays` reports how many actually had data. A long export with `NonEmptyDays: 0` means the window was entirely idle, not that the export failed. For CSV, `Events: 0` yields a header-only file.

---

## Cross-cutting flags from the CLI host

These appear on every command (not just audit) — set at the program level by the `uip` host:

| Flag | Description |
|---|---|
| `--output <table\|json\|yaml\|plain>` | Format of the success/failure envelope on stdout. Defaults to `json`. The export file body (ZIP or CSV) is unaffected — `--output` only controls the metadata envelope, NOT `--file-format`. |
| `--output-filter <jmespath>` | JMESPath query applied to the envelope before printing. Useful for `events`/`sources`. Less useful for `export` (envelope is small). |
| `--log-level <debug\|info\|warn\|error>` | Logger threshold. Logs go to stderr. |
| `--log-file <path>` | Redirect logs from stderr to a file. |
| `--help, -h` | Show help. |

---

## Error envelope

```json
{
  "Result": "Failure",
  "Message": "Audit export failed for 2026-04-02 (HTTP 504): Gateway Timeout",
  "Instructions": "Ensure you are logged in with 'uip login' and have access to the audit service."
}
```

Common failure modes and what they mean:

| `Message` snippet | Likely cause | Fix |
|---|---|---|
| `Not logged in. Run 'uip login' first.` | No cached login state | `uip login` |
| `Tenant ID required for tenant-scoped audit calls.` | `tenant` scope but no tenant in login context | Add `--tenant-id <guid>` or re-`uip login` selecting a tenant |
| `HTTP 401 / WWW-Authenticate: Bearer` | Token's `aud` claim missing `Audit` | `uip logout && uip login` to mint a fresh token (the `Audit.Read` scope is in `DEFAULT_SCOPES` post-onboarding) |
| `HTTP 504` on a single export day | Long-term store query timed out for that day's volume | Re-run the export — the failed day will be retried; OR narrow the window |
| `Audit export failed for YYYY-MM-DD (HTTP 504)` | Single-day chunk failed during multi-day export | The whole export is rolled back. Re-run, or narrow `--from-date/--to-date` to skip the bad day. |

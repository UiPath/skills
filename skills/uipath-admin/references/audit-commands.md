# `uip admin audit` — CLI Command Reference

Single source of truth for every `uip admin audit` subcommand, flag, and output shape. Run every command with `--output json`; commands return `{ "Result": "Success"|"Failure", "Code": "...", "Data": ... }`.

For task workflows (investigate → query → export), see [audit-workflow-guide.md](./audit-workflow-guide.md). This file documents only the command surface.

## Command tree and scope

```text
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

Run `uip admin audit org <verb>` or `uip admin audit tenant <verb>`. Never use `--scope`; `audit sources --scope organization` is invalid. Tenant commands additionally support `--tenant-id`.

| Verb | `Data` shape |
|---|---|
| `audit <scope> sources` | array of `AuditEventSourceDto` |
| `audit <scope> events` | object `{auditEvents, next, previous}` |
| `audit <scope> export` | object `{Path, Format, Bytes, Days, NonEmptyDays}`; `Files` for `json`, `Events` for `--file-format csv` |

## `uip admin audit <scope> sources`

Run:

```bash
uip admin audit org sources --output json
uip admin audit tenant sources --output json
```

List visible audit event sources. Pass inner `id` GUIDs from `eventTargets[]` and `eventTypes[]` to `events --source/--target/--type`. `Data` is always an array, including when empty.

| Flag | Required | Description |
|---|---|---|
| `--login-validity <minutes>` | no | Refresh the bearer when its remaining lifetime is below this threshold. |
| `--tenant-id <guid>` | no | Tenant scope only; overrides the tenant from login context. Silently rejected on `org`. |

**Output `Code`:** `AuditOrgSources` / `AuditTenantSources`.

**Output `Data`:** `AuditEventSourceDto` objects containing `id`, `name`, `eventTargets`, and `eventTypes`; nested targets and types contain `id` and `name`.

## `uip admin audit <scope> events`

Run queries with filters and cursor pagination:

```bash
uip admin audit tenant events --from-date 2026-04-22T00:00:00Z --to-date 2026-04-29T00:00:00Z --limit 50 --output json
```

| Flag | Required | Description |
|---|---|---|
| `--from-date <iso>` | no | ISO 8601 start; inclusive. Recommended for non-trivial queries. |
| `--to-date <iso>` | no | ISO 8601 end; inclusive of the exact instant. Pass the next day’s start (for example `2026-02-01`) or `T23:59:59.999Z` to capture a full final day. Applies only to `events`; `export` bounds are whole-day inclusive, so the next-day trick over-exports. See [workflow-guide gotchas](./audit-workflow-guide.md#common-gotchas). |
| `--source <guid...>` | no | Repeatable event-source filter; discover IDs with `sources`. |
| `--target <guid...>` | no | Repeatable event-target filter. |
| `--type <guid...>` | no | Repeatable event-type filter. |
| `--user-id <guid...>` | no | Repeatable acting-user filter. |
| `--search <term>` | no | Server-side substring search across event content. |
| `--status <Success\|Failure\|0\|1>` | no | Case-insensitive labels or raw `AuditEventStatus` enum values. |
| `--limit <n>` | no | Use 1–10000. Larger values fail before HTTP with `Result: "ValidationError"` / `invalid_argument`; do not use a huge value for “everything”. Each API call is clamped to 200; values above 200 trigger client-side pagination. Omit it for one call with the server default, typically up to 200 events. |
| `--login-validity <minutes>` | no | Token-refresh hint. |
| `--tenant-id <guid>` | no | Tenant scope only; overrides the active tenant. |

**Output `Code`:** `AuditOrgEvents` / `AuditTenantEvents`.

**Output `Data`:** always an object, never a bare array:

```json
{
  "auditEvents": [
    {
      "id": "...",
      "createdOn": "2026-04-29T17:46:07.123Z",
      "organizationId": "...",
      "organizationName": "...",
      "tenantId": "...",
      "tenantName": "...",
      "actorId": "...",
      "actorName": "...",
      "actorEmail": "...",
      "eventType": "...",
      "eventSource": "...",
      "eventTarget": "...",
      "eventDetails": "{...}",
      "eventSummary": "...",
      "status": 0,
      "clientInfo": {
        "ipAddress": "...",
        "ipCountry": "..."
      }
    }
  ],
  "next": null,
  "previous": "/{org}/{tenant}/tenantaudit_/api/query/events?to=...&before=...&beforeId=...&maxCount=...&qw=..."
}
```

`tenantId` and `tenantName` are null on org-scope events. `eventDetails` is a JSON-encoded string with type-specific fields. `clientInfo` is optional and absent on server-originated events; when present it contains `ipAddress` and `ipCountry`. `status` is `0=Success, 1=Failure`. Cursor naming is chronological: `next` means newer and is often null when anchored at now; `previous` means older and is normally followed to scroll backward.

## `uip admin audit <scope> export`

Run the long-term audit store export for `[--from-date, --to-date]` as inclusive whole UTC days into the directory specified by `--output-path`:

```bash
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date 2026-01-31 \
  --output-path ./audit-exports \
  --output json

uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date 2026-01-31 \
  --file-format csv \
  --output-path ./audit-exports \
  --output json

day=$(date -u -d 'yesterday' +%F)   # macOS/BSD: date -u -v-1d +%F
uip admin audit tenant export \
  --from-date "$day" \
  --to-date "$day" \
  --output-path ./audit-exports \
  --output json
```

Pass a directory, never a filename or extension. Each run creates `audit_<from>_<to>_<generated-at>`: a folder of day-wise JSON files by default or one merged CSV. JSON output is `./audit-exports/audit_2026-01-01_2026-01-31_<generatedAt>/`; CSV output is `./audit-exports/audit_2026-01-01_2026-01-31_<generatedAt>.csv`. The generated-at value is to the second; repeated exports do not collide.

This is the organization/tenant audit event store (LTS-schema columns such as `Identifier`, `DateCreatedUtc`, `ActorId`, `Action`, `Source`, `Category`) for compliance dumps, login history, and cross-platform “who did what where.” It is not `uip or audit-logs list --export` (the uipath-platform skill), which exports one Orchestrator tenant’s operational actions with `Component,User,Action,Operation,Time` columns. An org/tenant audit-event or compliance export with a date window and `--output-path`, whether JSON files or spreadsheet/Excel CSV, belongs here.

| Flag | Required | Description |
|---|---|---|
| `--output-path <dir>` | **yes** | Base directory, created if missing. Pass a directory only, never a filename or extension. The CLI creates a uniquely named folder of day-wise JSON files (`json`) or a single `.csv` (`csv`) inside it using `audit_<from>_<to>_<generated-at>`. It resolves the path to an absolute path internally. |
| `--output-file <dir>` | no | Deprecated alias for `--output-path`; it remains a base directory, not a file. Prefer `--output-path`; this flag emits a deprecation warning. |
| `--from-date <iso>` | **yes** | Required by Commander before HTTP. Interpreted as a whole UTC day; time components are truncated to the calendar day. |
| `--to-date <iso>` | **yes** | Required by Commander before HTTP. Inclusive as a whole UTC day. `--from-date X --to-date X` exports only day `X`; do not pass the next day to capture the final day. |
| `--file-format <json\|csv>` | no | `json` default: one `<YYYY-MM-DD>.json` per UTC day in a folder. `csv`: all events in one RFC 4180 CSV under a shared header. Invalid values fail before HTTP with `Invalid --file-format '<v>'. Use 'json' or 'csv'.` |
| `--login-validity <minutes>` | no | Token-refresh hint. |
| `--tenant-id <guid>` | no | Tenant scope only; overrides the active tenant. |

**Output `Code`:** `AuditOrgExport` / `AuditTenantExport`.

**Output `Data`:** contains `Path`, `Format`, `Bytes`, `Days`, `NonEmptyDays`, and `GeneratedAt`. `Format` echoes `--file-format`. `Path` is the generated folder under `--output-path` for JSON or the generated `.csv` for CSV. JSON additionally contains `Files`; CSV additionally contains `Events` (rows excluding the header).

```json
{
  "Path": "C:\\absolute\\path\\to\\audit-exports\\audit_2026-01-01_2026-01-31_20260617T112630",
  "Format": "json",
  "Files": 27,
  "Bytes": 1841,
  "Days": 31,
  "NonEmptyDays": 27,
  "GeneratedAt": "2026-06-17T11:26:30.000Z"
}
```

For CSV, `Path` ends in `.csv`, `Format` is `csv`, and `Events` reports total rows; `Bytes`, `Days`, `NonEmptyDays`, and `GeneratedAt` remain present.

### Export behavior and diagnostics

- Run one HTTP call per UTC day in `[from, to]`; both formats aggregate those responses, mirroring `audit-dowload-from-longterm-store.sh`.
- For JSON, create a uniquely named `audit_<from>_<to>_<generated-at>` folder with `<YYYY-MM-DD>.json` files. Write server `.txt` payloads with `.json` because they contain JSON arrays with LTS-schema keys (`Identifier`, `DateCreatedUtc`, `Action`, …). Flatten nested-ZIP entries to `<inner>_<outer>.json`; give same-name collisions an iso-day suffix. Validate entry names as safe basenames, confirm they resolve inside the folder before writing, and prevent path traversal / Zip-Slip.
- For CSV, parse the same per-day JSON arrays into one RFC 4180 CSV with CRLF endings and a first header row. Use this field order: `OrganizationId, TenantId, ActorId, ActorEmail, ActorDetails, EventDetails, Status, Identifier, DateCreatedUtc, User, Action, Source, Category, ClientInformation`; append extra server fields by union across events. Stringify nested objects such as `ClientInformation`. Keep `Status` numeric (`0`=Success, `1`=Failure). Prefix string cells beginning with `= + - @` or TAB/CR with a single quote to neutralize spreadsheet formula injection.
- On any single-day HTTP failure, or a CSV day with invalid JSON, write nothing. For JSON, do not create the output folder. Identify the failed day; discard earlier chunks to preserve atomic export.
- `Days` is the requested UTC-day count; `NonEmptyDays` is the count containing data. `NonEmptyDays: 0` means an idle window, not failure. JSON `Files` counts written day files; CSV `Events: 0` produces a header-only file.
- The long-term store lags live `events`, typically by up to ~24–48 h. Recent days can be empty even when `events` has data. For completeness, end the window ≥2 days in the past or rerun later.

## Cross-cutting flags from the CLI host

These program-level `uip` flags appear on every command:

| Flag | Description |
|---|---|
| `--output <table\|json\|yaml\|plain>` | Success/failure envelope format; defaults to `json`. It does not change exported files (`--file-format` controls those). |
| `--output-filter <jmespath>` | Applies a JMESPath query to the envelope; useful for `events`/`sources`, less useful for small `export` envelopes. |
| `--log-level <debug\|info\|warn\|error>` | Logger threshold; logs go to stderr. |
| `--log-file <path>` | Redirects logs from stderr to a file. |
| `--help, -h` | Show help. |

## Error envelope

```json
{
  "Result": "Failure",
  "Message": "Audit export failed for 2026-04-02 (HTTP 504): Gateway Timeout",
  "Instructions": "Ensure you are logged in with 'uip login' and have access to the audit service."
}
```

| `Message` snippet | Likely cause | Fix |
|---|---|---|
| `Not logged in. Run 'uip login' first.` | No cached login state | Run `uip login`. |
| `Tenant ID required for tenant-scoped audit calls.` | Tenant scope lacks a tenant in login context | Add `--tenant-id <guid>` or re-`uip login` selecting a tenant. |
| `HTTP 401 / WWW-Authenticate: Bearer` | Token `aud` lacks `Audit` | Run `uip logout && uip login` to mint a fresh token; `Audit.Read` is in `DEFAULT_SCOPES` post-onboarding. |
| `HTTP 504` on a single export day | Long-term-store query timed out | Rerun the export, or narrow the window. |
| `Audit export failed for YYYY-MM-DD (HTTP 504)` | A single-day chunk failed during a multi-day export | The whole export is rolled back. Rerun, or narrow `--from-date/--to-date` to skip the bad day. |

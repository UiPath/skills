# Audit Investigation Workflow Guide

Drive audit investigations from a natural-language question to a reproducible answer with `uip admin audit`: normally `sources` → `events` → `export`. Assume `uip login` has been run and the active token includes `Audit.Read`. Pass `--output json` to every command.

> **Use `uip admin audit`, never `uip or audit-logs`.** Answer every organization/tenant audit request—including “audit logs”, “export the audit trail”, “login history”, and “who did what”—with `uip admin audit <scope>` (`sources`/`events`/`export`). `uip or audit-logs` is the Orchestrator-operational surface with a different schema; its `--export` produces CSV and belongs to the `uipath-platform` skill. When asked what events or sources exist, run `uip admin audit <scope> sources` and report the live catalog; do not describe it from memory.

## Scope selection

Pick `org` or `tenant` before any audit call; they have different basePaths and event sets.

| User says... | Scope |
|---|---|
| Organization membership, admins, licenses, cross-tenant activity, failed/successful logins, login history, or who has been signing in | **org** — membership, license, tenant lifecycle, Identity Server / IdP authentication including User Login use `/orgaudit_`. |
| Tenant resources or activity: assets, queues, folders, jobs, Action Center, Apps, AgentHub, Document Understanding, Integration Service, Test Manager, Data Fabric, Process Mining, Relay, Hypervisor, or tenant Admin | **tenant** — these use `/{tenantId}/tenantaudit_`. |
| Governance/AOps policies, source control, or pipelines | **org**, despite the AOps name. |
| “Everything everywhere” | **both** — run the flow once per scope and combine results. |

If scope is vague and no previous turn establishes it, stop and ask one yes/no question, with at most two clarifications. Do not assume `tenant` because it is more common.

## Investigation 1 — Who did X to resource Y?

Discover matching source, target, and type IDs; query `events` with those IDs and the time window; report actor and timestamp.

### Step 1 — Discover sources at the correct scope

Route by what changed: Orchestrator entities and tenant-service activity are **tenant**; identity/authentication, membership, licenses, governance policies, and tenant lifecycle are **org**. Run:

```bash
uip admin audit tenant sources --output json > /tmp/sources.json
```

### Step 2 — Locate source, target, and type

Find the broad source in `Data[]`, its entity in `EventTargets[]`, and the verb in `EventTypes[]`. Names come from `event-metadata/definitions/{org,tenant}/*.json`.

Examples:

- Deleted folder: Source `Orchestrator`, Target `Folders`, Type `Delete folder`.
- Edited governance policy: **org**, Source `Governance`, Target `Policy management`, Type `Edited policy`.
- Removed organization user: **org**, Source `Organization Management`, Target `Org Membership`, Type `User Manually Removed From An Org`.
- Created Orchestrator queue/asset/process: **tenant**, Source `Orchestrator`, matching `EventTarget`.

Run these selectors to extract GUIDs:

```bash
jq -r '.Data[] | select(.name == "Orchestrator") | .id' /tmp/sources.json
jq -r '.Data[] | select(.name == "Orchestrator") | .eventTargets[] | select(.name == "Folders") | .id' /tmp/sources.json
jq -r '.Data[] | select(.name == "Orchestrator") | .eventTargets[] | select(.name == "Folders") | .eventTypes[] | select(.name == "Delete folder") | .id' /tmp/sources.json
```

Use the CLI’s lowerCamelCase response fields (`name`, `id`, `eventTargets`, `eventTypes`) in `jq`, not the metadata shape (`Name`, `Id`, `EventTargets`, `EventTypes`).

### Step 3 — Query filtered events

Run:

```bash
uip admin audit tenant events \
  --source <ORCHESTRATOR_SOURCE_GUID> \
  --target <FOLDERS_TARGET_GUID> \
  --type   <DELETE_FOLDER_TYPE_GUID> \
  --from-date   2026-05-11T00:00:00Z \
  --to-date     2026-05-18T00:00:00Z \
  --limit  50 \
  --output json
```

For more than 50 results, increase `--limit`. The CLI paginates internally for `--limit > 200`; each server call is clamped to 200 and the tool follows `previous` automatically. Do not loop on `--from-date`/`--to-date` or chase cursor flags.

### Step 4 — Present matching events

For each `auditEvent` in `Data.auditEvents`, report `createdOn` in UTC; `actorName`, falling back to `actorEmail` or `actorId`; parsed JSON-encoded `eventDetails`, including resource-specific identifying fields; and `status`, translating `0` → `Success` and `1` → `Failure`.

If `Data.previous` is non-null, say: “older results available — extend the window with `--from-date <earlier>` to see more.”

### Step 5 — Report no match safely

A “who did it” query with no matching event means **no such event was found**. State the negative result plainly with scope, source/target/type, and window; offer to widen the window, try the other scope, or check whether the resource existed.

Never identify an actor from an adjacent event, different resource, different type, or broad `--search` hit. Do not broaden filters until something returns and present that as the culprit. Two or three targeted empty queries are a complete investigation; stop and report them. Name an actor only when the cited event matches the requested resource and verb, and quote `createdOn` plus the identifying `eventDetails` field for verification.

## Investigation 2 — Show logins for user X

**Use scope `org`.** Org audit includes Identity Server / IdP authentication (`User Login`, password changes, MFA setup, federation, and SSO bindings), membership, license and billing, tenant lifecycle, org settings, and org-level robot accounts and external apps. Tenant-only activity includes Orchestrator runs, asset/queue/folder edits, Action Center tasks, Apps, AgentHub, Document Understanding, Integration Service, and Test Manager. AOps `Governance`, `Pipelines`, and `Source Control` are org sources.

Audit events store actor identity in top-level indexed fields (`actorId`, `actorName`, `actorEmail`), not in `clientInfo`/`eventDetails`. Resolve `email → actorId` with `uip admin users list --search <email>`; do not use audit `--search <email>`. Audit `--search` scans `ClientInfo` (`ipAddress`/`ipCountry`) and `EventDetails` (such as login `Authentication`), neither of which contains the email.

### Step 1 — Resolve `actorId`

Run:

```bash
uip admin users list \
  --search "jane.doe@example.com" \
  --limit 5 \
  --output json \
  --output-filter "Data[0].id"
```

The Identity Server user-list endpoint searches name/email columns and returns the user GUID, which equals the user’s audit-event `actorId`.

### Step 2 — Find the `User Login` type GUID

Run `org sources`, not `tenant sources`:

```bash
uip admin audit org sources --output json > /tmp/sources.json
jq -r '.Data[] | select(.name == "Identity") | .eventTargets[] | select(.name == "Authentication") | .eventTypes[] | select(.name == "User Login") | .id' /tmp/sources.json
```

The path is `Identity` → `Authentication` → `User Login`, matching `event-metadata/definitions/org/identity.json`. `Robot Login`, `External App Login`, and `User Logout` are adjacent alternatives. If `jq` returns empty, run `.Data[].name` and `.eventTargets[].name` selectors to inspect candidate names; names can vary by region/version.

### Step 3 — Query login events

If the prompt names a user by email, name, or username, **run the events call with `--user-id <GUID>` from Step 1**. A type/date query without it returns every user’s logins and is wrong, not degraded.

Run:

```bash
uip admin audit org events \
  --user-id   <USER_GUID> \
  --type      <USER_LOGIN_TYPE_GUID> \
  --from-date 2026-04-01T00:00:00Z \
  --to-date   2026-04-29T23:59:59Z \
  --limit     200 \
  --output    json
```

For failed logins, run:

```bash
uip admin audit org events \
  --user-id   <USER_GUID> \
  --type      <USER_LOGIN_TYPE_GUID> \
  --status    Failure \
  --from-date 2026-04-01T00:00:00Z \
  --to-date   2026-04-29T23:59:59Z \
  --output    json
```

Only if Identity Server returns 4xx/5xx, the user is not in the org, or the sandbox blocks the call may you omit `--user-id`. Then query by `--type <USER_LOGIN_GUID>` plus dates and post-filter client-side on `actorEmail`/`actorName`; explicitly state that this fallback was used and why, and call the answer approximate.

Use audit `--search` only for data in `clientInfo`/`eventDetails`, such as an IP (`--search "20.200.233.203"`), country code, authentication provider, or session ID. Do not use it for users.

### Step 4 — Present

For each event report `createdOn`, `clientInfo.ipAddress`/`clientInfo.ipCountry` parsed from `clientInfo`, and parsed `eventDetails`, typically including `AuthenticationProvider` and session information.

## Investigation 3 — Give an audit dump for a date range

Run `export` directly unless the user requests a preview. Default `json` writes a folder of day-wise JSON files. Add `--file-format csv` for one merged, spreadsheet-friendly CSV. Pass `--output-path` a base directory; the CLI creates `audit_<from>_<to>_<generated-at>` inside it. Do not hand-craft the generated name.

### Step 1 — Confirm scope and window

If scope is ambiguous, ask once. Compliance reviews typically require both scopes separately.

Resolve relative windows against the actual UTC date. Run `date -u +%F`, `date -u -d 'yesterday' +%F`, or on macOS/BSD `date -u -v-1d +%F`; never guess. Echo resolved bounds. Export bounds are whole UTC days, inclusive: “yesterday” uses the same date for both bounds; “past week” means 7 days ago through yesterday, or today if accepting a possibly lagging trailing day.

If the user specified a destination, pass it verbatim as `--output-path` without confirmation. If not, propose a default such as `./audit-exports` and confirm once.

### Step 2 — Export

Run the applicable command:

```bash
# Tenant scope — most events (default json: a uniquely-named folder of day-wise JSON files under the base dir)
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date   2026-01-31 \
  --output-path ./audit-exports \
  --output json

# Tenant scope as a single merged CSV (flat, Excel-friendly)
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date   2026-01-31 \
  --file-format csv \
  --output-path ./audit-exports \
  --output json

# Org scope — admin events (memberships, license, tenant lifecycle)
uip admin audit org export \
  --from-date 2026-01-01 \
  --to-date   2026-01-31 \
  --output-path ./audit-exports \
  --output json
```

The CLI makes one HTTP call per UTC day and creates `audit_<from>_<to>_<generated-at>` under `--output-path`: `json` creates one JSON file per UTC day; `csv` parses the daily JSON and merges all events into one `.csv`. The result’s `Path` is the generated folder/file and `GeneratedAt` is its timestamp. `Days`/`NonEmptyDays` report requested/non-empty days; `json` reports `Files`; `csv` reports `Events`.

### Step 3 — Verify

For JSON, run:

```bash
ls ./audit-exports/*/        # the generated audit_<from>_<to>_<generatedAt>/ folder
```

Typical layout:

```text
audit-exports/
└── audit_2026-01-01_2026-01-31_20260617T112630/
    ├── 2026-01-01.json
    ├── ...
    └── 2026-01-31.json
```

Each file is a JSON array with LTS-schema keys (`Identifier`, `DateCreatedUtc`, `OrganizationId`, `ActorId`, `User`, `Action`, …), unlike the camelCase live `events` response. Tell downstream users about this difference.

For CSV, run:

```bash
csv=$(ls ./audit-exports/audit_*.csv | head -1)   # the generated audit_<from>_<to>_<generatedAt>.csv
head -1 "$csv"                                      # shared header (LTS-schema columns)
python3 -c "import csv,sys; print(sum(1 for _ in csv.reader(open(sys.argv[1]))) - 1, 'rows')" "$csv"
```

CSV has one header and one row per event; its row count should match `Events`. Both formats use LTS-schema columns. In CSV, `Status` is numeric (`0`/`1`) and `ClientInformation` is a JSON-stringified cell.

Surface these edge cases: nested ZIPs are flattened as `<inner>_<outer>.json`; same-name collisions receive `_<YYYY-MM-DD>`, then `_<YYYY-MM-DD>_2`, `_3`, and so on.

### Step 4 — Hand off

Report the absolute path, total bytes, requested `Days` versus `NonEmptyDays`, and whether the user wants an org export when only tenant scope was requested. If `Days > 365` or the export failed mid-stream, suggest monthly chunks; one bad day in a multi-year export forces a full rerun.

## Investigation 4 — What's happening at org or tenant level?

Run both scopes over a bounded recent window without filters, then summarize event-type frequencies.

### Step 1 — Query recent events

Run:

```bash
uip admin audit org    events --from-date 2026-04-22 --to-date 2026-04-29 --limit 100 --output json > /tmp/org-events.json
uip admin audit tenant events --from-date 2026-04-22 --to-date 2026-04-29 --limit 100 --output json > /tmp/tenant-events.json
```

### Step 2 — Group by event type

Run:

```bash
jq -r '.Data.auditEvents | group_by(.eventType) | map({eventType: .[0].eventType, count: length}) | sort_by(-.count)' /tmp/org-events.json
jq -r '.Data.auditEvents | group_by(.eventType) | map({eventType: .[0].eventType, count: length}) | sort_by(-.count)' /tmp/tenant-events.json
```

### Step 3 — Present

Report the top 5 event types per scope, most active actors grouped by `actorName`, and events per day. For deeper analysis of one type, use Investigation 1’s `--source` and `--type` filtering pattern.

## Choose the investigation

| Intent signal | Investigation |
|---|---|
| “who” / “did” plus a resource verb | **1** — Who did X to Y |
| “logged in” / “login” / “authenticated” / a user email | **2** — Login history |
| “export” / “dump” / “JSON” / “CSV” / date range | **3** — Date-range dump |
| “overview” / “what's happening” / “recent activity” / “audit summary” | **4** — Overview |

If multiple signals appear, run the investigations in sequence and stitch the results together. Do not make the user re-ask.

## Common gotchas

- **Tenant context:** `tenant` commands fail without an active tenant. Re-run `uip login` with a tenant or pass `--tenant-id <guid>` on every call.
- **Pagination:** `next` means newer and is often null; `previous` means older. The CLI follows `previous` automatically for `--limit > 200`; do not reimplement it.
- **Events dates:** date-only ISO strings mean UTC midnight. `--from-date 2026-01-01` means `2026-01-01T00:00:00Z`. To include the full final day, use `--to-date 2026-02-01` as an exclusive next day or `--to-date 2026-01-31T23:59:59.999Z`.
- **Export dates:** bounds are inclusive whole UTC days. January is `--from-date 2026-01-01 --to-date 2026-01-31`; a single day uses the same date for both. Do not use the events next-day convention for exports.
- **Export lag:** the long-term store typically lags live `events` by up to 24–48 hours. Recent trailing days may be empty; offer to rerun later or end the window 2 days earlier when completeness matters.
- **Relative dates:** resolve them with `date -u +%F`, `date -u -d 'yesterday' +%F`, or macOS/BSD `date -u -v-1d +%F`, and echo the window.
- **Export schema:** default `json` writes one `<YYYY-MM-DD>.json` per UTC day in a generated folder; `--file-format csv` writes one merged CSV with the same LTS-schema field names. Both differ from live camelCase `events`; do not feed exports to a live-shape parser.
- **Source GUIDs:** org and tenant catalogs differ. Never reuse an `org sources` GUID in a `tenant events` query; it may silently match nothing.

## Output etiquette — after every audit query or export

Before waiting for a next-step choice, report:

1. **Operation and result:** for example, `Found 47 audit events on tenant T in the last 7 days`, `Wrote 27 JSON files (123,456 bytes) to /path/to/audit-jan/ (31 days, 27 non-empty)`, or `Wrote 98,765 bytes to /path/to/audit.csv (1,234 events across 31 days, 27 non-empty)`.
2. **Scope:** `org` or `tenant`, including any `--tenant-id` override.
3. **Time window:** explicit ISO bounds, including bounds resolved from relative language.
4. **Filters:** sources, types, users, and status.
5. **Cursor state:** for `events`, state whether `Data.previous` is null (start of audit history) or populated (older results available; rerun with a larger `--limit`).
6. **Next step:** ask whether to widen the window, export the slice, or filter by a user. Wait for the user’s choice unless the original request already asked for the follow-on sequence; complete that sequence before handing off. These are read-only queries, so do not pause to reconfirm already-requested work.

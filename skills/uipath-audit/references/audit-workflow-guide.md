# Audit Investigation Workflow Guide

Four canonical investigations the `uipath-audit` skill should drive. Each starts from a natural-language question and produces a reproducible answer using `uip admin audit` — typically `sources` (discover) → `events` (filter) → `export` (capture).

> Every command below assumes the user has run `uip login` and the active token includes the `Audit.Read` scope. Every command should pass `--output json` so the agent can parse the envelope.

---

## Investigation 1 — "Who did X to resource Y?"

**User asks:** "Who deleted the `Sales-Reports` folder last Tuesday?" / "Who edited the AI Trust Layer policy this week?" / "Who turned off MFA for the org admin group?"

**Approach:** Discover the source/target IDs that match the resource, narrow `events` by source + target + time window, then format actor + timestamp.

### Step 1 — Discover sources at the right scope

The "what changed" determines scope. Folder/queue/asset edits are **tenant** scope. Membership/license/tenant-lifecycle is **org** scope. Most resource-touching investigations are tenant.

```bash
uip admin audit tenant sources --output json > /tmp/sources.json
```

### Step 2 — Locate the matching source/target

Find a source whose `name` matches the resource type, then drill into its `eventTargets[]` for the specific entity type, and `eventTypes[]` for the verb.

For "deleted folder":

- Source: `Folders` (or similar)
- Target: `Folder`
- Type: `Deleted folder`

The agent should grep the JSON for these names to extract the GUIDs:

```bash
jq -r '.Data[] | select(.name == "Folders") | .id' /tmp/sources.json
jq -r '.Data[] | select(.name == "Folders") | .eventTargets[] | select(.name == "Folder") | .id' /tmp/sources.json
```

### Step 3 — Query events with filters

```bash
uip admin audit tenant events \
  --source <FOLDERS_SOURCE_GUID> \
  --target <FOLDER_TARGET_GUID> \
  --type   <DELETED_FOLDER_TYPE_GUID> \
  --from-date   2026-04-22T00:00:00Z \
  --to-date     2026-04-29T00:00:00Z \
  --limit  50 \
  --output json
```

### Step 4 — Present

For each `auditEvent` in `Data.auditEvents`, surface:

- `createdOn` (UTC)
- `actorName` (fall back to `actorEmail` or `actorId`)
- `eventDetails` — parse the JSON-encoded string for the resource-specific fields (e.g., folder name)
- `status` — translate `0`→`Success`, `1`→`Failure`

If `Data.previous` is non-null, mention "older results available — extend the window with `--from-date <earlier>` to see more."

---

## Investigation 2 — "Show me logins for user X"

**User asks:** "Show me failed logins for jane.doe@example.com this month." / "When did Bob last log in?" / "Was anyone logging in from outside the US last week?"

**Approach:** Filter events by user ID + the `User Login` event type, optionally with `--status Failure`. Present chronologically with `ipAddress`/`ipCountry` from `clientInfo`.

### Step 1 — Find the user's GUID

The user's `actorId` GUID is required by `--user-id`. It's not visible from email alone. Two ways:

1. If the user has at least one prior audit event you've already loaded, grab `actorId` from there.
2. Otherwise, run a search-only query (no `--user-id`) for `--search jane.doe` and take `actorId` from the first match.

```bash
uip admin audit tenant events \
  --search "jane.doe@example.com" \
  --limit 5 --output json --output-filter "Data.auditEvents[0].actorId"
```

### Step 2 — Find the User Login type GUID

```bash
jq -r '.Data[] | select(.name == "Identity") | .eventTargets[] | select(.name == "Authentication") | .eventTypes[] | select(.name == "User Login") | .id' /tmp/sources.json
```

### Step 3 — Query

For "all logins this month":

```bash
uip admin audit tenant events \
  --user-id <USER_GUID> \
  --type    <USER_LOGIN_TYPE_GUID> \
  --from-date    2026-04-01T00:00:00Z \
  --to-date      2026-04-29T23:59:59Z \
  --limit   200 \
  --output  json
```

For "failed logins only":

```bash
uip admin audit tenant events \
  --user-id <USER_GUID> \
  --type    <USER_LOGIN_TYPE_GUID> \
  --status  Failure \
  --from-date    2026-04-01T00:00:00Z \
  --to-date      2026-04-29T23:59:59Z \
  --output  json
```

### Step 4 — Present

For each event:

- `createdOn`
- `clientInfo.ipAddress` / `clientInfo.ipCountry` (parse from `clientInfo` field)
- `eventDetails` — typically contains `AuthenticationProvider` and session info

---

## Investigation 3 — "Give me an audit dump for January"

**User asks:** "Export everything for compliance for Q4." / "I need the full audit log for January for the security review." / "Pull last month's events for tenant X as a ZIP."

**Approach:** `export` straight to a ZIP. No need to query `events` first unless the user wants a preview.

### Step 1 — Confirm scope and window

If the user is ambiguous about scope, ask once. For compliance reviews, **both** scopes are typically needed (separately).

### Step 2 — Export

```bash
# Tenant scope — most events
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date   2026-02-01 \
  --output-file ./audit-tenant-2026-01.zip \
  --output json

# Org scope — admin events (memberships, license, tenant lifecycle)
uip admin audit org export \
  --from-date 2026-01-01 \
  --to-date   2026-02-01 \
  --output-file ./audit-org-2026-01.zip \
  --output json
```

The CLI issues one HTTP call per UTC day under the hood and aggregates daily responses into a flat ZIP. `Days` and `NonEmptyDays` in the result tell you how many calendar days had events.

### Step 3 — Verify the ZIP

```bash
unzip -l ./audit-tenant-2026-01.zip
```

Expected layout:

```
audit-tenant-2026-01.zip
├── 2026-01-01.txt
├── 2026-01-02.txt
├── ...
└── 2026-01-31.txt
```

Each `.txt` is a JSON array of audit events with **PascalCase** keys (`Id`, `CreatedOn`, `OrganizationId`, `ActorId`, `ActorName`, `EventType`, …) — different from the camelCase shape returned by the live `events` endpoint. Note this in the user's hand-off if they're going to feed the dump into other tooling.

### Step 4 — Hand off

Report:

- The absolute path written
- Total bytes
- `Days` requested vs `NonEmptyDays`
- Whether the user wants the agent to also run an org export (if they only asked for tenant)

If `Days > 365` or the export failed mid-stream, suggest narrowing to monthly chunks: the daily-chunked downloader is robust to multi-month windows but a single bad day in a multi-year export forces a full re-run.

---

## Investigation 4 — "What's been happening at the org / tenant level?"

**User asks:** "Show me the most recent admin activity in our org." / "What's happened on tenant T this past week?" / "I'm new — give me the audit history overview."

**Approach:** Run both scopes, fetch a bounded recent window with no filters, summarize event-type frequencies.

### Step 1 — Recent events at each scope

```bash
uip admin audit org    events --from-date 2026-04-22 --to-date 2026-04-29 --limit 100 --output json > /tmp/org-events.json
uip admin audit tenant events --from-date 2026-04-22 --to-date 2026-04-29 --limit 100 --output json > /tmp/tenant-events.json
```

### Step 2 — Group by event type/source

```bash
jq -r '.Data.auditEvents | group_by(.eventType) | map({eventType: .[0].eventType, count: length}) | sort_by(-.count)' /tmp/org-events.json
jq -r '.Data.auditEvents | group_by(.eventType) | map({eventType: .[0].eventType, count: length}) | sort_by(-.count)' /tmp/tenant-events.json
```

### Step 3 — Present

- Top 5 event types per scope
- Most active actors (group by `actorName`)
- Time distribution (events per day)

If the user wants more depth on any one event type, drill in with Investigation 1's pattern (filter by `--source` and `--type`).

---

## Picking the right investigation

| User intent signal | Investigation |
|---|---|
| "who" / "did" + a verb on a resource | **1** — Who did X to Y |
| "logged in" / "login" / "authenticated" / a user's email | **2** — Login history |
| "export" / "dump" / "ZIP" / "CSV" / a date range | **3** — Date-range dump |
| "overview" / "what's happening" / "recent activity" / "audit summary" | **4** — Overview |

Two or more signals? Run them in sequence and stitch the results in the final report. Don't make the user re-ask.

## Common gotchas

- **`tenant` events without an active tenant fail loudly.** If `uip login` has no tenant selected, every tenant-scoped command throws. Either re-`uip login` and pick a tenant, or pass `--tenant-id <guid>` on every call.
- **`events` cursor pagination is chronologically reversed from intuition.** `next` = newer (often null), `previous` = older (the typical "load more"). The CLI tool follows `previous` automatically when you bump `--limit > 200` — don't re-implement this in the agent.
- **Date-only ISO strings are interpreted as UTC midnight.** `--from-date 2026-01-01` means `2026-01-01T00:00:00Z`. To capture the full final day in `--to-date`, use `2026-02-01` (exclusive next day) or `2026-01-31T23:59:59.999Z`.
- **The export ZIP's per-day files are JSON, not CSV, and use PascalCase keys.** Different from the camelCase live `events` endpoint. Don't paste an export directly into a parser expecting the live shape.
- **Org sources and tenant sources are different sets.** Don't reuse a GUID from `org sources` in a `tenant events` query — the filter will silently match nothing.

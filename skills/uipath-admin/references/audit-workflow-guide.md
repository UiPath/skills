# Audit Investigation Workflow Guide

Four canonical investigations the `uipath-audit` skill should drive. Each starts from a natural-language question and produces a reproducible answer using `uip admin audit` — typically `sources` (discover) → `events` (filter) → `export` (capture).

> Every command below assumes the user has run `uip login` and the active token includes the `Audit.Read` scope. Every command should pass `--output json` so the agent can parse the envelope.

---

## Investigation 1 — "Who did X to resource Y?"

**User asks:** "Who deleted the `Sales-Reports` folder last Tuesday?" / "Who edited the production governance policy this week?" / "Who removed jane.doe from the organization yesterday?"

**Approach:** Discover the source/target IDs that match the resource, narrow `events` by source + target + time window, then format actor + timestamp.

### Step 1 — Discover sources at the right scope

The "what changed" determines scope. Orchestrator-managed entities (folders, queues, assets, processes) and tenant-service activity (Action Center, Apps, Document Understanding, Integration Service, Test Manager, Data Fabric) are **tenant** scope. Identity / authentication, org membership, license, governance policies, and tenant lifecycle are **org** scope.

```bash
uip admin audit tenant sources --output json > /tmp/sources.json
```

### Step 2 — Locate the matching source/target

Find a source whose `Name` matches the broad product area, then drill into its `EventTargets[]` for the specific entity type, and `EventTypes[]` for the verb. Names come straight from the `event-metadata/definitions/{org,tenant}/*.json` set published by the Audit Service.

For "deleted folder" (tenant scope):

- Source: `Orchestrator`
- Target: `Folders`
- Type: `Delete folder`

Other realistic mappings to keep in mind:

- "edited a governance policy" → **org** scope, Source `Governance`, Target `Policy management`, Type `Edited policy`
- "removed a user from the org" → **org** scope, Source `Organization Management`, Target `Org Membership`, Type `User Manually Removed From An Org`
- "created an Orchestrator queue/asset/process" → **tenant** scope, Source `Orchestrator`, with the matching `EventTarget`

The agent should grep the JSON for these names to extract the GUIDs:

```bash
jq -r '.Data[] | select(.name == "Orchestrator") | .id' /tmp/sources.json
jq -r '.Data[] | select(.name == "Orchestrator") | .eventTargets[] | select(.name == "Folders") | .id' /tmp/sources.json
jq -r '.Data[] | select(.name == "Orchestrator") | .eventTargets[] | select(.name == "Folders") | .eventTypes[] | select(.name == "Delete folder") | .id' /tmp/sources.json
```

> The CLI returns lowerCamelCase keys (`name`, `id`, `eventTargets`, `eventTypes`) over the `Name`/`Id`/`EventTargets`/`EventTypes` shape in the metadata JSON. Use lowerCamelCase in `jq` selectors against the CLI response.

### Step 3 — Query events with filters

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

> **Need more than 50 results?** Bump `--limit` directly — the CLI paginates internally for `--limit > 200` (server clamps each individual call to 200; the tool follows `previous` automatically). Do **not** loop on `--from-date` / `--to-date` or chase cursor flags from the agent.

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

**Scope: `org`.** Org-level audit events are everything that's not scoped to a single tenant — anything emitted by services that operate at the organization or cross-tenant level. The broad categories live under `/orgaudit_`:

- **Identity Server / IdP authentication** — `User Login`, password changes, MFA setup, federation events, SSO bindings
- **Membership** — users joining/leaving the org, role assignments, invitations, group changes at org scope
- **License & billing** — license assignments, plan changes, seat allocation, billing events
- **Tenant lifecycle** — tenant create/suspend/delete/restore, region moves
- **Org settings** — admin role changes, branding/identity provider settings, org-wide policy changes
- **Robot accounts & external apps** — when managed at org level (vs tenant-bound)

If the user's question maps to anything in those categories — and `User Login` does — query `org` scope. Anything scoped to a single tenant (Orchestrator runs, asset/queue/folder edits, Action Center task changes, Apps / AgentHub / Document Understanding / Integration Service / Test Manager activity) is `tenant` scope instead. Querying `tenant events` for org-level events returns nothing useful because the events don't live under `/{tenantId}/tenantaudit_`. Note that **AOps governance policies, pipelines, and source control are org-scoped** despite the AOps naming — `Governance`, `Pipelines`, and `Source Control` are sources in `org sources`, not tenant.

**Approach:** Audit events store actor identity in indexed top-level columns (`actorId`, `actorName`, `actorEmail`), not inside `clientInfo`/`eventDetails`. So filter by `--user-id <GUID>`, not by `--search <email>` — the audit-events `--search` flag is a `contains` scan over `ClientInfo` (which holds `ipAddress`/`ipCountry`) and `EventDetails` (which holds event-type-specific payload like `Authentication` provider for logins). Neither contains the email, so searching for an email returns zero login events.

To resolve `email → actorId`, use the **Identity Server** (`uip admin users list --search <email>`), not the audit API. The user-list endpoint searches the proper user-name/email columns and returns the GUID you plug into `--user-id`.

### Step 1 — Resolve the user's `actorId`

```bash
uip admin users list \
  --search "jane.doe@example.com" \
  --limit 5 \
  --output json \
  --output-filter "Data[0].id"
```

`uip admin users list --search` matches against the Identity Server's name/email columns (different from audit's `--search`, which is what you want for this lookup). The returned `id` is the user GUID — identical to the `actorId` you'll see in audit events for that user.

### Step 2 — Find the User Login type GUID

Discover from `org sources` (not tenant — login event metadata lives org-side):

```bash
uip admin audit org sources --output json > /tmp/sources.json
jq -r '.Data[] | select(.name == "Identity") | .eventTargets[] | select(.name == "Authentication") | .eventTypes[] | select(.name == "User Login") | .id' /tmp/sources.json
```

The `Identity` → `Authentication` → `User Login` path matches the Audit Service event metadata (`event-metadata/definitions/org/identity.json`). Adjacent types under the same target — `Robot Login`, `External App Login`, `User Logout` — work the same way and are useful when the question is about non-user sign-ins. If `jq` returns empty, list the candidate names with `jq -r '.Data[].name'` and `.eventTargets[].name` and pick the closest match (names can drift across cloud regions/versions).

### Step 3 — Query

For "all logins for jane.doe@example.com this month":

```bash
uip admin audit org events \
  --user-id   <USER_GUID> \
  --type      <USER_LOGIN_TYPE_GUID> \
  --from-date 2026-04-01T00:00:00Z \
  --to-date   2026-04-29T23:59:59Z \
  --limit     200 \
  --output    json
```

For "failed logins only" add `--status Failure`:

```bash
uip admin audit org events \
  --user-id   <USER_GUID> \
  --type      <USER_LOGIN_TYPE_GUID> \
  --status    Failure \
  --from-date 2026-04-01T00:00:00Z \
  --to-date   2026-04-29T23:59:59Z \
  --output    json
```

If Step 1 fails (Identity Server unreachable, user not in this org), you can still bound the query by `--type <USER_LOGIN_GUID>` + date range and post-filter the result client-side by `actorEmail` — slower than `--user-id` but works without the lookup.

When to use audit `--search` instead: useful when filtering by something that *does* live in `clientInfo`/`eventDetails` — e.g., a specific IP address (`--search "20.200.233.203"`), country code, authentication provider name, or session ID. Not useful for users.

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

Typical layout (one entry per UTC day with events):

```
audit-tenant-2026-01.zip
├── 2026-01-01.txt
├── 2026-01-02.txt
├── ...
└── 2026-01-31.txt
```

Each `.txt` is a JSON array of audit events with **PascalCase** keys (`Id`, `CreatedOn`, `OrganizationId`, `ActorId`, `ActorName`, `EventType`, …) — different from the camelCase shape returned by the live `events` endpoint. Note this in the user's hand-off if they're going to feed the dump into other tooling.

Edge cases the CLI handles automatically — surface in your hand-off only if they appear:

- **Nested ZIPs**: when a single day's response is itself a ZIP-of-ZIPs, inner files are renamed `<inner>_<outer>.txt` rather than collapsed.
- **Same-name collisions**: duplicate basenames across days get an `_<YYYY-MM-DD>` suffix (and `_<YYYY-MM-DD>_2`, `_3`, … if needed) to keep entries unique.

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

# Agent Workflow

Follow these steps in order when interacting with an external service.

## Progress Checklist

```
- [ ] Step 1: Find connector (get Key)
- [ ] Step 2: Find connection (get Id — present options, recommend default)
- [ ] Step 3: Ping connection (confirm Enabled)
- [ ] Step 4: Discover capabilities (activities first, then resources)
- [ ] Step 4T: (Triggers only) Get trigger objects → get trigger metadata
- [ ] Step 5: Resolve reference fields (if any)
- [ ] Step 5a: Validate all required fields have values
- [ ] Step 6: Execute operation
```

## Step 1: Find the Connector

Run:

```bash
uip is connectors list --filter "<vendor>" --output json
```

Use the native connector's **`Key`**. If none exists, use `uipath-uipath-http`; see [connectors.md — HTTP Connector Fallback](connectors.md#http-connector-fallback).

## Step 2: Find a Connection

Run:

```bash
uip is connections list "<connector-key>" --output json
```

Present options by name, never UUID. Show `Name`, `Owner`, `Folder`, `State`, and `IsDefault`; never show `Id` or `FolderKey`. Recommend the default enabled connection (`IsDefault: Yes`, `State: Enabled`), but require confirmation or another choice; never auto-select, even when there is exactly one default enabled connection. Say: "I found connection **<Name>** by <Owner> in **<Folder>** folder (default, enabled). Should I use this one?"

For HTTP fallback, match connections by vendor **Name** using a case-insensitive substring and present matches. If none exist, ask the user to create one via `is connections create "<connector-key>"`.

See [connections.md — Selecting a Connection](connections.md#selecting-a-connection).

## Step 3: Ping the Connection

Run:

```bash
uip is connections ping "<connection-id>" --output json
```

If the result is `Enabled`, proceed. If it fails, run `is connections edit <id>` to re-authenticate and ping again. If it still fails, ask the user to choose another connection or create one.

## Step 4: Discover Capabilities

### 4a. Check activities first

Run:

```bash
uip is activities list "<connector-key>" --output json
```

Use a matching activity that directly accomplishes the task; see [activities.md](activities.md). Otherwise continue to resources.

### 4b. List resources

If no activity matches, run this with both `--connection-id` and `--operation`:

```bash
uip is resources list "<connector-key>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --output json
```

### 4c. Describe the target resource

Run:

```bash
uip is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --output json
```

For reduced output, run:

```bash
uip is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --output json
```

Always use `--operation` for field detail: without it, the result only lists `availableOperations`; with it, the result includes `requestFields`, `responseFields`, and `parameters`. Always pass `--connection-id` for connection-specific metadata, including custom fields. Results are cached locally.

If the result has `requestFields` + `responseFields` + `parameters`, check `required` flags and `reference` sections, then proceed to Step 5. If it only has `availableOperations`, choose the needed operation and rerun with `--operation`. If it errors or is empty, treat it as a **metadata gap**, skip describe, and proceed to Step 5 with inferred fields; see [resources.md — Describe Failures](resources.md#describe-failures).

## Step 4T: Trigger Metadata (if trigger workflow)

For event-trigger configuration, discover trigger metadata instead of or in addition to CRUD resources.

### 4T-a. List trigger activities

Run:

```bash
uip is activities list "<connector-key>" --triggers --output json
```

Present trigger activities and their **Operation** (for example, CREATED, UPDATED, DELETED). If none are found, inform the user that the connector does not support events.

### 4T-b. Get trigger objects

For CREATED/UPDATED/DELETED operations, run:

```bash
uip is triggers objects "<connector-key>" "<OPERATION>" \
  --connection-id "<id>" --output json
```

Present the objects and let the user choose. If none are returned, verify that the operation is uppercase (CREATED/UPDATED/DELETED) and check the connector's `hasEvents`.

### 4T-c. Get trigger metadata

For the selected object, run:

```bash
uip is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" \
  --connection-id "<id>" --output json
```

For non-CRUD trigger operations, skip 4T-b, use the activity's `ObjectName` as `<object-name>`, and run 4T-c directly.

See [triggers.md](triggers.md) for the trigger domain reference and response fields.

## Step 5: Resolve Reference Fields

When describe succeeds, check for reference fields. If none exist, skip to Step 5a. For each reference field, list the referenced object, collect valid IDs, and present options to the user.

When describe is unavailable, infer references from the request: fields ending in `Id` (for example, `PromotionId`) typically reference the object with the matching base name (`Promotion`). List that object and resolve its ID before executing.

See [reference-resolution.md — Reference Fields](reference-resolution.md#reference-fields-critical) and [reference-resolution.md — Field Dependency Chains](reference-resolution.md#field-dependency-chains).

## Step 5a: Validate Required Fields

After resolving references, check every required field against the user's values. This is a hard gate: do not execute until all required fields have values. Ask the user for missing values.

See [reference-resolution.md — Validate Required Fields Before Executing](reference-resolution.md#validate-required-fields-before-executing).

## Step 6: Execute

Run:

```bash
uip is resources run <verb> "<connector-key>" "<object>" \
  --connection-id "<id>" --body '{"field": "value"}' --output json
```

See [resources.md — Execute Operations](resources.md#execute-operations) for the verb table and options.

### Pagination (list operations)

Check `Data.Pagination.HasMore` / `NextPageToken`. If more results exist, paginate with `--query "nextPage=<token>"`; stop early on a match. See [resources.md#pagination](resources.md#pagination) for the full protocol, anti-patterns, and offset/limit fallback.

## Error Recovery

When Step 6 returns a `Failure`, read the HTTP status in `Message` and the raw vendor error body in `Instructions`; do not retry blindly or give up.

### Recovery Loop

```
Execute → Success? → Done
  ↓ Failure
Step 6a: Read the failure response
  - Message — HTTP status (e.g., "400 Bad Request")
  - Instructions — raw vendor error body (WHAT failed)
  ↓
Step 6b: Diagnose using discovery
  - Field not found → run `is resources describe --operation <op>` to get valid field names
  - Invalid value → run `is resources run list` on the referenced object to get valid values
  - Vendor 400 "X is required" but `describe` marked X `required=False` → IS schema and vendor validators disagree; treat vendor as authoritative, list the parent resource and add the missing field (e.g., Jira project-level required `components_arrayRemap_name` is `required=False` in `describe`)
  - Auth error → run `is connections edit <id>` to re-authenticate, then ping again
  - Scope error → inform user, connection needs broader permissions
  - Read-only field → remove the field from `--body` and retry
  ↓
Step 6c: Correct and retry (max 2 retries)
  - Apply the specific fix from 6b
  - Re-execute with the corrected query/body
  - If still failing after 2 retries → present the error, attempted fixes, and suggested manual fix to the user
```

### Rules

1. **Max 2 semantic retries** — each retry must address a specific diagnosed issue; never retry blindly.
2. **Never retry the same query unchanged** — if no fix can be identified, escalate to the user.
3. **Discover before guessing** — use `describe` and `list` to find correct field names and values; do not hallucinate.
4. **Escalate with context** — show the original query, error message, attempted fixes, and suggested manual fix.
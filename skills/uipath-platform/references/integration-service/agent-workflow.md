# Agent Workflow

Follow these steps in order when the user asks to interact with an external service.

## Contents
- Progress Checklist
- Step 1: Find the Connector
- Step 2: Find a Connection
- Step 3: Ping the Connection
- Step 4: Discover Capabilities
- Step 4T: Trigger Metadata (if trigger workflow)
- Step 5: Resolve Reference Fields
- Step 5a: Validate Required Fields
- Step 6: Execute
- Error Recovery
- Happy-Path Example (CRUD)
- Happy-Path Example (Triggers)

## Progress Checklist

Copy and track progress:

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

```bash
uip is connectors list --filter "<vendor>" --output json
```

| Outcome | Action |
|---|---|
| Native connector found | Use its **`Key`**. Proceed to Step 2. |
| Not found | Fall back to HTTP connector (`uipath-uipath-http`). See [connectors.md — HTTP Connector Fallback](connectors.md#http-connector-fallback). |

## Step 2: Find a Connection

```bash
uip is connections list "<connector-key>" --output json
```

- **Always present options** to the user. Recommend the default enabled connection (`IsDefault: Yes`, `State: Enabled`) but let the user confirm or choose another.
- **HTTP fallback**: Match connection by vendor **Name** (case-insensitive substring). Present matches to user.
- **None**: Ask user to create via `is connections create "<connector-key>"`.

> **Do NOT auto-select a connection silently.** Even if there is exactly one default enabled connection, present it to the user: "I found connection **<name>** (default, enabled). Should I use this one?"

See [connections.md — Selecting a Connection](connections.md#selecting-a-connection) for full selection logic.

## Step 3: Ping the Connection

```bash
uip is connections ping "<connection-id>" --output json
```

| Result | Action |
|---|---|
| `Enabled` | Healthy. Proceed to Step 4. |
| Fails | Run `is connections edit <id>` to re-authenticate, then ping again. If still fails, ask user to choose another or create new. |

## Step 4: Discover Capabilities

**4a. Check activities first** — activities are pre-built actions (e.g., "Send Email", "Create Invoice") that may directly accomplish the task:

```bash
uip is activities list "<connector-key>" --output json
```

| Outcome | Action |
|---|---|
| Matching activity found for the user's task | Use the activity. See [activities.md](activities.md) for details. |
| No matching activity | Proceed to Step 4b (resources). |

**4b. List resources** — if no activity matches, discover CRUD-capable objects. **Always pass `--connection-id`** to include custom objects, and **`--operation`** to filter to the intended action:

```bash
uip is resources list "<connector-key>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --output json
```

**4c. Describe the target resource** — get field metadata for the matched object:

```bash
# All operations + all fields
uip is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --output json

# Filter to a single operation (reduces output size)
uip is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --output json
```

Without `--operation`, returns a list of `availableOperations` with a hint to use `--operation`. With `--operation`, returns per-operation detail: `requestFields` (what to send), `responseFields` (what comes back), and `parameters` (path/query params). Results are cached locally — subsequent calls for the same object are instant.

> **Always use `--operation`** to get field-level detail (e.g., `--operation Create`). Without it you only see which operations exist.

| Describe outcome | Action |
|---|---|
| Returns `requestFields` + `responseFields` + `parameters` | Use field metadata. Check `required` flags and `reference` sections. Proceed to Step 5. |
| Returns `availableOperations` (no `--operation`) | Pick the operation you need, re-run with `--operation`. |
| Returns error or empty | **Metadata gap** — skip describe, proceed to Step 5 with inferred fields. See [resources.md — Describe Failures](resources.md#describe-failures). |

**Always pass `--connection-id`** for connection-specific metadata including custom fields.

## Step 4T: Trigger Metadata (if user needs trigger/event configuration)

If the user's task involves **event triggers** (e.g., "when a record is created", "listen for updates"), discover trigger metadata instead of (or in addition to) CRUD resources.

**4T-a. List trigger activities** to see what events the connector supports:

```bash
uip is activities list "<connector-key>" --triggers --output json
```

Present trigger activities to the user. Note the **Operation** field (e.g., CREATED, UPDATED, DELETED).

**4T-b. For CREATED/UPDATED/DELETED operations** — get available trigger objects:

```bash
uip is triggers objects "<connector-key>" "<OPERATION>" \
  --connection-id "<id>" --output json
```

Present objects to the user and let them choose.

**4T-c. Get trigger field metadata** for the selected object:

```bash
uip is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" \
  --connection-id "<id>" --output json
```

**4T-d. For non-CRUD trigger operations** — skip 4T-b. Use the activity's **ObjectName** as the `<object-name>` and go directly to 4T-c.

| Trigger outcome | Action |
|---|---|
| Trigger activities found | Present to user, proceed to 4T-b or 4T-c based on operation type |
| No trigger activities | Connector doesn't support events. Inform user. |
| No objects for operation | Verify operation name is uppercase (CREATED/UPDATED/DELETED). Check connector `hasEvents`. |

See [triggers.md](triggers.md) for full trigger domain reference and response fields.

## Step 5: Resolve Reference Fields

**When describe succeeded:** Check output for reference fields. If none exist, skip to Step 5a. For each reference field: list the referenced object, collect valid IDs, and present options to the user.

**When describe was unavailable (metadata gap):** Infer references from the user's request — fields ending in `Id` (e.g., `PromotionId`) typically reference the object with the matching base name (`Promotion`). List that object to resolve the ID before executing.

See [reference-resolution.md — Reference Fields](reference-resolution.md#reference-fields-critical) and [reference-resolution.md — Field Dependency Chains](reference-resolution.md#field-dependency-chains).

## Step 5a: Validate Required Fields

After resolving references, **check every required field** against what the user provided. This is a hard gate — do NOT execute until all required fields have values. If any are missing, ask the user.

See [reference-resolution.md — Validate Required Fields Before Executing](reference-resolution.md#validate-required-fields-before-executing).

## Step 6: Execute

```bash
uip is resources execute <verb> "<connector-key>" "<object>" \
  --connection-id "<id>" --body '{"field": "value"}' --output json
```

See [resources.md — Execute Operations](resources.md#execute-operations) for the verb table and options.

### Pagination (list operations)

`execute list` may not return all results. **Always check `Data.Pagination`** in the response:

```bash
# First page
uip is resources execute list "<connector-key>" "<object>" \
  --connection-id "<id>" --output json
# → Check Data.Pagination.HasMore and Data.Pagination.NextPageToken

# Next page — use nextPage (NOT nextPageToken) as the query param name
uip is resources execute list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "nextPage=<value-from-NextPageToken>" --output json
# → Continue until HasMore is "false" or target item is found
```

**Stop early** if you find the target item. See [resources.md — Pagination](resources.md#pagination) for full details.

---

## Error Recovery

When Step 6 returns a `Failure` result, follow this loop instead of retrying blindly or giving up. The CLI returns the HTTP status in `Message` and the raw vendor error body in `Instructions`.

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
  - Invalid value → run `is resources execute list` on the referenced object to get valid values
  - Auth error → run `is connections edit <id>` to re-authenticate, then ping again
  - Scope error → inform user, connection needs broader permissions
  - Read-only field → remove the field from --body and retry
  ↓
Step 6c: Correct and retry (max 2 retries)
  - Apply the specific fix from 6b
  - Re-execute with the corrected query/body
  - If still failing after 2 retries → present the error, attempted fixes, and suggested manual fix to the user
```

### Rules

1. **Max 2 semantic retries** — each retry must address a specific diagnosed issue. Not blind retries.
2. **Never retry the same query unchanged** — if you can't identify what to fix, escalate to the user.
3. **Discover before guessing** — use `describe` and `list` to find correct field names and values. Do not hallucinate.
4. **Escalate with context** — when presenting to the user, show: original query, error message, what was tried, and the suggested manual fix.

---

## Happy-Path Example (CRUD)

```bash
# 1. Find connector
uip is connectors list --filter "salesforce" --output json
# → Key: "uipath-salesforce-sfdc"

# 2. Find connection
uip is connections list "uipath-salesforce-sfdc" --output json
# → Id: "abc-123", IsDefault: Yes, State: Enabled

# 3. Ping
uip is connections ping "abc-123" --output json
# → Status: Enabled

# 4a. Check activities first
uip is activities list "uipath-salesforce-sfdc" --output json
# → No matching activity for "create contact" → fall back to resources

# 4b. List resources with operation
uip is resources list "uipath-salesforce-sfdc" \
  --connection-id "abc-123" --operation Create --output json
# → includes "Contact"

# 4c. Describe the target resource
uip is resources describe "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --operation Create --output json
# → requestFields: [{name: "LastName", required: true}, {name: "FirstName", required: false}, ...]
# → responseFields: [{name: "Id"}, {name: "LastName"}, ...]

# 5. No reference fields (no fields with "reference" section) → skip resolution
# 5a. All required fields (LastName) have values → proceed

# 6. Execute
uip is resources execute create "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --body '{"LastName": "Doe", "FirstName": "Jane"}' --output json
```

---

## Happy-Path Example (Triggers)

```bash
# 1. Find connector
uip is connectors list --filter "salesforce" --output json
# → Key: "uipath-salesforce-sfdc"

# 2. Find connection
uip is connections list "uipath-salesforce-sfdc" --output json
# → Id: "228624", IsDefault: Yes, State: Enabled

# 3. Ping
uip is connections ping "228624" --output json
# → Status: Enabled

# 4T-a. List trigger activities
uip is activities list "uipath-salesforce-sfdc" --triggers --output json
# → Trigger activities with Operation: CREATED, UPDATED, DELETED

# 4T-b. Get objects for CREATED operation
uip is triggers objects "uipath-salesforce-sfdc" CREATED \
  --connection-id "228624" --output json
# → [AccountHistory, Contact, Lead, ...]
# → User picks "AccountHistory"

# 4T-c. Get trigger metadata (fields) for AccountHistory
uip is triggers describe "uipath-salesforce-sfdc" CREATED "AccountHistory" \
  --connection-id "228624" --output json
# → Returns eventParameters, filterFields, outputFields
```

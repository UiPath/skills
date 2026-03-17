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
- Step 6: Execute
- Happy-Path Example (CRUD)
- Happy-Path Example (Triggers)

## Progress Checklist

Copy and track progress:

```
- [ ] Step 1: Find connector (get Key)
- [ ] Step 2: Find connection (get Id)
- [ ] Step 3: Ping connection (confirm Enabled)
- [ ] Step 4: Discover capabilities (activities first, then resources)
- [ ] Step 4T: (Triggers only) Get trigger objects → get trigger metadata
- [ ] Step 5: Resolve reference fields (if any)
- [ ] Step 6: Execute operation
```

## Step 1: Find the Connector

```bash
uipcli is connectors list --filter "<vendor>" --format json
```

| Outcome | Action |
|---|---|
| Native connector found | Use its **`Key`**. Proceed to Step 2. |
| Not found | Fall back to HTTP connector (`uipath-uipath-http`). See [connectors.md — HTTP Connector Fallback](connectors.md#http-connector-fallback). |

## Step 2: Find a Connection

```bash
uipcli is connections list "<connector-key>" --format json
```

- **Native**: Pick default enabled connection (`IsDefault: Yes`, `State: Enabled`).
- **HTTP fallback**: Match connection by vendor **Name** (case-insensitive substring).
- **Multiple**: Present options to the user.
- **None**: Ask user to create via `is connections create "<connector-key>"`.

See [connections.md — Selecting a Connection](connections.md#selecting-a-connection) for full selection logic.

## Step 3: Ping the Connection

```bash
uipcli is connections ping "<connection-id>" --format json
```

| Result | Action |
|---|---|
| `Enabled` | Healthy. Proceed to Step 4. |
| Fails | Run `is connections edit <id>` to re-authenticate, then ping again. If still fails, ask user to choose another or create new. |

## Step 4: Discover Capabilities

**4a. Check activities first** — activities are pre-built actions (e.g., "Send Email", "Create Invoice") that may directly accomplish the task:

```bash
uipcli is activities list "<connector-key>" --format json
```

| Outcome | Action |
|---|---|
| Matching activity found for the user's task | Use the activity. See [activities.md](activities.md) for details. |
| No matching activity | Proceed to Step 4b (resources). |

**4b. List resources** — if no activity matches, discover CRUD-capable objects. **Always pass `--connection-id`** to include custom objects, and **`--operation`** to filter to the intended action:

```bash
uipcli is resources list "<connector-key>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --format json
```

**4c. Describe the target resource** — get field metadata for the matched object:

```bash
uipcli is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --operation <operation> --format json
```

| Describe outcome | Action |
|---|---|
| Returns `requiredFields` / `optionalFields` | Use field metadata. Proceed to Step 5. |
| Returns empty `availableOperations` or "Operation not found" | **Metadata gap** — do not retry with `--refresh`. Skip describe, proceed to Step 5 with inferred fields. See [resources.md — Describe Failures](resources.md#describe-failures). |

See [resources.md](resources.md) for why `--connection-id` and `--operation` are critical.

## Step 4T: Trigger Metadata (if user needs trigger/event configuration)

If the user's task involves **event triggers** (e.g., "when a record is created", "listen for updates"), discover trigger metadata instead of (or in addition to) CRUD resources.

**4T-a. List trigger activities** to see what events the connector supports:

```bash
uipcli is activities list "<connector-key>" --triggers --format json
```

Present trigger activities to the user. Note the **Operation** field (e.g., CREATED, UPDATED, DELETED).

**4T-b. For CREATED/UPDATED/DELETED operations** — get available trigger objects:

```bash
uipcli is triggers objects "<connector-key>" "<OPERATION>" \
  --connection-id "<id>" --format json
```

Present objects to the user and let them choose.

**4T-c. Get trigger field metadata** for the selected object:

```bash
uipcli is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" \
  --connection-id "<id>" --format json
```

**4T-d. For non-CRUD trigger operations** — skip 4T-b. Use the activity's **ObjectName** as the `<object-name>` and go directly to 4T-c.

| Trigger outcome | Action |
|---|---|
| Trigger activities found | Present to user, proceed to 4T-b or 4T-c based on operation type |
| No trigger activities | Connector doesn't support events. Inform user. |
| No objects for operation | Verify operation name is uppercase (CREATED/UPDATED/DELETED). Check connector `hasEvents`. |

See [triggers.md](triggers.md) for full trigger domain reference and response fields.

## Step 5: Resolve Reference Fields

**When describe succeeded:** Check output for `referenceFields`. If none exist, skip to Step 6. For each reference field: list the referenced object, collect valid IDs, and present options to the user.

**When describe was unavailable (metadata gap):** Infer references from the user's request — fields ending in `Id` (e.g., `PromotionId`) typically reference the object with the matching base name (`Promotion`). List that object to resolve the ID before executing.

See [resources.md — Reference Fields](resources.md#reference-fields-critical) and [resources.md — Inferring References Without Describe](resources.md#inferring-references-without-describe).

## Step 6: Execute

```bash
uipcli is resources execute <verb> "<connector-key>" "<object>" \
  --connection-id "<id>" --body '{"field": "value"}' --format json
```

See [resources.md — Execute Operations](resources.md#execute-operations) for the verb table and options.

---

## Happy-Path Example (CRUD)

```bash
# 1. Find connector
uipcli is connectors list --filter "salesforce" --format json
# → Key: "uipath-salesforce-sfdc"

# 2. Find connection
uipcli is connections list "uipath-salesforce-sfdc" --format json
# → Id: "abc-123", IsDefault: Yes, State: Enabled

# 3. Ping
uipcli is connections ping "abc-123" --format json
# → Status: Enabled

# 4a. Check activities first
uipcli is activities list "uipath-salesforce-sfdc" --format json
# → No matching activity for "create contact" → fall back to resources

# 4b. List resources with operation
uipcli is resources list "uipath-salesforce-sfdc" \
  --connection-id "abc-123" --operation Create --format json
# → includes "Contact"

# 4c. Describe the target resource
uipcli is resources describe "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --operation Create --format json
# → requiredFields: [LastName], optionalFields: [FirstName, Email, ...], referenceFields: []

# 5. No referenceFields → skip resolution, go straight to execute

# 6. Execute
uipcli is resources execute create "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --body '{"LastName": "Doe", "FirstName": "Jane"}' --format json
```

---

## Happy-Path Example (Triggers)

```bash
# 1. Find connector
uipcli is connectors list --filter "salesforce" --format json
# → Key: "uipath-salesforce-sfdc"

# 2. Find connection
uipcli is connections list "uipath-salesforce-sfdc" --format json
# → Id: "228624", IsDefault: Yes, State: Enabled

# 3. Ping
uipcli is connections ping "228624" --format json
# → Status: Enabled

# 4T-a. List trigger activities
uipcli is activities list "uipath-salesforce-sfdc" --triggers --format json
# → Trigger activities with Operation: CREATED, UPDATED, DELETED

# 4T-b. Get objects for CREATED operation
uipcli is triggers objects "uipath-salesforce-sfdc" CREATED \
  --connection-id "228624" --format json
# → [AccountHistory, Contact, Lead, ...]
# → User picks "AccountHistory"

# 4T-c. Get trigger metadata (fields) for AccountHistory
uipcli is triggers describe "uipath-salesforce-sfdc" CREATED "AccountHistory" \
  --connection-id "228624" --format json
# → Returns field definitions (names, types, descriptions)
```
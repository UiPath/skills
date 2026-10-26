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

Run:

```bash
uip is connectors list --filter "<vendor>" --output json
```

Use the native connector's **`Key`** and proceed to Step 2. If none is found, fall back to HTTP connector (`uipath-uipath-http`); see [connectors.md — HTTP Connector Fallback](connectors.md#http-connector-fallback).

## Step 2: Find a Connection

Run:

```bash
uip is connections list "<connector-key>" --output json
```

Always present options by name, not UUID: show `Name`, `Owner`, `Folder`, `State`, and `IsDefault`; never show `Id` or `FolderKey`. Recommend the default enabled connection (`IsDefault: Yes`, `State: Enabled`), but let the user confirm or choose another. Do **not** auto-select silently, even when there is exactly one default enabled connection. Say: "I found connection **<Name>** by <Owner> in **<Folder>** folder (default, enabled). Should I use this one?"

For HTTP fallback, match connections by vendor **Name** (case-insensitive substring) and present matches. If none exists, ask the user to create one via `is connections create "<connector-key>"`.

See [connections.md — Selecting a Connection](connections.md#selecting-a-connection) for full selection logic.

## Step 3: Ping the Connection

Run:

```bash
uip is connections ping "<connection-id>" --output json
```

If the result is `Enabled`, proceed to Step 4. If it fails, run `is connections edit <id>` to re-authenticate, then ping again. If it still fails, ask the user to choose another or create a new connection.

## Step 4: Discover Capabilities

### 4a. Activities

Check activities first because pre-built actions may directly accomplish the task:

```bash
uip is activities list "<connector-key>" --output json
```

Use a matching activity; see [activities.md](activities.md). If none matches, list resources.

### 4b. Resources

Always pass `--connection-id` to include custom objects and `--operation` to filter the intended action:

```bash
uip is resources list "<connector-key>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --output json
```

Search the full list, not only exact name matches: resource surfaces are generally much larger than curated activity lists because resources are generated from endpoints. An operation without an activity may still be available here (measured on Slack: **22 curated activities, 187 resources**).

- If a resource covers the operation, describe it.
- If none does, **generate the activity, then execute it**; see [activity-generation.md](activity-generation.md). It first checks whether the connector can host a generated activity and stops if it cannot.
- If the vendor has no such operation, tell the user; do not synthesise one.

### 4c. Describe the target resource

Run either:

```bash
# All operations + all fields
uip is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --output json

# Filter to a single operation (reduces output size)
uip is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --output json
```

Always use `--operation` for field-level detail (for example, `--operation Create`). Without it, the result only shows `availableOperations`; with it, the result includes `requestFields`, `responseFields`, and `parameters`. Results are cached locally. Always pass `--connection-id` for connection-specific metadata, including custom fields.

- On `requestFields` + `responseFields` + `parameters`, use the metadata, check `required` flags and `reference` sections, and proceed to Step 5.
- On `availableOperations` without `--operation`, choose the needed operation and rerun with `--operation`.
- If fields depend on a parent value, or a parameter's `design` has `solutionResourceKind` (a solution-resource picker, such as a Data Fabric folder entity), rerun with parent values as `-f <field>=<value>`; for a picker, use the resource name plus `--solution-folder` for a local solution. See [resources.md — Parent-Field-Driven Custom Fields](resources.md#parent-field-driven-custom-fields-api-type-objectactions) and its "Solution-resource pickers" subsection.
- On error or empty output, treat it as a **metadata gap**: skip describe and proceed to Step 5 with inferred fields. See [resources.md — Describe Failures](resources.md#describe-failures).

## Step 4T: Trigger Metadata (if user needs trigger/event configuration)

For **event triggers** (for example, "when a record is created" or "listen for updates"), discover trigger metadata instead of or in addition to CRUD resources.

1. List trigger activities:

   ```bash
   uip is activities list "<connector-key>" --triggers --output json
   ```

   Present them and note `Operation` (for example, CREATED, UPDATED, DELETED). If none exist, inform the user that the connector does not support events.

2. For CREATED/UPDATED/DELETED, list trigger objects and let the user choose:

   ```bash
   uip is triggers objects "<connector-key>" "<OPERATION>" \
     --connection-id "<id>" --output json
   ```

3. Describe the selected object:

   ```bash
   uip is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" \
     --connection-id "<id>" --output json
   ```

4. For non-CRUD trigger operations, skip object listing; use the activity's `ObjectName` as `<object-name>` and go directly to trigger describe.

If no objects are returned, verify the operation is uppercase (CREATED/UPDATED/DELETED) and check connector `hasEvents`. See [triggers.md](triggers.md) for the trigger domain reference and response fields.

## Step 5: Resolve Reference Fields

When describe succeeds, check for reference fields. For each, list the referenced object, collect valid IDs, and present options. If describe has a metadata gap, infer references from the request: fields ending in `Id` (for example, `PromotionId`) typically reference the object with the matching base name (`Promotion`); list that object to resolve the ID before executing.

See [reference-resolution.md — Reference Fields](reference-resolution.md#reference-fields-critical) and [reference-resolution.md — Field Dependency Chains](reference-resolution.md#field-dependency-chains).

## Step 5a: Validate Required Fields

After resolving references, check every required field against the user's input. This is a hard gate: do **not** execute until every required field has a value; ask the user for missing values.

See [reference-resolution.md — Validate Required Fields Before Executing](reference-resolution.md#validate-required-fields-before-executing).

## Step 6: Execute

Run:

```bash
uip is resources run <verb> "<connector-key>" "<object>" \
  --connection-id "<id>" --body '{"field": "value"}' --output json
```

See [resources.md — Execute Operations](resources.md#execute-operations) for the verb table and options.

### Pagination (list operations)

`run list` may not return all results. Check `Data.Pagination.HasMore` / `NextPageToken`, paginate with `--query "nextPage=<token>"`, and stop early on a match. See [resources.md#pagination](resources.md#pagination) for the full protocol, anti-patterns, and offset/limit fallback.

## Error Recovery

When Step 6 returns a `Failure`, follow this loop instead of retrying blindly or giving up. The CLI returns the HTTP status in `Message` and the raw vendor error body in `Instructions`.

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
uip is resources run create "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --body '{"LastName": "Doe", "FirstName": "Jane"}' --output json
```

---

## Happy-Path Example (Triggers)

Run Steps 1–3 as in the CRUD example (connector → connection → ping), then follow [triggers.md — Happy-Path Example](triggers.md#happy-path-example) for the trigger-specific commands (`activities list --triggers` → `triggers objects` → `triggers describe`).
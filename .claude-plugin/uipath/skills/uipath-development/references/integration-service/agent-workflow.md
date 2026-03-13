# Agent Workflow

Follow these steps in order when the user asks to interact with an external service.

## Contents
- Progress Checklist
- Step 1: Find the Connector
- Step 2: Find a Connection
- Step 3: Ping the Connection
- Step 4: Discover Capabilities
- Step 5: Resolve Reference Fields
- Step 6: Execute
- Happy-Path Example

## Progress Checklist

Copy and track progress:

```
- [ ] Step 1: Find connector (get Key)
- [ ] Step 2: Find connection (get Id)
- [ ] Step 3: Ping connection (confirm Enabled)
- [ ] Step 4: Discover capabilities (resources + activities)
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

Discover resources (CLI-executable CRUD operations):

```bash
uipcli is resources list "<connector-key>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --format json

uipcli is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --operation Create --format json
```

**Always pass `--connection-id` and `--operation`** — see [resources.md](resources.md) for why.

Also discover activities (pre-built actions like "Send Email", "HTTP Request"):

```bash
uipcli is activities list "<connector-key>" --format json
```

Some connectors have both activities and resources — always check both when discovering capabilities. If the user's task maps to an activity rather than resource CRUD, see [activities.md](activities.md) for details.

## Step 5: Resolve Reference Fields

Check describe output for `referenceFields`. **If none exist, skip to Step 6.**

For each reference field: list the referenced object, collect valid IDs, and present options to the user.

See [resources.md — Reference Fields](resources.md#reference-fields-critical) for the resolution workflow and examples.

## Step 6: Execute

```bash
uipcli is resources execute <verb> "<connector-key>" "<object>" \
  --connection-id "<id>" --body '{"field": "value"}' --format json
```

See [resources.md — Execute Operations](resources.md#execute-operations) for the verb table and options.

---

## Happy-Path Example

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

# 4. Describe the target resource
uipcli is resources describe "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --operation Create --format json
# → requiredFields: [LastName], optionalFields: [FirstName, Email, ...], referenceFields: []

# 5. No referenceFields → skip resolution, go straight to execute

# 6. Execute
uipcli is resources execute create "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --body '{"LastName": "Doe", "FirstName": "Jane"}' --format json
```
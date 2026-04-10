# HITL AppTask Node — Direct JSON Reference

The AppTask variant uses a deployed coded app (Studio Web) as the task form. Same node type as QuickForm (`uipath.human-in-the-loop`), same three output handles. Difference: `inputs.type = "custom"` and `inputs.app` points to the deployed app.

---

## App Lookup — Direct API Call

The agent resolves the app by name before writing the node JSON. No CLI command. Read credentials from the environment, then call the Orchestrator API directly.

### Step 1 — Read stored credentials

```bash
# Read from local .env (current dir) or global ~/.uipcli/.env
ENV_FILE=".env"
[ ! -f "$ENV_FILE" ] && ENV_FILE="$HOME/.uipcli/.env"
source "$ENV_FILE"

# Variables now available: UIPATH_URL, UIPATH_ORGANIZATION_ID, UIPATH_ACCESS_TOKEN, UIPATH_TENANT_ID
```

### Step 2 — List deployed apps and find by name

```bash
APP_NAME="Invoice Approval"   # The name the user provided

curl -s \
  "${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/apps_/default/api/v1/default/action-apps?state=deployed" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "X-Uipath-Tenantid: ${UIPATH_TENANT_ID}" \
  -H "Accept: application/json" | \
  jq --arg name "$APP_NAME" '.deployed[] | select(.deploymentTitle | ascii_downcase | contains($name | ascii_downcase))'
```

Response shape for each app:
```json
{
  "id": "c0ba97df-8a30-4fe0-b4b4-4611a631d77b",
  "deploymentTitle": "Invoice Approval",
  "systemName": "invoice-approval",
  "deployVersion": 3,
  "folderPath": "Shared"
}
```

Extract: `systemName` → use as `inputs.app.key`, `deploymentTitle` → use as `inputs.app.name`, `folderPath` → use as `inputs.app.folderPath`.

### Step 3 — (Optional) Fetch app schema for field reference

```bash
curl -s \
  "${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/apps_/default/api/v1/default/action-schema?appSystemName=${SYSTEM_NAME}&version=${DEPLOY_VERSION}" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "X-Uipath-Tenantid: ${UIPATH_TENANT_ID}" \
  -H "Accept: application/json"
```

Returns `{ inputs, outputs, inOuts, outcomes }` — the app's declared schema. Use this to understand what data the app expects, but the `.flow` node does not need to enumerate these fields (the app owns its own form).

---

## Full Node JSON

```json
{
  "id": "invoiceReview1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0.0",
  "display": { "label": "Invoice Review" },
  "ui": { "position": { "x": 474, "y": 144 } },
  "inputs": {
    "type": "custom",
    "channels": [],
    "recipient": {
      "channels": ["Email"],
      "assignee": { "type": "user", "value": "reviewer@company.com" }
    },
    "app": {
      "name": "Invoice Approval",
      "key": "invoice-approval",
      "folderPath": "Shared"
    },
    "schema": {
      "inputs": [],
      "outputs": [],
      "inOuts": [],
      "outcomes": [{ "name": "Submit", "type": "string" }]
    }
  },
  "model": { "type": "bpmn:UserTask" }
}
```

### `inputs.app` field mapping

| Field | Source | Example |
|---|---|---|
| `name` | `deploymentTitle` from app list | `"Invoice Approval"` |
| `key` | `systemName` from app list | `"invoice-approval"` |
| `folderPath` | `folderPath` from app list | `"Shared"` |

### `inputs.recipient` options

```json
// Action Center (default — no specific assignee)
"recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } }

// Specific user by email
"recipient": { "channels": ["Email"], "assignee": { "type": "user", "value": "user@company.com" } }

// Everyone in a group
"recipient": { "channels": ["ActionCenter"], "assignee": { "type": "group", "value": "Finance Team" } }
```

---

## Definition Entry

Same definition as QuickForm — see [hitl-node-quickform.md](hitl-node-quickform.md) for the full definition block. Add it once to `workflow.definitions`, deduplicated by `nodeType`.

---

## Edge Wiring

Identical to QuickForm. Wire `completed`, `cancelled`, `timeout`:

```json
{ "id": "invoiceReview1-completed-nextNode1-input", "sourceNodeId": "invoiceReview1", "sourcePort": "completed", "targetNodeId": "nextNode1", "targetPort": "input" },
{ "id": "invoiceReview1-cancelled-end1-input",      "sourceNodeId": "invoiceReview1", "sourcePort": "cancelled", "targetNodeId": "end1",      "targetPort": "input" },
{ "id": "invoiceReview1-timeout-end2-input",        "sourceNodeId": "invoiceReview1", "sourcePort": "timeout",   "targetNodeId": "end2",      "targetPort": "input" }
```

---

## `variables.nodes` — Regenerate After Adding

Same rule as QuickForm — add `result` and `status` entries for the new node, then replace the entire `variables.nodes` array. See [hitl-node-quickform.md](hitl-node-quickform.md) for the regeneration algorithm.

---

## Runtime Variables

Same as QuickForm:

| Variable | What it contains |
|---|---|
| `$vars.<nodeId>.result` | Outputs the human filled in via the app |
| `$vars.<nodeId>.status` | `"completed"`, `"cancelled"`, or `"timeout"` |

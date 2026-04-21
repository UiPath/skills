# action task — Implementation

## CLI Command

```bash
uip maestro case tasks add <file> <stage-id> \
  --type action \
  --display-name "<display-name>" \
  --task-title "<title>" \
  --priority <Low|Medium|High|Critical> \
  --recipient "<email>" \
  --task-type-id "<action-app-id>" \
  --is-required \
  --output json
```

### Required flags

| Flag | Required | Notes |
|------|----------|-------|
| `--type action` | yes | |
| `--display-name` | yes | Card header |
| `--task-title` | yes | Shown to the assignee inside the Action card |
| `--task-type-id` | yes | Action-app ID from `action-apps-index.json` |
| `--priority` | no | Default: `Medium` |
| `--recipient` | no | Omit for group/role assignment |

## Example

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type action \
  --display-name "Review Purchase Order" \
  --task-title "Please review this PO and approve or reject" \
  --priority High \
  --recipient "approver@corp.com" \
  --task-type-id "act_app_9876543210" \
  --is-required \
  --output json
```

## Resulting JSON Shape

```json
{
  "id": "tsk00000004",
  "elementId": "el_0004",
  "type": "action",
  "displayName": "Review Purchase Order",
  "data": {
    "taskTitle": "Please review this PO and approve or reject",
    "priority": "High",
    "recipient": "approver@corp.com",
    "actionCatalogName": "<catalog-name-from-enrichment>",
    "labels": [ /* enriched */ ],
    "context": { "taskTypeId": "act_app_9876543210" }
  },
  "isRequired": true
}
```

> The `data` shape for `action` differs from process/agent — no `inputs`/`outputs` arrays at the top of `data`. Form field bindings still use `uip maestro case var bind` in the standard way.

## Binding Inputs and Outputs

Use `uip maestro case var bind` per [bindings-and-expressions.md](../../../bindings-and-expressions.md). Input names for an action task map to fields on the Actions app form — discover them via `tasks describe --type action --id <action-app-id>`.

## Post-Add Validation

Capture `TaskId`. Confirm `type: "action"` and `data.taskTitle` non-empty. Verify `data.recipient` matches the sdd.md assignee if one was specified.

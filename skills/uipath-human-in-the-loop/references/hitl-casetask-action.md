# HITL Case Action Task — Implementation Reference

The agent writes an `action` task into a stage of `caseplan.json`. **Direct JSON is the default.** A CLI opt-in is available when the user explicitly requests it.

Two paths exist. **Present both to the user and confirm before writing:**

| Path | When to use | Requires |
|---|---|---|
| **Generic action task** | New plan, no app yet, simple approve/reject | Nothing — no registry pull needed |
| **App-based action task** | Existing deployed Action Center app with a custom form | `task-type-id` from registry + `tasks describe` |

> **If the user is unsure or says "just pick one":** Default to Generic. Say: "I'll use a generic action task — no deployed app needed, it's the quickest to set up. You can upgrade to an app-based task later if you need custom form fields."

---

## Step 1 — Extract the Task Configuration Through Conversation

Ask these questions before designing either path. Ask all missing ones in a single message.

| What you need to know | Question to ask |
|---|---|
| What the reviewer sees | "What information does the reviewer need to make their decision?" |
| What they decide or fill in | "Does the reviewer just approve/reject, or do they need to enter data?" |
| Who receives the task | "Who should receive this task — a specific user (email) or a group?" |
| Priority | "What priority should this task have? Low, Medium, or High?" |

**Common business descriptions → path selection:**

| Description | Path |
|---|---|
| "Finance team approves expense claims before payment" | Generic — group assignee, no custom form |
| "Manager approves a leave request" | Generic — user email, title = "Review this leave request" |
| "Legal reviews and signs off on a contract with custom fields" | App-based — deployed app with specific inputs/outputs |
| "Agent fills in form that a human corrects before submitting" | App-based — outputs populate downstream task inputs |

---

## Path 1 — Generic Action Task (no deployed app)

The human receives the task in Action Center, sees the `taskTitle`, and completes it. No structured form fields — outcome is resolved via Action Center's default task completion UI.

### Task JSON

```json
{
  "id": "ta1b2c3d4",
  "elementId": "Stage_aB3kL9-ta1b2c3d4",
  "displayName": "Invoice Review",
  "type": "action",
  "isRequired": true,
  "data": {
    "taskTitle": "Please review this invoice and approve or reject it",
    "priority": "High",
    "assignmentCriteria": "user",
    "recipient": { "Type": 2, "Value": "approver@company.com" }
  }
}
```

**Group assignee** — omit `assignmentCriteria` and `recipient` entirely; group rules are configured in Action Center separately:

```json
{
  "id": "ta1b2c3d4",
  "elementId": "Stage_aB3kL9-ta1b2c3d4",
  "displayName": "Expense Approval",
  "type": "action",
  "isRequired": true,
  "data": {
    "taskTitle": "Review and approve this expense claim",
    "priority": "Medium"
  }
}
```

### CLI (opt-in)

```bash
# Generic — user email
uip maestro case hitl add caseplan.json Stage_aB3kL9 \
  --label "Invoice Review" \
  --priority High \
  --assignee approver@company.com \
  --output json

# Generic — group (omit --assignee or use a non-email name)
uip maestro case hitl add caseplan.json Stage_aB3kL9 \
  --label "Expense Approval" \
  --priority Medium \
  --assignee finance-approvers \
  --output json
```

> `uip case hitl add` ships in UiPath/cli PR #1207.

### Field Reference (Generic)

| Field | Required | Notes |
|---|---|---|
| `id` | Yes | `t` + 8 alphanumeric chars (e.g. `ta1b2c3d4`) |
| `elementId` | Yes | `${stageId}-${taskId}` |
| `displayName` | Yes | Human-readable task name shown in the plan canvas |
| `type` | Yes | Always `"action"` |
| `data.taskTitle` | **Yes** | What the human sees in Action Center. Validator rejects empty. |
| `data.priority` | No | `"Low"` \| `"Medium"` (default) \| `"High"` \| `"Critical"` |
| `data.assignmentCriteria` | No | `"user"` when assigning to a specific email. Omit for group rules. |
| `data.recipient` | No | `{ "Type": 2, "Value": "<email>" }` for email; `{ "Type": 1, "Value": "<group>" }` for group |
| `isRequired` | No | Whether the task must complete for the stage exit condition to fire |

**`recipient.Type` values:** `0` = user ID, `1` = group ID, `2` = email address, `3` = `"=vars.<varId>"` (runtime resolution)

---

## Path 2 — App-Based Action Task (deployed Action Center app)

The task form is defined by a deployed Action Center app. Inputs are shown to the human; outputs are collected from the form and usable downstream via `=vars.<var>` expressions.

### Step 1 — Discover the App

```bash
# Pull the registry first (requires uip login)
uip maestro case registry pull

# Search for action apps
uip maestro case registry search --type action-apps --output json

# Get a specific app by name (check action-apps-index.json if CLI search fails)
uip maestro case registry get "<app-name>" --type action-apps --output json
```

> CLI search is known to fail for action-apps — always fall back to direct inspection of `~/.uipcli/case-resources/action-apps-index.json`. Use `id` (not `entityKey`), `deploymentTitle` (not `name`), and `deploymentFolder.fullyQualifiedName` for the folder path.

### Step 2 — Get the Input/Output Schema

```bash
uip maestro case tasks describe --type action --id "<action-app-id>" --output json
```

Returns `inputs[]` and `outputs[]`. Capture both — they define what the human fills in and what the automation reads back.

### Step 3 — Write Root-Level Bindings

Add 2 entries to `root.data.uipath.bindings[]` — one for `name` and one for `folderPath`. Deduplicate by `(default + resource + resourceKey)`.

```json
{
  "id": "bG0SraLpg",
  "name": "name",
  "type": "string",
  "resource": "app",
  "resourceKey": "Shared.Contract Review App",
  "propertyAttribute": "name",
  "default": "Contract Review App"
},
{
  "id": "bH1iJK2lm",
  "name": "folderPath",
  "type": "string",
  "resource": "app",
  "resourceKey": "Shared.Contract Review App",
  "propertyAttribute": "folderPath",
  "default": "Shared"
}
```

`resourceKey` = `<folderPath>.<deploymentTitle>`. Binding IDs: `b` + 8 chars.

For the full binding procedure, see [bindings/impl-json.md](../../../uipath-maestro-case/references/plugins/variables/bindings/impl-json.md) in the case skill.

### Step 4 — Write the Task

```json
{
  "id": "ta1b2c3d4",
  "elementId": "Stage_aB3kL9-ta1b2c3d4",
  "displayName": "Contract Review",
  "type": "action",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {
    "taskTitle": "Please review this contract and fill in the required fields",
    "priority": "Medium",
    "actionCatalogName": "Contract Review App",
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "assignmentCriteria": "user",
    "recipient": { "Type": 2, "Value": "reviewer@company.com" },
    "inputs": [],
    "outputs": []
  }
}
```

`data.name` and `data.folderPath` MUST be `=bindings.<id>` references — never string literals.
`data.inputs[]` and `data.outputs[]` are populated from the `tasks describe` response in Step 2.

For the full `inputs[]`/`outputs[]` variable shapes, see [action/impl-json.md](../../../uipath-maestro-case/references/plugins/tasks/action/impl-json.md).

### CLI (opt-in)

```bash
uip maestro case hitl add caseplan.json Stage_aB3kL9 \
  --label "Contract Review" \
  --task-type-id a1b2c3d4-0000-0000-0000-000000000001 \
  --assignee reviewer@company.com \
  --priority Medium \
  --output json
```

Note: the CLI creates the skeleton. You still need to separately:
1. Add the root-level bindings (Step 3 above)
2. Populate `data.inputs[]` / `data.outputs[]` from `tasks describe` (Step 2 above)

---

## Post-Write Verification

```bash
uip maestro case validate <caseplan.json> --output json
```

**Generic task:** verify `type: "action"`, `data.taskTitle` non-empty.

**App-based task:** additionally verify `data.name` and `data.folderPath` start with `=bindings.`, and `root.data.uipath.bindings[]` has 2 entries with `resource: "app"` and `propertyAttribute` = `name` / `folderPath`.

---

## Downstream Output Access

**Generic tasks** produce no structured outputs. Downstream tasks cannot read form data from them.

**App-based tasks** expose each `data.outputs[]` entry via a case variable. The `var` property on each output declares the variable name — reference it in downstream task inputs as `=vars.<var>`:

```json
{ "name": "decision", "type": "string", "id": "out_decision", "var": "decisionVar", ... }
```

Downstream task input: `"value": "=vars.decisionVar"`.

For the full cross-task wiring procedure, see [bindings-and-expressions.md](../../../uipath-maestro-case/references/bindings-and-expressions.md).

# HITL Case Action Task — Implementation Reference

The agent writes an `action` task into a stage of `caseplan.json`. **Direct JSON write is the only supported method on the Case surface.** Unlike the Flow surface (`uip maestro flow hitl add`), the `uipath-maestro-case` skill ships no `hitl` CLI subcommand — `case-commands.md` lists `validate`, `pack`, `debug`, `tasks describe`, `registry`, `process`, `job`, and `instance` only. Edit `caseplan.json` directly per the path-specific JSON shapes below.

Three paths exist. **Present all three to the user and confirm before writing:**

| Path | When to use | Requires |
|---|---|---|
| **QuickForm (inline schema)** | New plan, no deployed app, structured form fields needed | Nothing — schema designed inline, no registry pull |
| **Generic action task** | New plan, no app yet, simple approve/reject with no form fields | Nothing — no registry pull needed |
| **App-based action task** | Existing deployed Action Center app with a custom form | `task-type-id` from registry + `tasks describe` |

> **If the user is unsure or says "just pick one":** Default to QuickForm. Say: "I'll use QuickForm — it's the quickest to set up and works for most approval and review tasks. You can always upgrade to a deployed Action Center app later."

> **Build time vs design time.** A case action task lives in two surfaces:
> - **Design time** — the JSON written into `caseplan.json` (what this skill produces). Studio Web's case designer round-trips this JSON; the QuickForm schema must be valid here.
> - **Build / runtime time** — `uip maestro case validate` accepts it, `uip solution upload` packs it, and Action Center renders the form to the assignee at runtime.
>
> Every shape documented below is required to round-trip in both. After writing, always run `uip maestro case validate <caseplan.json> --output json`.

---

## Step 1 — Extract the Task Configuration Through Conversation

Ask these questions before designing any path. Ask all missing ones in a single message.

| What you need to know | Question to ask |
|---|---|
| What the reviewer sees | "What information does the reviewer need to make their decision?" |
| What they decide or fill in | "Does the reviewer just approve/reject, or do they need to enter data?" |
| Who receives the task | "Who should receive this task — a specific user (email) or a group?" |
| Priority | "What priority should this task have? Low, Medium, or High?" |

**Common business descriptions → path selection:**

| Description | Path |
|---|---|
| "Reviewer approves invoice; sees ID + amount, clicks Approve/Reject" | QuickForm — inline `fields[]` (input) + `outcomes[]` |
| "Human fills in missing vendor name and cost center, then submits" | QuickForm — inline `fields[]` (output direction) |
| "Reviewer edits an AI-drafted email, then sends or discards" | QuickForm — `direction: "inOut"` field for the body |
| "Finance team approves expense claims before payment" | Generic — group assignee, no structured form |
| "Manager approves a leave request" | Generic — user email, simple approve/reject |
| "Legal reviews and signs off on a contract with custom fields" | App-based — deployed app with custom form layout |
| "Agent fills in form that a human corrects before submitting" | App-based — outputs populate downstream task inputs |

---

## Path 1 — QuickForm (inline schema, no deployed app)

The form is defined inline inside the action task's `data.schema`. Action Center renders the fields and outcome buttons directly from that schema at runtime — no deployed app required.

Mirrors the Flow surface QuickForm node — same `fields[]` / `outcomes[]` shape, same `direction` semantics, same Action Center backend (`Actions.HITL`). For the field-design rules and worked schema examples, see [hitl-node-quickform.md](hitl-node-quickform.md).

### Step 1 — Design the Schema

Use these conceptual roles to plan the fields before writing the task JSON:

| Role | `direction` value | Human can… | Use for |
|---|---|---|---|
| Input field | `"input"` | Read only | Context the human needs to make a decision |
| Output field | `"output"` | Write | Data the automation needs back |
| InOut field | `"inOut"` | Read + modify | Data the human can see and optionally correct |

**Supported field types:** `text` (maps from `string`), `number`, `boolean`, `date`

**Design rules:**
- Input fields: bind to upstream case variables via `=vars.<varId>` — never hardcode literals from runtime data
- Output fields: only what downstream tasks actually consume; set `required: true` for mandatory outputs
- `outcomes[]`: use domain-specific names (Approve/Reject, not just Submit)
- Keep it focused — don't add fields the case won't use

**Show the designed schema to the user and confirm before writing.**

### Step 2 — Task JSON

```json
{
  "id": "ta1b2c3d4",
  "elementId": "Stage_aB3kL9-ta1b2c3d4",
  "displayName": "Invoice Review",
  "type": "action",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {
    "taskTitle": "Please review this invoice and approve or reject",
    "priority": "Medium",
    "assignmentCriteria": "user",
    "recipient": { "Type": 2, "Value": "approver@company.com" },
    "formType": "quick",
    "schema": {
      "id": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c",
      "fields": [
        {
          "id": "invoiceid",
          "label": "Invoice ID",
          "type": "text",
          "direction": "input",
          "binding": "=vars.invoiceIdVar"
        },
        {
          "id": "amount",
          "label": "Amount",
          "type": "number",
          "direction": "input",
          "binding": "=vars.amountVar"
        },
        {
          "id": "notes",
          "label": "Notes",
          "type": "text",
          "direction": "output",
          "variable": "notes",
          "required": false
        },
        {
          "id": "decision",
          "label": "Decision",
          "type": "text",
          "direction": "output",
          "variable": "decision",
          "required": true
        }
      ],
      "outcomes": [
        { "id": "approve", "name": "Approve", "isPrimary": true,  "outcomeType": "Positive", "action": "Continue" },
        { "id": "reject",  "name": "Reject",  "isPrimary": false, "outcomeType": "Negative", "action": "End" }
      ]
    }
  }
}
```

**Group assignee** — omit `assignmentCriteria` and `recipient` entirely; group rules are configured in Action Center separately.

### Step 3 — Field Reference (QuickForm)

| Field | Required | Notes |
|---|---|---|
| `id` | Yes | `t` + 8 alphanumeric chars (e.g. `ta1b2c3d4`) |
| `elementId` | Yes | `${stageId}-${taskId}` |
| `displayName` | Yes | Human-readable task name shown in the plan canvas |
| `type` | Yes | Always `"action"` |
| `data.taskTitle` | **Yes** | What the human sees as the task header in Action Center. Validator rejects empty. |
| `data.priority` | No | `"Low"` \| `"Medium"` (default) \| `"High"` \| `"Critical"` |
| `data.assignmentCriteria` | No | `"user"` when assigning to a specific email. Omit for group rules. |
| `data.recipient` | No | `{ "Type": 2, "Value": "<email>" }` for email; `{ "Type": 1, "Value": "<group>" }` for group |
| `data.formType` | **Yes** | Literal `"quick"` — discriminates QuickForm from app-based and generic. |
| `data.schema.id` | Yes | Fresh UUID v4 (e.g. `crypto.randomUUID()`) |
| `data.schema.fields[]` | Yes | At least one entry per role used (input / output / inOut) |
| `data.schema.outcomes[]` | Yes | At least one entry; first entry is primary |
| `isRequired` | No | Whether the task must complete for the stage exit condition to fire |

**`recipient.Type` values:** `0` = user ID, `1` = group ID, `2` = email address, `3` = `"=vars.<varId>"` (runtime resolution)

### Step 4 — Schema Conversion Rules

| Property | Rule |
|---|---|
| field `id` | lowercase label, spaces→`-`, strip non-alphanumeric. `"Invoice ID"` → `"invoiceid"`, `"Due Date"` → `"due-date"` |
| `direction` | inputs → `"input"`, outputs → `"output"`, inOut (read + modify) → `"inOut"` |
| field `type` | `string` → `"text"`, `number` → `"number"`, `boolean` → `"boolean"`, `date` → `"date"` |
| `binding` | Bind to a case variable: `"=vars.<varId>"`. Discover available variables from `root.data.uipath.variables` and upstream task `outputs[].var`. Never hardcode literals from runtime data. |
| `variable` | output / inOut variable name — defaults to `id` if omitted |
| `required` | Omit if false; set `true` for mandatory outputs |
| `outcomes[0]` | `isPrimary: true`, `outcomeType: "Positive"`, `action: "Continue"` |
| `outcomes[1+]` | `isPrimary: false`, `outcomeType: "Negative"` (or `"Neutral"` for Skip / Defer / Hold), `action: "End"` or `"Continue"` |

For four worked schema-conversion examples (simple approval, write-back validation, data enrichment, exception escalation), see [hitl-node-quickform.md § Schema Conversion — Examples](hitl-node-quickform.md#schema-conversion--examples). The examples target the Flow `.flow` shape — for case, copy only the `fields[]` / `outcomes[]` content into `data.schema` here, and rewrite the binding from `=js:$vars.<nodeId>.output.<varName>` to `=vars.<caseVarId>`.

### Step 5 — Discover Upstream Variables

Read available case variables from `root.data.uipath.variables` in `caseplan.json`:

```json
{
  "inputs":      [ { "id": "<varId>", "name": "invoiceId", "type": "string" } ],
  "outputs":     [],
  "inputOutputs":[]
}
```

For cross-task references, source values come from upstream task `outputs[].var` — see [bindings-and-expressions.md](../../../uipath-maestro-case/references/bindings-and-expressions.md) in the case skill for the full discovery procedure.

> **No root-level bindings needed for QuickForm.** Unlike App-based (Path 3), QuickForm does **not** add entries to `root.data.uipath.bindings[]`. There is no app to resolve.

### Post-Write Verification (QuickForm)

Run `uip maestro case validate <caseplan.json> --output json`. Confirm:

- `type === "action"`
- `data.taskTitle` non-empty
- `data.formType === "quick"`
- `data.schema.id` is a UUID
- `data.schema.fields[]` has at least one entry; every entry has `id`, `label`, `type`, `direction`
- `data.schema.outcomes[]` has at least one entry; first entry has `isPrimary: true`
- `root.data.uipath.bindings[]` is **not** modified by this path

### Downstream Output Access (QuickForm)

Each output / inOut field is exposed as a case variable via the field's `variable` property. Reference downstream as `=vars.<variable>`:

```json
{ "id": "decision", "direction": "output", "variable": "decisionVar", "type": "text", "label": "Decision" }
```

Downstream task input value: `"=vars.decisionVar"`. The selected outcome is exposed under the task's status — wire to `=vars.<taskId>.status` in conditions.

For the full cross-task wiring procedure, see [bindings-and-expressions.md](../../../uipath-maestro-case/references/bindings-and-expressions.md).

---

## Path 2 — Generic Action Task (no deployed app, no form fields)

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

## Path 3 — App-Based Action Task (deployed Action Center app)

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

> **Do not set `data.formType` for App-based tasks.** `formType` discriminates QuickForm only. The presence of `actionCatalogName` + `name` + `folderPath` is what marks an action task as app-based.

For the full `inputs[]`/`outputs[]` variable shapes, see [action/impl-json.md](../../../uipath-maestro-case/references/plugins/tasks/action/impl-json.md).

---

## Post-Write Verification (all paths)

```bash
uip maestro case validate <caseplan.json> --output json
```

| Path | Verify |
|---|---|
| QuickForm | `type: "action"`, `data.taskTitle` non-empty, `data.formType: "quick"`, `data.schema.fields[]` non-empty, `data.schema.outcomes[]` non-empty (first has `isPrimary: true`), no `actionCatalogName`/`name`/`folderPath` keys, no entries added to `root.data.uipath.bindings[]` |
| Generic | `type: "action"`, `data.taskTitle` non-empty, no `formType`, no `schema`, no `actionCatalogName` |
| App-based | `type: "action"`, `data.taskTitle` non-empty, `data.name` and `data.folderPath` start with `=bindings.`, `root.data.uipath.bindings[]` has 2 entries with `resource: "app"` and `propertyAttribute` = `name` / `folderPath`, `data.actionCatalogName` matches the deployed `deploymentTitle` |

If validate reports errors, **never report success**. Diagnose from the JSON output and fix before reporting back.

---

## Downstream Output Access

| Path | Outputs available downstream? | How |
|---|---|---|
| QuickForm | Yes — every `output` and `inOut` field | `=vars.<field.variable>` |
| Generic | No — produces no structured outputs | — |
| App-based | Yes — every `data.outputs[]` entry | `=vars.<output.var>` |

**App-based example:**

```json
{ "name": "decision", "type": "string", "id": "out_decision", "var": "decisionVar", ... }
```

Downstream task input: `"value": "=vars.decisionVar"`.

For the full cross-task wiring procedure, see [bindings-and-expressions.md](../../../uipath-maestro-case/references/bindings-and-expressions.md).

# HITL Case Action Task — Implementation Reference

The agent writes an `action` task into a stage of `caseplan.json`. **Direct JSON write is the only supported method on the Case surface.** Unlike the Flow surface (`uip maestro flow hitl add`), the `uipath-maestro-case` skill ships no `hitl` CLI subcommand — `case-commands.md` lists `validate`, `pack`, `debug`, `tasks describe`, `registry`, `process`, `job`, and `instance` only. Edit `caseplan.json` directly per the path-specific JSON shapes below.

Two paths exist. **Present both to the user and confirm before writing:**

| Path | When to use | Requires |
|---|---|---|
| **QuickForm** | Structured form fields, no deployed app needed | A separate `.hitl.json` schema file written alongside `caseplan.json` |
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
| "Reviewer approves invoice; sees ID + amount, clicks Approve/Reject" | QuickForm — `inputs[]` (read-only) + `outcomes[]` |
| "Human fills in missing vendor name and cost center, then submits" | QuickForm — `outputs[]` (writable) |
| "Reviewer edits an AI-drafted email, then sends or discards" | QuickForm — `inOuts[]` for the body |
| "Finance team approves expense claims before payment" | QuickForm — group assignee, outcomes are Approve/Reject |
| "Manager approves a leave request" | QuickForm — user email assignee, outcomes are Approve/Reject |
| "Legal reviews and signs off on a contract with custom fields" | App-based — deployed app with custom form layout |
| "Agent fills in form that a human corrects before submitting" | App-based — outputs populate downstream task inputs |

---

## Path 1 — QuickForm (file-based schema, no deployed app)

The form schema lives in a separate `.hitl.json` file that sits alongside `caseplan.json` in the case project directory. Action Center renders the fields at runtime from the schema — no deployed app required.

> **What makes Path 1 (QuickForm) unique — checklist before you finish:**
> - ✅ A `<TaskLabel>.hitl.json` file is **created** alongside `caseplan.json`
> - ✅ `data.context[hitlType].value` is `"quick"` (not `"custom"`)
> - ✅ `data.context[_schemaFileId].value` is a **plain UUID v4 string** — e.g. `"f1e2d3c4-b5a6-7890-abcd-ef1234567890"`. Never an `=bindings.xxx` expression.
> - ✅ `data.context[hitlSchemaId].value` is a **plain UUID v4 string** matching `schemaId` in the `.hitl.json` file. Never an `=bindings.xxx` expression.
> - ✅ `data.inputs[]` and `data.outputs[]` are **empty arrays** (`[]`)
> - ❌ `data.name` and `data.folderPath` do NOT exist — those are App-based (Path 2) only
> - ❌ No `=bindings.xxx` expressions anywhere in the task JSON — those are App-based only
> - ❌ No `root.data.uipath.bindings[]` entries added

### Step 1 — Design the Schema

Use these roles to plan the fields before writing:

| Role | `field.direction` | Human can… | Use for |
|---|---|---|---|
| Input field | `"input"` | Read only | Context the human needs to make a decision |
| Output field | `"output"` | Write | Data the automation needs back |
| InOut field | `"inOut"` | Read + modify | Data the human can see and optionally correct |

**Supported field types:** `text`, `number`, `boolean`, `date`, `dateTime`

**Design rules:**
- Input fields: bind to upstream case variables via `=vars.<varId>` — never hardcode literals from runtime data
- Output fields: only what downstream tasks actually consume; set `required: true` for mandatory outputs
- `outcomes[]`: use domain-specific names (Approve/Reject, not just Submit)
- Keep it focused — don't add fields the case won't use

**Show the designed schema to the user and confirm before writing.**

### Step 2 — Write the `.hitl.json` File

Generate two UUID v4 values:
- `schemaId` — identity of the schema, stored inside the file and referenced from the action task
- `fileId` — placeholder file system ID (Studio Web assigns the real one when it processes the project; use a fresh UUID v4 as a stable placeholder)

Create a file named `<TaskLabel>.hitl.json` in the case project directory (alongside `caseplan.json`).

The file uses a **unified `fields[]` array** — every field has a `direction` property that determines its role. This is the format the sync runtime reads (`parsed?.fields`).

```json
{
  "schemaId": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c",
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
    { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true,  "action": "Continue" },
    { "id": "reject",  "name": "Reject",  "type": "string", "isPrimary": false, "action": "End" }
  ]
}
```

**Field shape reference:**

| Property | Required | Notes |
|---|---|---|
| `id` | Yes | lowercase label, spaces→`-`, strip non-alphanumeric. `"Invoice ID"` → `"invoiceid"`, `"Due Date"` → `"due-date"` |
| `label` | Yes | Display label in the form. Validator rejects empty. |
| `type` | Yes | `text`, `number`, `boolean`, `date`, `dateTime` |
| `direction` | Yes | `"input"`, `"output"`, or `"inOut"` |
| `binding` | For `direction: "input"` / `"inOut"` | `"=vars.<varId>"` — reads from a case variable. Never hardcode literals. |
| `variable` | For `direction: "output"` / `"inOut"` | Variable name the output is written to, accessible downstream as `=vars.<variable>` |
| `required` | No | `true` for mandatory outputs — omit if false |

**`outcomes[]` shape:** `{ "id": "<slug>", "name": "<OutcomeName>", "type": "string", "isPrimary": <bool>, "action": "Continue" | "End" }` — first entry is the primary action.

### Step 3 — Write the Action Task in `caseplan.json`

```json
{
  "id": "ta1b2c3d4",
  "elementId": "Stage_aB3kL9-ta1b2c3d4",
  "type": "action",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "entryConditions": [
    {
      "id": "Condition_EnTk1",
      "displayName": "Entry Rule 1",
      "rules": [ [ { "id": "Rule_EnTk1", "rule": "current-stage-entered" } ] ]
    }
  ],
  "data": {
    "taskTitle": "Please review this invoice and approve or reject",
    "context": [
      { "name": "hitlType",                    "type": "string",  "value": "quick" },
      { "name": "_schemaFileId",               "type": "string",  "value": "f1e2d3c4-b5a6-7890-abcd-ef1234567890" },
      { "name": "hitlSchemaId",                "type": "string",  "value": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c" },
      { "name": "taskTitle",                   "type": "string",  "value": "Please review this invoice and approve or reject" },
      { "name": "labels",                      "type": "string" },
      { "name": "priority",                    "type": "string",  "value": "Medium" },
      { "name": "actionCatalogName",           "type": "string" },
      { "name": "enableActionableNotifications","type": "boolean", "value": "false" },
      { "name": "assignmentCriteria",          "type": "string",  "value": "user" },
      { "name": "recipient",                   "type": "json",    "body": { "Type": 2, "Value": "approver@company.com" } }
    ],
    "inputs": [],
    "outputs": []
  }
}
```

**Context entry notes:**

| `name` | Notes |
|---|---|
| `hitlType` | Always `"quick"` for QuickForm |
| `_schemaFileId` | Fresh UUID v4 — the placeholder file ID. **Different** from `schemaId` in the `.hitl.json` file. Studio Web replaces this with the real file ID when it processes the project. |
| `hitlSchemaId` | Must match the `schemaId` value inside the `.hitl.json` file exactly. |
| `taskTitle` | Appears both as `data.taskTitle` (top-level) and in `context[]` — **both are required**. |
| `labels` | No `value` — leave the entry present but empty. |
| `priority` | `"Low"` \| `"Medium"` (default) \| `"High"` \| `"Critical"` |
| `actionCatalogName` | No `value` for QuickForm — leave the entry present but empty. |
| `enableActionableNotifications` | Leave as `"false"` unless the user explicitly wants email notifications. |
| `assignmentCriteria` | `"user"` when assigning to a specific email. Omit the `value` (or omit the entry) for group rules. |
| `recipient` | `{ "Type": 2, "Value": "<email>" }` for email; `{ "Type": 1, "Value": "<group>" }` for group; `{ "Type": 3, "Value": "=vars.<varId>" }` for runtime-resolved assignee. |

**`data.inputs[]` and `data.outputs[]`** are always empty arrays for QuickForm — the schema is in the `.hitl.json` file.

### Step 4 — Discover Upstream Variables

Read available case variables from `root.data.uipath.variables` in `caseplan.json`:

```json
{
  "inputs":      [ { "id": "<varId>", "name": "invoiceId", "type": "string" } ],
  "outputs":     [],
  "inputOutputs":[]
}
```

For cross-task references, source values come from upstream task `outputs[].var` — see [bindings-and-expressions.md](../../../uipath-maestro-case/references/bindings-and-expressions.md) in the case skill for the full discovery procedure.

> **No root-level bindings needed for QuickForm.** Unlike App-based (Path 2), QuickForm does **not** add entries to `root.data.uipath.bindings[]`.

### Post-Write Verification (QuickForm)

Run `uip maestro case validate <caseplan.json> --output json`. Confirm:

- `.hitl.json` file exists in the project directory with `schemaId`, `fields[]` (unified array with `direction`), `outcomes[]`
- Action task `type === "action"`
- `data.taskTitle` non-empty and matches `data.context[taskTitle].value`
- `data.context[]` has entries for: `hitlType` (`"quick"`), `_schemaFileId`, `hitlSchemaId`, `taskTitle`, `labels`, `priority`, `actionCatalogName`, `enableActionableNotifications`
- `data.context[hitlSchemaId].value` matches `schemaId` in the `.hitl.json` file
- `data.inputs[]` and `data.outputs[]` are empty arrays
- `root.data.uipath.bindings[]` is **not** modified by this path

### Downstream Output Access (QuickForm)

Each field in `outputs[]` and `inOuts[]` exposes its value downstream via the field's `variable` property:

```json
{ "id": "decision", "variable": "decision", "type": "text", "label": "Decision" }
```

Downstream task input value: `"=vars.decision"`. The selected outcome is available via the task status.

For the full cross-task wiring procedure, see [bindings-and-expressions.md](../../../uipath-maestro-case/references/bindings-and-expressions.md).

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
  "type": "action",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "entryConditions": [
    {
      "id": "Condition_EnTk1",
      "displayName": "Entry Rule 1",
      "rules": [ [ { "id": "Rule_EnTk1", "rule": "current-stage-entered" } ] ]
    }
  ],
  "data": {
    "taskTitle": "Please review this contract and fill in the required fields",
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "actionCatalogName": "Contract Review App",
    "assignmentCriteria": "user",
    "recipient": { "Type": 2, "Value": "reviewer@company.com" },
    "context": [
      { "name": "hitlType", "type": "string", "value": "custom" },
      { "name": "_schemaFileId", "type": "string", "value": "<file-uuid>" },
      { "name": "hitlSchemaId", "type": "string", "value": "<schema-uuid>" }
    ],
    "inputs": [],
    "outputs": []
  }
}
```

`data.name` and `data.folderPath` MUST be `=bindings.<id>` references — never string literals.
`data.inputs[]` and `data.outputs[]` are populated from the `tasks describe` response in Step 2.

> **`hitlType` is `"custom"` for app-based tasks.** The `context[]` entries are required; `_schemaFileId` and `hitlSchemaId` reference the app's schema registration.

For the full `inputs[]`/`outputs[]` variable shapes, see [action/impl-json.md](../../../uipath-maestro-case/references/plugins/tasks/action/impl-json.md).

---

## Post-Write Verification (all paths)

```bash
uip maestro case validate <caseplan.json> --output json
```

| Path | Verify |
|---|---|
| QuickForm | `.hitl.json` file present; task `type: "action"`, `data.taskTitle` non-empty; `data.context[]` has `hitlType: "quick"`, `_schemaFileId`, `hitlSchemaId` (matches `.hitl.json` `schemaId`), `taskTitle`; `data.inputs[]` and `data.outputs[]` empty; no `actionCatalogName` value; no `root.data.uipath.bindings[]` entries added |
| App-based | `type: "action"`, `data.taskTitle` non-empty, `data.name` and `data.folderPath` start with `=bindings.`, `data.context[]` has `hitlType: "custom"`, `root.data.uipath.bindings[]` has 2 entries with `resource: "app"` and `propertyAttribute` = `name` / `folderPath`, `data.actionCatalogName` matches the deployed `deploymentTitle` |
| Both | The task node has `entryConditions[]` set — e.g. `current-stage-entered` (see the Step 3/4 examples above). Without it, validate fails with `Task has no entry rules`. This is a case-structural requirement, not HITL-specific — it applies to every action task written via direct JSON. |

If validate reports errors, **never report success**. Diagnose from the JSON output and fix before reporting back. A validate error unrelated to the HITL task itself (e.g. `Case has no completion rules` on a stage/case that predates your edit) is a pre-existing gap in the case plan, not something this skill introduces — surface it to the user rather than reverse-engineering the CLI to silence it.

---

## Downstream Output Access

| Path | Outputs available downstream? | How |
|---|---|---|
| QuickForm | Yes — every `outputs[]` and `inOuts[]` field in the `.hitl.json` | `=vars.<field.variable>` |
| App-based | Yes — every `data.outputs[]` entry | `=vars.<output.var>` |

**QuickForm example:**

```json
{ "id": "decision", "variable": "decision", "type": "text", "label": "Decision" }
```

Downstream task input: `"value": "=vars.decision"`.

**App-based example:**

```json
{ "name": "decision", "type": "string", "id": "out_decision", "var": "decisionVar" }
```

Downstream task input: `"value": "=vars.decisionVar"`.

For the full cross-task wiring procedure, see [bindings-and-expressions.md](../../../uipath-maestro-case/references/bindings-and-expressions.md).

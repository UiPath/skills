# HITL Case Action Task — Implementation Reference

The agent writes an `action` task into a stage of `caseplan.json`. **Direct JSON write is the primary method on the Case surface.** Unlike the Flow surface (`uip maestro flow hitl add`), the `uipath-maestro-case` skill ships no single `hitl add` CLI subcommand for the HITL-specific parts (`context[]` entries, `.hitl.json` linkage) — edit `caseplan.json` directly per the path-specific JSON shapes below.

> If the stage or case predates required entry/exit/completion rules (see the checklist below), `uip maestro case` does have CLI mutation commands for those (`stage-entry-conditions`, `stage-exit-conditions`, `case-exit-conditions`, `task-entry-conditions` — each with an `add` subcommand). Prefer them over hand-writing that JSON when the case project already exists as a file you can pass to the CLI. If you're editing a caseplan.json given to you directly (not one you scaffolded yourself with these commands), it's simplest to just include the correct rule shapes directly per the examples below.

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
> - ❌ No top-level `bindings[]` entries added

### Step 1 — Design the Schema

Use these roles to plan the fields before writing:

| Role | `field.direction` | Human can… | Use for |
|---|---|---|---|
| Input field | `"input"` | Read only | Context the human needs to make a decision |
| Output field | `"output"` | Write | Data the automation needs back |
| InOut field | `"inOut"` | Read + modify | Data the human can see and optionally correct |

**Supported field types:** `string`, `number`, `boolean`, `date`, `datetime` (canonical — see [hitl-node-quickform.md](hitl-node-quickform.md) for the same vocabulary on the Flow surface; legacy aliases like `text`/`dateTime` are silently normalized by the runtime, but write the canonical form directly)

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
  "title": "Invoice Approval",
  "fields": [
    {
      "id": "invoiceid",
      "label": "Invoice ID",
      "type": "string",
      "direction": "input",
      "colSpan": 6,
      "binding": "=vars.invoiceIdVar"
    },
    {
      "id": "amount",
      "label": "Amount",
      "type": "number",
      "direction": "input",
      "colSpan": 6,
      "binding": "=vars.amountVar"
    },
    {
      "id": "notes",
      "label": "Notes",
      "type": "string",
      "direction": "output",
      "colSpan": 6,
      "variable": "vars.notes"
    },
    {
      "id": "decision",
      "label": "Decision",
      "type": "string",
      "direction": "output",
      "colSpan": 6,
      "variable": "vars.decision"
    }
  ],
  "outcomes": [
    { "id": "outcome-0", "name": "Approve", "type": "string", "isPrimary": true },
    { "id": "outcome-1", "name": "Reject",  "type": "string", "isPrimary": false }
  ],
  "schemaId": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c"
}
```

**Field shape reference:**

| Property | Required | Notes |
|---|---|---|
| `id` | Yes | lowercase label, strip spaces and non-alphanumeric characters (no separator). `"Invoice ID"` → `"invoiceid"`, `"Due Date"` → `"duedate"` |
| `label` | Yes | Display label in the form. Validator rejects empty. |
| `type` | Yes | `string`, `number`, `boolean`, `date`, `datetime` |
| `direction` | Yes | `"input"`, `"output"`, or `"inOut"` |
| `colSpan` | No | Grid width hint for the form layout (e.g. `6` of 12). Safe to omit — confirmed optional against a real Studio Web export. |
| `binding` | For `direction: "input"` / `"inOut"` | `"=vars.<varId>"` — reads from a case variable. A literal is also valid as an `=`-expression (e.g. `="Acme Corp"`), confirmed against a real export, but prefer a variable binding when the value comes from upstream data. |
| `variable` | For `direction: "output"` / `"inOut"` | The **full** `"vars.<name>"` reference (no leading `=`) the output writes to — not a bare name. Downstream tasks read it as `=vars.<name>`. |
| `required` | No | `true` for mandatory outputs — omit if false |

**`outcomes[]` shape:** `{ "id": "<slug>", "name": "<OutcomeName>", "type": "string", "isPrimary": <bool> }` — first entry is the primary action. **No `action` key** — confirmed against a real Studio Web export; an earlier draft of this doc invented one, do not reintroduce it.

> **`title` is required, top-level in the `.hitl.json` file** — the form's display title in Action Center, separate from both the task's `displayName` (canvas label) and `data.taskTitle` (the assignee-facing message). All three are independent strings and do not need to match.

### Step 3 — Write the Action Task in `caseplan.json`

```json
{
  "id": "ta1b2c3d4",
  "elementId": "Stage_aB3kL9-ta1b2c3d4",
  "type": "action",
  "displayName": "Invoice Approval",
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
      { "name": "taskTitle",                   "type": "string",  "value": "Please review this invoice and approve or reject" },
      { "name": "labels",                      "type": "string" },
      { "name": "priority",                    "type": "string",  "value": "Medium" },
      { "name": "actionCatalogName",           "type": "string" },
      { "name": "enableActionableNotifications","type": "boolean", "value": "false" },
      { "name": "assignmentCriteria",          "type": "string",  "value": "user" },
      { "name": "recipient",                   "type": "json",    "body": { "Type": 2, "Value": "approver@company.com" } },
      { "name": "_schemaFileId",               "type": "string",  "value": "f1e2d3c4-b5a6-7890-abcd-ef1234567890" },
      { "name": "hitlSchemaId",                "type": "string",  "value": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c" }
    ],
    "inputs": [
      { "name": "invoiceid", "type": "string", "displayName": "Invoice ID", "target": "bodyField", "value": "=vars.invoiceIdVar" },
      { "name": "amount",    "type": "number", "displayName": "Amount",    "target": "bodyField", "value": "=vars.amountVar" }
    ],
    "outputs": [
      { "name": "Action", "type": "string", "displayName": "Action", "source": "=Action", "var": "invoiceDecision",
        "options": [ { "value": "Approve", "label": "Approve" }, { "value": "Reject", "label": "Reject" } ] }
    ],
    "inputSchema": {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {
        "invoiceid": { "type": "string", "title": "Invoice ID" },
        "amount": { "type": "number", "title": "Amount" }
      },
      "required": []
    }
  }
}
```

> **`displayName`, `inputs[]`/`outputs[]`, and `inputSchema` are all required — this is the part an earlier draft of this doc got wrong.** It previously claimed `data.inputs[]`/`data.outputs[]` "are always empty arrays for QuickForm — the schema is in the `.hitl.json` file." That is false. Confirmed against a real Studio Web export and by direct reproduction: without `inputSchema` (a JSON-Schema mirror of the input fields) and populated `inputs[]`/`outputs[]` on the task node itself, Studio Web's "Edit Schema" canvas does not open at all — clicking it does nothing, silently. The `.hitl.json` file and the task's own `data.*` fields are **two parallel representations of the same schema** that must both be written; neither one alone is sufficient.
> - `inputs[]`: one entry per input field, `name` = field `id`, `value` = the same `=`-expression as that field's `binding` in `.hitl.json`.
> - `outputs[]`: one entry per **output field with a `variable`**, plus one always-present `Action` entry whose `options[]` mirrors `outcomes[]` from `.hitl.json` (`{value, label}` pairs) — this is the decision/outcome the reviewer picks, not a separate field.
> - `inputSchema`: a `draft-07` JSON Schema, `properties` keyed by the same field ids as `inputs[]`, each `{"type": "<field type>", "title": "<field label>"}`.

**Context entry notes:**

| `name` | Notes |
|---|---|
| `hitlType` | Always `"quick"` for QuickForm |
| `_schemaFileId` | **Not a value you can invent — see the callout below.** It must be the real, backend-assigned file ID of the uploaded `.hitl.json`, not a fresh UUID. |
| `hitlSchemaId` | Must match the `schemaId` value inside the `.hitl.json` file exactly. |
| `taskTitle` | Appears both as `data.taskTitle` (top-level) and in `context[]` — **both are required**. |
| `labels` | No `value` — leave the entry present but empty. |
| `priority` | `"Low"` \| `"Medium"` (default) \| `"High"` \| `"Critical"` |
| `actionCatalogName` | No `value` for QuickForm — leave the entry present but empty. |
| `enableActionableNotifications` | Leave as `"false"` unless the user explicitly wants email notifications. |
| `assignmentCriteria` | `"user"` when assigning to a specific email. Omit the `value` (or omit the entry) for group rules. |
| `recipient` | `{ "Type": 2, "Value": "<email>" }` for email; `{ "Type": 1, "Value": "<group>" }` for group; `{ "Type": 3, "Value": "=vars.<varId>" }` for runtime-resolved assignee. |

> **`_schemaFileId` cannot be authored blind — it is a server-assigned foreign key, not a UUID you invent.** Confirmed by direct reproduction against Studio Web: a placeholder UUID here makes "Edit Schema" fail with a `404` on `FileOperations/File/Rename` (the fileId in that failed request is whatever placeholder was written) — Studio Web does **not** silently reconcile it on upload, contrary to what an earlier draft of this doc claimed. There is currently no `uip` CLI command that resolves this. The only known working procedure:
> 1. Upload the project once with any placeholder value in `_schemaFileId` (`uip solution upload`).
> 2. Look up the real ID Studio Web assigned to the `.hitl.json` file via `GET /api/Project/{projectId}/FileOperations/Structure` (find the entry whose `name` matches the `.hitl.json` filename — an internal Studio Web REST endpoint, not a `uip` CLI verb).
> 3. Patch `_schemaFileId` in `caseplan.json` to that real ID.
> 4. Push the corrected `caseplan.json` back with a **targeted single-file update** — `PUT /api/Project/{projectId}/FileOperations/File/{fileId}` (same file's own real ID) — **not** another whole-project `uip solution upload`. A second whole-project upload re-pushes every file and mints a **new** random file ID for each one, including `.hitl.json`, immediately invalidating whatever you just patched.
>
> This is a real gap, not just a documentation gap: today there is no supported CLI path to make a freshly-authored QuickForm task's schema editable in Studio Web without dropping to this undocumented internal API. Flag this to the user rather than silently attempting it, unless they've explicitly asked for the schema to be Studio-Web-editable.

### Step 4 — Discover Upstream Variables

Read available case variables from the top-level `variables` field in `caseplan.json` (current schema is flat — no `root` wrapper; see [case-schema.md](../../uipath-maestro-case/references/case-schema.md#top-level-shape) in the case skill):

```json
{
  "inputs":      [ { "id": "<varId>", "name": "invoiceId", "type": "string" } ],
  "outputs":     [],
  "inputOutputs":[]
}
```

For cross-task references, source values come from upstream task `outputs[].var` — see [bindings-and-expressions.md](../../uipath-maestro-case/references/bindings-and-expressions.md) in the case skill for the full discovery procedure.

> **No root-level bindings needed for QuickForm.** Unlike App-based (Path 2), QuickForm does **not** add entries to the top-level `bindings[]` array.

### Post-Write Verification (QuickForm)

Run `uip maestro case validate <caseplan.json> --output json`. Confirm:

- `.hitl.json` file exists in the project directory with `schemaId`, `fields[]` (unified array with `direction`), `outcomes[]`
- Action task `type === "action"`
- `data.taskTitle` non-empty and matches `data.context[taskTitle].value`
- `data.context[]` has entries for: `hitlType` (`"quick"`), `_schemaFileId`, `hitlSchemaId`, `taskTitle`, `labels`, `priority`, `actionCatalogName`, `enableActionableNotifications`
- `data.context[hitlSchemaId].value` matches `schemaId` in the `.hitl.json` file
- `data.inputs[]`/`data.outputs[]` are populated (mirroring `.hitl.json`'s fields) and `data.inputSchema` is present — see the callout in Step 3
- top-level `bindings[]` is **not** modified by this path

### Downstream Output Access (QuickForm)

Each field in `outputs[]` and `inOuts[]` exposes its value downstream via the field's `variable` property — the **full** `"vars.<name>"` string, not a bare name:

```json
{ "id": "decision", "variable": "vars.decision", "type": "string", "label": "Decision" }
```

Downstream task input value: `"=vars.decision"`. The selected outcome is available via the task's `Action` output (see Step 3).

For the full cross-task wiring procedure, see [bindings-and-expressions.md](../../uipath-maestro-case/references/bindings-and-expressions.md).

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

Add 2 entries to the top-level `bindings[]` array — one for `name` and one for `folderPath`. Deduplicate by `(default + resource + resourceKey)`.

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

For the full binding procedure, see [bindings/impl-json.md](../../uipath-maestro-case/references/plugins/variables/bindings/impl-json.md) in the case skill.

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
      { "name": "hitlType", "type": "string", "value": "custom" }
    ],
    "inputs": [],
    "outputs": []
  }
}
```

`data.name` and `data.folderPath` MUST be `=bindings.<id>` references — never string literals.
`data.inputs[]` and `data.outputs[]` are populated from the `tasks describe` response in Step 2.

> **`hitlType` is `"custom"` for app-based tasks.** App-based tasks have no schema file at all — the form is defined by the deployed app itself, not by a schema document. **Never write `_schemaFileId` or `hitlSchemaId` for an app-based task** — those two context entries exist only on the QuickForm path (Path 1), where they identify the `.hitl.json` schema file. An app-based task is fully described by `data.name`/`data.folderPath` (the bindings to the deployed app) plus `data.inputs[]`/`data.outputs[]` (from `tasks describe`) — nothing else identifies its "schema."

For the full `inputs[]`/`outputs[]` variable shapes, see [action/impl-json.md](../../uipath-maestro-case/references/plugins/tasks/action/impl-json.md).

---

## Post-Write Verification (all paths)

```bash
uip maestro case validate <caseplan.json> --output json
```

| Path | Verify |
|---|---|
| QuickForm | `.hitl.json` file present with `title`, `fields[]`, `outcomes[]` (no `action` key), `schemaId`; task has `displayName`; `data.context[]` has `hitlType: "quick"`, `_schemaFileId`, `hitlSchemaId` (matches `.hitl.json` `schemaId`), `taskTitle`; `data.inputs[]`/`data.outputs[]` populated (not empty) and `data.inputSchema` present, mirroring `.hitl.json`'s fields; no `actionCatalogName` value; no top-level `bindings[]` entries added |
| App-based | `type: "action"`, `data.taskTitle` non-empty, `data.name` and `data.folderPath` start with `=bindings.`, `data.context[]` has `hitlType: "custom"` and **no** `_schemaFileId`/`hitlSchemaId` entries (app-based tasks have no schema file), top-level `bindings[]` has 2 entries with `resource: "app"` and `propertyAttribute` = `name` / `folderPath`, `data.actionCatalogName` matches the deployed `deploymentTitle` |
| Both | The task node has `entryConditions[]` set — e.g. `current-stage-entered` (see the Step 3/4 examples above). Without it, validate fails with `Task has no entry rules`. This is a case-structural requirement, not HITL-specific — it applies to every action task written via direct JSON. |

If validate reports errors, **never report success**. Diagnose from the JSON output and fix before reporting back. A validate error unrelated to the HITL task itself (e.g. `Case has no completion rules` on a stage/case that predates your edit) is a pre-existing gap in the case plan, not something this skill introduces — surface it to the user rather than reverse-engineering the CLI to silence it.

---

## Downstream Output Access

| Path | Outputs available downstream? | How |
|---|---|---|
| QuickForm | Yes — every `outputs[]` and `inOuts[]` field in the `.hitl.json` | `field.variable` is already the full `=vars.<name>` reference (minus the leading `=`) |
| App-based | Yes — every `data.outputs[]` entry | `=vars.<output.var>` |

**QuickForm example:**

```json
{ "id": "decision", "variable": "vars.decision", "type": "string", "label": "Decision" }
```

Downstream task input: `"value": "=vars.decision"`.

**App-based example:**

```json
{ "name": "decision", "type": "string", "id": "out_decision", "var": "decisionVar" }
```

Downstream task input: `"value": "=vars.decisionVar"`.

For the full cross-task wiring procedure, see [bindings-and-expressions.md](../../uipath-maestro-case/references/bindings-and-expressions.md).

# HITL Case Action Task — Implementation Reference

Write an `action` task into a stage of `caseplan.json`. **Direct JSON write is the primary Case-surface method.** Unlike the Flow surface (`uip maestro flow hitl add`), `uipath-maestro-case` has no HITL-specific `hitl add` command for `context[]` or `.hitl.json` linkage; edit `caseplan.json` directly using the shapes below.

If the case predates required entry, exit, or completion rules, run the applicable CLI mutation command (`stage-entry-conditions`, `stage-exit-conditions`, `case-exit-conditions`, or `task-entry-conditions`, each with an `add` subcommand) when an existing case project can be passed to the CLI. For a directly supplied `caseplan.json`, write the rule shapes directly.

Infer the path and proceed; never wait for the user to choose:

| Path | Use when | Requires |
|---|---|---|
| **QuickForm** | Structured fields; no deployed app | A separate `.hitl.json` beside `caseplan.json` |
| **App-based action task** | Existing deployed Action Center app with custom form | `task-type-id` from the registry and `tasks describe` |

When unsure, default to QuickForm and say: “I'll use QuickForm — it's the quickest to set up and works for most approval and review tasks. You can always upgrade to a deployed Action Center app later.”

Write case JSON and the QuickForm schema so they round-trip in Studio Web; run validation, upload, and runtime rendering checks as applicable. After writing, **run** `uip maestro case validate <caseplan.json> --output json`.

## Step 1 — Extract the Task Configuration Through Conversation

Never block on configuration. Infer from the business description and ask only when the user is present and clarification helps. Defaults: recipient → a group named after the relevant team (for example, `finance-team` or `data-enrichment-team`); priority → `Low`.

| Need | Infer from |
|---|---|
| Reviewer sees | Data extracted or produced upstream |
| Reviewer decides/fills | “approve/reject” means decision; “fill in”, “correct”, or “enrich” means data entry |
| Recipient | Named person/email or team; otherwise infer a sensible team name |
| Priority | “urgent”/“high priority” → `High`/`Medium`; otherwise `Low` |

Select QuickForm for approvals, reviews, missing-field entry, and editable AI drafts. Select App-based for a deployed custom form, such as legal sign-off with custom fields or an agent-populated form that a human corrects.

## Path 1 — QuickForm (file-based schema, no deployed app)

Create `<TaskLabel>.hitl.json` alongside `caseplan.json`; Action Center renders it without a deployed app.

### Step 1 — Design the Schema

Use these roles:

| `field.direction` | Human can | Use for |
|---|---|---|
| `input` | Read only | Context needed for a decision |
| `output` | Write | Data automation needs back |
| `inOut` | Read and modify | Data the human may correct |

Use canonical types `string`, `number`, `boolean`, `date`, and `datetime`; legacy `text`/`dateTime` may normalize, but write canonical types. Bind `input` and `inOut` fields to upstream variables with `=vars.<varId>` and prefer variable bindings over literals. Write only downstream-consumed outputs and set `required: true` for mandatory outputs. Use domain-specific outcome names such as `Approve` and `Reject`. Never block: write the schema and mention it in the final report so the user can adjust it.

### Step 2 — Write the `.hitl.json` File

Generate fresh UUID v4 values for `schemaId` and the initial `fileId` placeholder. Use one unified `fields[]` array:

```json
{
  "title": "<form title>",
  "fields": [
    {
      "id": "<lowercase label without separators>",
      "label": "<display label>",
      "type": "string",
      "direction": "input",
      "colSpan": 6,
      "binding": "=vars.<varId>"
    },
    {
      "id": "<output id>",
      "label": "<display label>",
      "type": "string",
      "direction": "output",
      "variable": "vars.<name>",
      "required": true
    }
  ],
  "outcomes": [
    { "id": "outcome-0", "name": "Approve", "type": "string", "isPrimary": true },
    { "id": "outcome-1", "name": "Reject", "type": "string", "isPrimary": false }
  ],
  "schemaId": "<UUID v4>"
}
```

`title` is required and top-level, independent of task `displayName` and `data.taskTitle`. Required field keys are `id`, `label`, `type`, and `direction`. Make `id` the lowercase label with spaces and non-alphanumeric characters removed (`Invoice ID` → `invoiceid`). `colSpan` is optional. Require `binding` for `input`/`inOut`, normally `=vars.<varId>`; an `=` literal such as `="Acme Corp"` is valid. Require `variable` for `output`/`inOut`, using full `vars.<name>` without a leading `=`. `required` is optional. Make `outcomes[]` entries `{ "id": "<slug>", "name": "<OutcomeName>", "type": "string", "isPrimary": <bool> }`; the first is primary and there is no `action` key.

### Step 3 — Write the Action Task in `caseplan.json`

Write an action node with `id`, `elementId`, `type: "action"`, `displayName`, `isRequired`, `shouldRunOnlyOnce`, `entryConditions[]`, and `data`:

```json
{
  "id": "<task id>",
  "elementId": "<stage id>-<task id>",
  "type": "action",
  "displayName": "<canvas label>",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "entryConditions": [
    {
      "id": "<condition id>",
      "displayName": "Entry Rule 1",
      "rules": [[{ "id": "<rule id>", "rule": "current-stage-entered" }]]
    }
  ],
  "data": {
    "taskTitle": "<assignee message>",
    "context": [
      { "name": "hitlType", "type": "string", "value": "quick" },
      { "name": "taskTitle", "type": "string", "value": "<same assignee message>" },
      { "name": "labels", "type": "string" },
      { "name": "priority", "type": "string", "value": "Low" },
      { "name": "actionCatalogName", "type": "string" },
      { "name": "enableActionableNotifications", "type": "boolean", "value": "false" },
      { "name": "assignmentCriteria", "type": "string", "value": "user" },
      { "name": "recipient", "type": "json", "body": { "Type": 2, "Value": "<email>" } },
      { "name": "_schemaFileId", "type": "string", "value": "<placeholder UUID v4>" },
      { "name": "hitlSchemaId", "type": "string", "value": "<schemaId>" }
    ],
    "inputs": [
      { "name": "invoiceid", "type": "string", "displayName": "Invoice ID", "target": "bodyField", "value": "=vars.invoiceIdVar" },
      { "name": "amount", "type": "number", "displayName": "Amount", "target": "bodyField", "value": "=vars.amountVar" }
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

Populate `inputs[]` with one entry per input field: `name` = field `id`, `type`, `displayName`, `target: "bodyField"`, and `value` = the `.hitl.json` `binding`. Populate `outputs[]` with one entry per output field having a `variable`, plus one always-present `Action` entry whose `options[]` mirrors `outcomes[]` as `{ "value": "<name>", "label": "<name>" }` pairs. `Action` represents the selected outcome.

Set `inputSchema` to draft-07 JSON Schema with `properties` keyed by input field IDs and values `{ "type": "<field type>", "title": "<field label>" }`. Both task-level representations and `.hitl.json` are required; omitting either prevents Studio Web’s “Edit Schema” canvas from opening.

Context rules: `hitlType` is `"quick"`; `hitlSchemaId` exactly matches the file’s `schemaId`; `taskTitle` appears in both locations; `labels` and `actionCatalogName` have no `value`; priority is `"Low" | "Medium" | "High" | "Critical"`; leave `enableActionableNotifications` as string `"false"` unless notifications are requested; `assignmentCriteria` is `"user"` for an email and may omit `value` or the entry for a group. Recipient forms are `{ "Type": 2, "Value": "<email>" }`, `{ "Type": 1, "Value": "<group>" }`, or `{ "Type": 3, "Value": "=vars.<varId>" }` for runtime assignment.

`_schemaFileId` is a backend-assigned foreign key, not an authored UUID, and no `uip` CLI command resolves it. Never block: use a fresh UUID v4 placeholder, validate, and report that Studio Web editing requires reconciliation. If requested:

1. Run `uip solution upload` once with the placeholder.
2. Look up the real ID with `GET /api/Project/{projectId}/FileOperations/Structure`, matching the `.hitl.json` filename.
3. Patch `_schemaFileId` with the real ID.
4. Push only the corrected file with `PUT /api/Project/{projectId}/FileOperations/File/{fileId}`; do not run another whole-project `uip solution upload`, because it remints file IDs.

### Step 4 — Discover Upstream Variables

Read the flat top-level `variables` field; it has no `root` wrapper:

```json
{
  "inputs": [ { "id": "<varId>", "name": "<name>", "type": "string" } ],
  "outputs": [],
  "inputOutputs": []
}
```

For cross-task references, source values from upstream task `outputs[].var`. Follow [bindings-and-expressions.md](../../uipath-maestro-case/references/bindings-and-expressions.md). Do not modify top-level `bindings[]` for QuickForm.

## Path 2 — App-Based Action Task (deployed Action Center app)

The deployed app defines the form; inputs are shown to the human and outputs are available downstream.

### Step 1 — Discover the App

Run:

```bash
uip maestro case registry pull
uip maestro case registry search --type action-apps --output json
uip maestro case registry get "<app-name>" --type action-apps --output json
```

If CLI search fails for action apps, inspect `~/.uipcli/case-resources/action-apps-index.json` directly. Use `id` rather than `entityKey`, `deploymentTitle` rather than `name`, and `deploymentFolder.fullyQualifiedName` for the folder path.

### Step 2 — Get the Input/Output Schema

Run `uip maestro case tasks describe --type action --id "<action-app-id>" --output json` and capture both `inputs[]` and `outputs[]`.

### Step 3 — Write Root-Level Bindings

Add and deduplicate two top-level `bindings[]` entries by `(default + resource + resourceKey)`: one for `name` and one for `folderPath`.

```json
{
  "id": "b<8 chars>",
  "name": "name",
  "type": "string",
  "resource": "app",
  "resourceKey": "<folderPath>.<deploymentTitle>",
  "propertyAttribute": "name",
  "default": "<deploymentTitle>"
}
```

The `folderPath` entry has the same shape with `name: "folderPath"`, `propertyAttribute: "folderPath"`, and the folder as `default`. Binding IDs are `b` + 8 chars. Follow [bindings/impl-json.md](../../uipath-maestro-case/references/plugins/variables/bindings/impl-json.md).

### Step 4 — Write the Task

Write `type: "action"`, `isRequired`, `shouldRunOnlyOnce`, `entryConditions[]`, and:

```json
{
  "data": {
    "taskTitle": "<assignee message>",
    "name": "=bindings.<name-binding-id>",
    "folderPath": "=bindings.<folder-binding-id>",
    "actionCatalogName": "<deploymentTitle>",
    "assignmentCriteria": "user",
    "recipient": { "Type": 2, "Value": "<email>" },
    "context": [{ "name": "hitlType", "type": "string", "value": "custom" }],
    "inputs": [],
    "outputs": []
  }
}
```

Populate `data.inputs[]` and `data.outputs[]` from `tasks describe`. `data.name` and `data.folderPath` must be `=bindings.<id>` references, never literals. App-based tasks have no schema file: write `hitlType: "custom"` and never write `_schemaFileId` or `hitlSchemaId`. For full `inputs[]`/`outputs[]` variable shapes, see [action/impl-json.md](../../uipath-maestro-case/references/plugins/tasks/action/impl-json.md).

## Post-Write Verification

Run:

```bash
uip maestro case validate <caseplan.json> --output json
```

For QuickForm, confirm the adjacent `.hitl.json` has `title`, unified `fields[]`, `outcomes[]`, no `action` key, and `schemaId`; the task has `type: "action"`, `displayName`, non-empty matching `data.taskTitle` and context `taskTitle`, `hitlType: "quick"`, `_schemaFileId`, matching `hitlSchemaId`, required context entries, populated task `inputs[]`/`outputs[]`, `inputSchema`, no `actionCatalogName` value, and no new top-level bindings. Confirm schema fields and task representations mirror each other.

For App-based, confirm `type: "action"`, non-empty `data.taskTitle`, `data.name` and `data.folderPath` beginning `=bindings.`, `hitlType: "custom"`, no `_schemaFileId`/`hitlSchemaId`, two app bindings with `propertyAttribute` values `name` and `folderPath`, and matching `actionCatalogName`/`deploymentTitle`.

Both paths require task `entryConditions[]`, such as `current-stage-entered`; otherwise validation fails with `Task has no entry rules`. This is a case-structural requirement. If validation reports errors, diagnose and fix them before reporting success. Surface unrelated errors, such as `Case has no completion rules` in a pre-existing case, rather than suppressing them. Report the created files/task, validation result, any placeholder `_schemaFileId` reconciliation requirement, and schema-adjustment guidance.

## Downstream Output Access

| Path | Access |
|---|---|
| QuickForm | Every `.hitl.json` `outputs[]`/`inOuts[]` field uses its full `variable` (`vars.<name>`); the selected outcome is the task’s `Action` output. |
| App-based | Every `data.outputs[]` entry is read with `=vars.<output.var>`. |

For QuickForm, downstream input values use `=vars.<name>`; for App-based, use `=vars.<output.var>`. Follow [bindings-and-expressions.md](../../uipath-maestro-case/references/bindings-and-expressions.md).
---
name: uipath-hitl-from-formtask
description: "Convert existing Action Center FormTask FormLayouts (Formio JSON) to HITL QuickForm nodes in a UiPath Flow. Migrates legacy form-based human review steps to the modern uipath.human-in-the-loop node. Use when user mentions FormTask, form layout, action center form, or wants to migrate an existing form."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath HITL from FormTask Skill

Converts an existing Action Center **FormTask FormLayout** (Formio JSON) into a HITL QuickForm node in a UiPath Flow. Use this skill when migrating legacy FormTask-based review steps to the modern `uipath.human-in-the-loop` node.

## When to Use This Skill

- User mentions "FormTask", "Form task", "form layout", "action center form", or "old form"
- User wants to **migrate** a FormTask to a Flow HITL node
- User has a FormLayout JSON (Formio format) and wants to convert it to QuickForm
- User is modernizing an existing Orchestrator process that uses FormTasks
- User says "I have an existing task/form, can I use it in my flow?"

---

## Step 0 — Obtain the FormLayout JSON

Ask the user for the FormLayout. One of three ways:

**Option A — User pastes the JSON directly.** Proceed to Step 1.

**Option B — Fetch from Orchestrator API:**
```bash
uip login status --output json   # confirm logged in
```
Then look up the FormTask by name in the task catalog. The API returns `formLayout` (Formio JSON) and `buttonNamesList`. See [references/formtask-api.md](references/formtask-api.md) for the exact endpoint and response shape.

**Option C — User provides only a task type name.** Ask: "Can you paste the FormLayout JSON, or should I look it up by name from your tenant?"

---

## Step 1 — Parse the FormLayout

A FormLayout is a Formio configuration. Its root structure is:
```json
{ "components": [ ...field definitions... ] }
```

Read all components recursively:
- **Containers** (`panel`, `well`, `fieldset`, `columns`) — recurse into `components[]`
- **Repeating rows** (`datagrid`, `editgrid`) — mark as **unsupported**, note to user
- **Leaf fields** — convert using the type map in Step 2

The `buttonNamesList` from the API (or a `submit`-type button inside `components`) provides the outcome names.

---

## Step 2 — Map Field Types

| Formio `type` | QuickForm `type` | Notes |
|---|---|---|
| `textfield`, `textarea`, `email`, `phoneNumber`, `url` | `text` | |
| `number`, `currency` | `number` | |
| `checkbox`, `radio` (boolean true/false) | `boolean` | |
| `datetime`, `day` | `date` | |
| `select` | `text` | Options become a hint in the field label; no enum support in QuickForm |
| `button` | — | Becomes an `outcome` (see Step 3) |
| `panel`, `well`, `fieldset`, `columns` | — | Container — recurse, do not emit a field |
| `datagrid`, `editgrid` | **unsupported** | Inform user; suggest flattening into individual output fields |
| `hidden` | `text` / `input` direction | Hidden fields are pre-populated read-only values; map to `input` direction |
| `content`, `htmlelement` | — | Display-only, skip |
| `signature` | `text` | Best-effort; note to user that signature capture is not supported in QuickForm |

---

## Step 3 — Determine Field Direction

For each leaf field, set `direction` based on Formio properties:

| Condition | Direction | Meaning |
|---|---|---|
| `disabled: true` OR `hidden: true` | `input` | Pre-filled, read-only; human sees it |
| `calculateValue` is set (computed) | `input` | Computed from other values |
| Standard input field, user edits it | `output` | Human fills it in |
| Pre-populated AND user can edit | `inOut` | Use when the field has both a binding and `required` or is always shown |

When in doubt for a migration, default to `inOut` — it preserves both pre-fill and editability.

---

## Step 4 — Map Outcomes

Formio outcomes come from `buttonNamesList` or `button`-type components:

- First button (typically "Submit") → `isPrimary: true`, `action: "Continue"`
- All other buttons → `isPrimary: false`, `action: "End"`
- Rename generic "Submit" → "Approve" if context implies an approval flow
- If `buttonNamesList` is empty / unavailable, default to `[{name: "Submit", isPrimary: true}]`

---

## Step 5 — Build the QuickForm Schema

Assemble the `--schema` JSON for `uip maestro flow hitl add`, or write the node JSON directly.

**Schema format** (for `--schema` option):
```json
{
  "title": "<derived from FormTask name or user>",
  "inputs":  [{"name": "<label>", "binding": "=js:$vars.<upstream>.<field>"}],
  "outputs": [{"name": "<label>", "variable": "<varName>", "required": true}],
  "inOuts":  [{"name": "<label>", "binding": "=js:$vars.<upstream>.<field>", "variable": "<varName>"}],
  "outcomes":[{"name": "Approve"}, {"name": "Reject"}]
}
```

For each field:
- `direction: input` → put in `inputs[]`, add `binding` if upstream variable is known
- `direction: output` → put in `outputs[]`, add `required: true` for mandatory fields
- `direction: inOut` → put in `inOuts[]`, add both `binding` and `variable`
- `name` = Formio `label` (human-readable, preserves capitalisation and spaces)

---

## Step 6 — Write the Node

### Via CLI (recommended for brownfield inserts):
```bash
uip maestro flow hitl add <path/to/file.flow> \
  --label "<task name>" \
  --priority <Low|Medium|High> \
  --schema '<schema-json>' \
  --output json
```

### Via direct JSON edit:
Read [uipath-human-in-the-loop references/hitl-node-quickform.md](../uipath-human-in-the-loop/references/hitl-node-quickform.md) for the full node JSON format, definition entry, edge wiring, and `variables.nodes` regeneration.

After writing, validate:
```bash
uip maestro flow validate <file.flow> --output json
```

---

## Step 7 — Report Conversion Summary

After writing the node, tell the user:

1. **Fields converted** — list each Formio field → QuickForm field (type, direction)
2. **Fields skipped** — any `datagrid`, `content`, `htmlelement`, `signature` fields and why
3. **Outcomes mapped** — list original button names → outcome names
4. **Bindings to wire** — `input` and `inOut` fields have placeholders; list the `$vars` paths the user must fill in from their flow context
5. **Validation result** — pass or errors

---

## Conversion Example

**Input FormLayout:**
```json
{
  "components": [
    {"label": "Invoice ID",   "key": "invoiceId",  "type": "textfield", "input": true, "disabled": true},
    {"label": "Amount",       "key": "amount",     "type": "number",    "input": true, "disabled": true},
    {"label": "Approved",     "key": "approved",   "type": "checkbox",  "input": true},
    {"label": "Notes",        "key": "notes",      "type": "textarea",  "input": true},
    {"label": "Submit",       "key": "submit",     "type": "button",    "action": "submit"}
  ]
}
```
`buttonNamesList: ["Approve", "Reject"]`

**Generated schema:**
```json
{
  "title": "Invoice Review",
  "inputs": [
    {"name": "Invoice ID", "binding": "=js:$vars.<upstream>.output.invoiceId"},
    {"name": "Amount",     "binding": "=js:$vars.<upstream>.output.amount"}
  ],
  "outputs": [
    {"name": "Approved", "variable": "approved", "required": true},
    {"name": "Notes",    "variable": "notes"}
  ],
  "outcomes": [
    {"name": "Approve"},
    {"name": "Reject"}
  ]
}
```

**CLI command:**
```bash
uip maestro flow hitl add InvoiceApproval/InvoiceApproval/InvoiceApproval.flow \
  --label "Invoice Review" \
  --schema '{"title":"Invoice Review","inputs":[{"name":"Invoice ID","binding":"=js:$vars.<upstream>.output.invoiceId"},{"name":"Amount","binding":"=js:$vars.<upstream>.output.amount"}],"outputs":[{"name":"Approved","variable":"approved","required":true},{"name":"Notes","variable":"notes"}],"outcomes":[{"name":"Approve"},{"name":"Reject"}]}' \
  --output json
```

---

## References

- **[Formio → QuickForm type map](references/formio-to-quickform.md)** — Full type table with edge cases
- **[FormTask API endpoints](references/formtask-api.md)** — How to fetch FormLayout from Orchestrator
- **[HITL QuickForm node JSON](../uipath-human-in-the-loop/references/hitl-node-quickform.md)** — Full node format for direct JSON editing

# Human-in-the-Loop

*Exact signatures, fields, and defaults: `hitl()`.*

Pause a Flow for a person with the default inline form, `'quick-form'`, `'action-app'`, or `'document-validation'`.

Signature: `hitl({ variant?: 'quick-form' | 'action-app' | 'document-validation', app?, document?, title?, priority?, labels?, recipient?, fields?, outcomes, outcomePorts?, exposeError?, legacyCompleted? })`.

```ts
.var('status', types.string)
.stepSwitch('review', hitl({ title: 'Review invoice',
  fields: [{ id: 'comment', type: 'text', direction: 'output' }],
  outcomes: ['Approve', 'Reject'] }), [
  { value: 'Approve', body: (b) => b.step('pay', script({ … }), { updates: { status: lit('approved') } }) },
  { value: 'Reject', body: (b) => b.step('notify', script({ … }), { updates: { status: lit('rejected') } }) },
])
.return({ status: v('status') })
```

## At a glance

With an assignee and a pre-filled `inOut` field:

```ts
.var('status', types.string)
.stepSwitch('review', hitl({ title: 'Review invoice',
  recipient: { assignee: { type: 'user', value: 'reviewer@acme.test' } },
  fields: [{ id: 'amount', type: 'number', direction: 'inOut', value: input('amount') }],
  outcomes: ['Approve', 'Reject'] }), [
  { value: 'Approve', body: (b) => b.step('proceed', script({ code: 'return "approved";' }),
      { updates: { status: lit('approved') } }) },
  { value: 'Reject', body: (b) => b.step('notify', script({ code: 'return "rejected";' }),
      { updates: { status: lit('rejected') } }) }])
.return({ status: v('status') })
```

Every outcome exits as `outcome-<slug>`. `.stepSwitch` routes one arm per outcome on default nodes, quick-forms, and pinned tasks. Never combine it with `outcomePorts: false` (STEP_SWITCH_NO_EXITS: no ports to route). Drop the flag to get an arm per outcome. Keeping it means routing on `out('<step>', 'Action')` downstream ("The decision as data" below), and that branch must send every outcome value somewhere: an unhandled `Reject` continues down the main path. Arms act like `.switch()` arms: `.return()` is terminal, otherwise they converge and the next step receives every reaching arm. Assign Flow variables with `{ updates }` in arms and read them in the single `.return()`.

Default-node tasks with multiple outcomes route per outcome. A plain `.step()` continues every outcome when `variant: 'quick-form'`, `outcomePorts: false`, `{ version: '1.0' }`, one outcome, or all outcomes have `action: 'End'`. `outcomePorts: true` or `.stepSwitch` restores per-outcome routing for quick-form and pinned tasks, never with `outcomePorts: false`. `hitl({ variant: 'quick-form', outcomes: ['Approve', 'Reject'] })` followed by `.step('log', …)` emits `outcome-approve → log` and `outcome-reject → log`. On per-outcome tasks, `.step()` puts the FIRST outcome on the main path; use `.stepToList` for the others, never the FIRST. Otherwise all outcomes continue to the next step and the decision is data via `out('<step>', 'Action')`. The default node uses definition 1.1; quick-form uses 1.0; `exposeError: true` exposes `out('<step>', 'error')` and selects definition 1.2 on the default node.

## Delivery, fields, and routing

- `recipient` is `{ channels?, assignee: { type, value? }, connections? }`. Channels: `'Slack' | 'teams' | 'Email' | 'ActionCenter'` (Teams is lowercase `'teams'`). Assignee types: `user`, `group`, `staticEmail`, `staticGroupName`, `workload`, `roundRobin`, `custom`. Omit `recipient` for default channels: Email + Action Center on default and `'quick-form'`; Action Center alone on `'action-app'` and `'document-validation'`. Omitted recipients and assignees without `value` leave tasks unassigned in their folder. `user` and `staticEmail` require `value`; otherwise `check` warns `HITL_RECIPIENT_NO_USER` with `@uipath/maestro-builder-sdk` 6.61.1 or later. Older SDK silence does not make the assignee valid.
- `labels` is one comma-separated string shown in Action Center.
- Field `direction` is `'input'` (shown), `'output'` (asked), or `'inOut'` (pre-filled/editable; provide `value`; the reviewed value returns at its id).
- An asked field writes to the Flow variable named by `variable` (name only, no `vars.` prefix), defaulting to its field id. Read it with `v('<variable>')`; bind shown fields with `value: v('<variable>')`. Studio Web names it `<Step>_<field>` (`variable: 'P_comments'` writes `vars.P_comments`); preserve decompiled names or reads fail `EXPR_UNDECLARED_REF`. `check` reports `HITL_FIELD_VARIABLE` for a `vars.` prefix, dotted path, or `variable` on a non-`direction: 'output'` field. The answer is also always `out('<step>', '<id>')`. This needs `@uipath/maestro-builder-sdk` 6.44.0 or later; older SDKs ignore `variable`, write `vars.<id>`, cause `EXPR_UNDECLARED_REF`, and warn on decompile that the designer row cannot be written back
<!--skill-flavor:field-variable-sdk-upgrade:start-->
  — upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:field-variable-sdk-upgrade:end-->
- Field `type` is one of the 11 quick-form types: `'string'`, `'number'`, `'integer'`, `'float'`, `'double'`, `'boolean'`, `'date'`, `'datetime'`, `'file'`, `'object'`, `'array'`. `'text'` and `'date-time'` are accepted older spellings of `'string'`/`'datetime'`; leave them unchanged in existing source; decompiled canvas forms preserve types except bound Flow-variable types such as `'string[]'` and `'string | null'`, which decompile to resolved types (`'array'`, `'string'`).
- Picker types are `'singleSelect'` and `'enum'` (single-choice dropdown, `string` answer) or `'multiSelect'` (multi-select, `array` answer), with `options: [{ id, value, label }]` and all keys required. Do not replace them with `'string'` or `'array'`. Decompiled forms preserve spellings and `options`; edit unless `flow decompile` warns about a field. This needs `@uipath/maestro-builder-sdk` 6.31.9 or later; older SDKs report `HITL_FIELD_TYPE_UNKNOWN` (do not follow their `type: 'string'` hint),
<!--skill-flavor:field-type-sdk-upgrade:start-->
  so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:field-type-sdk-upgrade:end-->

  ```ts
  fields: [{
    id: 'priority', type: 'singleSelect', direction: 'output',
    options: [{ id: 'opt-1', value: 'high', label: 'High' }, { id: 'opt-2', value: 'low', label: 'Low' }],
  }]
  ```
- Preserve platform field settings and shapes: `controlType` (`'text'`, `'textarea'`, `'numberInput'`, `'datePicker'`, `'dateAndTimePicker'`, `'checkbox'`, `'dropdown'`, `'radioGroup'`, `'multiSelect'`, `'checkboxGroup'`, `'fileUpload'`), `defaultValue` (string or multi-select list), `colSpan` (1 to 12), `rules` (`{ id, conditions: [{ when, is?, ... }], operator?, effects }`), `requiredMessage`, and `description`. Preserve `type: 'string', controlType: 'dropdown'`; removing `controlType` makes a text box. Invalid values produce `HITL_FIELD_SETTING_INVALID`, `FLOW_AGENT_ESCALATION_FIELD_SETTING_INVALID` on an agent quick-form escalation, or `INLINE_AGENT_ESCALATION_FIELD_SETTING_INVALID` on an SDK older than 6.88.2. These need `@uipath/maestro-builder-sdk` 6.35.0 or later; older SDKs drop them on decompile and do not write them on compile,
<!--skill-flavor:field-settings-sdk-upgrade:start-->
  so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:field-settings-sdk-upgrade:end-->

  ```ts
  fields: [{
    id: 'priority', label: 'Priority', type: 'string', direction: 'output', required: true,
    requiredMessage: 'Pick one', colSpan: 6, controlType: 'dropdown',
    options: [{ id: 'o1', value: 'high', label: 'High' }, { id: 'o2', value: 'low', label: 'Low' }],
    defaultValue: 'high',
  }]
  ```
- If `flow decompile` warns that a field key cannot be written back (for example `variable` other than `vars.<id>` or an undefined platform-schema key), leave the node untouched so merge preserves it, or edit its JSON in `.flow`; `flow decompile --strict` refuses it.

**Every outcome is its own exit.** The SDK never emits `completed` on a task with outcomes. Each outcome is `outcome-<slug>` (lowercase, non-alphanumerics become `-`) on the default node and quick-form at every definition version. The designer derives handles from `inputs.schema.outcomes` and shows manifest `completed` only when there are none (`flow-workbench`, `getEffectiveHitlHandleCustomization`). A stale `completed` edge is remapped by Studio Web and the converter to the PRIMARY outcome, losing other paths; `check` refuses it with `HITL_COMPLETED_PORT_GONE`. The only exception is `legacyCompleted: true`, written by decompile for an existing `completed` edge so an unedited round trip preserves it; `check` warns `HITL_LEGACY_COMPLETED`. Never add it yourself. If the task asks you to fix that task's routing, replace it with `outcomePorts: false` (every outcome continues) or route each outcome.

A decompiled outcome may be `{ name: 'Reject', id: 'outcome-1778015958049' }`; preserve its id, whose port is `outcome-outcome-1778015958049`. Route it with `.stepToList` by port; `.stepSwitch` arms match the name. New outcomes need no `id`. `variant: 'document-validation'` takes `document: { extractionResult, storageBucket?, documentId?, render?, taxonomy? }` and no `fields`; bind `extractionResult` to the upstream extract step's `ExtractionResult`. `render: 'custom'` requires `taxonomy` and takes `app`.

**Every outcome must be wired; prefer `.stepSwitch`.**

- `.stepSwitch(name, hitl({…}), arms)` has one arm per outcome, with `value` naming it; no tacit exit. Arms converge; a missing arm warns `STEP_SWITCH_EXIT_UNROUTED` rather than leaving an unedged port.
- `.step()` plus `.stepToList('outcome-<slug>', …)` applies to per-outcome tasks: the FIRST outcome is the main path and the rest are side arms. Side arms do not converge; each gets its own End, mapping every output from its variable. `NO_RETURN` warns when an arm leaves one unset. Never route the FIRST outcome with `.stepToList` (`flow-builder-sdk#741`).
- `.step()` on a non-per-outcome task continues every outcome to the next step on its own edge; read the decision with `out('<step>', 'Action')`. All outcome ports are occupied, so `.stepToList('outcome-…')` is refused with `HITL_OUTCOME_PORTS_OFF`; use `outcomePorts: true`, or `.stepSwitch` on quick-form or a pin (never with `outcomePorts: false`).
- `action: 'End'` gives an outcome its own End instead of the next step, or joins `.return()` when that is next. Runtime never reads `action`; only the graph ends the run. If every outcome is `action: 'End'`, nothing may follow except `.return()` and `check` reports `HITL_UNREACHABLE_AFTER`.
- Inside a `.parallel()` arm, this task cannot be the arm's last step and no outcome may be `action: 'End'`; the join waits for every incoming edge while only one outcome fires. `check` refuses these with `HITL_FAN_OUT_INTO_JOIN` and `HITL_END_OUTCOME_IN_PARALLEL`. Add a step after the task inside the arm so every outcome reaches it and only it reaches the join. `.stepSwitch` does not remove this: every outcome needs an arm, no arm may end in `.return()`, and an empty arm alongside an arm that runs another step is refused (`HITL_FAN_OUT_INTO_JOIN`) unless a common step follows the `.stepSwitch` inside the arm. Write `a.stepSwitch('review', …).step('record', …)` and put `.return()` after `.parallel()`.
- `'action-app'` and `'document-validation'` differ: outcomes live in the app, `completed` is the only designer handle, `.step()` leaves on it, and downstream routing uses `out('<step>', 'Action')`.

A default task with multiple outcomes routes per outcome; otherwise a single continuation can compile and `flow validate` answer `Valid` while the wrong shape fails at runtime or in a grader (`flow-builder-sdk#735`). Warning alone was insufficient (`#739` measured it firing three times while the unreachable artifact shipped); the graph shape changed. `check` still warns `HITL_OUTCOMES_UNREACHABLE` when every outcome continues to one step and nothing reads `out('<step>', 'Action')`. **The decision as data** — `.step()` then `.switch()` on `out('<step>', 'Action')`: use quick-form or `outcomePorts: false` when the decision is wanted as data, recorded in an output, or compared in one place. A single continuation with nothing reading `Action` is the `HITL_OUTCOMES_UNREACHABLE` case, not a third shape.

With `.stepToList`, an unrouted outcome can deploy then stall when selected (`HITL_OUTCOME_UNROUTED`). With `.stepSwitch`, it compiles to an End; that End maps only declared outputs from variables and `STEP_SWITCH_EXIT_UNROUTED` reports unset values. In `.parallel()` it would hang the join and is refused with `HITL_END_OUTCOME_IN_PARALLEL`. `action: 'End'` changes outcome behavior, not whether its handle needs an edge.

`flow validate` checks `outcome-<id>` against declared outcomes: a real outcome passes on every version, while an unknown one is refused with *Edge references undeclared source handle "outcome-nope"*. On 1.1/1.2 it also refuses `completed`; it does not refuse `completed` on 1.0 or quick-form nodes with outcomes, so `check` and the SDK still enforce the rule.

## Action App inputs and answers

For `variant: 'action-app'`, pass the app action schema as `app.actionSchema`. Preserve either spelling:

- Coded `action-schema.json`: each `inputs`, `outputs`, `inOuts`, and `outcomes` section is `{ type: 'object', properties: { <name>: { type, required? } } }`.
- Platform solution resource `spec.actionSchema` at `resources/solution_folder/app/codedAction/<App>.json`: each section is an array of `{ name, type: 'System.String', required, isList }`. It is a JSON string; parse it and pass the object or `check` refuses it with `HITL_APP_SCHEMA_INVALID`.

If neither file exists, ask the user for the schema; never write one by hand.

```ts
.step('review', hitl({
  variant: 'action-app',
  app: {
    name: 'InvoiceReview', key: appKey, folderPath: 'Shared',
    inputs: { invoiceAmount: input('invoice_amount'), variancePct: out('math', 'variance_pct') },
    actionSchema: {                       // the app's action-schema.json
      inputs: { type: 'object', properties: {
        invoiceAmount: { type: 'number', required: true },
        variancePct: { type: 'number', required: true } } },
      outputs: { type: 'object', properties: {
        reviewerComments: { type: 'string', required: true } } },
      outcomes: { type: 'object', properties: { Approve: { type: 'string' }, Reject: { type: 'string' } } },
    },
  },
  outcomes: ['Approve', 'Reject'],
}))
.return({ decision: out('review', 'Action'), comments: out('review', 'reviewerComments') })
```

Without it, every `app.inputs` value is typed and delivered as a string; `check` warns `HITL_APP_NO_SCHEMA`. It errors on undeclared input (`HITL_APP_INPUT_UNKNOWN`), unbound required input (`HITL_APP_INPUT_REQUIRED`), unavailable outcome (`HITL_APP_OUTCOME_UNKNOWN`), or invalid schema (`HITL_APP_SCHEMA_INVALID`). Schema `outputs` and `inOuts` are typed answer fields, so `out('<step>', '<field>')` passes `check`; without schema it fails `HITL_READ_UNKNOWN_FIELD`. Nested object `properties` are not checked.

Decompile preserves the schema: it prints `app.actionSchema` when that compiles to the node's exact `inputSchema`; otherwise, such as a hand-edited schema with `title`s, it prints the node schema as `app.inputSchema`. Preserve it and provide `actionSchema` or `inputSchema`, never both.

Needs `@uipath/maestro-builder-sdk` 6.59.1 or later; older SDKs lack `actionSchema` on `app`, so TypeScript rejects it (check that `dist/api-index.md` lists `PlatformActionSchema`),
<!--skill-flavor:action-schema-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:action-schema-sdk-upgrade:end-->

## Variant judgment

Use the explicitly named variant. Default and quick-form own fields in the Flow; action-app delegates to an already-deployed app or one in this solution. Resolve an app task's key, name, folder, and argument names from the same tenant resource and pass its schema as `app.actionSchema` ([Action App inputs and answers](#action-app-inputs-and-answers)).

A coded Action App in the SAME solution is not yet deployed to a folder. Use `location: 'in-solution'` and omit `folderPath`:

```ts
.step('review', hitl({
  variant: 'action-app',
  app: { name: '<App>', key: '<APP_RESOURCE_KEY>', location: 'in-solution' },
  outcomes: ['Approve', 'Reject'],
}))
```

- **Where the key comes from.**
<!--skill-flavor:app-sibling-register:start-->
  Run `uip solution projects add`, then run `uip solution resources refresh` to register the app project and refresh resources. The
<!--skill-flavor:app-sibling-register:end-->
  generated `resources/solution_folder/app/codedAction/<App>.json` maps `resource.key` to `key` and `resource.name` to `name`. Never invent the key; the full recipe is in [agent.md](agent.md#task-created-in-solution-coded-agent).
- Do not provide `folderPath` with `location: 'in-solution'`. A literal `'solution_folder'` reaches the engine and the task is refused; `check` reports `HITL_APP_LOCAL_HAS_FOLDER`. Decompiled in-solution tasks with folder `''` or `'solution_folder'` return as `location: 'in-solution'`. This differs from an agent escalation app ([agent-resources.md](agent-resources.md#escalation)), which is an agent resource and does carry `'solution_folder'`; do not transfer either rule.
- Needs `@uipath/maestro-builder-sdk` 6.66.2 or later; older SDKs reject `location` on `app` (type error and `check` asks for missing `folderPath`),
<!--skill-flavor:inso-app-sdk-upgrade:start-->
  so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:inso-app-sdk-upgrade:end-->
<!--skill-flavor:inso-app-uip-floor:start-->
  No `uip` build checked so far preserves the app folder when packing this task (1.204.0 and 1.205.0-preview.269 both drop it); the task then fails at runtime with `170004 Invalid input for the HITL task`. Tell the user that an in-solution app task needs a `uip` release carrying the fix, and do not retry the run.
<!--skill-flavor:inso-app-uip-floor:end-->

## Evidence boundary

Offline execution scripts the selected action and output fields, proving wiring and downstream routing only—not that a real task appeared or a person participated. Live evidence should preserve the Action Center task identity, human-selected outcome, supplied answers, and resumed path.

# Human-in-the-Loop

*Exact signatures, fields, and defaults: `hitl()`.*

Pause a Flow for a person with the default inline form, quick-form node, deployed Action App, or document-validation station.

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

Each outcome exits as `outcome-<slug>`; a task with outcomes never emits `completed`. On the default node, multiple outcomes route automatically. `.stepSwitch` provides one arm per outcome on the default node, quick-form, or pinned task; do not combine it with `outcomePorts: false` (`STEP_SWITCH_NO_EXITS`); drop the flag, or keep it and route on `out('<step>', 'Action')`, sending every outcome value somewhere: an unhandled `Reject` continues down the main path. Arms behave like `.switch()` arms: terminal `.return()` arms end, others CONVERGE, so later steps fan in. That is what makes the single `.return()` above correct, and what a flow VARIABLE is for: each arm assigns it with `{ updates }` and the one return reads it. Wire every outcome. A missing arm compiles to an End that leaves outputs unset (`STEP_SWITCH_EXIT_UNROUTED`); an unhandled `.stepToList` outcome stalls the run when picked (`HITL_OUTCOME_UNROUTED`); `action: 'End'` ends it instead but still needs an edge.

## At a glance

Use `.stepSwitch` for per-outcome routing. Use `.step()` followed by `.switch()` on `out('<step>', 'Action')` when the decision is deliberately data (recorded in an output, compared in one place); ask for it with quick-form or `outcomePorts: false` on the default node. Every outcome continuing to one step with nothing reading `Action` is the unreachable-outcomes case, not a third shape. A plain `.step()` continues the FIRST outcome on a default task that routes per outcome, and the others need routes; otherwise it continues EVERY outcome on separate edges. The latter applies only with `outcomePorts: false`, `variant: 'quick-form'`, `{ version: '1.0' }`, one outcome, or all outcomes having `action: 'End'`. Quick-form defaults to it; `outcomePorts: true` or `.stepSwitch` enables per-outcome routing while version remains 1.0. A default multi-outcome task otherwise uses definition 1.1. An explicit `{ version: '1.0' }` pin wins, keeping decompile → compile exact on a deployed flow; `outcomePorts: true` still routes per outcome on 1.0.

When `.step()` continues every outcome, an `action: 'End'` outcome goes to its own End (or joins the `.return()` when that is the next step); the runtime never reads `action`, so only the graph ends the run. If every outcome is `action: 'End'`, nothing may follow except `.return()` (`HITL_UNREACHABLE_AFTER`). Do not route the FIRST outcome with `.stepToList`; its port is already the main path (flow-builder-sdk#741). On a task that does not route per outcome, `.stepToList('outcome-…')` is refused (`HITL_OUTCOME_PORTS_OFF`); use `outcomePorts: true` or `.stepSwitch`, never with `outcomePorts: false`.

## Delivery, fields, and routing

- `recipient` is `{ channels?, assignee: { type, value? }, connections? }`. Channels: `'Slack' | 'teams' | 'Email' | 'ActionCenter'`; assignee types: `user`, `group`, `staticEmail`, `staticGroupName`, `workload`, `roundRobin`, `custom`. Omit it for default channels: Email + Action Center on default and `'quick-form'`; Action Center only on `'action-app'` and `'document-validation'`. Omitted recipients and assignees without `value` create an unassigned task. `user` and `staticEmail` require `value`; otherwise `check` warns `HITL_RECIPIENT_NO_USER` with `@uipath/maestro-builder-sdk` 6.61.1 or later; absence of an older-SDK warning does not prove validity.
- `labels` is one comma-separated string shown in Action Center.
- Field `direction` is `'input'` (shown), `'output'` (asked), or `'inOut'` (pre-filled/editable; provide `value`). The reviewed value returns at its field id. An asked field writes to Flow variable `variable` (name only, no `vars.` prefix), defaulting to its field id; read it with `v('<variable>')`, or bind a shown field with `value: v('<variable>')`. Studio Web names it `<Step>_<field>`; `variable: 'P_comments'` writes `vars.P_comments`. Preserve decompiled names or downstream reads fail `EXPR_UNDECLARED_REF`. `check` reports `HITL_FIELD_VARIABLE` for a `vars.` prefix, dotted path, or `variable` on a non-`direction: 'output'` field. The answer is also always `out('<step>', '<id>')`. SDK 6.44.0+ is required; older SDKs ignore `variable`, write `vars.<id>`, cause `EXPR_UNDECLARED_REF`, and decompile warns it cannot write the designer row back
<!--skill-flavor:field-variable-sdk-upgrade:start-->
  — upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:field-variable-sdk-upgrade:end-->
- Field `type` is one of 11 quick-form types: `'string'`, `'number'`, `'integer'`, `'float'`, `'double'`, `'boolean'`, `'date'`, `'datetime'`, `'file'`, `'object'`, `'array'`. `'text'` and `'date-time'` are accepted as older spellings of `'string'` / `'datetime'`; leave them as they are in existing source; bound-variable types such as `'string[]'` and `'string | null'` decompile as `'array'` and `'string'`.
- Picker types are `'singleSelect'` and `'enum'` (single-choice dropdown, `string` answer) or `'multiSelect'` (multi-select, `array` answer), with `options: [{ id, value, label }]` and all three keys required. Never replace them with `'string'` or `'array'`; preserve spellings and options in decompiled forms. SDK 6.31.9+ is required; older SDKs report `HITL_FIELD_TYPE_UNKNOWN` (ignore its `type: 'string'` hint),
<!--skill-flavor:field-type-sdk-upgrade:start-->
  so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:field-type-sdk-upgrade:end-->
- A field also takes the platform's settings keys, with the platform's names and shapes: `controlType` (`'text'`, `'textarea'`, `'numberInput'`, `'datePicker'`, `'dateAndTimePicker'`, `'checkbox'`, `'dropdown'`, `'radioGroup'`, `'multiSelect'`, `'checkboxGroup'`, `'fileUpload'`), `defaultValue` (string or multi-select list), `colSpan` (1 to 12), `rules` (`{ id, conditions: [{ when, is?, ... }], operator?, effects }`), `requiredMessage`, and `description`. Preserve `type: 'string', controlType: 'dropdown'` and its `options`; removing `controlType` makes a text box. Decompiled canvas forms keep these keys and stay editable. `check` reports invalid values as `HITL_FIELD_SETTING_INVALID`, `FLOW_AGENT_ESCALATION_FIELD_SETTING_INVALID` on an agent quick-form escalation, or `INLINE_AGENT_ESCALATION_FIELD_SETTING_INVALID` on an SDK older than 6.88.2. SDK 6.35.0+ is required; older SDKs drop these on decompile and omit them on compile,
<!--skill-flavor:field-settings-sdk-upgrade:start-->
  so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:field-settings-sdk-upgrade:end-->

  A row key the SDK has no option for (a `variable` other than `vars.<id>`,
  a key the platform's schema does not define, a `binding` on an asked
  field) comes back in the field's `extra`, for instance
  `extra: { variable: 'vars.order.note' }`. Compile writes it back as it
  was, so you can edit the node; keep `extra` as decompile printed it.
  To change a key that rides in `extra`, change it in `extra`: setting the
  typed option of the same name next to it is refused
  (`HITL_FIELD_EXTRA_CONFLICT`). Never add `extra` to a field you write: use
  the typed keys above.
  `flow decompile` still warns that a key "cannot write back" for a value
  the platform refuses or drops itself (a `colSpan` off the grid, an
  unknown key inside `options`); editing that node drops that key.
  Needs `@uipath/maestro-builder-sdk` 6.104.1 or later (its
  `dist/api-index.md` lists `FormFieldRowExtra`); an older SDK warns for
  every such key instead: leave that node untouched so merge keeps the
  original, or edit its JSON in the `.flow` directly.

Each outcome gets `outcome-<slug>` (lowercase; non-alphanumerics become `-`) on the default node and quick-form at every definition version. The designer derives handles from `inputs.schema.outcomes` and shows manifest `completed` only when none exist (`flow-workbench`, `getEffectiveHitlHandleCustomization`). A `completed` edge on a task with outcomes is stale and is remapped to the PRIMARY outcome by Studio Web and the converter, losing other paths; `check` refuses it (`HITL_COMPLETED_PORT_GONE`). The only exception is existing `legacyCompleted: true`: decompile writes it when the task already leaves on `completed`, no-edit round trips preserve it, and `check` warns `HITL_LEGACY_COMPLETED`; never add it. If the task asks you to fix that task's routing, replace it with `outcomePorts: false` or explicit outcome routes. A decompiled outcome may be `{ name: 'Reject', id: 'outcome-1778015958049' }`; preserve it, route its port as `outcome-outcome-1778015958049` with `.stepToList`, and use the name for `.stepSwitch`. New outcomes need no `id`. `exposeError: true` additionally exposes `out('<step>', 'error')` and selects definition 1.2 (default node only).

Wire every outcome:

| Shape | Behavior |
| --- | --- |
| `.stepSwitch(name, hitl({…}), arms)` | One arm per outcome, `value` naming it; no tacit exit; arms converge; missing arms warn `STEP_SWITCH_EXIT_UNROUTED`. |
| `.step()` + `.stepToList('outcome-<slug>', …)` on a per-outcome task | FIRST outcome is the main path; other arms do not converge and each gets its own End, mapping every output from its variable (`NO_RETURN` warns if an arm leaves one unset). |
| `.step()` on a non-per-outcome task | Every outcome continues to the next step on its own edge; route later with `out('<step>', 'Action')`. |

A default multi-outcome task routes per outcome unless one of the five conditions in `## At a glance` applies. In `.parallel()`, the task must not be the arm's last step and no outcome may be `action: 'End'`; only one outcome fires, so the join would wait forever. `check` refuses these as `HITL_FAN_OUT_INTO_JOIN` (last step) and `HITL_END_OUTCOME_IN_PARALLEL` (`End` outcome). Add a step after it inside the arm so all outcomes reach that step, including after `.stepSwitch`; do not end an arm with `.return()`, and put `.return()` after `.parallel()`. An empty switch arm plus another arm ending in a step is also refused as `HITL_FAN_OUT_INTO_JOIN`; a missing switch arm, or one ending in `.return()`, is refused as `HITL_END_OUTCOME_IN_PARALLEL`; give every outcome an arm.

Action-app and document-validation outcomes live in the app; `completed` is their only designer handle and `.step()` leaves on it. Route downstream with `out('<step>', 'Action')`. An approve/reject task whose outcomes all lead to one place still compiles and `flow validate` answers `Valid`, so the mistake surfaces only at runtime; `check` warns `HITL_OUTCOMES_UNREACHABLE` when all outcomes continue to one step and nothing reads `Action`; warnings do not replace routing. `flow validate` accepts a declared `outcome-<id>` edge on every version and refuses undeclared handles with *Edge references undeclared source handle "outcome-nope"*. On a 1.1/1.2 node with outcomes, `flow validate` refuses `completed`, but not on 1.0 or quick-form; use `check` and the SDK rules.

`variant: 'document-validation'` takes `document: { extractionResult, storageBucket?, documentId?, render?, taxonomy? }`, no `fields`; bind `extractionResult` to the upstream extract step's `ExtractionResult`. `render: 'custom'` requires `taxonomy` and takes `app`.

## Action App inputs and answers

For `variant: 'action-app'`, pass the app schema as `app.actionSchema`, beside `name`, `key`, `folderPath`, and `inputs` (keys matching the schema's inputs), using either spelling unchanged:

- Coded action app `action-schema.json`: each `inputs`, `outputs`, `inOuts`, and `outcomes` section is `{ type: 'object', properties: { <name>: { type, required? } } }`.
- Platform action schema from solution resource `spec.actionSchema` (`resources/solution_folder/app/codedAction/<App>.json`): each section is an array of `{ name, type: 'System.String', required, isList }`. It is a JSON string; parse and pass the object or `check` refuses it (`HITL_APP_SCHEMA_INVALID`).

If neither file exists, ask the user for the schema; never write one by hand. Without a schema, every `app.inputs` value reaches the app as a `string`, and `check` warns `HITL_APP_NO_SCHEMA`. `check` errors on undeclared inputs (`HITL_APP_INPUT_UNKNOWN`), unbound required inputs (`HITL_APP_INPUT_REQUIRED`), unknown outcomes (`HITL_APP_OUTCOME_UNKNOWN`), or invalid schema (`HITL_APP_SCHEMA_INVALID`). Schema `outputs` and `inOuts` are typed answer fields readable via `out('<step>', '<field>')`; without the schema, such reads fail `HITL_READ_UNKNOWN_FIELD`. Nested object `properties` are not checked.

Decompile preserves the schema: it prints `app.actionSchema` when it compiles exactly to the node's `inputSchema`; otherwise, including hand-edited `title`s, it prints the node schema as `app.inputSchema`. Preserve that form and provide `actionSchema` or `inputSchema`, not both.

SDK 6.59.1+ is required; older SDKs lack `actionSchema` on `app`, so TypeScript rejects it (check that `dist/api-index.md` lists `PlatformActionSchema`),
<!--skill-flavor:action-schema-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:action-schema-sdk-upgrade:end-->

## Variant judgment

Use the scenario's explicit variant. Default and quick-form own fields in the Flow; action-app delegates to a deployed app or an app in this solution. For app tasks, resolve key, name, folder, and argument names from the same tenant resource and pass its schema as `app.actionSchema` ([Action App inputs and answers](#action-app-inputs-and-answers)).

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
  Register the app project and refresh resources (`uip solution projects add`, then `uip solution resources refresh`). The
<!--skill-flavor:app-sibling-register:end-->
  generated `resources/solution_folder/app/codedAction/<App>.json` carries `resource.key` → `key` and `resource.name` → `name`. Never invent the key; the full recipe is in [agent.md](agent.md#task-created-in-solution-coded-agent).
- Never give `folderPath` with `location: 'in-solution'`; a literal `'solution_folder'` reaches the engine and is refused; `check` refuses any non-empty `folderPath` (`HITL_APP_LOCAL_HAS_FOLDER`). Decompiled in-solution tasks with folder `''` or `'solution_folder'` return as `location: 'in-solution'`. Do not transfer this rule to an agent escalation's app, which is an agent resource and does carry `'solution_folder'` ([agent-resources.md](agent-resources.md#escalation)).
- SDK 6.66.2+ is required; older SDKs reject `location` on `app` and `check` asks for missing `folderPath`,
<!--skill-flavor:inso-app-sdk-upgrade:start-->
  so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:inso-app-sdk-upgrade:end-->
<!--skill-flavor:inso-app-uip-floor:start-->
  No `uip` build checked so far preserves the app folder when packing this task (1.204.0 and 1.205.0-preview.269 both drop it), causing runtime `170004 Invalid input for the HITL task`. Tell the user an in-solution app task needs a `uip` release carrying the fix; do not retry the run.
<!--skill-flavor:inso-app-uip-floor:end-->

## Evidence boundary

Offline execution scripts the selected action and output fields; it proves wiring and downstream routing, not that a real task appeared or a person participated. Live evidence should preserve the Action Center task identity, human-selected outcome, supplied answers, and resumed path.

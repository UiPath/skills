# Human-in-the-Loop

*Exact signatures, fields, and defaults: `hitl()`.*

Pause a Flow for a person using the default inline form, the quick-form node
type, a deployed Action App, or a document-validation station.

Signature:
`hitl({ variant?: 'quick-form' | 'action-app' | 'document-validation', app?,
document?, title?, priority?, labels?, recipient?, fields?, outcomes,
outcomePorts?, exposeError?, legacyCompleted? })`.

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

Every outcome is its own exit, `outcome-<slug>`. On the default node, more than
one outcome routes per outcome by itself — there is no flag to remember and no
decision node in the middle. On quick-form, with `outcomePorts: false`, or with a
pinned `{ version }`, a plain `.step()` after the task continues EVERY outcome to
the next step instead, each on its own edge.

`.stepSwitch` is how you route them: one arm per outcome, none of them the tacit
next step. It works on the default node, on quick-form and on a pinned task.
Arms behave like `.switch()`'s — one that ends in `.return()` is terminal, and one
that does not CONVERGES, so the step after the `.stepSwitch` fans in from every
arm that reaches it.
That is what makes the single `.return()` above correct, and what a flow VARIABLE
is for: each arm assigns it with `{ updates }` and the one return reads it, instead
of the return having to work out which arm ran.

## At a glance

Pause for a person: an inline form, quick form, deployed Action App, or a
document-validation station.

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

Every outcome is its own exit (`outcome-<slug>`); the SDK never emits `completed` on a task that has outcomes, and every outcome must be wired. `.stepSwitch` gives each one an arm — no tacit exit, arms converge like `.switch`'s, a missing arm warns — on the default node, on quick-form, or on a pinned task. After a default-node task with more than one outcome, `.step` + `.stepToList` is the older shape where the FIRST outcome continues the main path. After quick-form, `outcomePorts: false` or `{ version: '1.0' }`, a plain `.step()` continues EVERY outcome to the next step, each on its own edge, where you route on `out('review', 'Action')`.

## Delivery, fields, and routing

- `recipient` is `{ channels?, assignee: { type, value? }, connections? }` —
  channels are `'Slack' | 'teams' | 'Email' | 'ActionCenter'` (Teams really is
  the lowercase `'teams'`); assignee types are `user`, `group`, `staticEmail`,
  `staticGroupName`, `workload`, `roundRobin`, `custom`. Omit the whole object
  for the platform default (Email + Action Center, assigned to a group).
- `labels` is one comma-separated string, shown in Action Center.
- A field's `direction` is `'input'` (shown), `'output'` (asked), or `'inOut'`
  (pre-filled AND editable — give it a `value`; the reviewed value comes back
  at the field's own id).
- An asked field's answer also lands in a Flow variable, named by `variable`
  (the name only, no `vars.` prefix) and defaulting to the field id. Later steps
  read it as `v('<variable>')`, or bind a shown field to it with
  `value: v('<variable>')`. Studio Web names it `<Step>_<field>`
  (`variable: 'P_comments'` writes `vars.P_comments`), and a decompiled canvas
  form keeps that name — leave it as written, or every downstream read fails
  `EXPR_UNDECLARED_REF`. `check` reports `HITL_FIELD_VARIABLE` for a `vars.`
  prefix, a dotted path, or a `variable` on a shown field. The answer is always
  `out('<step>', '<id>')` too. Needs `@uipath/maestro-builder-sdk` 6.42.0 or
  later; an older SDK's decompile warns that it cannot write the row back.
- A field's `type` is one of the platform's 11 quick-form types: `'string'`,
  `'number'`, `'integer'`, `'float'`, `'double'`, `'boolean'`, `'date'`,
  `'datetime'`, `'file'`, `'object'`, `'array'`. `'text'` and `'date-time'` are
  accepted as older spellings of `'string'` / `'datetime'`; leave them as they
  are in existing source. A decompiled canvas form keeps its types as written,
  except a type copied from a bound Flow variable (`'string[]'`,
  `'string | null'`), which decompiles to the type it resolves to (`'array'`,
  `'string'`).
- A picker field uses a choice-control spelling, with its choices in `options`
  (`{ id, value, label }` each, all three required): `'singleSelect'` and
  `'enum'` are a single-choice dropdown (a `string` answer), `'multiSelect'` a
  multi-select (an `array` answer). Never change one to `'string'` or
  `'array'`: the form loses its picker. A decompiled canvas form keeps these
  spellings and their `options`, and you can edit the node unless a field has
  one of the keys below. Needs `@uipath/maestro-builder-sdk` 6.31.9 or later;
  an older SDK reports `HITL_FIELD_TYPE_UNKNOWN` (do not follow its
  `type: 'string'` hint), so upgrade with
  `npm install -g @uipath/maestro-builder-sdk@latest`.

  ```ts
  fields: [{
    id: 'priority', type: 'singleSelect', direction: 'output',
    options: [{ id: 'opt-1', value: 'high', label: 'High' }, { id: 'opt-2', value: 'low', label: 'Low' }],
  }]
  ```

  A canvas field row can also carry `controlType`, `defaultValue`, `colSpan`,
  `rules`, `requiredMessage` or `description`. Decompile does not keep those
  yet, so editing the node drops them from every field on the form. If any
  field in the `.flow` has one of them, leave that node untouched so merge
  keeps the original, or edit that node's JSON in the `.flow` directly.
- **Every outcome is its own exit — the SDK never emits `completed` on a task
  that has outcomes.** Each outcome gets `outcome-<slug>` (the name lowercased,
  non-alphanumerics to `-`). This holds on the default node and on quick-form,
  at every definition version, because it is what the designer draws: it derives
  one handle per entry in `inputs.schema.outcomes` and shows the manifest's
  `completed` placeholder only when there are none (flow-workbench,
  `getEffectiveHitlHandleCustomization`). A `completed` edge on a task with
  outcomes is stale: Studio Web and the converter remap it to the PRIMARY
  outcome, so every other outcome loses its path. `check` refuses it
  (HITL_COMPLETED_PORT_GONE). The one exception is `legacyCompleted: true`:
  decompile writes it for a file whose task already leaves on `completed`, so
  a no-edit round trip writes that edge back unchanged, and `check` warns
  (HITL_LEGACY_COMPLETED). Never add it yourself. If the task asks you to fix
  that task's routing, replace it with `outcomePorts: false` (every outcome
  continues) or route each outcome. A decompiled task the designer drew may write
  an outcome as `{ name: 'Reject', id: 'outcome-1778015958049' }`: the `id`
  keeps the original outcome id, so its port is `outcome-outcome-1778015958049`
  (route it with `.stepToList` by that port; `.stepSwitch` arms still match the
  name), and the merged edges match the original node. Leave it as it is; new
  outcomes need no `id`.
  `exposeError: true` additionally exposes
  `out('<step>', 'error')` and selects the 1.2 definition (default node only).

  **Every outcome must be wired**, and there are three ways. Prefer the first:

  | | |
  | --- | --- |
  | `.stepSwitch(name, hitl({…}), arms)` | one arm per outcome, `value` naming the outcome. No tacit exit, arms converge, and a missing arm is a warning (STEP_SWITCH_EXIT_UNROUTED) rather than a port with no edge. |
  | `.step()` + `.stepToList('outcome-<slug>', …)`, on a task that routes per outcome | the FIRST outcome continues the main path and the rest are side arms. Those arms do NOT converge — each gets an End of its own, which maps every output from its variable (NO_RETURN warns when the arm leaves one unset). |
  | `.step()`, on a task that does not route per outcome | every outcome continues to the next step, each on its own edge. The decision reaches the flow as data: `out('<step>', 'Action')`. |

  Do not route the FIRST outcome with `.stepToList`: its port is already taken by
  the main path (flow-builder-sdk#741). After a task that does not route per
  outcome EVERY outcome port is taken, so `.stepToList('outcome-…')` there is
  refused (HITL_OUTCOME_PORTS_OFF) — use `.stepSwitch`, or `outcomePorts: true`.

  **So `.step()` means one of two things.** After a task that routes per outcome,
  the FIRST outcome continues and the others need routes. After any other task,
  every outcome continues. For example, `hitl({ variant: 'quick-form', outcomes:
  ['Approve', 'Reject'] })` followed by `.step('log', …)` emits
  `outcome-approve → log` and `outcome-reject → log`.

  A default-node task with more than one outcome routes per outcome, on its 1.1
  definition. Five things make `.step()` continue every outcome instead, and only
  these:

  | | `.step()` continues every outcome because |
  | --- | --- |
  | `outcomePorts: false` | you asked for it: the decision is wanted as data |
  | `variant: 'quick-form'` | that is quick-form's default. `outcomePorts: true` or `.stepSwitch` route it per outcome, and its version stays 1.0 |
  | `{ version: '1.0' }` | an explicit pin wins, which keeps `decompile` → `compile` exact on a deployed flow. `outcomePorts: true` with the pin routes per outcome on the 1.0 node |
  | one outcome | an acknowledgement, not a choice |
  | every outcome `action: 'End'` | each outcome gets its own End, so nothing may follow the task except a `.return()` (HITL_UNREACHABLE_AFTER) |

  An `action: 'End'` outcome in that fan-out goes to an End node of its own
  instead of into the next step, or joins the `.return()` when that is the next
  step. The flow runtime never reads `action`, so only the graph can end the run
  on that outcome.

  Inside a `.parallel()` arm, such a task must not be the arm's last step, and
  none of its outcomes may be `action: 'End'`. The join waits for a token on
  every incoming edge, and only one outcome fires, so the run would never get
  past it.
  `check` refuses both (HITL_FAN_OUT_INTO_JOIN, HITL_END_OUTCOME_IN_PARALLEL).
  Add a step after the task inside the arm, for example
  `a.step('review', hitl(…)).step('record', …)`: every outcome continues to
  `record`, and only `record` reaches the join. `.stepSwitch` does not help
  here, because its arms rejoin at the same join. A `.stepSwitch` on a task
  inside an arm needs the same step after it: with an empty `Approve` arm and a
  `Reject` arm that runs `rej`, the arm would end on two paths (the `Approve`
  outcome edge and `rej`), and `check` refuses that too
  (HITL_FAN_OUT_INTO_JOIN). Write `a.stepSwitch('review', …).step('record', …)`.
  That `.stepSwitch` also needs an arm for every outcome, and no arm may end in
  `.return()`: either one sends that outcome's path to an End inside the arm,
  so the join waits forever for the arm's other path, and `check` refuses it
  (HITL_END_OUTCOME_IN_PARALLEL). Put the `.return()` after the `.parallel()`.

  The action-app and document-validation variants are different: their outcomes
  live in the app, `completed` is the only handle the designer draws for them,
  and `.step()` leaves on it. Route on `out('<step>', 'Action')` downstream.

  **Why routing is the default.** An approve/reject task whose outcomes all lead
  to one place compiles and `flow validate` answers `Valid`, so the mistake
  surfaced at runtime or in a grader (flow-builder-sdk#735). A warning was not
  enough — #739 measured it firing three times while the unreachable artifact
  shipped anyway — so the shape changed instead of the advice. `check` still
  warns `HITL_OUTCOMES_UNREACHABLE` where every outcome continues to one step and
  nothing reads `out('<step>', 'Action')`.

  **Route EVERY outcome.** With `.stepToList`, an unrouted one deploys and then
  stalls the run when the reviewer picks it (`check` warns
  HITL_OUTCOME_UNROUTED). With `.stepSwitch` it compiles to an End instead, so
  the run finishes rather than hanging — but the End only maps each declared
  output from its variable, and nothing on that path set them, which
  STEP_SWITCH_EXIT_UNROUTED says out loud. Inside a `.parallel()`
  arm that End would hang the join instead, so there it is refused
  (HITL_END_OUTCOME_IN_PARALLEL). `action: 'End'` changes
  what happens on that outcome (the run ends instead of stalling), not whether
  its handle needs an edge.

  **What `flow validate` checks.** It holds an `outcome-<id>` edge to the node's
  declared outcomes: one naming a real outcome passes on every version (so
  per-outcome wiring passes on 1.0 and on quick-form), and one naming no outcome
  is refused — *Edge references undeclared source handle "outcome-nope"*. On a
  1.1/1.2 node it also refuses `completed`. It does NOT refuse `completed` on a
  1.0 or quick-form node that has outcomes, which is why `check` and the SDK do.

  **The decision as data** — `.step()` then `.switch()` on
  `out('<step>', 'Action')` — still works: every outcome reaches the switch on
  its own edge, and the switch routes. Ask for it deliberately (quick-form, or
  `outcomePorts: false` on the default node); the reason is that the decision is
  wanted as DATA — recorded in an output, compared in one place. Every outcome
  continuing to one step with nothing reading `Action` is the unreachable-outcomes
  case above, not a third shape.
- `variant: 'document-validation'` takes `document: { extractionResult,
  storageBucket?, documentId?, render?, taxonomy? }` and no `fields`; bind
  `extractionResult` to the upstream extract step's `ExtractionResult`.
  `render: 'custom'` requires `taxonomy` (and takes `app`).

## Variant judgment

Use the node variant explicitly named by the scenario. The default and
quick-form variants own their fields in the Flow; action-app delegates the form
to an already-deployed app. For an app task, resolve the app key, name, folder,
and argument names from the same tenant resource.

## Evidence boundary

Offline execution scripts the selected action and output fields. It proves
wiring and downstream routing, not that a real task appeared or that a person
participated. Live evidence should preserve the Action Center task identity,
the human-selected outcome, supplied answers, and the path that resumed.

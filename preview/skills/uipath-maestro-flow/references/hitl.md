# Human-in-the-Loop

*Exact signatures, fields, and defaults: [`hitl()`](api.md#hitl-function).*

Pause a Flow for a person using the default inline form, the quick-form node
type, a deployed Action App, or a document-validation station.

Signature:
`hitl({ variant?: 'quick-form' | 'action-app' | 'document-validation', app?,
document?, title?, priority?, labels?, recipient?, fields?, outcomes,
outcomePorts?, exposeError? })`.

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

More than one outcome routes per outcome by itself — there is no flag to
remember and no decision node in the middle. `outcomePorts: false` is how you
ask for the older single-exit shape instead.

`.stepSwitch` is how you write that: one arm per outcome, none of them the tacit
next step.
Arms behave like `.switch()`'s — one that ends in `.return()` is terminal, and one
that does not CONVERGES, so the step after the `.stepSwitch` fans in from every
arm that reaches it.
That is what makes the single `.return()` above correct, and what a flow VARIABLE
is for: each arm assigns it with `{ updates }` and the one return reads it, instead
of the return having to work out which arm ran.

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
- **Per-outcome exits are the DEFAULT above one outcome.** Each outcome gets its
  own exit, `outcome-<slug>` (the name lowercased, non-alphanumerics to `-`).
  `exposeError: true` additionally exposes `out('<step>', 'error')` and selects
  the 1.2 definition.

  Two ways to route them, and prefer the first:

  | | |
  | --- | --- |
  | `.stepSwitch(name, hitl({…}), arms)` | one arm per outcome, `value` naming the outcome. No tacit exit, arms converge, and a missing arm is a warning (STEP_SWITCH_EXIT_UNROUTED) rather than a port with no edge. |
  | `.step()` + `.stepToList('outcome-<slug>', …)` | the FIRST outcome continues the main path and the rest are side arms. Those arms do NOT converge — each gets an End of its own. |

  Do not route the FIRST outcome with `.stepToList`: its port is already taken by
  the main path, and the second edge is emitted anyway
  (flow-builder-sdk#741). `.stepSwitch` is the way to route all of them.

  Four things stand the default down, and only these:

  | | keeps the single `completed` exit because |
  | --- | --- |
  | `outcomePorts: false` | you asked for it |
  | `variant: …` | the quick-form, action-app and document-validation node types have no per-outcome definition version to select |
  | `{ version: '1.0' }` | an explicit pin wins, which is what makes `decompile` → `compile` byte-exact on a deployed 1.0 flow |
  | every outcome `action: 'End'` | the run stops AT the node, so no exit distinguishes anything |

  **Why it is the default.** Outcomes on their own create no exits: on the 1.0
  definition the single `completed` handle is where every outcome leaves, so the
  choice reaches the reviewer and `inputs.schema.outcomes` and never reaches the
  graph. An approve/reject task wired that way compiles and `flow validate`
  answers `Valid`, so the mistake surfaced at runtime or in a grader
  (flow-builder-sdk#735). A warning was not enough — #739 measured it firing
  three times while the unreachable artifact shipped anyway — so the shape
  changed instead of the advice.

  `check` still warns `HITL_OUTCOMES_UNREACHABLE`, now for the cases where the
  single exit was CHOSEN and nothing reads `out('<step>', 'Action')`: a variant,
  a pin, or `outcomePorts: false`.

  **Route EVERY outcome.** With `.stepToList`, an unrouted one deploys and then
  stalls the run when the reviewer picks it (`check` warns
  HITL_OUTCOME_UNROUTED). With `.stepSwitch` it compiles to an End instead, so
  the run finishes rather than hanging — but finishes without the flow's declared
  outputs, which STEP_SWITCH_EXIT_UNROUTED says out loud. Either way the
  exception is `action: 'End'`, which ends the process at the node and needs no
  edge.

  **It REPLACES the `completed` exit; it does not add to it.** Routing per
  outcome selects the node's 1.1 definition (1.2 for `exposeError`), and those
  declare exactly one source handle — `outcome-{item.id}`, repeated over the
  outcomes. The 1.0
  definition's single `completed` handle is not part of them, so "the FIRST
  outcome continues the main path" means that continuation leaves on
  `outcome-<first>`; nothing leaves on `completed`, and an edge that tries is
  refused by the product (`flow validate`: *Edge references undeclared source
  handle "completed"*). `check` refuses it too (HITL_COMPLETED_PORT_GONE).

  **Per-outcome is the platform's live shape; `completed` is the placeholder.**
  The designer does not read the manifest's handle list for a human task — it
  derives one `outcome-<id>` handle per entry in `inputs.schema.outcomes` at
  render time, and falls back to a single `completed` placeholder only when there
  are no outcomes (flow-workbench, `getEffectiveHitlHandleCustomization`). So on a
  task that HAS outcomes, an edge leaving `completed` is not a handle the canvas
  draws, even where the manifest still declares one and `flow validate` still
  accepts it.

  `validate` is the looser of the two: it checks a literal handle against the
  definition — `bogus-port` is refused — but waves through anything shaped
  `outcome-<id>` whatever the definition declares, so per-outcome wiring passes
  even on the 1.0 definition. Measured, alongside the `completed`-on-1.1 refusal
  above.

  That is why the default went this way rather than the other: a consumer, a
  validator, the designer and a graded check all read the per-outcome handles,
  and the product warns `HITL_COMPLETED_UNWIRED` on the single exit — whose name
  says completed and whose text says outcome, the platform's vocabulary being
  mid-migration here.

  **The other shape — `completed` plus `.switch()` on `out('<step>', 'Action')` —
  still works, and is the ONLY shape the quick-form, action-app and
  document-validation variants have.** They carry no per-outcome definition
  version for the SDK to select. On a base task it is now something you ask for
  with `outcomePorts: false`, and the reason to ask is that the decision is
  wanted as DATA — recorded in an output, compared in one place, or fanned into
  something the graph cannot express. Reach for it deliberately: a single
  `completed` exit with nothing reading `Action` is the unreachable-outcomes case
  above, not a third shape.
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

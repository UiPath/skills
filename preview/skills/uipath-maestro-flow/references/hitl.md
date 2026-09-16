# Human-in-the-Loop

*Exact signatures, fields, and defaults: [`hitl()`](api.md#hitl-function).*

Pause a Flow for a person using the default inline form, the quick-form node
type, a deployed Action App, or a document-validation station.

Signature:
`hitl({ variant?: 'quick-form' | 'action-app' | 'document-validation', app?,
document?, title?, priority?, labels?, recipient?, fields?, outcomes,
outcomePorts?, exposeError? })`.

```ts
.step('review', hitl({ title: 'Review invoice',
  fields: [{ id: 'comment', type: 'text', direction: 'output' }],
  outcomes: ['Approve', 'Reject'] }))
.switch('route', out('review', 'Action'), [
  { value: 'Approve', body: (b) => b.return({ status: 'approved' }) },
], (other) => other.return({ status: 'rejected' }))
```

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
- `outcomePorts: true` gives each outcome its own exit, `outcome-<slug>` (the
  name lowercased, non-alphanumerics to `-`). The FIRST outcome continues the
  main path; route the others with `.stepToList('outcome-<slug>', …)`. Base
  variant only — the quick-form, action-app and document-validation variants have
  no per-outcome version and the SDK refuses the option on them.
  `exposeError: true` additionally exposes `out('<step>', 'error')` and implies
  outcome-port routing.

  **Declaring `outcomes` is HALF the decision — the flag reads optional and is not.**
  Outcomes on their own create no exits.
  Without `outcomePorts` the node emits its 1.0 definition's single `completed` handle and EVERY outcome leaves on it, so the choice reaches the reviewer and `inputs.schema.outcomes` and never reaches the graph.
  An approve/reject task wired that way compiles, and `flow validate` answers `Valid`.
  So every task with more than one outcome needs one of the two shapes, deliberately: `outcomePorts: true` to fork in the graph, or `.switch()` on `out('<step>', 'Action')` to route the decision as data.
  `check` warns `HITL_OUTCOMES_UNREACHABLE` when a task declares several outcomes and neither shape is present.

  **It REPLACES the `completed` exit; it does not add to it.** The option selects
  the node's 1.1 definition (1.2 for `exposeError`), and those declare exactly one
  source handle — `outcome-{item.id}`, repeated over the outcomes. The 1.0
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

  So prefer `outcomePorts: true` when the task has real outcomes and something
  downstream reads the graph — a consumer, a validator, the designer, a graded
  check. Route EVERY outcome when you do: an unrouted one stalls the run
  (`check` warns HITL_OUTCOME_UNROUTED, and the product warns
  `HITL_COMPLETED_UNWIRED` — whose name says completed and whose text says
  outcome, the platform's vocabulary being mid-migration here).

  The default shape — `completed` plus `.switch()` on `out('<step>', 'Action')`,
  as in the example above — stays correct and is the ONLY shape available on the
  quick-form, action-app and document-validation variants, which have no
  per-outcome version for the SDK to select. Use it there, and when the decision
  is read as data rather than forked in the graph — but do use one of the two:
  a `completed` exit with nothing reading `Action` is the unreachable-outcomes
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

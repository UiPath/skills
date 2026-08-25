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
  variant only. `exposeError: true` additionally exposes
  `out('<step>', 'error')` and implies outcome-port routing.
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

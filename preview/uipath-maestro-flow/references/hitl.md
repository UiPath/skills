# Human-in-the-Loop

*Exact signatures, fields, and defaults: [`hitl()`](api.md#hitl-function).*

Pause a Flow for a person using the default inline form, the quick-form node
type, or a deployed Action App.

Signature:
`hitl({ variant?: 'quick-form' | 'action-app', app?, title?, priority?, fields?, outcomes })`.

```ts
.step('review', hitl({ title: 'Review invoice',
  fields: [{ id: 'comment', type: 'text', direction: 'output' }],
  outcomes: ['Approve', 'Reject'] }))
.switch('route', out('review', 'Action'), [
  { value: 'Approve', body: (b) => b.return({ status: 'approved' }) },
], (other) => other.return({ status: 'rejected' }))
```

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

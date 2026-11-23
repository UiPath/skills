# Pattern: `failure-escalation`

One error event subprocess that catches every unhandled activity failure in its
container, classifies it, and routes business errors to a person and system
failures to operations. Use it on any process where a failure must never
disappear silently.

## Why it works

These four carry the shape. Change one and you are building something else.

- **It covers by placement, not by wiring.** The net is an event subprocess with
  no sequence flows in or out. Drop it into a container and every unhandled
  activity failure inside routes to it, with nothing attached to any task.
- **The engine pre-seeds the error context.** `vars.Error` arrives populated,
  so the classification gateway reads real values with no mapping authored.
- **It is interrupting and terminal, so outcomes must be named.** When the net
  fires, the normal path stops and the instance records **Completed**, not
  Faulted. Without an explicitly named end event on every branch, a handled
  failure is indistinguishable from a success.
- **Code-specific nets match before the catch-all.** Both can sit in one
  container, so a known error gets a precise response while everything else
  still lands somewhere.

## Shape

This pattern has no Entry row: it is never wired into a path.

The net itself is a `bpmn:subProcess` with `triggeredByEvent="true"`, holding:

| Node | Element | Role |
| --- | --- | --- |
| `err_start` | `bpmn:startEvent` + error event definition | Mechanism |
| `classify` | `bpmn:exclusiveGateway` | Mechanism |
| `reviewer` | `bpmn:userTask` | Placeholder |
| `end_human` | `bpmn:endEvent` | Mechanism |
| `record_failure` | `bpmn:serviceTask` | Placeholder |
| `alert_oncall` | `bpmn:sendTask` | Placeholder |
| `end_ops` | `bpmn:endEvent` | Mechanism |

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `err_start` → `classify` | | |
| `classify` → `reviewer` | Business error | `=vars.Error.category == "User"` |
| `reviewer` → `end_human` | | |
| `classify` → `record_failure` | System failure | default |
| `record_failure` → `alert_oncall` | | |
| `alert_oncall` → `end_ops` | | |

The pattern declares no process variables of its own. `vars.Error` is seeded by
the engine — capital `E`, lowercase fields: `code`, `message`, `detail`,
`category`, `status`, `traceId`, `response`, `element`. `category` is `User`,
`System`, or `Deployment`; business errors arrive as `User`. See
[expression-authoring.md](../expression-authoring.md#stored-expression-shape).

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Catch-all | What catches everything nothing else did? | The shape above |
| Code-specific | Does one known error deserve its own response? | Bound start, no classification |

**Code-specific.** Bind `err_start` to a single error code. The code already
identifies the failure, so there is no `classify` gateway: the bound start leads
straight to one response node and one named end event. It is the smaller net,
and it coexists with a catch-all in the same container.

## What to bind

- **`reviewer`** — `Actions.HITL`. Who works a business error: an operations
  queue, the process owner.
- **`record_failure`** — where a system failure is durably recorded for someone
  to work later: an exception queue, a task.
- **`alert_oncall`** — the notification channel.
- **The error code** on a code-specific net's `err_start`, via `errorRef` to a
  declared `bpmn:error`.

See [structural-bpmn.md](../structural-bpmn.md#subprocess-call-activity-event-subprocess-registry-gap-for-structure)
for event subprocess structure, and
[registry-workflow.md](../registry-workflow.md) for the payloads.

## Adapting it

Collapse the two branches into one when the process has no meaningful business
errors — everything is a system failure and there is nobody to escalate to.
Keep the named end event.

Do not extend the net to resume the interrupted work. It cannot: the normal path
has already stopped. Work that should recover and continue belongs on an error
boundary event instead — see
[structural-bpmn.md](../structural-bpmn.md#choosing-an-error-handling-construct).

Two limits are worth knowing before relying on it. Only activities enter the
chain, so a gateway whose condition fails to evaluate raises an incident and
never reaches the net. And transient failures should not arrive here at all —
they are absorbed by `uipath:retry` on the node.

## Composing

Nested patterns are covered for free: one net catches failures in every
subprocess beneath it. For when a second net inside a batch iteration or a queue
performer earns its place, see
[composing-guide.md](composing-guide.md#scoping-the-failure-net).

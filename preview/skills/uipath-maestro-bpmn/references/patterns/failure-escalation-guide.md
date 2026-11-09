# Pattern: `failure-escalation`

One error event sub-process that catches every unhandled activity failure in its container, classifies it, and routes business errors to a person and system failures to operations.
Use it on any process where a failure must never disappear silently.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **It covers by placement, not by wiring.** The net is an `.eventSubProcess()` with no flow in or out.
  Place it in a container and every unhandled activity failure inside routes to it, with nothing attached to any task: no `onError` in any activity's body.
- **The engine seeds the error context.** The net's start captures the caught error into `vars.<net>_Error` by default, so the classification reads real values with no mapping authored.
- **It is interrupting and terminal, so outcomes must be named.** When the net fires, the normal path stops and the instance records **Completed**, not Faulted.
  Without a named end event on every branch, a handled failure is indistinguishable from a success.
- **Code-specific nets match before the catch-all.** Both can sit in one container, so a known error gets a precise response while everything else still lands somewhere.

## Shape

This pattern has no Entry row: it is never wired into a path.
The process around it is only there to show where the net sits.

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

// Retry only what is transient. Without `allErrors`, a retry policy retries just the
// codes `errorMapping` marks retryable, so bad data goes straight to the net.
const transient = {
  retry: { maxRetries: 3, backoff: 'PT1M' },
  errorMapping: [{ code: '429', retryable: true }, { code: '503', retryable: true }],
};

export default bpmn('payroll-run')
  .name('PayrollRun')
  .flowMode('sequence')
  .startEvent('start', { name: 'Payroll due' })
  .scriptTask('fetchTimesheets', { name: 'Fetch timesheets', script: 'return { ok: true };', ...transient })
  .scriptTask('calculatePay', { name: 'Calculate pay', script: 'return { ok: true };', ...transient })
  .scriptTask('postPay', { name: 'Post to finance', script: 'return { ok: true };', ...transient })
  .endEvent('done', { name: 'Payroll posted' })
  // Placed, not wired: no flow enters or leaves the net. Sitting at process level,
  // it catches what any step above raises and nothing closer caught.
  .eventSubProcess('failures', { error: true, name: 'Failure net' }, (h) =>
    h.choose('classify', [
      {
        when: '=vars.failures_Error.category == "User"',
        label: 'Business error',
        body: (b) =>
          b.humanTask('reviewer', { name: 'Review bad data', form: { fields: [], outcomes: ['Resolved'] } })
            .endEvent('endHuman', { name: 'Bad data sent for review' }),
      },
      {
        otherwise: true,
        label: 'System failure',
        body: (b) =>
          b.scriptTask('recordFailure', { name: 'Record failure', script: 'return { ok: true };' })
            .plainTask('alertOncall', { name: 'Tell operations', element: 'bpmn:sendTask' })
            .endEvent('endOps', { name: 'Operations alerted' }),
      },
    ]),
  )
  .build();
```

The net is written last, after the main path's end event, and nothing names it: where it sits is what it guards.
At process level it guards every step above, and every sub-process nested under them: a nested sub-process's unhandled failure surfaces as that sub-process failing in its parent, which is the container the net sits in.

| Node | Builder | Role |
| --- | --- | --- |
| `failures` | `.eventSubProcess(id, { error: true })` | Mechanism |
| `failures_start` | synthesized, captures `vars.failures_Error` | Mechanism |
| `classify` | `.choose()` in the net's body | Mechanism |
| `reviewer` | `.humanTask()` | Placeholder |
| `endHuman` | `.endEvent()`, named | Mechanism |
| `recordFailure` | the system-failure work | Placeholder |
| `alertOncall` | a send step | Placeholder |
| `endOps` | `.endEvent()`, named | Mechanism |

The pattern declares no process variables of its own.
The capture is `vars.<net>_Error` (here `vars.failures_Error`), not `vars.Error`: the designer gives every capture its own id, and the SDK follows it.
`errorVar` renames it.
Its fields are lowercase: `code`, `message`, `detail`, `category`, `status`, `traceId`, `response`, `element`.
`category` is `User`, `System`, or `Deployment`; business errors arrive as `User`.

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Catch-all | What catches everything nothing else did? | The shape above |
| Code-specific | Does one known error deserve its own response? | A bound start, no classification |

**Code-specific.** `.eventSubProcess('badTimesheet', { error: { name: 'BadTimesheet', code: 'TS-001' } }, (h) => …)`.
The code already identifies the failure, so there is no `classify` choose: the body is one response node and one named end event.
It is the smaller net, and it sits beside a catch-all in the same container.

## What to bind

- **`reviewer`**: `.humanTask()`.
  Who works a business error: an operations queue, the process owner.
- **`recordFailure`**: where a system failure is durably recorded for someone to work later: an exception queue (`.queueItem()`), a task.
- **`alertOncall`**: the notification channel, usually a `.connector()` call.
- **Transient failures**: `retry: { maxRetries, backoff }` on the step itself, plus an `errorMapping` row with `retryable: true` for each transient code, as in the example.
  A policy without `allErrors` retries only the mapped codes, and with no mapping it retries nothing.
  `allErrors: true` retries every failure, business errors included, so bad data would be retried before it reaches the net; use it only on a step whose every failure is transient.
  The codes (`429`, `503`) are illustrative: map the ones the bound service actually raises.
  Transient failures should never reach the net.

## Adapting it

Collapse the two arms into one when the process has no meaningful business errors: everything is a system failure and there is nobody to escalate to.
Keep the named end event.

Do not extend the net to resume the interrupted work.
It cannot: the normal path has already stopped.
Work that should recover and continue belongs in an `onError` handler in that activity's body, whose interrupting path rejoins at the statement after the activity.

Two limits are worth knowing before relying on it.
Only activities enter the chain, so a gateway whose condition fails to evaluate raises an incident and never reaches the net.
And transient failures should not arrive here at all: they are absorbed by `retry` on the node.

## Composing

Nested patterns are covered for free: a failure no inner net handles surfaces as its sub-process failing, level by level, until it reaches the container this net sits in.
For when a second net inside a batch iteration or a queue performer earns its place, see [composing-guide.md](composing-guide.md#scoping-the-failure-net).

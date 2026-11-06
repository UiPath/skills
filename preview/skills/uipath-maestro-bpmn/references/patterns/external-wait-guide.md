# Pattern: `external-wait`

The process suspends until an outside party responds, nudges before the deadline, and escalates when the deadline passes.
Use it when a reply may take hours or weeks and an SLA has to be enforced either way.

## Why it works

These five carry the shape.
Change one and you are building something else.

- **A correlation key goes out with the request.** The reply carries it back, which is how the engine finds the one suspended instance that was waiting.
  Without it a reply cannot be matched and the wait never ends.
- **An event-based gateway makes the outcomes a race.** Reply, reminder, and deadline are mutually exclusive: whichever fires first wins and the others are discarded.
  Modelling them as `.fork()` arms would let two fire.
- **The reminder loops back to the same gateway.** After nudging, the process resumes waiting on the gateway it already has, so the wait exists once no matter how many reminders go out.
- **Replies are validated before they are believed.** A malformed or unmatched reply routes to a person instead of resuming the process on bad data.
- **Both exits are named.** A reply received, or an escalation exhausted.
  A wait that ends without a recorded reason is indistinguishable from one that never ended.

## Shape

Single-channel is the base shape.

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('vendor-docs')
  .name('VendorDocs')
  .flowMode('sequence')
  .var('correlationKey', 'string')
  .var('responseValid', 'boolean', { default: false })
  .startEvent('start', { name: 'Document needed' })
  .task('compose', { name: 'Compose request', set: { correlationKey: '=js:"DOC-" + Date.now()' } })
  .plainTask('sendRequest', { name: 'Ask vendor for document', element: 'bpmn:sendTask' })
  // The race IS the wait. The reminder arm loops back to the same gateway, so the
  // wait exists once however many reminders go out.
  .race('wait', [
    (b) => b.intermediateCatchEvent('replyReceived', { name: 'Vendor replied', message: 'VendorDocumentReply' }),
    (b) =>
      b.intermediateCatchEvent('reminderDue', { name: 'Nudge due', timer: 'P2D' })
        .plainTask('sendReminder', { name: 'Nudge vendor', element: 'bpmn:sendTask' })
        .goto('wait'),
    (b) =>
      b.intermediateCatchEvent('slaDeadline', { name: 'Deadline passed', timer: 'P10D' })
        .scriptTask('runEscalation', { name: 'Escalate', script: 'return { escalated: true };' })
        .endEvent('escalated', { name: 'Escalated' }),
  ])
  .scriptTask('validateReply', { name: 'Check reply', script: 'return { valid: true };', outputs: { responseValid: '=result.valid' } })
  .choose('validGate', [
    { when: '=vars.responseValid == true', label: 'Valid', body: (b) => b },
    { otherwise: true, label: 'Invalid', body: (b) => b.humanTask('reviewReply', { name: 'Review reply', form: { fields: [], outcomes: ['Accept', 'Submit Correction'] } }) },
  ])
  .endEvent('received', { name: 'Document received' })
  .build();
```

`.race()` is the event-based gateway.
Each arm must begin with something that waits (an `.intermediateCatchEvent()` with `message` or `timer`, a `.receiveMessage()`, or a `.waitForEvent()`); the builder refuses anything else in first position.
The reminder arm ends in `.goto('wait')`, back to the race's own id, which is the loop.
Only the reply arm falls through, so no join is emitted and validation follows the race directly.

| Node | Builder | Role |
| --- | --- | --- |
| `start` | `.startEvent()` | Entry |
| `compose` | `.task()` setting the key | Mechanism · insertion point: embeds the correlation key |
| `sendRequest` | a send step | Placeholder |
| `wait` | `.race()` | Mechanism |
| `replyReceived` | `.intermediateCatchEvent()` with `message` | Mechanism |
| `reminderDue` | `.intermediateCatchEvent()` with `timer` | Mechanism |
| `sendReminder` | a send step, then `.goto('wait')` | Placeholder |
| `slaDeadline` | `.intermediateCatchEvent()` with `timer` | Mechanism |
| `runEscalation` | the work in the deadline arm | Placeholder |
| `validateReply` | the statement after the race | Mechanism |
| `validGate` | `.choose()` | Mechanism |
| `reviewReply` | `.humanTask()` in the invalid arm | Placeholder |
| `received` | `.endEvent()`, named | Mechanism |
| `escalated` | `.endEvent()`, named | Mechanism |

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `correlationKey` | string | | Unique ID embedded in the request |
| `responseData` | jsonSchema | | The reply payload |
| `responseValid` | boolean | `false` | Did it pass validation |
| `validationIssue` | string | | Why it did not, shown to the reviewer |
| `reviewOutcome` | string | | `Accept` or `Submit Correction` |

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Single-channel | — | The shape above |
| Multi-channel | Can they reply however they like? | One race arm per channel |
| First valid response wins | Can any of several parties fulfil it? | Fan out, first acceptable reply closes the rest |
| Long-running probe | Can the far system push at all? | Poll on a timer instead of waiting for an event |

**Multi-channel.** Replace the reply arm with one arm per channel (email, webhook, portal), each beginning with its own catch event.
Several arms now fall through, so the race emits `wait_join` before `validateReply`.
The race already makes them exclusive: the first to arrive wins and the rest are dropped.
A connector event as a channel is a `.waitForEvent()` arm ([Connector events](../connectors.md#6-connector-events)).

**First valid response wins.** `.fork()` one send step per party, then race on the replies.
An unacceptable reply is discarded and the arm ends in `.goto('wait')`; the first acceptable one triggers a notification closing out the remaining parties.
Each request carries its own key, or replies cannot be told apart.

**Long-running probe.** There is no event to catch, so there is no race.
`sendRequest` leads to a timer catch, a poll task, and a `readyGate` choose whose ready arm falls through.
Its not-ready arm holds a `deadlineGate` choose: past the deadline it escalates and ends, otherwise it ends in `.goto('pollTimer')`.
The loop returns to the **timer**, not the poll task: the wait between polls is the point.
The deadline gate is what stops the loop; without it this shape never terminates.

## What to bind

- **`compose`**: build the outbound payload and embed the correlation key.
- **`sendRequest`**, **`sendReminder`**: the outbound channel (email, portal link, API call, EDI), usually a `.connector()` call.
  A bare `bpmn:sendTask` placeholder validates with a warning that it invokes nothing.
- **Reply catch events**: the inbound channel and the message each correlates on.
- **Timer durations**: reminder cadence and the SLA deadline, as ISO 8601 durations on the catch events ([Events](../bpmn-runtime.md#events-and-timers)).
- **`validateReply`**: correlation match, parseable content, acceptable values.
- **`reviewReply`**: `.humanTask()`.
- **`runEscalation`**: next-level contact, alternate channel, internal owner.

## Adapting it

Drop the reminder arm when there is no one to nudge: a machine counterpart that either answers or does not.
The deadline arm stays; that is the SLA.

Drop `reviewReply` and send invalid replies straight to escalation when no human can repair a malformed reply.

Add channels freely in the multi-channel variant: each is one more race arm, not a structural change.

## Composing

Nested inside `high-volume-batch` this becomes a per-item wait, giving each item its own correlation key and deadline.
Pair with `failure-escalation` for failures in sending or escalation.
See [composing-guide.md](composing-guide.md).

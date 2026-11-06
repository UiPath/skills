# Pattern: `external-wait`

The process suspends until an outside party responds, nudges before the deadline, and escalates when the deadline passes.
Use it when a reply may take hours or weeks and an SLA has to be enforced either way.

## Why it works

These six carry the shape.
Change one and you are building something else.

- **A correlation key goes out with the request.** The reply carries it back, which is how the engine finds the one suspended instance that was waiting.
  The reply arm binds it: `.receiveMessage()` takes the key as its `reference`.
  Without it a reply cannot be matched and the wait never ends.
- **An event-based gateway makes the outcomes a race.** Reply, reminder, and deadline are mutually exclusive: whichever fires first wins and the others are discarded.
  Modelling them as `.fork()` arms would let two fire.
- **The reminder loops back to the same gateway.** After nudging, the process resumes waiting on the gateway it already has, so the wait exists once no matter how many reminders go out.
- **The deadline is an absolute instant, computed once.** Re-entering the race re-arms every catch event in it, so a relative `P10D` behind a `P2D` reminder would restart every two days and never fire.
  `compose` computes `slaDueAt` before the wait, and `slaDeadline` waits for that date, which no number of loops moves.
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
  .var('slaDueAt', 'string')
  .var('responseData', 'jsonSchema')
  .var('responseValid', 'boolean', { default: false })
  .var('validationIssue', 'string')
  .var('reviewOutcome', 'string')
  .startEvent('start', { name: 'Document needed' })
  // The key and the deadline are computed ONCE, before the wait. The deadline is an
  // absolute instant, so re-entering the race below cannot push it back.
  .task('compose', {
    name: 'Compose request',
    set: { correlationKey: '=js:"DOC-" + Date.now()', slaDueAt: '=js:new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString()' },
  })
  .plainTask('sendRequest', { name: 'Ask vendor for document', element: 'bpmn:sendTask' })
  // The race IS the wait. The reminder arm loops back to the same gateway, so the
  // wait exists once however many reminders go out.
  .race('wait', [
    (b) =>
      b.receiveMessage('replyReceived', {
        name: 'Vendor replied',
        message: 'VendorDocumentReply',
        reference: '=vars.correlationKey',
        outputVar: 'responseData',
      }),
    (b) =>
      b.intermediateCatchEvent('reminderDue', { name: 'Nudge due', timer: 'P2D' })
        .plainTask('sendReminder', { name: 'Nudge vendor', element: 'bpmn:sendTask' })
        .goto('wait'),
    (b) =>
      b.intermediateCatchEvent('slaDeadline', { name: 'Deadline passed', timer: { date: '=vars.slaDueAt' } })
        .scriptTask('runEscalation', { name: 'Escalate', script: 'return { escalated: true };' })
        .endEvent('escalated', { name: 'Escalated' }),
  ])
  .scriptTask('validateReply', {
    name: 'Check reply',
    script: 'return { valid: true, issue: null };',
    outputs: { responseValid: '=result.response.valid', validationIssue: '=result.response.issue' },
  })
  .choose('validGate', [
    { when: '=vars.responseValid == true', label: 'Valid', body: (b) => b },
    {
      otherwise: true,
      label: 'Invalid',
      body: (b) =>
        b.humanTask('reviewReply', {
          name: 'Review reply',
          form: { fields: [], outcomes: ['Accept', 'Request Resend'] },
          outputs: { reviewOutcome: '=Action' },
        })
          .choose('reviewGate', [
            { when: '=vars.reviewOutcome == "Accept"', label: 'Accepted', body: (r) => r },
            {
              otherwise: true,
              label: 'Resend',
              body: (r) => r.plainTask('requestResend', { name: 'Ask vendor to resend', element: 'bpmn:sendTask' }).goto('wait'),
            },
          ]),
    },
  ])
  .endEvent('received', { name: 'Document received' })
  .build();
```

`.race()` is the event-based gateway.
Each arm must begin with something that waits (an `.intermediateCatchEvent()` with `message` or `timer`, a `.receiveMessage()`, or a `.waitForEvent()`); the builder refuses anything else in first position.
The reminder arm ends in `.goto('wait')`, back to the race's own id, which is the loop.
Only the reply arm falls through, so no join is emitted and validation follows the race directly.
A reply a reviewer sends back (`Request Resend`) also returns to `wait`, and the deadline still holds, because it is the same instant.

The reply arm is `.receiveMessage()`, not `.intermediateCatchEvent({ message })`.
The typed node carries the correlation `reference` and lands the reply in `outputVar`; the plain form has no correlation option in the builder, and the engine treats a bare `messageRef` catch in a race as a no-op.
`.receiveMessage()` waits for a Maestro message: whatever receives the vendor's reply (an intake process on the mailbox or portal) sends `VendorDocumentReply` with the same reference, as a `Maestro.SendMessageEvent` activity whose `Reference` input is the key.
The local engine passes a receive straight through, so only a live run shows a reply being matched.

| Node | Builder | Role |
| --- | --- | --- |
| `start` | `.startEvent()` | Entry |
| `compose` | `.task()` setting the key and the deadline | Mechanism · insertion point: embeds the correlation key, fixes the SLA instant |
| `sendRequest` | a send step | Placeholder |
| `wait` | `.race()` | Mechanism |
| `replyReceived` | `.receiveMessage()` with `reference` | Mechanism |
| `reminderDue` | `.intermediateCatchEvent()` with `timer` | Mechanism |
| `sendReminder` | a send step, then `.goto('wait')` | Placeholder |
| `slaDeadline` | `.intermediateCatchEvent()` with `timer: { date }` | Mechanism |
| `runEscalation` | the work in the deadline arm | Placeholder |
| `validateReply` | the statement after the race | Mechanism |
| `validGate` | `.choose()` | Mechanism |
| `reviewReply` | `.humanTask()` in the invalid arm | Placeholder |
| `reviewGate` | `.choose()` on `reviewOutcome` | Mechanism |
| `requestResend` | a send step, then `.goto('wait')` | Placeholder |
| `received` | `.endEvent()`, named | Mechanism |
| `escalated` | `.endEvent()`, named | Mechanism |

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `correlationKey` | string | | Unique ID embedded in the request, and the reply's `reference` |
| `slaDueAt` | string | | ISO 8601 instant the deadline fires at, set once |
| `responseData` | jsonSchema | | The reply payload, `replyReceived`'s `outputVar` |
| `responseValid` | boolean | `false` | Did it pass validation |
| `validationIssue` | string | | Why it did not, shown to the reviewer |
| `reviewOutcome` | string | | `Accept` or `Request Resend` |

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Single-channel | — | The shape above |
| Multi-channel | Can they reply however they like? | One race arm per channel |
| First valid response wins | Can any of several parties fulfil it? | Fan out, first acceptable reply closes the rest |
| Long-running probe | Can the far system push at all? | Poll on a timer instead of waiting for an event |

**Multi-channel.** Replace the reply arm with one arm per channel (email, webhook, portal), each beginning with its own `.receiveMessage()` or `.waitForEvent()`.
Several arms now fall through, so the race emits `wait_join` before `validateReply`.
The race already makes them exclusive: the first to arrive wins and the rest are dropped.
A connector event as a channel is a `.waitForEvent()` arm ([Connector events](../connectors.md#6-connector-events)).

**First valid response wins.** `.fork()` one send step per party, then race on the replies.
An unacceptable reply is discarded and the arm ends in `.goto('wait')`; the first acceptable one triggers a notification closing out the remaining parties.
Each request carries its own key, or replies cannot be told apart.

**Long-running probe.** There is no event to catch, so there is no race.
`sendRequest` leads to a timer catch, a poll task, and a `readyGate` choose whose ready arm falls through.
Its not-ready arm holds a `deadlineGate` choose: past `slaDueAt` it escalates and ends, otherwise it ends in `.goto('pollTimer')`.
The loop returns to the **timer**, not the poll task: the wait between polls is the point.
The deadline gate is what stops the loop; without it this shape never terminates.

## What to bind

- **`compose`**: build the outbound payload and embed the correlation key.
- **`sendRequest`**, **`sendReminder`**: the outbound channel (email, portal link, API call, EDI), usually a `.connector()` call.
  A bare `bpmn:sendTask` placeholder validates with a warning that it invokes nothing.
- **Reply arms**: the message name and its `reference` (`.receiveMessage()`), or the connector event (`.waitForEvent()`), per channel.
- **Timers**: the reminder cadence is an ISO 8601 duration on `reminderDue`, which re-arms on each loop by design.
  The SLA is not a duration: set its length in `compose`, where `slaDueAt` is computed once, and keep `slaDeadline` on `timer: { date: '=vars.slaDueAt' }` ([Events](../bpmn-runtime.md#events-and-timers)).
  Never give a race that is re-entered a relative SLA timer.
  `check`, `compile` and `validate` accept the date expression; that the runtime resolves an expression on an intermediate catch timer is not yet confirmed on a live run.
  If it does not, the fallback that also never resets is a `.subProcess()` around the race with an interrupting `onTimer('P10D', …)` in its body, armed once on entry.
- **`validateReply`**: correlation match, parseable content, acceptable values.
- **`reviewReply`**: `.humanTask()`; `Accept` falls through to `received`, `Request Resend` asks again and returns to the wait.
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

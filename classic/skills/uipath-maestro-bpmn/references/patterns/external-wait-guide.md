# Pattern: `external-wait`

The process suspends until an outside party responds, nudges before the
deadline, and escalates when the deadline passes. Use it when a reply may take
hours or weeks and an SLA has to be enforced either way.

## Why it works

These five carry the shape. Change one and you are building something else.

- **A correlation key goes out with the request.** The reply carries it back,
  which is how the engine finds the one suspended instance that was waiting.
  Without it a reply cannot be matched and the wait never ends.
- **An event-based gateway makes the outcomes a race.** Reply, reminder, and
  deadline are mutually exclusive: whichever fires first wins and the others are
  discarded. Modelling them as parallel branches would let two fire.
- **The reminder loops back to the same gateway.** After nudging, the process
  resumes waiting on the gateway it already has, so the wait exists once no
  matter how many reminders go out.
- **Replies are validated before they are believed.** A malformed or
  unmatched reply routes to a person instead of resuming the process on bad
  data.
- **Both exits are named.** A reply received, or an escalation exhausted. A
  wait that ends without a recorded reason is indistinguishable from one that
  never ended.

## Shape

Single-channel is the base shape.

| Node | Element | Role |
| --- | --- | --- |
| `start` | `bpmn:startEvent` + message event definition | Entry |
| `compose` | `bpmn:serviceTask` | Mechanism · insertion point — embeds the correlation key |
| `send_request` | `bpmn:sendTask` | Placeholder |
| `wait` | `bpmn:eventBasedGateway` | Mechanism |
| `reply_received` | `bpmn:intermediateCatchEvent` + message event definition | Mechanism |
| `reminder_timer` | `bpmn:intermediateCatchEvent` + timer event definition | Mechanism |
| `send_reminder` | `bpmn:sendTask` | Placeholder |
| `sla_deadline` | `bpmn:intermediateCatchEvent` + timer event definition | Mechanism |
| `validate` | `bpmn:serviceTask` | Mechanism |
| `valid_gate` | `bpmn:exclusiveGateway` | Mechanism |
| `review_reply` | `bpmn:userTask` | Placeholder |
| `run_escalation` | `bpmn:serviceTask` | Placeholder |
| `end_received` | `bpmn:endEvent` | Mechanism |
| `end_escalated` | `bpmn:endEvent` | Mechanism |

Every outgoing sequence flow from `wait` must target an intermediate catch event
or a receive task — that is a rule of the gateway, not a choice. See
[structural-bpmn.md](../structural-bpmn.md#gateways).

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `start` → `compose` → `send_request` → `wait` | | |
| `wait` → `reply_received` → `validate` | | |
| `wait` → `reminder_timer` → `send_reminder` → `wait` | | the reminder loop |
| `wait` → `sla_deadline` → `run_escalation` → `end_escalated` | | |
| `validate` → `valid_gate` | | |
| `valid_gate` → `end_received` | Valid | `=vars.responseValid == true` |
| `valid_gate` → `review_reply` | Invalid | default |
| `review_reply` → `end_received` | | |

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `correlationKey` | string | | Unique ID embedded in the request |
| `responseData` | jsonSchema | | The reply payload |
| `responseValid` | boolean | `false` | Did it pass validation |
| `validationIssue` | string | | Why it did not, shown to the reviewer |
| `reviewOutcome` | string | | `Accept` or `Submit Correction` |
| `reviewNote` | string | | Reviewer's note |

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Single-channel | — | The shape above |
| Multi-channel | Can they reply however they like? | One catch event per channel |
| First valid response wins | Can any of several parties fulfil it? | Fan out, first acceptable reply closes the rest |
| Long-running probe | Can the far system push at all? | Poll on a timer instead of waiting for an event |

**Multi-channel.** Replace `reply_received` with one
`bpmn:intermediateCatchEvent` per channel — email, webhook, portal — each an
outgoing target of `wait`, all converging on `validate`. The gateway already
makes them a race, so the first to arrive wins and the rest are dropped. Same
variables.

**First valid response wins.** Fan out with a `bpmn:parallelGateway` to one send
task per party, join, then open the response window and wait. An unacceptable
reply is discarded and the wait resumes; the first acceptable one triggers a
notification closing out the remaining parties.

Variables narrow to `correlationKey` (one per party), `responseData`, and
`replyAcceptable` (boolean, default `false`). Each request carries its own key,
or replies cannot be told apart.

**Long-running probe.** There is no event to catch, so there is no event-based
gateway. `send_request` leads to a timer, then a poll task, then a readiness
gateway; not-ready falls to a deadline gateway that either loops back to the
timer or escalates.

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `ready_gate` → `end_received` | Ready | `=vars.resultReady == true` |
| `ready_gate` → `deadline_gate` | Not yet | default |
| `deadline_gate` → `run_escalation` | Yes | `=vars.deadlinePassed == true` |
| `deadline_gate` → `poll_timer` | No | default |

Variables are `responseData`, `resultReady` (boolean, `false`), and
`deadlinePassed` (boolean, `false`). The loop returns to the **timer**, not the
poll task — the wait between polls is the point. The deadline gateway is what
stops the loop running forever; without it this shape never terminates.

## What to bind

- **`compose`** — build the outbound payload and embed the correlation key.
- **`send_request`**, **`send_reminder`** — the outbound channel: email, portal
  link, API call, EDI.
- **Reply catch events** — the inbound channel and the message each correlates
  on.
- **Timer durations** — reminder cadence and the SLA deadline, as ISO 8601
  durations on the timer event definitions.
- **`validate`** — correlation match, parseable content, acceptable values.
- **`review_reply`** — `Actions.HITL`.
- **`run_escalation`** — next-level contact, alternate channel, internal owner.

Fetch payloads through [registry-workflow.md](../registry-workflow.md); see
[structural-bpmn.md](../structural-bpmn.md#events-and-the-event-definition-matrix)
for event definition structure.

## Adapting it

Drop the reminder branch when there is no one to nudge — a machine counterpart
that either answers or does not. The deadline branch stays; that is the SLA.

Drop `review_reply` and route invalid replies straight to escalation when no
human can repair a malformed reply.

Add channels freely in the multi-channel variant: each is one more catch event
on the gateway, not a structural change.

## Composing

Nested inside `high-volume-batch` this becomes a per-item wait, giving each item
its own correlation key and deadline. Pair with `failure-escalation` for
failures in sending or escalation. See [composing-guide.md](composing-guide.md).

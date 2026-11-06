# Composing Patterns

Read this when a process uses more than one pattern, and for how any pattern's shared join is written.
For a single pattern, greenfield or inserted into a process that already runs, its own guide is otherwise enough.

## Shared joins: the mechanism nesting hides

Most patterns turn on one step reached two ways: one dispatch gate (`smart-triage`), one action (`ai-decision-review`), one rejection exit (`approval-chain`).
Nesting makes the wrong shape the easy one.
Writing what happens next inside each arm duplicates the step per arm; `check`, `compile` and `validate` all pass the duplicate, and only the pattern's grader, or a reader, notices.
Write the shared step once, by one of three forms, in this order of preference:

1. **Fall through.** Leave each arm that should reach the step empty, or ending on its last element, and write the step as the statement AFTER the `.choose()`.
   The builder joins the arms that fall through (`<choose id>_join`, emitted only when more than one does) and the step follows.
   An arm that must not reach it ends with an end event or a `.goto()`.
   This works through nesting: an empty arm of a choose inside an arm falls out through both.
2. **A gateway you name.** When the routes come from places fall-through cannot reach (a later arm, an outer scope, a second stage), declare the join with `.exclusiveGateway(id)`, send each route to it with `.goto(id)`, and wire its one way out with `.sequenceFlow(id, next)`.
   A bare gateway's outgoing flow is never implied, even in sequence mode.
   The tiered reviewer in [ai-decision-review-guide.md](ai-decision-review-guide.md#variants) is this form.
3. **A loop back to a gateway.** `.goto(id)` to an earlier gateway is itself a join, since a gateway may take several incoming flows: the reminder arm of `.race('wait', …)` ends in `.goto('wait')`.

Never `.goto()` an activity from two places.
That is a fake join: `check` warns `FAKE_JOIN`, `validate` says nothing, and the canvas contract forbids it on an activity.
A `.goto()` back to a human task to redo it (`examples/InvoiceEscalation.bpmn.ts`) draws the same warning; it is accepted there, never as a pattern's merge.

Read `uip maestro bpmn check <Name>.bpmn.ts --graph` after writing a pattern: the step that should be shared must appear once, with more than one incoming flow or behind a `_join`.

## Patterns are graph fragments

Each guide draws its pattern standalone, so the shape opens with a start event.
That start event is an artifact of drawing it alone; it is not part of the pattern.
A pattern goes anywhere in a graph.

Keep the start event only when the pattern happens to begin the process.
Author it into the middle of an existing process and you drop the start event entirely.

Two entries are load-bearing and do constrain placement:

- **`queue-distribution`'s performer**: its start event is the queue trigger, so the performer must begin the process.
  It cannot be inserted mid-process or nested in a sub-process.
- **`failure-escalation`**: an `.eventSubProcess()` with no flows in or out.
  It is placed inside the container it guards and must sit there *directly*; wrapping it in another sub-process changes which failures reach it.

Both are engine behavior, not style.

## Four ways to join

Building from scratch with several patterns, the outermost one keeps its start event and the rest go inside it.

### Inserted inline

The default.
Drop the pattern's start event and continue from the preceding step into its first real node; its steps become part of the surrounding chain.

Use it whenever the work belongs in this process and there is no reason to encapsulate: adding a confidence-gated review partway through a process that already runs.

### Nested as a `.subProcess()`

The pattern's start event becomes the sub-process's own start event, and the sub-process takes the flows in and out.
Give the body its own `.flowMode('sequence')`.

Prefer this over inserting when you need what a container gives you: its own variable scope, a `loop` over the whole pattern, its own `failure-escalation` net, or a collapsed box that keeps the parent readable.

Risk-tiered `approval-chain` already works this way internally: the standard and extended chains are sub-processes the risk gate chooses between.

### Placed, not wired

`failure-escalation` composes by placement alone.
Write the `.eventSubProcess()` in the container whose failures it should catch, and no flow to or from it.

### Dispatched by message to a separate process

The downstream work becomes its own Maestro process, started by a message.
Use this when the downstream has its own lifecycle, its own trigger, or should scale independently.

`smart-triage`'s per-category steps are placeholders for exactly this choice.
Replacing them with a dispatch keeps triage thin; filling them inline makes triage own handling for every category it routes.

## Adding a pattern to a process that already runs

Insert only the part the process lacks, and bind to what it already holds.
Each guide's "Adapting it" says which of its steps are commonly already present and which variable to bind instead of declaring.

Decompile the existing `.bpmn` with `--style nested` and edit that source; see [Brownfield](../bpmn-runtime.md#brownfield-editing).
Everything the pattern does not touch stays untouched: element ids, flow ids (the `.flowIds([…])` pin table), `.preserve()` state, imported connector data.
Inserting a pattern is a surgical edit, not a regeneration.

## Scoping the failure net

One net covers its whole container, including every sub-process nested under it, because unhandled failures propagate outward container by container.
A single net at process level is the usual answer.

Add a second net inside a looped sub-process or a queue performer only when per-item failures need per-item handling: when one bad item should be recorded and the batch should continue.
Without an inner net, the first failure escalates through the process-level net and ends the instance.

Choosing between a net, an `onError` handler in one activity's body, and `retry` on the node: [Events](../bpmn-runtime.md#events-and-timers).

## Variables across a nesting boundary

A nested pattern's variables are scoped to its sub-process.
Anything the parent needs after the sub-process completes must be mapped out explicitly (the sub-process's `payload`), and anything the nested pattern reads from the parent must be mapped in.
Two patterns that both declare a variable of the same name do not share it across that boundary.

Where two patterns meet, keep each one's variable names rather than merging them into a shared name: the guides' conditions reference those names directly.

## Worked combinations

| Combination | Outermost | How the rest join |
| --- | --- | --- |
| Batch of items, each AI-decided with review | `high-volume-batch` | `ai-decision-review` nested as the per-item sub-process |
| Triage inbound, then approve by category | `smart-triage` | `approval-chain` per category, dispatched by message |
| Queue performer with per-item error handling | `queue-distribution` performer | `failure-escalation` placed inside the performer |
| Add review to a process that already runs | the existing process | `ai-decision-review` inserted inline, no start event |
| Any production process | whichever owns the trigger | `failure-escalation` placed at process level |

The first row, written out: the review is the body of the looped sub-process, and its net sits directly inside that body, so one failed claim ends only its own iteration.

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('claims-nightly')
  .name('ClaimsNightly')
  .flowMode('sequence')
  .var('claims', 'jsonSchema')
  .var('aiConfidenceLevel', 'number', { default: 0 })
  .var('reviewOutcome', 'string')
  .startEvent('start', { name: 'Nightly', timer: { cycle: 'R/P1D' } })
  .scriptTask('fetchClaims', { name: 'Fetch claims', script: 'return { items: [] };', outputs: { claims: '=result.items' } })
  .subProcess(
    'eachClaim',
    (sp) =>
      sp
        .flowMode('sequence')
        .startEvent('claimStart')
        .scriptTask('score', { name: 'Score claim', script: 'return { confidence: 0.9 };', outputs: { aiConfidenceLevel: '=result.confidence' } })
        .choose('confidenceGate', [
          { when: '=vars.aiConfidenceLevel >= 0.85', label: 'Confident', body: (b) => b },
          {
            otherwise: true,
            label: 'Unsure',
            body: (b) =>
              b.humanTask('assessorReview', { name: 'Assessor review', form: { fields: [], outcomes: ['Approve', 'Reject'] }, outputs: { reviewOutcome: '=Action' } })
                .choose('assessorVerdict', [
                  { when: '=vars.reviewOutcome == "Approve"', label: 'Approved', body: (a) => a },
                  { otherwise: true, label: 'Rejected', body: (a) => a.endEvent('claimRejected', { name: 'Claim rejected' }) },
                ]),
          },
        ])
        .scriptTask('settle', { name: 'Settle claim', script: 'return { settled: true };' })
        .endEvent('claimSettled', { name: 'Claim settled' })
        // Directly inside the iteration: a failure ends this claim, not the night.
        .eventSubProcess('claimFailures', { error: true, name: 'Claim failure' }, (h) =>
          h.scriptTask('escalateClaim', { name: 'Escalate claim', script: 'return { ok: true };' }).endEvent('claimEscalated', { name: 'Claim escalated' })),
    { name: 'Handle each claim', loop: { collection: '=vars.claims', itemVar: 'item' } },
  )
  .scriptTask('aggregate', { name: 'Total the results', script: 'return { ok: true };' })
  .plainTask('sendSummary', { name: 'Send summary to finance', element: 'bpmn:sendTask' })
  .endEvent('done', { name: 'Night complete' })
  .build();
```

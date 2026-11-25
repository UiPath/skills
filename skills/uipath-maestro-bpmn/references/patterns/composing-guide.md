# Composing Patterns

Read this when a process uses multiple patterns or when writing a shared join; a single-pattern guide is otherwise sufficient.

## Shared joins: the mechanism nesting hides

Most patterns turn on one step reached two ways: a dispatch gate (`smart-triage`), an action (`ai-decision-review`), or a rejection exit (`approval-chain`). Writing what happens next inside each arm duplicates the step per arm; `check`, `compile` and `validate` all pass the duplicate, and only the pattern's grader, or a reader, notices. Write the shared step once, by one of three forms, in this order of preference:

1. **Fall through.** Leave each arm that should reach the step empty or ending at its last element, then write the step AFTER `.choose()`. Falling-through arms join as `<choose id>_join`, emitted only when more than one does. An arm that must not reach it ends with an end event or `.goto()`. This works through nesting: an empty inner arm falls through both chooses.
2. **A gateway you name.** For routes fall-through cannot reach (a later arm, outer scope, or second stage), declare `.exclusiveGateway(id)`, send each route with `.goto(id)`, and wire its sole exit with `.sequenceFlow(id, next)`. A bare gateway's outgoing flow is never implied, even in sequence mode. The tiered reviewer in [ai-decision-review-guide.md](ai-decision-review-guide.md#variants) uses this form.
3. **A loop back to a gateway.** `.goto(id)` to an earlier gateway is itself a join; the reminder arm of `.race('wait', …)` ends in `.goto('wait')`.

Never `.goto()` an activity from two places. This fake join makes `check` warn `FAKE_JOIN` while `validate` says nothing; although the platform accepts and runs the activity, the graph lacks a join node, so a grader looking for the join finds none. A `.goto()` back to a human task to redo it (`examples/InvoiceEscalation.bpmn.ts`) has the same warning and is accepted there, never as a pattern merge.

After writing a pattern, run `uip maestro bpmn check <Name>.bpmn.ts --graph`; the shared step must appear once, with multiple incoming flows or behind a `_join`.

## Patterns are graph fragments

Guides show a standalone start event, but it is an artifact unless the pattern begins the process; remove it when inserting into the middle of an existing process.

Placement constraints:

- **`queue-distribution`'s performer:** its start event is the queue trigger, so the performer must begin the process; it cannot be inserted mid-process or nested in a sub-process.
- **`failure-escalation`:** an `.eventSubProcess()` with no flows in or out, placed directly inside the guarded container. Wrapping it in another sub-process changes which failures reach it.

These are engine behavior, not style.

## Four ways to join

Building from scratch with several patterns, the outermost one keeps its start event and the rest go inside it.

### Inserted inline

Drop the pattern's start event, continue from the preceding step into its first real node, and make its steps part of the surrounding chain. The default: use it whenever the work belongs in this process and there is no reason to encapsulate.

### Nested as a `.subProcess()`

The pattern's start event becomes the sub-process start; the sub-process owns incoming and outgoing flows. Give its body `.flowMode('sequence')`.

Prefer this for a `loop` over the pattern, its own `failure-escalation` net, or a collapsed box. A container provides no separate variables; see [Variables across a nesting boundary](#variables-across-a-nesting-boundary).

Risk-tiered `approval-chain` already works this way internally: the standard and extended chains are sub-processes the risk gate chooses between.

### Placed, not wired

`failure-escalation` composes by placement only: write `.eventSubProcess()` in the container whose failures it catches, with no flow to or from it.

### Dispatched by message to a separate process

Make downstream work its own Maestro process, started by a message, when it has its own lifecycle or trigger or should scale independently. `smart-triage`'s per-category steps are placeholders: dispatch keeps triage thin; inline steps make triage own every category's handling.

## Adding a pattern to a process that already runs

Insert only what the process lacks and bind to what it already has. Each guide's "Adapting it" identifies existing steps and the variable to bind instead of declaring.

Decompile the existing `.bpmn` with `--style nested` and edit that source; see [Brownfield](../bpmn-runtime.md#brownfield-editing). Leave untouched everything the pattern does not affect: element ids, flow ids (the `.flowIds([…])` pin table), `.preserve()` state, and imported connector data. This is a surgical edit, not regeneration.

## Scoping the failure net

One net covers its entire container, including nested sub-processes, because unhandled failures propagate outward container by container. It catches only failures raised in the container where it sits directly ([Events](../bpmn-runtime.md#events-and-timers)); a nested sub-process's unhandled failure surfaces as that sub-process failing in its parent, reaching the next outer net. A single process-level net is usual.

Add an inner net inside a looped sub-process or queue performer only for per-item handling: one bad item is recorded and the batch continues. Without an inner net, the first failure reaches the process-level net and ends the instance.

Choose among a net, an `onError` handler in one activity's body, and `retry` on the node using [Events](../bpmn-runtime.md#events-and-timers).

## Variables across a nesting boundary

Nesting does not create local variables. Variable ids are document-wide, and the runtime resolves `vars.<id>` in one flat namespace wherever declared ([Variables](../bpmn-runtime.md#variables-and-the-process-contract)). Nested patterns read parent variables by id without input mapping, and parents read nested writes without output mapping.

Independent state needs unique ids. If composed patterns each hold their own value of the same kind, rename it everywhere that pattern reads it, including its gate conditions: use `claimReviewOutcome` and `paymentReviewOutcome`, not two `reviewOutcome` declarations. A duplicate id is not a second variable; `check` refuses it as `DUPLICATE_DOCUMENT_ID`. Keep a shared name only when both patterns mean the same value, such as a nested review gating on its parent's score.

Looped sub-process iterations write the same ids. On the local engine, parallel iterations overwrite each other's writes; one variable collects all results only in a sequential loop. See [high-volume-batch-guide.md](high-volume-batch-guide.md#getting-results-to-aggregate).

## Worked combinations

| Combination | Outermost | How the rest join |
| --- | --- | --- |
| Batch of items, each AI-decided with review | `high-volume-batch` | `ai-decision-review` nested as the per-item sub-process |
| Triage inbound, then approve by category | `smart-triage` | `approval-chain` per category, dispatched by message |
| Queue performer with per-item error handling | `queue-distribution` performer | `failure-escalation` placed inside the performer |
| Add review to a process that already runs | the existing process | `ai-decision-review` inserted inline, no start event |
| Any production process | whichever owns the trigger | `failure-escalation` placed at process level |

The first row, written out: the review is the body of the looped sub-process, and its net sits directly inside that body, so one failed claim ends only its own iteration.
Each of the body's three exits (settled, rejected, escalated) appends to `claimResults`, and the loop is sequential so `aggregate` sees every claim, as in [high-volume-batch-guide.md](high-volume-batch-guide.md#getting-results-to-aggregate).

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('claims-nightly')
  .name('ClaimsNightly')
  .flowMode('sequence')
  .var('claims', 'jsonSchema')
  .var('aiConfidenceLevel', 'number', { default: 0 })
  .var('reviewOutcome', 'string')
  .var('claimResults', 'array', { default: [] })
  .startEvent('start', { name: 'Nightly', timer: { cycle: 'R/P1D' } })
  .scriptTask('fetchClaims', { name: 'Fetch claims', script: 'return { items: [] };', outputs: { claims: '=result.response.items' } })
  .subProcess(
    'eachClaim',
    (sp) =>
      sp
        .flowMode('sequence')
        .startEvent('claimStart')
        .scriptTask('score', { name: 'Score claim', script: 'return { confidence: 0.9 };', outputs: { aiConfidenceLevel: '=result.response.confidence' } })
        .choose('confidenceGate', [
          { when: '=js:vars.aiConfidenceLevel >= 0.85', label: 'Confident', body: (b) => b },
          {
            otherwise: true,
            label: 'Unsure',
            body: (b) =>
              b.humanTask('assessorReview', { name: 'Assessor review', form: { fields: [], outcomes: ['Approve', 'Reject'] }, outputs: { reviewOutcome: '=Action' } })
                .choose('assessorVerdict', [
                  { when: '=js:vars.reviewOutcome == "Approve"', label: 'Approved', body: (a) => a },
                  {
                    otherwise: true,
                    label: 'Rejected',
                    body: (a) =>
                      a.task('recordRejected', { name: 'Record rejection', set: { claimResults: '=js:vars.claimResults.concat([{ claim: iterator[0].item, outcome: "rejected" }])' } })
                        .endEvent('claimRejected', { name: 'Claim rejected' }),
                  },
                ]),
          },
        ])
        .scriptTask('settle', { name: 'Settle claim', script: 'return { settled: true };' })
        .task('recordSettled', { name: 'Record settlement', set: { claimResults: '=js:vars.claimResults.concat([{ claim: iterator[0].item, outcome: "settled" }])' } })
        .endEvent('claimSettled', { name: 'Claim settled' })
        // Directly inside the iteration: a failure ends this claim, not the night.
        .eventSubProcess('claimFailures', { error: true, name: 'Claim failure' }, (h) =>
          h.scriptTask('escalateClaim', { name: 'Escalate claim', script: 'return { ok: true };' })
            .task('recordEscalated', { name: 'Record escalation', set: { claimResults: '=js:vars.claimResults.concat([{ claim: iterator[0].item, outcome: "escalated" }])' } })
            .endEvent('claimEscalated', { name: 'Claim escalated' })),
    { name: 'Handle each claim', loop: { collection: '=js:vars.claims', itemVar: 'iterator[0]', sequential: true } },
  )
  // Every exit of the body appended to claimResults; sequential, so none was lost.
  .scriptTask('aggregate', { name: 'Total the results', script: 'return vars.claimResults.length;' })
  .plainTask('sendSummary', { name: 'Send summary to finance', element: 'bpmn:sendTask' })
  .endEvent('done', { name: 'Night complete' })
  .build();
```

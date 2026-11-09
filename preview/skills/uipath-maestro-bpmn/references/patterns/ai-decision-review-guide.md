# Pattern: `ai-decision-review`

AI produces a decision, a confidence gate auto-actions the clear cases, and a human reviews the rest.
Use it when some items are clear-cut, others need judgment, and someone must stay accountable for the non-trivial ones.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **One tunable threshold owns the split.** A single confidence gate separates the auto-action path from the review path, so how much the AI handles on its own is one number, not a topology change.
  The shape survives re-tuning.
- **Validation runs before the gate.** Malformed output is not low confidence, it is invalid, and it must reach a reviewer carrying the reason.
  Validating first lets one gate handle both "unsure" and "broken" without a second branch.
- **One action step, reached two ways.** Both the auto path and the approved review converge on one join, whose single outgoing flow feeds the action node.
  The action is implemented, bound, and configured once.
  Send both routes straight into the action node instead (a `.goto('performAction')` from the review arm) and you have a fake join, which `check` warns about as `FAKE_JOIN` and `validate` does not report at all.
- **Every item exits through a named outcome.** Auto-actioned, or rejected by a reviewer.
  That is what makes the decision auditable afterwards.

## Shape

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('claims-review')
  .name('ClaimsReview')
  .flowMode('sequence')
  .var('aiDecision', 'string')
  .var('aiConfidenceLevel', 'number', { default: 0 })
  .var('validationPassed', 'boolean', { default: false })
  .var('reviewOutcome', 'string')
  .startEvent('start', { name: 'Claim received', message: 'ClaimReceived' })
  .startAgent('analyze', { name: 'Score claim', process: 'ClaimScorer', folder: 'Shared', outputs: { aiDecision: '=Decision', aiConfidenceLevel: '=Confidence' } })
  .businessRule('validate', { name: 'Validate decision', process: 'ClaimDecisionRules', folder: 'Shared', outputs: { validationPassed: '=result.Validate.passed' } })
  // Two routes reach the action: the confident arm falls through, and the review
  // arm's Approve falls through. The join `confidenceGate_join` is merge_gate.
  .choose('confidenceGate', [
    { when: '=vars.aiConfidenceLevel >= 0.85 && vars.validationPassed', label: 'High confidence', body: (b) => b },
    {
      otherwise: true,
      label: 'Low confidence',
      body: (b) =>
        b.humanTask('humanReview', { name: 'Review claim', form: { fields: [], outcomes: ['Approve', 'Reject'] }, outputs: { reviewOutcome: '=Action' } })
          .choose('postReviewGate', [
            { when: '=vars.reviewOutcome == "Approve"', label: 'Approved', body: (a) => a },
            { otherwise: true, label: 'Rejected', body: (a) => a.endEvent('endRejected', { name: 'Rejected by reviewer' }) },
          ]),
    },
  ])
  .scriptTask('performAction', { name: 'Settle claim', script: 'return { settled: true };' })
  .endEvent('endActioned', { name: 'Claim settled' })
  .build();
```

The join is not written: the confident arm is empty and the review arm's `Approved` arm is empty, so both fall through and the builder emits `confidenceGate_join` in front of `performAction`.
That join is the merge gate.
The `Rejected` arm ends, so it does not reach the join.

| Node | Builder | Role |
| --- | --- | --- |
| `start` | `.startEvent()` with `message` | Entry |
| `analyze` | `.startAgent()` | Placeholder · insertion point |
| `validate` | `.businessRule()` | Mechanism |
| `confidenceGate` | `.choose()` | Mechanism |
| `confidenceGate_join` | implied by the two arms that fall through | Mechanism, joins the auto and approved routes |
| `performAction` | the statement after the choose | Placeholder · Mechanism: bind the target, but keep it one node after the choose |
| `humanReview` | `.humanTask()` | Mechanism |
| `postReviewGate` | `.choose()` inside the review arm | Mechanism |
| `endActioned` | `.endEvent()`, named | Mechanism |
| `endRejected` | `.endEvent()`, named | Mechanism |

`0.85` is an illustrative threshold.
Set it from the cost asymmetry between a wrong auto-action and a needless review: that number is the pattern's tuning knob, not part of its definition.

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `aiDecision` | string | | The categorical decision |
| `aiRationale` | string | | Reasoning, where the analyzer produces it |
| `aiConfidenceLevel` | number | `0` | Confidence, 0–1 |
| `validationPassed` | boolean | `false` | Did the output pass validation |
| `validationFailures` | jsonSchema | | Why it did not |
| `reviewOutcome` | string | | `Approve` or `Reject` |
| `reviewerRationale` | string | | Reviewer's free-text reasoning |

The gate's defaults fail closed: `0` and `false` send an item to review when the analyzer or the rule did not write the variable (a wrong output path, a skipped node).
A default that passes the gate, such as `0.95` or `true`, auto-actions every item whose mapping missed, which is the one failure this pattern exists to catch.

`aiRationale`, `validationFailures` and `reviewerRationale` are not in the sketch: map them from the analyzer, the rule and a form field when the reviewer or the audit needs them.
Names are recommended, not required: they keep processes comparable.
When inserting into a process that already holds one of these under another name, bind to the existing one.

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Single reviewer | — | The shape above |
| Tiered reviewer | Do reviewers differ in authority? | A stakes gate and two reviewer paths |
| Verification chain | Is a wrong auto-action costlier than a second AI call? | A second analyzer before validation |

**Tiered reviewer.** Two steps are now reached more than one way, so both joins are written as gateways: `seniorGate` in front of `seniorReview` (high stakes, or a junior `Escalate`) and `mergeGate` in front of `performAction` (confident, junior approve, or senior approve).
Fall-through cannot express either, so declare each with `.exclusiveGateway(id)`, send every route to it with `.goto(id)`, and wire its one way out with `.sequenceFlow(id, next)`, since a bare gateway's outgoing flow is never implied:

```ts
  .choose('stakesGate', [
    { when: '=vars.stakesValue >= 5000', label: 'High stakes', body: (b) => b.goto('seniorGate') },
    { otherwise: true, label: 'Low stakes', body: (b) => b.choose('confidenceGate', [ /* arms end in .goto('mergeGate'), .goto('seniorGate') or an end event */ ]) },
  ])
  .exclusiveGateway('seniorGate', { name: 'Senior review' })
  .humanTask('seniorReview', { form: { fields: [], outcomes: ['Approve', 'Reject'] }, outputs: { seniorOutcome: '=Action' } })
  .choose('seniorVerdict', [
    { when: '=vars.seniorOutcome == "Approve"', label: 'Approved', body: (c) => c.goto('mergeGate') },
    { otherwise: true, label: 'Rejected', body: (c) => c.endEvent('endSeniorRejected', { name: 'Rejected by senior' }) },
  ])
  .exclusiveGateway('mergeGate', { name: 'Approved' })
  .task('performAction')
  .endEvent('endActioned', { name: 'Actioned' })
  .sequenceFlow('seniorGate', 'seniorReview')
  .sequenceFlow('mergeGate', 'performAction')
```

Senior review has no `Escalate` outcome on purpose: a senior verdict that can escalate again loops.
Adds `stakesValue` (number), a domain signal such as loan amount or claim value, and `seniorOutcome` (string); `5000` is illustrative.

**Verification chain.** Insert a second `.startAgent('verifier', …)` between `analyze` and `validate`, and extend the gate to require agreement:
`'=vars.aiConfidenceLevel >= 0.85 && vars.verifierConfidence >= 0.85 && vars.verifierDecision == vars.aiDecision && vars.validationPassed'`.
Adds `verifierDecision` (string) and `verifierConfidence` (number).
Bind the verifier to a **different model** than the analyzer; the same model has the same blind spots, so the second call verifies nothing.

## What to bind

- **`analyze`**: the node that produces the decision at runtime, a UiPath agent (`.startAgent()`), Document Understanding, or a chain of both.
  Place and bind the node.
  Never decide the categories or hardcode a result while authoring.
  Its `outputs` keys are the process variables written (`aiDecision`, `aiConfidenceLevel`), and each value is an expression read against the agent's result (`'=Decision'`, `'=Confidence'`, the agent's output arguments).
  The confidence gate reads those variables, so a key spelled as the agent's argument instead leaves them at their defaults.
- **`performAction`**: the downstream target, an ERP, CRM, case system, or outbound message: `.connector()`, `.http()`, `.startProcess()`.
- **`validate`**: `.businessRule()`, a deployed BusinessRules package addressed by name.
  A decision's column reads `=result.<Decision>.<column>` ([Work dispatch](../bpmn-runtime.md#http-and-orchestrator-work)).
- **`humanReview`**: `.humanTask()`.
  Route `postReviewGate` on the exact variable its `outputs` maps `=Action` into, not a copy.
- **Review SLA**: a non-interrupting `t.onTimer(…, { interrupting: false }, …)` in the human task's body for reminders; see [Human tasks](../bpmn-runtime.md#human-task-outcomes).

## Adapting it

The commonest reduction: the process already scores the item.
Insert only `validate` onward, gate on the existing score variable, and add no second analyzer.

The action step already exists too.
On an imported process, decompile it with `--style nested` ([Brownfield](../bpmn-runtime.md#brownfield-editing)) and put the new `confidenceGate` choose directly in front of the existing action, so the action becomes the statement after it.
Keep the action's id: `merge` keys on it, and a renamed action reads as a delete plus an add.
Do not route the existing flow into the action from both new routes; that is the fake join above.

`validate` is the one load-bearing step you can remove, and only when its mechanism is vacuous rather than unwanted.
If the analyzer's output is schema-constrained and cannot be malformed, there is no invalid case to route, so simplify the gate to the confidence term alone.
If malformed output is merely unlikely, keep it.

Keep both named end events regardless; that is the audit trail.

## Composing

Nested inside `high-volume-batch` this becomes the per-item sub-process.
Pair it with `failure-escalation` so a failure in `analyze` or `performAction` does not vanish.
See [composing-guide.md](composing-guide.md).

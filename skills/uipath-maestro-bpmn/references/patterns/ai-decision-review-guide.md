# Pattern: `ai-decision-review`

AI makes a decision; one confidence gate auto-actions clear cases and sends the rest to accountable human review. Use this when some items are clear-cut and others require judgment.

## Why it works

These four carry the shape.
Change one and you are building something else.

- One tunable confidence threshold owns the auto-action/review split.
- Validation precedes the gate: malformed output is not low confidence, it is invalid, and it must reach a reviewer carrying the reason.
- Auto and approved-review routes converge at one join, then one outgoing flow reaches one action node. Do not send both directly to the action (for example, `.goto('performAction')` from the review arm): that fake join produces `FAKE_JOIN` from `check`, while `validate` does not.
- Every item exits through a named outcome: auto-actioned or reviewer-rejected.

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
  .businessRule('validate', { name: 'Validate decision', process: 'ClaimDecisionRules', folder: 'Shared', outputs: { validationPassed: '=result.decision1.passed' } })
  // Empty confident and approved arms fall through to the emitted merge join.
  .choose('confidenceGate', [
    { when: '=js:vars.aiConfidenceLevel >= 0.85 && vars.validationPassed', label: 'High confidence', body: (b) => b },
    {
      otherwise: true,
      label: 'Low confidence',
      body: (b) =>
        b.humanTask('humanReview', { name: 'Review claim', form: { fields: [], outcomes: ['Approve', 'Reject'] }, outputs: { reviewOutcome: '=Action' } })
          .choose('postReviewGate', [
            { when: '=js:vars.reviewOutcome == "Approve"', label: 'Approved', body: (a) => a },
            { otherwise: true, label: 'Rejected', body: (a) => a.endEvent('endRejected', { name: 'Rejected by reviewer' }) },
          ]),
    },
  ])
  .scriptTask('performAction', { name: 'Settle claim', script: 'return { settled: true };' })
  .endEvent('endActioned', { name: 'Claim settled' })
  .build();
```

The empty confident and approved arms emit `confidenceGate_join` before `performAction`, joining auto and approved-review routes; the rejected arm ends and cannot reach it.

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

`0.85` is illustrative: tune it from wrong auto-action cost versus needless review; it is the tuning knob, not the definition.

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `aiDecision` | string | | Categorical decision |
| `aiRationale` | string | | Analyzer reasoning, where produced |
| `aiConfidenceLevel` | number | `0` | Confidence, 0–1 |
| `validationPassed` | boolean | `false` | Whether validation passed |
| `validationFailures` | jsonSchema | | Why validation failed |
| `reviewOutcome` | string | | `Approve` or `Reject` |
| `reviewerRationale` | string | | Reviewer's free-text reasoning |

Defaults fail closed: `0` and `false` send unmapped items to review (for example, a wrong output path or skipped node); `0.95` or `true` would auto-action every unmapped item. The sketch omits `aiRationale`, `validationFailures`, and `reviewerRationale`; map them from the analyzer, rule, and form field when needed for review or audit. Names are recommended, not required; bind differently named existing variables when inserting into an existing process.

## Variants

| Variant | Question | Delta |
| --- | --- | --- |
| Single reviewer | — | Shape above |
| Tiered reviewer | Do reviewers differ in authority? | Stakes gate and two reviewer paths |
| Verification chain | Is a wrong auto-action costlier than a second AI call? | Second analyzer before validation |

**Tiered reviewer.** Declare both gateways because each has multiple incoming routes: `seniorGate` before `seniorReview` (high stakes or junior `Escalate`) and `mergeGate` before `performAction` (confident, junior approve, or senior approve). Fall-through cannot express these: declare each with `.exclusiveGateway(id)`, route every path with `.goto(id)`, and wire its sole output with `.sequenceFlow(id, next)` because a bare gateway's outgoing flow is never implied.

```ts
  .choose('stakesGate', [
    { when: '=js:vars.stakesValue >= 5000', label: 'High stakes', body: (b) => b.goto('seniorGate') },
    { otherwise: true, label: 'Low stakes', body: (b) => b.choose('confidenceGate', [ /* arms end in .goto('mergeGate'), .goto('seniorGate') or an end event */ ]) },
  ])
  .exclusiveGateway('seniorGate', { name: 'Senior review' })
  .humanTask('seniorReview', { form: { fields: [], outcomes: ['Approve', 'Reject'] }, outputs: { seniorOutcome: '=Action' } })
  .choose('seniorVerdict', [
    { when: '=js:vars.seniorOutcome == "Approve"', label: 'Approved', body: (c) => c.goto('mergeGate') },
    { otherwise: true, label: 'Rejected', body: (c) => c.endEvent('endSeniorRejected', { name: 'Rejected by senior' }) },
  ])
  .exclusiveGateway('mergeGate', { name: 'Approved' })
  .task('performAction')
  .endEvent('endActioned', { name: 'Actioned' })
  .sequenceFlow('seniorGate', 'seniorReview')
  .sequenceFlow('mergeGate', 'performAction')
```

Senior review intentionally has no `Escalate` outcome: another escalation would loop. Add `stakesValue` (number), a domain signal such as loan amount or claim value, and `seniorOutcome` (string); `5000` is illustrative.

**Verification chain.** Insert `.startAgent('verifier', …)` between `analyze` and `validate`, and require agreement in the gate:
`'=js:vars.aiConfidenceLevel >= 0.85 && vars.verifierConfidence >= 0.85 && vars.verifierDecision == vars.aiDecision && vars.validationPassed'`.
Add `verifierDecision` (string) and `verifierConfidence` (number). Bind the verifier to a **different model**: the same model shares blind spots and verifies nothing.

## What to bind

- **`analyze`**: Bind the runtime decision producer: UiPath agent (`.startAgent()`), Document Understanding, or both. Never choose categories or hardcode a result while authoring. Its `outputs` keys are process variables (`aiDecision`, `aiConfidenceLevel`); values read the agent result (`'=Decision'`, `'=Confidence'`, or output arguments). A key matching the agent argument but not the process variable leaves gate inputs at their defaults.
- **`performAction`**: Bind the downstream ERP, CRM, case system, or outbound message with `.connector()`, `.http()`, or `.startProcess()`.
- **`validate`**: Use `.businessRule()` for the deployed BusinessRules package addressed by name. Key its result by the decision's `OutputArguments` property name (such as `decision1`), not display name ([Work dispatch](../bpmn-runtime.md#http-and-orchestrator-work)).
- **`humanReview`**: Use `.humanTask()` and route `postReviewGate` on the exact variable its `outputs` maps `=Action` into, not a copy.
- **Review SLA**: Configure the Task timer in the Studio Web task-panel; `.humanTask()` cannot write it. See [Human tasks](../bpmn-runtime.md#human-task-outcomes).

## Adapting it

If the process already scores items, insert only `validate` onward, gate on its existing score, and do not add an analyzer.

If the action already exists, decompile an imported process with `--style nested` ([Brownfield](../bpmn-runtime.md#brownfield-editing)), place `confidenceGate` directly before that action, and make the action the statement after it. Keep its id: `merge` keys on it, and renaming it is a delete plus an add. Do not route both new paths into the action; that creates the fake join described above.

Remove `validate` only when its mechanism is vacuous: if schema-constrained analyzer output cannot be malformed, route on confidence alone. If malformed output is merely unlikely, keep validation. Keep both named end events for the audit trail.

## Composing

Nested inside `high-volume-batch`, this is the per-item subprocess. Pair it with `failure-escalation` so failures in `analyze` or `performAction` do not vanish. See [composing-guide.md](composing-guide.md).

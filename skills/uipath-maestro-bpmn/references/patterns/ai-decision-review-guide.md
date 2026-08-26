# Pattern: `ai-decision-review`

AI produces a decision, a confidence gate auto-actions the clear cases, and a
human reviews the rest. Use it when some items are clear-cut, others need
judgment, and someone must stay accountable for the non-trivial ones.

## Why it works

These four carry the shape. Change one and you are building something else.

- **One tunable threshold owns the split.** A single confidence gate separates
  the auto-action path from the review path, so how much the AI handles on its
  own is one number, not a topology change. The shape survives re-tuning.
- **Validation runs before the gate.** Malformed output is not low confidence,
  it is invalid, and it must reach a reviewer carrying the reason. Validating
  first lets one gate handle both "unsure" and "broken" without a second branch.
- **One action step, reached two ways.** The approve edge routes back into the
  same action node the auto path uses. The action is implemented, bound, and
  configured once.
- **Every item exits through a named outcome.** Auto-actioned, or rejected by a
  reviewer. That is what makes the decision auditable afterwards.

## Shape

Roles: **Entry** — omit when inserting into a process that already runs.
**Mechanism** — changing it changes the pattern. **Placeholder** — bind it, or
skip it if the process already does this.

| Node | Element | Role |
| --- | --- | --- |
| `start` | `bpmn:startEvent` + message event definition | Entry |
| `analyze` | `bpmn:serviceTask` | Placeholder · insertion point |
| `validate` | `bpmn:businessRuleTask` | Mechanism |
| `confidence_gate` | `bpmn:exclusiveGateway` | Mechanism |
| `perform_action` | `bpmn:serviceTask` | Placeholder · Mechanism — bind the target, but keep it a single node with two inbound edges |
| `human_review` | `bpmn:userTask` | Mechanism |
| `post_review_gate` | `bpmn:exclusiveGateway` | Mechanism |
| `end_actioned` | `bpmn:endEvent` | Mechanism |
| `end_rejected` | `bpmn:endEvent` | Mechanism |

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `start` → `analyze` | | |
| `analyze` → `validate` | | |
| `validate` → `confidence_gate` | | |
| `confidence_gate` → `perform_action` | High confidence | `=vars.aiConfidenceLevel >= 0.85 && vars.validationPassed` |
| `confidence_gate` → `human_review` | Low confidence | `=vars.aiConfidenceLevel < 0.85 \|\| !vars.validationPassed` |
| `perform_action` → `end_actioned` | | |
| `human_review` → `post_review_gate` | | |
| `post_review_gate` → `perform_action` | Approved | `=vars.reviewOutcome == "Approve"` |
| `post_review_gate` → `end_rejected` | Rejected | `=vars.reviewOutcome == "Reject"` |

`0.85` is an illustrative threshold. Set it from the cost asymmetry between a
wrong auto-action and a needless review — that number is the pattern's tuning
knob, not part of its definition.

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `aiDecision` | string | | The categorical decision |
| `aiRationale` | string | | Reasoning, where the analyzer produces it |
| `aiConfidenceLevel` | double | `0.95` | Confidence, 0–1 |
| `validationPassed` | boolean | `true` | Did the output pass validation |
| `validationFailures` | jsonSchema | | Why it did not |
| `reviewOutcome` | string | | `Approve` or `Reject` |
| `reviewerRationale` | string | | Reviewer's free-text reasoning |
| `actionTakenResponse` | jsonSchema | | Response from the action target |

Names are recommended, not required — they keep processes comparable. When
inserting into a process that already holds one of these under another name,
bind to the existing one.

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Single reviewer | — | The shape above |
| Tiered reviewer | Do reviewers differ in authority? | Stakes gate + two reviewer paths |
| Verification chain | Is a wrong auto-action costlier than a second AI call? | Second analyzer before validation |

**Tiered reviewer.** Insert `stakes_gate` (`bpmn:exclusiveGateway`) between
`validate` and `confidence_gate`, and split `human_review` into `junior_review`
and `senior_review`.

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `stakes_gate` → `senior_review` | High stakes | `=vars.stakesValue >= 5000` |
| `stakes_gate` → `confidence_gate` | Low stakes | default |
| `confidence_gate` → `junior_review` | Low confidence | as above |
| `senior_review` → `perform_action` | | no gate |
| `post_review_gate` → `senior_review` | Escalate | `=vars.reviewOutcome == "Escalate"` |

Adds `stakesValue` (double) — a domain signal such as loan amount or claim
value. `5000` is illustrative. Senior review has no post-review gate on
purpose: routing a senior verdict through a gate that can escalate again loops.

**Verification chain.** Insert `verifier` (`bpmn:serviceTask`) between `analyze`
and `validate`, and extend both gate conditions to require agreement:

- Auto — `=vars.aiConfidenceLevel >= 0.85 && vars.verifierConfidence >= 0.85 && vars.verifierDecision == vars.aiDecision && vars.validationPassed`
- Review — negate it

Adds `verifierDecision` (string) and `verifierConfidence` (double). Bind the
verifier node to a **different model** than the analyzer node; the same model
has the same blind spots, so the second call verifies nothing.

## What to bind

- **`analyze`** — the node that produces the decision at runtime: a UiPath
  agent, Document Understanding, or a chain of both. Place and bind the node.
  Never decide the categories or hardcode a result while authoring.
- **`perform_action`** — the downstream target: ERP, CRM, case system, outbound
  message.
- **`validate`** — `Orchestrator.BusinessRules`. Rules are uploaded to
  Orchestrator separately; the BPMN references them.
- **`human_review`** — `Actions.HITL`. Route `post_review_gate` on the exact
  variable the template's `<uipath:output ... var="...">` binds, not a copy.
- **Review SLA** — the timer and its breach outcome are properties of the user
  task, not a boundary timer (SKILL.md rule 12).

Fetch every payload through
[registry-workflow.md](../registry-workflow.md); confirm type names with
`registry list` rather than trusting the ones above.

## Adapting it

The commonest reduction: the process already scores the item. Insert only
`validate` onward, bind the gate to the existing score variable, and add no
second analyzer.

`validate` is the one load-bearing step you can remove, and only when its
mechanism is vacuous rather than unwanted: if the analyzer's output is
schema-constrained and cannot be malformed, there is no invalid case to route,
so simplify the gate to the confidence term alone. If malformed output is merely
unlikely, keep it.

Keep both named end events regardless; that is the audit trail.

## Composing

Nested inside `high-volume-batch` this becomes the per-item subprocess. Pair it
with `failure-escalation` so a failure in `analyze` or `perform_action` does not
vanish. See [composing-guide.md](composing-guide.md).

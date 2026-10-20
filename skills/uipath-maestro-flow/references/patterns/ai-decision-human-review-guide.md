# Pattern: `ai-decision-human-review`

An agent makes a decision and a person reviews it before the flow acts on it. The
variants differ in who brings the person in: a confidence threshold, the agent
itself, or every item. Use it when the action is consequential and someone must
stay accountable for the calls the agent cannot make alone.

## Why it works

- **One action step, reached two ways.** The auto route and the reviewer's
  approval both end at the same `applyDecision`. The action is chosen, bound and
  configured once; a second copy per route drifts.
- **The agent's output is typed.** The gate and the review form read named
  fields (`decision`, `confidence`, `rationale`), never text parsed out of a
  reply, so the routing is an expression on data.
- **One tunable number owns the split.** In `human-fallback` a single
  confidence threshold decides how much the agent handles alone. Re-tuning it
  never changes the topology.
- **Every item leaves through a named outcome.** Applied, or rejected or taken
  over by a person. A rejection or a takeover ends at its own End, which is the
  audit trail; an applied item continues.

## Shape

The default variant, `human-fallback`:

| Step | Node | Builder | Role |
| --- | --- | --- | --- |
| `analyzeItem` | `uipath.agent.autonomous` | `inlineAgent({ returns })` | Mechanism |
| `confidenceGate` | `core.logic.decision` | `.branch(...)` | Mechanism |
| `reviewDecision` | `uipath.human-in-the-loop.*` | `.stepSwitch(..., hitl({ outcomes }), arms)` | Mechanism |
| `applyDecision` | the action's node | per SKILL.md's node table | Placeholder · Mechanism: one node, reached by both routes |
| `endApplied` | `core.control.end` | `.return(...)` | Entry: the flow continues here when steps follow |
| `endRejected` | `core.control.end` | `.return(...)` in the Reject arm | Mechanism |

| From | Port | To |
| --- | --- | --- |
| `analyzeItem` | `success` | `confidenceGate` |
| `confidenceGate` | `true` (`confidence >= 0.8`) | `applyDecision` |
| `confidenceGate` | `false` | `reviewDecision` |
| `reviewDecision` | `outcome-approve` | `applyDecision` |
| `reviewDecision` | `outcome-reject` | `endRejected` |
| `applyDecision` | | `endApplied` |

`analyzeItem` returns `decision` (string), `rationale` (string) and `confidence`
(number, 0 to 1). The review form shows all three as `direction: 'input'`
fields. The canvas uses a quick form; pick the `hitl` variant the request names
([hitl.md](../hitl.md)).

In the builder, the gate's `true` arm holds `applyDecision`, its `false` arm
holds the `.stepSwitch`, and the Approve arm ends `.stepToRef('applyDecision')`.
These are the canvas's names and port directions.

## Variants

| Variant | Who brings the person in | Delta |
| --- | --- | --- |
| `human-fallback` | A confidence threshold | The shape above |
| `asks-for-help` | The agent | The agent returns `needsHelp` and `question`; the gate routes on `needsHelp` |
| `every-item-reviewed` | Always | No gate; every item goes to the form |

**`asks-for-help`.** `prepareAction` returns `proposedAction`, `riskLevel`,
`summary`, `needsHelp` (boolean) and `question`. When `needsHelp` is true, the
form shows the question and has an `answer` output field and two outcomes:
**Answer** goes back to `prepareAction`, whose prompt reads the answer so the
next pass can finish, and **Take over** ends at its own End. In the builder, the
Answer arm is `.stepToRef('prepareAction')`.

**`every-item-reviewed`.** `prepareAction` returns `proposedAction`, `riskLevel`
and `summary`, and goes straight to the form. The form has a `reviewerNotes`
output field and three outcomes: **Approve** goes to `applyAction`, **Send back**
returns to `prepareAction` with the notes in its prompt, and **Take over** ends.

In both loop-back variants the agent runs again, so it cannot read the trigger's
output or the form's output directly: `validate` refuses a read of a step that
runs on only some of the paths reaching the agent. Carry the item and the
person's answer or notes in flow variables: a `.var()` set with `{ updates }` on
a step before the agent, and on the form. A variable cannot share an input's
name (`VARIABLE_NAME_COLLISION`).

Neither loop has an iteration cap. A person ends it with Take over; add a
counter only when the request bounds the retries.

## What to bind

- **The agent** (`analyzeItem` / `prepareAction`): a published agent whose
  output carries these fields, else an `inlineAgent` with `returns`, never
  `mock()`. Write its prompt.
- **The action** (`applyDecision` / `applyAction`): the downstream target, such
  as an RPA workflow, a connector, or a subflow, chosen by rule 1.
- **The form**: route its outcomes on the outcome names, not on a field.

## Adapting it

The commonest reduction: the flow already has an agent that scores the item and
an action step after it. Insert only `confidenceGate` and `reviewDecision`. Bind
the gate to the existing confidence field, keep the existing action as
`applyDecision`, and retarget its inbound edge at the gate. Do not add a second
analyzer or a second copy of the action. Keep `endRejected` separate from
`endApplied`.

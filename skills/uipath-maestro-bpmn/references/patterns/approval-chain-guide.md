# Pattern: `approval-chain`

A request passes through several approvers before it can be fulfilled. Use it
when sign-off is needed from more than one person or group, and a rejection at
any point should stop the request.

## Why it works

These four carry the shape. Change one and you are building something else.

- **A gateway after every stage, and rejection exits.** A stage is one
  approver, or a parallel group after its join. The next stage is reachable only
  through the gate's approve branch, so the chain stops at the first rejected
  stage. A parallel group cannot stop early: its join waits for every approver,
  so its gate reads all their verdicts at once. Every reject edge converges on
  `reject_merge`, which feeds one shared notify-and-end pair, so adding an
  approver adds a row, not a new terminal branch. Wiring the reject edges
  straight into `notify_rejected` is a fake join (`FAKE_JOIN`) that `validate`
  does not report; see [structural-bpmn.md](../structural-bpmn.md#gateways).
- **Per-approver outcome variables.** Each step records its own verdict and
  rationale. A single shared `outcome` variable would let the last approver
  overwrite the audit trail of the ones before.
- **Ordering and depth are separate questions.** Sequential and parallel answer
  *in what order*. Risk-tiered answers *how much approval at all*, and routes to
  a chain of either shape. That is why risk-tiered reuses the others as
  subprocesses instead of redrawing them.
- **Unclassified risk takes the longest chain.** The risk gateway's default
  sequence flow points at the extended chain, so a gap in the rules over-scrutinises
  rather than under-scrutinises.

## Shape

Sequential is the base shape. `N` approvers is illustrative — three below, but
the row repeats for however many the policy needs.

| Node | Element | Role |
| --- | --- | --- |
| `start` | `bpmn:startEvent` + message event definition | Entry |
| `approver1..N` | `bpmn:userTask` | Mechanism · insertion point |
| `gate1..N` | `bpmn:exclusiveGateway` | Mechanism |
| `fulfill` | `bpmn:serviceTask` | Placeholder |
| `notify` | `bpmn:sendTask` | Placeholder |
| `end_fulfilled` | `bpmn:endEvent` | Mechanism |
| `reject_merge` | `bpmn:exclusiveGateway` | Mechanism, joins the reject edges |
| `notify_rejected` | `bpmn:sendTask` | Placeholder |
| `end_rejected` | `bpmn:endEvent` | Mechanism |

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `start` → `approver1` | | |
| `approverI` → `gateI` | | |
| `gateI` → `approverI+1` | Approve | `=vars.approvalIOutcome == "Approve"` |
| `gateN` → `fulfill` | Approve | `=vars.approvalNOutcome == "Approve"` |
| `gateI` → `reject_merge` | Rejected | `=vars.approvalIOutcome == "Reject"` |
| `reject_merge` → `notify_rejected` | | |
| `fulfill` → `notify` → `end_fulfilled` | | |
| `notify_rejected` → `end_rejected` | | |

| Variable | Type | Holds |
| --- | --- | --- |
| `requestId` | string | Identifier of the request |
| `requestType` | string | Category — vendor onboarding, expense, access |
| `requesterId` | string | Who raised it |
| `requestDetails` | jsonSchema | Payload: amount, sensitivity, decision fields |
| `approvalIOutcome` | string | `Approve` or `Reject`, one per approver |
| `approvalIRationale` | string | That approver's reasoning |
| `fulfillmentResponse` | jsonSchema | Response from the fulfillment target |

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Sequential | — | The shape above |
| Parallel | Does order matter? | Fork/join around simultaneous approvals |
| Risk-tiered | How much approval does this request need? | Risk gateway selecting between chains |

**Parallel.** Replace the approver rows with a `bpmn:parallelGateway` fork, one
`bpmn:userTask` per approver, a `bpmn:parallelGateway` join, and a single
`bpmn:exclusiveGateway` verdict. With one gate there is nothing to merge, so
`decision` routes straight to `notify_rejected`. Outcome variables are suffixed
`A`/`B`/`C` rather than numbered, since there is no order to number.

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `join` → `decision` | | |
| `decision` → `notify_rejected` | No | `=vars.approvalAOutcome == "Reject" \|\| vars.approvalBOutcome == "Reject" \|\| vars.approvalCOutcome == "Reject"` |
| `decision` → `fulfill` | Yes | default |

The join waits for every branch, so the verdict runs once with all outcomes
present. All-must-approve is the shape; the verdict condition is where a quorum
rule would go instead.

**Risk-tiered.** Insert `evaluate` (`bpmn:businessRuleTask`) and `risk_gate`
(`bpmn:exclusiveGateway`) after the start, `fulfill_merge`
(`bpmn:exclusiveGateway`) before `fulfill`, and put the chains inside
`bpmn:subProcess` nodes.

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `risk_gate` → `fulfill_merge` | Low | `=vars.riskTier == "low"` |
| `risk_gate` → `standard_chain` | Standard | `=vars.riskTier == "standard"` |
| `risk_gate` → `extended_chain` | High | default |
| `standard_chain` / `extended_chain` → `approved_gate` | | |
| `approved_gate` → `notify_rejected` | No | any `approvalIOutcome == "Reject"` |
| `approved_gate` → `fulfill_merge` | Yes | default |
| `fulfill_merge` → `fulfill` | | |

Adds `riskTier` (string: `low` / `standard` / `high`). Low risk reaches
`fulfill` with no human step at all — that is the point of the tier. Both chains
share the same approver variables because only one runs per instance.

## What to bind

- **Approver tasks** — `Actions.HITL`. Resolving *who* approves is a lookup
  against your directory; the BPMN holds the task, not the roster.
- **Per-step SLA** — timer, reassignment, and breach outcome are properties of
  the user task, not boundary timers (SKILL.md rule 12).
- **Segregation of duties** — enforce at approver lookup, so no one person signs
  consecutive steps. It is not a BPMN construct.
- **`evaluate`** — `Orchestrator.BusinessRules`, with rules uploaded to
  Orchestrator separately.
- **`fulfill`** — ERP, CRM, provisioning system. **`notify`** — email, chat,
  requester callback.

Fetch payloads through [registry-workflow.md](../registry-workflow.md).

## Adapting it

Change the approver count freely; the row is the unit. Two approvers is a chain,
six is a chain.

Mix the shapes per stage. A parallel group followed by a sequential approver
gets its verdict gateway after the join and before that approver: approve to
the approver, reject to `reject_merge`.

Reuse the shape for any all-must-agree sign-off, not only approvals — a
multi-party sign-off on a document or a release gate is the same topology.

Drop `notify` when the requester is a system that reads the outcome rather than
a person who needs telling. Keep both named end events.

## Composing

Risk-tiered is already a composition: the chains are `bpmn:subProcess` nodes,
and either can hold the sequential or the parallel shape. Add
`failure-escalation` so a failure in `fulfill` does not vanish silently. See
[composing-guide.md](composing-guide.md).

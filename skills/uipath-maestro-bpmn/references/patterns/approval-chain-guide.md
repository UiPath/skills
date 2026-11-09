# Pattern: `approval-chain`

A request passes through several approvers before it can be fulfilled.
Use it when sign-off is needed from more than one person or group, and a rejection at any point should stop the request.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **A gate after every stage, and rejection exits.** A stage is one approver, or a parallel group after its join.
  The next stage is reachable only through the gate's approve arm, so the chain stops at the first rejected stage.
  A parallel group cannot stop early: its join waits for every approver, so its gate reads all their verdicts at once.
  Every reject converges on one shared notify-and-end pair, so adding an approver adds a stage, not a new terminal branch.
- **Per-approver outcome variables.** Each step records its own verdict and rationale.
  A single shared `outcome` variable would let the last approver overwrite the audit trail of the ones before.
- **Ordering and depth are separate questions.** Sequential and parallel answer *in what order*.
  Risk-tiered answers *how much approval at all*, and routes to a chain of either shape.
  That is why risk-tiered reuses the others as sub-processes instead of redrawing them.
- **Unclassified risk takes the longest chain.** The risk gate's `otherwise` arm is the extended chain, so a gap in the rules over-scrutinises rather than under-scrutinises.

## Shape

Approval continues INWARD and rejection falls OUT.
Each gate's approve arm holds the next stage; its reject arm is empty, so it falls through to the statement after the whole chain.
That statement is the shared rejection exit, and the join the builder emits in front of it (`panelVerdict_join`) is the reject merge.
Writing a separate `notifyRejected` inside every reject arm, or a `.goto('notifyRejected')` from each, is what the shape avoids: the first duplicates the exit per approver, and the second is a fake join on a task (`check` warns `FAKE_JOIN`; `validate` does not report it).

The example mixes the shapes the way a real policy does: a parallel pair, then a sequential final approver.

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

const review = (outcome: string, rationale: string) => ({
  form: { fields: [{ id: 'rationale', label: 'Reasoning', type: 'string' as const, direction: 'output' as const }], outcomes: ['Approve', 'Reject'] },
  outputs: { [outcome]: '=Action', [rationale]: '=rationale' },
});

export default bpmn('vendor-onboarding')
  .name('VendorOnboarding')
  .flowMode('sequence')
  .var('complianceOutcome', 'string')
  .var('complianceRationale', 'string')
  .var('financeOutcome', 'string')
  .var('financeRationale', 'string')
  .var('managerOutcome', 'string')
  .var('managerRationale', 'string')
  .startEvent('start', { name: 'Request received', message: 'VendorOnboardingRequested' })
  .fork('panel', [
    (b) => b.humanTask('complianceReview', { name: 'Compliance review', ...review('complianceOutcome', 'complianceRationale') }),
    (b) => b.humanTask('financeReview', { name: 'Finance review', ...review('financeOutcome', 'financeRationale') }),
  ])
  // Approval continues INWARD; every rejection falls OUT to the statement after
  // the chain. The joins the arms imply are the one shared reject merge.
  .choose('panelVerdict', [
    {
      when: '=vars.complianceOutcome == "Approve" && vars.financeOutcome == "Approve"',
      label: 'Both approve',
      body: (b) =>
        b.humanTask('managerReview', { name: 'Manager review', ...review('managerOutcome', 'managerRationale') })
          .choose('managerVerdict', [
            {
              when: '=vars.managerOutcome == "Approve"',
              label: 'Approve',
              body: (a) => a.scriptTask('provision', { name: 'Provision vendor', script: 'return { ok: true };' })
                .plainTask('notifyApproved', { name: 'Tell requester', element: 'bpmn:sendTask' })
                .endEvent('provisioned', { name: 'Vendor provisioned' }),
            },
            { otherwise: true, label: 'Reject', body: (a) => a },
          ]),
    },
    { otherwise: true, label: 'Rejected', body: (b) => b },
  ])
  .plainTask('notifyRejected', { name: 'Tell requester it was rejected', element: 'bpmn:sendTask' })
  .endEvent('rejected', { name: 'Request rejected' })
  .build();
```

| Node | Builder | Role |
| --- | --- | --- |
| `start` | `.startEvent()` with `message` | Entry |
| `complianceReview`, `financeReview` | `.humanTask()` inside `.fork()` | Mechanism · insertion point |
| `panelVerdict` | `.choose()` after the fork's join | Mechanism |
| `managerReview` | `.humanTask()` in the approve arm | Mechanism |
| `managerVerdict` | `.choose()` | Mechanism |
| `provision` | the work in the last approve arm | Placeholder |
| `notifyApproved` | a send step | Placeholder |
| `provisioned` | `.endEvent()`, named | Mechanism |
| `panelVerdict_join` | implied by the reject arms that fall through | Mechanism, the reject merge |
| `notifyRejected` | the statement after the chain | Placeholder |
| `rejected` | `.endEvent()`, named | Mechanism |

| Variable | Type | Holds |
| --- | --- | --- |
| `requestId` | string | Identifier of the request |
| `requestDetails` | jsonSchema | Payload: amount, sensitivity, decision fields |
| `<approver>Outcome` | string | `Approve` or `Reject`, one per approver |
| `<approver>Rationale` | string | That approver's reasoning, one per approver |

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Sequential | — | Each approve arm holds the next approver and its gate |
| Parallel | Does order matter? | A `.fork()` of approvers and one verdict gate after it |
| Risk-tiered | How much approval does this request need? | A risk gate choosing between chains |

**Sequential.** Nest one stage per approver: `.humanTask('approver1', …).choose('gate1', [{ when: approve, body: (b) => b.humanTask('approver2', …).choose('gate2', [ … ]) }, { otherwise: true, body: (b) => b }])`.
Every `otherwise` arm is empty and falls out to the same rejection exit.

**Parallel.** `.fork()` one `.humanTask()` per approver, then one verdict `.choose()`.
The fork's join waits for every arm, so the verdict reads all outcomes at once; all-must-approve is the shape, and the verdict's `when` is where a quorum rule would go instead.

**Risk-tiered.** Put `.businessRule('evaluate', …)` first and a `riskGate` choose after it.
The low-risk arm is empty, so a low-risk request reaches fulfilment with no human step at all, which is the point of the tier.
The standard and extended arms each hold a `.subProcess()` containing a chain; the `otherwise` arm is the extended one.
An `approvedGate` choose after `riskGate` reads the outcome variables and sends a reject to the shared exit.
Adds `riskTier` (string: `low` / `standard` / `high`).
Both chains can share the approver variables because only one runs per instance.

## What to bind

- **Approver tasks**: `.humanTask()`, an inline form unless a deployed Action App is named.
  Map `=Action` and each form field into that approver's own variables.
  Resolving *who* approves is a lookup against your directory; the process holds the task, not the roster.
- **Per-step reminders and SLA**: a non-interrupting `t.onTimer()` in the task's body; see [Human tasks](../bpmn-runtime.md#human-task-outcomes).
- **Segregation of duties**: enforce it at approver lookup, so no one person signs consecutive steps.
  It is not a BPMN construct.
- **`evaluate`**: `.businessRule()`, a deployed BusinessRules package addressed by name.
- **`provision`**: ERP, CRM, provisioning system. **`notify*`**: email, chat, requester callback.
  A bare `bpmn:sendTask` placeholder validates with a warning that it invokes nothing; bind it to a connector before it runs ([Connectors](../connectors.md)).

## Adapting it

Change the approver count freely; the stage is the unit.
Two approvers is a chain, six is a chain.

Mix the shapes per stage, as the example does.
A parallel group followed by a sequential approver gets its verdict gate after the fork and before that approver: approve to the approver, reject falls out.

Reuse the shape for any all-must-agree sign-off, not only approvals: a multi-party sign-off on a document or a release gate is the same topology.

Drop `notifyApproved` when the requester is a system that reads the outcome rather than a person who needs telling.
Keep both named end events.

## Composing

Risk-tiered is already a composition: the chains are sub-processes, and either can hold the sequential or the parallel shape.
Add `failure-escalation` so a failure in `provision` does not vanish silently.
See [composing-guide.md](composing-guide.md).

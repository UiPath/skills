# Render — Section 2: Stages & Tasks

What each Section 2 block of a case `sdd.md` must contain. Semantics live in [model.md](model.md),
[variables.md](variables.md), and [slas.md](slas.md); this file defines cells and markers. Render shape:
[case-sdd-template.md](../../assets/templates/case-sdd-template.md).

## Stage headings

- Primary: `### Stage {N}: {Stage Name} (\`{stage_id}\`)` — N is 1-based flow order.
- Secondary: `### Secondary Stage: {Stage Name} (\`{stage_id}\`)`.
- The trailing code-formatted `{stage_id}` MUST appear, and every cell that names a stage appends the id in
  code-formatted parens — cross-references stay greppable.

## Stage fields

| Field | Required? | Cell rule |
|---|---|---|
| Type | yes | The literal `Stage` |
| Stage Kind | conditional | Omitted for primary; `secondary` for exception lanes ([model.md § Secondary stages](model.md#secondary-stages)) |
| Design Rationale | yes | One concrete sentence: why primary/secondary, why the entry/exit behavior fits. A global-event lane names the event and states that one interrupting entry replaces per-stage duplication; an SLA lane names the SLA, the response, and why it interrupts or not |
| Description | yes (primary) / optional (secondary) | One sentence |
| Required for Case Completion | yes | Explicit `Yes`/`No` — design default: primary `Yes`, secondary always `No`. Never leave it implicit |
| Interrupting | secondary only | Per [model.md § Secondary stages](model.md#secondary-stages) |
| Stage SLA | when the stage has an SLA | The `#### Stage SLA` block below |

## Stage SLA block

When the source gives every primary stage an SLA target, every named primary stage renders its own
`#### Stage SLA` block. Deterministic titles when unnamed: `**SLA Title:** <Stage Name> SLA`, at-risk
display name `<Stage Name> SLA at risk`, breach `<Stage Name> SLA breached`; every `sla-status-change`
reference uses those exact strings. Render `**SLA Type:**` and `**SLA Title:**` as two separate lines — a
collapsed single line hides the title from line-start tooling and `sla-status-change` references stop
resolving. Duration, thresholds, recipients, and escalation cells: [slas.md](slas.md).

## Stage condition tables

- **Entry:** `WHEN | IF | Interrupting | Display Name`. ≥ 1 row per stage.
- **Exit (completion `Yes` + exit `No` rows in ONE table):** `WHEN | IF | Exit Type | Marks Stage Complete
  | Display Name`. ≥ 1 completion row per primary stage.
- Legal WHEN per slot and exit-type legality: [model.md § Lifecycle gates](model.md#lifecycle-gates) and
  [model.md § Exit types](model.md#exit-types).
- Call forms with complete args appear ONLY in table rows; prose uses bare rule names.
- `sla-status-change` arg forms: `sla-status-change("<target>","<SLA Title>")` for breach;
  `sla-status-change("<target>","<SLA Title>","<At-Risk Escalation Display Name>")` for at-risk. Target is
  the literal `root` (case scope) or the exact stage display name — never the case name or a synonym.

## Stage Task Summary

In plan order, ≥ 1 task per stage: `# | Task ID | Task | Type | Owner`. `Task ID` is code-formatted
(`` `t11` ``); Required-Tasks cells elsewhere use those bare ids. Owner = persona name or `system`.

## Task detail blocks

Headings: `##### Task {N}.{M}: {Task Name}` (primary) / `##### Task S{K}.{M}: {Task Name}` (secondary,
K = secondary-stage order) — never letter prefixes (`R.1`, `ESC.1`). Every block carries, in order:

1. `**Type:**` — one of the nine values in [model.md § Task types](model.md#task-types)
2. `**Activation Mode:**` — `sequential` \| `parallel` \| `parallel-after-predecessor` \| `event-triggered`
   \| `adhoc` \| `fan-in` \| `conditional-gate`
3. `**Design Rationale:**` — why the type fits the actor/work and why the mode fits the timing
   (sequential names the ordering evidence; parallel states independence)
4. `**Entry Condition:**` + its `WHEN | IF | Display Name` table (≥ 1 row; multiple rows = OR; render
   `current-stage-entered` first when present)
5. Exact marker `**Task envelope**` (no colon) + the `Required | Run Only Once | Skip Condition` table
6. The type-specific detail block below

`<UNRESOLVED>` renders as plain text, exactly `<UNRESOLVED>` — never backtick-wrapped, never annotated
inside the cell.

### Which WHEN to write (task entry)

Grammar and exclusivity: [model.md § Task activation](model.md#sequencing--activation).

| Rule | Write when |
|---|---|
| `current-stage-entered` | Ungated stage-started task. Never alongside event/adhoc/sequential rules |
| `runs-sequentially` | The source states order (`then`, `after`, `before`, a dependency) — EVERY task in the ordered run, including the first |
| `selected-tasks-completed("<Task>")` | True fan-in, branch convergence, condition-result routing, or a non-immediate dependency. Never for simple next-step order; never selects `adhoc` or cross-stage tasks |
| `wait-for-connector` | Async connector callback; `IF` gates case state only ([variables.md](variables.md)) |
| `sla-status-change(...)` | The `start-task` SLA response ([slas.md](slas.md)) — never alongside `current-stage-entered` |
| `adhoc` | User-launched from the Case App; `Required: No` |

## Per-type required cells

### `action`

| Cell | Rule |
|---|---|
| HITL Implementation | `Action App: <deploymentTitle>` — concrete intended name (registry-canonical when resolved, else user-requested). NEVER `<UNRESOLVED>`, never paraphrased |
| Action App ID / Deployment Folder | Concrete when resolved; `<UNRESOLVED>` + high review item when not |
| Recipient | Typed prefix only: `Email:` / `User:` / `UserGroup:` / `Role:` / `Expression:` — never a bare string. None known → drop the cell + high review item |
| Priority · Task Title · Labels | `Low/Medium/High/Critical` · one-line user-visible instruction (required — Action Center displays it) · CSV or `—` |
| Run Only Once · Required | Explicit `Yes`/`No` each |
| Input / Output Schema | Tables `Field | Type | Binding (| Required)`. Declared fields MUST be a subset of the resolved app's schema; a field the app lacks → Ask (task-specific app / drop / placeholder), never silently author |
| Buttons | Only when `is_decision: Yes` — then ≥ 2 rows, each `Maps To` referencing a declared §1.5 `Name` or `taskOutcome`, never an undeclared identifier |

Reusing ONE deployed app across several `action` tasks is sanctioned when each task carries a distinct
`actionType` dispatch value AND its declared fields ⊆ the app schema (the code-switched app); without a
distinct `actionType`, or with non-bindable fields, it is the substitute-app defect ([review.md](review.md)).

### `wait-for-connector` / `execute-connector-activity`

Connector key · Connection (name + ID) · Activity Type ID · Service Type · Auth Method · Account/Endpoint ·
Operation (and Trigger/Event for waits) · `Operation Configuration` carry-through · Inputs table (`Field`
verbatim to the IS activity schema) · Outputs table. Missing `Connection ID` / `Activity Type ID` → high
review item.

### `wait-for-timer`

Timer Type (`timeDuration` relative / `timeDate` absolute) · Duration/Until (ISO-8601 — NEVER
`<UNRESOLVED>`: a timer cannot fire without it; block approval) · Business Calendar optional (`—`).

### `case-management`

Child Case (concrete intended name — NEVER `<UNRESOLVED>`, never the parent task's display name) · Folder
Path / Resource Identity (`entityKey`; `<UNRESOLVED>` + high review item when unresolved) · Child Case
Identifier prefix · Data Passed table (`Parent Variable | Child Variable`) · Wait for Completion `Yes`/`No`
· Data Returned table only when waiting.

### `process` / `agent` / `rpa` / `api-workflow` (shared block)

| Cell | Rule |
|---|---|
| Resolved Resource | Concrete intended resource name — NEVER `<UNRESOLVED>` |
| Folder Path | The exact resource folder (never a parent), or `<UNRESOLVED>` when identity is unresolved |
| Resource Identity | `apiWorkflowId` / `agentId` (+version) / `processOrchestrationId`, or `<UNRESOLVED>` + high review item |
| Binding Sub-Type | `Api` (api-workflow) / `Agent` (agent) / `ProcessOrchestration` (process) / `—` (rpa). Omitting it makes Studio Web report the resource as not found |
| Dispatch / Operation | Selector + value for shared façades (`requestSource = "RegisterCaseShell"`), also an Inputs row; `—` for single-purpose resources |
| Inputs / Outputs | Tables; `Field` verbatim to the declared In/Out argument names |

No task-level SLA on any non-`action` type ([slas.md](slas.md)). Deep runtime metadata (agent prompts,
package versions, endpoints) stays out of the SDD — it belongs to build-time discovery
([grounding.md](grounding.md) records identities only).

## I/O completeness (resolved resources)

When a task resolves to a live resource: every REQUIRED declared input has a non-empty `Binding` (any form
in [variables.md](variables.md), including a direct upstream-output reference — which needs no §1.5 row) OR
`<UNRESOLVED>` + a high review item; every Outputs `->` row's `Field` exists verbatim in the resolved
output contract (a phantom field → high review item). Optional inputs may be omitted. Tasks whose identity
is `<UNRESOLVED>` have no contract and are skipped — their portable names stay concrete.

**Bare field-name input lists are forbidden** (`**Inputs:** loanId, borrower`) — they force name-match
guessing downstream; use the table form only.

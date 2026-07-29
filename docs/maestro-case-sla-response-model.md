---
title: Maestro Case Design Decisions
status: design-note
updated: 2026-07-29
owner: uipath-maestro-case
---

# Maestro Case Design Decisions

This note captures design decisions from the July 29, 2026 discussion about how the `uipath-maestro-case` skill should model SLA status changes, safe Case Designer display names, and task-set grouping. It is also the implementation tracker for the branch that updates the skill guidance and eval coverage.

## Problem

The broad issue is not just SLA or payment handling. The current skill needs a stronger conceptual model for case execution so it can reason from business intent into Case Designer structure instead of translating phrases into local task rules too literally.

Observed gaps:

- It models case and stage SLA escalations as SLA rules with escalation actions.
- When an SLA status change must affect case flow, it mainly describes one interrupting secondary-stage entry using `sla-status-change`.
- Task-level SLA exists in the wider case/task model, but the skill docs do not yet fully explain how to choose between task timer fields and graph-level SLA response behavior.
- It can model parallel work that starts after a predecessor as duplicate event-triggered task entries instead of a single next parallel task set.
- It can place waits, timers, and connector listeners after the result-producing work, which means the case is no longer listening while the external obligation is actually outstanding.

The current skill also only forbids `:` in several display names. It does not consistently prevent `.`, `/`, `&`, parentheses, quotes, emoji, or other punctuation from generated stage, task, rule, SLA, or escalation names.

## Case Execution Mental Model

Teach the model to reason in case primitives before it chooses task types or rules.

A Case stage is an active business state, not a prose paragraph converted line by line. While a stage is active, some work runs, some listeners wait, some clocks measure obligations, and conditions decide when the stage completes, diverts, returns, or exits the case.

Core primitives:

| Primitive | Meaning | Authoring implication |
|---|---|---|
| Stage | Bounded business state or milestone | Starts by entry condition; completes or exits by stage-exit condition |
| Task | Unit of work inside the active stage | Completes by finishing its own work; tasks do not have exit rules |
| Task set | Concurrent frontier inside a stage | `data.tasks` outer array is ordered; each inner array is a sibling group |
| Rule | Gate/listener that activates or exits something | Choose scope first: task entry, stage entry, stage exit, case exit |
| Fact | Case state learned from a task/event/decision | Store in output/case variable or direct task-output reference; downstream work gates on it |
| Obligation | Something requested from a person/system | Start waits, timers, and SLA clocks when the obligation is created |
| Listener | A wait for an external event or callback | Use `wait-for-connector` as task or rule depending on what should be activated/exited |
| Clock | Time-based constraint | Use SLA when business deadline/escalation matters; use timer task when simply waiting for duration |
| Race | Competing outcomes from the same active state | Model confirmation, timeout, rejection, cancellation, etc. as concurrent listeners/rules |
| Outcome gate | Decision from observed fact | Downstream tasks/stages must key off the fact, not merely off task-set completion |

Reasoning sequence for Phase 0:

1. Identify lifecycle states: what is the case trying to accomplish now, and what makes that stage done?
2. Identify the active frontier for each stage: what work, waits, and clocks should become active when the stage starts or when a predecessor task finishes?
3. Identify obligations created by tasks: payment request, signature request, document upload request, customer response, external approval, agency clearance, background check, remediation request, or vendor/customer callback.
4. Start listeners and clocks at obligation creation time, not after the expected response has already arrived.
5. Classify concurrency: strict sequence, parallel siblings, race, fan-in, conditional branch, adhoc work, or interrupt.
6. Record facts: every confirmation, timeout, rejection, decision, or failure that affects later flow must produce a variable or direct task-output reference.
7. Gate downstream work on facts: fulfillment work starts after the success fact; escalation/cancel/rework starts after the exception fact.
8. Choose the smallest correct scope: task-entry for in-stage work, stage-entry for entering a stage, stage-exit for leaving/diverting a stage, case-exit for final disposition.

## Common Case Patterns

These patterns should guide the agent across domains. They are not domain-specific recipes; they are reusable case shapes.

| Pattern | Signal in requirements | Preferred case shape |
|---|---|---|
| Request and wait | "send request and wait for response" | Request task, then listener task/rule active immediately after request |
| Obligation deadline | "must respond/pay/sign/upload within N days" | Start SLA or timer when obligation is created; breach routes or escalates from the waiting state |
| Race | "whichever happens first: confirmation or timeout/cancellation" | Same active stage with parallel listener/clock paths; downstream branches gated by outcome facts |
| Fulfillment after confirmation | "after payment/signature/approval, issue/fulfill/proceed" | Fulfillment task starts only after confirmation fact, not after deadline branch completes |
| Parallel after predecessor | "after A, do B and C in parallel" | `data.tasks: [[A], [B, C]]`; do not duplicate selected-task event gates |
| Fan-in | "after B and C both finish, do D" | D uses `selected-tasks-completed(B, C)` or task-set sequencing when it is a simple next set |
| Conditional branch | "if approved do X, if rejected do Y" | Decision fact plus guarded task/stage rules for each branch |
| External callback as stage boundary | "stage completes when system sends event" | Stage-exit `wait-for-connector` can be better than a wait task when the event is purely the boundary |
| Global interrupt | "can happen at any time" | One interrupting secondary-stage entry using the appropriate event/SLA rule |
| Local optional work | "user may do this if needed" | Adhoc task, required false; do not make a secondary stage unless it interrupts or changes lifecycle |

## Manual Surface and Dependency Eligibility

The model must distinguish work done by a person from work started manually.

`action` is the human-work task type. It is appropriate for required approvals, reviews, corrections, data entry, sign-off, and other tasks assigned to a user or group. These tasks can still be sequential, parallel, event-driven, fan-in, or condition-gated depending on when they should start.

`adhoc` is an activation mode. It means the task is started by a user from the Case App, does not auto-start, has an `adhoc` task-entry rule, and is not required for the main flow.

Dependency rule:

> `selected-tasks-completed` must only select non-adhoc sibling tasks in the same stage. Never select a task whose entry condition contains `adhoc`. Never make required downstream flow depend on an adhoc task. If later work must wait for a human task to finish, the upstream task is not adhoc; model it as a regular `action` task with the appropriate activation mode.

Reason:

- A manually triggered task may never be launched.
- Studio Web filters ad-hoc tasks out of selected-task and required-task pickers.
- A downstream gate waiting on optional user-launched work can deadlock the main path.
- Treating "manual review" as `adhoc` conflates actor with activation; the correct actor model is `action`, while activation is a separate choice.

Phase 0 should use this decision table:

| Requirement signal | Correct modeling choice |
|---|---|
| "Reviewer must approve before proceeding" | Required `action` task, usually sequential or fan-in |
| "User may add a note or optional follow-up if needed" | `adhoc` task, `Required: No`, no required downstream dependency |
| "Case worker can manually trigger extra investigation" | `adhoc` task if optional; secondary stage if it interrupts lifecycle |
| "After manual review, generate output" | Regular `action` task followed by sequential or gated downstream work |
| "Manager can override at any time" | Usually user-selected secondary stage or explicit decision path, not adhoc dependency |

Case Review should expose the distinction when relevant:

| Task | Human Work | Activation | Required | May Be Selected By Dependency Rules | Decision |
|---|---|---|---|---|---|
| Manager Approval | Yes | sequential | Yes | Yes | Blocks downstream issuance |
| Add Internal Note | Yes | adhoc | No | No | Optional side work |

## Entry Producer and Concrete Reference Invariants

The model must treat every entry rule as a subscription to a concrete producer. A stage or task entry rule is not a wish that the case should go somewhere; it must name or imply the event, exit, status change, or user action that can actually fire it.

### Entry Producer Invariant

For every stage-entry and task-entry rule in the SDD, Phase 0 should identify the matching producer before approval.

| Entry rule | Required producer or reference | Common wrong shape | Preferred correction |
|---|---|---|---|
| `case-entered` | Root case start | Multiple unrelated stages marked as case-started | One normal first stage unless the case deliberately starts multiple independent stages |
| `selected-stage-completed("Stage")` | Named stage exists and has a completion path | Target stage name exists only in prose | Create or rename the source stage, or choose a different trigger |
| `selected-stage-exited("Stage")` | Named stage exists and can exit on the intended route | Used when the origin never exits before the target should start | Use a true interrupting entry such as `wait-for-connector`, `sla-status-change`, or `user-selected-stage` |
| `user-selected-stage` | At least one other stage has an exit condition with `Exit Type: wait-for-user` | Used for deterministic rejection or exception routing | Use a decision fact plus guarded stage exit or stage entry |
| `wait-for-connector` | Concrete connector event detail and any required output extraction | Bare connector wait with no event details | Add Connector Rule Detail or use a placeholder connector event explicitly |
| `sla-status-change` | Concrete SLA scope, SLA name, status, and escalation intent | Bare SLA status entry with no `slaId` target to resolve | Add an SLA Response Map row and resolve IDs during build |
| `selected-tasks-completed("Task")` | Named non-adhoc sibling task exists in the same stage | Selects optional adhoc/manual task or a task from another stage | Convert blocking human work to regular `action`, or choose a stage-level rule |

`user-selected-stage` deserves special handling. It means a case worker is being asked to choose a next stage from a `wait-for-user` exit. It is not the right rule for ordinary rejection, approval, cancellation, or SLA intervention unless the product behavior really is "pause and let the user choose the next stage." For a stage such as `Application Rejected`, prefer a decision output from the review task and a guarded route to the rejected outcome.

### SLA Reference Invariant

An SDD may use display names because IDs do not exist yet, but it must never author a bare `sla-status-change`.

Every SLA status response row should identify:

- SLA scope: case or named stage.
- SLA display name.
- Status: at-risk, breached, or any escalation.
- Escalation rule display name or explicit "any escalation" intent.
- Response target: notification, task, stage, stage exit, or case exit.
- Interrupting choice and rationale.

Build phase then resolves this to `slaId` and, when applicable, `escalationId` through preallocated IDs before conditions are written. A missing `escalationId` can be valid in persisted JSON for a breached rule, but the design must still say what breached status is intended so the build is auditable.

Case Review should expose this as a rule firing map:

| Target | Rule | Producer or Reference | Resolution Required | Decision |
|---|---|---|---|---|
| Application Rejected | `selected-stage-exited("Review")` + rejection fact | Review task decision and Review stage exit | Stage and variable names | Deterministic rejection route |
| Deadline Intervention | `sla-status-change("Permit Payment SLA","Payment Breached")` | Permit Payment SLA breach escalation | `slaId`, `escalationId` | Interrupting recovery lane |

## Re-entry Attempt Model

The model must classify why a stage can be re-entered before it chooses `Run Only Once` or writes routing variables. Re-entry is not one behavior.

| Re-entry type | Meaning | `Run Only Once` default | State handling |
|---|---|---|---|
| New attempt or resubmission | The case returns so corrected or revised work can be reviewed, validated, approved, or decided again | `No` for tasks that create the new attempt, request review, collect responses, validate, decide, or produce routing facts | Reset live routing variables to neutral values, or use attempt-scoped/latest-result variables |
| Re-evaluate existing fact | The case returns only so the origin can continue routing based on a fact produced by the exception lane | `Yes` only for tasks whose previous output must be preserved and must not re-prompt/re-run | Do not reset the preserved fact; gate exits on it |
| Optional repeat work | A user may repeat a task, but the main flow does not require it | Usually adhoc or non-required task | Do not let required flow depend on it |

Detection signals for a new attempt loop include:

- Sent back for corrections.
- Fixed and resubmitted.
- Retry, revise, re-review, revalidate, appeal, counter-proposal, revised proposal, resubmit through decision.
- A decision value such as `SendBack`, `Rejected`, `NeedsCorrection`, or `MoreInfoRequired` routes to correction and then back to the same review or approval stage.

Decision rule:

> If the requirement says corrected work is resubmitted through a review or decision, the review/request/decision producer tasks must run again on stage re-entry. Set `Run Only Once: No` for those tasks and reset the live decision variable before the new attempt starts, or write the new result to an iteration-scoped/latest-result variable.

State reset rule:

> Any variable that controls an exit from the re-entered stage must not retain a terminal value from the previous attempt while the new attempt is pending. Reset values such as `buyerDecision = "SendBack"` to a neutral value such as `Pending`, `NotStarted`, or `null` before the stage can evaluate the next decision route.

For the buyer review pattern:

| Item | Correct choice | Reason |
|---|---|---|
| Send buyer review request | `Run Only Once: No` | A new request must be sent for the corrected submission |
| Buyer decision | `Run Only Once: No` | A fresh decision is required after correction |
| `buyerDecision` | Reset to `Pending` on re-entry or write a new latest-decision fact | Prevents stale `SendBack` from immediately routing again |
| Sendback route | Gate on fresh Buyer decision completion plus `buyerDecision == SendBack` | Avoids routing on stale state before the new decision exists |

Case Review should expose loops explicitly:

| Loop | Re-entered Stage | Re-entry Type | Tasks That Rerun | State Reset | Exit Guard |
|---|---|---|---|---|---|
| Buyer sendback | Buyer Review | New attempt | Send buyer review request; Buyer decision | `buyerDecision = Pending` | Route only after fresh Buyer decision completes |

## Listener Versus Task Versus Exit Rule

The model should choose where a wait belongs by asking what the wait does.

| Need | Better shape |
|---|---|
| The case needs a visible in-stage waiting work item | `wait-for-connector` task |
| A task should start when an external event arrives | Task-entry `wait-for-connector` rule |
| A stage should complete only when the external event arrives | Stage-exit `wait-for-connector` with `Marks Stage Complete: Yes` |
| A stage should divert on the external event | Stage-exit `wait-for-connector` with `Marks Stage Complete: No` and route |
| A new exception/recovery stage should interrupt active work | Secondary-stage entry `wait-for-connector` |
| The whole case should close or cancel on the event | Case-exit `wait-for-connector` |

Do not create a wait task after the dependent outcome task. A listener is useful only while the case is waiting for the external fact.

## Clock Versus Timer Versus SLA

The model should choose the clock by asking what time means.

| Need | Better shape |
|---|---|
| Just wait for a fixed delay before continuing | `wait-for-timer` task |
| Track a business deadline with at-risk/breach semantics | SLA rule plus escalation |
| Breach should affect case flow | SLA status response rule, stage exit, stage entry, task start, or case exit |
| Human action has its own due date | Action task SLA/timer fields first |
| Timeout competes with a confirmation event | Race pattern: listener and clock active from the same obligation point |

Timers and SLAs should attach to the period where something is pending. A timeout that starts after the success task cannot detect lateness.

## Core Decision

Separate the SLA clock from the response to that clock.

The SLA scope says what deadline is being measured:

- Case SLA
- Stage SLA
- Action task SLA

The SLA response says what the case should do when the SLA reaches at-risk or breached status:

- Notify only
- Start a task
- Enter another stage
- Exit the current stage
- Exit or complete the case
- Configure task-local timer fields only

Interrupting versus non-interrupting is a property of the response, not a property of the SLA scope.

## Notify Only

"Notify only" means the SLA escalation rule is sufficient by itself. The model should not create a stage or task just to represent a notification.

Use notify-only when the requirement says things like:

- Notify the owner
- Email the supervisor
- Page the support queue
- Alert compliance
- Send reminder before breach

In JSON terms, this stays on the SLA rule's escalation actions. It does not need an additional `sla-status-change` condition unless the case graph must also change.

## Response Decision Rules

During Phase 0, the agent should make the best functional choice from the requirement and disclose it in Case Review.

Use these defaults:

| Requirement signal | Recommended modeling choice | Interrupting default |
|---|---|---|
| Only notify, alert, email, page, or remind | SLA escalation notification only | Not applicable |
| Add local work while the current stage continues | Prefer SLA escalation notification plus regular same-stage follow-up work that starts after the relevant pending obligation or task state. A stage SLA breach must not be modeled as an interrupting same-stage task. | No |
| Escalation needs ownership, audit, supervision, or recovery workflow | Enter a dedicated stage | Yes if takeover or blocking recovery, No if parallel oversight |
| Breach should move the case out of the current stage | Stage exit rule | Yes when it terminates current work |
| Breach should close, cancel, reject, or fail the case | Case exit rule | Usually Yes |
| Action task has its own due date or timer outcome | Configure action-task SLA or timer fields | Not applicable unless graph behavior is also required |

If the user only gives an SLA duration and no response, default to:

- At-risk: notify the stage or case owner group.
- Breached: notify the next escalation tier.
- No extra stage, task, stage exit, or case exit.

## Case SLA

A case SLA breach can be either interrupting or non-interrupting.

Recommended choices:

- Notify-only case breach: keep the response on the case SLA escalation rule.
- Parallel oversight: enter a non-interrupting escalation stage or start a task that does not stop the happy path.
- Takeover or recovery: enter an interrupting secondary stage.
- Terminal breach: route to a case exit rule, with `marksCaseComplete` chosen by business semantics.

The skill must not assume that every case SLA breach means an interrupting secondary stage.

## Stage SLA

A stage SLA breach can reasonably produce:

- A notification only.
- Local same-stage follow-up work, but not as an interrupting same-stage task. Keep the active stage/task lifecycle intact; use notification, existing/pending task state, or a regular follow-up that starts after the relevant obligation/task condition.
- A different stage, such as "Recovery Review" or "Supervisor Escalation".
- A stage exit path if the original stage should stop or fail.

Default to notify-only when the requirement only alerts the stage owner. Default to a separate stage when the response changes ownership, lifecycle state, audit posture, recovery responsibility, or needs to interrupt the current stage. Do not model "stage SLA breached" as an interrupting task inside that same stage.

## Task SLA

Action task SLA should first be modeled as task-local SLA or timer behavior when the requirement is about the human action deadline itself.

Only add graph-level SLA status behavior when the missed task deadline affects the broader case flow. Examples:

- A late task requires supervisor review.
- A late task cancels the case.
- A late task starts a recovery stage.
- A late task changes stage or case completion.

The skill update should document the available action task fields and avoid pretending that task SLA is identical to root or stage `slaRules`.

## Phase 0 SDD Generation Rule

Add a Phase 0 rule equivalent to this:

> For every SLA mentioned or inferred, identify the SLA scope, status, and response separately. Scope is case, stage, or action task. Status is at-risk, breached, or both. Response is notify-only, enter-stage, exit-stage, exit-case, task-local timer configuration, or non-interrupting follow-up work tied to an existing pending obligation/task state. Choose the least graph-changing response that satisfies the business requirement. Do not create a stage or task for notification-only escalation. A stage SLA breach must not interrupt a task inside the same stage. Use a separate stage when breach handling changes ownership, lifecycle, audit posture, recovery responsibility, or needs to interrupt the active stage; use task timer fields for action-task due dates. Set interrupting based on whether the response stops or diverts active work, not based on whether the SLA is case-level or stage-level. Record the rationale and show it in Case Review.

The SDD should include an SLA Response Map before approval:

| Scope | SLA | Status | Response | Target | Interrupting | Rationale |
|---|---|---|---|---|---|---|
| Case | Overall Resolution SLA | At-risk | Notify only | Case Owner Group | No | Warning before breach |
| Case | Overall Resolution SLA | Breached | Enter stage | Director Review | Yes | Breach requires management takeover |
| Stage | Intake SLA | Breached | Notify plus follow-up after pending work | Resolve Intake Delay | No | Same-stage breach response must not interrupt the running stage task |
| Action task | Approval Task SLA | Breached | Task-local timer | Approval Task | No | Deadline belongs to the human action |

## Case Review Presentation

The approval surface should not hide SLA behavior inside prose. It should show:

- SLA clocks: case, stage, and task deadlines.
- Escalation rules: at-risk and breached recipients.
- Flow responses: any task, stage, stage exit, or case exit created because of SLA status.
- Interrupting choice: Yes or No with rationale.
- Smart defaults: any response inferred because the user did not specify one.

Recommended Case Review section:

```md
### SLA Response Map

| Scope | SLA | Status | Response | Target | Interrupting | Decision |
|---|---|---|---|---|---|---|
| Case | Overall Resolution SLA | At-risk | Notify only | Case Owner Group | No | Default warning |
| Case | Overall Resolution SLA | Breached | Enter stage | Executive Review | Yes | Breach changes ownership |
```

## Safe Display Name Contract

Generated Case Designer display names should use only:

- Letters
- Numbers
- Spaces
- Hyphen `-`
- Underscore `_`

This applies to authored or generated display names for:

- Stages
- Tasks
- Entry rules
- Exit rules
- Case exit rules
- SLA rules
- Escalation rules
- Other Case Designer labels emitted into `displayName` or equivalent title fields

Do not generate these characters in display names:

- Colon `:`
- Period `.`
- Slash `/`
- Backslash `\`
- Quotes
- Parentheses
- Ampersand `&`
- Comma
- Semicolon
- Emoji or other symbols

This is stricter than the current skill text, which mainly forbids `:`.

## Name Normalization Rule

Future implementation should add a single reusable normalization rule:

1. Replace each run of disallowed characters with one space.
2. Collapse repeated spaces.
3. Trim leading and trailing spaces.
4. Preserve meaningful words and casing.
5. If the name becomes empty, ask for a replacement or use a domain-specific generated name.
6. If normalization causes a collision, choose a clear safe qualifier when one exists, or append a safe numeric suffix such as `2`; disclose the change in Case Review.

Examples:

| Input | Safe generated name |
|---|---|
| `AP Review: Escalation` | `AP Review Escalation` |
| `KYC.Approval` | `KYC Approval` |
| `Review/Approve` | `Review Approve` |
| `At-risk (Tier 2)` | `At-risk Tier 2` |
| `Legal & Compliance` | `Legal Compliance` |

Generated fallback names are already mostly safe, such as `Entry Rule 1`, `Complete Rule 1`, `Exit Rule 1`, `SLA Rule 1`, and `Escalation Rule 1`. The gap is user-provided or inferred semantic names that are currently carried verbatim.

## Important Boundary

Do not normalize external registry identifiers that must match tenant resources exactly. Resource names, connector names, process names, action app names, queue names, bucket names, and API names may contain punctuation because they are lookup keys.

Instead:

- Preserve exact external names in resource resolution fields.
- Generate safe Case Designer display names separately.
- Show both values when they differ.

Example:

| Purpose | Value |
|---|---|
| External Action App name | `KYC.Approval: Manager Review` |
| Case task display name | `KYC Approval Manager Review` |

## Parallel Task-Set Decision

The skill must distinguish task-set structure from task-entry conditions.

In the Case model, a stage's tasks are stored as `Task[][]`:

- The outer array is ordered task sets.
- The inner array is a group of sibling tasks in the same visual and execution set.
- A strict sequential chain is represented as consecutive single-task sets.
- Parallel siblings share the same inner set.

The current skill already knows about `Task[][]`, but it applies same-set grouping too narrowly. It tends to treat tasks that start after another task as event-triggered tasks with `selected-tasks-completed("<previous task>")`. That can work mechanically, but Studio Web classifies that as event-driven and does not show the expected parallel group.

Future implementation should add this rule:

> If multiple tasks share the same immediate predecessor task or predecessor task set, and those tasks are independent of each other, place them in the same next `data.tasks` inner array. Do not model them as separate event-triggered tasks with identical `selected-tasks-completed` rules. Use `selected-tasks-completed` for fan-in, branch convergence, decision-result routing, non-immediate dependency, or an explicitly authored gate.

Example:

```text
Collect Fees completes.
Then Payment Deadline and Wait for Payment Confirmation start in parallel.
Generate Permit happens after payment succeeds.
```

Expected task-set shape:

```json
"tasks": [
  ["Collect Fees"],
  ["Payment Deadline", "Wait for Payment Confirmation"],
  ["Generate Permit"]
]
```

Decision details:

- `Payment Deadline` and `Wait for Payment Confirmation` are a parallel-after-predecessor group.
- They should share the same next task set after `Collect Fees`.
- They should not both be authored as event-triggered tasks whose entry rule is `selected-tasks-completed("Collect Fees")`.
- `Generate Permit` should not simply wait for the whole parallel set if the timer is a competing timeout path; it should be gated by successful payment confirmation.

Case Review should expose this directly, for example:

| Set | Tasks | Starts When | Relationship | Decision |
|---|---|---|---|---|
| 1 | Collect Fees | Stage enters or prior stage completes | Sequential step | Collect payment before downstream work |
| 2 | Payment Deadline; Wait for Payment Confirmation | After Collect Fees | Parallel group | Deadline clock and confirmation wait run side by side |
| 3 | Generate Permit | Payment confirmed | Conditional next step | Permit is generated only on successful payment |

This means the skill should model `parallel-after-predecessor` before choosing task-entry rules. The task-entry rule is not the only source of truth; the `data.tasks` set shape is part of the executable and visual contract. The encoded rule is: siblings after the same immediate predecessor share the same next `data.tasks` inner array and each uses `runs-sequentially`; they must not become duplicate `selected-tasks-completed("<previous>")` event-triggered tasks.

## Obligation Race Example

Payment is one concrete example of the broader obligation pattern. The same logic applies to signatures, uploaded documents, customer replies, third-party approvals, background checks, inspections, and agency clearances.

Incorrect shape:

```text
Collect Fees
Generate Permit
Wait for Payment Confirmation
Payment Deadline
```

Why it is wrong:

- The connector listener starts after the case no longer needs to listen.
- The deadline starts after the payment is already assumed complete.
- The permit can be generated before the confirmation fact exists.
- The alternate outcome for no payment is not represented at the point where the obligation is pending.

Correct reasoning shape:

```text
Send Payment Request or Collect Fees starts the obligation.
Payment Confirmation listener and Payment Deadline clock become active immediately.
Payment confirmed gates permit generation.
Deadline breached gates follow-up, escalation, cancellation, or stage exit.
```

Possible case shape:

```json
"tasks": [
  ["Collect Fees"],
  ["Payment Deadline", "Wait for Payment Confirmation"],
  ["Generate Permit"]
]
```

But the third set must be gated by the success fact, because one sibling in the second set is a timeout branch. If the deadline branch completes first, the case should not issue the permit.

## Implementation Touchpoints

Update should cover all of these, not Phase 0 only:

- `references/sdd-generation-rules.md`: add the Case Execution Mental Model, Common Case Patterns, and listener/timer/SLA decision tables before detailed task-type rules.
- `references/phase-0-interview.md`: ask or infer SLA scope and response, then present the SLA Response Map.
- `references/sdd-generation-rules.md`: add the SLA response model and global safe-name contract.
- `references/sdd-generation-rules.md`: add the manual-surface rule: human-performed work uses task type `action`; manually-triggered optional work uses activation mode `adhoc`; `selected-tasks-completed` and required-task rules may not select adhoc tasks.
- `references/sdd-generation-rules.md` and `references/phase-0-interview.md`: add an Entry Producer audit so every entry rule has a concrete producer before Case Review approval.
- `assets/templates/sdd-template.md`: add a Rule Firing Map or equivalent review field showing each non-trivial entry rule, its producer, and any build-time ID resolution.
- `assets/templates/sdd-template.md`: add SLA Response Map and update the Case App validation contract.
- `references/sdd-generation-rules.md` and `references/phase-0-interview.md`: add a Re-entry Loop Map that classifies each return/rework loop as new attempt, re-evaluate existing fact, or optional repeat work.
- `assets/templates/sdd-template.md`: add stage/task guidance for re-entry behavior: tasks that rerun, tasks intentionally run once, variables reset, and exit guards.
- `references/planning.md`: preserve SLA response rationale and safe display names into `tasks.md`.
- `references/planning.md`: reject bare `sla-status-change`; require scope, SLA display name, status, and escalation intent so Phase 3 can resolve `slaId` and `escalationId`.
- `references/planning.md`: reject re-entered review/decision stages where all producer tasks are `Run Only Once: Yes` and no state reset/attempt-scoped variable is declared.
- `references/plugins/sla/planning.md` and `impl-json.md`: clarify notify-only versus graph-changing SLA responses.
- `references/plugins/conditions/*`: support SLA status change wherever the product model supports it, not only one hard-coded stage-entry pattern.
- `references/plugins/conditions/stage-entry-conditions/*`: validate that `user-selected-stage` is paired with an upstream `wait-for-user` exit; otherwise rewrite deterministic routes as decision-fact routes.
- `references/plugins/conditions/task-entry-conditions/*` and `stage-exit-conditions/*`: reject or rewrite `selected-tasks-completed` references to adhoc tasks; force the model to convert blocking human work to a regular required `action` task.
- `references/plugins/tasks/action/*`: document task-local SLA and timer modeling.
- Task plugin `impl-json.md` files: stop treating task type as the source of truth for `shouldRunOnlyOnce`; use the SDD's re-entry classification and preserve the explicit value.
- Task grouping guidance in `references/sdd-generation-rules.md`, `references/planning.md`, `references/implementation.md`, and task plugin `impl-json.md` files: recognize parallel-after-predecessor groups and preserve them as same inner `data.tasks` arrays.
- Task-entry guidance in `references/plugins/conditions/task-entry-conditions/*`: clarify that `runs-sequentially` plus task-set order can represent upstream task-set completion, while `selected-tasks-completed` should not be used for simple parallel-after-predecessor grouping.
- Tests under `tests/tasks/uipath-maestro-case/`: add fixtures for case SLA interrupting, case SLA non-interrupting, stage SLA same-stage task, stage SLA separate stage, notify-only SLA, task-local SLA, unsafe display-name normalization, parallel-after-predecessor task grouping, obligation-race modeling, selected-task rules that must not reference adhoc tasks, `user-selected-stage` without `wait-for-user`, bare `sla-status-change`, and sendback/resubmission loops where review/request/decision tasks must rerun and stale decision state must be reset. The current branch adds `phase_0_to_case/case_reasoning_regressions` as the first combined regression fixture.

## Acceptance Criteria

This patch should be considered complete when:

- Phase 0 chooses a functional SLA response without over-asking.
- Case Review shows the SLA Response Map before approval.
- Notify-only SLA breach does not create unnecessary stages or tasks.
- Case SLA breach can be interrupting or non-interrupting.
- Stage SLA breach can route to another stage or drive non-interrupting local follow-up, but it must not interrupt a task inside the same stage.
- Action task SLA is represented using task-local timer fields when appropriate.
- `sla-status-change` is not treated as stage-entry-only if the frontend schema supports more scopes.
- Generated display names for stages, tasks, rules, SLAs, and escalations contain only letters, numbers, spaces, hyphen, and underscore.
- External resource lookup names are not corrupted by display-name normalization.
- Required human work is modeled as regular `action` tasks, not as adhoc tasks.
- `selected-tasks-completed` and required-task completion rules never select tasks with `adhoc` entry conditions.
- Optional adhoc tasks are disclosed as optional side work and no required downstream path depends on them.
- Every non-start stage entry has a concrete producer or reference: source stage, source exit, connector event, user-selected wait, or SLA status rule.
- `user-selected-stage` is used only when a matching `wait-for-user` exit exists; deterministic rejection/approval routes use decision facts and guarded routes instead.
- Every `sla-status-change` row names scope, SLA display name, status, and escalation intent; build resolves that to concrete `slaId` and valid `escalationId` or an explicit valid any/breached form.
- Re-entry loops are classified before approval as new attempt, re-evaluate existing fact, or optional repeat work.
- New-attempt loops set `Run Only Once: No` on request/review/decision/validation tasks that must run again after corrections or resubmission.
- Variables that drive routing out of a re-entered stage are reset to neutral pending values or replaced with attempt-scoped/latest-result facts so stale terminal values cannot fire immediately.
- `Run Only Once: Yes` is reserved for immutable setup or for preserving an existing fact during a re-evaluate-only return, not for tasks that must produce a fresh attempt result.
- Multiple independent tasks that start after the same predecessor are emitted in one parallel task set, not as duplicate event-triggered `selected-tasks-completed` task entries.
- Downstream work after a parallel group is gated on the actual success signal when one branch is a timeout or exception path.
- External waits and deadlines become active while the corresponding obligation is outstanding, not after the expected result has already been produced.
- Stage/task/case rules are chosen by the lifecycle effect of the event, not by keyword matching on the requirement text.

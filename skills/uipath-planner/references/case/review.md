# Case Review & Finalization

The ONE confirmation checkpoint and the checks that gate it. Run §Finalization against the in-memory model
FIRST — fix failures silently (they are authoring defects, not user decisions); anything unfixable becomes
a Review Flags row. Severity levels and the review-item shape: [principles.md](principles.md).

## The Case Review — eight sections, one question

A decision-first business approval surface, complete enough to approve the case behavior without opening
any SDD file — never a generic build plan and never a compressed SDD copy. The tenant resolution gate
([grounding.md](grounding.md)), when it has items, rides this same turn.

**Coverage map:** SDD §1 → Case Snapshot + SLA and Escalations + Rules and Outcomes; §2 → Primary Journey +
Other Paths Considered + SLA and Escalations + Rules and Outcomes; §3 → Case Snapshot + human action labels
+ Resources and Integrations; §4 → Resources and Integrations. The review intentionally omits the data
contract, variables, and task inputs/outputs — those stay complete in the SDD. Anything carrying a high
review item also appears in Review Flags.

Start with `## Case Review: <Case name>`, then exactly this order:

1. **Case Snapshot** — `Item | Proposed design`. Rows: `Objective`, `Starts when`, `Primary personas`,
   `Successful completion`, `Other terminal outcomes`, `SLA coverage`. Mark assumed values `(assumed)`.
   No case ID prefix unless it affects a user decision.
2. **Primary Journey** — `# | Stage | Purpose | Tasks | Starts when | Completes or exits when | Required? |
   SLA`. Every primary stage once, in flow order. The `Tasks` cell names every task in execution order with
   type, required/optional status, and activation/grouping — e.g. `Sequential: Capture request (Human
   action, required) → Validate request (RPA workflow, required)`; `After both: Make decision (Human
   action, required)`. Event-triggered and manually triggered tasks are shown explicitly.
3. **Other Paths Considered** — `Scenario | Trigger or condition | Modeled as | Tasks | Interrupts active
   work? | Return or case outcome | Rationale`. Every modeled exception, secondary stage, optional path,
   and alternate terminal — AND standard paths intentionally left unmodeled when that omission is a
   decision. Path tasks carry type, required/optional, activation/grouping.
4. **SLA and Escalations** — `Scope | SLA | Time target or condition | Status or threshold | Response |
   Response target | Interrupts active work? | Rationale`. One row per meaningful `(scope, SLA, status)`,
   separate at-risk and breached rows when both exist. Responses from the closed set in
   [slas.md](slas.md). Interrupting cell: `N/A` for `notify-only`; `—` for `start-task` (a task entry
   interrupts nothing — never `Yes`/`No`); otherwise `Yes`/`No` matching the produced entry row. Never
   assume every breach creates an escalation stage. `None` when the case has no SLA.
5. **Rules and Outcomes** — `Scope | Element | Rule | When | If | Then`. Business-significant routing,
   completion, and terminal rules only. Omit generated sequencing already visible in `Tasks`; do not
   repeat SLA rows unless needed to understand routing. Business conditions in `If`; no data column.
6. **Resources and Integrations** — `Task | Intended resource or system | Resolution`. Action apps,
   agents, RPA/processes, API workflows, child cases, connectors, named external systems. `Resolution` =
   the design-time outcome: `resolved (<folder>)`, a gate decision (`create during build`,
   `resolve at build`), or a candidate pick. A missing row is not acceptable.
7. **Decisions I Made** — `Decision | Why | Provenance`. Every assumption, override, resource decision,
   task-type decision, activation/sequence decision, and intentionally omitted path, in plain language
   (`you said "then"`, `compliance wording`, `no SLA mentioned`). Group only decisions sharing rationale
   AND provenance. Flagged items carry ⚠.
8. **Review Flags** — `Item to review | Why it matters | Default if accepted`. `None` when empty.
   Unfixable findings, missing connections, unresolved high-impact choices.

After Review Flags, when any §1.5 row is `Category: In` + `Type: file`, show this fixed block (omit
otherwise — a conditional build obligation, not a ninth section):

```
Caller obligation (file In-arg detected):
  File In-args:  <comma-separated names>
  Programmatic callers must pre-create each JobAttachment via POST /odata/Attachments,
  PUT bytes to the returned blob URI, then pass {ID,FullName,MimeType,Metadata} as the
  In-arg value AND include the attachment ID in StartProcessDto.Attachments[].
  Maestro Studio Web's "Start case" dialog does this automatically.
```

**Product vocabulary.** User-visible activation labels: `Sequential`, `Parallel`, `Parallel after
predecessor`, `Event-triggered`, `Manually triggered`, `Fan-in`, `Conditional gate` (`adhoc` → `Manually
triggered`). Prefer product task labels — `Human action`, `Agent`, `RPA workflow`, `API workflow`,
`Child case` — over schema enum names.

**No duplicated review surfaces.** Each business decision appears once. No Data Contract section, variable
rows, task I/O rows, second stages list, or per-stage detail cards — technical detail stays in the SDD.

**Completeness gate.** Incomplete unless: all eight sections shown, every stage and task named, every
modeled and intentionally omitted path covered, every meaningful SLA response/status row present, Caller
obligation when relevant. No approval question before every section has been shown — even sections reading
`None`. Never substitute a list of build steps, artifacts, folders, or validation commands, or a summary
that points at the SDD for a missing business decision.

**Confirmation question (one AskUserQuestion)** — options by mode:

| Mode | Options |
|---|---|
| Build handoff | `Build it — straight through` / `Build it — pause at the build preview` / `Change something`. The Build answer is the consent AND the build-review preference, captured once, never re-asked mid-build. With ⚠ flags: first option reads `Build despite N flagged items — straight through` |
| Direct design-only | `Save the design` / `Change something` (⚠ → `Save despite N flagged items`) |
| Draft request | `Save as draft` / `Change something`. A prompt that already says save-a-draft-and-stop counts as the answer: write immediately, no extra prompt |

Corrections (`Change something` or free text) update the model, re-run the affected Finalization checks,
and re-show ONLY the changed sections or rows, then one `Suggested next steps` line before the next
prompt. A correction never restarts the walk. **Explicit sign-off requests** ("only after I approve") add
exactly one approval prompt after acceptance, before any file is created — nothing else changes.

## Logical integrity — the stage-graph walk

Reachability is condition-only ([model.md](model.md) — the case has no edges), so this walk is the sole
guard. Any failure is blocking; offer `Re-edit` / `Restart` / `Abort`.

1. **Every stage reachable from a trigger** — walk entry conditions forward from each trigger and SLA
   source. An unreachable primary stage is an orphan.
2. **Every stage exits** — each primary stage has a completion consumed downstream, or another stage's
   entry references it, or it feeds a secondary lane. A stage nothing keys off is a terminal loop.
3. **Every case-exit row references a stage that exists** — no dangling selectors.
4. **The §1.4 path can complete** — ≥ 1 primary stage is `Required: Yes`; otherwise the case can never
   complete ([model.md § Lifecycle gates](model.md#lifecycle-gates)).
5. **Secondary-lane entries: ≥ 1 interrupting entry each, DISTINCT, chosen by the lane's trigger source**
   ([model.md § Secondary stages](model.md#secondary-stages)). Two lanes with identical entries (same rule
   + selectors + expression) are ambiguous routing — a design requirement to differentiate, not
   validate-enforced (as of uip 1.198.0-preview.102). A decision-reachable lane MUST carry a
   `selected-stage-exited(origin)` + `IF` entry matching the origin's gated diverting exit, with the
   origin's completion gated by the inverse `IF`; a missing divert dual-fires or deadlocks. A lane
   described as decision-reachable but entered only via `wait-for-connector` is unreachable from its
   stated source. `adhoc` is never a stage entry.
6. **Every `sla-status-change` entry resolves** — the target is `root` or an existing stage, that target
   declares the SLA, and every supplied title matches a row on THAT target; a two-arg breach row is
   complete as written ([slas.md](slas.md)). Any real miss leaves the lane unreachable.
7. **Every secondary stage is interrupting except a non-diverting SLA oversight row**
   ([model.md § Secondary stages](model.md#secondary-stages)). Wrong classification is blocking; never
   promote the lane to a regular stage.
8. **No gate reads a variable its own trigger writes** — for every condition whose WHEN names a task,
   the `IF` references that task's output, not a case variable the task's Outputs row feeds. The gate is
   evaluated before the extract lands, so such a guard is dead on the first pass and the stage stalls with
   no error ([variables.md § Gate on the producer](variables.md#gate-on-the-producer-never-on-the-variable-it-writes)).

Worked example — a decision-routed return lane (AP Review → SLA Escalation on `requiresEscalation`):

| Stage | Condition | WHEN | IF | Exit Type | Marks Complete |
|---|---|---|---|---|---|
| AP Review | exit (complete) | `required-tasks-completed` | `=js:(vars.requiresEscalation !== true)` | `exit-only` | Yes |
| AP Review | exit (divert) | `selected-tasks-completed("AP ownership review")` | `=js:(vars.requiresEscalation === true)` | `exit-only` (`exitToStageId` → SLA Escalation) | No |
| SLA Escalation | entry (`Interrupting: Yes`) | `selected-stage-exited("AP Review")` | `=js:(vars.requiresEscalation === true)` | — | — |
| SLA Escalation | exit | `required-tasks-completed` | — | `return-to-origin` | Yes |

On escalate the divert fires (completion's inverse `IF` is false), the lane runs, `return-to-origin`
re-activates AP Review; on non-escalate the completion fires and the next stage enters via its own
`selected-stage-completed("AP Review")`. The decision is read directly from the producing action's output
([variables.md](variables.md)) — never relayed through a §1.5 variable.

## Architect's lens — advisory pass

Emit medium review items when these fire; the noted high variants gate like any high item.

| Check | Trigger | Review item |
|---|---|---|
| Single-recipient bottleneck | An `action` recipient is one `User:`/`Email:` AND the stage runs on every case AND no documented volume limit | `rev_bottleneck_<task>`: confirm volume or use UserGroup/Role |
| No escalation on SLA | Stage SLA set, escalation absent | `rev_escalation_<stage>`: no one is paged on breach |
| Escalation loops to the breacher | Escalation recipient = the stage's primary recipient | `rev_escalation_loop_<stage>`: pick a tier-up recipient |
| Sync child case in the critical path | `Wait for Completion: Yes` + parent SLA + no timeout cover | `rev_childcase_<task>`: consider async + completion event, or an exception path |
| All-human stage | 100% `action` tasks, > 2 tasks | `rev_human_only_<stage>`: consider agent/process pre-screening |
| No happy path on the first stage | Only `No` exits, no `required-tasks-completed` completion | `rev_no_happy_path_<stage>` |
| Decision outcome unread | `is_decision: Yes` writes a variable no downstream rule reads | `rev_orphan_decision_<task>`: consume it or downgrade `is_decision` |
| Connector failure uncovered | Connector task in a primary stage, no failure lane (HIGH when ≥ 2 connector tasks share a critical path with zero cover) | `rev_no_failure_path_<task>` |
| Substitute app (HIGH) | One Action App on ≥ 2 tasks WITHOUT a distinct `actionType` each, or declared fields outside the app schema. Exempt: the code-switched app ([render-stages-tasks.md](render-stages-tasks.md)) | `rev_substitute_app_<app>`: code-switch or deploy task-specific apps |
| Parallel bottleneck fan-in | ≥ 2 bottleneck stages fan into one downstream stage | `rev_multi_bottleneck_<stages>` |
| Relay variable | A §1.5 `Variable` whose only producer is one task output and only consumer is one binding (exemptions in [variables.md](variables.md)) | `rev_relay_var_<name>`: reference the output directly, drop the row |
| Aliased output | An Outputs `->` row whose `Field` leaf has no matching §1.5 row and lands in a differently-named variable | `rev_aliased_output_<task>`: declare a dedicated variable or confirm the reuse |

## Finalization checklist

Run ONCE against the in-memory model before presenting the review. Checks 16 and 19 need resolved I/O
contracts, which design-time resolution does not pull — they are enforced at build; run them here only
when a contract is already in memory.

1. **Schema** — every task type is one of the nine in [model.md § Task types](model.md#task-types); every
   WHEN ↔ Marks-Complete pair is legal per [model.md § Lifecycle gates](model.md#lifecycle-gates).
2. **Render contract** — every required cell concrete ([render-case-definition.md](render-case-definition.md),
   [render-stages-tasks.md](render-stages-tasks.md)); no banned `—`/`<UNRESOLVED>`
   ([principles.md](principles.md)).
   2a. **Template shape** — the rendered text passes the template conformance gate
   ([case-design-lane-guide.md](../case-design-lane-guide.md)) on disk, before the `Status: ready` flip.
   2b. **Safe display names** — the charset and repair procedure in
   [model.md § Naming rules](model.md#naming-rules) on every generated or carried display field.
3. **Decision buttons** — `is_decision: Yes` ⟹ ≥ 2 buttons; every `Maps To` LHS is a §1.5 `Name` or
   `taskOutcome`.
4. **Recipient encoding** — typed prefixes only ([render-stages-tasks.md](render-stages-tasks.md)).
5. **Connector ids** — every connector task has `Connection ID` + `Activity Type ID`; every
   `wait-for-connector` rule (any scope) resolves connector key + event operation (+ connection when not
   tenant-default). Missing → paired high review item.
6. **Variable lineage** — every consumer closes ([variables.md](variables.md)).
7. **Override conflict** — no compliance trigger phrase paired with a non-`action` type without explicit
   user reconciliation ([authoring.md](authoring.md)).
8. **Alt-disposition coverage** — ≥ 1 secondary stage ⟹ §1.4a non-empty OR an open high item.
9. **High-severity acknowledgment** — open high items force the `Build despite N flagged items` pick.
10. **Provenance** — every non-user-stated, non-verbatim value carries a provenance kind
    ([principles.md](principles.md)).
    10a. **Design rationale** — every stage (kind + routing), task (type + activation), and configured SLA
    (thresholds, recipients, response) carries durable rationale — blocking when missing.
    10b. **SLA Response Map closure** — one row per `(Scope, SLA, Status)`, closure both ways, Interrupting
    cells agree ([render-case-definition.md](render-case-definition.md)); a `notify-only` row that minted
    a stage or task, or a bare SLA with no row, is blocking.
11. **File-In-arg caller obligation** — the fixed block above whenever an `In` + `file` row exists.
12. **Stage-graph connectivity** — the §Logical integrity walk, all seven checks.
    12a. **Entry producer** — every non-start entry names a concrete producer (source stage, task,
    connector event, paired `wait-for-user` exit, or a declared SLA reference); at-risk rows name the
    escalation, breach rows the SLA alone ([slas.md](slas.md)).
13. **Domain fidelity** — every verbatim-captured entity renders exactly ([principles.md](principles.md));
    drift → `Re-edit` with the phrase pre-filled.
14. **Architect's lens** — the advisory table above; medium rows are non-blocking, high variants gate.
15. **Decision-routing closure** — every routing button's variable + value is consumed by a downstream
    rule or declared terminal; a named destination lane with no keyed entry is a dead branch — blocking.
    A fully-orphaned decision variable on an `is_decision: Yes` task is blocking.
16. **Action-app schema fidelity** — declared Input/Output fields ⊆ the resolved app's schema; a
    violation → high item `rev_action_schema_<task>`; code-switched reuse is sanctioned
    ([render-stages-tasks.md](render-stages-tasks.md)).
17. **Required-task presence** — a `required-tasks-completed` completion over a stage with zero
    `Required: Yes` tasks is vacuous and fails validation with `Stage exit rule '<name>' has no task(s)
    marked as required` (verified on uip 1.198.0-preview.102) — blocking; offer marking the stage's
    terminal task required.
18. **Resolved-resource presence** — concrete portable names everywhere (`Resolved Resource`, Action App
    title, `Child Case` — never `<UNRESOLVED>`); identity + folder pairs concrete together, or unresolved
    with a paired high item ([render-stages-tasks.md](render-stages-tasks.md)).
19. **Resolved-resource I/O completeness** — required inputs bound, extract fields exist verbatim
    ([render-stages-tasks.md](render-stages-tasks.md)); an unbound required input with no review item is
    blocking.
20. **Re-entry attempt check** — classify every `return-to-origin` / rework loop per
    [model.md § Task activation](model.md#sequencing--activation); new-attempt loops keep producer tasks
    rerunnable and reset or attempt-scope routing variables; re-evaluate loops document the re-read fact.

**On pass:** present the Case Review (the Build/Save answer is the consent; explicit sign-off adds one
prompt; design-only and draft requests save and stop). Corrections update the model and re-run only the
affected checks. **On fail:** fix the model and re-run the failed checks plus any whose inputs changed —
never the full suite; never present the review or render `sdd.md` while a fixable check is failing; only
unfixable items surface, as ⚠ flags.

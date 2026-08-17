# Case Review & Finalization

Planner-owned contract for the ONE confirmation checkpoint and the pre-confirmation checks that gate it.
Shared semantics are cited by ID from `../case-knowledge/` — never restated here.

## Case Review — the single checkpoint

One structured review, one question. Run §Finalization against the in-memory model FIRST — fix failures
silently (agent defects, not user decisions); unfixable → Review Flags rows. Decision-first business
approval surface, complete enough to approve case behavior without opening any SDD file — never a generic
build plan or a compressed SDD copy. The tenant-grounding resolution gate rides this same turn.

**Coverage map:** SDD §1 → Case Snapshot + SLA and Escalations + Rules and Outcomes; §2 → Primary Journey +
Other Paths Considered + SLA and Escalations + Rules and Outcomes; §3 → Case Snapshot + human action labels
+ action apps in Resources and Integrations; §4 → Resources and Integrations. The review intentionally
omits the data contract, variables, and task inputs/outputs — those stay complete in the SDD. Anything with
a `high` review item also appears in Review Flags.

Start with `## Case Review: <Case name>`, then exactly this section order:

1. **Case Snapshot** — `Item | Proposed design`. Rows: `Objective`, `Starts when`, `Primary personas`,
   `Successful completion`, `Other terminal outcomes`, `SLA coverage`. Mark assumed values `(assumed)`.
   No case ID prefix unless it affects a user decision.
2. **Primary Journey** — `# | Stage | Purpose | Tasks | Starts when | Completes or exits when | Required? |
   SLA`. Every primary stage once, flow order. `Tasks` names every task in execution order with type,
   required/optional status, activation/grouping — e.g. `Sequential: Capture request (Human action,
   required) → Validate request (RPA workflow, required)`; `After both: Make decision (Human action,
   required)`. Event-triggered and manually triggered tasks shown explicitly.
3. **Other Paths Considered** — `Scenario | Trigger or condition | Modeled as | Tasks | Interrupts active
   work? | Return or case outcome | Rationale`. Every modeled exception, secondary stage, optional path,
   alternate terminal — AND standard paths intentionally left unmodeled when that omission is a decision.
   Path tasks carry type, required/optional, activation/grouping.
4. **SLA and Escalations** — `Scope | SLA | Time target or condition | Status or threshold | Response |
   Response target | Interrupts active work? | Rationale`. One row per meaningful `(scope, SLA, status)`,
   separate at-risk and breached rows when both exist. Response from the closed set (K-SLA-4). Interrupting
   cell: `N/A` for `notify-only`; `—` for `start-task` (a task entry interrupts nothing — K-SLA-4, never
   `Yes`/`No`); otherwise `Yes`/`No` matching the produced entry row. Never assume every breach creates an
   escalation stage. `None` when the case has no SLA.
5. **Rules and Outcomes** — `Scope | Element | Rule | When | If | Then`. Business-significant routing,
   completion, and terminal rules only. Omit generated sequencing already visible in `Tasks`; do not repeat
   SLA rows unless needed to understand routing. Business conditions in `If`; no data/variable column.
6. **Resources and Integrations** — `Task | Intended resource or system | Resolution`. Action apps, agents,
   RPA/processes, API workflows, child cases, connectors, named external systems. `Resolution` = the
   design-time outcome: `resolved (<folder>)`, gate decision (`create during build`, `resolve at build`),
   or a candidate pick. A missing row is not acceptable.
7. **Decisions I Made** — `Decision | Why | Provenance`. Every assumption, override, resource decision,
   task-type decision, activation/sequence decision, intentionally omitted path. Plain-language provenance
   (`you said "then"`, `compliance wording`, `no SLA mentioned`). Group only decisions sharing rationale AND
   provenance. Don't repeat facts clear in another section unless the choice itself needs approval.
   Flagged items carry ⚠.
8. **Review Flags** — `Item to review | Why it matters | Default if accepted`. `None` when empty. Unfixable
   Finalization findings, missing connections, unresolved high-impact choices, anything to inspect before
   approving.

After Review Flags, show the fixed **Caller obligation** text (checklist item 11) when any §1.5 row is
`Category: In` + `Type: file`; omit otherwise — a conditional build obligation, not a ninth section.

**Product vocabulary.** User-visible activation labels: `Sequential`, `Parallel`, `Parallel after
predecessor`, `Event-triggered`, `Manually triggered`, `Fan-in`, `Conditional gate` (`adhoc` → `Manually
triggered`, `parallel-after-predecessor` → `Parallel after predecessor`). Prefer product task labels —
`Human action`, `Agent`, `RPA workflow`, `API workflow`, `Child case` — over schema enum names.

**No duplicated review surfaces.** Each business decision appears once. No Data Contract section, variable
rows, task I/O rows, second stages list, or per-stage/per-task detail cards — technical detail stays in
the SDD.

**Completeness gate.** Incomplete unless: all eight sections shown, every stage and task named, every
modeled and intentionally omitted path covered, every meaningful SLA response/status row present, Caller
obligation when relevant. No approval question before every section has been shown — even sections reading
`None`. Never substitute a list of build steps, artifacts, folders, or validation commands, or a summary
pointing at the SDD for a missing business decision.

**Confirmation question (AskUserQuestion)** — options by mode:

| Mode | Options |
|---|---|
| Build handoff | `Build it — straight through` / `Build it — pause at the build preview` / `Change something`. The Build answer is the consent AND the build-review preference, captured once, never re-asked mid-build. With ⚠ flags: first option reads `Build despite N flagged items — straight through`. |
| Direct design-only | `Save the design` / `Change something` (⚠ → `Save despite N flagged items`) |
| Draft request | `Save as draft` / `Change something`. A prompt that already says save-a-draft-and-stop counts as the answer: write immediately, no extra prompt. |

Corrections (`Change something` or free text) update the model, re-run affected Finalization checks, and
re-show ONLY the changed sections/rows, then a short `Suggested next steps` line before the next prompt.
A correction never restarts the walk. **Explicit sign-off requests** ("only after I approve") add exactly
one approval prompt after acceptance, before any file is created — nothing else changes.

## Review items

Shape: `{id: rev_<slug>, target, issue, severity: high|medium|low, next_step}` — kept in the model,
surfaced only in Review Flags (never the SDD body); the build persists them into
`tasks/registry-resolved.json` `review_items[]` (K-LEDG-4). Severity: `high` blocks the build until
resolved (missing connector/app/runnable identity, unbound required input `rev_unbound_input_<task>_<field>`,
phantom output `rev_phantom_output_<task>_<field>`, open lineage, missing trigger config, unreconciled
compliance override); `medium` = build can default with a prompt; `low` = cosmetic. With any `high` open,
the Build option is relabeled `Build despite N flagged items` — silently building past `high` is forbidden.
Never downgrade severity to pass the gate.

## Logical integrity — stage graph

Condition-only reachability is the sole guard (K-EDGE-2). Any failure → blocking error; offer `Re-edit` /
`Restart` / `Abort`.

1. **Every stage reachable from a trigger** — walk entry conditions forward from each trigger/SLA source
   (K-STG-7). Unreachable primary stage = orphan → blocking.
2. **Every stage exits** — each primary stage has a completion consumed downstream, or another stage's
   entry references it, or it feeds a secondary lane. A stage nothing keys off → blocking (terminal-loop).
3. **Every case-exit row references a stage that exists** — no dangling selectors.
4. **Every §1.4 Required-Stages path can complete** — ≥ 1 primary stage `Required: Yes` (K-PAIR-5), else
   the case can never complete.
5. **Secondary-lane entries: ≥ 1 interrupting entry each, DISTINCT, chosen by trigger source** (K-STG-5
   shapes; K-STG-6 global events — never repeat per origin). Two lanes with identical entries (rule +
   selectors + expression) are ambiguous routing — a design requirement to differentiate, NOT
   validate-enforced (as of uip 1.198.0-preview.102). Decision-reachable lanes MUST carry a
   `selected-stage-completed`/`-exited` + `IF` entry matching the origin's gated diverting exit, with the
   origin's completion gated by the inverse `IF` (K-STG-5) — missing divert dual-fires or deadlocks →
   blocking. A lane described as decision-reachable but entered only via `wait-for-connector` is unreachable
   from its stated source → blocking. `adhoc` is never a stage entry (K-SEQ-4).
6. **Every `sla-status-change` entry resolves** — target is `root` or an existing stage, that target
   declares the SLA, every supplied title matches a row on THAT target; a two-arg breach row is complete as
   written (K-SLA-3). Any real miss leaves the lane unreachable → blocking.
7. **Every secondary stage interrupting except a non-diverting SLA oversight row** (K-STG-3). Wrong
   classification → blocking; never promote the lane to a regular stage.

Worked example — decision-routed return lane (AP Review → SLA Escalation on `requiresEscalation`):

| Stage | Condition | WHEN | IF | Exit Type | Marks Complete |
|---|---|---|---|---|---|
| AP Review | exit (complete) | `required-tasks-completed` | `=js:(vars.requiresEscalation !== true)` | `exit-only` | Yes |
| AP Review | exit (divert) | `selected-tasks-completed("AP ownership review")` | `=js:(vars.requiresEscalation === true)` | `exit-only` (`exitToStageId` → SLA Escalation) | No |
| SLA Escalation | entry (`Interrupting: Yes`) | `selected-stage-exited("AP Review")` | `=js:(vars.requiresEscalation === true)` | — | — |
| SLA Escalation | exit | `required-tasks-completed` | — | `return-to-origin` | Yes |

On escalate the divert fires (completion's inverse `IF` false), the lane runs, `return-to-origin`
re-activates AP Review; on non-escalate the completion fires and the next stage enters via its own
`selected-stage-completed("AP Review")`. The decision is read directly from the producing action's output
(K-VAR-1) — never relayed through a §1.5 variable.

## Architect's lens — advisory pass

Emit `medium` review items when these fire (the noted `high` variants gate like any `high`):

| Check | Trigger | Review item |
|---|---|---|
| Single-recipient bottleneck | `action` recipient is one `User:`/`Email:` AND stage runs on every case AND no documented volume limit | `rev_bottleneck_<task>`: confirm volume or use UserGroup/Role |
| No escalation on SLA | Stage SLA set, escalation absent | `rev_escalation_<stage>`: no one paged on breach |
| Escalation loops to breacher | Escalation recipient = stage's primary recipient | `rev_escalation_loop_<stage>`: pick a tier-up recipient |
| Sync child case in critical path | `Wait for Completion: Yes` + parent SLA + no timeout cover | `rev_childcase_<task>`: consider async + completion connector or exception path |
| All-`action` stage | 100% `action`, > 2 tasks | `rev_human_only_<stage>`: consider agent/process pre-screen |
| No happy path on first stage | Only `No` exits, no `required-tasks-completed` row | `rev_no_happy_path_<stage>` |
| Decision outcome unread | `is_decision: Yes` writes a var no downstream rule reads | `rev_orphan_decision_<task>`: consume it or downgrade `is_decision` |
| Connector failure uncovered | Connector task in primary stage, no failure lane (`high` when ≥ 2 connector tasks share a critical path with zero cover) | `rev_no_failure_path_<task>` |
| Generic app substitute (`high`) | One Action App on ≥ 2 tasks WITHOUT distinct `actionType` each, or declared fields outside the app schema. Exempt: code-switched app (distinct `actionType` per task, fields ⊆ schema) — sanctioned pattern | `rev_substitute_app_<app>`: code-switch or deploy task-specific apps |
| Parallel bottleneck fan-in | ≥ 2 bottleneck stages fan into one downstream stage | `rev_multi_bottleneck_<stages>` |
| Case-var relay | §1.5 `Variable` whose only producer is one task output and only consumer is one binding (K-VAR-2 exemptions apply) | `rev_relay_var_<name>`: reference the output directly, drop the row |
| Aliased output | An Outputs `-> caseVar` row whose `Field` leaf has no matching §1.5 row and lands in a differently-named variable (K-VAR-7 forbids aliasing to CLOSE lineage; this catches the intentional-looking rest) | `rev_aliased_output_<task>`: declare a dedicated variable for the datum or confirm the reuse |

## Finalization checklist

Run ONCE against the in-memory model before presenting the review. Checks 16/19 need resolved I/O
contracts (`tasks describe` / `case spec`) the lane does not pull — they are enforced at build; run here
only when a contract is already in memory.

1. **Schema check** — every task type ∈ K-TYP-1; every WHEN ↔ Marks-Complete pair legal (K-PAIR-2).
2. **Render contract** — every required cell concrete (no banned `—`/`<UNRESOLVED>`).
   2a. **Template shape** — the rendered text passes the lane guide's template conformance gate, on-disk,
   before the `Status: ready` flip.
   2b. **Safe display names** — K-NAME-1 charset on every generated/carried display field; repair per
   K-NAME-2, disclose changes.
3. **Decision buttons** — `is_decision: Yes` ⟹ ≥ 2 buttons; every `Maps To` LHS is a §1.5 `Name` or `taskOutcome`.
4. **Recipient encoding** — typed prefixes only (K-TYP-7).
5. **Connector ids** — every connector task has `Connection ID` + `Activity Type ID`; every
   `wait-for-connector` rule (any scope) resolves `Connector Key` + `Event Operation` (+ `Connection ID`
   when not tenant-default). Missing → paired `high` item.
6. **Variable lineage** — every consumer closes (K-VAR-7).
7. **Override conflict** — no compliance trigger phrase paired with a non-`action` type without explicit
   user reconciliation.
8. **Alt-disposition coverage** — ≥ 1 secondary stage ⟹ §1.4a non-empty OR an open `high` item.
9. **High-severity acknowledgment** — `high` items force the `Build despite N flagged items` pick.
10. **Source ledger** — every non-`user-stated`/non-`verbatim` value has provenance.
    10a. **Design rationale** — every stage (kind + routing), task (type + activation/sequencing), and
    configured SLA (thresholds, recipients, response) carries durable rationale — blocking when missing.
    10b. **SLA Response Map closure** — one row per `(Scope, SLA, Status)`, responses ∈ K-SLA-4, every
    non-`notify-only` row has its matching rule and vice versa, Interrupting cells agree; a `notify-only`
    row that minted a stage/task, or a bare SLA with no row, is blocking.
11. **File-In-arg caller obligation** — when any `In` + `file` row exists, the review includes:
    `Caller obligation (file In-arg detected): File In-args: <names>. Programmatic callers must pre-create
    each JobAttachment via POST /odata/Attachments, PUT bytes, then pass {ID,FullName,MimeType,Metadata} as
    the In-arg value AND include the attachment ID in StartProcessDto.Attachments[]. Maestro Studio Web's
    "Start case" dialog does this automatically.` Informational, not blocking.
12. **Stage-graph connectivity** — the §Logical integrity walk, all seven checks.
    12a. **Entry producer/reference** — every non-start entry names a concrete producer (K-STG-7); at-risk
    rows name the escalation, breach rows the SLA alone (K-SLA-3).
13. **Domain fidelity** — every `verbatim:"…"` entity renders exactly; drift → `Re-edit` with the phrase pre-filled.
14. **Architect's lens** — run the advisory table; `medium` non-blocking, `high` variants gate.
15. **Decision-routing closure** — every routing button's variable+value consumed by a downstream rule or
    declared terminal; a named destination lane with no keyed entry = dead branch → blocking. Fully-orphaned
    decision var on `is_decision: Yes` → blocking.
16. **Action-app schema fidelity** — declared Input/Output fields ⊆ the resolved app's schema; violation →
    `high` `rev_action_schema_<task>`; code-switched reuse sanctioned (lens row).
17. **Required-task presence** — a `required-tasks-completed` completion over a stage with zero
    `Required: Yes` tasks is vacuous and fails validate (`Stage exit rule '…' has no task(s) marked as
    required` — K-PAIR-5) → blocking; offer marking the terminal task required.
18. **Resolved-resource presence** — concrete portable names everywhere (`Resolved Resource`, Action App
    title, `Child Case` — never `<UNRESOLVED>`); identity+folder pairs concrete together, or unresolved
    with a paired `high` item.
19. **Resolved-resource I/O completeness** — every required input bound (xref forms count, no §1.5 row
    needed — K-VAR-1) or `<UNRESOLVED>` + `high` item; every `->` Field exists verbatim in the resolved
    contract. Skip tasks with unresolved identity.
20. **Re-entry attempt check** — classify every `return-to-origin`/rework loop per K-SEQ-7; new-attempt
    loops keep producers rerunnable and reset/attempt-scope routing vars; re-evaluate loops document the
    re-read fact.

**On pass:** present the Case Review (the Build/Save answer is the consent; explicit sign-off adds one
prompt; design-only/draft requests save and stop). Corrections update the model and re-run only affected
checks. **On fail:** fix the model and re-run the failed checks (plus any whose inputs changed) — never the
full suite, never present the review or render `sdd.md` while a fixable check fails; only unfixable items
surface, as ⚠ flags.

<!-- END: review-finalize.md -->

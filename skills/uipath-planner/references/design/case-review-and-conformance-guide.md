# Case Management Review and Conformance Guide

The case review, draft finalization and SDD conformance gate. The case model they check is [case-product-guide.md](case-product-guide.md) (Layers 1–2) and [case-data-and-time-guide.md](case-data-and-time-guide.md) (Layers 3–4, § Layer closure). Read § Presenting the Case Design at the Phase 2 Step 5 review, § Finalizing a Case Draft when finalizing a draft, and § SDD Conformance Checklist at the template-superset check.

## Presenting the Case Design

The Phase 2 Step 5 architecture review of a case ([design-guide.md](design-guide.md)) is the **Case Review**: a decision-first business approval surface, complete enough to approve the case behaviour without opening the SDD — never a build plan and never a compressed SDD copy. Coverage: SDD Section 1 → review sections 1/4/5; Section 2 → 2/3/4/5; Section 3 → 1/6; Section 4 → 6. Each business decision appears ONCE. The review omits the data contract, variables, task inputs and outputs, a second stages list and per-stage detail cards — that detail stays in the SDD. Anything carrying a high review item also appears in Review Flags. An autonomous run writes no review; its decisions go to the SDD's Decisions Made and Design Rationale cells.

Start with `## Case Review: <Case name>`, then exactly this order:

1. **Case Snapshot** — `Item | Proposed design`. Rows: `Objective`, `Starts when`, `Primary personas`, `Successful completion`, `Other terminal outcomes`, `SLA coverage`. Assumed values marked `(assumed)`. No case ID prefix unless it affects a decision.
2. **Primary Journey** — `# | Stage | Purpose | Tasks | Starts when | Completes or exits when | Required? | SLA`. Every primary stage once, flow order. `Tasks` cell: every task in execution order with type, required/optional, activation/grouping — e.g. `Sequential: Capture request (Human action, required) → Validate request (RPA workflow, required)`; `After both: Make decision (Human action, required)`. Event-triggered and manually triggered shown explicitly.
3. **Other Paths Considered** — `Scenario | Trigger or condition | Modeled as | Tasks | Interrupts active work? | Return or case outcome | Rationale`. Every modeled exception, secondary stage, optional path, alternate terminal — AND standard paths intentionally unmodeled when that omission is a decision. Path tasks carry type/required/activation.
4. **SLA and Escalations** — `Scope | SLA | Time target or condition | Status or threshold | Response | Response target | Interrupts active work? | Rationale`. One row per meaningful `(scope, SLA, status)`; separate at-risk and breached rows when both exist; responses from the closed set ([§ Choosing the response](case-data-and-time-guide.md#choosing-the-response)). Interrupting cell: per the Response column's row in [§ Choosing the response](case-data-and-time-guide.md#choosing-the-response) — that table is the only home for which values are legal. `None` when no SLA. Never assume every breach creates an escalation stage.
5. **Rules and Outcomes** — `Scope | Element | Rule | When | If | Then`. Business-significant routing/completion/terminal rules only; omit generated sequencing visible in `Tasks`; no SLA repeats unless needed for routing; business conditions in `If`, no data column.
6. **Resources and Integrations** — `Task | Intended resource or system | Resolution`. Action apps, agents, RPA/processes, API workflows, business rules, child cases, connectors, named external systems. `Resolution` = design-time outcome: `resolved (<folder>)`, `create during build`, `resolve at build`, or a candidate pick. A missing row is not acceptable.
7. **Decisions I Made** — `Decision | Why | Provenance`. Every assumption, override, resource/task-type/activation decision, and intentionally omitted path, plain language (`you said "then"`, `compliance wording`, `no SLA mentioned`). Group only decisions sharing rationale AND provenance. Flagged items carry ⚠.
8. **Review Flags** — `Item to review | Why it matters | Default if accepted`. `None` when empty. Unfixable findings, missing connections, unresolved high-impact choices.

After Review Flags, when any §1.5 row is `Category: In` + `Type: file`, show this fixed block (omit otherwise — a conditional build obligation, not a ninth section):

```
Caller obligation (file In-arg detected):
  File In-args:  <comma-separated names>
  Programmatic callers must pre-create each JobAttachment via POST /odata/Attachments,
  PUT bytes to the returned blob URI, then pass {ID,FullName,MimeType,Metadata} as the
  In-arg value AND include the attachment ID in StartProcessDto.Attachments[].
  Maestro Studio Web's "Start case" dialog does this automatically.
```

**Product vocabulary.** User-visible activation labels: `Sequential`, `Parallel`, `Parallel after predecessor`, `Event-triggered`, `Manually triggered`, `Fan-in`, `Conditional gate` (`adhoc` → `Manually triggered`). Use product task labels — `Human action`, `Agent`, `RPA workflow`, `API workflow`, `Child case` — over schema enum names.

**Completeness gate.** Incomplete unless: all eight sections shown, every stage and task named, every modeled and intentionally omitted path covered, every meaningful SLA response/status row present, Caller obligation when relevant. No approval question before every section has been shown — even sections reading `None`. Never substitute a list of build steps, artifacts, folders, or validation commands, or a summary that points at the SDD for a missing business decision.

When a design was handed over by `uipath-maestro-case` ([sdd-writing-guide.md](sdd-writing-guide.md) § Design Handed Over by a Build Skill), the review's one question carries its build options: `Build it — straight through` / `Build it — pause at the build preview` / `Change something`; with open high review items the first option reads `Build despite N flagged items — straight through`. The answer is the build consent and the build-review preference, never re-asked mid-build.

## Finalizing a Case Draft

A case draft resumed by [sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 6 keeps every business element; these repairs are the only changes it makes on the way to the final SDD, beside the template's § Validation footer:

1. `user-selected-stage` repair per [case-product-guide.md](case-product-guide.md) § Repairing a `user-selected-stage` lane; wording such as "any active case" means every primary stage.
2. Every `=js:` expression in the draft appears verbatim in the output, inside the same owning task or stage block, with its field names, variable references, and output mapping intact — an equivalent-looking shorthand that drops an input, predicate, or intermediate field is a failure, not a simplification.
3. Threshold-policy conversion — MANDATORY scan, not optional polish. Scan the draft (descriptions, personas table, rationale) for comparator + amount phrases: `>`, `<`, `≥`, `≤`, `over`, `above`, `under`, `below`, `at least`, `more/less than` next to an amount (`$5M`, `100000`, `L4`). EVERY such policy must also appear in an executable cell of the owning task or stage in the final — prose-only is a render failure:
    - A personas row whose draft scope reads `StageX (amount > $N only)` renders in the final as Stages `StageX` and Notes `amount > $N only` — the Stages cell holds exact stage names only, since convert turns it into the role's stage ids — and REQUIRES a matching guarded expression inside a StageX task block, phrased on the HIGH side and assigning the exception role: an owner/recipient cell or entry-condition IF cell containing `=js:vars.amount > N000000 ? "Role:SomeRole" : "Role:DefaultRole"` — the numeral written out (`5000000`, not `$5M`), the role and attribute on the same line. The expression lives in a table cell (Inputs/owner/recipient/WHEN/IF); an `=js:` fragment inside `**Design Rationale:**` or `**Description:**` prose is NOT an encoding and fails the gate.
    - Reuse an existing variable that carries the attribute; the conversion never adds or renames a task or variable.
    - Persona prose and Design Rationale alone are not final.
4. Secondary-stage task headings normalize to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; never keep draft letter prefixes (`R.1`, `W.1`, `CC.1`, `ESC.1`).
5. A draft's per-stage SLA table may carry `At-Risk Action` / `Breach Action` columns; the final SDD does not. Move each response into the § SLA Response Map row for that `(scope, SLA, status)` — never drop it, never keep the column.

## SDD Conformance Checklist

The gate for the case template's § Validation footer, walked against the written file before the `Status: ready` flip — by a read-only subagent when the host has one (it returns the PASS/FAIL table; the parent edits), otherwise inline. Not part of authoring: the template's cell rules are the render contract.

Answer every item PASS or FAIL with one verbatim quote from the file — the line that violates (FAIL) or
the line that satisfies (PASS). Judge structure by the ROLE and POSITION of a block (which heading level,
which table, which column), not by prose wording. The enforcement detail behind each item is the
template's cell rules, which are COMPLETE for the render contract; design semantics stay
the case product guides'.

CONFORMANCE CHECKLIST — 37 items in 10 families. Items 30–33 apply only when finalizing a draft. Each item
names only what to LOOK AT.

 Skeleton
  1. The first non-empty line is `# SDD — <Case Name>`.
  2. Present, in this order: `## Document History`; `## Planner Handoff` with the `<!-- planner-handoff:v1 -->`
     marker; `## Table of Contents`; `## Section 1: Case Definition` holding `### Case Metadata`,
     `### Case Triggers`, `### Case Exit Conditions`, `### Case Variables`; `## Section 2: Stages & Tasks`;
     `## Section 3: Personas & App Views` holding `### Personas` and `### Process App Views`;
     `## Section 4: Integrations`.
  3. No summary-only top-level heading: `## Source`, `## Case Objective`, `## Actors And Systems`,
     `## Case Trigger`, `## Stages`, `## Business Rules`, `## Task Plan`, `## Resource Resolution`,
     `## Acceptance Scenarios`.
  4. The Case Variables header is literally
     `| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |`, and that
     table is the section's only table: every variable, task-output targets included, is a row of it —
     no second table, no `####` sub-heading split, no sibling `###` section (e.g.
     `### Task-output variables`). Only the first table declares variables; later rows drop silently.
  5. Every `### Stage <N>:` / `### Secondary Stage:` block carries `**Type:** Stage`, `**Design Rationale:**`,
     `#### Stage Entry Conditions`, `#### Stage Exit Conditions`, `#### Tasks`; a secondary stage carries an
     explicit `**Interrupting:** Yes` or `No`, and `Yes` whenever one of its exit rows is `return-to-origin`.
  6. Every row of a stage's Tasks table has its own `##### Task <N>.<M>:` block (`S<K>.<M>` in a secondary
     stage; never the letter prefixes `R.1` / `W.1` / `CC.1` / `ESC.1`) carrying `**Type:**`,
     `**Activation Mode:**`, `**Design Rationale:**`, an `**Entry Condition:**` table, `**Task envelope**`,
     and the detail block its type requires — action: `**HITL Implementation:**`; wait-for-connector:
     `**Connector:**` / `**Trigger / Event:**`; execute-connector-activity / external-agent / external-workflow:
     `**Connector:**` / `**Operation:**`; wait-for-timer: `**Timer:**` / `**Duration:**`; case-management:
     `**Child Case:**`; http-request: `**Method:**` / `**URL:**`; script: a ```` ```js ```` fenced function body; document-extraction: `**IXP Deployment:**` / `**Model Name:**`; process / agent / rpa / api-workflow / function / business-rule / flow-process: `**Resolved Resource:**`.
  7. No literal `\n` escape inside block content; `<UNRESOLVED>` is never backtick-wrapped; none of the
     skill-internal terms (groupOperator, savedFilterTrees, io-binding, auto-mint, originalVar,
     inputOutputs[]) appears anywhere in the body.
 Closed enums + gate-slot pairing
  8. Every task `**Type:**` is one of the seventeen literals in [case-product-guide.md](case-product-guide.md) § Task types. If a `Type:` appears in that section's never-author block, fix it as the block directs for its group: write the plan type it gives, or leave the task to Studio Web.
  9. In every table with a `Marks Stage Complete` / `Marks Case Complete` column, the WHEN rule is legal for
     that row's Yes/No per case-product-guide.md § Lifecycle gates; Stage Entry Conditions rows use only Stage-entry rules and task
     Entry Condition rows only Task-entry rules.
 10. Exit Type pairs with Marks Stage Complete — Yes: exit-only / return-to-origin / wait-for-user;
     No: exit-only / wait-for-user. `return-to-origin` never appears in Case Exit Conditions.
 Names
 11. No stage label and no task display name contains `:`.
 12. Stage labels are unique case-wide; task display names are unique case-wide, across every stage.
 SLA references + selectors
 13. Every `sla-status-change(...)` has 2 or 3 quoted args; arg 1 is the literal `root` or a declared stage
     display name; arg 2 is an SLA Title that target declares (the `SLA Title` row of Case Metadata for
     root; `**SLA Title:**` under the stage's `#### Stage SLA`); every SLA Response Map row whose response is not
     `notify-only` has its `sla-status-change` row, and every `sla-status-change` row has its Map row.
 14. Every `selected-stage-completed("X")` / `selected-stage-exited("X")` names a declared stage; every
     `selected-tasks-completed("T")` names a declared, non-`adhoc` task in the SAME stage.
 15. No stage's entry row references its own stage.
 Data closure
 16. Every `=vars.X` is a row in Case Variables.
 17. Every consumed variable whose Category is not `In` is produced somewhere: an Outputs row `-> X`, an
     assignment `X = ...`, a Default, or a sourceTriggers entry.
 18. Every `Out` variable has a Default or a producing Outputs row.
 19. Every Buttons `Maps To` target is a declared variable, `taskOutcome`, or an identifier read somewhere
     outside the Buttons tables.
 Recipients, entry tables
 20. Every `**Recipient:**` is `—`, `<UNRESOLVED>`, an `=` expression, or carries a typed prefix
     (`Role:` / `User:` / `UserGroup:` / `Email:` / `Expression:`).
 21. Every task `**Entry Condition:**` table, every `#### Stage Entry Conditions` table and every
     `#### Stage Exit Conditions` table has at least one body row.
 Structure
 22. Some stage's entry table carries a `case-entered` row.
 23. Case Triggers has at least one row.
 24. Case Exit Conditions has at least one row with Marks Case Complete `Yes`, and no two rows identical in
     (WHEN, IF, THEN, Marks).
 25. A `wait-for-user` exit exists if and only if a `user-selected-stage` entry exists.
 26. `required-stages-completed` used → some stage declares `**Required for Case Completion:** Yes`;
     `required-tasks-completed` on a stage → some task envelope in that stage has Required `Yes`.
 Precedence & liveness
 27. No stage entry row equals a Case Exit row in (rule, selector, IF) — case exit evaluates first, so the
     stage would be unreachable.
 28. Within a stage, no unguarded exit row (Marks `No`, empty IF) shares its WHEN with a guarded completion
     row (Marks `Yes`, IF set) — the exit always wins and the stage never completes.
 29. The Case-Level SLA and every stage SLA expressed in minutes lie within 15–1000, and no stage SLA
     exceeds the case-level SLA.
 Draft parity (finalizing a draft only)
 30. The ordered stage and task inventory equals the draft's — names verbatim, only letter prefixes renumbered.
 31. Every `=js:` expression in the draft appears verbatim in the final, inside the same owning block.
 32. Every comparator + amount policy in the draft (`>`, `<`, `≥`, `≤`, or the draft language's words for
     over / under / at least / more than / less than, next to an amount) is encoded in an executable cell
     (owner / recipient / WHEN / IF / Inputs) of the owning task or stage, on the same side of the
     comparison — prose in Design Rationale or Description does not count.
 33. The draft file still exists beside the final, unrenamed.
 Modelling completeness
 34. Every task's `Persona` cell names exactly ONE role — never an either/or (`Underwriter or Credit
     Analyst`, `Recruiter / Hiring Manager`). An either/or persona is a routing rule the source stated and
     the design never modelled: no guard picks between the roles at run time. Repair by naming the owning
     role, and where the split was genuinely conditional, author the condition as a guarded row on the
     deciding variable rather than as prose in the persona cell. `system` and `—` are single roles.
 35. No `user-selected-stage` entry sits on a lane that a decision, event, or SLA routes to.
     `user-selected-stage` is picker exposure — a person choosing the next stage by hand — never
     deterministic routing, so when the source says entry is automatic the picker row IS the defect:
     repair it per § Section 2 Authoring rules, stage-picker bullet, decision-routed branch (all four
     edits). Source silent on who launches the lane ⟹ keep what is authored.
 36. The Personas table header is literally `| Persona | Scope | Stages | Permissions | Description | Notes |`,
     and every row is machine-readable: Scope is `Case` or `Stages`; Stages names exact Section 2 stage
     display names (`—` for `Case`); Permissions holds only the permission keys the template lists, and a
     `Stages` row only View, Assign, ManageSLA, RunAdhocTasks; every task's `Persona` cell (rule 34) names a
     row of this table or `system`. `View, Act, Reassign` is prose, not permissions — `uip maestro case sdd
     convert` reports each such cell as a `case-role` Unresolved item and `validate --sdd` fails it. A
     condition on the persona goes in Notes and in a guarded cell (rule 32), never in Permissions or Stages.
 37. Every `api-event("<Name>")` WHEN cell quotes a Name declared verbatim in `### Business Events`
     (a Section 1 `###` sibling of Case Variables, header `| Name | Description | Payload |`), and every
     declared event is quoted by ≥1 cell. `api-event` stands only in Stage Entry, Stage Exit, Task Entry
     and Case Exit tables — never in Case Triggers, and never in a task's Entry Conditions that also hold
     `runs-sequentially`. A Payload cell is a JSON Schema object in one code span, or `—`.

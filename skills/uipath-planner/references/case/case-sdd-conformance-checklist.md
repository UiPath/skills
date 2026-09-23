# Case SDD — conformance checklist

The gate for `case-sdd-template.md`'s § Validation footer. The Case Design Lane runs this against the
written `sdd.md` BEFORE the `Status: ready` flip, in every mode — normally inside the one subagent
§ Template conformance gate allows ([case-design-lane-guide.md](case-design-lane-guide.md)).

This file is NOT part of the design reading set. Authoring reads the template for the render contract;
only the gate reads the item list. Keeping the two apart keeps 35 items of checker detail out of the
turn that is writing the document.

Answer every item PASS or FAIL with one verbatim quote from the file — the line that violates (FAIL) or
the line that satisfies (PASS). Judge structure by the ROLE and POSITION of a block (which heading level,
which table, which column), not by prose wording. The enforcement detail behind each item is the
template's cell rules, which are COMPLETE for the render contract; design semantics stay
[case-design-layers-guide.md](case-design-layers-guide.md)'s.

CONFORMANCE CHECKLIST — 35 items in 10 families. Items 30–33 apply only when finalizing a draft. Each item
names only what to LOOK AT; the enforcement detail behind it is the cell rules above, and for the render
contract those cells are COMPLETE — there is no third location, and nothing outside this template states a
shape rule they do not. (Design semantics — which response, which gate, which default — stay
case-design-layers-guide.md's; the cells own the shape.)

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
     `| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |`.
  5. Every `### Stage <N>:` / `### Secondary Stage:` block carries `**Type:** Stage`, `**Design Rationale:**`,
     `#### Stage Entry Conditions`, `#### Stage Exit Conditions`, `#### Tasks`; a secondary stage carries an
     explicit `**Interrupting:** Yes` or `No`, and `Yes` whenever one of its exit rows is `return-to-origin`.
  6. Every row of a stage's Tasks table has its own `##### Task <N>.<M>:` block (`S<K>.<M>` in a secondary
     stage; never the letter prefixes `R.1` / `W.1` / `CC.1` / `ESC.1`) carrying `**Type:**`,
     `**Activation Mode:**`, `**Design Rationale:**`, an `**Entry Condition:**` table, `**Task envelope**`,
     and the detail block its type requires — action: `**HITL Implementation:**`; wait-for-connector:
     `**Connector:**` / `**Trigger / Event:**`; execute-connector-activity: `**Connector:**` /
     `**Resolved Resource:**`; wait-for-timer: `**Timer:**` / `**Duration:**`; case-management:
     `**Child Case:**`; process / agent / rpa / api-workflow / function: `**Resolved Resource:**`.
  7. No literal `\n` escape inside block content; `<UNRESOLVED>` is never backtick-wrapped; none of the
     skill-internal terms (groupOperator, savedFilterTrees, io-binding, auto-mint, originalVar,
     inputOutputs[]) appears anywhere in the body.
 Closed enums + gate-slot pairing
  8. Every task `**Type:**` is one of the ten literals in case-design-layers-guide.md § Task types.
  9. In every table with a `Marks Stage Complete` / `Marks Case Complete` column, the WHEN rule is legal for
     that row's Yes/No per § Lifecycle gates; Stage Entry Conditions rows use only Stage-entry rules and task
     Entry Condition rows only Task-entry rules.
 10. Exit Type pairs with Marks Stage Complete — Yes: exit-only / return-to-origin / wait-for-user;
     No: exit-only / wait-for-user. `return-to-origin` never appears in Case Exit Conditions.
 Names
 11. No stage label and no task display name contains `:`.
 12. Stage labels are unique case-wide; task display names are unique case-wide, across every stage.
 SLA references + selectors
 13. Every `sla-status-change(...)` has 2 or 3 quoted args; arg 1 is the literal `root` or a declared stage
     display name; arg 2 is an SLA Title that target declares (the `SLA Title` row of Case Metadata for
     root; `**SLA Title:**` under the stage's `#### Stage SLA`); every SLA Response Map row has its
     `sla-status-change` row and vice versa.
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

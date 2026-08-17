# Build-ready SDD — the contract

What a case `sdd.md` must contain for the build to consume it trust-as-written. The full render shape is
the planner's template (`assets/templates/case-sdd-template.md`); this contract is the structural subset
both skills depend on.

**[K-SDD-1] Required skeleton.** First heading `# SDD — {Case Name}`; `## Document History`;
`## Planner Handoff` header + `<!-- planner-handoff:v1 -->` marker with `Status: ready`;
`## Table of Contents`; exact section headings `## Section 1: Case Definition` (containing
`### Case Metadata`, `### Case Triggers`, `### Case Exit Conditions`, `### Case Variables`),
`## Section 2: Stages & Tasks`, `## Section 3: Personas & App Views` (`### Personas`,
`### Process App Views`), `## Section 4: Integrations` (resource families or explicit `> None.`).

**[K-SDD-2] Per-stage / per-task blocks.** Every primary stage: `### Stage {N}: {Name}`; every secondary
stage: `### Secondary Stage: {Name}` with an explicit `**Interrupting:**` line. Every stage block:
`**Type:**`, `**Design Rationale:**`, `#### Stage Entry Conditions`, `#### Stage Exit Conditions`
(completion `Yes` and exit `No` rows in one table: `WHEN | IF | Exit Type | Marks Stage Complete |
Display Name`), `#### Tasks`. Every task: `##### Task {N}.{M}: {Name}` (secondary: `##### Task S{K}.{M}:`,
never letter prefixes) with `**Type:**` (K-TYP-1 value), `**Activation Mode:**`, `**Design Rationale:**`,
`**Entry Condition:**` + its `| WHEN | IF | Display Name |` table, exact marker `**Task envelope**`
(no colon), and the type-specific detail block. `<UNRESOLVED>` renders as plain text — never
backtick-wrapped (build checkers match the plain marker).

**[K-SDD-3] Cell grammar the build parses mechanically.** Condition cells use the call forms with complete
args (`selected-stage-completed("<Stage>")`, `sla-status-change("<root|Stage>","<SLA Title>"[,"<At-Risk
Escalation>"])` — target literal `root` for case scope); prose uses bare rule names, never partial call
forms. Inputs `Binding` cells use the K-EXPR-1 forms plus the xref forms (K-VAR-1); Outputs rows use the
K-VAR-5 operators. Bare field-name lists are forbidden. Portable names are ALWAYS concrete — `Resolved
Resource` on every `process`/`agent`/`rpa`/`api-workflow` task, the Action App title on every action, the
`Child Case` name on every case-management task — never `<UNRESOLVED>`. Identity and folder cells
(`Resource Identity`, `Folder Path`, `Action App ID`, `Deployment Folder`, `Binding Sub-Type`) are concrete
when resolved, or `<UNRESOLVED>` paired with a review item when deferred (K-LEDG-2's `resolve-at-build`
flow depends on this).

**[K-SDD-4] Companion artifacts.** The build derives `tasks/tasks.md` and
`tasks/registry-resolved.json` in a `tasks/` directory at the working root, ADJACENT to `sdd.md` — never
inside the solution/project directory. Any SDD header naming a tasks file points at `tasks/tasks.md`.

**[K-SDD-5] Receipt check** (the build runs this on any `sdd.md` it did not watch being written — one
Grep): the four `## Section {1..4}:` headings AND ≥ 1 `##### Task` detail block must be present. A
freeform/summary SDD (top-level `## Source`, `## Case Objective`, `## Task Plan`, `## Acceptance
Scenarios`, build-mode/path narration) is not buildable — route it back through the planner's template
conformance gate. A valid `caseplan.json` never proves the SDD followed the template.

<!-- END: sdd-contract.md -->

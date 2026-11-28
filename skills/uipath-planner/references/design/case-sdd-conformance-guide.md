# Case Management SDD Conformance Guide

The Validation footer of [case-sdd-template.md](../../assets/templates/case-sdd-template.md): its markers, the rules for finalizing a draft, the Draft repairs and the CONFORMANCE CHECKLIST. [sdd-writing-guide.md](sdd-writing-guide.md) Step 4 item 8 reads it whole and walks the checklist against the written file; finalizing a draft reads it before the first edit.

Markers: <UNRESOLVED> renders as plain text — never backtick-wrapped, never annotated in-cell — and stands only
where case-product-guide.md § Resources and Identities (`<UNRESOLVED>` scope) allows it, each paired with a review
item. `—` only where a template cell allows it. Narrative cells never carry skill-internal vocabulary (Pattern C,
bridge, companion, inputOutputs[], groupOperator, essentialConfiguration-as-prose, savedFilterTrees, dispatcher,
io-binding, aliased into/from, reassign, originalVar, auto-mint).

Never ship a summary SDD (top-level headings like ## Source / ## Case Objective / ## Stages / ## Task Plan, or
build-mode/path narration), even if a later caseplan.json would validate — rewrite from the model and the template.

FINALIZING a draft (`sdd.draft.md` -> the final SDD): the render obeys this contract IN FULL — the template's skeleton,
one `##### Task <n>: <Name>` detail block per task the draft inventories (never a stage-level Tasks table standing
in for them), `**Type:** Stage` on every stage block, the exact detail headings and bold field labels
(`**Timer:**` stays `**Timer:**`), Section 3/4 column headers verbatim, real newlines. Display names stay verbatim.
A task the draft left as a summary still gets its full detail block: concise defaults, every concrete value the
draft supplied kept, `**Resolved Resource:**` = the draft's intended resource name, else the task display name —
never <UNRESOLVED> there.

Upgrade every draft task block; never copy its shape. A draft task block lacks `**Activation Mode:**`,
`**Design Rationale:**` and `**Task envelope**` — add all three to EVERY task block, including blocks the draft
rendered completely (checklist item 3). Every table keeps the template's column headers, never the draft's:
- `**Activation Mode:**` from the draft's Starts When / sequencing column; `sequential` when it says nothing.
- `**Design Rationale:**` from the draft's own reasoning for the task: one concrete sentence, never boilerplate.
- `**Task envelope**` from the Inputs/Outputs the draft already lists.
Every stage block gets `**Type:** Stage` and `**Design Rationale:**` the same way.

Start the final as a copy of the draft (`cp <NAME>.draft.md <NAME>.md`, the draft kept), then upgrade it in place,
block by block, with file edits. Never rebuild it by writing ranges of draft lines in chunks: a chunk boundary inside
a table silently drops the rows after it. After every scripted rewrite, and before the checklist walk, run
`node "<SKILL_DIR>/scripts/case-draft-parity.mjs" "<NAME>.draft.md" "<NAME>.md"` (`<SKILL_DIR>` is the folder
holding planner's `SKILL.md`). It compares the stages in order with their kinds, the tasks under each stage, the
Case Variables rows and every `=js:` expression, finds every comparator + amount policy (repair 3) without its
`=js:` cell, and checks each Tasks table row's cell count and each `Role:` Recipient against its task's Persona.
Each `FAIL:` line is a defect your edits introduced: repair it in place from the draft and run it again until it
prints `OK`.
Then run `node "<SKILL_DIR>/scripts/case-sdd-check.mjs" "<NAME>.md"` the same way: it finds the template markers a
stage or task block lost (`**Design Rationale:**`, `**Activation Mode:**`, `**Entry Condition:**`, `**Task envelope**`),
a `**Type:**` outside the task types, an SLA Response Map row that breaks the template's cell rules, a Personas row
off the template's six cells or permission keys, an action task's `**HITL Implementation:**` that is not
`Action App: <title>` or names another task, and a Tasks-table Activation Mode that differs from its task block's.

Draft repairs — the only changes beside the template's rules and the rules above:
1. `user-selected-stage` repair per case-product-guide.md § Repairing a `user-selected-stage` lane; wording such as
   "any active case" means every primary stage.
2. Every `=js:` expression in the draft appears verbatim in the output, inside the same owning task or stage block,
   with its field names, variable references and output mapping intact — a shorthand that drops an input,
   predicate or intermediate field is a failure, not a simplification.
3. Threshold-policy conversion — a MANDATORY scan, not optional polish. Scan the draft (descriptions, personas
   table, rationale) for every comparator next to an amount: `>`, `<`, `≥`, `≤`, `over`, `above`, `under`,
   `below`, `at least`, `more/less than` beside `$5M`, `100000`, `L4`. Every such policy also appears in the
   final in an executable table cell (Inputs, owner/recipient, WHEN/IF) of the owning task or stage:
   - A personas row whose draft scope reads `StageX (amount > $N only)` renders as Stages `StageX` and Notes
     `amount > $N only`, AND a task block in StageX carries the guarded cell in its `**Recipient:**` (the policy
     picks WHO does the task, so never an entry-condition IF, which skips the task on the other side), phrased on
     the high side and assigning the exception role: `=js:vars.amount > 5000000 ? "Role:CreditAnalyst" : "Role:Underwriter"` —
     numeral written out (`5000000`, not `$5M`), role and attribute on one line.
   - Reuse the variable that carries the attribute; the conversion never adds or renames a task or variable.
   - Persona prose, Description, Design Rationale, or an `=js:` fragment inside them is not an encoding and
     fails the gate.
4. Secondary-stage task headings normalize to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; never
   keep draft letter prefixes (`R.1`, `W.1`, `CC.1`, `ESC.1`).
5. A draft's per-stage SLA table may carry `At-Risk Action` / `Breach Action` columns; the final SDD does not.
   Move each response into the § SLA Response Map row for that `(scope, SLA, status)` — never drop it, never keep
   the column.
6. A draft's `**HITL Implementation:**` cell (`JSON Schema`, a form, a schema) becomes
   `Action App: <this task's own name>` — the name in the `##### Task` heading of the block the cell sits in, never
   the stage's first task or the previous block's. A script that rewrites these cells reads the heading of each
   block, not the last one it matched.
7. A draft's Personas table (`| Persona | Stage Scope | Permissions | Description |` or any other shape) is
   re-rendered row by row into the template's `| Persona | Scope | Stages | Permissions | Description | Notes |`:
   stage scope `All` → Scope `Case`, Stages `—`; named stages → Scope `Stages`, those exact stage names; Permissions
   keep only the template's keys (`Act` is dropped — task work comes from each task's Recipient; `Reassign` →
   `Assign`), a `Stages` row only View, Assign, ManageSLA, RunAdhocTasks; the dropped prose goes to Notes. The
   persona names stay verbatim.
8. A task's Activation Mode is one literal, written the same in its stage's Tasks table and in its block's
   `**Activation Mode:**` line; where they differ, the block's Entry Condition decides (a task that starts after
   another is never `parallel`).

Gate: the CONFORMANCE CHECKLIST below, walked against the on-disk file BEFORE the Status: ready flip, in every
mode, by the procedure of sdd-writing-guide.md Step 4 item 8 — which also checks every template heading is present.
Items 19–21 apply only when finalizing a draft. Each item names what to LOOK AT; the template's cell rules are the
render contract, and a cell rule broken anywhere is a FAIL of the item that covers its section.

CONFORMANCE CHECKLIST — 21 items.

 Shape
  1. No summary-only top-level heading (`## Source`, `## Case Objective`, `## Actors And Systems`,
     `## Case Trigger`, `## Stages`, `## Business Rules`, `## Task Plan`, `## Resource Resolution`,
     `## Acceptance Scenarios`) — the rules live in Section 1's `### Business Rules`; no literal `\n` escape in block content; `<UNRESOLVED>` never backtick-wrapped.
  2. `### Case Variables` holds exactly one table, whose header is literally
     `| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |` — never the draft's own
     columns — and no second table, `####` sub-heading or sibling `###` section of variables (only the first
     table declares; later rows drop silently).
  3. Every stage block carries `**Type:** Stage`, `**Design Rationale:**` and the three `####` condition/task
     sections; a secondary stage an explicit `**Interrupting:**`, `Yes` whenever an exit row is
     `return-to-origin`. Every Tasks-table row has its own `##### Task <N>.<M>:` block (`S<K>.<M>` in a
     secondary stage) carrying `**Type:**`, `**Activation Mode:**`, `**Design Rationale:**`, an
     `**Entry Condition:**` table, `**Task envelope**`, and the detail block its type requires — action:
     `**HITL Implementation:**`; wait-for-connector: `**Connector:**` / `**Trigger / Event:**`;
     execute-connector-activity / external-agent / external-workflow: `**Connector:**` / `**Operation:**`;
     wait-for-timer: `**Timer:**`; case-management: `**Child Case:**`; http-request: `**Method:**` / `**URL:**`;
     script: a ```` ```js ```` fenced function body; document-extraction: `**IXP Deployment:**` /
     `**Model Name:**`; process / agent / rpa / api-workflow / function / business-rule / flow-process:
     `**Resolved Resource:**`. The `**Activation Mode:**` value, and the Tasks table's Activation Mode cell, is one
     template literal written verbatim — `sequential`, `parallel`, `parallel-after-predecessor`, `event-triggered`,
     `adhoc`, `fan-in`, `conditional-gate`; `Parallel after predecessor` or `Sequential: stage start` is a FAIL. A
     task that starts after another task is never `parallel` — siblings after one task are
     `parallel-after-predecessor`. The Tasks table keeps the template's nine columns. `runs-sequentially` is
     written bare, never with an argument (`runs-sequentially("Collect Fees")` is a FAIL).
  4. Every task `**Type:**` is one of the seventeen literals in case-product-guide.md § Task types. A `Type:` in
     that section's never-author block is fixed as the block directs: write the plan type it gives.
  5. Every WHEN is legal for its table and its Marks value (case-product-guide.md § Lifecycle gates); Exit Type
     pairs with Marks Stage Complete — Yes: exit-only / return-to-origin / wait-for-user, No: exit-only /
     wait-for-user; `return-to-origin` never in Case Exit Conditions.
  6. No stage label or task display name contains `:` (case-data-and-time-guide.md § Naming rules); stage labels are unique case-wide, and task display
     names unique across every stage.
 References
  7. Every `selected-stage-*("X")` names a declared stage other than its own; every `selected-tasks-completed("T")`
     a declared, non-`adhoc` task in the SAME stage.
  8. Every `sla-status-change(...)` has 2 or 3 quoted args: arg 1 `root` or a declared stage display name, arg 2
     an SLA Title that target declares. Every SLA Response Map row not `notify-only` has its `sla-status-change`
     row, and every `sla-status-change` row its Map row. A breach entry is the 2-arg form; arg 3, when present, is a
     display name from that target's SLA table (its At-Risk or Breach Escalation Display Name) — a status word
     (`Breached`, `At-Risk`) is a FAIL. Each `#### Stage SLA` holds the template's `**SLA Title:**` line and its
     `| SLA | Unit | At-Risk | … |` table, never `**Duration:**` / `**Breach Response:**` bullet lines.
  9. Every `api-event("<Name>")` quotes a `### Business Events` Name verbatim, every declared event is quoted
     once or more, and each cell stands where § Business Events allows. An event that enters an interrupting
     secondary stage from any point ("at any point", "any active case") is that lane's ONE entry row and no
     primary stage's exit row: the same `api-event` WHEN in two or more primary-stage Stage Exit tables is a FAIL.
 Data
 10. Every `=vars.X` is a Case Variables row; every consumed variable not `In` has a producer (an Outputs row
     `-> X`, an assignment, a Default, a sourceTriggers entry); every `Out` variable a Default or a producing
     Outputs row; every Buttons `Maps To` target is a declared variable, `taskOutcome`, or read outside the
     Buttons tables.
 Structure and liveness
 11. Every task Entry Condition, Stage Entry and Stage Exit table has a body row; some stage enters on
     `case-entered`; Case Triggers has a row; Case Exit Conditions has a Marks `Yes` row and no two identical
     rows.
 12. An exit row with Exit Type `wait-for-user` exists if and only if a `user-selected-stage` entry exists; no WHEN
     cell holds `wait-for-user`.
 13. `required-stages-completed` → some stage is `Required for Case Completion: Yes`; `required-tasks-completed`
     on a stage → some task envelope in that stage is Required `Yes`.
 14. No stage entry row equals a Case Exit row in (rule, selector, IF) — the case exit evaluates first; within
     a stage, no unguarded exit row (Marks `No`, empty IF) shares its WHEN with a guarded completion row.
 15. Case-Level SLA and every stage SLA in minutes lie within 15–1000; no stage SLA exceeds the case SLA.
 Roles
 16. Every task `Persona` cell names exactly ONE role — a row of the Personas table, or `system` — never an
     either/or (`Underwriter or Credit Analyst`); a conditional split is a guarded row on the deciding variable.
     Every `**Recipient:**` is `—`, `<UNRESOLVED>`, an `=` expression, or typed (`Role:` / `User:` /
     `UserGroup:` / `Email:` / `Expression:`), and a `Role:` names the task's own Persona from its Tasks-table row.
     Answer it as a list, one line per action task: `<task> — Persona <cell> — Recipient <value>`; any line where
     the two differ is a FAIL. Recipients a script wrote are read back this way before the item can PASS.
 17. The Personas table header is literally `| Persona | Scope | Stages | Permissions | Description | Notes |`, and
     every row is machine-readable per its § Personas comment: Scope, exact stage names, listed permission keys
     only. `View, Act, Reassign` is prose, not permissions — convert reports a `case-role`
     Unresolved item and `validate --sdd` fails it.
 18. No `user-selected-stage` entry sits on a lane that a decision, event or SLA routes to — the picker row is
     then the defect (case-product-guide.md § Repairing a `user-selected-stage` lane). Source silent on who
     launches the lane → keep what is authored.
 Mechanical gate — the template markers, the task types and the SLA Response Map rows PASS only after
 `case-sdd-check.mjs` prints `OK`, and § Business Rules only after `br-coverage.mjs` prints `OK` against the
 source; quote both lines
 Draft parity (finalizing a draft only) — items 16, 19 and 20 PASS only after `case-draft-parity.mjs` prints `OK`;
 quote that line
 19. The ordered stage and task inventory equals the draft's — names verbatim, only letter prefixes renumbered —
     and every Case Variables row of the draft is in the final with its name and type; count the rows in both.
     Every stage keeps its draft kind (primary stays primary with its completion exit, secondary stays
     secondary); list `<stage> — draft kind — final kind`. Every task keeps its draft start point: a task gated
     on `selected-tasks-completed("X")` still starts after X — siblings after X become
     `parallel-after-predecessor` with `runs-sequentially`, a lone follower `sequential` — never `parallel` /
     `current-stage-entered`; list `<task> — draft WHEN — final WHEN`.
 20. Draft repairs 2 and 3 hold: every draft `=js:` expression verbatim in its owning block, and every
     comparator + amount policy in an executable cell of its owning task or stage — a policy that picks a role in
     the `**Recipient:**`, never an entry IF — with a one-sided role written on the high side. The PASS quote is
     the `=js:` cell itself; a quote without `=js:` is a FAIL.
 21. The draft file still exists beside the final, unrenamed.

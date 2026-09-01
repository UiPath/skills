<!-- tasks/tasks.md — COMPACT NO-BUILD PLAN.
     Copy this file's shape. Do not invent one from the SDD's heading style: the SDD
     nests tasks under `##### Task: <name>`, and carrying that habit here produces
     `#### T21:` headings that audit_plan.py cannot see as T-entries at all — it
     reports no error, it just silently counts zero tasks.

     Every T heading is EXACTLY two hashes. Not `###`, not `####`, at any depth of
     the document. `## T{N}: task "{Task Name}"` and nothing else.

     This is the PLAN-ONLY shape, used whenever the request stops at sdd.md +
     tasks/tasks.md with no caseplan.json. It carries NO registry-derived data:
     no task-type id, activity-type id or connection id, and none of the resolved
     registry / resolved recipients sidecar keys. audit_plan.py rejects those by
     name anywhere in the file — including inside a comment, so do not quote them
     even to explain them. The build-path plan is a different shape
     (`## T{N}: Add <type> task "<name>" to "<stage>"`); never mix the two.

     Gate: `python3 <this skill>/scripts/audit_plan.py tasks/tasks.md` must print
     AUDIT OK before the plan is considered finished. -->

## Inventory

- case: "<CaseName>"
- stages: <N>
- tasks: <N>

<!-- One `## T{N}` entry per SDD stage, task, trigger, condition, SLA rule, variable
     and argument — lossless. Number them in plan order. -->

## T01: task "<Task Name>"

- stage: "<Stage Name>"
- type: <process | agent | rpa | action | api-workflow | case-management | execute-connector-activity | wait-for-connector | wait-for-timer>
- activation-mode: sequential
- entry-rule: runs-sequentially
- lane: 0
- required: true
- run-only-once: false
- resource-intent: "<what this task is for, from the SDD>"
- identity: <UNRESOLVED: resolve at build>
- rationale: "<the SDD's Design Rationale for this task, preserved verbatim>"
- inputs:
  - APIInput1 = "literal-seed"
  - APIInput2 <- "Stage Name"."Producer Task".APIOutput1
- outputs:
  - APIOutput1 -> renamedResult
  - literalResult = "literal-assigned"

<!-- I/O rows are BARE. One list item per SDD Inputs/Outputs row, in SDD order.
     The separator IS the operator: `=` assigns, `<-` consumes another task's
     output, `->` extracts a field into a case variable.

     Strip the SDD's presentation: its `Field` and `Binding / Value` cells are
     Markdown code spans and its `Type` is its own column. Emit NO backticks on
     either operand, NO type annotation in any form, and NO `:` separator. An
     operand that already carries quotes (`"literal-seed"`) keeps exactly those.

       INVALID   - `APIOutput1` (string) -> `renamedResult`
       INVALID   - APIOutput1 (string) -> renamedResult
       INVALID   - APIInput1 | string | <- "Stage"."Task".APIOutput1
       INVALID   - APIInput1: '<- "Stage"."Task".APIOutput1'
       VALID     - APIOutput1 -> renamedResult

     A bare item with no operator (`- APIOutput1`) is reserved for a
     schema-discovered auto-mint output and never comes from an SDD row.
     Full projection contract, both tables:
     references/plugins/variables/io-binding/planning.md -->

<!-- All fields above are REQUIRED on every task entry except `lane`, which is
     mandatory only for sequential runs. `identity` stays `<UNRESOLVED: ...>` on the
     plan-only path — never fabricate an id.

     `activation-mode` and `entry-rule` must pair legally:

       entry-rule                  legal activation-mode
       -------------------------   -------------------------------------------
       runs-sequentially           sequential, parallel-after-predecessor
       current-stage-entered       parallel
       adhoc                       adhoc
       selected-tasks-completed    fan-in, conditional-gate
       wait-for-connector          event-triggered

     Any other entry-rule is an explicitly authored event/condition rule and pairs
     with whichever mode permits it. Repeat BOTH lines on every task — never author
     them once and let later tasks inherit. `validate` only warns on a missing entry
     rule; `case debug` hangs on it. -->

## T02: task "<Second Task Name>"

- stage: "<Stage Name>"
- type: action
- activation-mode: parallel
- entry-rule: current-stage-entered
- required: true
- run-only-once: true
- resource-intent: "<what this task is for>"
- identity: <UNRESOLVED: resolve at build>
- rationale: "<preserved from the SDD>"

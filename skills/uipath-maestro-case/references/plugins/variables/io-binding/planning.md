# I/O Binding — Planning

Trust the SDD. Emit inputs/outputs exactly as declared. There is no `caseplan.json` yet — all validation happens during [implementation](impl-json.md).

## Discovering Input/Output Names

1. **SDD per-task tables** — primary source. Each task lists input/output field names, types, and variable bindings.
2. **`uip maestro case tasks describe --type <type> --id "<taskTypeId>" --output json`** — validates SDD names and discovers additional fields (e.g., standard `Error` output). The SDD per-task Outputs table uses TWO operators (per v1 contract — see [`assets/templates/sdd-template.md`](../../../../assets/templates/sdd-template.md) Section 2):

   **`->` operator — extract a field into a case variable.** Left side is the **full runtime path** the value lives at relative to the task's root scope; right side is the target case variable name:
   ```markdown
   - outputs:
     - response.status        -> sendStatus    # connector payload field → vars.sendStatus
     - response.message.ts    -> messageTs     # nested connector field  → vars.messageTs
     - Error                  -> error         # top-level error (connector or action) → vars.error
     - Error.code             -> errorCode     # nested error sub-field   → vars.errorCode
     - Action                 -> userDecision  # action task's top-level output → vars.userDecision
   ```

   `<sdd-field-path> -> <case variable>`. Left side is the full runtime path. Right side becomes `var` / `id` / `value` on `task.data.outputs[]` (the case-scope variable name). Extracted source is `"=<sdd-field-path>"` verbatim — the skill emits the SDD's left-side string with `=` prefix; never adds, removes, or infers envelope prefixes. Target case variable MUST exist in the Case Variables table.

   **`=` operator — set / compute / copy a literal or expression into an existing case variable.** Left side is the target case variable (must already exist in Case Variables); right side is the expression. No `Field` column:
   ```markdown
   - outputs:
     - caseStatus  = "InReview"                            # literal
     - reviewCount = =js:vars.reviewCount + 1              # computed expression
     - summary     = =vars.response.message.text           # copy from another variable's sub-field
   ```

   `<case variable> = <expression>`. Expression can be a plain literal string/number/bool, a `=js:` computation, or a `=vars.X.Y` variable reference. Target case variable MUST exist in the Case Variables table.

   **Dot-path support** on the left side of `->`: full paths like `response.message.ts`, `response.data.user.email`, `Error.code` are emitted as-is. Array indexing (`items[0]`) is NOT supported in v1 — fall back to consuming the array variable and using `=js:` expressions downstream.

   **Bare-name outputs** (no operator): emits an auto-mint entry that references a **top-level** Step 0 schema entry (e.g., `Error` or a pre-expanded shortcut like Slack's `ts`). `id = var = value = camelCase(entry name)`. Source is the entry's pre-populated value verbatim. For non-top-level fields, use the `->` operator with the full path instead.
   ```markdown
   - outputs:
     - Error            # bare — references top-level Error entry; produces vars.error (source = entry's =Error)
   ```

3. **Unresolved taskTypeId** — `tasks describe` unavailable. Follow [placeholder-tasks](../../../placeholder-tasks.md) — omit `inputs:`/`outputs:`, capture wiring intent in a fenced code block.

Do not fabricate names not in the SDD or `tasks describe`. Validation of variable existence happens at planning time (Phase 2) for `=` rows (target must exist in Case Variables); at implementation time (Phase 3) for `->` rows (deferred to io-binding validator).

## Input/Output Notation

For the full notation and expression prefixes, see [bindings-and-expressions.md](../../../bindings-and-expressions.md). Quick reference:

| Source | Notation | Example |
|---|---|---|
| Cross-task output | `input <- "Stage"."Task".output` | `emails <- "Triage"."Fetch Inbox".emails` |
| Global variable | `input = "=vars.<id>"` | `caseId = "=vars.caseId"` |
| Metadata | `input = "=metadata.<field>"` | `caseRef = "=metadata.ExternalId"` |
| Binding | `input = "=bindings.<id>"` | `connectionId = "=bindings.bA1B2C3D4"` |
| Literal | `input = "<value>"` | `maxResults = "50"` |

> **Note:** task INPUT bindings still use `<-` for cross-task references (`input <- "Stage"."Task".output`) — this is the planner-side notation for "this input value comes from another task's output." Task OUTPUT bindings use `->` for extract (`Field -> caseVar`) and `=` for set/compute/copy. Different directional conventions because inputs read from somewhere; outputs write to somewhere.

Record discovered outputs on each task entry (`outputs: kycResult, riskScore, error`) so downstream cross-task references can be validated during implementation.

> **Planner emits SDD-natural form; impl applies the per-sink canonical wrap.** Values in `tasks.md` use the natural prefix notation shown above — `=vars.X`, `=metadata.X`, `=bindings.X`, cross-task `<-`. The implementation step rewrites each value to its canonical sink form when constructing `caseplan.json` (e.g., `=js:(vars.X)` for connector body fields, `=js:metadata.X` for `=metadata` references in any sink that runs the JS evaluator). Full rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Outputs table validation rules

Apply at planning time (Phase 2):

| Rule | Severity | Detail |
|---|---|---|
| `->` row's target case variable not in Case Variables table | ERROR | Outputs declare bindings, not new variables. Target must pre-exist. |
| `=` row's target case variable not in Case Variables table | ERROR | Same — `=` writes to existing variable's slot. |
| `->` row missing left-side Field | ERROR | `->` requires a schema field name on the left. |
| `=` row has a non-empty Field column | ERROR | `=` rows have `—` (no field), since the source is the right-side expression, not a schema field. |
| Per task: same target case variable appears in multiple Outputs rows | ERROR | No double-binding; one row per target var per task. Last-writer-wins is a runtime footgun. |

## Scoping

| Task location | Can reference |
|---|---|
| Regular stage task | Earlier stages + same stage earlier tasks + root variables |
| Exception stage task | ALL tasks across ALL stages |
| Adhoc task | ALL tasks |

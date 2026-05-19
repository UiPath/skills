# I/O Binding — Planning

Trust the SDD. Emit inputs/outputs exactly as declared. There is no `caseplan.json` yet — all validation happens during [implementation](impl-json.md).

## Discovering Input/Output Names

1. **SDD per-task tables** — primary source. Each task lists input/output field names, types, and variable bindings.
2. **`uip maestro case tasks describe --type <type> --id "<taskTypeId>" --output json`** — validates SDD names and discovers additional fields (e.g., standard `Error` output). When SDD names differ from `tasks describe`:

   **Input-side aliasing** (when SDD's input name differs from the connector/process arg name):
   ```markdown
   - inputs:
     - in_Amount = "=vars.amount"   # SDD calls this "amount", process arg is "in_Amount"
   ```

   **Output-side aliasing** (when SDD's case-variable name differs from the connector/process response field name):
   ```markdown
   - outputs:
     - finalDecision <- Decision         # response field "Decision" → vars.finalDecision
     - creditScore   <- result.score     # nested response path → vars.creditScore
     - notes         <- Comments         # display label "Comments" → vars.notes
     - error                              # bare name = response field "Error" → vars.error (camelCased)
   ```

   **Notation:** `<sdd-name> <- <response-path>`. Left side becomes `var` / `id` on `task.data.outputs[]` (the case-scope variable name). Right side becomes the `source: "=<response-path>"` extraction. Bare name (no `<-`) defaults to camelCased response field name for both sides.

   **Dot-path support** on the right side: `result.score`, `data.user.email`, etc. Array indexing (`items[0]`) is NOT supported in v1 — fall back to consuming the array variable and using `=js:` expressions downstream.

3. **Unresolved taskTypeId** — `tasks describe` unavailable. Follow [placeholder-tasks](../../../placeholder-tasks.md) — omit `inputs:`/`outputs:`, capture wiring intent in a fenced code block.

Do not fabricate names not in the SDD or `tasks describe`. Do not validate variable existence or scoping — those checks belong in implementation.

## Input/Output Notation

For the full notation and expression prefixes, see [bindings-and-expressions.md](../../../bindings-and-expressions.md). Quick reference:

| Source | Notation | Example |
|---|---|---|
| Cross-task output | `input <- "Stage"."Task".output` | `emails <- "Triage"."Fetch Inbox".emails` |
| Global variable | `input = "=vars.<id>"` | `caseId = "=vars.caseId"` |
| Metadata | `input = "=metadata.<field>"` | `caseRef = "=metadata.ExternalId"` |
| Literal | `input = "<value>"` | `maxResults = "50"` |

Record discovered outputs on each task entry (`outputs: kycResult, riskScore, error`) so downstream cross-task references can be validated during implementation.

## Scoping

| Task location | Can reference |
|---|---|
| Regular stage task | Earlier stages + same stage earlier tasks + root variables |
| Exception stage task | ALL tasks across ALL stages |
| Adhoc task | ALL tasks |

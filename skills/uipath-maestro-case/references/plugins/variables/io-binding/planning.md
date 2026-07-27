# I/O Binding — Planning

Trust the SDD. Emit inputs/outputs exactly as declared. Every SDD Outputs row carries `->` or `=`; preserve that operator and both operands through `tasks.md`. Bare `tasks.md` outputs come only from resolved-schema discovery, never from an SDD row. There is no `caseplan.json` yet — all validation happens during [implementation](impl-json.md).

## SDD table to `tasks.md` projection (mandatory)

The SDD Outputs table has separate `Field`, `Type`, and `Binding / Value` columns, while `tasks.md` uses one canonical list item per row. Project each SDD row exactly once:

| SDD `Field` | SDD `Binding / Value` | Canonical `tasks.md` item |
|---|---|---|
| `Error.Message` | `-> errorMessage` | `Error.Message -> errorMessage` |
| `—` or blank | `literalResult = "literal-assigned"` | `literalResult = "literal-assigned"` |
| `—` or blank | `copiedResult = =vars.renamedResult` | `copiedResult = =vars.renamedResult` |

Treat `—` and blank `Field` cells on `=` rows as presentation-only placeholders, never as operands or operators. The `Binding / Value` cell already contains the complete assignment; copy that cell unchanged and do not prepend the Field or another `=`. For a `->` row, concatenate the non-empty Field and `Binding / Value` cells once. A non-empty Field with a blank or `—` Binding is not a third SDD form; reject it as ambiguous and use AskUserQuestion.

```markdown
<!-- INVALID: leaked the SDD Field placeholder and invented an extra operator -->
- — = literalResult = "literal-assigned"

<!-- INVALID: bare auto-mint is schema-discovered, not SDD-authored -->
| APIOutput1 | string | — |

<!-- VALID -->
- literalResult = "literal-assigned"
```

Before the Phase 1 approval gate, reject any SDD Outputs row without `->` or `=`, and reject any `tasks.md` output item whose first token is `—`, `->`, or `=`. Every SDD-projected item must match `<field-path> -> <case-variable>` or `<case-variable> = <expression>`; `<top-level-field>` is reserved for schema-discovered items.

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

   `<sdd-field-path> -> <case variable>`. Left side is the full runtime path. Right side becomes `var` / `value` on `task.data.outputs[]` (the case-scope variable pointer); `id` / `originalVar` / `target` are allocated independently from the source leaf and global collision pool. Extracted source is `"=<sdd-field-path>"` verbatim — the skill emits the SDD's left-side string with `=` prefix; never adds, removes, or infers envelope prefixes. Target case variable MUST exist in the Case Variables table.

   **Equal-name extract is still an extract.** `greeting -> greeting` means "write schema field `greeting` into the already-declared case variable `greeting`." Keep the arrow in `tasks.md`; never normalize it to bare `greeting`. Implementation keeps `var` / `value` pointed at the existing `greeting` Case variable and always emits `originalVar`. The source-side `id`, `originalVar`, and `target` stay `greeting` when the only collision is that matching root companion; an unrelated task/trigger/rule owner forces normal allocation (`greeting2`, `greeting3`, ...).

   **`=` operator — set / compute / copy a literal or expression into an existing case variable.** Left side is the target case variable (must already exist in Case Variables); right side is the expression. The SDD `Field` cell is `—` or blank and contributes no token to `tasks.md`:
   ```markdown
   - outputs:
     - caseStatus  = "InReview"                            # literal
     - reviewCount = =js:vars.reviewCount + 1              # computed expression
     - summary     = =vars.response.message.text           # copy from another variable's sub-field
   ```

   `<case variable> = <expression>`. Expression can be a plain literal string/number/bool, a `=js:` computation, or a `=vars.X.Y` variable reference. Target case variable MUST exist in the Case Variables table.

   **Dot-path support** on the left side of `->`: full paths like `response.message.ts`, `response.data.user.email`, `Error.code` are emitted as-is. The first segment selects the top-level schema output; implementation then walks that output's nested schema one segment at a time and takes the emitted `type` from the final leaf — never from the top-level parent. A nested row references its top-level parent, so `Error.Message -> errorMessage` does NOT also auto-mint a bare `Error` output unless schema discovery independently adds `Error` to `tasks.md`. Array indexing (`items[0]`) is NOT supported in v1 — fall back to consuming the array variable and using `=js:` expressions downstream.

   **Schema-discovered bare outputs** (no SDD row): emit an auto-mint item for a **top-level** Step 0 schema entry that the SDD does not bind (e.g., `Error` or a pre-expanded shortcut like Slack's `ts`). `id = var = value = camelCase(entry name)`. Source is the entry's pre-populated value verbatim. Never obtain this form from an SDD Outputs row. For non-top-level fields, require the SDD `->` operator with the full path instead.
   ```markdown
   - outputs:
     - Error            # bare — references top-level Error entry; produces vars.error (source = entry's =Error)
   ```

3. **Unresolved taskTypeId** — `tasks describe` unavailable. Follow [placeholder-tasks](../../../placeholder-tasks.md) — omit `inputs:`/`outputs:`, capture wiring intent in a fenced code block.

Do not fabricate names not in the SDD or `tasks describe`. Validation of variable existence happens at planning time (Phase 1) for `=` rows (target must exist in Case Variables); at implementation time (Phase 3) for `->` rows (deferred to io-binding validator).

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

### Canonical `tasks.md` output list

Record outputs on each task entry as one item per row. This is the common output-list grammar for every resolved task type. Project SDD-declared rows using the table above, then preserve each canonical item unchanged; append only genuinely additional schema-discovered fields as bare items:

```markdown
- outputs:
  - APIOutput1
  - greeting -> greeting
  - Error.Message -> errorMessage
  - literalResult = "literal-assigned"
  - copiedResult = =vars.renamedResult
```

Do not reduce this to a comma-separated list of names: that representation loses the operator and destination required by implementation.

> **Planner emits SDD-natural form; impl applies the per-sink canonical wrap.** Values in `tasks.md` use the natural prefix notation shown above — `=vars.X`, `=metadata.X`, `=bindings.X`, cross-task `<-`. The implementation step rewrites each value to its canonical sink form when constructing `caseplan.json` (e.g., `=js:(vars.X)` for connector body fields, `=js:metadata.X` for `=metadata` references in any sink that runs the JS evaluator). Full rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Outputs table validation rules

Apply at planning time (Phase 1):

| Rule | Severity | Detail |
|---|---|---|
| `->` row's target case variable not in Case Variables table | ERROR | Outputs declare bindings, not new variables. Target must pre-exist. |
| `=` row's target case variable not in Case Variables table | ERROR | Same — `=` writes to existing variable's slot. |
| `->` row missing left-side Field | ERROR | `->` requires a schema field name on the left. |
| `=` row has a non-empty Field column | ERROR | `=` rows have `—` (no field), since the source is the right-side expression, not a schema field. |
| SDD row has a non-empty Field and blank / `—` Binding | ERROR | Bare output is not SDD syntax. AskUserQuestion; schema discovery may independently add the field to `tasks.md`. |
| `tasks.md` output item starts with `—`, `->`, or `=` | ERROR | An SDD table placeholder or operator leaked into the left operand. Re-project the row using the mandatory table above. |
| Per task: same target case variable appears in multiple Outputs rows | ERROR | No double-binding; one row per target var per task. Last-writer-wins is a runtime footgun. |
| Any SDD Outputs row differs from its `tasks.md` item in operator or operand | ERROR | The handoff is lossy. Restore the exact SDD row before approval; this includes equal-name `field -> field`. |

## Scoping

| Task location | Can reference |
|---|---|
| Regular stage task | Earlier stages + same stage earlier tasks + root variables |
| Secondary stage task | ALL tasks across ALL stages |
| Adhoc task | ALL tasks |

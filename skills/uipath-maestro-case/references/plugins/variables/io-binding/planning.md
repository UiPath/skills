# I/O Binding — Planning

Trust the SDD and emit inputs/outputs exactly as declared. Every SDD Outputs row carries `->` or `=`; preserve its operator and both operands in the caseplan. Bare outputs come only from resolved-schema discovery, never from an SDD row.

## Input/Output Notation

Use only these canonical reasoning forms—not intermediate-plan files: `<field-path> -> <case-variable>`, `<case-variable> = <expression>`, and `<Field> <- <Binding>`. Normalize SDD rows for [impl-json.md](impl-json.md), which writes `data.inputs[]` / `data.outputs[]`.

For the full notation and expression prefixes, see [bindings-and-expressions.md](../../../bindings-and-expressions.md). Quick reference:

| Source | Notation | Example |
|---|---|---|
| Cross-task output | `input <- "Stage"."Task".output` | `emails <- "Triage"."Fetch Inbox".emails` |
| Global variable | `input = "=vars.<id>"` | `caseId = "=vars.caseId"` |
| Metadata | `input = "=metadata.<field>"` | `caseRef = "=metadata.ExternalId"` |
| Binding | `input = "=bindings.<id>"` | `connectionId = "=bindings.bA1B2C3D4"` |
| Literal | `input = "<value>"` | `maxResults = "50"` |

> **Note:** task INPUT bindings still use `<-` for cross-task references (`input <- "Stage"."Task".output`) — this is the planner-side notation for "this input value comes from another task's output." Task OUTPUT bindings use `->` for extract (`Field -> caseVar`) and `=` for set/compute/copy. Different directional conventions because inputs read from somewhere; outputs write to somewhere.

## Canonical output list

Record outputs on each task entry as one item per row. This is the common output-list grammar for every resolved task type. Project SDD-declared rows using the table in [§ SDD Outputs table to caseplan projection](#sdd-outputs-table-to-caseplan-projection-mandatory), then preserve each canonical item unchanged; append only genuinely additional schema-discovered fields as bare items:

```markdown
- outputs:
  - APIOutput1
  - greeting -> greeting
  - Error.Message -> errorMessage
  - literalResult = "literal-assigned"
  - copiedResult = =vars.renamedResult
```

Do not reduce this to a comma-separated list of names: that representation loses the operator and destination required by implementation.

### SDD Outputs table to caseplan projection (mandatory)

The SDD Outputs table has `Field`, `Type`, and `Binding / Value`; project each row exactly once:

| SDD `Field` | SDD `Binding / Value` | Canonical item |
|---|---|---|
| `Error.Message` | `-> errorMessage` | `Error.Message -> errorMessage` |
| `—` or blank | `literalResult = "literal-assigned"` | `literalResult = "literal-assigned"` |
| `—` or blank | `copiedResult = =vars.renamedResult` | `copiedResult = =vars.renamedResult` |

For `=` rows with blank or `—` `Field`, copy the complete `Binding / Value` cell unchanged; do not prepend `Field` or another `=`. For `->` rows, concatenate non-empty `Field` and `Binding / Value` once. Reject a non-empty `Field` with blank or `—` Binding and use AskUserQuestion. A bare output such as `APIOutput1` is schema-discovered, not SDD-authored.

```markdown
<!-- INVALID: leaked the SDD Field placeholder and invented an extra operator -->
- — = literalResult = "literal-assigned"

<!-- INVALID: bare auto-mint is schema-discovered, not SDD-authored -->
| APIOutput1 | string | — |

<!-- VALID -->
- literalResult = "literal-assigned"
```

Before writing `data.outputs[]`, reject SDD Outputs rows lacking `->` or `=`, and projected items whose first token is `—`, `->`, or `=`. Every SDD-projected item must match `<field-path> -> <case-variable>` or `<case-variable> = <expression>`; reserve `<top-level-field>` for schema-discovered items.

### SDD Inputs table to caseplan projection (mandatory)

The SDD Inputs table has `Field`, `Type`, and `Binding`; drop `Type`. Project each row as `<Field> <- <Binding>` or `<Field> = <Binding>`, using the Binding-cell operator per [Input/Output Notation](#inputoutput-notation):

- `APIInput1`, `string`, `"literal-seed"` → `APIInput1 = "literal-seed"`
- `APIInput1`, `string`, `=vars.caseInput` → `APIInput1 = =vars.caseInput`
- `APIInput1`, `string`, `<- "Binding Matrix"."Echo literal".APIOutput1` → `APIInput1 <- "Binding Matrix"."Echo literal".APIOutput1`

Binding cells are Markdown code spans (`` `=vars.caseInput` ``, `` `<- "Stage"."Task".out` ``): unwrap them and copy their contents verbatim. Never re-wrap them, add quotes, use `:`, or retain backticks; preserve existing quotes. Apply the same rule to `input.value` in `caseplan.case`; a backtick or quote absent from the SDD cell must not reach JSON.

```markdown
<!-- INVALID: leaked the SDD Type column as a literal pipe segment -->
- APIInput1 | string | <- "Binding Matrix"."Echo literal".APIOutput1

<!-- INVALID: re-quoted the code-span cell and replaced the operator with `:` -->
- APIInput1: '<- "Binding Matrix"."Echo literal".APIOutput1'

<!-- INVALID: kept the SDD cell's backticks -->
- APIInput1 <- `"Binding Matrix"."Echo literal".APIOutput1`

<!-- VALID -->
- APIInput1 <- "Binding Matrix"."Echo literal".APIOutput1
```

Before writing `data.inputs[]`, reject values wrapped in backticks or an unprovided quote pair, and items separating name and value with `:` rather than `<-` or `=`. Do not carry the SDD Type column into the caseplan.

## Discovering Input/Output Names

1. **SDD per-task tables** are primary: each task declares input/output names, types, and variable bindings.
2. Run `uip maestro case tasks describe --type <type> --id "<taskTypeId>" --output json` to validate SDD names and discover additional fields (for example, standard `Error` output). The SDD per-task Outputs table uses two operators per v1 contract (see the case SDD template (`uipath-planner`) Section 2):
   - **`->` extract:** `<sdd-field-path> -> <case variable>`. The left side is the full runtime path relative to the task root; the right side is the target case variable, which MUST exist in the Case Variables table. Emit the source as `"=<sdd-field-path>"` verbatim; never infer, add, remove, or alter envelope prefixes. The target becomes `var` / `value` on `task.data.outputs[]`; allocate `id` / `originalVar` / `target` independently from the source leaf and global collision pool.

   ```markdown
   - outputs:
     - response.status        -> sendStatus    # connector payload field → vars.sendStatus
     - response.message.ts    -> messageTs     # nested connector field  → vars.messageTs
     - Error                  -> error         # top-level error (connector or action) → vars.error
     - Error.code             -> errorCode     # nested error sub-field   → vars.errorCode
     - Action                 -> userDecision  # action task's top-level output → vars.userDecision
   ```

   - Equal-name extracts remain extracts: `greeting -> greeting` keeps the arrow, points `var` / `value` to the existing Case variable, and emits `originalVar`. If the only collision is the matching root companion, source-side `id`, `originalVar`, and `target` remain `greeting`; an unrelated task/trigger/rule owner forces normal allocation (`greeting2`, `greeting3`, ...).
   - **`=` set/compute/copy:** `<case variable> = <expression>`. The target MUST already exist in Case Variables. Expressions may be a plain literal string/number/bool, `=js:` computation, or `=vars.X.Y` reference. **For `=` rows only, the emitted JSON carries `"target": ""` and `"body": ""` as present keys** — an empty value is not a reason to omit the key. This blank form is specific to `=`; `->` and bare outputs carry a real `target` (`"=<id>"`) and a real `value`, and must not be blanked. Full shape: [`impl-json.md` § Scenario E](impl-json.md).

   ```markdown
   - outputs:
     - caseStatus  = "InReview"                            # literal
     - reviewCount = =js:vars.reviewCount + 1              # computed expression
     - summary     = =vars.response.message.text           # copy from another variable's sub-field
   ```

   **Dot-path support** on the left side of `->`: full paths like `response.message.ts`, `response.data.user.email`, `Error.code` are emitted as-is. The first segment selects the top-level schema output; implementation then walks that output's nested schema one segment at a time and takes the emitted **`name` and `type` from the final leaf — never from the top-level parent, and never the dotted path itself**. `Error.Message -> errorMessage` emits `name: "Message"` (the leaf's display name, else its exact final segment) and the leaf's `type`; `name: "Error.Message"` and the parent's `type: "jsonSchema"` are both wrong. Full shape and worked example: [`impl-json.md` § Nested extract example](impl-json.md). A nested row references its top-level parent, so `Error.Message -> errorMessage` does NOT also auto-mint a bare `Error` output unless schema discovery independently adds `Error` as a bare output. Array indexing (`items[0]`) is NOT supported in v1 — fall back to consuming the array variable and using `=js:` expressions downstream.

   **Schema-discovered bare outputs** (no SDD row): emit an auto-mint item for a **top-level** Step 0 schema entry that the SDD does not bind (e.g., `Error` or a pre-expanded shortcut like Slack's `ts`). `id = var = value = camelCase(entry name)`. Source is the entry's pre-populated value verbatim. Never obtain this form from an SDD Outputs row. For non-top-level fields, require the SDD `->` operator with the full path instead.
   ```markdown
   - outputs:
     - Error            # bare — references top-level Error entry; produces vars.error (source = entry's =Error)
   ```

3. **Unresolved taskTypeId** — `tasks describe` unavailable. Follow [placeholder-tasks](../../../placeholder-tasks.md) — write no `data.inputs[]` / `data.outputs[]`, and capture wiring intent in the entry's `wiringNotes` in `registry-resolved.json`.

Do not fabricate names not in the SDD or `tasks describe`. Validation of variable existence happens at planning time (Phase 1) for `=` rows (target must exist in Case Variables); at implementation time (Phase 3) for `->` rows (deferred to io-binding validator).

> **The SDD carries natural form; impl applies the per-sink canonical wrap.** Values in the canonical form use the natural prefix notation shown above — `=vars.X`, `=metadata.X`, `=bindings.X`, cross-task `<-`. The implementation step rewrites each value to its canonical sink form when constructing `caseplan.case` (e.g., `=js:(vars.X)` for connector body fields, `=js:metadata.X` for `=metadata` references in any sink that runs the JS evaluator). Full rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## I/O table validation rules

Apply at planning time (Phase 1). The first two rules cover Inputs; the rest cover Outputs:

| Rule | Severity | Detail |
|---|---|---|
| A projected input item wraps its value in backticks or quotes the SDD `Binding` cell did not contain | ERROR | The SDD cell is a Markdown code span. Unwrap it and copy the contents verbatim. |
| A projected input item separates name from value with `:` | ERROR | The separator is the operator itself — `<-` for a cross-task reference, `=` otherwise. |
| `->` row's target case variable not in Case Variables table | ERROR | Outputs declare bindings, not new variables. Target must pre-exist. |
| `=` row's target case variable not in Case Variables table | ERROR | Same — `=` writes to existing variable's slot. |
| `->` row missing left-side Field | ERROR | `->` requires a schema field name on the left. |
| `=` row has a non-empty Field column | ERROR | `=` rows have `—` (no field), since the source is the right-side expression, not a schema field. |
| SDD row has a non-empty Field and blank / `—` Binding | ERROR | Bare output is not SDD syntax. AskUserQuestion; schema discovery may independently add the field as a bare auto-mint output. |
| A projected output item starts with `—`, `->`, or `=` | ERROR | An SDD table placeholder or operator leaked into the left operand. Re-project the row using the mandatory table in [§ SDD Outputs table to caseplan projection](#sdd-outputs-table-to-caseplan-projection-mandatory). |
| Per task: same target case variable appears in multiple Outputs rows | ERROR | No double-binding; one row per target var per task. Last-writer-wins is a runtime footgun. |
| Any SDD Outputs row differs from its projected item in operator or operand | ERROR | The projection is lossy. Restore the exact SDD row before approval; this includes equal-name `field -> field`. |

## Scoping

| Task location | Can reference |
|---|---|
| Regular stage task | Earlier stages + same stage earlier tasks + root variables |
| Secondary stage task | ALL tasks across ALL stages |
| Adhoc task | ALL tasks |

<!-- END: planning.md -->
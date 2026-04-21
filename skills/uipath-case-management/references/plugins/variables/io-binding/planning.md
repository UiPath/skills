# I/O Binding — Planning

Trust the SDD. Emit inputs/outputs exactly as declared. There is no `caseplan.json` yet — all validation happens during [implementation](impl.md).

## Discovering Input/Output Names

1. **SDD per-task tables** — primary source. Each task lists input/output field names, types, and variable bindings.
2. **`uip case tasks describe --type <type> --id "<taskTypeId>" --output json`** — validates SDD names and discovers additional fields (e.g., standard `Error` output). When SDD names differ from `tasks describe`, note the mapping:
   ```markdown
   - inputs:
     - in_Amount = "=vars.amount"   # SDD calls this "amount", process arg is "in_Amount"
   ```
3. **Unresolved taskTypeId** — `tasks describe` unavailable. Follow [skeleton-tasks](../../../skeleton-tasks.md) — omit `inputs:`/`outputs:`, capture wiring intent in a fenced code block.

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

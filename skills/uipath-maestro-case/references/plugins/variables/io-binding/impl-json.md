# I/O Binding — Implementation

> **Phase split.** Phase 3 only (Step 9.8). Phase 2 writes task shape (schema with empty `value` fields) but does not bind values. See [`../../../phased-execution.md`](../../../phased-execution.md).

Wire task inputs by editing `caseplan.json` directly. Runs after all tasks are created and enriched (Step 9) and after global variable + output wiring is complete.

## Task Input Shape

`task.data.inputs[]` — binding = setting `value`:

```json
{ "name": "in_CustomerId", "type": "string",
  "id": "vA1b2C3d4", "var": "vA1b2C3d4",
  "elementId": "Stage_verify-tKYC001",
  "value": "=vars.customerId" }
```

Inputs are populated with empty `value` from the `tasks describe` schema when `data.context.taskTypeId` is set during the task plugin's impl-json write. Input IDs are random (`v` + 8 chars).

## Task Output Shape

`task.data.outputs[]` — read-only, set at enrichment:

```json
{ "name": "KycResult", "type": "string",
  "id": "kycResult", "var": "kycResult", "value": "kycResult",
  "source": "=KycResult", "target": "=kycResult",
  "elementId": "Stage_verify-tKYC001" }
```

Output IDs are name-based camelCase per [uniqueness rule](../global-vars/impl-json.md#uniqueness-rule). `source` reads from the task response — never changes even when `var` is counter-suffixed.

## Binding Procedure

For each task input in `tasks.md`:

**Literals/expressions** — write the value string directly to `input.value`:
```
"=vars.amount"  |  "=metadata.ExternalId"  |  "50"  |  "=js:new Date()"
```

**Cross-task references** (`input <- "Stage A"."Task X".outputName`) — resolve first:

1. Find Stage A by `data.label`, Task X by `displayName`
2. Find output by `name` in `task.data.outputs[]`, read its `var` field
3. Write `=vars.<var>` to target input's `value`

```text
# pseudocode — not executed. Realize via Read → reason → Write/Edit.
src_output = find_output_by_name(src_task, "outputName")
target_input["value"] = f"=vars.{src_output['var']}"
```

After all bindings, verify every bound input has a non-empty `value` and every `=vars.X` resolves to an existing ID in: any task `data.outputs[].var`, `root.data.uipath.variables.inputOutputs[].id`, or `root.data.uipath.variables.inputs[].id`.

## Connector Tasks

Connector task input values are written during Step 9.7 (connector detail), not during this I/O binding step. Resolve cross-task `var` IDs before constructing the `input-values` body from `tasks.md`:

```json
{ "body": { "email": "=vars.employeeEmail", "caseRef": "=metadata.ExternalId" } }
```

Use `=js:()` only for expressions with operators (e.g., `=js:(vars.amount > 5000)`). See [connector-activity/impl-json.md](../../../plugins/tasks/connector-activity/impl-json.md).

## End-to-End: Task A Output → Task B Input

"Validate Expense Data" produces `validationResult`, consumed by "Enrich Employee Details":

```json
// 1. Task A output (auto-enriched) — Stage "Submission", task.data.outputs[]
{ "name": "ValidationResult", "var": "validationResult", "id": "validationResult",
  "value": "validationResult", "source": "=ValidationResult", "target": "=validationResult",
  "type": "string", "elementId": "Stage_submit-tValidate01" }

// 2. Task B input after binding — value set to =vars.<output.var>
{ "name": "in_ValidationResult", "value": "=vars.validationResult",
  "type": "string", "id": "vXr9pQ2mK", "var": "vXr9pQ2mK",
  "elementId": "Stage_submit-tEnrich02" }
```

Two things must exist: output on Task A with a `var` field, and bound input on Task B referencing `=vars.<var>`. Root `inputOutputs` companion entries for task outputs are optional — see [global-vars/impl-json.md § Task Output → inputOutputs Wiring](../global-vars/impl-json.md#task-output--inputoutputs-wiring).

## Error Handling

All issues go to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md). No fuzzy matching, no auto-creation, no retries.

| Check | Severity | Action |
|---|---|---|
| Skeleton task (no `data.inputs[]`) | `SKIPPED` | Skip all bindings |
| Input name not found (exact match) | `ERROR` | Skip binding — log available inputs |
| Source output not found (exact match) | `ERROR` | Skip binding — log available outputs |
| `=vars.X` not in any task `outputs[]` or root `inputOutputs[]` | `ERROR` | Skip binding |
| Type mismatch (input vs variable) | `WARNING` | Proceed |

Example log entry (pseudocode — record in-reasoning, not via subprocess):

```text
# pseudocode — not executed
issues.append({"severity": "ERROR", "step": "9", "plugin": "io-binding",
    "message": f'input "{name}" not found on task "{task}" — available: {available}',
    "context": {"task": task, "stage": stage, "input": name, "available": available}})
```

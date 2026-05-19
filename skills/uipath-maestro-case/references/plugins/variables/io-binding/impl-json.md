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

After all bindings, run the end-of-Phase-3 validator. It performs three cross-reference checks:

### Check 1 — `=vars.X` reference resolution

Verify every bound input has a non-empty `value`, and every `=vars.X` reference resolves to an existing entry in one of:
- Any task `data.outputs[].id` (the resolver match key; mirrors `var` under skill convention)
- Variables `inputOutputs[].id`
- Variables `inputs[].id`

Variables array path is schema-dependent — `root.data.uipath.variables.{inputOutputs,inputs}[].id` in v19, top-level `variables.{inputOutputs,inputs}[].id` in v20 (Rule 18).

> **Scan key:** match by `.id`, NOT `.var`. The runtime resolver matches on `Variable.id` (`VariablesService.findVariableByVariableId`). Under the skill convention `id === var` on self-declaring outputs, scanning by `.var` is harmless in practice, but `.id` is symmetric with the resolver.

Also scan `=vars.X` references in:
- Edge guard expressions (`edges[].data.conditionExpression`)
- Entry / exit condition expressions (stage and task)
- SLA expressions
- `=js:` expressions anywhere they appear

Same resolution rule applies — these are read-side consumers of the variable namespace.

### Check 2 — Out-arg producer presence (Q10 Option II)

For every entry in `root.data.uipath.variables.outputs[]` (formal Out-arg entries), the entry's `var` field is a POINTER to the variable slot that should hold the value at case end. Per the revised Q10b (always emit companion), the companion in `root.inputOutputs[]` is always present; its `default` field is empty when SDD didn't declare a Default.

**The check:** can the Out-arg's slot be populated at runtime? Three populating mechanisms exist:

1. **Companion default** — non-empty `default` field on the companion → always-populated fallback.
2. **Extraction producer** — a task's `outputs: <field> -> <var>` row (extract response field into the Out-arg slot).
3. **Assignment producer** — a task's `outputs: <var> = <expr>` row (`=` operator: set/compute/copy a literal or expression into the Out-arg slot).
4. **Bare-name producer** — a task's `outputs: <var>` row where the bare name matches the Out-arg's var (camelCase of schema field name).

If none of these exist → **pure orphan**, prompt the author.

| Producer status | Validate time action |
|---|---|
| Companion has non-empty `default` | OK — Out-arg always has a value. |
| At least one producer (extraction, assignment, or bare-name) exists in tasks.md AND its task is resolved (not Rule 17 placeholder) | OK — producer wires the slot when its task fires. |
| Producer declared but its task is a Rule 17 placeholder (declared-but-unwirable) | **Silent WARN.** Log to `tasks/build-issues.md` under `## Open Items for User`. Rule 17 already prompted the author for this task. |
| NO producer anywhere AND companion default empty | **AskUserQuestion** — pure orphan. 4 options below. |

Pseudocode:

```text
for entry in root.outputs[]:
  var = entry.var
  case_var_row = tasks_md_row_for_out_arg(name=entry.name)
  has_companion_default = (case_var_row.default not empty)

  # Producer scan — three patterns. All operate on tasks.md `outputs:` lines:
  has_extraction_producer  = exists in tasks.md any task's T-entry with an `outputs:` line containing `<field> -> <var>` (where var matches the Out-arg's var)
  has_assignment_producer  = exists in tasks.md any task's T-entry with an `outputs:` line containing `<var> = <expression>` (where var matches the Out-arg's var)
  has_bare_name_producer   = exists in tasks.md any task's T-entry with an `outputs:` line `- <name>` (bare, no operator) where camelCase(name) == var
  has_any_producer         = has_extraction_producer || has_assignment_producer || has_bare_name_producer

  producer_task_unresolved = the tasks.md-declared producer task is a Rule 17 placeholder (look up the task in caseplan.json by displayName; check `node.data.uipath` is empty `{}`)

  if has_companion_default:
      # Companion default guarantees a value; producer is optional bonus
      OK
  elif has_any_producer and producer_task_unresolved:
      # Declared producer but task is unresolvable — Rule 17 already prompted; just log
      LOG_OPEN_ITEM("Out-arg with declared but unresolvable producer — runtime returns empty until producer is wired")
  elif not has_any_producer:
      # Pure orphan — author never declared a producer AND no Default. Ask.
      AskUserQuestion("pure orphan", options=(a, b, c, d))
```

**On AskUserQuestion ("pure orphan" branch):**

```
Out-argument "<name>" (id <random>, var <var>) has no value source:
  SDD row Default: <"" (empty)>
  Companion root.inputOutputs[].id="<var>": exists, default=""
  Producing task in tasks.md (extraction or assignment): none found

Pick one:
  (a) Add producer task output — supply the producer task's **display name** as shown in tasks.md (e.g., `Send Slack Message`). If the named task doesn't exist, re-prompt. Skill appends `<field> -> <var>` to that task's Outputs.
  (b) Add a Default value to the SDD Case Variables row — supply value inline (literal string).
  (c) Recategorize as Variable (case-internal state) or remove the variable.
  (d) Continue with best-effort emit (case builds; runtime returns empty string for this Out-arg; entry logged under "Open Items for User" in build-issues.md).
```

**Skill response per user pick:**

- **(a)** Edit `tasks.md`: append `outputs: <field> -> <var-name>` to the named task's T-entry (use spec-derived field name if available, else `<UNKNOWN>` placeholder). Re-run Phase 1 dispatcher from the modified tasks.md, then retry Step 12.
- **(b)** Edit `tasks.md`: set `default: "<value>"` on the Out-arg's T-entry. Re-run Phase 1 dispatcher, then retry Step 12.
- **(c)** Prompt the user inline: `Recategorize as "Variable" or "Remove" the variable?` On `Variable`: edit `tasks.md` Case Variables row Category → Variable, re-run Phase 1 dispatcher, retry Step 12. On `Remove`: delete the row from `tasks.md`, re-run Phase 1 dispatcher, retry Step 12.
- **(d)** Append the build-issues entry (template below) and continue to Phase 4. No re-run.

Option (d) is the build-with-best escape for cases where the author intends to wire the producer later but wants to keep iterating now — equivalent to the silent-WARN treatment that declared-but-unresolvable producers (T20-style) get automatically.

**Rationale for the split:** real-world authoring is iterative. When an author has already gone through a Rule 17 prompt for the producer task (T20-style), the skill should not pile a second prompt on top — that's the path the author already chose by picking "Skip". But when the author authored a *pure orphan* with no producer declared at all (T14-style — wait-for-timer with no aliasing wire AND no Default), there's no prior signal of intent; the AskUserQuestion is the right surface to ask "did you mean to forget this, or wire it now?" Option (d) preserves the build-with-best escape.

**Build-issues entry template** (both branches log to this, only the AskUserQuestion branch ALSO prompts):

```markdown
## Open Items for User

- **[Q10 II — Out-arg `<name>` has no value source]** — The Out-argument `<name>` (id `<random>`, var `<var>`) is declared in `variables.outputs[]` but {no producer wired AND no Default}. Runtime will return empty string for this Out-argument unless one of:
  - Add a `<field> -> <name>` row to a task's Outputs that produces this value (extraction)
  - Add a `<name> = <expression>` row to a task's Outputs (assignment from literal / computed / variable reference)
  - Add a Default value to the SDD Case Variables row
  - Recategorize the variable as `Variable` or remove it
```

See [implementation.md § Step 12 — End-of-Phase-3 validator pass](../../../implementation.md) for invocation.

### Check 3 — Type mismatch warnings

Where a `=vars.X` reference resolves to a declaration with a different `type` than the consuming input expects, log WARNING. Proceed (string coercion is common and runtime-tolerant).

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
| Placeholder task (no `data.inputs[]`) | `SKIPPED` | Skip all bindings |
| Input name not found (exact match) | `ERROR` | Skip binding — log available inputs |
| Source output not found (exact match) | `ERROR` | Skip binding — log available outputs |
| `=vars.X` not in any task `outputs[].id` or root `inputOutputs[].id` / `inputs[].id` | `ERROR` | Skip binding |
| Out-arg formal entry's `var` doesn't match any task `outputs[].id` AND companion has no `default` | `ERROR` | Log Out-arg producer issue (Check 2 above); AskUserQuestion |
| Type mismatch (input vs variable) | `WARNING` | Proceed |

Example log entry (pseudocode — record in-reasoning, not via subprocess):

```text
# pseudocode — not executed
issues.append({"severity": "ERROR", "step": "9", "plugin": "io-binding",
    "message": f'input "{name}" not found on task "{task}" — available: {available}',
    "context": {"task": task, "stage": stage, "input": name, "available": available}})
```

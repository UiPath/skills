# I/O Binding — Implementation

> **Phase split.** Phase 3 only. Input/output binding at Step 9.8; in-expression `vars.$xref` marker resolution at Step 11.5 (after conditions + SLA). Phase 2 writes task shape (schema with empty `value` fields) but does not bind values. See [`../../../phased-execution.md`](../../../phased-execution.md).

Wire task inputs by editing `caseplan.json` directly. Runs after all tasks are created and enriched (Step 9) and after global variable + output wiring is complete.

## Task Input Shape

`task.data.inputs[]` — binding = setting `value`:

```json
{ "name": "in_CustomerId", "type": "string",
  "id": "vA1b2C3d4", "var": "vA1b2C3d4",
  "elementId": "Stage_verify-tKYC001",
  "value": "=vars.customerId" }
```

Inputs are populated with empty `value` from the `tasks describe` schema when the task's `data.inputs[]` are written during the task plugin's impl-json write. Input IDs are random (`v` + 8 chars) — letter-leading, same convention as variable formal slots ([global-vars § Formal-arg slot ID format](../global-vars/impl-json.md#formal-arg-slot-id-format)).

## Task Output Shape

`task.data.outputs[]` — read-only, set at enrichment:

```json
{ "name": "KycResult", "type": "string",
  "id": "kycResult", "var": "kycResult", "value": "kycResult",
  "source": "=KycResult", "target": "=kycResult",
  "elementId": "Stage_verify-tKYC001" }
```

Output IDs are name-based camelCase per [uniqueness rule](../global-vars/impl-json.md#uniqueness-rule). `source` reads from the task response — never changes even when `var` is counter-suffixed.

## Output Binding Shapes

If every task/rule output is an ordinary current schema/spec output, preserve the [Task Output Shape](#task-output-shape), apply the global allocator, and copy every descriptor-defined type-refining attribute — especially `options` — verbatim onto its output; do not load projection guidance. Descriptor attributes do not apply to computed/literal `=` custom assignments. If any output uses `->`, `=`, reassignment, or needs a root companion, read [Output Projection](../global-vars/output-projection-guide.md) before the owner writes its output array.

## Output Binding Shapes for Connector Condition Rules

After a condition owner upgrades a resolved connector rule, preserve ordinary spec outputs without loading projection guidance. If a rule output uses `->`, `=`, reassignment, or needs a root companion, read [Output Projection — Task and rule ownership](../global-vars/output-projection-guide.md#task-and-rule-ownership) before the owner's final output-dispatch step; an unresolved stub is skipped.

## Binding Procedure

### Output reference ID (authoritative)

Both whole-value `<-` and in-expression `$xref` resolve through the same runtime variable ID:

```text
# pseudocode — not executed. Realize via Read → reason → Write/Edit.
resolve_output_reference_id(caseplan, src_output):
    if src_output["id"] is a non-empty string:
        return src_output["id"]
    if src_output["custom"] is true and src_output["var"] is a non-empty string:
        companion = exactly one variables.inputOutputs[] entry where
                    id == src_output["var"] and elementId == "root"
        if companion exists:
            return companion["id"]
    ERROR — the output has no runtime-resolvable ID
```

Normal, bare, and reassigned outputs use their own `.id`. This is load-bearing when reassignment collision handling produces `id: "estimatedAge2"` with `var: "estimatedAge"`: downstream references must use `=vars.estimatedAge2`. Only a custom `=` output intentionally lacks `.id`; its `.var` points to an existing Case-variable companion, so resolve through that companion's verified `.id`. Never use a reassigned output's `.var` as its source reference ID.

For each task input in `tasks.md`:

**Literals/expressions** — write the value string directly to `input.value`. Values shown are POST-rewrite — impl translates `=metadata.X` from `tasks.md` to `=js:metadata.X` per the [canonical-form table](../../../bindings-and-expressions.md#canonical-form-per-sink) (plain `=metadata.X` is not resolved by the lookup-path evaluator):
```
"=vars.amount"  |  "=js:metadata.ExternalId"  |  "50"  |  "=js:new Date()"
```

**Cross-task references** (`input <- "Stage A"."Task X".outputName`) — resolve first:

1. Find Stage A by `data.label`, Task X by `displayName`
2. Find output by `name` in `task.data.outputs[]`
3. Resolve its output reference ID using the authoritative algorithm above
4. Write `=vars.<outputReferenceId>` to target input's `value`

```text
# pseudocode — not executed. Realize via Read → reason → Write/Edit.
src_output = find_output_by_name(src_task, "outputName")
output_reference_id = resolve_output_reference_id(caseplan, src_output)
target_input["value"] = f"=vars.{output_reference_id}"
```

## In-Expression Marker Resolution (Step 11.5)

Whole-value `<-` (above) only resolves an input whose value IS the reference. To reference an upstream output from **inside** a `=js:` expression (composite payload, `conditionExpression`, SLA `expression`, computed `=` output, connector body field), the SDD embeds a `vars.$xref('Stage','Task','output')` marker — see [bindings-and-expressions.md § In-expression references](../../../bindings-and-expressions.md#in-expression-references-varsxref). Resolve all markers in **one pass over the whole `caseplan.json`** at **Step 11.5** — after conditions (Step 10) and SLA (Step 11) are written, and every task/trigger/rule output is minted and deduped (so the marker resolves to the final output reference ID). This is the LAST mutation of Phase 3 before the validator; running it earlier (e.g. right after Step 9.8 input binding) misses markers in conditions / SLA and reads pre-dedup IDs.

This single sink-blind pass replaces per-sink resolution: it walks every string value regardless of which sink holds it, so conditions, SLA, inputs, and connector bodies are all covered in one place.

```text
# pseudocode — not executed. Realize via Read → reason → Write/Edit.
TOKEN = /vars\.\$xref\('([^']+)','([^']+)','([^']+)'\)/   # global, all matches

for each string value V anywhere in caseplan.json:
    for each match (stageLabel, taskName, outputName) of TOKEN in V:
        src_stage  = find_node_by_label(nodes, stageLabel)        # data.label
        src_task   = find_task_by_name(src_stage, taskName)       # displayName
        src_output = find_output_by_name(src_task, outputName)    # data.outputs[].name
        if any lookup fails: leave token unsubstituted — Check 4 (validator) surfaces it via AskUserQuestion
        output_reference_id = resolve_output_reference_id(caseplan, src_output)
        if ID resolution fails: leave token unsubstituted — Check 4 surfaces it
        replace the matched token with "vars." + output_reference_id  # bare, no leading "="
    write V back
```

Resolution semantics are identical to whole-value `<-` (same name-triple and output-reference-ID algorithm), with two differences: the substitution is **bare** `vars.<outputReferenceId>` (the marker already sits inside `=js:`), and it happens in a global string pass rather than against a single input's `value`. Secondary-stage / adhoc scoping (reference any task across any stage) applies unchanged.

After this pass and all bindings, Phase 3 exit validation begins. Read [I/O Binding Exit Validation](validation-guide.md) and run Checks 1–5 before entering Phase 4. Do not load that guide while ordinary binding or the Step 11.5 pass is still in progress.

### Check 1 — `=vars.X` reference resolution

Compatibility route: at Phase 3 exit, run [Check 1](validation-guide.md#check-1--varsx-reference-resolution) against the complete runtime reference pool.

### Check 1.5 — Custom-output metadata expressions are canonical

Compatibility route: run [Check 1.5](validation-guide.md#check-15--custom-output-metadata-expressions).

### Check 2 — Out-arg producer presence

Compatibility route: run [Check 2](validation-guide.md#check-2--out-arg-producer-presence) against declared and emitted task, trigger, and connector-rule producers.

### Check 3 — Type and descriptor fidelity

Compatibility route: run [Check 3](validation-guide.md#check-3--type-and-descriptor-fidelity) against each selected owner's current descriptor.

### Check 4 — No surviving `$xref` markers

Compatibility route: after Step 11.5, run [Check 4](validation-guide.md#check-4--no-surviving-xref-markers) over the whole artifact.

### Check 5 — Resolved-resource I/O completeness

Compatibility route: run [Check 5](validation-guide.md#check-5--resolved-resource-io-completeness) for every resolved owner against its exact current descriptor/spec contract.

## Connector Tasks

Connector task input values are written during Step 9.7 (connector detail), not during this I/O binding step. Resolve cross-task output reference IDs with the authoritative algorithm above before constructing the `input-values` body from `tasks.md`, then apply the canonical wrap per sink:

```json
{ "body": { "email": "=js:(vars.employeeEmail)", "caseRef": "=js:(metadata.ExternalId)" } }
```

**Connector body sinks require `=js:(...)` wrap for ALL references** — `=vars.X`, `=metadata.X`, `=bindings.X`, and operator expressions (e.g. `=js:(vars.amount > 5000)`). The runtime only evaluates `=js:` prefixed strings inside connector body fields; plain prefix forms arrive at the API as literal strings (silent runtime fault). Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

See [connector-activity/impl-json.md](../../../plugins/tasks/connector-activity/impl-json.md) for the connector body write path.

## End-to-End: Task A Output → Task B Input

"Validate Expense Data" produces `validationResult`, consumed by "Enrich Employee Details":

```json
// 1. Task A output (auto-enriched) — Stage "Submission", task.data.outputs[]
{ "name": "ValidationResult", "var": "validationResult", "id": "validationResult",
  "value": "validationResult", "source": "=ValidationResult", "target": "=validationResult",
  "type": "string", "elementId": "Stage_submit-tValidate01" }

// 2. Task B input after binding — value set to =vars.<output.id>
{ "name": "in_ValidationResult", "value": "=vars.validationResult",
  "type": "string", "id": "vXr9pQ2mK", "var": "vXr9pQ2mK",
  "elementId": "Stage_submit-tEnrich02" }
```

Two things must exist: output on Task A with a runtime-resolvable reference ID, and bound input on Task B referencing `=vars.<outputReferenceId>`. Root `inputOutputs` companion entries for case Variables produced via `->` are also written for picker visibility — see [global-vars/impl-json.md § Task Output → variable resolution](../global-vars/impl-json.md#task-output--variable-resolution).

## Error Handling

Ordinary binding issues go to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md). No fuzzy matching or auto-creation.

| Check | Severity | Action |
|---|---|---|
| Placeholder task (no `data.inputs[]`) | `SKIPPED` | Skip all bindings |
| Placeholder connector rule (no `rule.uipath.outputs[]`) | `SKIPPED` | Skip rule output bindings (nothing minted) |
| Input name not found (exact match) | `ERROR` | Skip binding — log available inputs |
| Source output not found (exact match) | `ERROR` | Skip binding — log available outputs |

Phase-exit severities, bounded retries, user choices, and Open Items for Checks 1–5 are owned only by [I/O Binding Exit Validation](validation-guide.md#remediation-decision-table).

Example log entry (pseudocode — record in-reasoning, not via subprocess):

```text
# pseudocode — not executed
issues.append({"severity": "ERROR", "step": "9", "plugin": "io-binding",
    "message": f'input "{name}" not found on task "{task}" — available: {available}',
    "context": {"task": task, "stage": stage, "input": name, "available": available}})
```

<!-- END: impl-json.md -->

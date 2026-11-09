# I/O Binding — Implementation

> **Phase split.** Phase 3 only. Bind I/O at Step 9.8; resolve in-expression `vars.$xref` markers at Step 11.5 (after conditions + SLA). Phase 2 writes task shape (schema with empty `value` fields), but does not bind values. See [`../../../phased-execution.md`](../../../phased-execution.md).

Wire `caseplan.case` after all tasks are created/enriched (Step 9), global-variable wiring, and output wiring.

## Task Input Shape

Set `task.data.inputs[].value`. Schema-written inputs initially have empty `value`; IDs are random, letter-leading `v` + 8 chars, using [global-vars § Formal-arg slot ID format](../global-vars/impl-json.md#formal-arg-slot-id-format).

```json
{ "name": "in_CustomerId", "type": "string", "id": "vA1b2C3d4", "var": "vA1b2C3d4", "elementId": "Stage_verify-tKYC001", "value": "=vars.customerId" }
```

## Task Output Shape

`task.data.outputs[]` is read-only after enrichment. Output IDs are name-based camelCase under [global-vars § Uniqueness rule](../global-vars/impl-json.md#uniqueness-rule); `source` reads the task response and is unchanged by `var` suffixing. For every `->`, `originalVar` equals that entry’s allocated `id` (including collision suffixes and equal-name reassignment), never another output’s name. Retain minted `id`, set `var` to the case variable, repeat `id` in `originalVar` for FE root-mirroring filtering, and compare locally with the same entry’s `id`, not its schema name. Null/wrong `originalVar` is `CASE_MGMT_OUTPUT_ORIGINAL_VAR_MISSING`.

## Output Binding Shapes

Combine each plugin’s Step 0 schema (`tasks describe` for non-connectors; `case spec --input-details` `caseShape.outputs[]` for connectors) with SDD `->`/`=` rows and schema-discovered bare items. Bare is internal auto-minting, never an SDD Outputs operator. Apply during plugin task-write.

### Descriptor resolution

Resolve each `<sdd-field-path>` before selecting a shape:

1. Split on `.`; match the first segment exactly to a top-level Step 0 output, using `source` without leading `=` and falling back to `name`.
2. With no remainder use that descriptor; otherwise walk remaining segments through top-level `Body.Properties` (`body.properties` normalized; `JsonSchema.Properties` is the equivalent CLI mirror), ending at the leaf.
3. For nested paths, `name` is the leaf display name or exact final segment; copy `type` and type-refining attributes only from the leaf. Never copy a parent object’s `jsonSchema` type/body onto a scalar leaf.
4. A nested path references its top-level parent; do not auto-mint that parent unless a separate schema bare item exists. Connector nodes are exempt: `data.outputs[]` is a verbatim splice of `caseShape.outputs[]`, so every spec entry remains and nested rows bind into spliced `response` ([connector-trigger-impl.md § Write `context` / `inputs` / `outputs` from the spec-cache](../../../connector-trigger-impl.md#write-context--inputs--outputs-from-the-spec-cache)). Business-rule tasks always carry `output` (`=result`) and `Error`; `<decision>.<column>` is additional ([business-rule/impl-json.md](../../tasks/business-rule/impl-json.md)). If any segment fails, log `ERROR`, skip the binding, and never fall back to the last parent.

For each top-level Step 0 entry, schema auto-mint only when the SDD references neither it bare nor as the first `->` segment. On connectors this controls shape, not existence, because splicing fixes entries. `$xref('Stage','Task','output')` is neither form: auto-mint its named output and retain the additional `=` row.

### Shapes

- **`<sdd-field-path> -> <sdd-name>`:** Allocate `baseId = camelCase(leaf segment)` under [global-vars § Uniqueness rule](../global-vars/impl-json.md#uniqueness-rule), including controlled equal-name alias. Emit `{name: <resolved name>, type: <resolved leaf type>, id: <allocated id>, var: "<sdd-name>", originalVar: <allocated id>, value: "<sdd-name>", source: "=<sdd-field-path>", target: "=<allocated id>", elementId: "<stage-task>"}`. Top-level `name` is its display name; nested `name` is leaf display name or final segment. `source` is the verbatim SDD left side prefixed with `=`. `type` is required and for resource tasks comes from `uip maestro case splice --described` ([resource-task-common.md](../../tasks/resource-task-common.md)); never type by hand, except business-rule `<decision>.<column>`, whose type comes from the leaf ([business-rule/impl-json.md](../../tasks/business-rule/impl-json.md)). The parser retains a row only when `name`, `type`, `source`, and `var` exist; otherwise drop it before evaluation. Packaging may omit undefined `type`. `originalVar` mirrors `id` and preserves the case-variable companion through FE `mutateRootVariables` (`VariableMutationUtils.ts:135`).
- **Bare `<name>`:** Emit `{name, type: <Step 0 type>, id: <camelCase(name)>, var: <id>, value: <id>, source: <Step 0 source verbatim>, target: "=<id>", elementId}`; no `originalVar`. Use only unaliased top-level entries. Schema fields without SDD references use it; connectors also apply global uniqueness suffixing (for example `response` → `response2`).
- **`<sdd-name> = <expression>`:** Emit Scenario E `{name: "<sdd-name>", custom: true, var: "<sdd-name>", value: "<expression>", source: "<same as value>", target: "", body: "", type: <SDD Outputs Type>, elementId: "root"}`. Do not emit `id` or `originalVar`. `type` is the SDD row Type, never root case-variable type (`sdd convert` writes root `number` as `double`) or converter placeholder `string`. Only Scenario E has literal blank `target` and `body`; omitted keys differ. Its value is the expression and it produces no root mirror because FE `isUpdateExistingOutput` at `VariableMutationUtils.ts:49-64` skips it. Canonicalize `=metadata.X` to `=js:metadata.X` in `value` and `source`, retaining the SDD-natural form in the projected item. Strip SDD delimiter quotes from quoted literals (`status = "InReview"` yields `InReview`, not escaped quotes).

`=` values may be literals (`"InReview"`, `5`, `true`), computed (`=js:vars.x + 1`), or variable references (`=vars.X.Y.Z`). Dot paths in `->` work; array indexing is unsupported in v1. Every `->` and `=` target case variable MUST exist in the Case Variables table.

Never blank `target` or `value` on `->`/bare rows:

| shape | `target` | `value` | `body` |
|---|---|---|---|
| Scenario E (`=` custom) | `""` | expression | `""` |
| reassign (`->`) | `"=<allocated id>"` | SDD name | absent |
| bare auto-mint | `"=<id>"` | id | absent |

Carry every extra type-refining attribute, especially `options`, verbatim onto reassign, auto-mint, and connector-rule outputs. Nested extracts copy leaf attributes only; do not inherit parent `body`, `jsonSchema`, `options`, or `type`. Scenario E carries no schema `options`.

Apply [global uniqueness rule](../global-vars/impl-json.md#uniqueness-rule), including controlled equal-name alias, to every source-side `->` `id`; mirror allocated ID into `target` and `originalVar`, retain `source`, and keep `var` pointed at the existing target Case variable.

Emit an output before any same-task row whose expression reads its `var`, regardless of SDD order. `data.outputs` is sequential; otherwise the reader sees the case-variable default while `validate` may still report `Valid`. Typically emit schema auto-mint first and the `$xref`-driven `=` row last. `--strict` reports a violation as `STRICT_OUTPUT_FORWARD_READ`.

Extract IDs derive from field names, not `v` + 8 input/formal-slot IDs. Suffix only `id`, never `var`; tasks may share a case-variable `var` but each has a distinct `id`. Random IDs prevent collision handling and leave variables undeclared. Dispatch equal operands by operator first: `greeting -> greeting` is reassign, not bare. Without unrelated collision, `id`, `var`, `originalVar`, and `value` are `greeting`, `source: "=greeting"`, `target: "=greeting"`; allocator controls suffixing.

## Output Binding Shapes for Connector Condition Rules

Apply the same `->`, `=`, and schema-bare shapes to `wait-for-connector` condition rules in stage-entry, stage-exit, case-exit, and task-entry scopes, with these overrides:

| Aspect | Connector task | Connector condition rule |
|---|---|---|
| Target array | `task.data.outputs[]` | `rule.uipath.outputs[]` |
| Step 0 schema source | `tasks describe` / `case spec --input-details` `caseShape.outputs[]` | `case spec --type trigger --input-details` `caseShape.outputs[]` |
| `elementId` | `<stageId>-<taskId>` | `<ownerNodeId>-<ruleId>`; `<stageId>-<ruleId>` except case-exit `root-<ruleId>` |
| `->` root companion | Required, `elementId: "root"`, `custom: true` | Required, same shape |
| Scenario E | Permitted | Permitted for `caseVar = response.X`, literals, or expressions; no root mirror |

The [global pool](../global-vars/impl-json.md#uniqueness-rule) includes tasks, triggers, rules, and root; deduplicate their union. Each condition plugin invokes this dispatch as the LAST `wait-for-connector` recipe step, after writing `rule.uipath` (Step 5 of [connector-trigger-impl.md § Procedure](../../../connector-trigger-impl.md#procedure-phase-3)) and before root bindings (Step 6). Iterate SDD Outputs against already-minted `rule.uipath.outputs[]`, rewrite matches, then retain schema bare items. See the four condition `impl-json.md` files.

**Skip guard.** If `rule.uipath.outputs[]` is absent or empty because connector configuration is unresolved ([connector-trigger-impl.md § Placeholder fallback](../../../connector-trigger-impl.md#placeholder-fallback)), log `SKIPPED` and continue; the stub has `uipath` but nothing to bind.

**Runtime order (KNOWN ISSUE).** The backend evaluates the gateway before rule output extraction, so an in-rule gate sees the pre-extract case variable. Extract-then-gate on one rule does not work for event-payload conditioning. Put the case-state gate on downstream stage-entry/task-entry condition. Treat in-rule gates against extracted values as undefined behavior until verified; backend disposition is pending.

## Binding Procedure

### Output reference ID (authoritative)

Whole-value `<-` and in-expression `$xref` use the same runtime ID:

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

Normal, bare, and reassigned outputs use `.id`, including collision IDs such as `estimatedAge2`; references therefore use `=vars.estimatedAge2`, never reassigned `.var`. Only custom `=` outputs lack `.id`; resolve them through the verified root companion `.id`.

For each task input, write literal/expression values after rewrite to `input.value`; translate `=metadata.X` to `=js:metadata.X` per [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink); strip SDD delimiter quotes from quoted literals while embedded delimiters remain payload. The projected item keeps SDD cell quotes ([planning.md § code spans](planning.md)); `caseplan.case` does not.

For cross-task `input <- "Stage A"."Task X".outputName`, find stage by `data.label`, task by `displayName`, and output by exact `name`; resolve its ID authoritatively and write `=vars.<outputReferenceId>`. Do not fuzzy-match, create, or retry.

### In-Expression Marker Resolution (Step 11.5)

Whole-value `<-` handles an entire input value. At Step 11.5, after conditions (Step 10), SLA (Step 11), and all task/trigger/rule outputs are minted and deduped, resolve markers inside `=js:` expressions, composite payloads, `conditionExpression`, SLA `expression`, computed `=` outputs, connector body fields, and every other string in `caseplan.case`. This is the LAST Phase-3 mutation before validation; do not run it earlier than Step 9.8.

Walk every string and globally replace `/vars\.\$xref\('([^']+)','([^']+)','([^']+)'\)/` by finding `data.label`, `displayName`, and `data.outputs[].name`, then applying the authoritative ID resolver. Replace with bare `vars.<outputReferenceId>` (no leading `=` inside `=js:`). On lookup or ID failure, leave the token unchanged; Check 4 prompts. Secondary-stage and adhoc cross-stage scope is unchanged.

After bindings, run the end-of-Phase-3 validator:

### Check 1 — `=vars.X` reference resolution

Every bound input has non-empty `value`. Every `=vars.X` resolves by `.id`, not `.var`, to task `data.outputs[].id`, `variables.inputOutputs[].id`, or `variables.inputs[].id` (`variables.{inputOutputs,inputs}[].id`). Scan the same namespace in stage/task entry/exit conditions, case-exit and trigger rules, SLA expressions, and all `=js:` strings. Custom `=` outputs resolve through their root companion `.id`.

### Check 1.5 — Custom-output metadata expressions are canonical

For every `custom: true` output, reject `value` or `source` beginning with `=metadata.`; emit `=js:metadata.<field>` in both.

### Check 2 — Out-arg producer presence

For every `variables.outputs[]` formal Out-arg, `var` points to the end-of-case slot and its `variables.inputOutputs[]` companion is present; `default` is empty without an SDD Default. A source is a non-empty companion `default`; extraction `<field> -> <var>`; assignment `<var> = <expression>`; or schema bare output whose camelCase name equals `var`.

Accept a non-empty default. If a producer exists but its task is a Rule 18 placeholder (`node.data.inputs` is empty `{}`), silently WARN and log to `tasks/build-issues.md` under `## Open Items for User` (`LOG_OPEN_ITEM("Out-arg with declared but unresolvable producer — runtime returns empty until producer is wired")`); Rule 18 already prompted. If neither producer nor default exists, `AskUserQuestion` for pure orphan:

```text
Out-argument "<name>" (id v<random8>, var <var>) has no value source:
  SDD row Default: <"" (empty)>
  Companion root.inputOutputs[].id="<var>": exists, default=""
  Producing task in the SDD (extraction or assignment): none found

Pick one:
  (a) Add producer task output — supply the producer task's display name as shown in the SDD. If it does not exist, re-prompt; append <field> -> <var>.
  (b) Add a Default value to the SDD Case Variables row — supply a literal inline.
  (c) Recategorize as Variable (case-internal state) or remove the variable.
  (d) Continue with best-effort emit; case builds, runtime returns empty string, and log under "Open Items for User" in build-issues.md.
```

For (a), append to the named task’s Outputs using the spec-derived field or `<UNKNOWN>`, rerun Phase 1 from modified `sdd.md`, then retry Step 12. For (b), set Default, rerun Phase 1, retry Step 12. For (c), ask `Recategorize as "Variable" or "Remove" the variable?`; edit Category and rerun the Phase 1 dispatcher, or delete the row and rerun Phase 1, then retry Step 12. For (d), append the build issue and continue to Phase 4 without rerun.

### Check 3 — Type and descriptor fidelity

If an input expected type differs from the declaration resolved by `=vars.X`, log `WARNING` and proceed. For every `->`, re-resolve the complete source against Step 0; emitted `name` and `type` must equal exact resolved name and leaf type. Nested extracts must not separately auto-mint their parent unless a separate schema bare item exists; connector and business-rule tasks are exempt. A mismatch is `ERROR`: correct from the exact descriptor and rerun Check 3. `uip maestro case validate` is insufficient because it does not compare nested bindings to schema leaves.

### Check 4 — No surviving `$xref` markers

Scan every string for `$xref(`. Any survivor is an unresolved name triple or ID and receives the same interactive remediation as unresolved `=vars.X`, never a silent error; never ship `vars.$xref(...)` because it throws at runtime.

Present:

```text
In-expression reference $xref('<stage>','<task>','<output>') does not resolve:
  Stage  "<stage>":  <found | NOT FOUND>
  Task   "<task>":   <found | NOT FOUND in that stage>
  Output "<output>": NOT FOUND on task
  Available outputs on "<task>": <name, name, ...>
  Used in: <sink>

Pick one:
  (a) Name the intended output — supply the correct output or full Stage / Task / output triple.
  (b) Edit the SDD expression — the marker is one term in a larger =js: expression.
  (c) Continue with best-effort emit — leave token unsubstituted, build case, and log runtime failure.
```

For (a), rewrite the triple in `caseplan.case`, rerun [Step 11.5](#in-expression-marker-resolution-step-115) for that token, and rescan; re-prompt if needed. For (b), edit SDD, rerun Phase 1, then Step 11.5 and Check 4. For (c), leave token, append build issue, and continue to Phase 4 without rerun.

### Check 5 — Resolved-resource I/O completeness

For each resolved task, read its persisted contract from `tasks/registry-resolved.json` (per-input `name` and `required`, declared output-field list written at §Resolve). Skip tasks without a contract (Rule 18 placeholder or `<UNRESOLVED>`), as in Check 2.

```text
for task in caseplan.case tasks where contract = registry_resolved[task].contract is present:
    bound_inputs = { inp.name : inp.value for inp in task.data.inputs[] }
    for decl in contract.inputs where decl.required:
        v = bound_inputs.get(decl.name)
        if v is missing or v == "": ERROR → AskUserQuestion (unbound-required-input)
    declared_out = set(contract.outputs[].name)
    for out in task.data.outputs[]:
        leaf = top_level_segment(strip_leading_"=", out.source)
        if leaf not in declared_out: ERROR → AskUserQuestion (phantom-output-field)
```

Required inputs fed upstream pass with non-empty `=vars.<outputReferenceId>` or resolved `=js:`; do not require a §1.5 declaration.

For unbound required input, show task/resource and other required-input status, then ask: (a) bind from case variable, literal, or upstream `"Stage"."Task".out` and write Inputs row; (b) mark `<UNRESOLVED>`, append high review item `rev_unbound_input_<task>_<field>`, continue; or (c) best-effort, log Open Items, continue. For (a), write `sdd.md` and `caseplan.case`, run Step 9.8, retry Check 5.

For phantom output, show available resource outputs and ask: (a) choose available field and rewrite `source`/`Field`, retry Check 5; (b) delete row, allowing orphaned `=vars.<caseVar>` to reach Check 1; or (c) leave it, log Open Items, continue. Check 5 follows the build-with-best policy of Checks 1, 2, and 4; Phase 4 `validate` may remain green.

### Build-issues entries

Use `## Open Items for User` and retain these meanings:

```markdown
- **[Out-arg `<name>` has no value source]** — The Out-argument `<name>` is declared in `variables.outputs[]` but no producer wired AND no Default. Runtime will return empty string unless a `<field> -> <name>` extraction, `<name> = <expression>` assignment, Default, Variable recategorization, or removal is supplied.
- **[Unresolved `$xref` marker]** — `vars.$xref('<stage>','<task>','<output>')` in <sink> did not resolve. The `=js:` expression throws at runtime until fixed. Correct the source output name in the SDD and rebuild.
- **[Unbound required input]** — task "<task>" (resource "<resource>") input "<field>" is required but unbound; resolves to runtime null. Bind it in the SDD and rebuild.
- **[Phantom output field]** — task "<task>" extracts "<field>", which resource "<resource>" does not emit; resolves to runtime null. Correct the output name in the SDD and rebuild.
```

See [implementation.md § Step 12 — End-of-Phase-3 validator pass](../../../implementation.md) for invocation.

## Connector Tasks

Connector task input values are written during Step 9.7 (connector detail), not this binding step. Resolve cross-task IDs authoritatively before constructing `input-values`, then apply the canonical sink wrap:

```json
{ "body": { "email": "=js:(vars.employeeEmail)", "caseRef": "=js:(metadata.ExternalId)" } }
```

Connector body sinks require `=js:(...)` for ALL references: `=vars.X`, `=metadata.X`, `=bindings.X`, and operator expressions such as `=js:(vars.amount > 5000)`. Plain prefix forms arrive at the API as literal strings. See [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink) and [connector-activity/impl-json.md](../../../plugins/tasks/connector-activity/impl-json.md).

## Error Handling

Send all issues to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md). No fuzzy matching, auto-creation, or retries.

| Check | Severity | Action |
|---|---|---|
| Placeholder task (no `data.inputs[]`) | `SKIPPED` | Skip all bindings |
| Placeholder connector rule (no `rule.uipath.outputs[]`) | `SKIPPED` | Skip rule output bindings |
| Exact input name not found | `ERROR` | Skip binding; log available inputs |
| Exact source output not found | `ERROR` | Skip binding; log available outputs |
| `$xref(...)` name triple or ID fails (Step 11.5 / Check 4) | `ERROR` | Leave token; AskUserQuestion; log triple and available outputs |
| `=vars.X` absent from task output or root `inputOutputs`/`inputs` IDs | `ERROR` | Skip binding |
| Out-arg has no producer and no companion `default` | `ERROR` | Check 2 issue and AskUserQuestion |
| Required resolved-resource input lacks bound `value` | `ERROR` | Check 5 AskUserQuestion: bind / `<UNRESOLVED>` + review / best-effort |
| Extract Field absent from resolved contract | `ERROR` | Check 5 AskUserQuestion: re-point / drop / best-effort |
| Resolved task has no persisted contract | `SKIPPED` | Skip Check 5 |
| Input/variable type mismatch | `WARNING` | Proceed |
| Extract `name`/`type` differs from exact descriptor | `ERROR` | Correct and rerun Check 3 |
| Nested extract auto-mints undeclared parent on non-connector/non-business-rule task | `ERROR` | Remove parent and rerun Check 3 |

Log in reasoning rather than subprocess with the shared structure:

```text
issues.append({"severity": "ERROR", "step": "9", "plugin": "io-binding",
    "message": f'input "{name}" not found on task "{task}" — available: {available}',
    "context": {"task": task, "stage": stage, "input": name, "available": available}})
```

<!-- END: impl-json.md -->
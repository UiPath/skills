# I/O Binding — Implementation

> **Phase split.** Phase 3 only. Bind task I/O at Step 9.8; resolve in-expression `vars.$xref` markers at Step 11.5 (after conditions + SLA). Phase 2 writes task shape with empty `value` fields but does not bind values. See [`../../../phased-execution.md`](../../../phased-execution.md).

After all tasks are created/enriched (Step 9) and global variable/output wiring is complete, edit `caseplan.case` to bind task I/O.

## Task Input Shape

Set `task.data.inputs[].value`. `tasks describe` inputs have empty `value`; IDs are random `v` + 8 chars, letter-leading, as in [global-vars § Formal-arg slot ID format](../global-vars/impl-json.md#formal-arg-slot-id-format).

```json
{ "name": "in_CustomerId", "type": "string",
  "id": "vA1b2C3d4", "var": "vA1b2C3d4",
  "elementId": "Stage_verify-tKYC001",
  "value": "=vars.customerId" }
```

## Task Output Shape

`task.data.outputs[]` is read-only after enrichment. Output IDs are name-based camelCase under [uniqueness rule](../global-vars/impl-json.md#uniqueness-rule); `source` reads the task response and is unchanged when `var` is suffixed.

```json
{ "name": "KycResult", "type": "string",
  "id": "kycResult", "var": "kycResult", "value": "kycResult",
  "source": "=KycResult", "target": "=kycResult",
  "elementId": "Stage_verify-tKYC001" }
```

For every `->` row, `originalVar` equals the allocated entry `id`, including collision suffixes and equal-name reassignment; it is the pre-reassignment slot used by FE root-mirroring filters. A foreign or missing `originalVar` is `CASE_MGMT_OUTPUT_ORIGINAL_VAR_MISSING`; test that entry's `id`, never the schema field name. Two tasks each producing `APIOutput1`:

```json
// first task to claim the name
{ "name": "APIOutput1", "id": "aPIOutput1",  "var": "aPIOutput1" }

// second task, reassigned: id is suffixed, and originalVar repeats THAT id
{ "name": "APIOutput1", "id": "aPIOutput12", "var": "renamedResult",
  "originalVar": "aPIOutput12", "source": "=APIOutput1", "target": "=aPIOutput12" }
```

`"originalVar": "aPIOutput1"` on that second entry names another task's output and is an error.

## Output Binding Shapes

Combine each plugin's Step 0 schema (`tasks describe` for non-connectors; `case spec --input-details` `caseShape.outputs[]` for connectors), SDD `->`/`=` rows, and schema-discovered bare items during task write. Bare is internal auto-minting, never an SDD operator.

Resolve each SDD field path before choosing a shape:

1. Split on `.`; match the first segment exactly to a top-level Step 0 output, using `source` without `=` then `name`.
2. With no remainder, use that descriptor.
3. Otherwise walk `Body.Properties` (`body.properties` normalized; `JsonSchema.Properties` CLI equivalent) exactly to the leaf.
4. For nested paths use the leaf display name, otherwise the exact final segment; copy only leaf `type` and type-refining attributes, never the parent object's `jsonSchema` type/body.
5. A nested path references its top-level parent; do not auto-mint that parent unless a separate schema-discovered bare item exists. Connector nodes verbatim-splice `caseShape.outputs[]`, regardless of SDD references, and bind nested rows into `response` ([connector-trigger-impl.md § Write `context` / `inputs` / `outputs` from the spec-cache](../../../connector-trigger-impl.md#write-context--inputs--outputs-from-the-spec-cache)). Business-rule tasks retain `output` (`=result`) and `Error`; `<decision>.<column>` is beside them ([business-rule/impl-json.md](../../tasks/business-rule/impl-json.md)). If any segment fails, log `ERROR`, skip the binding, and never fall back to the last parent.

For each top-level Step 0 entry, only an SDD bare name or explicit `->` first segment suppresses schema auto-minting. On connectors this controls shape only; the spliced entry set is fixed. `$xref('Stage','Task','output')` is neither reference form: auto-mint its named output and add the `=` row.

- **`<sdd-field-path> -> <sdd-name>`:** reassign the shape. Set `baseId = camelCase(leaf segment)` and allocate `id` under [uniqueness rule](../global-vars/impl-json.md#uniqueness-rule), including controlled equal-name aliasing. Emit top-level display name, or nested leaf display name/final segment, with required `type` (resolved leaf type), allocated `id`, `var: <sdd-name>`, `originalVar: <allocated id>`, `value: <sdd-name>`, `source: =<sdd-field-path>` verbatim, `target: =<allocated id>`, and `elementId: <stage-task>`. Resource-task type comes from `uip maestro case splice --described` ([resource-task-common.md](../../tasks/resource-task-common.md)), never by hand; business-rule extracts use the leaf type ([business-rule/impl-json.md](../../tasks/business-rule/impl-json.md)). Retain a parser row only when `name`, `type`, `source`, and `var` exist; packaging may omit undefined `type`. Keep `originalVar`; it drives FE `mutateRootVariables` (`VariableMutationUtils.ts:135`).
- **Bare `<name>`:** emit `{name, type: <Step 0 type>, id: <camelCase(name)>, var: <id>, value: <id>, source: <Step 0 source verbatim>, target: =<id>, elementId}`; omit `originalVar`.
- **`<sdd-name> = <expression>`:** emit Scenario E `{name: <sdd-name>, custom: true, var: <sdd-name>, value: <expression>, source: <same>, target: "", body: "", type: <SDD Outputs Type>, elementId: "root"}`. It has no `id` or `originalVar`; `type` is the SDD row Type, not root-variable type (`sdd convert` maps SDD `number` to `double`) or converter placeholder `string`. Only this shape has literal blank `target` and `body`; reassign and auto-mint retain real targets/values. Canonicalize `=metadata.X` to `=js:metadata.X` in `value` and `source`; retain SDD-natural form in the projected item. Strip quotes from quoted string literals (`"InReview"` becomes `InReview`). It has no root mirror: FE `isUpdateExistingOutput` at `VariableMutationUtils.ts:49-64` skips it.

| shape | `target` | `value` | `body` |
|---|---|---|---|
| Scenario E (`=` custom) | `""` | the expression | `""` |
| reassign (`->`) | `"=<allocated id>"` | the SDD name | absent |
| bare auto-mint | `"=<id>"` | the `id` | absent |

- **Unreferenced schema fields:** auto-mint as above; connector plugins also apply [uniqueness rule](../global-vars/impl-json.md#uniqueness-rule) suffixing.

Carry every type-refining descriptor attribute, especially `options`, verbatim on reassign, bare, and connector-rule outputs; nested extracts copy only leaf attributes. `=` outputs carry no schema `options`. `=` expressions may be literals (`"InReview"`, `5`, `true`), computed (`=js:vars.x + 1`), or references (`=vars.X.Y.Z`); dot paths work and array indexing is unsupported in v1. Targets of both `->` and `=` MUST exist in the Case Variables table. Apply [uniqueness rule](../global-vars/impl-json.md#uniqueness-rule) to every `->` source-side `id`; mirror the allocated ID in `target` and `originalVar`, keep `source` unchanged, and keep `var` at the existing target variable.

**Emission order:** emit an output before any same-task `=` row reading its `var`; evaluate `data.outputs` in array order. Thus schema auto-mint commonly precedes an SDD `=` row even when the row comes first. `--strict` reports forward reads as `STRICT_OUTPUT_FORWARD_READ`.

```json
[
  {
    "name": "Action",
    "type": "string",
    "id": "action4",
    "var": "action4",
    "value": "action4",
    "source": "=Action",
    "target": "=action4",
    "elementId": "Stage_review-tBuyer01"
  },
  {
    "name": "buyerDecision",
    "type": "string",
    "custom": true,
    "var": "buyerDecision",
    "value": "=js:vars.action4",
    "source": "=js:vars.action4",
    "target": "",
    "body": "",
    "elementId": "root"
  }
]
```

**Reassign collision:** derive collision-prone `id` from the field name, not the `v` + 8 input/formal-slot format. Suffix `id`, `target`, and `originalVar`; retain `var` and `value` as the case variable. Multiple extractions to one case variable get distinct IDs and one shared `var`; random IDs would defeat collision detection and suffix the wrong field. Given another task already owns `id: "aPIOutput1"`, the row `APIOutput1 -> renamedResult` emits:

```json
{
  "name": "APIOutput1",
  "type": "string",
  "id": "aPIOutput12",
  "var": "renamedResult",
  "originalVar": "aPIOutput12",
  "value": "renamedResult",
  "source": "=APIOutput1",
  "target": "=aPIOutput12",
  "elementId": "Stage_verify-tCallApi01"
}
```

**Equal-name extract:** dispatch on `->` before comparing names. `greeting -> greeting` is reassign, with `id`, `var`, `originalVar`, and `value` equal to `greeting`, `source: =greeting`, and `target: =greeting`, subject to controlled aliasing.

**Nested extract example.** Given a top-level `Error` output with `type: "jsonSchema"` and `Body.Properties.Message.Type: "string"`, the SDD row `Error.Message -> errorMessage` emits only this reassigned leaf unless schema discovery separately adds a bare `Error` item:

```json
{
  "name": "Message", "type": "string",
  "id": "message", "var": "errorMessage", "originalVar": "message",
  "value": "errorMessage", "source": "=Error.Message", "target": "=message",
  "elementId": "Stage_verify-tCallApi01"
}
```

`type: "jsonSchema"` on this row is wrong: that is the parent `Error` descriptor, not the resolved `Message` leaf.

## Output Binding Shapes for Connector Condition Rules

Apply the same `->`, `=`, and schema-bare shapes to `wait-for-connector` condition rules in stage-entry, stage-exit, case-exit, and task-entry scopes:

| Aspect | Connector task | Connector condition rule |
|---|---|---|
| Target array | `task.data.outputs[]` | `rule.uipath.outputs[]` |
| Step 0 schema | `tasks describe` / `case spec --input-details` `caseShape.outputs[]` | `case spec --type trigger --input-details` `caseShape.outputs[]` |
| `elementId` | `<stageId>-<taskId>` | `<ownerNodeId>-<ruleId>`; stage scopes use `<stageId>-<ruleId>`, case-exit uses `root-<ruleId>` |
| `->` root companion | Required, `elementId: "root"`, `custom: true` | Required, same shape |
| `=` Scenario E | Permitted | Permitted for rule response, literal, or expression; no root mirror |

The [global pool](../global-vars/impl-json.md#uniqueness-rule) is tasks ∪ triggers ∪ rules ∪ root. Each condition plugin invokes this dispatch as the LAST step of its `wait-for-connector` recipe, after `rule.uipath` Step 5 and before root bindings Step 6; iterate SDD `Outputs:` over already-minted entries, rewrite matches, and retain schema bare items. See the four condition `impl-json.md` files and [connector-trigger-impl.md § Target: connector-bound condition rule](../../../connector-trigger-impl.md#target-connector-bound-condition-rule).

If `rule.uipath.outputs[]` is absent/empty (unresolved connector placeholder), log `SKIPPED` and continue; the stub has a `uipath` block but nothing to bind ([connector-trigger-impl.md § Placeholder fallback](../../../connector-trigger-impl.md#placeholder-fallback)).

**Runtime order (KNOWN ISSUE):** the backend evaluates the gateway before rule extraction, so an in-rule gate cannot use the extracted case variable. Treat it as undefined until verified; put the gate on the downstream stage-entry/task-entry condition.

## Binding Procedure

### Output reference ID (authoritative)

Whole-value `<-` and in-expression `$xref` use the same ID:

```text
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

Normal, bare, and reassigned outputs use `.id`; custom `=` outputs use the verified root companion `.id`. Never use a reassigned output's `.var` as its source ID; `estimatedAge2` requires `=vars.estimatedAge2`.

For each SDD Inputs row:

- **Literal/expression:** write the post-rewrite string directly to `input.value`; translate `=metadata.X` to `=js:metadata.X` per [canonical-form table](../../../bindings-and-expressions.md#canonical-form-per-sink). **A quoted string literal's quotes are SDD delimiters, never payload**: the SDD's `APIInput1 = "literal-seed"` emits `"value": "literal-seed"`, NOT `"value": "\"literal-seed\""`. The projected item keeps the SDD cell's own quotes ([planning.md § code spans](planning.md)); `caseplan.case` strips them. Embedded delimiters pass `validate` and ship the quote characters to the resource as payload.
- **Cross-task `input <- "Stage A"."Task X".outputName`:** find stage by `data.label`, task by `displayName`, and output by exact `name`; resolve its authoritative ID and write `=vars.<outputReferenceId>`.

### In-Expression Marker Resolution (Step 11.5)

Whole-value `<-` handles only a reference value. In one global pass at Step 11.5, after Step 10 conditions and Step 11 SLA, after all task/trigger/rule outputs are minted/deduped and immediately before validation, resolve `vars.$xref` in every string in `caseplan.case`, including `=js:` composites, `conditionExpression`, SLA `expression`, computed `=` outputs, and connector body fields. This is the LAST Phase 3 mutation.

```text
TOKEN = /vars\.\$xref\('([^']+)','([^']+)','([^']+)'\)/   # global, all matches
for each string value V anywhere in caseplan.case:
    for each match (stageLabel, taskName, outputName) of TOKEN in V:
        find stage by data.label; task by displayName; output by data.outputs[].name
        if lookup fails: leave token; Check 4 invokes AskUserQuestion
        resolve_output_reference_id(caseplan, output); if it fails: leave token
        replace with "vars." + output_reference_id   # bare, no leading "="
    write V back
```

Use the same name-triple and ID rules as `<-`; substitution is bare because the marker is inside `=js:`. Secondary-stage/adhoc cross-stage scope applies.

After binding, run the end-of-Phase-3 validator.

### Check 1 — `=vars.X` reference resolution

Every bound input has non-empty `value`. Every `=vars.X` in inputs, stage/task entry/exit conditions, case-exit/trigger rules, SLA expressions, and any `=js:` string resolves by `.id` to a task `data.outputs[].id`, `variables.inputOutputs[].id`, or `variables.inputs[].id`. Match `.id`, not `.var`; custom outputs use their companion ID.

### Check 1.5 — Custom-output metadata expressions are canonical

For every `custom: true` output, reject `value` or `source` beginning `=metadata.`; both must be `=js:metadata.<field>`.

### Check 2 — Out-arg producer presence

For each top-level `variables.outputs[]` formal Out-arg, `var` points to the end-case slot; its always-present `variables.inputOutputs[]` companion may have empty `default`. A value source is a non-empty companion `default`, any SDD `<field> -> <var>` extraction, `<var> = <expression>` assignment, or schema-discovered bare `<name>` whose camelCase equals `var`.

- Default present: `OK`.
- Producer exists and task is resolved: `OK`.
- Producer exists but task is Rule 18 placeholder (look up the producer task in `caseplan.case` by `displayName`; `node.data.inputs` is empty `{}`): silent `WARN`; `LOG_OPEN_ITEM("Out-arg with declared but unresolvable producer — runtime returns empty until producer is wired")` under `## Open Items for User` because Rule 18 already prompted.
- No producer and empty default: `AskUserQuestion` pure orphan.

```text
for entry in root.outputs[]:
  var = entry.var
  case_var_row = tasks_md_row_for_out_arg(name=entry.name)
  has_companion_default = (case_var_row.default not empty)

  # Producer scan — three patterns. All operate on the SDD Outputs rows projected per planning.md:
  has_extraction_producer  = exists in the SDD any task with an Outputs row projecting to `<field> -> <var>` (where var matches the Out-arg's var)
  has_assignment_producer  = exists in the SDD any task with an Outputs row projecting to `<var> = <expression>` (where var matches the Out-arg's var)
  has_bare_name_producer   = exists a schema-discovered bare output `<name>` (no operator) where camelCase(name) == var
  has_any_producer         = has_extraction_producer || has_assignment_producer || has_bare_name_producer

  producer_task_unresolved = the SDD-declared producer task is a Rule 18 placeholder (look up the task in caseplan.case by displayName; check `node.data.inputs` is empty `{}`)

  if has_companion_default:
      OK
  elif has_any_producer and producer_task_unresolved:
      LOG_OPEN_ITEM("Out-arg with declared but unresolvable producer — runtime returns empty until producer is wired")
  elif not has_any_producer:
      AskUserQuestion("pure orphan", options=(a, b, c, d))
```

```
Out-argument "<name>" (id v<random8>, var <var>) has no value source:
  SDD row Default: <"" (empty)>
  Companion root.inputOutputs[].id="<var>": exists, default=""
  Producing task in the SDD (extraction or assignment): none found

Pick one:
  (a) Add producer task output — supply the producer task's **display name** as shown in the SDD (e.g., `Send Slack Message`). If the named task doesn't exist, re-prompt. Skill appends `<field> -> <var>` to that task's Outputs.
  (b) Add a Default value to the SDD Case Variables row — supply value inline (literal string).
  (c) Recategorize as Variable (case-internal state) or remove the variable.
  (d) Continue with best-effort emit (case builds; runtime returns empty string for this Out-arg; entry logged under "Open Items for User" in build-issues.md).
```

The pure-orphan prompt reports Out-arg name/id/var, empty Default, companion existence/default, and no producing task, then offers: (a) supply producer task **display name**, append `<field> -> <var>` using a spec-derived field or `<UNKNOWN>`, re-run Phase 1, retry Step 12, and re-prompt if absent; (b) supply inline literal Default, edit SDD, re-run Phase 1, retry Step 12; (c) ask `Recategorize as "Variable" or "Remove" the variable?`; Variable changes Category and reruns Phase 1 dispatcher/retries Step 12, Remove deletes the row and does likewise; (d) continue best-effort, build, log under `## Open Items for User`, and proceed Phase 4 without rerun.

Log:

```markdown
## Open Items for User

- **[Out-arg `<name>` has no value source]** — The Out-argument `<name>` is declared in `variables.outputs[]` but {no producer wired AND no Default}. Runtime will return empty string for this Out-argument unless one of:
  - Add a `<field> -> <name>` row to a task's Outputs that produces this value (extraction)
  - Add a `<name> = <expression>` row to a task's Outputs (assignment from literal / computed / variable reference)
  - Add a Default value to the SDD Case Variables row
  - Recategorize the variable as `Variable` or remove it
```

See [implementation.md § Step 12 — End-of-Phase-3 validator pass](../../../implementation.md).

### Check 3 — Type and descriptor fidelity

For a `=vars.X` input type mismatch, log `WARNING` and proceed. For every `->`, re-resolve the complete source path and require emitted `name` and `type` to equal the exact resolved leaf; nested extracts must not separately auto-mint their parent unless a schema-discovered bare item exists. Connector and business-rule tasks are exempt. A mismatch is `ERROR`: correct from the descriptor and rerun Check 3; `uip maestro case validate` is insufficient.

### Check 4 — No surviving `$xref` markers

Scan every string for `$xref(`. A survivor means failed name/ID resolution and receives the same interactive remediation as unresolved `=vars.X`, never silent error. Show stage/task/output found status, available task outputs, and sink:

```
In-expression reference $xref('<stage>','<task>','<output>') does not resolve:
  Stage  "<stage>":  <found | NOT FOUND>
  Task   "<task>":   <found | NOT FOUND in that stage>
  Output "<output>": NOT FOUND on task
  Available outputs on "<task>": <name, name, ...>
  Used in: <sink — e.g. entry condition on stage "Approve" | input "payload" on task "Notify">

Pick one:
  (a) Name the intended output — supply the correct output name (or full Stage / Task / output triple).
  (b) Edit the SDD expression — the marker is one term in a larger =js: expression; the upstream output genuinely does not exist.
  (c) Continue with best-effort emit — token left unsubstituted; case builds; the =js: expression throws at runtime until fixed.
```

Offer: (a) provide corrected output or full triple, rewrite in place, rerun Step 11.5 and rescan, reprompt if needed; (b) edit the SDD expression, rerun Phase 1, retry Step 11.5/check; (c) leave token, append an Open Items entry, proceed Phase 4; runtime `=js:` fails. Never ship `vars.$xref(...)`.

```markdown
## Open Items for User

- **[Unresolved `$xref` marker]** — `vars.$xref('<stage>','<task>','<output>')` in <sink> did not resolve (output not found on the named task). The `=js:` expression throws at runtime until fixed. Correct the source output name in the SDD and rebuild.
```

### Check 5 — Resolved-resource I/O completeness

Read each resolved task's persisted contract from `tasks/registry-resolved.json` (per-input `name`/`required`, declared output-field list written at §Resolve). Skip tasks without a contract (Rule 18 / `<UNRESOLVED>`), as in Check 2.

For each required input, require a matching non-empty `task.data.inputs[].value`; upstream references count whether whole-value `=vars.<outputReferenceId>` or resolved inside `=js:`. For each task output whose `source` is `=<path>`, strip `=`, take the top-level segment after `response.`, `Error.`, or `data.`, and require it in the contract's declared output names. Missing required input or phantom output is `ERROR` and `AskUserQuestion`.

```text
for task in caseplan.case tasks where contract = registry_resolved[task].contract is present:
    bound_inputs = { inp.name : inp.value for inp in task.data.inputs[] }
    for decl in contract.inputs where decl.required:
        v = bound_inputs.get(decl.name)
        if v is missing or v == "":
            ERROR → AskUserQuestion (unbound-required-input)
    declared_out = set(contract.outputs[].name)
    for out in task.data.outputs[]:            # extract rows: source = "=<path>"
        leaf = top_level_segment(strip_leading_"=", out.source)   # strip envelope prefix: response. / Error. / data.
        if leaf not in declared_out:
            ERROR → AskUserQuestion (phantom-output-field)
```

```
Required input "<field>" on task "<task>" (resource "<resource>") is not bound:
  Declared by the resource as required; no Inputs row with a value in the case plan.
  Other required inputs on this task: <bound / unbound list>

Pick one:
  (a) Bind it — supply the source: a case variable, a literal, or an upstream task's output ("Stage"."Task".out). Skill writes the Inputs row and binds it.
  (b) Mark <UNRESOLVED> — record a placeholder + a high review item; case builds, this input is runtime-null until wired.
  (c) Continue with best-effort emit — leave it unbound; entry logged under Open Items; the job may fault at runtime.
```

```
Output field "<field>" extracted by task "<task>" is not in resource "<resource>"'s declared outputs:
  Available outputs on this resource: <name, name, ...>
  Used in: outputs row "<field> -> <caseVar>"

Pick one:
  (a) Name the intended output — pick from the available list; skill rewrites the extract Field + re-resolves.
  (b) Drop the extract row — the case does not consume this output.
  (c) Continue with best-effort emit — left as-is; entry logged under Open Items; the extract resolves to runtime null.
```

The unbound-input prompt identifies field/task/resource and other required inputs, then offers (a) bind from case variable, literal, or upstream `"Stage"."Task".out`, write SDD + `caseplan.case`, run Step 9.8, retry; (b) mark `<UNRESOLVED>`, append high review item `rev_unbound_input_<task>_<field>`, continue; (c) leave unbound, append Open Items, continue.

The phantom-output prompt identifies field/task/resource and available outputs, then offers (a) select an available field and rewrite `source`/`Field`, retry; (b) delete the row and let any orphaned `=vars.<caseVar>` reach Check 1; (c) leave as-is, append Open Items, continue.

Both checks honor build-with-best: option (c) proceeds to Phase 4; `validate` may remain green although runtime is null.

```markdown
## Open Items for User

- **[Unbound required input]** — task "<task>" (resource "<resource>") input "<field>" is required but unbound; resolves to runtime null. Bind it in the SDD and rebuild.
- **[Phantom output field]** — task "<task>" extracts "<field>", which resource "<resource>" does not emit; resolves to runtime null. Correct the output name in the SDD and rebuild.
```

## Connector Tasks

Connector task input values are written during Step 9.7, not this step. Resolve cross-task IDs with the authoritative algorithm before constructing `input-values`, then apply the sink wrap:

```json
{ "body": { "email": "=js:(vars.employeeEmail)", "caseRef": "=js:(metadata.ExternalId)" } }
```

Connector body sinks require `=js:(...)` for ALL `=vars.X`, `=metadata.X`, `=bindings.X`, and operator expressions such as `=js:(vars.amount > 5000)`. Plain forms become literal API strings. See [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink) and [connector-activity/impl-json.md](../../../plugins/tasks/connector-activity/impl-json.md).

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

Send all issues to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md). Use exact matching only; no fuzzy matching, auto-creation, or retries.

| Check | Severity | Action |
|---|---|---|
| Placeholder task (no `data.inputs[]`) | `SKIPPED` | Skip all bindings |
| Placeholder connector rule (no `rule.uipath.outputs[]`) | `SKIPPED` | Skip rule output bindings |
| Input name not found (exact) | `ERROR` | Skip binding; log available inputs |
| Source output not found (exact) | `ERROR` | Skip binding; log available outputs |
| `$xref(...)` name-triple or ID failure | `ERROR` | Leave token; Check 4 AskUserQuestion; log triple and outputs |
| `=vars.X` absent from task output/root variable IDs | `ERROR` | Skip binding |
| Out-arg has no producer and no companion `default` | `ERROR` | Check 2 issue and AskUserQuestion |
| Required resolved-resource input lacks bound `value` | `ERROR` | Check 5 AskUserQuestion: bind / `<UNRESOLVED>`+review / best-effort |
| Extract `Field` absent from resolved contract | `ERROR` | Check 5 AskUserQuestion: re-point / drop / best-effort |
| No persisted contract (placeholder / `<UNRESOLVED>`) | `SKIPPED` | Skip Check 5 |
| Input/variable type mismatch | `WARNING` | Proceed |
| Extract `name`/`type` differs from schema descriptor | `ERROR` | Correct exact leaf; rerun Check 3 |
| Undeclared nested parent auto-mint on non-connector/non-business-rule | `ERROR` | Remove parent; rerun Check 3 |

Record issues in-reasoning, not via subprocess, for example:

```text
issues.append({"severity": "ERROR", "step": "9", "plugin": "io-binding",
    "message": f'input "{name}" not found on task "{task}" — available: {available}',
    "context": {"task": task, "stage": stage, "input": name, "available": available}})
```

<!-- END: impl-json.md -->
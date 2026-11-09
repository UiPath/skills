# I/O Binding — Implementation

> **Phase split.** Phase 3 only. Bind I/O at Step 9.8; resolve in-expression `vars.$xref` markers at Step 11.5 (after conditions + SLA). Phase 2 writes task shape (schema with empty `value` fields), but does not bind values. See [`../../../phased-execution.md`](../../../phased-execution.md).

Wire `caseplan.case` after all tasks are created/enriched (Step 9), global-variable wiring, and output wiring.

## Task Input Shape

Set `task.data.inputs[].value`. Schema-written inputs initially have empty `value`; IDs are random, letter-leading `v` + 8 chars, using [global-vars § Formal-arg slot ID format](../global-vars/impl-json.md#formal-arg-slot-id-format).

```json
{ "name": "in_CustomerId", "type": "string", "id": "vA1b2C3d4", "var": "vA1b2C3d4", "elementId": "Stage_verify-tKYC001", "value": "=vars.customerId" }
```

## Task Output Shape

`task.data.outputs[]` is read-only after enrichment. Output IDs are name-based camelCase under [global-vars § Uniqueness rule](../global-vars/impl-json.md#uniqueness-rule); `source` reads the task response and is unchanged by `var` suffixing. For every `->`, `originalVar` equals that entry's allocated `id` (including collision suffixes and equal-name reassignment), never another output's name. Retain minted `id`, set `var` to the case variable, repeat `id` in `originalVar` for FE root-mirroring filtering, and compare locally with the same entry's `id`, not its schema name. Null/wrong `originalVar` is `CASE_MGMT_OUTPUT_ORIGINAL_VAR_MISSING`.

Two tasks each producing `APIOutput1`:

```json
// first task to claim the name
{ "name": "APIOutput1", "id": "aPIOutput1",  "var": "aPIOutput1" }

// second task, reassigned: id is suffixed, and originalVar repeats THAT id
{ "name": "APIOutput1", "id": "aPIOutput12", "var": "renamedResult",
  "originalVar": "aPIOutput12", "source": "=APIOutput1", "target": "=aPIOutput12" }
```

`"originalVar": "aPIOutput1"` on that second entry names another task's output and is an error — `CASE_MGMT_OUTPUT_ORIGINAL_VAR_MISSING`. The test is local and needs no lookup: read `originalVar` off the same entry's `id`, never off the schema field name.

## Output Binding Shapes

Combine each plugin's Step 0 schema (`tasks describe` for non-connectors; `case spec --input-details` `caseShape.outputs[]` for connectors) with SDD `->`/`=` rows and schema-discovered bare items. Bare is internal auto-minting, never an SDD Outputs operator. Apply during plugin task-write.

Resolve the schema descriptor for every SDD field path **before** choosing an output shape:

1. Split `<sdd-field-path>` on `.`. Match the first segment exactly to a top-level Step 0 output (`source` with the leading `=` removed, falling back to `name`).
2. With no remaining segments, the resolved descriptor is that top-level output.
3. With remaining segments, walk them exactly through the top-level output's `Body.Properties` (`body.properties` in normalized case-shape data; `JsonSchema.Properties` is the equivalent CLI mirror). The descriptor after the final segment is the **leaf descriptor**.
4. For a nested path, set the emitted `name` to the leaf's display name when present, otherwise its exact final path segment. Take `type` plus any type-refining attributes from the leaf descriptor only. Never copy the parent object's `jsonSchema` type or body onto a scalar leaf.
5. A nested path references its top-level parent. Do not additionally auto-mint that parent unless the projected output list contains a separate schema-discovered bare item for it. **Connector nodes are exempt:** their `data.outputs[]` is a verbatim splice of `caseShape.outputs[]`, so every spec entry is present regardless of what the SDD references, and a nested row binds into the spliced `response` rather than suppressing it ([connector-trigger-impl.md § Write `context` / `inputs` / `outputs` from the spec-cache](../../../connector-trigger-impl.md#write-context--inputs--outputs-from-the-spec-cache)). **Business rule tasks are exempt too:** the task always carries `output` (`=result`) and `Error`, and a `<decision>.<column>` extract sits beside them ([business-rule/impl-json.md](../../tasks/business-rule/impl-json.md)). If any segment does not resolve, log `ERROR` and skip the binding; never fall back to the last resolved parent.

For each top-level Step 0 entry, schema auto-mint only when the SDD references neither it bare nor as the first `->` segment. On connectors this controls shape, not existence, because splicing fixes entries. `$xref('Stage','Task','output')` is neither form: auto-mint its named output and retain the additional `=` row.

- **`<sdd-field-path> -> <sdd-name>`:** Allocate `baseId = camelCase(leaf segment)` under [global-vars § Uniqueness rule](../global-vars/impl-json.md#uniqueness-rule), including controlled equal-name alias. Emit `{name: <resolved name>, type: <resolved leaf type>, id: <allocated id>, var: "<sdd-name>", originalVar: <allocated id>, value: "<sdd-name>", source: "=<sdd-field-path>", target: "=<allocated id>", elementId: "<stage-task>"}`. Top-level `name` is its display name; nested `name` is leaf display name or final segment. `source` is the verbatim SDD left side prefixed with `=`. `type` is required and for resource tasks comes from `uip maestro case splice --described` ([resource-task-common.md](../../tasks/resource-task-common.md)); never type by hand, except business-rule `<decision>.<column>`, whose type comes from the leaf ([business-rule/impl-json.md](../../tasks/business-rule/impl-json.md)). The parser retains a row only when `name`, `type`, `source`, and `var` exist; otherwise drop it before evaluation. Packaging may omit undefined `type`. `originalVar` mirrors `id` and preserves the case-variable companion through FE `mutateRootVariables` (`VariableMutationUtils.ts:135`).
- **Bare `<name>`:** Emit `{name, type: <Step 0 type>, id: <camelCase(name)>, var: <id>, value: <id>, source: <Step 0 source verbatim>, target: "=<id>", elementId}`; no `originalVar`. Use only unaliased top-level entries. Schema fields without SDD references use it; connectors also apply global uniqueness suffixing (for example `response` → `response2`).
- **`<sdd-name> = <expression>`:** Emit Scenario E `{name: "<sdd-name>", custom: true, var: "<sdd-name>", value: "<expression>", source: "<same as value>", target: "", body: "", type: <SDD Outputs Type>, elementId: "root"}`. Do not emit `id` or `originalVar`. `type` is the SDD row Type, never root case-variable type (`sdd convert` writes root `number` as `double`) or converter placeholder `string`. **On this shape only, `target` and `body` are present-but-blank: emit `"target": ""` and `"body": ""` literally rather than dropping the keys.** An omitted key is not the same as a blank one — the FE reads a missing `target` as unset rather than deliberately-empty. Its value is the expression and it produces no root mirror because FE `isUpdateExistingOutput` at `VariableMutationUtils.ts:49-64` skips it. Canonicalize `=metadata.X` to `=js:metadata.X` in `value` and `source`, retaining the SDD-natural form in the projected item. Strip SDD delimiter quotes from quoted literals (`status = "InReview"` yields `InReview`, not escaped quotes).

`=` values may be literals (`"InReview"`, `5`, `true`), computed (`=js:vars.x + 1`), or variable references (`=vars.X.Y.Z`). Dot paths in `->` work; array indexing is unsupported in v1. Every `->` and `=` target case variable MUST exist in the Case Variables table.

Never blank `target` or `value` on `->`/bare rows:

| shape | `target` | `value` | `body` |
|---|---|---|---|
| Scenario E (`=` custom) | `""` | expression | `""` |
| reassign (`->`) | `"=<allocated id>"` | SDD name | absent |
| bare auto-mint | `"=<id>"` | id | absent |

Carry every extra type-refining attribute, especially `options`, verbatim onto reassign, auto-mint, and connector-rule outputs. Nested extracts copy leaf attributes only; do not inherit parent `body`, `jsonSchema`, `options`, or `type`. Scenario E carries no schema `options`.

Apply [global uniqueness rule](../global-vars/impl-json.md#uniqueness-rule), including controlled equal-name alias, to every source-side `->` `id`; mirror allocated ID into `target` and `originalVar`, retain `source`, and keep `var` pointed at the existing target Case variable.

Emit an output before any same-task row whose expression reads its `var`, regardless of SDD order. `data.outputs` is sequential; otherwise the reader sees the case-variable default while `validate` may still report `Valid`. Emit the auto-mint first and the `=` row last, whatever order the SDD's table used. `--strict` reports a violation as `STRICT_OUTPUT_FORWARD_READ`.

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

**Reassign collision.** The allocated `id` is derived from the field name, never the `v` + 8 form task inputs and formal slots use, so `id` is the field that can clash and the field that takes the suffix. `target` and `originalVar` follow it; `var` and `value` keep pointing at the case variable. Given another task already owns `id: "aPIOutput1"`, the row `APIOutput1 -> renamedResult` emits:

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

Eight tasks extracting the same field into one case variable produce this eight times: eight distinct `id` values, one shared `var`. Minting `id` randomly leaves nothing that can clash, the suffix lands on `var` instead, and seven of the eight then name a case variable that was never declared.

**Equal-name extract dispatch.** Dispatch by the explicit operator before comparing names; equal operands select the reassign shape, never the bare auto-mint branch. Apply the global [controlled-alias rule](../global-vars/impl-json.md#uniqueness-rule). With no unrelated collision, `greeting -> greeting` emits `id`, `var`, `originalVar`, and `value` as `"greeting"`, with `source: "=greeting"` and `target: "=greeting"`. `originalVar` distinguishes reassignment from a bare output and keeps the predeclared root companion intact during frontend synchronization; the linked allocator owns any required suffixing.

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

For each task input row in the SDD's Inputs table:

**Literals/expressions** — write the value string directly to `input.value`. Values shown are POST-rewrite — impl translates the SDD's `=metadata.X` to `=js:metadata.X` per the [canonical-form table](../../../bindings-and-expressions.md#canonical-form-per-sink) (plain `=metadata.X` is not resolved by the lookup-path evaluator). **A quoted string literal's quotes are SDD delimiters, never payload** — same rule as the `=` output side above: the SDD's `APIInput1 = "literal-seed"` emits `"value": "literal-seed"`, NOT `"value": "\"literal-seed\""`. The projected item keeps the SDD cell's own quotes ([planning.md § code spans](planning.md)); `caseplan.case` strips them. Embedded delimiters pass `validate` and ship the quote characters to the resource as payload:
```
"=vars.amount"  |  "=js:metadata.ExternalId"  |  "literal-seed"  |  "50"  |  "=js:new Date()"
```

For cross-task `input <- "Stage A"."Task X".outputName`, find stage by `data.label`, task by `displayName`, and output by exact `name`; resolve its ID authoritatively and write `=vars.<outputReferenceId>`. Do not fuzzy-match, create, or retry.

## In-Expression Marker Resolution (Step 11.5)

Whole-value `<-` (above) only resolves an input whose value IS the reference. To reference an upstream output from **inside** a `=js:` expression (composite payload, `conditionExpression`, SLA `expression`, computed `=` output, connector body field), the SDD embeds a `vars.$xref('Stage','Task','output')` marker — see [bindings-and-expressions.md § In-expression references](../../../bindings-and-expressions.md#in-expression-references-varsxref). Resolve all markers in **one pass over the whole `caseplan.case`** at **Step 11.5** — after conditions (Step 10) and SLA (Step 11) are written, and every task/trigger/rule output is minted and deduped (so the marker resolves to the final output reference ID). This is the LAST mutation of Phase 3 before the validator; running it earlier (e.g. right after Step 9.8 input binding) misses markers in conditions / SLA and reads pre-dedup IDs.

This single sink-blind pass replaces per-sink resolution: it walks every string value regardless of which sink holds it, so conditions, SLA, inputs, and connector bodies are all covered in one place.

```text
# pseudocode — not executed. Realize via Read → reason → Write/Edit.
TOKEN = /vars\.\$xref\('([^']+)','([^']+)','([^']+)'\)/   # global, all matches

for each string value V anywhere in caseplan.case:
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

After this pass and all bindings, run the end-of-Phase-3 validator. It performs the cross-reference checks below:

### Check 1 — `=vars.X` reference resolution

Verify every bound input has a non-empty `value`, and every `=vars.X` reference resolves to an existing entry in one of:
- Any task `data.outputs[].id` (the resolver match key; mirrors `var` under skill convention)
- Variables `inputOutputs[].id`
- Variables `inputs[].id`

Variables array path is top-level `variables.{inputOutputs,inputs}[].id`.

> **Scan key:** match by `.id`, NOT `.var`. The runtime resolver matches on `Variable.id` (`VariablesService.findVariableByVariableId`). Bare self-declaring outputs commonly have `id === var`, but reassigned outputs can have a collision-safe `.id` whose `.var` points at a different Case variable. Custom `=` outputs resolve through their root companion's `.id` per the authoritative algorithm above.

Also scan `=vars.X` references in:
- Entry / exit condition expressions (stage and task)
- Case-exit and trigger rule expressions
- SLA expressions
- `=js:` expressions anywhere they appear

Same resolution rule applies — these are read-side consumers of the variable namespace.

### Check 1.5 — Custom-output metadata expressions are canonical

For every `custom: true` output, reject `value` or `source` beginning with `=metadata.`; emit `=js:metadata.<field>` in both properties instead.

### Check 2 — Out-arg producer presence

For every entry in top-level `variables.outputs[]` (formal Out-arg entries), the entry's `var` field is a POINTER to the variable slot that should hold the value at case end. Per the always-emit-companion rule, the companion in `variables.inputOutputs[]` is always present; its `default` field is empty when SDD didn't declare a Default.

**The check:** can the Out-arg's slot be populated at runtime? Three populating mechanisms exist:

1. **Companion default** — non-empty `default` field on the companion → always-populated fallback.
2. **Extraction producer** — a task's `outputs: <field> -> <var>` row (extract response field into the Out-arg slot).
3. **Assignment producer** — a task's `outputs: <var> = <expr>` row (`=` operator: set/compute/copy a literal or expression into the Out-arg slot).
4. **Bare-name producer** — a task's `outputs: <var>` row where the bare name matches the Out-arg's var (camelCase of schema field name).

If none of these exist → **pure orphan**, prompt the author.

| Producer status | Validate time action |
|---|---|
| Companion has non-empty `default` | OK — Out-arg always has a value. |
| At least one producer (extraction, assignment, or bare-name) exists in the SDD AND its task is resolved (not Rule 18 placeholder) | OK — producer wires the slot when its task fires. |
| Producer declared but its task is a Rule 18 placeholder (declared-but-unwirable) | **Silent WARN.** Log to `tasks/build-issues.md` under `## Open Items for User`. Rule 18 already prompted the author for this task. |
| NO producer anywhere AND companion default empty | **AskUserQuestion** — pure orphan. 4 options below. |

Pseudocode:

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
      # Companion default guarantees a value; producer is optional bonus
      OK
  elif has_any_producer and producer_task_unresolved:
      # Declared producer but task is unresolvable — Rule 18 already prompted; just log
      LOG_OPEN_ITEM("Out-arg with declared but unresolvable producer — runtime returns empty until producer is wired")
  elif not has_any_producer:
      # Pure orphan — author never declared a producer AND no Default. Ask.
      AskUserQuestion("pure orphan", options=(a, b, c, d))
```

**On AskUserQuestion ("pure orphan" branch):**

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

**Skill response per user pick:**

- **(a)** Edit `sdd.md`: append a `<field> -> <var-name>` row to the named task's Outputs table (use the spec-derived field name if available, else an `<UNKNOWN>` placeholder). Re-run Phase 1 from the modified `sdd.md`, then retry Step 12.
- **(b)** Edit `sdd.md`: set the Out-arg's `Default` cell in the Case Variables table. Re-run Phase 1, then retry Step 12.
- **(c)** Prompt the user inline: `Recategorize as "Variable" or "Remove" the variable?` On `Variable`: edit the SDD's Case Variables row Category → Variable, re-run Phase 1 dispatcher, retry Step 12. On `Remove`: delete the row from `sdd.md`, re-run Phase 1, retry Step 12.
- **(d)** Append the build-issues entry (template below) and continue to Phase 4. No re-run.

Option (d) is the build-with-best escape for cases where the author intends to wire the producer later but wants to keep iterating now — equivalent to the silent-WARN treatment that declared-but-unresolvable producers (T20-style) get automatically.

**Rationale for the split:** real-world authoring is iterative. When an author has already gone through a Rule 18 prompt for the producer task (T20-style), the skill should not pile a second prompt on top — that's the path the author already chose by picking "Skip". But when the author authored a *pure orphan* with no producer declared at all (T14-style — wait-for-timer with no aliasing wire AND no Default), there's no prior signal of intent; the AskUserQuestion is the right surface to ask "did you mean to forget this, or wire it now?" Option (d) preserves the build-with-best escape.

**Build-issues entry template** (both branches log to this, only the AskUserQuestion branch ALSO prompts):

```markdown
## Open Items for User

- **[Out-arg `<name>` has no value source]** — The Out-argument `<name>` is declared in `variables.outputs[]` but {no producer wired AND no Default}. Runtime will return empty string for this Out-argument unless one of:
  - Add a `<field> -> <name>` row to a task's Outputs that produces this value (extraction)
  - Add a `<name> = <expression>` row to a task's Outputs (assignment from literal / computed / variable reference)
  - Add a Default value to the SDD Case Variables row
  - Recategorize the variable as `Variable` or remove it
```

See [implementation.md § Step 12 — End-of-Phase-3 validator pass](../../../implementation.md) for invocation.

### Check 3 — Type and descriptor fidelity

**Input consumers.** Where a `=vars.X` reference resolves to a declaration with a different `type` than the consuming input expects, log WARNING. Proceed (string coercion is common and runtime-tolerant).

**Extract outputs.** For every `->` row, re-resolve its full source path against the Step 0 schema using the algorithm above. Require the emitted output's `name` and `type` to equal the resolved name and leaf type. For a nested path, also require that the top-level parent was not separately auto-minted unless there is a schema-discovered bare item for it; connector and business rule tasks are exempt (rule 5). A mismatch is `ERROR`: correct the output from the resolved descriptor and re-run this check before Phase 4. Do not accept a passing `uip maestro case validate` as evidence here; structural validation does not compare a nested binding with its schema leaf.

### Check 4 — No surviving `$xref` markers

Scan every string value in `caseplan.case` for the literal token `$xref(`. The [Step 11.5 pass](#in-expression-marker-resolution-step-115) should have resolved them all; any survivor means its name-triple or output reference ID failed to resolve. This is the same class of failure as a Check 1 unresolved `=vars.X` — so it gets the **same interactive remediation**, NOT a silent ERROR. Never ship a marker to runtime (`vars.$xref(...)` throws — a method call on `vars`).

**On AskUserQuestion** (present the outputs that DO exist on the named task as candidates — same diagnostic shape as a failed whole-value `<-`):

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

**Skill response per pick:**

- **(a)** Rewrite the marker's triple in place in `caseplan.case` with the corrected name(s), re-run the [Step 11.5](#in-expression-marker-resolution-step-115) resolution for that token, then re-scan. If it still fails, re-prompt.
- **(b)** Edit the SDD expression as directed, re-run the Phase 1 dispatcher from the modified SDD, then retry Step 11.5 + this check.
- **(c)** Leave the token unsubstituted, append the build-issues entry (template below), continue to Phase 4. No re-run.

**Build-issues entry template:**

```markdown
## Open Items for User

- **[Unresolved `$xref` marker]** — `vars.$xref('<stage>','<task>','<output>')` in <sink> did not resolve (output not found on the named task). The `=js:` expression throws at runtime until fixed. Correct the source output name in the SDD and rebuild.
```

### Check 5 — Resolved-resource I/O completeness

Verifies each resolved task's binding contract **covers** its resource's declared I/O — the build-side re-check of the design-side Resolved-resource I/O completeness rule (case SDD content contract, `uipath-planner`) (Approve-gate item 9 / Finalization step 19). Where Checks 1–4 verify that references which *exist* resolve, Check 5 verifies the *right set of references exists*: required inputs are not silently missing, and extract outputs name real fields.

Read each resolved task's persisted contract from `tasks/registry-resolved.json` (per-input `name` + `required` flag, declared output-field list — written at §Resolve). **Skip** any task with no persisted contract (Rule 18 placeholder / `<UNRESOLVED>`) — same treatment as Check 2's unresolved-producer branch.

```text
# pseudocode — not executed. Realize via Read → reason → Write/Edit.
for task in caseplan.case tasks where contract = registry_resolved[task].contract is present:
    bound_inputs = { inp.name : inp.value for inp in task.data.inputs[] }
    # (a) required-input coverage
    for decl in contract.inputs where decl.required:
        v = bound_inputs.get(decl.name)
        if v is missing or v == "":            # no row, or row with empty value
            ERROR → AskUserQuestion (unbound-required-input)
    # (b) output-field fidelity
    declared_out = set(contract.outputs[].name)
    for out in task.data.outputs[]:            # extract rows: source = "=<path>"
        leaf = top_level_segment(strip_leading_"=", out.source)   # strip envelope prefix: response. / Error. / data.
        if leaf not in declared_out:
            ERROR → AskUserQuestion (phantom-output-field)
```

An **upstream-output-fed** required input is covered like any other — its `value` is `=vars.<outputReferenceId>` (whole-value `<-`) or sits inside a `=js:` (resolved `$xref`); a non-empty `value` passes. Do NOT expect a §1.5 declaration for it.

**On AskUserQuestion — unbound required input:**

```
Required input "<field>" on task "<task>" (resource "<resource>") is not bound:
  Declared by the resource as required; no Inputs row with a value in the case plan.
  Other required inputs on this task: <bound / unbound list>

Pick one:
  (a) Bind it — supply the source: a case variable, a literal, or an upstream task's output ("Stage"."Task".out). Skill writes the Inputs row and binds it.
  (b) Mark <UNRESOLVED> — record a placeholder + a high review item; case builds, this input is runtime-null until wired.
  (c) Continue with best-effort emit — leave it unbound; entry logged under Open Items; the job may fault at runtime.
```

**On AskUserQuestion — phantom output field:**

```
Output field "<field>" extracted by task "<task>" is not in resource "<resource>"'s declared outputs:
  Available outputs on this resource: <name, name, ...>
  Used in: outputs row "<field> -> <caseVar>"

Pick one:
  (a) Name the intended output — pick from the available list; skill rewrites the extract Field + re-resolves.
  (b) Drop the extract row — the case does not consume this output.
  (c) Continue with best-effort emit — left as-is; entry logged under Open Items; the extract resolves to runtime null.
```

**Skill response per pick:**

- Unbound (a) — write the Inputs row to `sdd.md` + `caseplan.case`, run the Step 9.8 binding for that input, retry Check 5. (b) — set the input `value` to a placeholder and append a `high` review item (`rev_unbound_input_<task>_<field>`), continue. (c) — append the build-issues entry, continue. No re-run.
- Phantom (a) — rewrite the output `source`/`Field` in `caseplan.case`, retry Check 5. (b) — delete the output row (and any now-orphaned `=vars.<caseVar>` consumer falls to Check 1). (c) — append the build-issues entry, continue.

Check 5 honors the same **build-with-best** policy as Checks 1, 2, 4: option (c) appends a `## Open Items for User` entry and proceeds to Phase 4. Phase 4 `validate` stays green (a missing input / phantom extract is structurally valid); the runtime concern is surfaced for pre-publish review.

**Build-issues entry templates:**

```markdown
## Open Items for User

- **[Unbound required input]** — task "<task>" (resource "<resource>") input "<field>" is required but unbound; resolves to runtime null. Bind it in the SDD and rebuild.
- **[Phantom output field]** — task "<task>" extracts "<field>", which resource "<resource>" does not emit; resolves to runtime null. Correct the output name in the SDD and rebuild.
```

## Connector Tasks

Connector task input values are written during Step 9.7 (connector detail), not this binding step. Resolve cross-task IDs authoritatively before constructing `input-values`, then apply the canonical sink wrap:

```json
{ "body": { "email": "=js:(vars.employeeEmail)", "caseRef": "=js:(metadata.ExternalId)" } }
```

Connector body sinks require `=js:(...)` for ALL references: `=vars.X`, `=metadata.X`, `=bindings.X`, and operator expressions such as `=js:(vars.amount > 5000)`. Plain prefix forms arrive at the API as literal strings. See [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink) and [connector-activity/impl-json.md](../../../plugins/tasks/connector-activity/impl-json.md).

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

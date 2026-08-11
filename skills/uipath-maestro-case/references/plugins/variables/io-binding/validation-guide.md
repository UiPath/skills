# I/O Binding Exit Validation

Read this guide only after every Phase 3 binding is emitted and the whole-artifact [Step 11.5 marker pass](impl-json.md#in-expression-marker-resolution-step-115) has finished. Run Checks 1–5 in order before Phase 4. Do not load it for ordinary input binding or output-reference resolution.

## Check 1 — `=vars.X` reference resolution

First build one runtime reference-ID set. Enumerate every array below; absent arrays contribute nothing.

| Producer family | Current `caseplan.json` path | Inclusion rule |
|---|---|---|
| Root variables and formal arguments | top-level `variables.{inputs,outputs,inputOutputs}[]` | Include every non-empty `id`. |
| Tasks, all stages/lanes | `nodes[<stage>].data.tasks[<lane>][].data.outputs[]` | Include every non-empty `id`; a placeholder `data: {}` contributes none. |
| Event triggers | `nodes[<trigger>].data.inputs.outputs[]` | Include every non-empty `id`; an unresolved trigger has no emitted spec outputs. Pattern-C/auto-emit entries without `id` resolve through their root companion. |
| Stage entry/exit connector rules | `nodes[<stage>].data.entryConditions[].rules[][].uipath.outputs[]` and `nodes[<stage>].data.exitConditions[].rules[][].uipath.outputs[]` | Include every non-empty `id`. |
| Task-entry connector rules | `nodes[<stage>].data.tasks[<lane>][].entryConditions[].rules[][].uipath.outputs[]` | Include every non-empty `id`. |
| Case-exit connector rules | `metadata.caseExitRules[].rules[][].uipath.outputs[]` | Include every non-empty `id`. |

A connector-rule stub with absent or empty `uipath.outputs[]` contributes none. These are the same producer paths and skip guards as the [global uniqueness pool](../global-vars/impl-json.md#pool-composition-what-to-scan).

Scan every string-valued runtime read in the artifact, including task/trigger/rule inputs, stage/task entry and exit conditions, case-exit rules, SLA fields, connector bodies, and custom or `=js:` expressions. Every canonical `vars.<X>` token must find `X` in the ID set. Also require a non-empty value for each input that `tasks.md` declares bound; optional descriptor inputs with no declared binding are handled by Check 5, not misclassified here.

Match the runtime-owned `id`, never `var`. A reassigned `->` output's `var` is its target Case-variable pointer while consumers of that producer use its collision-safe source `id`. A custom `=` output has no `id` and resolves through its root companion.

## Check 1.5 — Custom-output metadata expressions

For every `custom: true` output, reject `value` or `source` beginning with `=metadata.`. Canonicalize both properties to the same `=js:metadata.<field>` form, then re-run Check 1 for the affected expression.

## Check 2 — Out-arg producer presence

For each formal Out argument in top-level `variables.outputs[]`, use its `var` as the target slot. Find the matching `variables.inputOutputs[]` companion and its Default, then join declared output rows in `tasks.md` to emitted outputs across every task, event trigger, and connector rule in the four scopes from Check 1.

A declared producer must deliberately write the slot:

- `<field> -> <out-var>`: emitted `var == <out-var>` and the owner has the corresponding reassigned output;
- `<out-var> = <expression>`: emitted custom output has `var == <out-var>`; or
- a deliberately declared bare output: its emitted `id`/`var` owns the Out slot.

Do not count an unrelated schema-generated bare output merely because its display `name` camel-cases to something similar. Declaration ownership plus emitted slot identity is required.

| State | Result |
|---|---|
| Companion exists with non-empty Default | `OK`; a producer is optional. |
| Declared producer owner is resolved and its emitted output writes the slot | `OK`. |
| Producer is declared, but its task/trigger is a genuine placeholder, its connector rule is an unresolved stub, or its selected connector task, event trigger, or connector rule owner is marked enrichment-ineligible after spec failure/fallback | `WARNING`; accumulate one Open Item without prompting again because the resource gate already supplied the choice. |
| Producer is declared on an enrichment-eligible resolved owner but the matching output was not emitted | `ERROR`; re-run that selected output owner once and recheck. Halt if it still differs. |
| No Default and no declared producer in any family | True orphan: ask the four-way choice in the remediation table. |
| Default is declared but the required companion is absent | Ask whether to restore the canonical companion or revise/remove the Out declaration; do not enter Phase 4 until the selected repair is consistent. |

## Check 3 — Type and descriptor fidelity

For every explicit `->`, resolve the complete source path against the current contract selected by that exact producer's owner precedence:

- registry-backed non-connector task: its owner's current Step 0 `tasks describe --output json` descriptor; reuse the same-session result or rerun the exact Step 0 command after compaction; when that owner permits and describe is unavailable, use its planning-captured `tasks.md` schema; if neither exists, take that owner's placeholder/fallback;
- locally resolved agent/API sibling, existing or Rule-17-built: its case-preserving on-disk `entry-points.json` at `entryPoints[0].input/.output.properties`; for API, preserve owner fallbacks through `input/output.schema.document.properties` when flat properties are absent, then `Workflow.json` root input/output schemas when entry-point I/O is null; never call tenant `tasks describe`, and follow the local owner's fallback if its contract chain is unavailable;
- connector task: that target's enrichment-eligible `tasks/spec-cache.<elementId>.json` at raw `Data.CaseShape.Outputs`;
- event trigger: its target-local raw spec cache and the derived `tasks/trigger-spec-cache.json[T<N>]` view used by the global-variable dispatcher; and
- connector rule: its own `tasks/spec-cache.<ownerNodeId>-<ruleId>.json` and selected condition owner.

Walk every dot segment through the normalized descriptor. Require emitted `name`, `type`, and refining attributes such as `options` to match the final leaf. A nested leaf must not inherit its parent object's body/type and must not cause that parent to be auto-minted unless `tasks.md` separately declares the parent as bare. The [projection owner](../global-vars/output-projection-guide.md#descriptor-resolution-and-bare-outputs) defines the emission shape.

A consumer type mismatch logs `WARNING` and proceeds because runtime coercion is supported. A producer descriptor mismatch is `ERROR`. Before repair, capture each affected output's old source `id` and enumerate every whole-value `<-` and in-expression consumer. Re-emit once from the exact current owner contract selected above, then capture the new source `id` or its removal. When source identity changes or disappears, redispatch every affected consumer from its declarative `tasks.md`/SDD source through the consumer's owning binding/projection path; restore `vars.$xref(...)` marker form for in-expression consumers where applicable rather than string-replacing final IDs. Rerun Step 11.5, then Checks 1, 3, and 4. Any surviving read of an old ID, unresolved marker, or consumer still bound to a removed output is a stale-reference `ERROR`; halt before Phase 4. CLI structural validation is not evidence for leaf fidelity.

## Check 4 — No surviving `$xref` markers

Only after Step 11.5, scan every string value in the complete `caseplan.json` for the literal token `$xref(`. Any survivor is unresolved; never ship `vars.$xref(...)` as though it were runtime syntax.

Report the failed Stage/Task/output triple, the exact sink, and the outputs that actually exist on the resolved task. A corrected triple is resolved with the authoritative [output-reference-ID algorithm](impl-json.md#output-reference-id-authoritative), substituted as bare `vars.<id>` inside the surrounding expression, and scanned again. One correction attempt follows each user answer; if it still fails, offer SDD-expression repair or build-with-best rather than looping silently.

## Check 5 — Resolved-resource I/O completeness

Validate every resolved owner against its exact current descriptor/spec contract after the owning phase has completed:

- Registry-backed non-connector tasks use their owner's current Step 0 `tasks describe --output json` descriptor, including required flags and all declared outputs. Reuse the same-session descriptor or rerun the exact Step 0 command after compaction. When that owner permits and describe is unavailable, use its planning-captured `tasks.md` schema; if neither exists, take that owner's placeholder/fallback. `tasks/registry-resolved.json` is identity/audit evidence only and never an I/O-contract source.
- Every locally resolved agent/API sibling, existing or Rule-17-built, uses case-preserving on-disk `entry-points.json` at `entryPoints[0].input/.output.properties`. For API, preserve owner fallbacks through `input/output.schema.document.properties` when flat properties are absent, then `Workflow.json` root input/output schemas when entry-point I/O is null. Never call tenant `tasks describe`; follow the local owner's fallback if its contract chain is unavailable.
- Connector activities and in-stage connector waits use their own Phase 3 enrichment-eligible `tasks/spec-cache.<elementId>.json`; raw contract paths remain PascalCase `Data.CaseShape.Inputs`/`Outputs`. Preserve that exact casing and never read another target's cache.
- Event triggers use their target-local raw spec cache after the required-field gate plus the derived trigger-spec-cache view after global output dispatch.
- Connector rules in stage-entry, stage-exit, task-entry, and case-exit use their own target-local spec cache after the condition owner upgrades the rule.

For each contract, require every required input to have a non-empty emitted value at the owner-defined sink and require every explicit extract source path to resolve exactly in the declared outputs. Optional omitted inputs are allowed. A whole-value `=vars.<outputReferenceId>` or a resolved upstream reference inside `=js:` counts as bound only when Check 1 resolves its ID; it needs no Case-variable declaration.

Classify each missing required value before repair. An existing descriptor-defined input row with empty `value` is a binding defect. A completely absent descriptor row is a schema-emission defect; ordinary binding does not create it.

Skip only a genuine unresolved target: a non-connector placeholder emitted after its owner exhausted the precedence above, a Rule-17 placeholder trigger, a connector cache retained for audit but marked ineligible for enrichment, or a condition-rule stub left by the connector owner's fallback. Do not invent a universal missing-contract gate. A resolved owner whose selected current contract proves a required/emitted-field mismatch remains an error.

## Remediation decision table

| Finding | Exact choice/action | Continue rule |
|---|---|---|
| Check 1 unresolved read or declared binding with empty value | Ask: (a) select the intended existing ID/source from observed candidates and rewrite the sink; (b) remove/edit the consumer in the SDD and redispatch its owner; (c) build with best, preserving the value and logging its runtime-undefined risk. | Re-run Check 1 after (a)/(b); (c) may continue with an Open Item. |
| Check 1.5 metadata form | Rewrite `value` and `source` to the same canonical form. | Non-interactive; recheck once. |
| Check 2 true orphan | Ask: (a) add a producer on a named task, trigger, or connector rule using a real descriptor field; (b) add an Out Default; (c) recategorize as Variable or remove it; (d) build with best and log the empty runtime result. | Redispatch and rerun Checks 1–3 after (a)–(c); (d) may continue. |
| Check 2 missing companion or resolved-owner emission drift | Restore/revise the declaration, or re-run the selected producer owner once. | Blocking until consistent. |
| Check 3 descriptor mismatch | Run the Check 3 repair sequence above: capture old source IDs and consumers, re-emit from the selected current owner-contract leaf, capture new IDs/removals, redispatch affected declarative consumers, then run Step 11.5. | One automatic repair pass; rerun Checks 1, 3, and 4, and halt on any mismatch or stale reference. |
| Check 4 surviving marker | Ask: (a) correct the observed triple; (b) edit the SDD expression and redispatch its owner; (c) build with best, leave the token, and log that the expression throws. | Re-run Step 11.5 plus Check 4 after (a)/(b); (c) may continue. |
| Check 5 required input row exists with empty `value` | Ask: (a) bind a literal, Case variable, or observed upstream output; (b) mark `<UNRESOLVED>` with paired high review item; (c) build with best and log runtime-null risk. | Run the owner-appropriate binding route against the existing row, then rerun Checks 1 and 5. Owner hard gates still apply. |
| Check 5 required descriptor input row is absent | Restore the row through the selected task/trigger/rule schema-emission owner from its selected current contract source, copying the current fields and minting the owner-specific `id`/`var` and `elementId` shape. Then apply the preceding binding choices to that restored row. Ordinary binding never creates a missing schema row. | Run the schema-emission owner, then the owner-appropriate binding route, then Checks 1 and 5. Owner hard gates still apply. |
| Check 5 phantom extract | Ask: (a) select an exact available output and re-project it; (b) drop the extract row; (c) build with best and log runtime-null risk. | Re-run Checks 1, 3, and 5 after (a)/(b), plus Check 2 when the extract targeted an Out slot; a drop may create a true orphan. Choice (c) may continue. |

## Exact repair routing and Open Items

First classify the required-input defect. When the descriptor-defined row already exists with empty `value`, the selected binding owner may set only that row's value. When the row is absent, first re-run the selected task/trigger/rule schema-emission owner from its selected current contract source, preserving the current fields and generating that owner's `id`/`var` and `elementId` shape; ordinary binding must not mint or reconstruct schema rows.

After the row exists, route its value through the selected owner. For a non-connector input repair, update `tasks.md`, run its ordinary binding owner, and edit only that task. For a connector task, event trigger, or connector rule, update `tasks.md`, rebuild that target's `--input-details`, rerun its own `case spec`, replace its complete raw cache, pass the selected owner's post-spec gate, and splice through that owner. Never patch a cached CaseShape, send a connector repair through Step 9.8, or reuse a sibling cache.

A user-selected `<UNRESOLVED>` or best-effort branch does not bypass a connector hard gate: if the selected owner requires fallback, emit its canonical placeholder/stub and then treat that genuine unresolved owner under the skip rule. Do not invent a name-similar output or weaken a blocking Check 2/3 repair.

Every warning or build-with-best choice accumulates one check-local deduplicated Open Item in the in-reasoning issue list. Record check number, owner and scope, exact sink/source, observed candidates or descriptor mismatch, runtime consequence, user choice, and the precise repair needed. Do not render or count Open Items here; the already-loaded Step-12 case-validation owner is the sole dump/render/count owner. Do not repeat prompt transcripts or create separate templates per check.

<!-- END: validation-guide.md -->

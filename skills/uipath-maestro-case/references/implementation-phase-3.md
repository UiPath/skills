<!-- Split out of implementation.md so each phase file can be read whole. Phase 2 is in [implementation.md](implementation.md); Phase 4-7 in [implementation-phase-4-7.md](implementation-phase-4-7.md). -->

# Phase 3 — Implementation (Steps 9.6 – 11.5)

Execution order: 9.6 → 9.65 → 9.7 → 9.8 → 10.5 → 11.5 → 12. Phase 3 wires connector task schemas, input/output values, resolved connector-rule configuration, and in-expression markers. Conditions and SLA already exist from Phase 2. Full contract in [phased-execution.md § Phase 3](phased-execution.md#phase-3--implementation).

## Step 9.6 — Phase 3 re-entry

Before any Phase 3 mutation:

1. **Re-read `tasks.md`** — per Rule 7 of `SKILL.md`.
2. **Re-read `caseplan.json`** — rebuild name → ID maps from authoritative artifact. See [phased-execution.md § Re-entry protocol](phased-execution.md#re-entry-protocol) for which fields to index.
3. **Seed Phase 3 progress todos** — call TodoWrite with the section-level items below. Mark each `in_progress` on entry, `completed` on exit. Phase 2 todos (if any) are stale — replace, do not append.

   **If your harness has no TodoWrite tool, the step list is still binding.** It is the phase's execution order, not bookkeeping: without it the tail of the phase — Step 11.5 and the Step 12 checks — is what gets dropped, and both are things `uip maestro case validate` cannot see. Keep the list explicitly and run every item through Step 12's verification commands before declaring Phase 3 done.
   1. Read the Phase 3 manifest (Step 9.65)
   2. Wire connector task schemas (Step 9.7)
   3. Bind task I/O values (Step 9.8)
   4. Upgrade resolved connector-bound condition rules (Step 10.5)
   5. Resolve in-expression `vars.$xref` markers (Step 11.5)

   Inside each section, also seed per-T-entry sub-items (one per T-entry that section will Edit). Mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit returns success. Per-T-entry items are the audit trail under the per-section batched contract (per [case-editing-operations.md § Per-section batch write contract](case-editing-primitives.md#per-section-batch-write-contract--canonical)).

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

## Step 9.65 — Phase 3 read manifest (mandatory, before any write)

Phase 3 crosses a hard stop, so its manifest is read fresh here even when Phase 2 read the same file — a Phase 2 read does not survive the boundary. Derive the list from `sdd.md` and the just-re-read `caseplan.json`, read every file on it, then start Step 9.7.

**Step 1 — derive.** Derive from `sdd.md` and the just-re-read `caseplan.json`, exactly as [Step 5.9](implementation.md#step-59--phase-2-read-manifest-mandatory-before-any-write) does; `tasks/tasks.md` is read as well when present, but is never required. Collect three facts:

1. Whether any task is typed `execute-connector-activity` or `wait-for-connector`.
2. Whether any condition rule uses `wait-for-connector`.
3. Whether any task declares Inputs or Outputs rows — in practice every build does.

**Step 2 — build the manifest.**

Fixed core — always on the manifest:

- [`case-editing-primitives.md`](case-editing-primitives.md)
- [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md) — carries both the `=vars.<id>` write form for Step 9.8 and the `vars.$xref` resolution algorithm for Step 11.5
- [`plugins/variables/bindings/impl-json.md`](plugins/variables/bindings/impl-json.md)
- [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md)
- [`bindings-and-expressions.md`](bindings-and-expressions.md)
- [`bindings-v2-sync.md`](bindings-v2-sync.md)

Add, when Step 1 found any connector task or any `wait-for-connector` rule:

- [`connector-trigger-impl.md`](connector-trigger-impl.md)
- [`case-spec-input-details.md`](case-spec-input-details.md)
- [`plugins/tasks/connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md) — per connector-activity task
- [`plugins/tasks/connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md) — per `wait-for-connector` task or rule

**Step 3 — read.** Read every manifest file in full, to its `<!-- END: … -->` marker, per Rule 24 of `SKILL.md`. Read them as one batch before Step 9.7; do not interleave manifest reads with writes.

**The manifest is a floor, never a ceiling.** It is the minimum set this build cannot be correct without. It is not the complete list of what you may need, and finishing it does not mean you are done reading. Whenever a step, a plugin, or an SDD row references a shape or procedure you have not read, read that file too — the manifest never overrides Rule 24. A build that reads only the manifest and nothing else has under-read.

**Exact paths, not directories.** Each manifest entry names one file. `planning.md` and `impl-json.md` are different documents with different content, and reading the sibling does NOT satisfy the entry: `plugins/variables/global-vars/planning.md` does not satisfy `plugins/variables/global-vars/impl-json.md`. Planning references describe what to decide; `impl-json.md` carries the JSON shape you are about to write. Check each entry off by its full path.

**Phase 3 is not complete until all four of these hold** — none is checked by `uip maestro case validate`, and each corresponds to a manifest file above:

| Must hold at Phase 3 exit | Written by | Manifest file |
|---|---|---|
| Every task **input** reference is `=vars.<outputReferenceId>` — on inputs the `vars.` prefix is required, and a bare `=<id>` there is wrong | Step 9.8 | `io-binding/impl-json.md` |
| Every **output** `target` is `=<id>` with **no** `vars.` prefix, and a bare auto-mint output's `value` is the bare `<id>` with no `=` — the input rule above does not apply to outputs | Step 9 / 9.7 | `io-binding/impl-json.md` § Output Binding Shapes |
| Zero `vars.$xref(` markers remain anywhere in `caseplan.json` | Step 11.5 | `io-binding/impl-json.md`, `bindings-and-expressions.md` |
| `bindings_v2.json` carries a `resources[]` key for every resolved resource task | Step 9.7 Phase C | `bindings-v2-sync.md` |
| Every formal argument has a non-null `var` and a synthetic `id` | Step 12 Check 10 | `global-vars/impl-json.md` |

**Step 4 — gate.** Do not enter Step 9.7 until every manifest file has been read to its END marker in this session. Walk the manifest entry by entry and confirm each exact path was read. Connector schema and I/O binding are the two places where a partial read produces a caseplan that validates and is still wrong — `validate` checks neither `caseShape.context` completeness nor cross-task output reference IDs, and it does not check that Step 11.5 resolved every `vars.$xref` marker or that `bindings_v2.json` carries a key for every resource task.

## Step 9.7 — Connector task detail (gather-then-write)

**Phase A — gather.** For each connector task (`connector-activity`, `connector-trigger`) in `tasks.md`:

1. Run `get-connection` (each task runs its own — never reuse).
2. Run `uip maestro case spec --type <activity|trigger> --activity-type-id <id> --connection-id <id> --input-details '<json>' --output json` per the plugin's `impl-json.md`.
3. Substitute `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders in `caseShape.context[*].value` with minted binding ids; mint `var` / `id` / `elementId` on `caseShape.inputs` / `outputs` per the plugin's uniqueness rule.

Hold all gathered shapes (per-task `caseShape` + root-level Connection + FolderKey bindings) in reasoning. Skip connector tasks that are placeholders (unresolved `typeId` / `connectionId`).

**Phase B — batched write.** One Read of `caseplan.json`. Then for each gathered task: one Edit setting `data.context = caseShape.context`, `data.inputs = caseShape.inputs`, `data.outputs = caseShape.outputs` plus the matching root-level Connection + FolderKey binding entries. Skip the re-Read between sibling Edits.

**Phase C — sync + validate.** Populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Regenerate `bindings_v2.json` once per [bindings-v2-sync.md § Regenerate](bindings-v2-sync.md) — single pass includes non-connector bindings from Step 9 and Connection bindings from this step. Run validate.

On context-compaction mid-gather: re-Read `caseplan.json`, scan for connector tasks without `data.context` populated, re-run Phase A for those only.

## Step 9.8 — Bind task input/output values (per-task Edit batch)

One Read of `caseplan.json` at Step 9.8 entry. Then **one Edit per task** replacing that task's full `data.inputs` array. Skip the re-Read between sibling Edits. Skip placeholder tasks entirely — they have no inputs.

Per-task composition (in reasoning, before that task's Edit) per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md):

1. Literals / expressions (`input = "<value>"`): write `<value>` to `input.value`.
2. Cross-task references (`input <- "Stage"."Task".output`): resolve the source output reference ID from the just-Read `caseplan.json` using [`io-binding/impl-json.md` § Output reference ID](plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative), then write `=vars.<outputReferenceId>` to the target input's `value`.

If a cross-task reference points to a task that does not exist in the just-Read `caseplan.json`, halt — `tasks.md` ordering is wrong; report to the user.

One validate at section end.

## Step 10.5 — Upgrade connector-bound condition-rule stubs (gather-then-write)

Read `caseplan.json` and scan all four condition scopes for `wait-for-connector` rules whose `uipath.context` still contains the canonical `connectorKey: "placeholder"` and `operation: "placeholder"` entries. Match each rule to its `tasks.md` connector fields through its Phase 2 `id-map.json` entry.

For each matched rule whose connector resolved in planning, run the connector-trigger `case spec --type trigger --input-details` procedure, mint its output IDs/element IDs, and gather its root Connection/Folder bindings. Then Edit **only that rule's `uipath` block**. Preserve the enclosing condition array plus the rule's `id`, `rule`, `conditionExpression`, scope, and placement. Apply declared rule-output bindings after the real outputs exist.

**Verify the upgrade ran, with a command.** `case spec` is the only source of a real `caseShape.context`, and a hand-composed context looks plausible and passes `validate` — the doc's own caveat is that validate does not check `uipath` internals. The tell is the connector's **Activity Type ID**: it appears in a spec-derived context and in nothing an agent writes from the SDD alone.

```bash
cat <Solution>/<Project>/caseplan.json | python3 -c '
import json,sys,re
p=json.load(sys.stdin)
for n in (p.get("nodes") or p.get("schema",{}).get("nodes") or []):
    d=n.get("data") or {}
    for c in (d.get("entryConditions") or [])+(d.get("exitConditions") or []):
        for grp in c.get("rules") or []:
            for r in grp:
                if r.get("rule")=="wait-for-connector":
                    u=json.dumps(r.get("uipath") or {})
                    ids=re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",u)
                    print(d.get("label"), r.get("id"), "placeholder" if "\"placeholder\"" in u else "resolved", "uuids:", len(set(ids)))'
```

A resolved rule carries **at least two distinct UUIDs** — its connection id and its activity type id. One UUID means the connection was bound but the activity type never arrived, which is exactly what a skipped `case spec` produces. Cross-check each against the SDD's `Activity Type ID` for that operation.

If the connector is `<UNRESOLVED>` or `case spec` fails, leave the stub unchanged, log it, and list it in the completion report. After all successful upgrades, populate the IS cache and regenerate `bindings_v2.json` once. Re-scan: every resolved rule must be free of `"placeholder"`; any remaining stub must map to a reported unresolved connector. Full procedure and scope-specific `elementId` rules: [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule).

## Step 11.5 — Resolve in-expression `vars.$xref` markers (whole-file pass)

Runs after bindings (9.8) and connector-rule upgrades (10.5), when every task / trigger / rule output is minted and deduped. Conditions and SLA were already written in Phase 2. Resolve every `vars.$xref('Stage','Task','output')` marker in `caseplan.json` in ONE pass: one Read, then Edit each string value holding a marker — resolve the source through the common output-reference-ID algorithm and substitute bare `vars.<outputReferenceId>` (no leading `=`; the marker already sits inside `=js:`). Sink-blind: covers composite input payloads, `conditionExpression`, SLA `expression`, computed `=` outputs, and connector body fields in one place. An unresolved name-triple or reference ID is an ERROR (Check 4 below). Algorithm + pseudocode: [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md#in-expression-marker-resolution-step-115). One validate at section end.

**Verify with a command, not from memory.** `validate` does not check this, so run:

```bash
grep -c '\$xref(' <Solution>/<Project>/caseplan.json
```

It must print `0`. A non-zero count means this step did not finish — resolve the survivors and re-run it. Do not enter Phase 4 on a non-zero count. This is the same assertion as Step 12 Check 4; running it here catches the omission at the step that causes it.

## Step 12 — End-of-Phase-3 validator pass

> **Algorithm reference:** the per-check pseudocode + AskUserQuestion prompt templates + skill-response-per-pick details all live in [`plugins/variables/io-binding/impl-json.md § Binding Procedure`](plugins/variables/io-binding/impl-json.md#binding-procedure). This step is the orchestration hook; that doc is the algorithm. When in doubt, follow the impl-json doc.

After value bindings (Step 9.8), connector-rule upgrades (Step 10.5), and marker resolution (Step 11.5), invoke the end-of-Phase-3 validator — Checks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15. Phase 2 conditions and SLA remain in place throughout.

- **Check 1** — Resolve every `=vars.X` reference against `variables.{inputs, inputOutputs}[].id`. Scan all task input `value` fields, entry/exit condition expressions (stage and task), case-exit and trigger rule expressions, SLA expressions, and `=js:` expressions anywhere they appear. On unresolved → **AskUserQuestion** offering: (a) name the intended variable, (b) remove the reference, (c) continue with best-effort emit (entry logged under Open Items, runtime returns undefined).
- **Check 2 — Out-arg producer presence** — For every formal Out-arg in `variables.outputs[]`, verify the producer/Default situation per [`io-binding/impl-json.md` § Check 2](plugins/variables/io-binding/impl-json.md):
  - **Has Default but no companion** → AskUserQuestion.
  - **No Default + producer declared in SDD on a Rule 17 placeholder task** (declared-but-unresolvable) → no prompt; silent log to `## Open Items for User` in `tasks/build-issues.md`. Rule 17 already prompted the author for this task.
  - **No Default + no producer declared anywhere (pure orphan)** → AskUserQuestion offering 4 options: (a) add producer task output, (b) add Default value, (c) recategorize as Variable / remove, (d) continue with best-effort emit (entry logged under Open Items).
- **Check 3** — Type mismatch between `=vars.X` reference and consumer slot → log WARN inline (non-blocking; string coercion is runtime-tolerant).
  - **Check 4 — No surviving `$xref` markers** — Scan every string value in `caseplan.json` for the literal `$xref(`. Step 11.5 resolves all; any survivor means its name-triple or output reference ID failed — the same class of failure as a Check 1 unresolved `=vars.X`, so it gets the same interactive remediation. On unresolved → **AskUserQuestion** (present the outputs that DO exist on the named task as candidates): (a) name the intended source output — skill rewrites the triple, re-resolves, substitutes `vars.<outputReferenceId>`; (b) edit the SDD expression + re-run the Phase 1 dispatcher (when the output genuinely doesn't exist); (c) continue with best-effort emit (token left unsubstituted, entry logged under Open Items; `vars.$xref(...)` throws at runtime until fixed). Detail: [`io-binding/impl-json.md` § Check 4](plugins/variables/io-binding/impl-json.md).
  - **Check 5 — Resolved-resource I/O completeness** — For each task with a persisted contract in `tasks/registry-resolved.json`, verify every **required** declared input has a bound `value` and every extract output `Field` exists in the resolved output contract. An upstream-output-fed input (`=vars.<outputReferenceId>` / resolved `$xref`) counts as bound with NO §1.5 row. On unbound-required-input or phantom-output-field → **AskUserQuestion**: (a) bind / re-point, (b) `<UNRESOLVED>`+review-item / drop row, (c) continue with best-effort emit (entry logged under Open Items; runtime null until fixed). Tasks with no contract (placeholder / `<UNRESOLVED>`) are skipped. Detail: [`io-binding/impl-json.md` § Check 5](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness).
- **Check 6 — Entry-point schema parity** — Verify every `entry-points.json` entry's `input`/`output` matches the In/Out args projected at Step 6.3 (keys, type mapping, `required`, `file`/`jsonSchema` shapes), plus unique `filePath` fragments and no orphaned `inputs[].elementId`. **Non-interactive:** on mismatch re-run the Step 6.3 refresh once; if still divergent (or a uniqueness/orphan finding) log to `## Open Items for User` and continue. No AskUserQuestion. Algorithm: [`entry-points-sync.md § Check 6`](entry-points-sync.md#check-6--entry-point-schema-parity-step-12-validator).
- **Check 7 — Bindings sidecar parity** — Compare `bindings_v2.json.resources[]` with the complete projection of top-level `caseplan.json.bindings[]` using [`bindings-v2-sync.md`](bindings-v2-sync.md). If they differ — including non-empty bindings with empty resources — regenerate the full sidecar once and re-check. If they still differ, halt before Phase 4. This check is non-interactive.
- **Check 8 — Global generated-output ID uniqueness** — Read the completed `caseplan.json` and build one owner-keyed uniqueness pool from root variables plus every task, trigger, and connector-rule output across all condition scopes. Include unused and schema-generated outputs such as `Error` and `response`. Apply the [global uniqueness rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule): on collision, suffix the later producer, update only that producer's fields and consumers by producer ownership, then re-run the affected binding and marker-resolution steps. Re-read and re-scan the complete pool; halt before Phase 4 if any duplicate generated `id` or `var` remains. `uip maestro case validate` success does not satisfy this check.
- **Check 9 — Resolved-resource emission and repair preservation** — Read `tasks/registry-resolved.json`, `tasks.md`, `caseplan.json`, and `bindings_v2.json`. For every registry entry with a non-null `selected`, locate its declared `(stage, task)` in `caseplan.json`. The task MUST exist and MUST NOT have `data: {}`. For non-connector task types, `data.name` and `data.folderPath` MUST each be `=bindings.<id>` references to complete root binding entries (all required fields present) — Check 7 covers their projection into `bindings_v2.json.resources[]`. A selected resource is never eligible for a placeholder fallback. Repair only the named task/binding with a targeted Edit per the repair-preservation contract in [`case-editing-operations.md § Per-section batch write contract`](case-editing-primitives.md#per-section-batch-write-contract--canonical) — never by rewriting the file; a dropped stage, task, root binding, or selected-resource task is a hard failure. Then repeat Checks 7 and 9. Do not enter Phase 4, report completion, or downgrade this finding to an Open Item while it remains unresolved; `uip maestro case validate` success does not satisfy this check.
- **Check 10 — Formal-arg slot ID format** — For every entry in `variables.inputs[]` and `variables.outputs[]`, verify `id` matches `^v[A-Za-z0-9]{8}$` per [`global-vars/impl-json.md` § Formal-arg slot ID format](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format). The most common violation is copying the human-readable companion name into the formal slot (e.g. `variables.inputs[].id: "applicantName"` instead of `"vK3mNp9Qx"`) — `uip maestro case validate` does not catch this, so it silently produces a case whose BPMN packaging can reject the id. **Non-interactive repair:** mint a replacement `v`+8-chars id, deduplicated against the Check 8 global pool; update the `variables.inputs[]`/`variables.outputs[]` entry's `id` to the new value; for an `inputs[]` (In-arg) entry, also find its bound trigger node's `data.inputs.outputs[]` bridge entry whose `source == "=vars.<old id>"` and rewrite it to `"=vars.<new id>"` (skip this sub-step when the bound trigger is a placeholder — no bridge was ever written, per [global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md#in-argument)). Leave `name`, `var`, and the `inputOutputs[]` companion's `id` unchanged — only the formal slot's `id` (and, for In-args, the bridge's `source`) are rewritten. Re-scan `variables.inputs[]`/`variables.outputs[]` after repair; halt before Phase 4 if any entry still fails the format after one repair pass.
- **Check 11 — resourceKey self-consistency (non-connector tasks)** — For every top-level `bindings[]` pair sharing a `resourceKey` on a non-connector task (`process`, `agent`, `rpa`, `api-workflow`, `case-management`, `action`), verify `resourceKey` is internally consistent with the pair's own `default` fields per [`bindings/impl-json.md` § resourceKey construction](plugins/variables/bindings/impl-json.md#resourcekey-construction--non-connector-tasks): normally `resourceKey == "<folderPath-binding default>.<name-binding default>"`; for an inline-built sibling (agent/api-workflow whose `folderPath` binding `default` is `""`), `resourceKey == "solution_folder.<name-binding default>"` instead. The most common violation is copying a tenant identity value — the SDD's "Resource Identity" column, a `tasks describe --id` argument, or a registry `entityKey` — directly into `resourceKey` instead of constructing the composite string. `uip maestro case validate` does not catch this: it silently produces an unresolvable process reference that only faults at `case debug`. **Non-interactive repair:** recompute the correct `resourceKey` from the pair's own `default` fields and rewrite both bindings in the shared pair (a pair's two `resourceKey` values must stay identical), then re-run Check 7 to resync `bindings_v2.json`. Re-scan `bindings[]` after repair; halt before Phase 4 if any pair still fails after one repair pass.
- **Check 12 — Connector node resolution completeness** — Checks 9 and 11 exempt connector nodes; this check covers them. Read `tasks/registry-resolved.json` and `caseplan.json`. Enumerate every **connector node**: tasks typed `wait-for-connector` / `execute-connector-activity`, the case-level `Intsvc.EventTrigger` node, and every `wait-for-connector` rule across all 4 condition scopes (stage-entry / stage-exit / task-entry, plus case-exit under `metadata.caseExitRules`). For each whose registry entry has a **non-null `selected`** — i.e. the connector resolved in planning — verify its connector block (`data` for a task, `data.inputs` for a trigger node, `uipath` for a rule):
  1. `context` is present and non-empty. A block carrying only `serviceType` + `typeId` + `connectionId` is the Phase 2 / `case spec`-failed shape ([connector-trigger/impl-json.md § Graceful degradation](plugins/tasks/connector-trigger/impl-json.md#graceful-degradation)) and is a **failure** here — the spec call succeeded, so the populated `caseShape` must be spliced in.
  2. `context[name="connectorKey"].value` equals `selected.connectorKey`, and a `context[name="connection"]` entry exists whose `value` is `=bindings.<id>`.
  3. No `"placeholder"` values anywhere in `context` (legal only for a genuinely unresolved connector, which by definition has `selected: null`), and no residual `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` / `{{TRIGGER_REGISTRATION_KEY}}` token anywhere in the node.
  4. Every `=bindings.<id>` referenced by the block resolves to a complete entry in top-level `caseplan.json.bindings[]` (ConnectionId + FolderKey, the latter omitted only when `spec.connection.folderKey` was null).
  5. The node's spec-cache artifact exists — `tasks/spec-cache.<elementId>.json` for tasks and rules, or this trigger's T-number entry in `tasks/trigger-spec-cache.json` for the case-level event trigger — and its cached `Context` matches the written `context` modulo the placeholder substitutions in (3) and the key re-casing in [connector-trigger-impl.md § Normalize key casing](connector-trigger-impl.md#normalize-key-casing-pascalcase--camelcase). A mismatch means the context was composed from agent memory rather than spliced — forbidden per [connector-trigger-impl.md § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext).

  **Non-interactive repair:** re-run `case spec --type trigger` (or `--type activity`) for the failing node, persist the response to its spec-cache file, splice `context` / `inputs` / `outputs` verbatim per [connector-trigger-impl.md § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext) and [§ Step 5](connector-trigger-impl.md#step-5--mint-var--id--elementid-on-inputs-and-outputs), append the missing root bindings per [§ Root-level bindings](connector-trigger-impl.md#root-level-bindings), then re-run Check 7 to resync `bindings_v2.json`. Re-scan after repair; halt before Phase 4 if any resolved connector node still fails after one repair pass. If `case spec` itself fails on the retry, keep the degraded shape, log it under `## Open Items for User` as **"connector node <name> is not runnable — `context` unresolved"**, and report it — do not silently emit it as complete. `uip maestro case validate` success does not satisfy this check: it reports `Valid` for a connector task with an empty `context` and no root bindings.

- **Check 13 — Rule selector integrity (task and stage references)** — Enumerate every rule across all 4 condition scopes (stage-entry / stage-exit / task-entry, plus case-exit under `metadata.caseExitRules`) whose rule type requires a task selector (`selected-tasks-completed`). Each MUST carry a non-empty `selectedTasksIds` array in which every id resolves to a task in the owning stage, and each resolved task MUST have no `adhoc` entry rule. **Non-interactive repair:** resolve missing ids from the rule's T-entry `selected-tasks-ids` names via `tasks/id-map.json` using EXACT `tasks.md` display names (paraphrased or shortened names are the common miss — match the task's exact name, per the conditions plugins' selector contract); rewrite the rule, re-scan. If any resolved task is adhoc, stop and return to the plan: required routing cannot depend on optional user-launched work, and replacing the selector without redesigning that route is forbidden. Unresolvable after one pass → **AskUserQuestion** (name the intended task / repair the plan / continue with best-effort emit, logged under Open Items). Halt before Phase 4 while any selector is empty with no user decision or selects an adhoc task; build-with-best does not waive the adhoc restriction. `uip maestro case validate` reports empty selectors as `... has no task(s) selected` but does not enforce the adhoc restriction, so a clean validate is not evidence this check passed. **Stage references too:** in the same pass, every `exitToStageId` and every `selectedStageId` (`selected-stage-completed` / `selected-stage-exited`) MUST resolve to an existing `case-management:Stage` node `id`; repair identically, re-resolving the T-entry's `exit-to-stage` / `selected-stage` name through `tasks/id-map.json`.

- **Check 14 — Variable `default` encoding** — Scan `variables.inputs[]`, `variables.outputs[]`, and `variables.inputOutputs[]`. Every entry carrying a `default` MUST hold a **JSON string**, whatever the entry's `type`. An object or array `default` is **silently deleted** by the caseplan → BPMN converter (`bpmn-moddle.ts` keeps only primitive attributes), leaving the variable null at runtime; the first task bound to it fails with `AGENT_STARTUP.INPUT_VALIDATION_ERROR / <input> Field required`. Numbers and booleans survive serialization but violate the field's declared string type and are equally non-conforming.

  **Nothing upstream catches this.** `uip maestro case validate` returns `Valid`; the frontend's own Zod schema types the field `z.any()` and parses an object clean, so borrowing it as a gate does not work here. The enforcement point is [`global-vars/impl-json.md` § `default` encoding](plugins/variables/global-vars/impl-json.md#default-encoding-every-type-mandatory) and this check.

  **Non-interactive repair:** re-encode in place — `{"a":1}` → `"{\"a\":1}"`, `5` → `"5"`, `true` → `"true"` (lowercase JSON, not Python `True`), `{}` → `"{}"`. Do not drop the value and do not change the variable's `type`. Re-scan once; halt before Phase 4 if any non-string `default` remains.

- **Check 15 — Every task carries a non-empty entry rule** — Enumerate every task across `data.tasks` in every stage, all classes, with **no exemptions**: placeholder tasks (Step 9.1: they "integrate with the rest of the graph" via normal task-entry conditions) and connector tasks are included; a manually-triggered task still needs its own `adhoc` entry rule (SKILL.md Rule 6). Each task's top-level `entryConditions` MUST be a non-empty array whose first element has a non-empty `rules[][]`. **`uip maestro case validate`'s "Task has no entry rules" finding is a warning, not an error — a clean `Valid` result is not evidence this check passed.** An empty `entryConditions` means the runtime never tells that task to start; the task never runs, its stage's exit condition can never be satisfied, and `uip maestro case debug` hangs indefinitely rather than faulting — worse than most Step 12 findings since it surfaces only as a live-debug timeout, not a build-time error.
  **Non-interactive repair, in order:**
  1. Look up the task's `tasks.md §4.6` T-entry. If it carries a recorded `entry-rule:` (mandatory per SKILL.md Rule 6's `activation-mode:`/`entry-rule:` lines), reconstruct the condition object from that value using the shapes in [`task-entry-conditions/impl-json.md § Rule Types`](plugins/conditions/task-entry-conditions/impl-json.md#rule-types) and append it.
  2. If `tasks.md` has no recorded entry rule for that task — a Phase 1 planning gap, not just a missed Phase 3 write — fall back to the task's matching `##### Task N.M` section in the source SDD and reconstruct from its **Entry Condition** table instead. Do not substitute a `current-stage-entered` default when the SDD specifies something else (`runs-sequentially`, `adhoc`, `selected-tasks-completed`, `wait-for-connector`, `sla-status-change`) — use it only when the SDD specifies it.
  3. If NEITHER `tasks.md` nor an accompanying SDD records an entry rule for the task (no SDD in this build, or a brownfield edit predating one) — **AskUserQuestion**: (a) name the intended entry rule, (b) default to `current-stage-entered` (stage-start, parallel) and log an Open Item. **Option (c) "continue with best-effort emit" is not offered for this check** — an empty `entryConditions` is not a partial or degraded result, it is a task that can never execute, so the agent must pick (a) or (b).
  Re-scan every task after repair; halt before Phase 4 if any task's `entryConditions` is still empty after one repair pass. This check is the mandatory backstop for Step 10 (`plugins/conditions/task-entry-conditions/impl-json.md § Post-Write Verification` only confirms count-parity against `tasks.md`, which is not a safety net when `tasks.md` itself never recorded the condition) — do not treat Step 10 having run as sufficient evidence this check passes.

**Build-with-best policy:** for any user pick of "continue with best-effort emit" on a Check 1, Check 2, Check 4, Check 5, or Check 13 AskUserQuestion, append a `## Open Items for User` entry to `tasks/build-issues.md` and proceed to Phase 4. Checks 14 and 15 have no best-effort escape — a deleted default or a task with no entry rule is not a partial result. AskUserQuestion is the surface; build-with-best is the escape. The skill conservatively emits what it has; Phase 4 validate stays green (structural validity is intact); runtime concerns are listed for pre-publish review.

**Reporting:** at end of Phase 4, count entries in the `## Open Items for User` section of `tasks/build-issues.md` (read the file after writing). If count > 0, the completion report MUST include a literal line of the form:

```
Open Items: <N> entry/entries — review tasks/build-issues.md § Open Items for User before publishing.
```

(Use `entry` for N == 1, `entries` otherwise.) Place this line above the per-stage / per-task summary in the completion report so it's not buried.

End of Phase 3 mutations. Proceed directly to Phase 4 — no hard stop between Phase 3 and Phase 4.

---

---

**Continues in** [implementation-phase-4-7.md](implementation-phase-4-7.md) — Phase 4 validate, Phase 5 publish, Phase 6 debug, Phase 7 Orchestrator. **Preceded by** [implementation.md](implementation.md) (Phase 2).

<!-- END: implementation-phase-3.md -->

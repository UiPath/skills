# End-of-Phase-3 Case Validation

Read this guide only when Step 12 starts, after all Phase 3 mutations and the Step 11.5 whole-artifact marker pass. The Step 12 implementation route has already loaded the separate I/O exit owner for Checks 1–5; this guide does not discover or duplicate it.

## Ordered orchestration

Run Checks 1 through 12 in numeric order, with Check 1.5 immediately after Check 1. Phase 2 conditions and SLA remain in place. Checks 1–5 use the separately loaded canonical algorithms and remediation table. Do not advance past an unresolved blocking result or substitute `uip maestro case validate` for a semantic check.

Checks 6–12 run as follows.

## Check 6 — Entry-point schema parity

Use the canonical [Step 12 entry-point parity owner](entry-points-sync.md#check-6--entry-point-schema-parity-step-12-validator). Verify every `entry-points.json` entry's input/output projection against the Step 6.3 In/Out arguments: keys, type mapping, `required`, file and `jsonSchema` bodies, per-trigger distribution, unique `filePath` fragments, and no orphaned `inputs[].elementId`.

This check is non-interactive. On mismatch, run the Step 6.3 refresh once and recheck. If parity still differs, or uniqueness/orphan findings remain, accumulate one deduplicated Open Item in the in-reasoning issue list and continue; do not ask or repeat the refresh.

## Check 7 — Bindings sidecar parity

Use the complete projection and regeneration contract in the [bindings sidecar owner](bindings-v2-sync.md). Compare all top-level `caseplan.json.bindings[]` with `bindings_v2.json.resources[]`; non-empty bindings with an empty resource array is a mismatch.

Regenerate the full sidecar once and recheck. If it still differs, halt before Phase 4. Never patch a partial resource subset.

## Check 8 — Global generated-output ID uniqueness

Use the [global uniqueness rule and complete pool](plugins/variables/global-vars/impl-json.md#uniqueness-rule). Build one owner-keyed pool from root variables and every task, trigger, and connector-rule output in stage-entry, stage-exit, task-entry, and case-exit scopes. Include unused/schema-generated outputs such as `Error` and `response`, while honoring placeholder/stub skips and the controlled equal-name alias.

For each real collision, suffix the later independently owned producer and update only that producer's owned fields and consumers. Re-run the affected binding and Step 11.5 marker-resolution work, then re-read `caseplan.json` and perform one complete pool rescan. Halt if any duplicate generated `id`/`var` remains; structural CLI validation is not a substitute.

## Check 9 — Resolved-resource emission and preservation

Match each exact `(stage, task)` in `tasks/registry-resolved.json` using the [registry audit contract](registry-discovery.md#registry-resolvedjson-content-discipline). Every entry with non-null `selected` must have a real task in `caseplan.json`, never `data: {}`. For non-connectors, `data.name` and `data.folderPath` must reference complete root bindings; Check 7 owns their sidecar projection. A selected resource is never eligible for placeholder fallback.

Any repair must obey the [per-section preservation contract](case-editing-operations.md#per-section-batch-write-contract--canonical). Edit only the named task/binding; a dropped stage, sibling task, root binding, or selected-resource task is a hard failure. After the targeted repair, repeat Check 7 and then Check 9. Halt, do not report completion, and do not downgrade to an Open Item while either still fails.

## Check 10 — Formal-argument slot IDs

Use the [formal-slot ID owner](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format). Every `variables.inputs[].id` and `variables.outputs[].id` must match `^v[A-Za-z0-9]{8}$`.

Repair non-interactively once: mint a globally deduplicated `v`+8 ID and change only the formal slot. For an In argument, also rewrite the bound trigger bridge in `node.data.inputs.outputs[]` whose `source == "=vars.<old id>"`; a placeholder trigger has no bridge and is skipped. Preserve `name`, `var`, and the human-readable `variables.inputOutputs[].id`. Re-scan both formal arrays and halt if any entry remains invalid after that one pass.

## Check 11 — Non-connector `resourceKey` consistency

Use the canonical [non-connector resourceKey construction](plugins/variables/bindings/impl-json.md#resourcekey-construction--non-connector-tasks). For every shared binding pair on `process`, `agent`, `rpa`, `api-workflow`, `case-management`, or `action`, require both entries to carry the same value derived from their own defaults:

- normal resource: `<folderPath default>.<name default>`;
- inline-built agent/API sibling whose folder default is empty: `solution_folder.<name default>`.

A registry identity, entity key, or `tasks describe --id` argument is not a `resourceKey`. Repair non-interactively once by recomputing the value and rewriting both entries in the pair, then run Check 7 and re-scan Check 11. Halt if either parity or consistency still fails.

## Check 12 — Connector node resolution completeness

Read `tasks/registry-resolved.json` and `caseplan.json`. Enumerate every connector node: `wait-for-connector` and `execute-connector-activity` tasks, the case-level `Intsvc.EventTrigger` node, and every `wait-for-connector` rule across stage-entry, stage-exit, task-entry, and case-exit scopes. For each node whose registry entry has non-null `selected`, verify:

1. Its connector block (`data`, trigger `data.inputs`, or rule `uipath`) has non-empty `context`; a `serviceType` + `typeId` + `connectionId`-only Phase 2/degraded block fails.
2. `context[name="connectorKey"].value` equals `selected.connectorKey`, and `context[name="connection"].value` is an `=bindings.<id>` reference.
3. No `"placeholder"` value or unresolved connector/folder/registration placeholder token remains.
4. Every referenced binding ID resolves to a complete top-level ConnectionId or optional FolderKey binding.
5. The target's complete raw response exists at `tasks/spec-cache.<elementId>.json`; for an event trigger, its T-number entry also exists in `tasks/trigger-spec-cache.json`. Cache `Data.CaseShape.Context` must match written `context` modulo permitted placeholder substitutions and recursive key re-casing.

Repair non-interactively once: rerun the failing target's own `case spec`, immediately replace its full raw cache, Read and splice its complete `Context`, `Inputs`, and `Outputs` through the selected target owner, append missing root bindings, then run Check 7 and re-scan Check 12. If the retry spec call fails, preserve the degraded shape, record that the connector node is not runnable, and report it; never present it as complete. Any remaining completeness mismatch blocks Phase 4, regardless of structural CLI validation.

## Repair and halt order

Use this dependency order after a repair; do not restart unrelated discovery:

| Repair source | Required recheck sequence | Phase 4 gate |
|---|---|---|
| Checks 1–5 | Follow the separately loaded I/O owner's exact bounded sequence. | Honor that owner's blocking/build-with-best result. |
| Check 6 | Step 6.3 refresh → Check 6, once. | Residual is an Open Item; non-blocking. |
| Check 7 | Full sidecar regenerate → Check 7, once. | Residual blocks. |
| Check 8 | Affected output owner/binding → Step 11.5 → complete Check 8 rescan. | Residual blocks. |
| Check 9 | Targeted task/binding edit → Check 7 → Check 9. | Either residual blocks. |
| Check 10 | Formal slot and optional trigger-bridge edit → Check 10 rescan, once. | Residual blocks. |
| Check 11 | Rewrite both binding entries → Check 7 → Check 11 rescan, once. | Either residual blocks. |
| Check 12 | Target-local spec/cache/splice repair → Check 7 → Check 12 rescan, once. | Residual blocks; a failed spec retry is reported as not runnable. |

Do not enter Phase 4 while a blocking Check 1–5 result, Check 7 parity, Check 8 duplicate, Check 9 emission/preservation fault, Check 10 format fault, Check 11 consistency fault, or Check 12 connector completeness fault remains.

## Build-with-best and Open Items

Build-with-best is available only when the user explicitly selects it from a Check 1, 2, 4, or 5 choice. Accumulate one deduplicated Open Item in the in-reasoning issue list, preserve the emitted artifact, and continue after that check's owner permits it. Do not write `tasks/build-issues.md` before the canonical Phase-4 dump. This escape never downgrades Check 3 or Checks 7–12, and it never bypasses a connector hard gate.

Check 2's declared-but-unresolved owner warning and Check 6's residual parity finding also accumulate Open Items without another prompt. Each item records the check, owner/scope, exact source or sink, observed state, runtime consequence, user choice when applicable, and precise repair.

## Completion reporting

At the single canonical Phase-4 dump, write the issue list and write or preserve exactly one `## Open Items for User` section containing the accumulated deduplicated entries. Then read `tasks/build-issues.md` and count that section's entries. If the count is nonzero, place this literal line above the per-stage/per-task completion summary:

```text
Open Items: <N> entry/entries — review tasks/build-issues.md § Open Items for User before publishing.
```

Use `entry` for one and `entries` otherwise. Never report Step 12 complete before all blocking checks have cleared.

<!-- END: case-validation-guide.md -->

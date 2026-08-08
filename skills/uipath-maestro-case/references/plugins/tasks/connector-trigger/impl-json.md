# connector-trigger task — Implementation (Direct JSON Write)

> **Node `type` value: `wait-for-connector` (schema-kebab).** NEVER write `connector-trigger` (plugin folder name) into the JSON `type` field. The Phase 3 CLI target is `case spec --type trigger`. See SKILL.md Rule 16 + Plugin Index.

This file owns the in-stage task envelope, task/input/output IDs, output binding, placement, and fallback. The connector metadata algorithm and raw-cache contract are owned by [connector-trigger-common.md](../../../connector-trigger-common.md).

## Prerequisites from Planning

The T-entry supplies `type-id`, `connection-id`, `connector-key`, optional `object-name`, `event-operation`, `event-mode`, optional `input-values.eventParameters`, optional `filter`, output mappings, and the task placement fields.

## Phase 2 — Write the task envelope

Mint task ID `t` + 8 characters and `elementId = <stageId>-<taskId>`. For a resolved T-entry, write the task with `data.typeId` and `data.connectionId`; do not call `case spec` or add `serviceType` / `context` / `inputs` / `outputs` yet. Append that envelope exactly once, applying its `activation-mode` + `entry-rule` through the central task-placement contract. A planning-time unresolved T-entry uses the Rule 8 task placeholder with `data: {}`.

## Phase 3 — Configure the task

### Step 1 — Run the common target-local pipeline

Run [common § Phase 3 Implementation — Single CLI Call](../../../connector-trigger-common.md#phase-3-implementation--single-cli-call) for this task, using the existing task `elementId` as the common cache identity. Continue only after the common required-field gate and cache-read/splice steps succeed.

For this target, `{{TRIGGER_REGISTRATION_KEY}}` uses `<connection-id>_<case-start-node.id>`, not the stage ID.

### Step 2 — Mint task input/output IDs

For every normalized input and output, mint `var = id = v<8 characters>` and set `elementId` to the task element ID. Dedupe outputs through [common § Step 5](../../../connector-trigger-common.md#step-5--mint-var--id--elementid-on-inputs-and-outputs), then apply the [I/O output binding owner](../../variables/io-binding/impl-json.md#output-binding-shapes) to the T-entry's output mappings.

### Step 3 — Enrich the existing task

Preserve the Phase 2 identity, envelope, entry conditions, and placement. Targeted Edit only its `data` property to the following cache-derived result:

```json
{
  "typeId": "<type-id>",
  "connectionId": "<connection-id>",
  "serviceType": "Intsvc.WaitForEvent",
  "context": "<complete normalized Context; placeholders substituted>",
  "inputs": "<complete normalized Inputs; IDs minted>",
  "outputs": "<complete normalized Outputs; IDs minted/projected/deduped>",
  "bindings": []
}
```

### Step 4 — Append bindings and defer batch sync

Append the canonical ConnectionId and optional FolderKey root bindings per [common § Root-level bindings](../../../connector-trigger-common.md#root-level-bindings). Keep `data.bindings` empty. Populate the IS cache after the task batch and regenerate `bindings_v2.json` once at the end of implementation Step 9.7.

## Graceful degradation

| Failure | Result | Log |
|---|---|---|
| Planning-time unresolved type/connection | Rule 8 placeholder, `data: {}` | `[SKIPPED] unresolved connector wait written as placeholder` |
| Phase 3 spec call fails | Preserve resolved Phase 2 `typeId` and `connectionId`; omit spec enrichment | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required field declined | Rule 8 placeholder; retain any successfully written raw cache | `[SKIPPED] required event parameter <name> missing — placeholder task per Rule 8` |

Append issues through the logging owner. Do not create a raw cache or root bindings when no successful spec response exists.

## Post-Write Verification

Checks 3–6 apply only to a fully configured task.

1. A fully configured task has `type: "wait-for-connector"` plus real `data.typeId`, `data.connectionId`, and `data.serviceType: "Intsvc.WaitForEvent"`; a failed spec retains only the two Phase 2 IDs, while a Rule 8 fallback has `data: {}`.
2. After any successful spec call, the task's own retained full-response cache has PascalCase `Data.CaseShape.Context`, `Inputs`, and `Outputs` paths.
3. On a fully configured task, `data.context`, `inputs`, and `outputs` are complete normalized subtrees from that cache, with only common-owner mutations.
4. `context` placeholders use this task's binding IDs and case-start-node registration key.
5. Every input/output has this task's `elementId`; outputs are globally deduped and projected.
6. On a fully configured task, root ConnectionId/optional FolderKey bindings exist; `data.bindings` is `[]`; the deferred `bindings_v2` sync includes them.

## What NOT to Do

- Do not call a legacy connector `tasks describe` command or reuse another target's response.
- Do not reconstruct or selectively copy a `CaseShape` subtree.
- Do not let implementation Step 9.8 replace this task's CLI-authored inputs.
- Do not auto-inject task entry conditions outside the preserved placement contract.

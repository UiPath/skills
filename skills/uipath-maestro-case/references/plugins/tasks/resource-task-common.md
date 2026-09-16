# Resource tasks — the shape every non-connector task shares

`action`, `agent`, `api-workflow`, `case-management`, `process` and `rpa` all bind a tenant resource and share the rules below. Each type's own `impl-json.md` states only what differs — its `type` discriminator, its `data` fields, and its lookup. Read this file once per build, then that type's file.

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../variables/io-binding/impl-json.md). See [phased-execution.md](../../phased-execution.md).

**Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is the `tasks describe` output (Step 0 above).

- `data.inputs` and `data.outputs` populated (unless placeholder)

- `data.name` / `data.folderPath` MUST be `=bindings.<id>` references — never literals.

- `data.name` and `data.folderPath` start with `=bindings.`

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.

- `description`: the task's `**Description:**` line from sdd.md, word for word. Do not shorten or reword it. `**Design Rationale:**` is a different line and goes to `tasks/build-issues.md`; use it here only when the block writes no `**Description:**`.

- `isRequired` and `shouldRunOnlyOnce` come from the SDD task envelope; default `shouldRunOnlyOnce` to `false` when omitted. Do not infer run-once from task type.

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)

Dedup per [§ Deduplication](../variables/bindings/impl-json.md).

Fallback: planning-captured schema from `registry-resolved.json`. If unavailable, placeholder per [placeholder-tasks.md](../../placeholder-tasks.md).

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

<!-- END: resource-task-common.md -->
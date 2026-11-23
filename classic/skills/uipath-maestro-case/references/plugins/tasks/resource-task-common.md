# Resource tasks — the shape every non-connector task shares

`action`, `agent`, `api-workflow`, `business-rule`, `case-management`, `function`, `process` and `rpa` bind a tenant resource and share these rules. Read this file once per build, then the type's `impl-json.md` for its `type` discriminator, `data` fields, and lookup.

> **Phase split.** Phase 2 writes shape with empty input values; Phase 3 binds values per [io-binding/impl-json.md](../variables/io-binding/impl-json.md). See [phased-execution.md](../../phased-execution.md).

**Output binding:** apply [io-binding/impl-json.md § Output Binding Shapes](../variables/io-binding/impl-json.md#output-binding-shapes). The plugin's Step 0 schema is that type's `tasks describe` output.

> **Never hand-write a `type` or `_jsonSchema` onto an input or output row.** Run:
>
> ```bash
> uip maestro case tasks describe --type <taskType> --id <selected.identifier> --output json   # save verbatim with Write
> uip maestro case splice "<caseplan.case>" --task-id "<taskId>" --described "<that saved file>" --output json
> ```
>
> `splice` merges by row `name` into existing task rows. `type`, `_jsonSchema`, `options` and `displayName` come from `describe`; `id`, `var`, `elementId` and SDD-authored `value` / `source` / `target` are preserved. A described name absent from the task goes to `Summary.Unmatched` and is never appended. `Error` goes there for every resource; the SDD determines which outputs the case uses. Read `Summary.InputsUpdated` / `OutputsUpdated` to confirm. Repeating the operation is byte-identical. This closes `sdd convert`'s `output-type` unresolved entry names; do not close them by hand.

- Populate `data.inputs` and `data.outputs` unless placeholder.
- Set `data.name` / `data.folderPath` to `=bindings.<id>` references, never literals.
- Set `id` to `t` + 8 alphanumeric chars and `elementId` to `${stageId}-${taskId}`.
- Set `description` to the task's `**Description:**` line from sdd.md verbatim; never shorten or reword it. `**Design Rationale:**` is separate and belongs in `tasks/build-issues.md`; use it here only when the block has no `**Description:**`.
- Take `isRequired` and `shouldRunOnlyOnce` from the SDD task envelope; default omitted `shouldRunOnlyOnce` to `false`. Never infer run-once from task type.

Dedup per [§ Deduplication](../variables/bindings/impl-json.md).

Use the planning-captured schema in `registry-resolved.json`; if unavailable, use the placeholder in [placeholder-tasks.md](../../placeholder-tasks.md).

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../variables/bindings/impl-json.md) for the canonical 7-field shape. All fields are required because omitting any causes Studio Web render failure; per-task differences are in each type's `impl-json.md`.

<!-- END: resource-task-common.md -->
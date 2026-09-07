<!--skill-flavor:trigger-node-id-note:start-->
> **Set `triggerNodeId` on every `in` global** — omit it and the input is silently dropped from the packed entry point.
>
> - **What to set** — the `id` of the trigger that supplies the value; `"start"` in a single-trigger flow.
> - **Why** — packaging reads the input contract from the trigger manifest's output schema when it declares one, and otherwise keeps only globals where `direction === "in"` and `triggerNodeId` matches the start node's `id`. Core triggers declare no output schema, so that second branch is the live one.
> - **Failure mode** — the package built on publish or debug carries an empty `input.properties` while `flow validate` and `flow format` both stay green, so nothing warns you.
> - **Via CLI** — `uip maestro flow variable add --direction in` sets it for you.
<!--skill-flavor:trigger-node-id-note:end-->

<!--skill-flavor:file-input-guidance:start-->
**File input (`type: "file"`):**
```json
{
  "id": "inputDoc",
  "direction": "in",
  "type": "file",
  "description": "Document supplied when the flow is triggered",
  "triggerNodeId": "start"
}
```

> **Runtime shape of a `file` variable.** At runtime a `file` variable is an **object** (the *Flow Attachment* object), not a string. A Script node reading `$vars.start.output.inputDoc` receives:
>
> ```json
> { "ID": "<uuid>", "FullName": "report.pdf", "MimeType": "application/pdf", "Metadata": { "size": "1024" } }
> ```
>
> The uploaded file's name is **`.FullName`**. Property access is **case-sensitive** at runtime — these exact casings resolve, others return `undefined`/`null`: `.ID` (uppercase, not `.Id`), `.FullName`, `.MimeType`, and the **nested `.Metadata.size`** (lowercase `size`, NOT `.Size`). `.name` / `.fileName` do **not** exist. Two layers: the `.flow` *declaration* is camelCase (`type`, `direction`); the *runtime* object carries the casing above. Do NOT write `"FullName"` into the `.flow` source. In Studio Web `uip flow debug` cannot attach files (`--attachment` is ignored); test file inputs from the designer's Debug panel or with an upstream node that produces the attachment — see [cli-commands.md — Pre-flight](cli-commands.md#attachment-preflight).
<!--skill-flavor:file-input-guidance:end-->

<!--skill-flavor:type-reference-table:start-->
| Type | Default Value | Notes |
| --- | --- | --- |
| `string` | `""` | Default type if omitted |
| `number` | `0` | Integer or float |
| `boolean` | `false` | |
| `object` | `{}` | Use `schema` for structured objects |
| `array` | `[]` | Use `subType` for typed arrays |
| `file` | — | Hydrates as an object at runtime — read `.FullName` (see [File input](#file-input) above); in Studio Web supply it from the designer's Debug panel or an upstream node, not `--attachment` |
<!--skill-flavor:type-reference-table:end-->

<!--skill-flavor:legacy-string-form-symptom:start-->
> **Symptom of the legacy string form:** `uip maestro flow validate` fails with
> `[MIGRATION] Workflow migration failed at 1.9→1.10 … Offending field(s): variables.variableUpdates.<nodeId>.0.expression`
> and `"Retry": "RetryWillNotFix"`. The string form was dropped in file-format version 1.3; the `uip flow init` scaffold writes the current version into `new.flow`.
<!--skill-flavor:legacy-string-form-symptom:end-->

<!--skill-flavor:variable-add-trigger-binding-note:start-->
> **`variable add --direction in` binds the variable to a trigger** by writing `triggerNodeId`. That binding is what puts the input in the packed entry point's contract — without it the package built on publish or debug carries an empty `input.properties` while `validate` and `format` stay green. The CLI infers the flow's single trigger; if a flow has more than one, it fails and asks for `--trigger-node-id <nodeId>` to say which entry point the input belongs to. Hand-authored globals need the same field — see [Workflow Variables](#workflow-variables).
<!--skill-flavor:variable-add-trigger-binding-note:end-->

<!--skill-flavor:adding-input-variable-steps:start-->
1. Open `/solution/<ProjectName>/new.flow`
2. Add the variable object to `variables.globals`
3. Run `uip maestro flow validate` to check for errors
<!--skill-flavor:adding-input-variable-steps:end-->

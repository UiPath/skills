<!--skill-flavor:trigger-node-id-note:start-->
> - **Failure mode** — the package built on publish or debug carries an empty `input.properties` while `flow validate` and `flow format` both stay green, so nothing warns you.
<!--skill-flavor:trigger-node-id-note:end-->

<!--skill-flavor:file-input-guidance:start-->
  "description": "Document supplied when the flow is triggered",
<!--skill-flavor:file-input-guidance:end-->

<!--skill-flavor:file-input-guidance-2:start-->
> The uploaded file's name is **`.FullName`**. Property access is **case-sensitive** at runtime — these exact casings resolve, others return `undefined`/`null`: `.ID` (uppercase, not `.Id`), `.FullName`, `.MimeType`, and the **nested `.Metadata.size`** (lowercase `size`, NOT `.Size`). `.name` / `.fileName` do **not** exist. Two layers: the `.flow` *declaration* is camelCase (`type`, `direction`); the *runtime* object carries the casing above. Do NOT write `"FullName"` into the `.flow` source. In Studio Web `uip flow debug` cannot attach files (`--attachment` is ignored); test file inputs from the designer's Debug panel or with an upstream node that produces the attachment — see [cli-commands.md — Pre-flight](cli-commands.md#attachment-preflight).
<!--skill-flavor:file-input-guidance-2:end-->

<!--skill-flavor:type-reference-table:start-->
| `file` | — | Hydrates as an object at runtime — read `.FullName` (see [File input](#file-input) above); in Studio Web supply it from the designer's Debug panel or an upstream node, not `--attachment` |
<!--skill-flavor:type-reference-table:end-->

<!--skill-flavor:legacy-string-form-symptom:start-->
> and `"Retry": "RetryWillNotFix"`. The string form was dropped in file-format version 1.3; the `uip flow init` scaffold writes the current version into `new.flow`.
<!--skill-flavor:legacy-string-form-symptom:end-->

<!--skill-flavor:variable-add-trigger-binding-note:start-->
> **`variable add --direction in` binds the variable to a trigger** by writing `triggerNodeId`. That binding is what puts the input in the packed entry point's contract — without it the package built on publish or debug carries an empty `input.properties` while `validate` and `format` stay green. The CLI infers the flow's single trigger; if a flow has more than one, it fails and asks for `--trigger-node-id <nodeId>` to say which entry point the input belongs to. Hand-authored globals need the same field — see [Workflow Variables](#workflow-variables).
<!--skill-flavor:variable-add-trigger-binding-note:end-->

<!--skill-flavor:adding-input-variable-steps:start-->
1. Open `/solution/<ProjectName>/new.flow`
<!--skill-flavor:adding-input-variable-steps:end-->

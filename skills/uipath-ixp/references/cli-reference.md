# CLI Commands Reference

All commands use `uip ixp` prefix. Always append `--output json` when parsing output programmatically.

## Projects

| Command | Description |
|---------|-------------|
| `uip ixp projects list --output json` | List all IXP projects |
| `uip ixp projects get <project-name> --output json` | Get a project |
| `uip ixp projects create "<name>" <folder-path> [-d "<description>"] [--skip-taxonomy] --output json` | Create project and upload supported docs in `<folder-path>` (top-level only — sub-folders are not scanned; see [Supported document files](#supported-document-files)). By default suggests+imports taxonomy. `-d` provides context for better taxonomy suggestion. Use `--skip-taxonomy` to create a blank project (import taxonomy separately). Use `ProjectName` from output. |
| `uip ixp projects import-taxonomy <project-name> <file> --output json` | Import taxonomy from a local JSON file. Accepts `{ field_types, label_group }` or `{ entity_defs, label_groups }` format. |
| `uip ixp projects update-title <project-name> "<new-title>" --output json` | Update the display title of a project |
| `uip ixp projects get-taxonomy <project-name> --output json` | Get taxonomy (entity_defs + label_groups with field definitions) |
| `uip ixp projects get-metrics <project-name> --output json` | Get validation metrics — `FieldGroups[]` (per-group) and `Fields[]` (per-field F1/Precision/Recall) |
| `uip ixp projects configure-model <project-name> [options] --output json` | Configure extraction model. Options: `--model` (gemini_2_5_flash/gemini_2_5_pro/gpt_4o_2024_05_13) and `--preprocessing` (none/table_mini/table). |
| `uip ixp projects update-prompts <project-name> --fields <json> [--groups <json>] --output json` | Update field and/or field group instructions. `--fields` (required): per-field updates `[{"name":"Invoice Number","instructions":"..."}]`. `--groups` (optional): label_def updates `[{"name":"Invoice","instructions":"..."}]`. |
| `uip ixp projects list-models <project-name> --output json` | List all model versions and tags. Returns `Models[]` (Version, Pinned, TrainedTime) and `Tags[]` (Name, Version). |
| `uip ixp projects publish <project-name> --output json` | Publish (pin) the latest model version. Options: `--model-version <N>` (specific version, default: latest), `--description "<text>"` (set description), `--tag <name>` (assign tag: "live", "staging", or custom). |

## Documents

| Command | Description |
|---------|-------------|
| `uip ixp documents list <project-name> [-l <limit>] [--offset <n>] --output json` | List documents — returns `[{ DocumentId, AttachmentRef, Filename }]`. `Filename` is the original upload filename (null if the upload didn't carry one). Paginated: defaults to 50 items per page (max 10000). Pass `-l` for larger pages or `--offset` to skip ahead. |
| `uip ixp documents download <project-name> <document-id> -o <path> --output json` | Download the original document file (PDF/PNG/JPG/etc.). The CLI auto-corrects the file extension to match the actual content; use the response `Path` field as the resolved location. |
| `uip ixp documents upload <project-name> <file> --output json` | Upload a single document file to an existing project. See [Uploading documents](#uploading-documents-to-an-existing-project) below for validation, output shape, and the multi-file loop pattern. |
| `uip ixp documents delete <project-name> <document-id> --output json` | Delete a document (and its labellings) from a project. Irreversible — triggers a retrain. |

### Supported document files

Both `projects create` (bulk folder upload) and `documents upload` (single file) validate against the same extension whitelist, case-insensitive:

`.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.tif`, `.tiff`, `.bmp`

Validation differs by command:

- `documents upload` rejects an unsupported file with `Unsupported file type "<ext>"` before any network call.
- `projects create` scans only the top level of `<folder-path>` (sub-folders are ignored), silently skips unsupported files, and fails only when **no** supported files exist (`No supported documents found in <folder>`).

Each upload triggers a retrain — wait ~2 min before reading metrics or predictions for new docs.

### Uploading documents to an existing project

`uip ixp documents upload <project-name> <file> --output json` pushes one document to an existing project.

For supported extensions, validation error strings, and retrain timing, see [Supported document files](#supported-document-files) above.

Returns `{ ProjectName, FileName, AttachmentRef, DocumentId }` (Code: `IxpDocumentsUpload`). Capture `DocumentId` for later `documents download` or `labellings confirm` calls.

**Multiple files** — one file per call; loop the command:

```bash
cd "<folder-with-docs>"
for f in *.pdf *.png *.jpg *.jpeg *.gif *.tif *.tiff *.bmp; do
    [ -e "$f" ] || continue   # skip unmatched glob patterns
    uip ixp documents upload <project-name> "$f" --output json
done
```

**When NOT to use this:** for filling a brand-new project, prefer `projects create <name> <folder-path>` — uploads the whole folder and suggests a taxonomy in one call.

## Data Types

Manage the reusable type definitions (entity_defs) that fields reference via `field_type_id`. In the IXP UI, these are the project's "Data Types".

| Command | Description |
|---------|-------------|
| `uip ixp data-types add <project-name> --name <name> --kind <text\|date\|money\|number\|boolean\|choice> --instructions <text> --input-value <exact-match\|inferred> [--choices <json>] --output json` | Create a new data type. `--kind` selects the underlying data shape; `text` is the default Text type. `--input-value exact-match` marks the value as appearing verbatim in the document; `inferred` is for computed/derived values that don't have a visible location. (Matches the IXP UI's "Exact match" / "Inferred" radio.) `--choices` is **required when `--kind choice`** and forbidden otherwise. JSON array of `{"value":"<canonical>","alternates":["<alt1>",...]}`; `value` is the canonical display name (model output); `alternates` is optional (defaults to `[]`) and lists alternate spellings the model maps to `value`. |
| `uip ixp data-types update-instructions <project-name> --name <name> --instructions <text> --output json` | Replace the instructions on an existing data type. Name, kind, and input-value stay the same. |
| `uip ixp data-types rename <project-name> --name <name> --new-name <name> --output json` | Rename a data type. Existing field references (via `field_type_id`) stay intact. |
| `uip ixp data-types delete <project-name> --name <name> --confirm-data-loss --output json` | Delete a data type. **IRREVERSIBLE** — any field referencing it via `field_type_id` will break. `--confirm-data-loss` is required. |

## Groups

Manage field groups (label_defs) — the document type containers for fields. To edit fields **inside** an existing group, use the `fields` subject below.

| Command | Description |
|---------|-------------|
| `uip ixp groups add <project-name> --name <group-name> --instructions <text> --fields <json> --output json` | Create a new field group with instructions and at least one field. `--instructions` describes what document/section the group covers (the model sees it during extraction). `--fields` is a JSON array `[{"name":"...","type":"<type-name>","instructions":"..."}]` (1-32 entries); every entry must include `name`, `type`, and a non-empty `instructions`. `type` resolves against the project's `entity_defs`. |
| `uip ixp groups delete <project-name> --name <group-name> --confirm-data-loss --output json` | Delete a field group. **IRREVERSIBLE** — deletes all annotations on all fields in the group. `--confirm-data-loss` is required. |
| `uip ixp groups rename <project-name> --name <group-name> --new-name <name> --output json` | Rename a field group. Preserves all fields and annotations. |

## Fields

Structural edits to a field within an existing field group. For instruction-only edits use `projects update-prompts`. To create the group itself, use `groups add` above.

| Command | Description |
|---------|-------------|
| `uip ixp fields add <project-name> --group <field-group-name> --field <name> --type <type-name> --instructions <text> --output json` | Add a new field to an **existing** field group. `--type` is the name of an entity_def in the project's taxonomy (see `projects get-taxonomy`). `--instructions` is required — describe what to extract and where it appears. |
| `uip ixp fields delete <project-name> --group <field-group-name> --field <name> --output json` | Remove a field from a field group. |
| `uip ixp fields rename <project-name> --group <field-group-name> --field <name> --new-name <name> --output json` | Rename a field. Preserves `field_id` and existing annotations. |
| `uip ixp fields change-type <project-name> --group <field-group-name> --field <name> --type <type-name> --confirm-data-loss --output json` | Change a field's type. **IRREVERSIBLE** — the server creates a new field under the hood, so all existing annotations for that field are deleted. `--confirm-data-loss` is required. |

## Labellings

| Command | Description |
|---------|-------------|
| `uip ixp labellings get-predictions <project-name> [document-id] --output json` | Get IXP model predictions for all documents (or a single document). Returns predicted labels with `FieldId`, `FieldName`, and `FormattedValue`. |
| `uip ixp labellings confirm <project-name> <document-id> [--fields <ids>] [--corrections <json>] --output json` | Confirm predictions for a document. `--fields "id1,id2,id3"` confirms only those fields. `--corrections '[{"field_id":"...","value":"..."}]'` is **only for OCR-mangled values** — same field, same location, garbled bytes. Do NOT use `--corrections` to flip wrong booleans, fix wrong inferred values, or override any non-OCR mistake; those fields must be left unannotated. See Critical Rule 8. |
| `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` | Roll back confirmations on a document — the listed fields go back to un-annotated state. Use when an earlier `confirm` or `mark-missing` was a mistake. Every other annotation on the document is carried forward. Returns `Unmatched` for IDs that weren't annotated to begin with. |
| `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json` | Mark fields as missing on a document — the field is annotated as having no value and no location. **Only use for fields where IXP itself predicted no value** (the prediction's `FormattedValue` is empty/absent for that field in `labellings get-predictions`). If IXP predicted a wrong value, leave the field unannotated instead. Returns `Unmatched` for any IDs not found in the document's extractions. |

## Deployments

For working with runtime (deployed) IXP models — separate from the training workflow above.

| Command | Description |
|---------|-------------|
| `uip ixp deployments get-taxonomy <model-name> --folder-key <key> --output json` | Get the taxonomy (field names) of a deployed model. Pairs with `uip maestro flow registry get` — use `inputDefaults.modelName` and `inputDefaults.folderKey` from that output. |

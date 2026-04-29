# CLI Commands Reference

All commands use `uip ixp` prefix. Always append `--output json` when parsing output programmatically.

## Projects

| Command | Description |
|---------|-------------|
| `uip ixp project list --output json` | List all IXP projects |
| `uip ixp project get <project-name> --output json` | Get a project |
| `uip ixp project create "<name>" <folder-path> [-d "<description>"] [--skip-taxonomy] --output json` | Create project and upload docs. By default suggests+imports taxonomy. `-d` provides context for better taxonomy suggestion. Use `--skip-taxonomy` to create a blank project (import taxonomy separately). Use `ProjectName` from output. |
| `uip ixp project import-taxonomy <project-name> <file> --output json` | Import taxonomy from a local JSON file. Accepts `{ field_types, label_group }` or `{ entity_defs, label_groups }` format. |
| `uip ixp project rename <project-name> "<new-title>" --output json` | Update the display title of a project |
| `uip ixp project taxonomy <project-name> --output json` | Get taxonomy (entity_defs + label_groups with field definitions) |
| `uip ixp project metrics <project-name> --output json` | Get validation metrics — `FieldGroups[]` (per-group) and `Fields[]` (per-field F1/Precision/Recall) |
| `uip ixp project configure-model <project-name> [options] --output json` | Configure extraction model. Options: `--model` (gemini_2_5_flash/gemini_2_5_pro/gpt_4o_2024_05_13), `--preprocessing` (none/table_mini/table), `--attribution` (model/rules), `--temperature`, `--top-p`, `--seed`, `--frequency-penalty` |
| `uip ixp project update-prompts <project-name> --fields <json> [--groups <json>] --output json` | Update field and/or field group instructions. `--fields` (required): per-field updates `[{"name":"Invoice Number","instructions":"..."}]`. `--groups` (optional): label_def updates `[{"name":"Invoice","instructions":"..."}]`. |
| `uip ixp project list-models <project-name> --output json` | List all model versions and tags. Returns `Models[]` (Version, Pinned, TrainedTime) and `Tags[]` (Name, Version). |
| `uip ixp project publish <project-name> --output json` | Publish (pin) the latest model version. Options: `--model-version <N>` (specific version, default: latest), `--description "<text>"` (set description), `--tag <name>` (assign tag: "live", "staging", or custom). |

## Documents

| Command | Description |
|---------|-------------|
| `uip ixp document list <project-name> --output json` | List documents — returns `[{ DocumentId, AttachmentRef }]` |
| `uip ixp document image <project-name> <document-id> -o <path> --output json` | Download the document image (rendered page) for viewing |
| `uip ixp document text <project-name> <document-id> -o <path> --output json` | Get OCR text and save to file — use to cross-reference predicted values against the document |

## Labellings

| Command | Description |
|---------|-------------|
| `uip ixp labelling predictions <project-name> [document-id] --output json` | Get IXP model predictions for all documents (or a single document). Returns predicted labels with `FieldId`, `FieldName`, and `FormattedValue`. |
| `uip ixp labelling confirm <project-name> <document-id> [--fields <ids>] [--corrections <json>] --output json` | Confirm predictions for a document. `--fields "id1,id2,id3"` confirms only those fields. `--corrections '[{"field_id":"...","value":"..."}]'` overrides OCR-mangled values while keeping the prediction's document references. |

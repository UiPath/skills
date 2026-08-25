# CLI Commands Reference

All commands use `uip ixp` prefix. Always append `--output json` when parsing output programmatically.

> **Destructive commands require `-y, --yes`.** Every irreversible `uip ixp` command (all `delete`s and `fields change-type`) gates on `-y/--yes`; the CLI never prompts. Always pass `-y/--yes`.

## Projects

| Command | Description |
|---------|-------------|
| `uip ixp projects list [-l <limit>] [--offset <n>] --output json` | List IXP projects — returns a paged envelope `Data: { Projects: [{ Id, Name, Title, CreatedAt }], Total, Offset, Limit }` (rows under `Projects`, **not** a bare array). `-l, --limit` defaults 50 (range 1-10000); `--offset` defaults 0 to page. |
| `uip ixp projects get <project-name> --output json` | Get a project |
| `uip ixp projects create "<name>" <folder-path> [-d "<description>"] [--skip-taxonomy] --output json` | Create project and upload supported docs in `<folder-path>` (top-level only — sub-folders are not scanned; see [Supported document files](#supported-document-files)). By default suggests+imports taxonomy. `-d` provides context for better taxonomy suggestion. Use `--skip-taxonomy` to create a blank project (import taxonomy separately). Use `ProjectName` from output. |
| `uip ixp projects import-taxonomy <project-name> <file> --output json` | Import taxonomy from a local JSON file. Accepts `{ field_types, label_group }` or `{ entity_defs, label_groups }` format. **Merges — it never replaces**: entries you omit are kept and a posted `field_id` is ignored, so it cannot remove, move, or replace anything (a re-imported edit returns `{"status":"ok"}` and silently leaves duplicates). Use it to seed a project that has no taxonomy; change an existing one with the targeted `groups`/`fields`/`data-types` commands. |
| `uip ixp projects update-title <project-name> "<new-title>" --output json` | Update the display title of a project |
| `uip ixp projects update-prompt <project-name> --prompt "<text>" --output json` | Update the project's **Overall extraction instructions** — the taxonomy-wide prompt the model sees on every extraction (the field at the top of the IXP UI's Manage Taxonomy page). Distinct from per-field-group prompts (`groups update-prompts`) and per-field prompts (`fields update-prompts`). Replaces the existing value. |
| `uip ixp projects get-taxonomy <project-name> --output json` | Export the raw IXP taxonomy artifact. Data is `{ status, dataset: { entity_defs, label_groups } }` — read `entity_defs` and `label_groups` under `dataset`. Intended for re-import (see `import-taxonomy`), not a human-readable view. `dataset` also carries `_model_config`, the only read path for the configured extraction model and pre-processing — see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing). |
| `uip ixp projects get-metrics <project-name> [--model-version <N>] --output json` | Get validation metrics. **Validated model →** flat Data: `ProjectScore`, `ProjectScoreQuality`, `ValidatedDocuments`, `ModelVersion`, plus per-group `FieldGroups[]` (`FieldGroup`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`) and per-field `Fields[]` (`FieldGroup`, `FieldId`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`, `Annotations`, `Quality`). **Trained but not yet validated →** Data is `{ Metrics: null }` (not an error). **No trained model yet (e.g. a project with no confirmed labellings) →** the call returns a failure envelope `Result: Failure` with `ErrorCode: not_found` (no `Data`), NOT `{ Metrics: null }` — treat it as "no metrics yet". Defaults to the latest version; pass `--model-version <N>` (`-m`, `latest` or an integer) to scope to a specific trained version. |
| `uip ixp projects configure-model <project-name> [options] --output json` | Configure extraction model. Options: `--model` (gemini_2_5_flash/gemini_2_5_pro/gpt_4o_2024_05_13) and `--preprocessing` (none/table_mini/table). To read the current settings, see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing). |
| `uip ixp projects list-models <project-name> --output json` | List all model versions and tags. Returns `Models[]` (`Version`, `ModelName`, `Pinned`, `TrainedTime`, `Description`), `Tags[]` (`Name`, `Version`, `UpdatedAt`), and `MaxPublished`. `ModelName` is the trained labeller's **family** (e.g. `gemini_ixp`, `gemini_pro_ixp`) — it is never a `--model` value like `gemini_2_5_flash`, so it does not answer "which extraction model is configured" (see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing)). |
| `uip ixp projects publish <project-name> [--model-version <N>] [--tag <live\|staging>] --output json` | Publish a model version — defaults to the latest; pass `-m, --model-version <N>` to pick a specific one. `-d, --description "<text>"` sets a description; `--tag <live\|staging>` tags the published version. |
| `uip ixp projects unpublish <project-name> --model-version <N> --output json` | Unpublish a model version — it stays trained and listable; only its published status is removed. `--model-version` is **required**. Errors if the version isn't found or isn't currently published. To change which version is live, `publish` a different one instead. |
| `uip ixp projects untag <project-name> --tag <live\|staging> --output json` | Remove a tag by **name** (`--tag` is **required**; tag names are unique within a project, so this is unambiguous even when one version holds several tags). The version the tag pointed at stays published; only that tag is cleared. Errors if no version carries the tag. Only `untag` removes a tag — `publish` without `--tag` leaves the existing tag untouched. To switch `live`→`staging`, `publish --tag staging` instead. |
| `uip ixp projects delete <project-name> -y --output json` | **Permanently** delete a project — its documents, taxonomy, and trained models. **Irreversible.** `-y, --yes` is **required**; the command refuses to run without it (the CLI never prompts). |

### Reading the current model and pre-processing

There is **no `get-model-config` command** — `configure-model` only writes. The configured extraction model and pre-processing are in the taxonomy artifact under `Data.dataset._model_config`:

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

**Model** — `_model_config.model_version` holds the `--model` value verbatim (e.g. `gemini_2_5_flash`). Report that one. Do **not** report `list-models`' `ModelName`: that is the trained labeller's family (`gemini_ixp`) and carries no pre-processing information at all.

**Pre-processing** — `_model_config.input_config` stores the underlying mode, not the `none|table_mini|table` token, so invert it:

| `input_config` | `--preprocessing` |
|----------------|-------------------|
| `null` | never configured — report it as *not configured* (the project uses the IXP default), **not** as `none` |
| `{"mode": "image_only"}` | `none` |
| `{"mode": "text_plus_image", "text_config": {"kind": "uipath_cv_table_only"}}` | `table_mini` |
| `{"mode": "text_plus_image", "text_config": {"kind": "gemini_table_only"}}` | `table` |

The remaining `_model_config` keys (`kind`, `flags`, `attribution_method`, `temperature`, `top_p`, `seed`, `system_prompt_override`, `iterative_config`) have no `uip ixp` flag — mention them only if the user asks.

`_model_config` reflects the project's **current** setting, not the setting a given trained version was built with — so report it as the project's configuration, not as a property of the published version.

## Documents

| Command | Description |
|---------|-------------|
| `uip ixp documents list <project-name> [-l <limit>] [--offset <n>] --output json` | List documents — returns a paged envelope `Data: { Documents: [{ DocumentId, AttachmentRef, Filename }], Total, Offset, Limit }` (rows are under `Documents`, **not** a bare array). `AttachmentRef`/`Filename` may be `null`; `Filename` is the original upload filename. `-l, --limit` defaults 50 (range 1-10000); `--offset` defaults 0 (range 0-1000000). |
| `uip ixp documents download <project-name> <document-id> -o <path> --output json` | Download the original document file (PDF/PNG/JPG/etc.) to exactly the `-o` path you give. **The CLI does not append or correct a file extension** — the file is written verbatim to `-o`, and `Data.ContentType` is commonly the generic `application/octet-stream` rather than the true MIME type — so include the correct extension in `-o` yourself (e.g. `-o invoice.pdf`). `Data.Path` echoes the path you provided. |
| `uip ixp documents upload <project-name> <file> --output json` | Upload a single document file to an existing project. See [Uploading documents](#uploading-documents-to-an-existing-project) below for validation, output shape, and the multi-file loop pattern. |
| `uip ixp documents delete <project-name> <document-id> -y --output json` | Delete a document (and its labellings) from a project. Irreversible — triggers a retrain. `-y, --yes` is **required** (the CLI never prompts; without it the command refuses and exits 1). |

### Supported document files

Both `projects create` (bulk folder upload) and `documents upload` (single file) validate against the same extension whitelist, case-insensitive:

`.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.tif`, `.tiff`, `.bmp`

Validation differs by command:

- `documents upload` rejects an unsupported file with `Unsupported file type "<ext>"` before any network call.
- `projects create` scans only the top level of `<folder-path>` (sub-folders are ignored), silently skips unsupported files, and fails only when **no** supported files exist (`No supported documents found in <folder>`).

Each upload triggers a retrain — wait it out before reading metrics or predictions for new docs, under the bounded wait in [Improve Prompts Guide § Waiting for retrain](improve-prompts-guide.md#waiting-for-retrain).

### Uploading documents to an existing project

`uip ixp documents upload <project-name> <file> --output json` pushes one document to an existing project.

For supported extensions, validation error strings, and retrain timing, see [Supported document files](#supported-document-files) above.

Returns `{ ProjectName, Filename, AttachmentRef, DocumentId }` (Code: `IxpDocumentsUpload`). Capture `DocumentId` for later `documents download` or `labellings confirm` calls.

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
| `uip ixp data-types add <project-name> --name <name> --kind <text\|date\|money\|number\|boolean\|choice> --instructions <text> [--input-value <exact-match\|inferred>] [--choices <json>] --output json` | Create a new data type. `--kind` selects the underlying data shape; `text` is the default Text type. `--input-value` is **required for `--kind text` and `--kind choice`, forbidden for `date`, `money`, `number`, and `boolean`** — those kinds don't expose the "Exact match" / "Inferred" radio in the IXP UI, so the CLI rejects the flag when the kind doesn't support it. `exact-match` marks the value as appearing verbatim in the document; `inferred` is for computed/derived values that don't have a visible location. `--choices` is **required when `--kind choice`** and forbidden otherwise. JSON array of `{"value":"<canonical>","alternates":["<alt1>",...]}`; `value` is the canonical display name (model output); `alternates` is optional (defaults to `[]`) and lists alternate spellings the model maps to `value`. |
| `uip ixp data-types update-instructions <project-name> --name <name> --instructions <text> --output json` | Replace the instructions on an existing data type. Name, kind, and input-value stay the same. |
| `uip ixp data-types rename <project-name> --name <name> --new-name <name> --output json` | Rename a data type. Existing field references (via `field_type_id`) stay intact. |
| `uip ixp data-types delete <project-name> --name <name> -y --output json` | Delete a data type. **IRREVERSIBLE** — any field referencing it via `field_type_id` will break. `-y, --yes` is **required** (the CLI never prompts). |

### Default data types

Every IXP project ships with the built-in data types below (the project's `entity_defs` from `projects get-taxonomy` are the authoritative list). **Before `data-types add`, or before choosing a field's `--type` (in `fields add` / `groups add`), check the existing `entity_defs` and reuse a matching default.** A redundant custom type (e.g. a `Currency Amount` when `Monetary Quantity` already exists) splits annotations across two types and forfeits the default's pre-trained model. Add a new data type only when it carries something no default does — a `Choice`, or a reusable concept that needs its own tailored extraction instructions — not as a clone of a default.

| Default type | `--kind` | `--input-value` | Reuse for |
|--------------|----------|-----------------|-----------|
| `Exact Text` | `text` | `exact-match` | Text copied verbatim from the document — names, IDs, addresses, codes |
| `Inferred Text` | `text` | `inferred` | Text derived/computed, not appearing verbatim in the document |
| `Number` | `number` | — | Counts, quantities, plain numbers |
| `Date` | `date` | — | Dates |
| `Monetary Quantity` | `money` | — | Any currency / monetary amount — total, subtotal, tax, unit price, freight |
| `Boolean` | `boolean` | — | True / false values |

`Date`, `Number`, `Monetary Quantity`, and `Boolean` carry pre-trained models with a fixed output format (below) — instructions cannot change their formatting, so a hand-rolled equivalent is strictly worse. `Choice` is the only `--kind` with no default: choice types are always project-specific (`data-types add --kind choice --choices …`).

### Normalized output formats

`get-predictions` reports these types in the type's normalized form, never the page's literal text. A plain `confirm` stores that same normalized string as the label.

| Type | `FormattedValue` | Page → prediction |
|------|------------------|-------------------|
| `Date` | `YYYY-MM-DDTHH:MM:SSZ` — a date-only page value comes back at `T00:00:00Z` | `21-JUN-22` → `2022-06-21T00:00:00Z` |
| `Monetary Quantity` | `<amount> <ISO-4217 code>` — no thousands separator, decimals as written on the page (not fixed to 2), currency appended even when the page shows none | `114.91` → `114.91 AUD`; `8.0700` → `8.0700 USD` |
| `Number` | bare numeric string, no unit or separator | `29311577` → `29311577` |
| `Boolean` | `True` / `False` | — |

`--corrections` neither normalizes nor validates — the string you send is stored verbatim (`21-JUN-22`, even `not-a-date`, all return Success). Sending the page's format replaces a correct label with one the model will never predict and drops the field's F1. Reformatting is never a reason to use `--corrections` (Critical Rule 8).

## Groups

Manage field groups (label_defs) — the document type containers for fields. To edit fields **inside** an existing group, use the `fields` subject below.

| Command | Description |
|---------|-------------|
| `uip ixp groups add <project-name> --name <group-name> --instructions <text> --fields <json> --output json` | Create a new field group with its fields. `--instructions` describes what document/section the group covers (the model sees it during extraction). `--fields` is a JSON array `[{"name":"...","type":"<type-name>","instructions":"..."}]` — **put ALL of the new group's fields in this one array (batch); do NOT create the group then add its fields one at a time.** Every entry must include `name`, `type`, and a non-empty `instructions`. `type` resolves against the project's `entity_defs` — reuse a [default data type](#default-data-types) before inventing a new one. To add a field to an **already-existing** group, use `fields add` instead. |
| `uip ixp groups delete <project-name> --name <group-name> -y --output json` | Delete a field group. **IRREVERSIBLE** — deletes all annotations on all fields in the group. `-y, --yes` is **required** (the CLI never prompts). |
| `uip ixp groups rename <project-name> --name <group-name> --new-name <name> --output json` | Rename a field group. Preserves all fields and annotations. |
| `uip ixp groups update-prompts <project-name> --updates <json> --output json` | Bulk-update field group (label_def) instructions. `--updates` is a JSON array `[{"name":"<group>","instructions":"..."}]` matched by group name. Existing fields are preserved. Unmatched names are reported in the response without failing the command. |

## Fields

Structural edits to a field within an existing field group. For instruction-only edits use `fields update-prompts` (see below). To create the group itself, use `groups add` above.

| Command | Description |
|---------|-------------|
| `uip ixp fields add <project-name> --group <field-group-name> --field <name> --type <type-name> --instructions <text> --output json` | Add a new field to an **existing** field group. `--type` is the name of an entity_def in the project's taxonomy (see `projects get-taxonomy`) — reuse a [default data type](#default-data-types) (e.g. `Monetary Quantity` for a currency amount) before adding a custom one. `--instructions` is required — describe what to extract and where it appears. |
| `uip ixp fields delete <project-name> --group <field-group-name> --field <name> -y --output json` | Remove a field from a field group. `-y, --yes` is **required** (the CLI never prompts). |
| `uip ixp fields rename <project-name> --group <field-group-name> --field <name> --new-name <name> --output json` | Rename a field. Preserves `field_id` and existing annotations. |
| `uip ixp fields change-type <project-name> --group <field-group-name> --field <name> --type <type-name> -y --output json` | Change a field's type. **IRREVERSIBLE** — the server creates a new field under the hood, so all existing annotations for that field are deleted. `-y, --yes` is **required** (the CLI never prompts). |
| `uip ixp fields update-prompts <project-name> --updates <json> --output json` | Bulk-update per-field extraction instructions. `--updates` is a JSON array `[{"name":"<field>","instructions":"..."}]` matched by `moon_form` field name (across all field groups). Existing field definitions are preserved. Unmatched names are reported in the response without failing the command. |

### Moving a field to a different field group

There is **no move/reparent command**. Every field command takes its group as `--group`, which only addresses the field — it cannot change which group owns it. A move is two `fields` calls against the existing groups, in this order:

1. `uip ixp projects get-taxonomy <project-name> --output json` — read the field's current `type` and `instructions` so they can be carried over. In `Data.dataset`, the field is a `moon_form` entry under its group's `label_def`; its type is the `entity_defs[]` entry whose `id` matches the entry's **`field_type_id`** (NOT its `field_id`, which is the field's own identity and matches no `entity_def`).
2. `uip ixp fields add <project-name> --group <target-group> --field <name> --type <type-name> --instructions <text> --output json` — recreate it in the target group.
3. `uip ixp fields delete <project-name> --group <source-group> --field <name> -y --output json` — remove it from the source group.

Add before deleting: if the add fails, the field is still in its original group. Both groups must already exist — a move never creates one. Creating the target group first, if the user asked for a group that isn't there yet, is a separate `groups add` step you should confirm with them.

**IRREVERSIBLE** — `fields add` mints a new `field_id`, so the field's confirmed labels do not follow it into the new group. Tell the user before starting; documents must be re-reviewed for that field.

**Do NOT move a field by editing the taxonomy and re-importing it.** `projects import-taxonomy` **merges** — it does not replace. Fields you omit from a posted group are kept, and a posted `field_id` is ignored (the backend mints a new one), so the import returns `{"status":"ok"}` while leaving the field in **both** groups as two separate fields. Do not use `groups delete` + `groups add` either: that destroys every other field in the group along with its annotations.

## Labellings

| Command | Description |
|---------|-------------|
| `uip ixp labellings get-predictions <project-name> <document-id> --output json` | Get IXP model predictions for one document. Returns `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`. Each `Predictions[]` entry is one document `{ DocumentId, Labels[] }`; each label is `{ Name, Occurrence, Fields[] }`; each field is `{ FieldId, FieldName, FormattedValue }`. This is the model's **prediction** layer, not the confirmed/annotation layer. Each label carries an explicit `Occurrence` (the value for `--occurrence`/`--updates`); it is 0-based and usually runs 0..N-1 in document order, but do NOT assume it is contiguous or starts at 0 — a single-occurrence group can come back as `Occurrence` 1 with no 0. Always target the actual `Occurrence` value reported here, never a positional guess. **The order is not stable across writes**: the server lists annotation↔prediction matched pairs first, so confirmed rows of a repeatable group sort to the front and the rest renumber — see [Occurrence numbering and read order](#occurrence-numbering-and-read-order). Each document also carries `ModelVersion` (the model version that produced its predictions) — capture it and pass it to `confirm -m/--model-version` to guard against a mid-review retrain. |
| `uip ixp labellings confirm <project-name> <document-id> [--fields <ids>] [--corrections <json>] [--model-version <version>] --output json` | Confirm predictions for a document. (`--fields` has short alias `-f`; `--corrections` has short alias `-c`.) Without `--fields`, confirms every predicted field that has content. `--fields "a7c3e9105f2b4d86,b2f8a01c7d3e6940"` confirms only those fields, and applies a **single uniform rule**: listed fields with content get confirmed; listed fields whose IXP prediction is empty get a missing marker (the explicit listing IS the confirmation that the empty state is intentional — see Critical Rule 12). `--corrections '[{"field_id":"...","value":"..."}]'` is **only for OCR-mangled values** — same field, same location, garbled bytes. Do NOT use `--corrections` to flip wrong booleans, fix wrong inferred values, or override any non-OCR mistake; those fields must be left unannotated. See Critical Rule 8. Existing missing markers and other annotations carry forward across calls. `-m, --model-version <N>` pins the model version you reviewed (the `ModelVersion` from `get-predictions`); if a retrain produced a newer version since, the confirm is rejected (`PredictionVersionChangedError`) instead of stamping drifted values — re-read predictions and review again. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --occurrence <N> [--fields <ids>] [--corrections <json>] [--model-version <version>] --output json` | **Single-occurrence form** — confirm ONE occurrence. The ergonomic choice for a single line. `--occurrence` is the 0-based index of the target extraction within `--group`, as reported by the **latest** `get-predictions`. Without `--fields`, confirms every predicted field in that one occurrence; with `--fields`, confirms only those fields there. Other occurrences are untouched. Requires `--group` (Critical Rule 13). Mutually exclusive with `--updates`. The call renumbers the group for subsequent reads ([Occurrence numbering and read order](#occurrence-numbering-and-read-order)), so use `--updates` for more than one row instead of chaining these off one read. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --updates <json> [--model-version <version>] --output json` | **Batched form** — confirm SEVERAL occurrences in ONE atomic call (one request; avoids N round-trips, e.g. a 10-line invoice). `--updates` is a JSON array `[{"occurrence":<0-based-index>,"fields"?:["<field_id>",…],"corrections"?:{"<field_id>":"<value>"}}]`. Per entry: **omit `"fields"`** to confirm every predicted field in that occurrence (same default as `--occurrence` without `--fields`), or list specific IDs; un-selected fields in a selected occurrence carry forward any existing annotation. **`--updates` is the superset** — `--occurrence <N>` ≡ `--updates` with one entry; both share the same per-occurrence logic. Use `--occurrence` for a single line, `--updates` for several together. Mutually exclusive with `--fields`/`--corrections`/`--occurrence`. |
| `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` | Roll back confirmations on a document (`--fields` has short alias `-f`) — the listed fields go back to un-annotated state. Use when an earlier `confirm` was a mistake (confirm can't un-confirm — Critical Rule 14). Every other annotation on the document is carried forward. **With `--fields` alone, a field id shared across occurrences of a repeatable group is removed from all of them**; to scope the roll-back to specific occurrences, add `--group` (see the two rows below). Returns `Unmatched` for IDs that weren't annotated to begin with. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> [--occurrence <N>] [--fields <ids>] --output json` | **Per-occurrence form** — roll back specific occurrences of a repeatable group instead of every occurrence a field id appears in. `--group` alone unconfirms every occurrence of the group; add `--occurrence <N>` (0-based, same index as `get-predictions`/`confirm`, taken from a **fresh** read — on a partly-confirmed group the index that confirmed a row is usually not the index that rolls it back) to roll back ONE occurrence. Without `--fields`, unconfirms every annotated field in the targeted occurrence(s); with `--fields`, only those there. Other occurrences are untouched. Mutually exclusive with `--updates`. Mirrors `confirm`'s `--group`/`--occurrence` flags. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> --updates <json> --output json` | **Batched form** — roll back SEVERAL occurrences in ONE atomic call. `--updates` is a JSON array `[{"occurrence":<0-based-index>,"fields"?:["<field_id>",…]}]`. Per entry: omit `"fields"` to unconfirm every annotated field in that occurrence, or list specific IDs. Occurrences not listed are left as-is. Mutually exclusive with `--fields`/`--occurrence`. |
| `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json` | Mark the listed fields as missing (`--fields` has short alias `-f`; annotated with no value and no location) — use when a field is genuinely absent from the document and IXP predicted no value for it. Unlike `confirm --fields`, it also marks a field that's gone from the current predictions entirely (e.g. a stale prior annotation after a model/taxonomy change), which `confirm` can't reach. **Only for fields where IXP predicted no value** — if IXP predicted a *wrong* value, leave the field unannotated instead. Returns `Unmatched` for any IDs not found in the document's annotation OR prediction. |

### Occurrence numbering and read order

`Occurrence` is the row's position in the read that reported it, not a stable row id — a repeatable group's rows have no per-row identifier in the contract (`field_group.id` is the taxonomy group id and is identical for every row).

The server pairs annotations with predictions and returns the **matched pairs first**, then the unmatched predictions. Confirming one row therefore moves it to `Occurrence` 0 on the next read and shifts the others down (the IXP UI shows it first too). The row's values and page location are unchanged — only its position in the read moves. Document order holds only for a group with no annotations, or one where every row is annotated.

So an `Occurrence` value is invalidated by any write to its group:

- confirm/unconfirm every target row in ONE `--updates` call — all indices in a call resolve against the same read;
- between sequential per-occurrence calls, re-run `get-predictions` and re-locate each row by its field values;
- never carry an index across a write.

## Deployments

Publishing a version (`projects publish`) makes it usable **inside** the project. Deploying it to an Orchestrator folder is the separate step that makes it callable **at runtime** — activity packs and Maestro Flow address a model by the `{FolderKey, DeploymentName}` pair.

| Command | Description |
|---------|-------------|
| `uip ixp deployments create <project-name> --version <N> --folder-key <guid> [--title <title>] --output json` | Deploy a trained model version to an Orchestrator folder. **Only ever adds** — never repoints an existing deployment (see [create vs upgrade](#create-vs-upgrade)). `--version` and `--folder-key` are both **required**; `--title` defaults to the project name minus its `-ixp` suffix. Returns `ProjectName`, `ModelVersion`, `FolderKey`, `DeploymentTitle`, `DeploymentName` (Code: `IxpDeploymentsCreate`). |
| `uip ixp deployments upgrade <project-name> <deployment-name> --version <N> --folder-key <guid> --output json` | Move an existing deployment to another trained model version. `<deployment-name>` is a positional argument and takes the **`DeploymentName`** from `deployments list` — NOT the title (Code: `IxpDeploymentsUpgrade`). |
| `uip ixp deployments list <project-name> --output json` | List the project's deployments across every version and folder. **The only reliable source of `DeploymentName`.** `Data` is an array — `[]` for a never-deployed project, never a `{Message: ...}` object, so iterate unconditionally. Each entry carries `DeploymentName`, `DeploymentTitle`, `ModelVersion`, `FolderKey`, `DeployedAt` (Code: `IxpDeploymentsList`). |
| `uip ixp deployments get-taxonomy <project-name> --version <N> --output json` | Get the project taxonomy (data types + field groups) at a specific trained model version. `--version` is **required** (non-negative integer; 0 is valid; no short alias) — get the number from `projects list-models`. Like `projects get-taxonomy`, the body is the raw IXP dataset artifact in snake_case, under `Data.dataset` (`entity_defs[]` + `label_groups[]`), bound to the snapshot the version was trained on (Code: `IxpDeploymentsGetTaxonomy`). |

### create vs upgrade

Two commands, not one. `create` only adds; `upgrade` moves an existing deployment.

| Existing deployment in the folder | `create` | `upgrade` |
|---|---|---|
| none | deploys | `404 [DeploymentNotFoundError]` |
| same model version | no-op, exit `0` | no-op, exit `0` — `DeployedAt` does not move |
| different model version | `409 [DeploymentAlreadyExistsError]` | repoints |

Both verbs are no-ops at the same version, so both are safe to re-run from CI. `create` has **no `--force`** — use `upgrade` to repoint.

`upgrade` changes which model version **every runtime caller of that folder and name** gets. Confirm the intent before running it against a shared folder.

`upgrade`'s response echoes the *requested* version without re-reading. Call `list` to prove the move landed.

### DeploymentName vs DeploymentTitle

Distinct fields. Confusing them is the failure mode this command split exists to prevent.

- `--title` sets `DeploymentTitle` — free-form, returned verbatim.
- `DeploymentName` is the name the **runtime** resolves: the backend slugs the title and appends a per-deployment suffix (`invoices` → `invoices-08963f00-ixp`).
- The suffix is generated per deployment and **cannot be predicted from the request** — two deployments of the same project in the same folder get different suffixes, and it matches neither the project name's suffix nor the folder key. Read `DeploymentName` off the create response or from `list`; never construct it.
- A deploy with no `--title` still gets its own suffix. `DeploymentName` is never just the project name.
- When `create` returns `DeploymentName: null` (the backend had not yet listed the new deployment), get it from `list`.
- `upgrade` takes `DeploymentName`. Passing a title lands a `404 [DeploymentNotFoundError]`.

### --folder-key

Required on both `create` and `upgrade`; passed in the body, never as a path. The same name can be deployed in several folders, so the folder is part of the deployment identity — there is no tenant-level or default-folder deploy. Get keys from `uip or folders list --output json`. There is no `--folder-path` form, and the key format is not validated client-side (the backend owns what a valid key is), so a malformed key fails server-side.

When filtering the folder list, pass an explicit `--limit` — `--output-filter` without one is rejected on current CLIs (older builds silently filter a single page):

```bash
uip or folders list --limit 500 --output json --output-filter "[?Path=='Shared'].Key"
```

Omitting either required option fails locally with exit `3` / `Result: ValidationError` before any auth or backend call. `--version 0` is valid — versions are 0-based.

### Deployment errors

| Surfaced error | Meaning | Fix |
|---|---|---|
| `409 [DeploymentAlreadyExistsError]` on `create` | The title is already deployed in that folder on a **different** version | Run `upgrade` with the `DeploymentName` from `list` — NOT the title the backend's message quotes |
| `404 [DeploymentNotFoundError]` on `upgrade` | Name was never deployed, is deployed only in **another** folder, or a *title* was passed where `DeploymentName` belongs | Re-read `DeploymentName` from `list`; verify `--folder-key` |
| `404 [ModelVersionNotFoundError]` on `upgrade` | `--version` is not deployable (the version is checked before the deployment is looked up) | Pick a version from `projects list-models <project-name> --output json` |
| `408 Timed out waiting for new model version` on `upgrade` | Upstream IXP timeout. The CLI surfaces it without retrying, and the outcome is **unknown** — the write may or may not have landed | Run `list` and read the version actually being served before retrying. Do not assume either outcome |
| `409 [AmbiguousDeploymentError]` | More than one deployment matches in the folder | Disambiguate from `list`; carries the same `create` hint as the conflict above |

**Rejected writes are no-ops** — every `409`/`404` above leaves the deployment on its original version with `DeployedAt` untouched.

**Do not branch on `ErrorCode` for these.** A `409` surfaces as `ErrorCode: invalid_argument`, because `400`/`409`/`422` map alike. Branch on `Context.HttpStatus` or the bracketed backend error name.

**`upgrade` is not a rollback path.** Versions leave the deployable list as a project retrains, so a deployment can be serving a version it can no longer be moved back to. Verify the target is in `projects list-models` first.

After a successful deploy, the folder-scoped runtime API takes roughly 15 seconds to resolve the new deployment. A runtime lookup immediately after `create` can miss it.

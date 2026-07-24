# CLI Commands Reference

All commands use `uip ixp` prefix. Always append `--output json` when parsing output programmatically.

> **Destructive commands require `-y, --yes`.** Every irreversible `uip ixp` command (all `delete`s and `fields change-type`) gates on `-y/--yes`; the CLI never prompts. Always pass `-y/--yes`.

## Projects

| Command | Description |
|---------|-------------|
| `uip ixp projects list [-l <limit>] [--offset <n>] --output json` | List IXP projects — returns a paged envelope `Data: { Projects: [{ Id, Name, Title, CreatedAt }], Total, Offset, Limit }` (rows under `Projects`, **not** a bare array). `-l, --limit` defaults 50 (range 1-10000); `--offset` defaults 0 to page. |
| `uip ixp projects get <project-name> --output json` | Get a project |
| `uip ixp projects create "<name>" <folder-path> [-d "<description>"] [--skip-taxonomy] --output json` | Create project and upload supported docs in `<folder-path>` (top-level only — sub-folders are not scanned; see [Supported document files](#supported-document-files)). By default suggests+imports taxonomy. `-d` provides context for better taxonomy suggestion. Use `--skip-taxonomy` to create a blank project (import taxonomy separately). Use `ProjectName` from output. |
| `uip ixp projects import-taxonomy <project-name> <file> --output json` | Import taxonomy from a local JSON file. Accepts `{ field_types, label_group }` or `{ entity_defs, label_groups }` format. |
| `uip ixp projects update-title <project-name> "<new-title>" --output json` | Update the display title of a project |
| `uip ixp projects update-prompt <project-name> --prompt "<text>" --output json` | Update the project's **Overall extraction instructions** — the taxonomy-wide prompt the model sees on every extraction (the field at the top of the IXP UI's Manage Taxonomy page). Distinct from per-field-group prompts (`groups update-prompts`) and per-field prompts (`fields update-prompts`). Replaces the existing value. |
| `uip ixp projects get-taxonomy <project-name> --output json` | Export the raw IXP taxonomy artifact. Data is `{ status, dataset: { entity_defs, label_groups } }` — read `entity_defs` and `label_groups` under `dataset`. Intended for re-import (see `import-taxonomy`), not a human-readable view. |
| `uip ixp projects get-metrics <project-name> [--model-version <N>] --output json` | Get validation metrics. **Validated model →** flat Data: `ProjectScore`, `ProjectScoreQuality`, `ValidatedDocuments`, `ModelVersion`, plus per-group `FieldGroups[]` (`FieldGroup`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`) and per-field `Fields[]` (`FieldGroup`, `FieldId`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`, `Annotations`, `Quality`). **Trained but not yet validated →** Data is `{ Metrics: null }` (not an error). **No trained model yet (e.g. a project with no confirmed labellings) →** the call returns a failure envelope `Result: Failure` with `ErrorCode: not_found` (no `Data`), NOT `{ Metrics: null }` — treat it as "no metrics yet". Defaults to the latest version; pass `--model-version <N>` (`-m`, `latest` or an integer) to scope to a specific trained version. |
| `uip ixp projects configure-model <project-name> [options] --output json` | Configure extraction model. Options: `--model` (gemini_2_5_flash/gemini_2_5_pro/gpt_4o_2024_05_13) and `--preprocessing` (none/table_mini/table). |
| `uip ixp projects list-models <project-name> --output json` | List all model versions and tags. Returns `Models[]` (`Version`, `ModelName`, `Pinned`, `TrainedTime`, `Description`), `Tags[]` (`Name`, `Version`, `UpdatedAt`), and `MaxPublished`. |
| `uip ixp projects publish <project-name> [--model-version <N>] [--tag <live\|staging>] --output json` | Publish a model version — defaults to the latest; pass `-m, --model-version <N>` to pick a specific one. `-d, --description "<text>"` sets a description; `--tag <live\|staging>` tags the published version. |
| `uip ixp projects unpublish <project-name> --model-version <N> --output json` | Unpublish a model version — it stays trained and listable; only its published status is removed. `--model-version` is **required**. Errors if the version isn't found or isn't currently published. To change which version is live, `publish` a different one instead. |
| `uip ixp projects untag <project-name> --tag <live\|staging> --output json` | Remove a tag by **name** (`--tag` is **required**; tag names are unique within a project, so this is unambiguous even when one version holds several tags). The version the tag pointed at stays published; only that tag is cleared. Errors if no version carries the tag. Only `untag` removes a tag — `publish` without `--tag` leaves the existing tag untouched. To switch `live`→`staging`, `publish --tag staging` instead. |
| `uip ixp projects delete <project-name> -y --output json` | **Permanently** delete a project — its documents, taxonomy, and trained models. **Irreversible.** `-y, --yes` is **required**; the command refuses to run without it (the CLI never prompts). |

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

Each upload triggers a retrain — wait ~2 min before reading metrics or predictions for new docs.

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

`Date`, `Number`, and `Monetary Quantity` carry pre-trained models with a fixed output format (e.g. `Monetary Quantity` normalises `"1M USD"`, `"USD 1000000"`, and `"1,000,000 usd"` all to `1,000,000.00 USD`) — instructions cannot change their formatting, so a hand-rolled equivalent is strictly worse. `Choice` is the only `--kind` with no default: choice types are always project-specific (`data-types add --kind choice --choices …`).

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

## Labellings

| Command | Description |
|---------|-------------|
| `uip ixp labellings get-predictions <project-name> [document-id] --output json` | Get IXP model predictions for all documents (or a single document). Returns `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`. Each `Predictions[]` entry is one document `{ DocumentId, Labels[] }`; each label is `{ Name, Occurrence, Fields[] }`; each field is `{ FieldId, FieldName, FormattedValue }`. This is the model's **prediction** layer, not the confirmed/annotation layer. Each label carries an explicit `Occurrence` (the value for `--occurrence`/`--updates`); it is 0-based and usually runs 0..N-1 in document order, but do NOT assume it is contiguous or starts at 0 — a single-occurrence group can come back as `Occurrence` 1 with no 0. Always target the actual `Occurrence` value reported here, never a positional guess. |
| `uip ixp labellings confirm <project-name> <document-id> [--fields <ids>] [--corrections <json>] --output json` | Confirm predictions for a document. (`--fields` has short alias `-f`; `--corrections` has short alias `-c`.) Without `--fields`, confirms every predicted field that has content. `--fields "a7c3e9105f2b4d86,b2f8a01c7d3e6940"` confirms only those fields, and applies a **single uniform rule**: listed fields with content get confirmed; listed fields whose IXP prediction is empty get a missing marker (the explicit listing IS the confirmation that the empty state is intentional — see Critical Rule 12). `--corrections '[{"field_id":"...","value":"..."}]'` is **only for OCR-mangled values** — same field, same location, garbled bytes. Do NOT use `--corrections` to flip wrong booleans, fix wrong inferred values, or override any non-OCR mistake; those fields must be left unannotated. See Critical Rule 8. Existing missing markers and other annotations carry forward across calls. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --occurrence <N> [--fields <ids>] [--corrections <json>] --output json` | **Single-occurrence form** — confirm ONE occurrence. The ergonomic choice for a single line. `--occurrence` is the 0-based index of the target extraction within `--group`. Without `--fields`, confirms every predicted field in that one occurrence; with `--fields`, confirms only those fields there. Other occurrences are untouched. Requires `--group`. Mutually exclusive with `--updates`. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --updates <json> --output json` | **Batched form** — confirm SEVERAL occurrences in ONE atomic call (one request; avoids N round-trips, e.g. a 10-line invoice). `--updates` is a JSON array `[{"occurrence":<0-based-index>,"fields"?:["<field_id>",…],"corrections"?:{"<field_id>":"<value>"}}]`. Per entry: **omit `"fields"`** to confirm every predicted field in that occurrence (same default as `--occurrence` without `--fields`), or list specific IDs; un-selected fields in a selected occurrence carry forward any existing annotation. **`--updates` is the superset** — `--occurrence <N>` ≡ `--updates` with one entry; both share the same per-occurrence logic. Use `--occurrence` for a single line, `--updates` for several together. Mutually exclusive with `--fields`/`--corrections`/`--occurrence`. |
| `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` | Roll back confirmations on a document (`--fields` has short alias `-f`) — the listed fields go back to un-annotated state. Use when an earlier `confirm` was a mistake (confirm can't un-confirm — Critical Rule 14). Every other annotation on the document is carried forward. **With `--fields` alone, a field id shared across occurrences of a repeatable group is removed from all of them**; to scope the roll-back to specific occurrences, add `--group` (see the two rows below). Returns `Unmatched` for IDs that weren't annotated to begin with. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> [--occurrence <N>] [--fields <ids>] --output json` | **Per-occurrence form** — roll back specific occurrences of a repeatable group instead of every occurrence a field id appears in. `--group` alone unconfirms every occurrence of the group; add `--occurrence <N>` (0-based, same index as `get-predictions`/`confirm`) to roll back ONE occurrence. Without `--fields`, unconfirms every annotated field in the targeted occurrence(s); with `--fields`, only those there. Other occurrences are untouched. Mutually exclusive with `--updates`. Mirrors `confirm`'s `--group`/`--occurrence` flags. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> --updates <json> --output json` | **Batched form** — roll back SEVERAL occurrences in ONE atomic call. `--updates` is a JSON array `[{"occurrence":<0-based-index>,"fields"?:["<field_id>",…]}]`. Per entry: omit `"fields"` to unconfirm every annotated field in that occurrence, or list specific IDs. Occurrences not listed are left as-is. Mutually exclusive with `--fields`/`--occurrence`. |
| `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json` | Mark the listed fields as missing (`--fields` has short alias `-f`; annotated with no value and no location) — use when a field is genuinely absent from the document and IXP predicted no value for it. Unlike `confirm --fields`, it also marks a field that's gone from the current predictions entirely (e.g. a stale prior annotation after a model/taxonomy change), which `confirm` can't reach. **Only for fields where IXP predicted no value** — if IXP predicted a *wrong* value, leave the field unannotated instead. Returns `Unmatched` for any IDs not found in the document's annotation OR prediction. |

## Deployments

For working with runtime (deployed) IXP models — separate from the training workflow above.

| Command | Description |
|---------|-------------|
| `uip ixp deployments get-taxonomy <project-name> --version <N> --output json` | Get the project taxonomy (data types + field groups) at a specific trained model version. `--version` is **required** (non-negative integer; 0 is valid; no short alias) — get the number from `projects list-models`. Like `projects get-taxonomy`, the body is the raw IXP dataset artifact in snake_case, under `Data.dataset` (`entity_defs[]` + `label_groups[]`), bound to the snapshot the version was trained on (Code: `IxpDeploymentsGetTaxonomy`). |

### Runtime extraction

Runtime extraction runs a **published (deployed) model** on a new file — the live runtime path, not the training-data prediction path. **Async, two-step flow:**

1. `uip ixp extraction start <project-id> <file> --tag <tag> --output json` — uploads the file and starts extraction; returns an `operationId` immediately (does **not** wait for the result). **File types:** same whitelist as document upload — see [Supported document files](#supported-document-files). Redirect the response to a file under the project working dir so a later session can resume the poll — same pattern as saving a taxonomy snapshot:

   ```bash
   uip ixp extraction start <project-id> <file> --tag <tag> --output json \
     > /tmp/ixp/<project-name>/<file>.extraction.json
   ```
2. `uip ixp extraction get-result <project-id> <operation-id> --tag <tag> --output json` — fetches the operation by id: still running, the extracted fields when done, or a failure. **Output** on completion (Code `IxpExtractionGetResult`): `Data` is an array of field groups, each `{ "fieldGroupName": "<name>", "fields": [{ "name": "<field>", "value": "<extracted>" }] }`.

> **Runtime extraction vs `labellings get-predictions` — two separate workflows, NOT two ways to process one file.** You never pick between them for a given document; they differ in how the file gets in and which model runs:
> - **Design-time (`labellings get-predictions`)** — the labelling/review loop against the *draft* model. Two steps: `documents upload` first adds the file to the **training set**, then `get-predictions` returns the draft model's predictions on that already-uploaded document to label and review. The file lives in the training set.
> - **Runtime (`extraction start`)** — production extraction against a *published* model. One step: the file is passed inline to `extraction start`, which uploads it as part of the call — there is **no** separate upload command and the file is **not** added to the training set. Use it to run a deployed model on a fresh document.

#### Project **Id**, not Name

Unlike every other `uip ixp` command (which take the project `Name` slug — Critical Rule 7), the runtime extraction commands take the project **Id** (a GUID). If you already hold the GUID (the user gave it, or it's in context from an earlier `projects list`), use it directly — no lookup call. Otherwise — the usual case, where the user names a project by **Title or Name** — resolve its `Id` by calling `uip ixp projects list --output json` and picking the entry whose `Title` or `Name` matches. If nothing matches, the title/name is wrong — list projects and confirm. If **more than one** matches, STOP and ask which project (Critical Rule 16).

Pass that `Id` as `<project-id>` to **all extraction commands**.

#### `--tag` (required)

`--tag` is **required** on all extraction commands — `live` (production) or `staging`; those are the only two tags (see `projects publish --tag`). Use the **same tag and project-id** for `extraction start` and every `extraction get-result` poll of that operation. (There is no `--version`; runtime extraction is tag-only.)

#### Polling — you drive it

`extraction start` returns as soon as extraction begins; the CLI no longer waits or polls. **Poll `extraction get-result` every 5 seconds until it returns a terminal shape** (finished or failed — below). Do NOT impose an arbitrary time cap: extraction runs server-side and continues whether or not you poll, so quitting early neither cancels it nor makes it finish sooner. If your own turn/time budget runs out before the operation resolves, report the resumable `operationId` (persisted in step 1) and stop — a later session can pick up the same poll. `extraction get-result` returns one of three shapes (Code `IxpExtractionGetResult`):

| State | Envelope | What to do |
|-------|----------|------------|
| Still running | `Result: Success`, `Data: { operationId, status }` where `status` is `NotStarted` or `Running`, plus `Instructions` "…still in progress…". | Wait 5 s and poll again. |
| Finished | `Result: Success`, `Data` is the **array of field groups** (no `status` field). | Done — report the fields. |
| Failed | `Result: Failure` (model failure, or a digitization/extractor timeout — the backend has **no timeout status**, it surfaces as a failure). | Stop and report the error. |

> The framework operation status is only `NotStarted \| Running \| Failed \| Succeeded` — there is **no `Timeout` status**. When extraction runs too long the backend itself ends the operation as `Failure` (surfaced by `extraction get-result`) rather than inventing a distinct timeout state — so the backend owns the timeout, not you. Poll until `extraction get-result` is terminal; don't guess a client-side deadline.

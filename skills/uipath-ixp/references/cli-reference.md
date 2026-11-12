# CLI Commands Reference

All commands use `uip ixp`; run `--output json` when parsing output programmatically. Run destructive `delete` and `fields change-type` commands with `-y, --yes`; the CLI never prompts. JSON options take files: `--updates-file`, `--fields-file`, and `--choices-file` (Critical Rule 5).

Instructions/prompts are limited to **4096 characters** at every level; names/field types to **64**, project names to **116**, and project/deployment titles to **1024**. Exceeding a limit fails the whole call with `Result: ValidationError` and writes nothing; shorten and retry rather than splitting one prompt across calls.

## Projects

| Command | Behavior |
|---|---|
| `uip ixp projects list [-l <limit>] [--offset <n>] --output json` | Returns paged `Data: { Projects: [{ Id, Name, Title, CreatedAt }], Total, Offset, Limit }`; rows are under `Projects`, not a bare array. `-l, --limit` defaults to 50 (range 1-10000); `--offset` defaults to 0. |
| `uip ixp projects get <project-name> --output json` | Get a project. |
| `uip ixp projects create "<name>" [<folder-path>] [-d "<description>"] [--skip-taxonomy] --output json` | Create a project and upload supported documents only from the top level of `<folder-path>`; subfolders are not scanned (see [Supported document files](#supported-document-files)). By default suggest/import taxonomy; `-d` supplies taxonomy context. Run with `--skip-taxonomy` to upload without taxonomy and import it separately. Without `<folder-path>`, create an empty project with no documents/taxonomy; `--skip-taxonomy` then has no effect. Use `ProjectName` from output. |
| `uip ixp projects import-taxonomy <project-name> <file> --output json` | Import `{ field_types, label_group }` or `{ entity_defs, label_groups }`. To copy taxonomy, import a user file or another project's `get-taxonomy` dump into a project with no taxonomy. Import merges by NAME; `field_id` is not identity and is re-minted on collision. Against existing content, omitted entries remain, renamed entries are added beside old names, and a field added to another group remains in the first. Same-name fields/groups overwrite instructions and data type because CLI always sends `overwrite_duplicates: true`. Returns `{"status":"ok"}` either way. Accepts only ONE, default label group. |
| `uip ixp projects update-title <project-name> "<new-title>" --output json` | Update display title. |
| `uip ixp projects update-prompt <project-name> --prompt "<text>" --output json` | Replace project-wide **Overall extraction instructions**, distinct from `groups update-prompts` and `fields update-prompts`. |
| `uip ixp projects get-taxonomy <project-name> --output json` | Returns raw artifact `Data: { status, dataset: { entity_defs, label_groups } }`; read under `dataset`. Import only `Data.dataset` (for example `jq '.Data.dataset'`), not the whole response. It is not human-readable. `dataset` also contains `_model_config`, the only read path for configured extraction model/preprocessing; see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing). |
| `uip ixp projects get-metrics <project-name> [--model-version <N\|latest>] --output json` | For a validated model, flat `Data` contains `ProjectScore`, `ProjectScoreQuality`, `ValidatedDocuments`, `ModelVersion`; `FieldGroups[]` contains `FieldGroup`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`; `Fields[]` contains `FieldGroup`, `FieldId`, `Name`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`, `Annotations`, `Quality`. `Name` is that version's taxonomy display name; reporting/joining `FieldGroup`/`FieldId`/`Name` is SKILL.md Critical Rule 21. `Name` is `null` only when the version taxonomy is unreadable, then every name is `null`; use `FieldId` and rerun if needed. Long decimal tails are float rounding: round for display, compare raw values. A trained but unvalidated model returns `{ Metrics: null }`. With no trained model, returns `Result: Failure`, `ErrorCode: not_found`, and no `Data`; treat as no metrics. Default is the **latest trained**, not necessarily published/live; resolve with `list-models` and pass `--model-version <N>` whenever reporting a score (SKILL.md Critical Rule 20). Any ever-scored version remains readable, including versions no longer listed; `not_found` for a version means never scored. See [Improve Prompts Guide § What get-metrics returns](improve-prompts-guide.md#what-get-metrics-returns-and-which-values-decide). `ErrorRate` is `errors / Annotations`, not `1 - Precision`; `Quality` and `ProjectScoreQuality` scales are inconsistent, so never gate on them. |
| `uip ixp projects configure-model <project-name> [options] --output json` | Configure with `--model` (`gemini_2_5_flash`/`gemini_2_5_pro`/`gpt_4o_2024_05_13`) and/or `--preprocessing` (`none`/`table_mini`/`table`). Read current settings as described in [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing). |
| `uip ixp projects list-models <project-name> --output json` | Returns `Models[]` (`Version`, `ModelName`, `Pinned`, `TrainedTime`, `Description`), `Tags[]` (`Name`, `Version`, `UpdatedAt`), and `MaxPublished`. This is the only read path for live version: use `Tags[]` Name=`live`, otherwise highest `Models[]` with `Pinned: true`. Folder runtime version is separate; see [Deployments](#deployments). `ModelName` is trained labeller family (for example `gemini_ixp`, `gemini_pro_ixp`), never a `--model` value and not the configured extraction model. |
| `uip ixp projects publish <project-name> [--model-version <N>] [--tag <live\|staging>] --output json` | Publish, defaulting to latest; `-m, --model-version <N>` selects a version. `-d, --description "<text>"` sets description; `--tag <live\|staging>` tags it. |
| `uip ixp projects unpublish <project-name> --model-version <N> --output json` | Required `--model-version`; remove published status while retaining trained/listable version. Errors if missing or not published. Publish another version to change live. |
| `uip ixp projects untag <project-name> --tag <live\|staging> --output json` | Required tag; names are unique, so removal is unambiguous. Version remains published. Errors if no version carries it. Only `untag` removes a tag; publish without `--tag` preserves tags. Switch `live` to `staging` with `publish --tag staging`. |
| `uip ixp projects delete <project-name> -y --output json` | Permanently and irreversibly delete project, documents, taxonomy, and trained models. `-y, --yes` is required; CLI never prompts. |

### Reading the current model and pre-processing

There is **no `get-model-config` command**; `configure-model` only writes. Run:

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

Read `Data.dataset._model_config`. Report `_model_config.model_version` verbatim as the `--model` value; never report `list-models` `ModelName` (`gemini_ixp` is a trained labeller family and has no preprocessing information).

| `_model_config.input_config` | Report `--preprocessing` |
|---|---|
| `null` | *not configured* (IXP default), not `none` |
| `{"mode": "image_only"}` | `none` |
| `{"mode": "text_plus_image", "text_config": {"kind": "uipath_cv_table_only"}}` | `table_mini` |
| `{"mode": "text_plus_image", "text_config": {"kind": "gemini_table_only"}}` | `table` |

Other keys (`kind`, `flags`, `attribution_method`, `temperature`, `top_p`, `seed`, `system_prompt_override`, `iterative_config`) have no `uip ixp` flag; mention them only if asked. `_model_config` is the current project setting, not the setting used to build a trained version; report it as project configuration.

## Documents

| Command | Behavior |
|---|---|
| `uip ixp documents list <project-name> [-l <limit>] [--offset <n>] --output json` | Returns `Data: { Documents: [{ DocumentId, AttachmentRef, Filename }], Total, Offset, Limit }`; rows are under `Documents`, not a bare array. `AttachmentRef` and `Filename` may be `null`; `Filename` is original upload filename. `-l, --limit` defaults 50 (range 1-10000); `--offset` defaults 0 (range 0-1000000). |
| `uip ixp documents download <project-name> <document-id> -o <path> --output json` | Download original to `-o`. For `Data.ContentType` `application/pdf` or `image/png\|jpeg\|gif\|tiff\|bmp`, CLI appends an extension to extensionless paths or replaces a mismatched supported extension; other types such as `application/octet-stream` leave path unchanged. Always use final `Data.Path`; no extension means unknown type. |
| `uip ixp documents upload <project-name> <file> --output json` | Upload one; see [Uploading documents](#uploading-documents-to-an-existing-project). |
| `uip ixp documents delete <project-name> <document-id> -y --output json` | Irreversibly delete document and labellings; triggers retrain. `-y, --yes` required; without it CLI refuses and exits 1. |

### Supported document files

The same case-insensitive whitelist applies to `projects create` and `documents upload`: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.tif`, `.tiff`, `.bmp`.

- `documents upload` rejects unsupported extensions before network with `Unsupported file type "<ext>"`.
- `projects create` scans only top-level `<folder-path>`, silently skips unsupported files, and fails only if none are supported: `No supported documents found in <folder>`.

Each upload triggers retrain; wait under [Improve Prompts Guide § Waiting for retrain](improve-prompts-guide.md#waiting-for-retrain) before reading metrics or predictions for new documents.

### Uploading documents to an existing project

Run `uip ixp documents upload <project-name> <file> --output json` once per file in an existing project. It returns `{ ProjectName, Filename, AttachmentRef, DocumentId }` (Code: `IxpDocumentsUpload`); capture `DocumentId` for `documents download` or `labellings confirm`. For validation and retrain timing, see [Supported document files](#supported-document-files). For multiple files, loop one call per file:

```bash
cd "<folder-with-docs>"
for f in *.pdf *.png *.jpg *.jpeg *.gif *.tif *.tiff *.bmp; do
    [ -e "$f" ] || continue # skip unmatched glob patterns
    uip ixp documents upload <project-name> "$f" --output json
done
```

For a new project, prefer `projects create <name> <folder-path>` to upload the folder and suggest taxonomy in one call.

## Data Types

Manage reusable `entity_defs` referenced by `field_type_id`; in the UI these are Data Types.

| Command | Behavior |
|---|---|
| `uip ixp data-types add <project-name> --name <name> --kind <text\|date\|money\|number\|boolean\|choice> --instructions <text> [--input-value <exact-match\|inferred>] [--choices-file <path>] --output json` | `text` is default Text. `--input-value` is required for `text` and `choice`, forbidden for `date`, `money`, `number`, `boolean`; `exact-match` means verbatim document value, `inferred` computed/derived with no visible location. `--choices-file` is required for `choice`, forbidden otherwise; it contains JSON array `{"value":"<canonical>","alternates":["<alt1>",...]}`. `value` is canonical output; optional `alternates` defaults to `[]` and maps alternate spellings to `value`. |
| `uip ixp data-types update-instructions <project-name> --name <name> --instructions <text> --output json` | Replace instructions; preserve name, kind, and input-value. |
| `uip ixp data-types rename <project-name> --name <name> --new-name <name> --output json` | Rename while preserving field references through `field_type_id`. |
| `uip ixp data-types delete <project-name> --name <name> -y --output json` | Irreversibly delete; fields referencing it via `field_type_id` break. `-y, --yes` required; CLI never prompts. |

### Default data types

Before `data-types add` or selecting `--type` in `fields add`/`groups add`, inspect authoritative `entity_defs` from `projects get-taxonomy` and reuse a matching default. A redundant custom type (e.g. a `Currency Amount` when `Monetary Quantity` already exists) splits annotations and lose the pretrained model. Add only a project-specific `Choice` or reusable concept needing tailored instructions.

| Default type | `--kind` | `--input-value` | Reuse for |
|---|---|---|---|
| `Exact Text` | `text` | `exact-match` | Verbatim names, IDs, addresses, codes |
| `Inferred Text` | `text` | `inferred` | Derived/computed text |
| `Number` | `number` | — | Counts, quantities, plain numbers |
| `Date` | `date` | — | Dates |
| `Monetary Quantity` | `money` | — | Currency amounts: total, subtotal, tax, unit price, freight |
| `Boolean` | `boolean` | — | True/false |

`Date`, `Number`, `Monetary Quantity`, and `Boolean` have pretrained fixed output formats; instructions cannot change formatting, so equivalents are worse. `Choice` has no default and is always project-specific (`data-types add --kind choice --choices-file …`).

### Normalized output formats

`get-predictions` and `confirm` use normalized values, not page literals:

| Type | `FormattedValue` | Page → prediction |
|---|---|---|
| `Date` | `YYYY-MM-DDTHH:MM:SSZ`; date-only values use `T00:00:00Z` | `21-JUN-22` → `2022-06-21T00:00:00Z` |
| `Monetary Quantity` | `<amount> <ISO-4217 code>`; no thousands separator, page decimal precision retained, currency appended if absent | `114.91` → `114.91 AUD`; `8.0700` → `8.0700 USD` |
| `Number` | Bare numeric string, no unit/separator | `29311577` → `29311577` |
| `Boolean` | `True` / `False` | — |

## Groups

Manage `label_defs`, document-type containers for fields. Edit fields in an existing group with `fields`.

| Command | Behavior |
|---|---|
| `uip ixp groups add <project-name> --name <group-name> --instructions <text> --fields-file <path> --output json` | Create group and all new fields in one JSON array `[ {"name":"...","type":"<type-name>","instructions":"..."} ]`; batch all fields, never create then add individually. Every entry requires non-empty `name`, `type`, `instructions`. `type` resolves against `entity_defs`; reuse [default data type](#default-data-types). Use `fields add` for an existing group. Group instructions describe document/section scope. |
| `uip ixp groups delete <project-name> --name <group-name> -y --output json` | Irreversibly delete group and all annotations; `-y, --yes` required. |
| `uip ixp groups rename <project-name> --name <group-name> --new-name <name> --output json` | Rename while preserving fields and annotations. |
| `uip ixp groups update-prompts <project-name> --updates-file <path> --output json` | File is `[ {"name":"<group>","instructions":"..."} ]`, matched by group name; preserve fields. Unmatched names are reported without failure. |

## Fields

Structural edits inside an existing group; use `fields update-prompts` for instruction-only edits and `groups add` to create a group.

| Command | Behavior |
|---|---|
| `uip ixp fields add <project-name> --group <field-group-name> --field <name> --type <type-name> --instructions <text> --output json` | Add to existing group. `--type` names an `entity_def` from `projects get-taxonomy`; reuse [default data type](#default-data-types). `--instructions` is required and must describe what to extract and where. |
| `uip ixp fields delete <project-name> --group <field-group-name> --field <name> -y --output json` | Remove field; `-y, --yes` required and CLI never prompts. |
| `uip ixp fields rename <project-name> --group <field-group-name> --field <name> --new-name <name> --output json` | Rename while preserving `field_id` and annotations. |
| `uip ixp fields change-type <project-name> --group <field-group-name> --field <name> --type <type-name> -y --output json` | Irreversibly replace field and delete annotations; `-y, --yes` required. |
| `uip ixp fields update-prompts <project-name> --updates-file <path> --output json` | File is `[ {"group":"<field-group>","name":"<field>","instructions":"..."} ]`, matched by `label_def` group + `moon_form` field; preserve definitions. Fails if any group or field is absent. |

### Moving a field to a different field group

There is no move/reparent command; `--group` only addresses a field. Move in order:

1. Run `uip ixp projects get-taxonomy <project-name> --output json` and read current `type` and `instructions`. In `Data.dataset`, the field is a `moon_form` under its `label_def`; its type is the `entity_defs[]` entry whose `id` matches `field_type_id`, **not** `field_id`.
2. Run `uip ixp fields add <project-name> --group <target-group> --field <name> --type <type-name> --instructions <text> --output json`.
3. Run `uip ixp fields delete <project-name> --group <source-group> --field <name> -y --output json`.

Add before deleting: if add fails, source remains. Both groups must already exist; creating a missing target is a separate `groups add` step — confirm it with the user first. This is **IRREVERSIBLE**: `fields add` mints a new `field_id`, labels do not follow, and documents must be re-reviewed. Tell the user before starting.

**Do not** edit taxonomy and re-import (SKILL.md Critical Rule 23): `projects import-taxonomy` merges by name, omission does not remove source, and `field_id` is re-minted; the field becomes two fields in both groups while returning `{"status":"ok"}`. `groups delete` + `groups add` is not an alternative because it destroys every other field and annotation in the group.

## Labellings

| Command | Behavior |
|---|---|
| `uip ixp labellings get-predictions <project-name> <document-id> --output json` | Returns `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`; each document is `{ DocumentId, Labels[] }`, label `{ Name, Occurrence, Fields[] }`, field `{ FieldId, FieldName, FormattedValue }`. This is prediction, not confirmation. `Occurrence` is explicit, 0-based, usually 0..N-1 but may be non-contiguous or start at 1; use it, never a positional guess. Read order is unstable because annotated rows come first; see [Occurrence numbering and read order](#occurrence-numbering-and-read-order). Capture each document's `ModelVersion` and pass it to `confirm -m/--model-version` to guard against retrain. |
| `uip ixp labellings confirm <project-name> <document-id> [--fields <ids>] [--model-version <version>] --output json` | `--fields` aliases `-f`. Without it, confirm every predicted field with content. With it, listed fields with content are confirmed and listed empty fields receive a missing marker; explicit listing confirms intentional emptiness (Critical Rule 11). Leave wrong predictions out; they remain unannotated (Critical Rule 8). Existing missing markers/annotations carry forward. `-m, --model-version <N>` pins the `ModelVersion` read; newer retrain causes `PredictionVersionChangedError`; reread and review. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --occurrence <N> [--fields <ids>] [--model-version <version>] --output json` | Confirm one occurrence; `--occurrence` is the 0-based index from latest `get-predictions`. Without `--fields`, confirm all predicted fields there; with it, only listed fields. Other occurrences untouched. Requires `--group` (Critical Rule 12), mutually exclusive with `--updates-file`. A write renumbers subsequent reads; use `--updates-file` for multiple rows. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --updates-file <path> [--model-version <version>] --output json` | Confirm several occurrences atomically. File: `[ {"occurrence":<0-based-index>,"fields"?:["<field_id>",…]} ]`. Omit `fields` to confirm all predicted fields; list IDs to select fields, while unselected fields carry existing annotations. Superset: `--occurrence <N>` equals one-entry `--updates-file`; use occurrence for one row and updates file for several. Mutually exclusive with `--fields`/`--occurrence`. |
| `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` | `--fields` aliases `-f`; remove listed fields to unannotated, carrying other annotations. Confirm cannot unconfirm (Critical Rule 13). With fields alone, shared IDs are removed from all repeatable-group occurrences; add `--group` to scope. Returns `Unmatched` for IDs not previously annotated. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> [--occurrence <N>] [--fields <ids>] --output json` | Scope rollback to group occurrences. `--group` alone targets every occurrence; `--occurrence <N>` targets one, using a fresh read (partial confirmation usually changes its index). Without fields, remove all annotated fields in targets; with fields, only those. Other occurrences untouched; mutually exclusive with `--updates-file`. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> --updates-file <path> --output json` | Atomically roll back several occurrences. File: `[ {"occurrence":<0-based-index>,"fields"?:["<field_id>",…]} ]`; omit fields for all annotated fields, otherwise select IDs. Unlisted occurrences remain; mutually exclusive with `--fields`/`--occurrence`. |
| `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json` | `--fields` aliases `-f`; mark listed fields missing (no value/location) when genuinely absent and IXP predicted no value. Unlike confirm, reaches fields absent from current predictions, including stale annotations after model/taxonomy change. Never use for a wrong predicted value: leave it unannotated. Returns `Unmatched` for IDs in neither annotations nor predictions. |

### Occurrence numbering and read order

`Occurrence` is position in reporting read, not a stable row ID; repeatable rows have no per-row identifier (`field_group.id` is the same taxonomy group ID for every row). `get-predictions` lists annotated occurrences first, then unannotated. Confirming moves a row to `Occurrence` 0 and shifts others; values/page locations do not change. Document order holds only when no rows, or all rows, are annotated.

Any write to a group invalidates occurrence values:

- Confirm/unconfirm all target rows in one `--updates-file`; all indices in that call use the same read.
- Between sequential per-occurrence calls, rerun `get-predictions` and relocate rows by field values.
- Never carry an index across a write.

## Deployments

`projects publish` makes a version usable inside the project. Deployment to an Orchestrator folder makes it callable at runtime; activity packs and Maestro Flow address `{FolderKey, DeploymentName}`.

| Command | Behavior |
|---|---|
| `uip ixp deployments create <project-name> --version <N> --folder-key <guid> [--title <title>] --output json` | Only add; never repoint existing deployment (see [create vs upgrade](#create-vs-upgrade)). `--version` and `--folder-key` required; `--title` defaults to project name minus `-ixp`. Returns `ProjectName`, `ModelVersion`, `FolderKey`, `DeploymentTitle`, `DeploymentName` (Code: `IxpDeploymentsCreate`). |
| `uip ixp deployments upgrade <project-name> <deployment-name> --version <N> --folder-key <guid> --output json` | Move existing deployment. Positional `<deployment-name>` must be `DeploymentName` from `deployments list`, not title (Code: `IxpDeploymentsUpgrade`). |
| `uip ixp deployments list <project-name> --output json` | Only reliable source of `DeploymentName`; lists every version/folder. `Data` is always an array, `[]` for never deployed, never `{Message: ...}`, so iterate unconditionally. Entries contain `DeploymentName`, `DeploymentTitle`, `ModelVersion`, `FolderKey`, `DeployedAt` (Code: `IxpDeploymentsList`). |
| `uip ixp deployments get-taxonomy <project-name> --version <N> --output json` | `--version` required, non-negative integer including 0, no short alias; obtain from `projects list-models`. Returns raw snake_case dataset artifact at `Data.dataset` (`entity_defs[]` and `label_groups[]`) for that trained snapshot (Code: `IxpDeploymentsGetTaxonomy`). |

### create vs upgrade

`create` adds; `upgrade` moves an existing deployment:

| Existing deployment in folder | `create` | `upgrade` |
|---|---|---|
| none | deploys | `404 [DeploymentNotFoundError]` |
| same model version | no-op, exit `0` | no-op, exit `0`; `DeployedAt` unchanged |
| different model version | `409 [DeploymentAlreadyExistsError]` | repoints |

Both are safe to rerun at the same version. `create` has no `--force`; use `upgrade` to repoint. Upgrade changes the version served to every runtime caller of that folder/name; confirm intent for shared folders. Its response echoes requested version without rereading; run `list` to prove the move.

### DeploymentName vs DeploymentTitle

`--title` sets free-form `DeploymentTitle`, returned verbatim. `DeploymentName` is runtime name: slugged title plus per-deployment suffix (for example `invoices-08963f00-ixp`). The suffix is generated, unpredictable, distinct per deployment, and matches neither project suffix nor folder key. Never construct it; read it from create or `list`. A no-title deployment still has a suffix and is never merely the project name. If create returns `DeploymentName: null`, run `list`. `upgrade` requires `DeploymentName`; a title produces `404 [DeploymentNotFoundError]`.

### --folder-key

`--folder-key` is required for create and upgrade. The same name can exist in multiple folders; folder is part of identity. There is no tenant/default-folder deployment or `--folder-path`. Obtain keys from `uip or folders list --output json`; the CLI does not validate the key format, so a malformed key is only rejected by UiPath when the command runs.

When filtering, pass explicit `--limit` because current CLIs reject `--output-filter` without it (older builds silently filter one page):

```bash
uip or folders list --limit 500 --output json --output-filter "[?Path=='Shared'].Key"
```

Omitting either required option fails locally with exit `3` / `Result: ValidationError`; no request is sent, so this is never an authentication or connectivity problem. `--version 0` is valid because versions are 0-based.

### Deployment errors

| Error | Meaning | Fix |
|---|---|---|
| `409 [DeploymentAlreadyExistsError]` on `create` | Same title already deployed in folder at a different version | Run `upgrade` with `DeploymentName` from `list`, not title in error |
| `404 [DeploymentNotFoundError]` on `upgrade` | Never deployed, exists only in another folder, or title supplied | Reread `DeploymentName`; verify `--folder-key` |
| `404 [ModelVersionNotFoundError]` on `upgrade` | Version is not deployable; says nothing about deployment existence | Choose from `projects list-models <project-name> --output json` |
| `408 Timed out waiting for new model version` on `upgrade` | Upstream timeout; CLI does not retry and outcome is unknown | Run `list`, inspect served version, then decide; assume neither outcome |
| `409 [AmbiguousDeploymentError]` | Multiple matching deployments in folder | Disambiguate from `list`; same create-conflict hint applies |

All listed `409`/`404` rejected writes leave original version and `DeployedAt` unchanged. **Do not branch on `ErrorCode` for these.** A `409` surfaces as `ErrorCode: invalid_argument`, because `400`/`409`/`422` map alike; branch on `Context.HttpStatus` or bracketed error name.

`upgrade` is not rollback: retraining can remove versions from the deployable list, leaving a deployment serving a version that cannot be restored. Verify the target in `projects list-models` first. After successful deployment, folder-scoped runtime resolution takes roughly 15 seconds; an immediate lookup can miss it.
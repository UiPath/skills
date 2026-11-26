# CLI Commands Reference

Run all commands with `uip ixp`; run `--output json` for programmatic parsing. Irreversible `delete` and `fields change-type` require `-y, --yes`; the CLI never prompts. Always pass `-y/--yes`. Use `--updates-file`, `--fields-file`, or `--choices-file` for JSON options (Critical Rule 5).

Instructions/prompts are at most **4096 characters** at every level; names/field types at most **64**; project names at most **116**; project/deployment titles at most **1024**. Exceeding a limit fails the whole call with `Result: ValidationError` and writes nothing. Shorten and retry; do not split one prompt across calls.

## Projects

| Command | Contract |
|---|---|
| `uip ixp projects list [-l <limit>] [--offset <n>] --output json` | Return paged `Data: { Projects: [{ Id, Name, Title, CreatedAt }], Total, Offset, Limit }`; rows are under `Projects`, not a bare array. `-l, --limit` defaults 50, range 1-10000; `--offset` defaults 0. |
| `uip ixp projects get <project-name> --output json` | Get a project. |
| `uip ixp projects create "<name>" [<folder-path>] [-d "<description>"] [--skip-taxonomy] --output json` | Create a project. Upload supported documents only from the folder top level; see [Supported document files](#supported-document-files). By default suggest/import taxonomy; `-d` supplies taxonomy context. `--skip-taxonomy` uploads without taxonomy for separate import. Without a folder, create empty (no documents/taxonomy), and `--skip-taxonomy` has no effect. Use `ProjectName` from output. |
| `uip ixp projects import-taxonomy <project-name> <file> --output json` | Import `{ field_types, label_group }` or `{ entity_defs, label_groups }`. To copy taxonomy, pass a user file or another project's `get-taxonomy` dump into a project with no taxonomy. Merge by **NAME**, not `field_id`; colliding IDs are re-minted. Omitted entries remain; renamed entries are new beside old; a field added to another group remains in the first; same-name fields/groups overwrite instructions and data type because the CLI always sends `overwrite_duplicates: true`. Returns `{"status":"ok"}` either way. Accepts only ONE, default label group. |
| `uip ixp projects update-title <project-name> "<new-title>" --output json` | Update display title. |
| `uip ixp projects update-prompt <project-name> --prompt "<text>" --output json` | Replace **Overall extraction instructions** (taxonomy-wide prompt), distinct from `groups update-prompts` and `fields update-prompts`. |
| `uip ixp projects get-taxonomy <project-name> --output json` | Return raw artifact `Data: { status, dataset: { entity_defs, label_groups } }`; read under `dataset`. For import, pass only `Data.dataset` (`jq '.Data.dataset'`), not the whole response. It is not human-readable. `dataset._model_config` is the only read path for configured extraction model/pre-processing; see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing). |
| `uip ixp projects get-metrics <project-name> [--model-version <N\|latest>] --output json` | For a validated model return flat `Data` with `ProjectScore`, `ProjectScoreQuality`, `ValidatedDocuments`, `ModelVersion`, `FieldGroups[]` (`FieldGroup`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`), and `Fields[]` (`FieldGroup`, `FieldId`, `Name`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`, `Annotations`, `Quality`). `Name` is the versioned taxonomy display name; reporting/joining `FieldGroup`/`FieldId`/`Name` is SKILL.md Critical Rule 21. `Name` is `null` only when that taxonomy is unreadable, then every name is null; use `FieldId` and rerun if names are needed. Float tails are rounding, not accuracy: round for display, compare raw values. Trained but unvalidated returns `{ Metrics: null }`. No trained model returns `Result: Failure`, `ErrorCode: not_found`, no `Data`; treat as no metrics. Default is latest **trained**, not necessarily live; resolve with `list-models` and pass `--model-version <N>` when reporting scores (SKILL.md Critical Rule 20). Any ever-scored version remains readable; `not_found` means never scored, not aged out. See [Improve Prompts Guide § What get-metrics returns](improve-prompts-guide.md#what-get-metrics-returns-and-which-values-decide). `ErrorRate` is `errors / Annotations`, not `1 - Precision`; never gate on `Quality`/`ProjectScoreQuality` because scales are inconsistent. |
| `uip ixp projects configure-model <project-name> [options] --output json` | Configure `--model` (`gemini_2_5_flash/gemini_2_5_pro/gpt_4o_2024_05_13`) and `--preprocessing` (`none/table_mini/table`). To read current settings, see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing). |
| `uip ixp projects list-models <project-name> --output json` | Return `Models[]` (`Version`, `ModelName`, `Pinned`, `TrainedTime`, `Description`), `Tags[]` (`Name`, `Version`, `UpdatedAt`), and `MaxPublished`. The only read path for the live version: `Tags[]` Name=`live`, else highest `Models[]` with `Pinned: true`. Folder runtime version is separate: [Deployments](#deployments). `ModelName` is trained-labeller family (`gemini_ixp`, `gemini_pro_ixp`), never a `--model` value or configured extraction model (see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing)). |
| `uip ixp projects publish <project-name> [--model-version <N>] [--tag <live\|staging>] --output json` | Publish, default latest; `-m, --model-version <N>` selects one; `-d, --description "<text>"` sets description; `--tag <live\|staging>` tags it. |
| `uip ixp projects unpublish <project-name> --model-version <N> --output json` | Require `--model-version`; remove published status while retaining trained/listable version. Error if absent or unpublished. Publish another version to change live. |
| `uip ixp projects untag <project-name> --tag <live\|staging> --output json` | Require tag; remove only that tag, leaving publication. Tag names are unique; error if absent. Only `untag` removes a tag; publish without `--tag` leaves it. Publish `--tag staging` to switch `live`→`staging`. |
| `uip ixp projects delete <project-name> -y --output json` | **Permanently and irreversibly** delete documents, taxonomy, and trained models; `-y, --yes` required and CLI never prompts. |

### Reading the current model and pre-processing

There is **no `get-model-config` command**; `configure-model` only writes. Run:

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

Read `Data.dataset._model_config.model_version` and report it verbatim as `--model` (for example `gemini_2_5_flash`), never `list-models.ModelName` (`gemini_ixp`), which has no pre-processing information. Invert `_model_config.input_config`:

| `input_config` | `--preprocessing` |
|---|---|
| `null` | Never configured; report *not configured*, not `none` (IXP default applies). |
| `{"mode": "image_only"}` | `none` |
| `{"mode": "text_plus_image", "text_config": {"kind": "uipath_cv_table_only"}}` | `table_mini` |
| `{"mode": "text_plus_image", "text_config": {"kind": "gemini_table_only"}}` | `table` |

Other keys (`kind`, `flags`, `attribution_method`, `temperature`, `top_p`, `seed`, `system_prompt_override`, `iterative_config`) have no `uip ixp` flag; mention them only on request. `_model_config` is current project configuration, not the setting used to build a particular trained version.

## Documents

| Command | Contract |
|---|---|
| `uip ixp documents list <project-name> [-l <limit>] [--offset <n>] --output json` | Return paged `Data: { Documents: [{ DocumentId, AttachmentRef, Filename }], Total, Offset, Limit }`, rows under `Documents`, not a bare array. `AttachmentRef`/`Filename` may be null; `Filename` is original upload name. `-l, --limit` defaults 50, range 1-10000; `--offset` defaults 0, range 0-1000000. |
| `uip ixp documents download <project-name> <document-id> -o <path> --output json` | Download original. **The CLI sets the extension from the server's content type** — for `Data.ContentType` `application/pdf` or `image/png\|jpeg\|gif\|tiff\|bmp`, it appends one to an extensionless `-o` or replaces a mismatched supported one; other types (for example `application/octet-stream`) leave path unchanged. Always use final `Data.Path`; no extension means unknown type. |
| `uip ixp documents upload <project-name> <file> --output json` | Upload one; see [Uploading documents](#uploading-documents-to-an-existing-project). |
| `uip ixp documents delete <project-name> <document-id> -y --output json` | Irreversibly delete document and labellings, triggering retrain; `-y, --yes` required, CLI never prompts, and omission refuses/exits 1. |

### Supported document files

Bulk create and single upload accept, case-insensitively: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.tif`, `.tiff`, `.bmp`. `documents upload` rejects before network with `Unsupported file type "<ext>"`; `projects create` scans only top level, silently skips unsupported files, and fails only if none are supported: `No supported documents found in <folder>`. Each upload triggers retrain; wait under [Improve Prompts Guide § Waiting for retrain](improve-prompts-guide.md#waiting-for-retrain) before metrics or predictions for new documents.

### Uploading documents to an existing project

Run `uip ixp documents upload <project-name> <file> --output json` once per file. Return `{ ProjectName, Filename, AttachmentRef, DocumentId }` (Code: `IxpDocumentsUpload`); capture `DocumentId` for download or `labellings confirm`. For validation/retrain timing see [Supported document files](#supported-document-files). For multiple files:

```bash
cd "<folder-with-docs>"
for f in *.pdf *.png *.jpg *.jpeg *.gif *.tif *.tiff *.bmp; do
    [ -e "$f" ] || continue   # skip unmatched glob patterns
    uip ixp documents upload <project-name> "$f" --output json
done
```

For a new project, prefer `projects create <name> <folder-path>` to upload and suggest taxonomy in one call.

## Data Types

Manage reusable `entity_defs` referenced by `field_type_id` (the UI's Data Types).

| Command | Contract |
|---|---|
| `uip ixp data-types add <project-name> --name <name> --kind <text\|date\|money\|number\|boolean\|choice> --instructions <text> [--input-value <exact-match\|inferred>] [--choices-file <path>] --output json` | Create. `--input-value` required for `text`/`choice`, forbidden for `date`/`money`/`number`/`boolean`; `exact-match` means verbatim, `inferred` computed/derived. `--choices-file` required for `choice`, forbidden otherwise; JSON array `{"value":"<canonical>","alternates":["<alt1>",...]}`; `value` is canonical model output, optional `alternates` defaults `[]` and maps alternate spellings. |
| `uip ixp data-types update-instructions <project-name> --name <name> --instructions <text> --output json` | Replace instructions; name, kind, and input-value remain. |
| `uip ixp data-types rename <project-name> --name <name> --new-name <name> --output json` | Rename, preserving `field_type_id` references. |
| `uip ixp data-types delete <project-name> --name <name> -y --output json` | Irreversibly delete; referencing fields via `field_type_id` break. `-y, --yes` required; CLI never prompts. |

### Default data types

Before `data-types add` or choosing `--type` in `fields add`/`groups add`, inspect authoritative `entity_defs` from `projects get-taxonomy` and reuse a matching default. Redundant custom types split annotations and lose the default model; add only a genuinely new `Choice` or reusable tailored concept.

| Default type | `--kind` | `--input-value` | Reuse for |
|---|---|---|---|
| `Exact Text` | `text` | `exact-match` | Verbatim names, IDs, addresses, codes |
| `Inferred Text` | `text` | `inferred` | Derived text not verbatim |
| `Number` | `number` | — | Counts, quantities, plain numbers |
| `Date` | `date` | — | Dates |
| `Monetary Quantity` | `money` | — | Currency amounts: total, subtotal, tax, unit price, freight |
| `Boolean` | `boolean` | — | True/false |

`Date`, `Number`, `Monetary Quantity`, and `Boolean` have fixed-format pre-trained models, so instructions cannot alter formatting and a custom equivalent is worse. `Choice` has no default and is always project-specific (`data-types add --kind choice --choices-file …`).

### Normalized output formats

`get-predictions` and `confirm` use normalized values, not page literals:

| Type | `FormattedValue` | Page → prediction |
|---|---|---|
| `Date` | `YYYY-MM-DDTHH:MM:SSZ`; date-only uses `T00:00:00Z` | `21-JUN-22` → `2022-06-21T00:00:00Z` |
| `Monetary Quantity` | `<amount> <ISO-4217 code>`; no thousands separator, page decimal precision retained, currency appended if absent | `114.91` → `114.91 AUD`; `8.0700` → `8.0700 USD` |
| `Number` | Bare numeric string, no unit/separator | `29311577` → `29311577` |
| `Boolean` | `True` / `False` | — |

## Groups

Manage `label_defs`, document-type containers for fields. Edit existing-group fields with `fields`.

| Command | Contract |
|---|---|
| `uip ixp groups add <project-name> --name <group-name> --instructions <text> --fields-file <path> --output json` | Create group and all fields in one batch. `--instructions` describes what document/section the group covers (the model sees it during extraction). JSON is `[ {"name":"...","type":"<type-name>","instructions":"..."} ]`; each entry requires non-empty `name`, `type`, `instructions`. Resolve `type` in `entity_defs`; reuse [default data type](#default-data-types). Do not create then add fields individually. Use `fields add` for an existing group. |
| `uip ixp groups delete <project-name> --name <group-name> -y --output json` | Irreversibly delete group and all field annotations; `-y, --yes` required, CLI never prompts. |
| `uip ixp groups rename <project-name> --name <group-name> --new-name <name> --output json` | Rename; fields and annotations persist. |
| `uip ixp groups update-prompts <project-name> --updates-file <path> --output json` | File `[ {"name":"<group>","instructions":"..."} ]`, matched by group name; preserve fields and report unmatched names without failing. |

## Fields

Structural edits within an existing group; use `fields update-prompts` for instruction-only edits and `groups add` to create a group.

| Command | Contract |
|---|---|
| `uip ixp fields add <project-name> --group <field-group-name> --field <name> --type <type-name> --instructions <text> --output json` | Add to existing group. `--type` is an `entity_defs` name; reuse [default data type](#default-data-types); required `--instructions` must say what/where to extract. |
| `uip ixp fields delete <project-name> --group <field-group-name> --field <name> -y --output json` | Remove; `-y, --yes` required and CLI never prompts. |
| `uip ixp fields rename <project-name> --group <field-group-name> --field <name> --new-name <name> --output json` | Rename, preserving `field_id` and annotations. |
| `uip ixp fields change-type <project-name> --group <field-group-name> --field <name> --type <type-name> -y --output json` | Irreversibly replace field and delete annotations; `-y, --yes` required. |
| `uip ixp fields update-prompts <project-name> --updates-file <path> --output json` | File `[ {"group":"<field-group>","name":"<field>","instructions":"..."} ]`, matched by `label_def` group + `moon_form` field; preserve definitions and fail if group/field absent. |

### Moving a field to a different field group

There is no move/reparent command; `--group` only addresses a field. Move in order:

1. Run `uip ixp projects get-taxonomy <project-name> --output json`; in `Data.dataset`, read the field's `type` and `instructions` from its `moon_form` entry under `label_def`. Resolve its type as the `entity_defs[]` entry whose `id` equals `field_type_id`, **not** its own `field_id`.
2. Run `uip ixp fields add <project-name> --group <target-group> --field <name> --type <type-name> --instructions <text> --output json`.
3. Run `uip ixp fields delete <project-name> --group <source-group> --field <name> -y --output json`.

Add before delete; if add fails, source remains. Both groups must exist. If target is absent, creating it is a separate `groups add` step to confirm. This is **irreversible**: add mints a new `field_id`, so confirmed labels do not follow and documents require re-review; tell the user first.

**Do NOT move a field by editing taxonomy and re-importing** (SKILL.md Critical Rule 23): import merges by name, does not remove the old field, and re-mints `field_id`, producing `{"status":"ok"}` with separate fields in both groups. `groups delete` + `groups add` is not an alternative because it destroys every other field and annotation in the group.

## Labellings

| Command | Contract |
|---|---|
| `uip ixp labellings get-predictions <project-name> <document-id> --output json` | Return `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`; each prediction document `{ DocumentId, Labels[] }`, label `{ Name, Occurrence, Fields[] }`, field `{ FieldId, FieldName, FormattedValue }`. This is prediction, not confirmed layer. `Occurrence` is 0-based but need not be contiguous or start at 0 — a single-occurrence group can come back as `Occurrence` 1 with no 0; use it, never a positional guess. Annotated occurrences sort first and renumber after writes; see [Occurrence numbering and read order](#occurrence-numbering-and-read-order). Capture document `ModelVersion` and pass it to `confirm -m/--model-version` to guard against retraining during review. |
| `uip ixp labellings confirm <project-name> <document-id> [--fields <ids>] [--model-version <version>] --output json` | `--fields` alias `-f`. Without it, confirm every predicted field with content. With it, listed fields with content confirm; listed empty predictions receive missing markers (explicit listing confirms intentional empty state; Critical Rule 11). Leave wrong predictions out (Critical Rule 8). Existing missing markers/annotations carry forward. `-m, --model-version <N>` pins reviewed `ModelVersion`; drift rejects with `PredictionVersionChangedError`, requiring reread/review. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --occurrence <N> [--fields <ids>] [--model-version <version>] --output json` | Confirm one occurrence using its 0-based value from the **latest** predictions. Without fields confirm all predicted fields there; with fields only those; other occurrences untouched. Requires `--group` (Critical Rule 12), mutually exclusive with `--updates-file`. Writes renumber the group; use updates file for multiple rows. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --updates-file <path> [--model-version <version>] --output json` | Atomically confirm several occurrences. File `[ {"occurrence":<0-based-index>,"fields"?:["<field_id>",…]} ]`; omit `fields` for every predicted field, otherwise selected fields while unselected fields carry existing annotation. Superset: one `--occurrence` equals one entry. Mutually exclusive with `--fields`/`--occurrence`; use for several rows. |
| `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` | `--fields` alias `-f`; roll back an earlier `confirm` or `mark-missing` for listed fields to unannotated, carrying others forward. Confirm cannot unconfirm (Critical Rule 13). Without `--group`, shared IDs are removed from all repeatable occurrences; group-scoped forms are below. Return `Unmatched` for IDs not initially annotated. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> [--occurrence <N>] [--fields <ids>] --output json` | Scope rollback to group: group alone all occurrences; `--occurrence` one, using a fresh read and same 0-based index (partial confirmation can shift it). Without fields roll back all annotated fields in targets; with fields only those. Other occurrences untouched; mutually exclusive with `--updates-file`; mirrors confirm group/occurrence. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> --updates-file <path> --output json` | Atomically roll back several occurrences. File `[ {"occurrence":<0-based-index>,"fields"?:["<field_id>",…]} ]`; omit fields for every annotated field, otherwise selected IDs; unlisted occurrences remain. Mutually exclusive with `--fields`/`--occurrence`. |
| `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json` | `--fields` alias `-f`; mark listed fields absent with no value/location when IXP predicted no value. Unlike confirm, reaches fields absent from current predictions (for example stale annotations after model/taxonomy change). Do not use for wrong predicted values—leave them unannotated. Return `Unmatched` for IDs absent from both annotations and predictions. |

### Occurrence numbering and read order

`Occurrence` is read position, not stable row ID; repeatable rows have none (`field_group.id` is the same taxonomy group ID for every row). `get-predictions` lists annotated rows first, so confirming moves a row to `Occurrence` 0 and shifts others; values/page location do not change. Document order holds only when no rows, or all rows, are annotated.

Any write invalidates group indices: confirm/unconfirm all target rows in one `--updates-file` using one read; between sequential occurrence calls, rerun `get-predictions` and relocate by field values; never carry an index across a write.

## Deployments

`projects publish` makes a version usable inside the project; deployment to an Orchestrator folder makes it callable at runtime. Activity packs and Maestro Flow address `{FolderKey, DeploymentName}`.

| Command | Contract |
|---|---|
| `uip ixp deployments create <project-name> --version <N> --folder-key <guid> [--title <title>] --output json` | Add only; never repoint (see [create vs upgrade](#create-vs-upgrade)). Required `--version`/`--folder-key`; title defaults to project name minus `-ixp`. Return `ProjectName`, `ModelVersion`, `FolderKey`, `DeploymentTitle`, `DeploymentName` (Code: `IxpDeploymentsCreate`). |
| `uip ixp deployments upgrade <project-name> <deployment-name> --version <N> --folder-key <guid> --output json` | Move existing deployment to another trained version. Positional name must be `DeploymentName` from `deployments list`, not title (Code: `IxpDeploymentsUpgrade`). |
| `uip ixp deployments list <project-name> --output json` | Only reliable source of `DeploymentName`; list across versions/folders. `Data` is array, `[]` for never deployed, never `{Message: ...}`; iterate unconditionally. Entries have `DeploymentName`, `DeploymentTitle`, `ModelVersion`, `FolderKey`, `DeployedAt` (Code: `IxpDeploymentsList`). |
| `uip ixp deployments get-taxonomy <project-name> --version <N> --output json` | Required `--version` (non-negative integer, 0 valid, no short alias), from `projects list-models`. Return raw snake_case artifact under `Data.dataset` (`entity_defs[]`, `label_groups[]`) for that trained snapshot (Code: `IxpDeploymentsGetTaxonomy`). |

### create vs upgrade

| Existing deployment in folder | `create` | `upgrade` |
|---|---|---|
| none | Deploys | `404 [DeploymentNotFoundError]` |
| same model version | No-op, exit `0` | No-op, exit `0`; `DeployedAt` unchanged |
| different model version | `409 [DeploymentAlreadyExistsError]` | Repoints |

Both are safely repeatable at the same version. `create` has no `--force`; use `upgrade` to repoint. Upgrade changes the version all runtime callers of that folder/name receive; confirm intent for shared folders. Its response echoes requested version without rereading; run `list` to prove the move.

### DeploymentName vs DeploymentTitle

`--title` sets free-form `DeploymentTitle`, returned verbatim. Runtime resolves `DeploymentName`, a slugged title plus generated per-deployment suffix (for example `invoices` → `invoices-08963f00-ixp`). Never construct it: suffixes differ between deployments, match neither project suffix nor folder key, and no-title deployments still have one. Read it from create response or `list`; if create returns `DeploymentName: null`, run `list`. Upgrade requires `DeploymentName`; title yields `404 [DeploymentNotFoundError]`.

### --folder-key

`--folder-key` is required for create and upgrade; folder is part of identity and there is no tenant/default-folder deployment, `--folder-path` form, or CLI format validation, so a malformed key is only rejected by UiPath when the command runs. Get keys from `uip or folders list --output json`. When filtering, run:

```bash
uip or folders list --limit 1000 --output json --output-filter "[?Path=='Shared'].Key"
```

An `--output-filter` without explicit `--limit` is rejected on current CLIs (older builds silently filter one page). If `Pagination.HasMore` is true and `Data` empty, repeat with `--offset 1000`, `--offset 2000`, etc. before declaring the folder missing.

Omitting either required option fails locally with exit `3` / `Result: ValidationError`; no request is sent, so this is never an authentication or connectivity problem. `--version 0` is valid — versions are 0-based.

### Deployment errors

| Error | Meaning | Fix |
|---|---|---|
| `409 [DeploymentAlreadyExistsError]` on `create` | Same title already deployed in folder at another version | Run `upgrade` with `DeploymentName` from `list`, not title in error. |
| `404 [DeploymentNotFoundError]` on `upgrade` | Never deployed, another folder, or title supplied | Reread `DeploymentName`; verify `--folder-key`. |
| `404 [ModelVersionNotFoundError]` on `upgrade` | Version not deployable; says nothing about deployment existence | Choose from `projects list-models <project-name> --output json`. |
| `408 Timed out waiting for new model version` on `upgrade` | Upstream timeout; CLI does not retry and outcome is unknown | Run `list`, read served version, then decide; assume neither outcome. |
| `409 [AmbiguousDeploymentError]` | More than one deployment matches in the folder | Disambiguate from `list`; same create-conflict hint applies. |

All listed rejected `409`/`404` writes are no-ops: original version and `DeployedAt` remain. Do not branch on `ErrorCode`: these `409`s surface as `ErrorCode: invalid_argument` because 400/409/422 map alike; branch on `Context.HttpStatus` or bracketed error name.

`upgrade` is not rollback: retraining can remove versions from the deployable list, leaving a deployment on a version that cannot be moved back to. Verify the target with `projects list-models` first. After successful deployment, folder-scoped runtime resolution takes roughly 15 seconds; an immediate lookup may miss it.

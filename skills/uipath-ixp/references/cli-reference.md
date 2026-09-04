# CLI Commands Reference

All commands use `uip ixp`. Always append `--output json` when parsing output programmatically.

> **Destructive commands require `-y, --yes`.** Every irreversible `uip ixp` command (all `delete`s and `fields change-type`) gates on `-y/--yes`; the CLI never prompts. Always pass `-y/--yes`.

## Projects

| Command | Description |
|---|---|
| `uip ixp projects list [-l <limit>] [--offset <n>] --output json` | List projects. Returns paged `Data: { Projects: [{ Id, Name, Title, CreatedAt }], Total, Offset, Limit }`; rows are under `Projects`, not a bare array. `-l, --limit`: default 50, range 1-10000. `--offset`: default 0. |
| `uip ixp projects get <project-name> --output json` | Get a project. |
| `uip ixp projects create "<name>" <folder-path> [-d "<description>"] [--skip-taxonomy] --output json` | Create a project and upload supported documents from the top level of `<folder-path>`; do not scan sub-folders. By default suggest+import taxonomy. `-d` supplies taxonomy context; `--skip-taxonomy` creates a blank project. Use `ProjectName` from output. See [Supported document files](#supported-document-files). |
| `uip ixp projects import-taxonomy <project-name> <file> --output json` | Import local JSON in `{ field_types, label_group }` or `{ entity_defs, label_groups }` format. **Merges; never replaces**: omitted entries remain and posted `field_id` is ignored, so this cannot remove, move, or replace definitions. Re-imported edits can return `{"status":"ok"}` while leaving duplicates. Run it only to seed a project without taxonomy; modify existing taxonomy with targeted `groups`/`fields`/`data-types` commands. |
| `uip ixp projects update-title <project-name> "<new-title>" --output json` | Update display title. |
| `uip ixp projects update-prompt <project-name> --prompt "<text>" --output json` | Replace **Overall extraction instructions**, distinct from `groups update-prompts` and `fields update-prompts`. |
| `uip ixp projects get-taxonomy <project-name> --output json` | Export raw taxonomy. Read `Data.dataset.entity_defs` and `Data.dataset.label_groups`; use it for re-import, not human-readable viewing. `dataset` also contains `_model_config`, the only read path for configured extraction model and pre-processing; see [Reading the current model and pre-processing](#reading-the-current-model-and-pre-processing). |
| `uip ixp projects get-metrics <project-name> [--model-version <N>] --output json` | Get validation metrics. Validated: flat `Data` with `ProjectScore`, `ProjectScoreQuality`, `ValidatedDocuments`, `ModelVersion`, `FieldGroups[]` (`FieldGroup`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`) and `Fields[]` (`FieldGroup`, `FieldId`, `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`, `Annotations`, `Quality`). Trained but unvalidated: `Data: { Metrics: null }`. No trained model: failure envelope `Result: Failure`, `ErrorCode: not_found`, no `Data`; treat as no metrics. Default is latest trained, not necessarily published/live. Resolve the version with `list-models` and pass `--model-version <N>` whenever reporting a score so score and version match (SKILL.md Critical Rule 21). `ErrorRate` is `errors / Annotations`, not `1 - Precision`; `Quality` and `ProjectScoreQuality` use inconsistent scales—never gate on them. See [Improve Prompts Guide § What get-metrics returns](improve-prompts-guide.md#what-get-metrics-returns-and-which-values-decide). |
| `uip ixp projects configure-model <project-name> [options] --output json` | Configure model: `--model` (`gemini_2_5_flash/gemini_2_5_pro/gpt_4o_2024_05_13`) and `--preprocessing` (`none/table_mini/table`). Read settings below. |
| `uip ixp projects list-models <project-name> --output json` | List `Models[]` (`Version`, `ModelName`, `Pinned`, `TrainedTime`, `Description`), `Tags[]` (`Name`, `Version`, `UpdatedAt`), and `MaxPublished`. Read the live version only from `Tags[]` Name=`live`; otherwise use the highest `Models[]` with `Pinned: true`. Folder runtime version is separate; see [Deployments](#deployments). `ModelName` is the trained labeller family (for example, `gemini_ixp`, `gemini_pro_ixp`), never a `--model` value and not the configured extraction model. |
| `uip ixp projects publish <project-name> [--model-version <N>] [--tag <live\|staging>] --output json` | Publish a trained version; defaults latest. `-m, --model-version <N>` selects one. `-d, --description "<text>"` sets description; `--tag <live\|staging>` tags it. |
| `uip ixp projects unpublish <project-name> --model-version <N> --output json` | Remove published status while retaining the trained version. `--model-version` is required; errors if missing or not published. Publish another version to change live. |
| `uip ixp projects untag <project-name> --tag <live\|staging> --output json` | Remove a required tag. Tags are unique within a project; errors if no version has it. Only `untag` removes a tag; publish without `--tag` leaves tags unchanged. Publish with `--tag staging` to switch `live` to `staging`. |
| `uip ixp projects delete <project-name> -y --output json` | **Permanently and irreversibly** delete project documents, taxonomy, and trained models. `-y, --yes` is required. |

### Reading the current model and pre-processing

There is **no `get-model-config` command**. Run:

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

Read `Data.dataset._model_config.model_version` and report it verbatim as the configured `--model`; never report `list-models` `ModelName`. Invert `Data.dataset._model_config.input_config`:

| `input_config` | `--preprocessing` |
|---|---|
| `null` | never configured; report *not configured*, not `none` |
| `{"mode": "image_only"}` | `none` |
| `{"mode": "text_plus_image", "text_config": {"kind": "uipath_cv_table_only"}}` | `table_mini` |
| `{"mode": "text_plus_image", "text_config": {"kind": "gemini_table_only"}}` | `table` |

`kind`, `flags`, `attribution_method`, `temperature`, `top_p`, `seed`, `system_prompt_override`, and `iterative_config` have no `uip ixp` flag; mention them only if asked. `_model_config` is the project's current setting, not the setting used by a trained version; report it as project configuration.

## Documents

| Command | Description |
|---|---|
| `uip ixp documents list <project-name> [-l <limit>] [--offset <n>] --output json` | List documents. Returns `Data: { Documents: [{ DocumentId, AttachmentRef, Filename }], Total, Offset, Limit }`; rows are under `Documents`, not a bare array. `AttachmentRef`/`Filename` may be `null`; `Filename` is the original upload filename. `-l, --limit`: default 50, range 1-10000. `--offset`: default 0, range 0-1000000. |
| `uip ixp documents download <project-name> <document-id> -o <path> --output json` | Download the original file exactly to `-o`; the CLI does not append or correct extensions. Include the extension. `Data.ContentType` is commonly `application/octet-stream`; `Data.Path` echoes the supplied path. |
| `uip ixp documents upload <project-name> <file> --output json` | Upload one document; see [Uploading documents to an existing project](#uploading-documents-to-an-existing-project). |
| `uip ixp documents delete <project-name> <document-id> -y --output json` | Irreversibly delete a document and labellings; triggers retrain. `-y, --yes` is required. |

### Supported document files

`projects create` and `documents upload` accept, case-insensitively: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.tif`, `.tiff`, `.bmp`.

- `documents upload` rejects unsupported extensions before network access with `Unsupported file type "<ext>"`.
- `projects create` scans only the folder's top level, silently skips unsupported files, and fails only when none remain: `No supported documents found in <folder>`.

Each upload triggers retrain. Wait under the bounded wait in [Improve Prompts Guide § Waiting for retrain](improve-prompts-guide.md#waiting-for-retrain) before reading metrics or predictions for new documents.

### Uploading documents to an existing project

Run `uip ixp documents upload <project-name> <file> --output json` once per file. Supported files return `{ ProjectName, Filename, AttachmentRef, DocumentId }` (`Code: IxpDocumentsUpload`); capture `DocumentId` for download or `labellings confirm`.

For multiple files, run one call per file:

```bash
cd "<folder-with-docs>"
for f in *.pdf *.png *.jpg *.jpeg *.gif *.tif *.tiff *.bmp; do
    [ -e "$f" ] || continue
    uip ixp documents upload <project-name> "$f" --output json
done
```

For a new project, prefer `projects create <name> <folder-path>` to upload the folder and suggest taxonomy together.

## Data Types

Data types are reusable `entity_defs` referenced by fields through `field_type_id`; the UI calls them Data Types.

| Command | Description |
|---|---|
| `uip ixp data-types add <project-name> --name <name> --kind <text\|date\|money\|number\|boolean\|choice> --instructions <text> [--input-value <exact-match\|inferred>] [--choices <json>] --output json` | Add a type. `--input-value` is required for `text` and `choice`, forbidden for `date`, `money`, `number`, `boolean`; `exact-match` means verbatim and `inferred` means computed/not visibly located. `--choices` is required for `choice`, forbidden otherwise; JSON is `[ {"value":"<canonical>","alternates":["<alt1>",...]} ]`, with optional `alternates` defaulting to `[]`. |
| `uip ixp data-types update-instructions <project-name> --name <name> --instructions <text> --output json` | Replace instructions; name, kind, and input-value remain. |
| `uip ixp data-types rename <project-name> --name <name> --new-name <name> --output json` | Rename while preserving `field_type_id` references. |
| `uip ixp data-types delete <project-name> --name <name> -y --output json` | **Irreversibly** delete a type; referencing fields break. `-y, --yes` is required. |

### Default data types

Before `data-types add` or selecting `--type` in `fields add`/`groups add`, run `projects get-taxonomy`, inspect authoritative `entity_defs`, and reuse a matching default. Do not create redundant types: they split annotations and lose pretrained behavior.

| Default type | `--kind` | `--input-value` | Reuse for |
|---|---|---|---|
| `Exact Text` | `text` | `exact-match` | Verbatim names, IDs, addresses, codes |
| `Inferred Text` | `text` | `inferred` | Derived/computed text |
| `Number` | `number` | — | Counts, quantities, plain numbers |
| `Date` | `date` | — | Dates |
| `Monetary Quantity` | `money` | — | Currency amounts: total, subtotal, tax, unit price, freight |
| `Boolean` | `boolean` | — | True/false |

`Date`, `Number`, `Monetary Quantity`, and `Boolean` have pretrained fixed output formats; hand-rolled equivalents are worse. `Choice` has no default and is always project-specific.

### Normalized output formats

`get-predictions` and plain `confirm` use normalized values, not literal page text:

| Type | `FormattedValue` | Example |
|---|---|---|
| `Date` | `YYYY-MM-DDTHH:MM:SSZ`; date-only values use `T00:00:00Z` | `21-JUN-22` → `2022-06-21T00:00:00Z` |
| `Monetary Quantity` | `<amount> <ISO-4217 code>`; no thousands separator, decimals as written, currency appended if absent | `114.91` → `114.91 AUD`; `8.0700` → `8.0700 USD` |
| `Number` | Bare numeric string, without unit or separator | `29311577` → `29311577` |
| `Boolean` | `True` / `False` | — |

`--corrections` neither normalizes nor validates; it stores the supplied string verbatim, including `21-JUN-22` or `not-a-date`, and returns Success. Use it only for OCR-mangled values; never reformat page values with it (Critical Rule 8).

## Groups

Field groups (`label_defs`) contain fields.

| Command | Description |
|---|---|
| `uip ixp groups add <project-name> --name <group-name> --instructions <text> --fields <json> --output json` | Add a group and **all** its fields in one batch. `--instructions` describes the document/section. `--fields` is `[ {"name":"...","type":"<type-name>","instructions":"..."} ]`; every entry requires non-empty `name`, `type`, and `instructions`. Resolve `type` in `entity_defs` and reuse [default data types](#default-data-types). Use `fields add` for an existing group. |
| `uip ixp groups delete <project-name> --name <group-name> -y --output json` | Irreversibly delete the group and all field annotations. `-y, --yes` is required. |
| `uip ixp groups rename <project-name> --name <group-name> --new-name <name> --output json` | Rename while preserving fields and annotations. |
| `uip ixp groups update-prompts <project-name> --updates <json> --output json` | Bulk replace group instructions with `[ {"name":"<group>","instructions":"..."} ]`. Fields remain; unmatched names are reported without failing. |

## Fields

| Command | Description |
|---|---|
| `uip ixp fields add <project-name> --group <field-group-name> --field <name> --type <type-name> --instructions <text> --output json` | Add a field to an existing group. `--type` names an `entity_defs` entry; reuse [default data types](#default-data-types). `--instructions` is required and must say what to extract and where. |
| `uip ixp fields delete <project-name> --group <field-group-name> --field <name> -y --output json` | Remove a field; `-y, --yes` is required. |
| `uip ixp fields rename <project-name> --group <field-group-name> --field <name> --new-name <name> --output json` | Rename while preserving `field_id` and annotations. |
| `uip ixp fields change-type <project-name> --group <field-group-name> --field <name> --type <type-name> -y --output json` | **Irreversibly** change type; the server creates a new field and deletes annotations. `-y, --yes` is required. |
| `uip ixp fields update-prompts <project-name> --updates <json> --output json` | Bulk replace per-field instructions with `[ {"name":"<field>","instructions":"..."} ]`, matched by `moon_form` field name across groups. Definitions remain; unmatched names are reported without failing. |

### Moving a field to a different field group

There is no move/reparent command. Tell the user before starting, then:

1. Run `uip ixp projects get-taxonomy <project-name> --output json`; in `Data.dataset`, read the field's `moon_form` entry under its group's `label_def`. Resolve its type through the `entity_defs[]` entry whose `id` matches `field_type_id`, **not** `field_id`.
2. Run `uip ixp fields add <project-name> --group <target-group> --field <name> --type <type-name> --instructions <text> --output json`.
3. After the add succeeds, run `uip ixp fields delete <project-name> --group <source-group> --field <name> -y --output json`.

Both groups must already exist; creating a target group is a separate `groups add` step requiring confirmation. The add mints a new `field_id`, so labels do not follow and documents require re-review.

Do **not** edit and re-import taxonomy to move a field: `import-taxonomy` merges, retains omitted fields, ignores posted `field_id`, and can leave duplicate fields in both groups while returning `{"status":"ok"}`. Do not use `groups delete` + `groups add`; it destroys every other field and its annotations.

## Labellings

| Command | Description |
|---|---|
| `uip ixp labellings get-predictions <project-name> <document-id> --output json` | Return `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`. Each prediction document is `{ DocumentId, Labels[] }`; each label `{ Name, Occurrence, Fields[] }`; each field `{ FieldId, FieldName, FormattedValue }`. `Occurrence` is explicit, 0-based, may be non-contiguous or start at 1; use it, never a positional guess. Read order changes after writes; see [Occurrence numbering and read order](#occurrence-numbering-and-read-order). Capture each document's `ModelVersion` and pass it to `confirm -m/--model-version`. |
| `uip ixp labellings confirm <project-name> <document-id> [--fields <ids>] [--corrections <json>] [--model-version <version>] --output json` | Without `--fields`, confirm every predicted field with content. `--fields`/`-f` confirms listed fields with content and marks listed empty predictions missing; listing is intentional confirmation of empty state (Critical Rule 12). `--corrections`/`-c` is only for OCR-mangled values at the same location; do not use it for wrong booleans, inferred values, or other non-OCR errors—leave those unannotated (Critical Rule 8). Existing annotations carry forward. Pass reviewed `ModelVersion` with `-m, --model-version`; a newer retrain causes `PredictionVersionChangedError`; reread and review. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --occurrence <N> [--fields <ids>] [--corrections <json>] [--model-version <version>] --output json` | Confirm one occurrence. Use the 0-based value from the latest `get-predictions`; without `--fields`, confirm all predicted fields in that occurrence, otherwise only listed fields. Other occurrences remain untouched. Requires `--group` (Critical Rule 13). Mutually exclusive with `--updates`. A write renumbers subsequent reads; use `--updates` for several rows. |
| `uip ixp labellings confirm <project-name> <document-id> --group <name> --updates <json> [--model-version <version>] --output json` | Atomically confirm several occurrences. JSON: `[ {"occurrence":<0-based-index>,"fields"?:["<field_id>",…],"corrections"?:{"<field_id>":"<value>"}} ]`. Omit `fields` to confirm all predicted fields; selected occurrences' unselected fields retain annotations. `--updates` is equivalent to one-entry `--occurrence`; mutually exclusive with `--fields`/`--corrections`/`--occurrence`. |
| `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` | Roll back listed fields to unannotated while carrying other annotations. Without `--group`, a shared field ID is removed from all repeatable occurrences. Returns `Unmatched` for IDs not initially annotated. Use when confirm was mistaken; confirm cannot un-confirm (Critical Rule 14). |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> [--occurrence <N>] [--fields <ids>] --output json` | Scope rollback to a group or one occurrence. `--group` alone targets every occurrence; add `--occurrence <N>` from a fresh prediction read to target one. Without `--fields`, target all annotated fields; with it, only those IDs. Other occurrences remain. On partly confirmed groups, reread because indices shift. Mutually exclusive with `--updates`. |
| `uip ixp labellings unconfirm <project-name> <document-id> --group <name> --updates <json> --output json` | Atomically roll back several occurrences. JSON: `[ {"occurrence":<0-based-index>,"fields"?:["<field_id>",…]} ]`; omit `fields` for all annotated fields. Unlisted occurrences remain. Mutually exclusive with `--fields`/`--occurrence`. |
| `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json` | Mark listed fields missing with no value/location; use only when IXP predicted no value. Unlike `confirm --fields`, reaches fields absent from current predictions, including stale annotations after model/taxonomy changes. Do not use for wrong predictions; leave them unannotated. Returns `Unmatched` for IDs absent from both annotations and predictions. |

### Occurrence numbering and read order

`Occurrence` is a read position, not a stable row ID; repeatable groups have no per-row identifier (`field_group.id` is identical for every row). The server returns annotation↔prediction matched pairs first, then unmatched predictions. Confirming a row moves it to occurrence 0 and shifts others; values and page locations do not change. Document order is reliable only when no rows, or all rows, are annotated.

Any write to a group invalidates occurrence values:

- Confirm/unconfirm all target rows in one `--updates` call; indices in that call use one read.
- Between sequential per-occurrence calls, run `get-predictions` and relocate each row by field values.
- Never carry an index across a write.

## Deployments

`projects publish` makes a version usable inside the project. Deploying it to an Orchestrator folder makes it callable at runtime; callers address `{FolderKey, DeploymentName}`.

| Command | Description |
|---|---|
| `uip ixp deployments create <project-name> --version <N> --folder-key <guid> [--title <title>] --output json` | Add a deployment; never repoint an existing one. `--version` and `--folder-key` are required. `--title` defaults to project name minus `-ixp`. Returns `ProjectName`, `ModelVersion`, `FolderKey`, `DeploymentTitle`, `DeploymentName` (`Code: IxpDeploymentsCreate`). |
| `uip ixp deployments upgrade <project-name> <deployment-name> --version <N> --folder-key <guid> --output json` | Move an existing deployment to another trained version. Positional `<deployment-name>` must be `DeploymentName` from `deployments list`, not title (`Code: IxpDeploymentsUpgrade`). |
| `uip ixp deployments list <project-name> --output json` | List deployments across versions/folders. `Data` is an array, `[]` when never deployed, never `{Message: ...}`. Entries contain `DeploymentName`, `DeploymentTitle`, `ModelVersion`, `FolderKey`, `DeployedAt` (`Code: IxpDeploymentsList`). |
| `uip ixp deployments get-taxonomy <project-name> --version <N> --output json` | Get version-specific taxonomy. `--version` is required, a non-negative integer; 0 is valid; no short alias. Read version from `projects list-models`. Raw snake_case artifact is under `Data.dataset` with `entity_defs[]` and `label_groups[]` (`Code: IxpDeploymentsGetTaxonomy`). |

### create vs upgrade

| Existing deployment in folder | `create` | `upgrade` |
|---|---|---|
| none | deploys | `404 [DeploymentNotFoundError]` |
| same model version | no-op, exit `0` | no-op, exit `0`; `DeployedAt` does not move |
| different model version | `409 [DeploymentAlreadyExistsError]` | repoints |

Both are safe to rerun at the same version. `create` has no `--force`; use `upgrade` to repoint. Confirm before upgrading a shared folder. `upgrade` echoes the requested version without rereading; run `list` to prove the move landed.

### DeploymentName vs DeploymentTitle

`--title` sets free-form `DeploymentTitle`. `DeploymentName` is runtime-resolved: the backend slugs the title and appends a per-deployment suffix. The suffix is generated per deployment and cannot be predicted; never construct it. A deployment without `--title` still has a suffix, and `DeploymentName` is never just the project name. If create returns `DeploymentName: null`, run `list`. `upgrade` requires `DeploymentName`; passing a title returns `404 [DeploymentNotFoundError]`.

### --folder-key

`--folder-key` is required on both `create` and `upgrade`, passed in the body, never the path. The same name may exist in several folders; there is no tenant-level/default-folder deployment and no `--folder-path`. The key is not client-validated; malformed keys fail server-side. Get keys by running `uip or folders list --output json`.

When filtering folders, pass an explicit `--limit`; `--output-filter` without one is rejected on current CLIs (older builds silently filter one page):

```bash
uip or folders list --limit 500 --output json --output-filter "[?Path=='Shared'].Key"
```

Omitting either required option fails locally with exit `3` / `Result: ValidationError`, before auth or backend access. `--version 0` is valid; versions are 0-based.

### Deployment errors

| Surfaced error | Meaning | Fix |
|---|---|---|
| `409 [DeploymentAlreadyExistsError]` on `create` | Title already deployed in folder at a different version | Run `upgrade` with `DeploymentName` from `list`, not the quoted title |
| `404 [DeploymentNotFoundError]` on `upgrade` | Name absent, exists only in another folder, or title was supplied | Reread `DeploymentName`; verify `--folder-key` |
| `404 [ModelVersionNotFoundError]` on `upgrade` | Version is not deployable | Choose one from `projects list-models <project-name> --output json` |
| `408 Timed out waiting for new model version` on `upgrade` | Outcome unknown; write may have landed | Run `list`, inspect served version, then decide whether to retry |
| `409 [AmbiguousDeploymentError]` | Multiple deployments match in folder | Disambiguate from `list`; use the same `create` conflict guidance |

Rejected `409`/`404` writes leave the original version and `DeployedAt` unchanged. Do not branch on `ErrorCode`: these statuses map to `ErrorCode: invalid_argument`; branch on `Context.HttpStatus` or bracketed backend error name.

`upgrade` is not a rollback path: retraining can remove versions from the deployable list. Verify the target in `projects list-models` first. After successful deployment, folder-scoped runtime resolution takes roughly 15 seconds; an immediate lookup may miss it.
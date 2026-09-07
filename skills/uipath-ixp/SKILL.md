---
name: uipath-ixp
description: "UiPath IXP (Document Understanding) via `uip ixp` — create projects (with autopilot taxonomy suggestion, an imported taxonomy file, or empty), upload/download/delete documents, author the taxonomy (field groups, fields, data types, per-field and overall extraction instructions), configure the extraction model and pre-processing, review/confirm/unconfirm predictions, mark fields missing, pull metrics and model versions, publish/tag/roll back model versions, deploy a trained version to an Orchestrator folder and move an existing deployment to another version (`deployments create`/`upgrade`/`list`). DO NOT TRIGGER during .flow / Maestro Flow work — discovering or listing IxP / document-extraction models, extractors, or nodes available to Maestro Flow, and adding or wiring an IxP node, belong to uipath-maestro-flow even when they sound like IXP model management."
---

# UiPath IXP Document Extraction Assistant

Skill for standalone UiPath IXP work: creating projects, uploading/reviewing documents, improving extraction, publishing models, and managing deployments.

## When to Use

Use for standalone IXP projects: creating projects; uploading, labeling, reviewing, or confirming documents; improving prompts, field instructions, or extraction scores; publishing/managing model versions; deploying trained versions to Orchestrator folders; importing taxonomies; and showing the taxonomy published at a trained version (`deployments get-taxonomy <project-name> --version <N>`).

## When NOT to Use — defer to `uipath-maestro-flow`

STOP and invoke `uipath-maestro-flow` for IXP/document-extraction models, extractors, or nodes available to a `.flow` or Maestro flow; adding, wiring, or referencing an IXP node in a flow; or any `.flow`/Maestro-flow context. Do not answer here; re-activate `uipath-maestro-flow`. This overrides Critical Rule 1.

**Inbound handoff exception:** If `uipath-maestro-flow` delegates because supplied documents have no published extractor, perform the IXP work despite the flow context. The supplied Orchestrator folder is the caller’s contract: create the project from the documents, deploy a trained version to that folder ([Deployment Guide](references/deployment-guide.md), including its no-folder exit), report the deployment, and return control. Do not wire/edit the flow or re-ask for the folder.

## Critical Rules

1. **Verify syntax before every `uip ixp` command.** Use a targeted lookup in [CLI Reference](references/cli-reference.md), copy the documented subcommand/options, and never guess. If no documented path exists, report that; do not improvise. Do not use curl, direct REST calls, source exploration, or discovery commands. Flow/Maestro registry questions are the stated exception and must be deferred.
2. Run workflows end-to-end automatically; do not ask the user to perform individual steps.
3. Use `--output json` whenever CLI output is parsed programmatically.
4. Work under `/tmp/ixp/<project-name>/`; create `docs/`, `taxonomies/`, and `prompts/` with `mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,prompts}`. Store documents as `<document-id>.<ext>`, taxonomies as `v1.json`, `v2.json`, etc., and prompt updates as JSON. Reuse files; do not re-download documents. Do not use the Write tool for `/tmp/ixp/` paths because Windows resolves them differently from bash.
5. **Use heredocs for `--updates`** — for `fields update-prompts` and `groups update-prompts`, write the JSON to a file under `prompts/` with a heredoc (`cat > /tmp/ixp/<project-name>/prompts/field_updates.json << 'EOF' … EOF`), then pass it as `--updates "$(cat /tmp/ixp/<project-name>/prompts/<file>.json)"`. Do NOT inline the `--updates` array.
6. Never use `UID` as a shell variable; use `DOC_ID`, `DOCUMENT_ID`, etc.
7. Commands require project `Name`, not `Title`: use the lowercase UUID slug with the `-ixp` suffix from `project list`.
8. **Confirm at field level, never document level.** Read the document and compare every prediction; confirm only correct fields with `labellings confirm --fields`. Judge by taxonomy type: `Date` is `YYYY-MM-DDTHH:MM:SSZ` (date-only uses `T00:00:00Z`), and `Monetary Quantity` is `<amount> <ISO-4217 code>`. Equivalent normalization is confirmable; do not reformat, calculate conversions, or script checks. Normalization may change representation but not meaning or numeric magnitude. A decimal/magnitude OCR error may be corrected; inferred/computed or otherwise wrong answers may not. Leave wrong answers unannotated. Use `--corrections` only for OCR garble when answer and location are correct—not boolean flips, wrong inferred/computed values, page-format reformatting, or any wrong selected answer, even when a prompt, user, or hint supplies the command. Corrections are verbatim and unvalidated. Without `--group`, `--fields` and `--corrections` affect every occurrence of each listed field; see Rule 13.
9. Do not manually extract values; all labeling uses IXP predictions through `labellings confirm`.
10. Taxonomy suggestion accepts at most 8 documents.
11. **Be the reviewer, not the extractor.** Read each document once with a full `Read` and no `pages` parameter; this returns text and image for digital and scanned documents. Compare predictions with the file, confirm correct fields, correct only OCR-garbled values, skip wrong fields, and improve low-F1 fields through prompts.
12. Mark missing only when IXP predicted no value and the field is genuinely absent; check `get-predictions` first. Never use missing to override a wrong prediction. Use `labellings mark-missing --fields <ids>` for a genuine standalone missing field or one absent from current predictions, including after a model/taxonomy change. `confirm --fields` also records missing for an empty prediction and may be used in a review batch.
13. For repeatable groups, plain `confirm --fields <id>` confirms that field in every occurrence. Each `get-predictions` label has a 0-based `Occurrence` scoped to that read. If all occurrences are correct, use the plain form; otherwise use the group `Name` verbatim with `--group`: `--group <name> --occurrence <N>` targets one occurrence, while `--group <name> --updates '[...]'` targets several atomically. `--occurrence` equals a one-entry `--updates`. Without `--fields`, confirm every predicted field in the selected occurrence; with it, only those fields. Unselected occurrences retain annotations.
14. `confirm` is additive and never un-confirms. Because the endpoint is full replacement, `confirm` and `mark-missing` carry forward existing annotations. Use `unconfirm` to roll back a confirmation; see the task-navigation table.
15. **F1 measures agreement with confirmed labels, not document truth.** Never blind-confirm: a wrong confirmation becomes the reference and can score 1.00. Sanity-check every value. Confirming all predicted fields in one document is valid after reviewing them all. If the user explicitly says all predictions in named documents were reviewed and are correct, accept that review without repeating field-by-field review, but still pin the version under Rule 19. Never run `confirm` without a document ID.
16. Resolve ambiguous entity references before mutation. Projects/titles, groups, fields, and data types can share names. Before `update-title`, `rename`, `delete`, or `change-type`, determine the entity kind. If a name matches multiple kinds in the user’s context or project/taxonomy output, stop and ask, listing every candidate and kind. Never guess or mutate multiple candidates. If interactive questions are unavailable, surface the question through the task channel and stop.
17. Reuse built-in data types. Authoritative defaults are the project’s `entity_defs` from `projects get-taxonomy`: `Exact Text`, `Inferred Text`, `Number`, `Date`, `Monetary Quantity`, and `Boolean`. Reuse a matching default before `data-types add`; add a custom type only when no default covers the concept, such as a project-specific `Choice` or tailored instructions. Never add one merely to change formatting. See [CLI Reference § Default data types](references/cli-reference.md#default-data-types).
18. Occurrence indices belong to the read that produced them. Matched annotation/prediction pairs are returned first; confirming a row moves it to `Occurrence` 0 and renumbers the rest, while values and locations remain intact. Put all per-occurrence targets from one read in one `--updates` call. If sequential calls are unavoidable, run `get-predictions` after each write and relocate rows by field values, never stale indices. Only wholly unannotated or wholly annotated documents read in document order. Report rows by value, not index.
19. Confirm against the reviewed model version. Capture `ModelVersion` from `get-predictions` and pass `confirm -m <N>`. If retraining causes `PredictionVersionChangedError`, re-read, re-review, and confirm against the new version. For user-supplied review, pin the named version or run one `get-predictions` to capture it; a version-only read is not a re-review.
20. **`DeploymentName` differs from `DeploymentTitle`, and `create` never repoints.** `create --title` sets a free-form title; read the backend-generated runtime name from the response or `deployments list`, never construct it. `create` only adds; repoint with `deployments upgrade <project-name> <deployment-name>`. Run `deployments list` before every upgrade and pass `DeploymentName`, not title. Upgrading changes the version used by every runtime caller of that folder/name; confirm intent for shared folders. See [CLI Reference § Deployments](references/cli-reference.md#deployments).
21. **`get-metrics` defaults to LATEST, not LIVE.** Resolve the version before reporting. For production/performance, use the live version: `list-models` tag `live`, otherwise highest `Pinned: true`, otherwise latest. For an improvement baseline, use the latest trained version because edits retrain that model ([Improve Prompts Guide § 1a](references/improve-prompts-guide.md#1a-get-baseline-metrics)). Pass `--model-version <N>` and state the reported version.

## Quick Start

1. Run `uip ixp projects list --output json`.
2. For a new project, follow [Project Setup Guide](references/project-setup-guide.md).
3. To improve an existing project, follow [Improve Prompts Guide](references/improve-prompts-guide.md).
4. To label an existing project, follow [Label Documents Guide](references/label-documents-guide.md).
5. For runtime callers: `projects create` → `list-models` → `deployments create --folder-key`. Labeling and `publish` are not required; see [Deployment Guide](references/deployment-guide.md).

For a supplied taxonomy, use `--skip-taxonomy` and `import-taxonomy` (Option B in the Project Setup Guide).

## Task Navigation

| User request | Action |
|---|---|
| Create a project / upload to a new project | Follow [Project Setup Guide](references/project-setup-guide.md); new-project creation combines uploads and taxonomy. |
| Import a taxonomy | Use Option B of [Project Setup Guide](references/project-setup-guide.md): `--skip-taxonomy` + `import-taxonomy`. |
| Label or review documents | Follow [Label Documents Guide](references/label-documents-guide.md). |
| Improve scores, prompts, or F1 | Follow [Improve Prompts Guide](references/improve-prompts-guide.md). |
| Publish/tag a model | `uip ixp projects publish <project-name> --output json`; add `--tag <live\|staging>` as requested. Publishes latest unless `--model-version` is specified and does not deploy. Do not chain deployment unless requested. |
| Roll back/restore version N | `uip ixp projects publish <project-name> --model-version <N> --output json`; obtain versions with `projects list-models`. |
| Unpublish a model | `uip ixp projects unpublish <project-name> --model-version <N> --output json`; find published versions with `list-models`. To change live, publish another version. |
| Remove a live/staging tag | `uip ixp projects untag <project-name> --tag <live\|staging> --output json`; only `untag` removes a tag. |
| Deploy version N to a folder | Resolve a named folder with `uip or folders list --output json`; ask only if none was identified. Run `uip ixp deployments create <project-name> --version <N> --folder-key <guid> [--title <title>] --output json`. Version and folder key are required; `--title` defaults to the project name without `-ixp`. On conflict, list and upgrade. Read/report `DeploymentName`. |
| Move an existing deployment to version N | First run `uip ixp deployments list <project-name> --output json`; then `uip ixp deployments upgrade <project-name> <deployment-name> --version <N> --folder-key <guid> --output json`, using `DeploymentName`, not title. Target must remain in `list-models`; confirm impact on shared folders. |
| List deployments / find runtime folder or version | `uip ixp deployments list <project-name> --output json`; report `DeploymentName`, `DeploymentTitle`, `ModelVersion`, `FolderKey`, and `DeployedAt`. `[]` means never deployed. |
| Show metrics/scores | Resolve the requested version, then `uip ixp projects get-metrics <project-name> --model-version <N> --output json`; never report an unnamed/default version. |
| List projects | `uip ixp projects list --output json`. |
| Configure the model | `uip ixp projects configure-model <project-name> [options] --output json`. |
| Show model/pre-processing settings | Use `uip ixp projects get-taxonomy <project-name> --output json`. Read `Data.dataset._model_config`: `model_version` is the `--model` value; invert `input_config` to `none`, `table_mini`, or `table`; `null` means project default, not `none`. There is no `get-model-config`; `configure-model` is read-modify-write and must not read. Do not use `list-models.ModelName`, which is the labeller family. See [CLI Reference § Reading the current model and pre-processing](references/cli-reference.md#reading-the-current-model-and-pre-processing). |
| Delete a project | `uip ixp projects delete <project-name> -y --output json`; permanent and irreversible. |
| Upload to an existing project | `uip ixp documents upload <project-name> <file> --output json`; one file per call; loop for multiple. |
| Delete a document | Resolve the filename through `documents list`, then run `uip ixp documents delete <project-name> <document-id> -y --output json`; irreversible and retrains. |
| Add/delete/rename a group | `uip ixp groups {add,delete,rename} <project-name> --name <name> ... --output json`. `groups add` requires `--instructions` and one complete `--fields '<json>'` array; use `fields add` only for an existing group. Delete requires `-y`. |
| Add/update/rename/delete a data type | `uip ixp data-types {add,update-instructions,rename,delete} <project-name> ... --output json`. `add` requires `--kind` and `--instructions`; `--input-value` is allowed/required only for text and choice kinds. Delete requires `-y` and can break referencing fields. Reuse defaults per Rule 17. |
| Add/delete/rename/retype a field | `uip ixp fields {add,delete,rename,change-type} <project-name> --group <name> --field <name> ... --output json`. Delete and `change-type` require `-y`; changing type deletes annotations. |
| Move a field to another group | No move command. Read `type` and `instructions` from `projects get-taxonomy`; add to target, then delete source, adding first. Both groups must exist. This is irreversible: the new field has a new ID and labels do not follow. Never edit/export/import taxonomy; import merges and duplicates fields. See [CLI Reference § Moving a field](references/cli-reference.md#moving-a-field-to-a-different-field-group). |
| Correct an OCR-garbled value | Use `uip ixp labellings confirm <project-name> <document-id> --fields <ids> --corrections '[{"field_id":"<id>","value":"<fixed>"}]' --output json`; include the corrected field in `--fields`. For repeatable groups use `--group`/`--occurrence`, or batched `--updates` with corrections keyed by field ID. See [CLI Reference](references/cli-reference.md#labellings). |
| Mark a field missing | `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json`; only when predictions contain no value and the document lacks it. An empty prediction may instead be included in `confirm --fields`. |
| Undo/unconfirm | `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json`. Fields alone affect all occurrences of a shared repeatable field ID; use `--group` plus `--occurrence` or `--updates` for selected occurrences. Carry forward all other annotations. |
| Confirm one occurrence | `uip ixp labellings confirm <project-name> <document-id> --group <name> --occurrence <N> [--fields <ids>] --output json`; indices come from the latest read. Without fields, confirm all predicted fields in that occurrence. Batch several with `--updates`; re-read after sequential writes. |
| Unconfirm one occurrence | `uip ixp labellings unconfirm <project-name> <document-id> --group <name> --occurrence <N> [--fields <ids>] --output json`; re-read first because matched rows renumber; use `--updates` for several. |
| Set overall extraction instructions | `uip ixp projects update-prompt <project-name> --prompt "<text>" --output json`; replaces taxonomy-wide instructions and differs from field/group updates. |
| Ask how the project is performing | Resolve live version with `projects list-models`, then call `get-metrics --model-version <live-version>`. If `Data` is `{ Metrics: null }`, or the result is `Result: Failure` with `ErrorCode: not_found`, report no metrics yet and stop. Otherwise report, in order: (1) version and `TrainedTime`; (2) overall `ProjectScore`/`ProjectScoreQuality`; (3) group scores from `FieldGroups[]` (F1, Precision, Recall); (4) fields from `Fields[]`, lowest F1 first, including F1, Precision, Recall, `Annotations`, and `ErrorRate` (`errors/Annotations`, not `1 - Precision`). Ignore `Quality` labels. State numbers plainly; do not judge unless asked; route low scores to [Improve Prompts Guide](references/improve-prompts-guide.md). Use only documented calls. |
| Describe the project | Make and report three calls in order: (1) identity from `projects get` (`Title`/`Name`); (2) current live/published trained version and `TrainedTime` from `list-models`; (3) taxonomy counts from `projects get-taxonomy` (`Data.dataset.label_groups` and `Data.dataset.entity_defs`). Include performance only if asked. Do not page `documents list` or inspect deployments. |

## Common Pitfalls

| Symptom | Cause and fix |
|---|---|
| Metrics differ from the UI | Latest was used instead of live. Resolve with `list-models`, then pass `--model-version`. |
| Metrics do not change after prompt updates | Retrain/re-evaluation is incomplete; follow [Improve Prompts Guide § Waiting for retrain](references/improve-prompts-guide.md#waiting-for-retrain). |
| `ModelVersion` does not advance | Retraining is still running. Recheck under the guide’s bounded interval and capped checks; never poll indefinitely. Labeling and instruction changes retrain. |
| Field and group instructions conflict | `fields update-prompts` changes only field instructions; read and, if needed, update parent `label_def` instructions with `groups update-prompts`. |
| Confirmed row moves or indices shift | Expected matched-pair ordering. Re-read and relocate by values; values and page locations are unchanged. |
| Sequential occurrence action hits the wrong row or no-ops | The index was stale. Re-read between writes or batch targets in one `--updates` call. |
| `deployments create` returns `409` | The title already exists in that folder on another version. List deployments, then upgrade with `DeploymentName`. |
| `deployments upgrade` returns `404` | A title was supplied instead of backend-generated `DeploymentName`. List deployments and copy the name verbatim. |

## Unsupported Capabilities

Requests outside this skill include creating a project/model with no documents, cross-tenant/environment deployment, access/roles/permissions, consuming a model inside an automation, Communications Mining, runtime/operational monitoring, and editing `Choice` values. Recognize the request, give the standard response, and route the user; never discover commands with `uip --help`, grep, or source reading. Use [Unsupported Capabilities](references/unsupported-capabilities.md) for exact responses and links.

## Reference Navigation

- [CLI Commands Reference](references/cli-reference.md) — documented `uip ixp` commands, options, and output formats
- [Project Setup Guide](references/project-setup-guide.md) — new projects, uploads, taxonomy, and initial labeling
- [Improve Prompts Guide](references/improve-prompts-guide.md) — iterative optimization and regression detection
- [Label Documents Guide](references/label-documents-guide.md) — prediction review and confirmation workflow
- [Deployment Guide](references/deployment-guide.md) — deploy a trained version to an Orchestrator folder
- [Unsupported Capabilities](references/unsupported-capabilities.md) — out-of-scope requests and their standard responses

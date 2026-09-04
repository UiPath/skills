# Project Setup Guide

Create a **new** IXP project, label its documents, and obtain initial metrics end-to-end automatically. Deployment is optional and separate: [Deployment Guide](deployment-guide.md).

> **Wrong page if the project already exists.** Use `uip ixp documents upload <project-name> <file>` — see [CLI Reference § Uploading documents](cli-reference.md#uploading-documents-to-an-existing-project).

## Step 1 — Create the Project

Use the user-provided name. If none is provided, generate a temporary name such as `ixp_project_NNNN` with a random number; rename it in Step 3 after the taxonomy reveals the document type. `<folder-path>` is filtered to supported document files — see [CLI Reference § Supported document files](cli-reference.md#supported-document-files).

For auto-suggested taxonomy, run:

```bash
uip ixp projects create "<name>" <folder-path> --output json
```

If the user specified what to extract, run:

```bash
uip ixp projects create "<name>" <folder-path> -d "<what to extract>" --output json
```

These commands upload documents and auto-suggest a taxonomy from their content and, when provided, the description.

If the user provides a taxonomy file, run:

```bash
uip ixp projects create "<name>" <folder-path> --skip-taxonomy --output json
uip ixp projects import-taxonomy <project-name> <taxonomy-file> --output json
```

The CLI detects either format from its keys:

- `{ "field_types": [...], "label_group": {...} }` — taxonomy suggested by a previous `project create` run.
- `{ "entity_defs": [...], "label_groups": [...] }` — user-provided taxonomy or one cloned from an existing project. `projects get-taxonomy` returns these under a `dataset` wrapper (`{ status, dataset: { entity_defs, label_groups } }`); `import-taxonomy` requires `entity_defs`/`label_groups` at the **top level**, so pass the inner `dataset` object (for example, `jq .Data.dataset`), not the whole response.

Use `ProjectName` from the create output for all subsequent commands. It is the lowercase slug with UUID and `-ixp` suffix, not the Title. Run:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
```

## Step 2 — Configure the Model

Before labelling, inspect 2–3 sample document images. Run:

```bash
uip ixp documents list <project-name> --output json
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/sample --output json
```

View each sample with the **Read tool**, using one full Read per document and **no `pages` parameter**; it returns text and image natively. Select configuration as follows:

| Document characteristics | Pre-processing | Model |
|---|---|---|
| Simple documents, no tables | `none` | `gemini_2_5_flash` |
| Simple tables or multiple tables | `table_mini` | `gemini_2_5_flash` |
| Complex nested tables, merged cells, or multi-page tables | `table` | `gemini_2_5_flash` |
| Very long documents (100+ pages) | `none` or `table_mini` | `gemini_2_5_pro` |

The default is `--model gemini_2_5_flash --preprocessing table_mini`. Apply the configuration by running:

```bash
uip ixp projects configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --output json
```

## Step 3 — Name the Project

Use the Step 1 taxonomy to choose a descriptive title. For example, "Invoice Details", "Line Items", and "Bill-To" indicate an invoices project. Run:

```bash
uip ixp projects update-title <project-name> "Vendor Invoices" --output json
```

Skip this step when the user provided a meaningful name in Step 1.

## Step 4 — Label All Documents

**Default:** follow the [Label Documents Guide](label-documents-guide.md) and label every document.

Labelling is optional. It produces the **project score** (`get-metrics` reports nothing until documents are confirmed) but is not required for a callable model; a trained version appears on its own within seconds of `projects create`.

Skip labelling only when:

- **The model unblocks a larger build in this session:** the deliverable is something else, such as a flow or automation, waiting on a callable model; no score, metrics, or accuracy target was named. Deploy per the [Deployment Guide](deployment-guide.md) and resume the build. The canonical case is the inbound `uipath-maestro-flow` handoff (see *When NOT to Use This Skill* in [SKILL.md](../SKILL.md)).
- **The user opts out:** the user says to skip labelling or that somebody else will handle it. Stop after Step 3 and hand over the project name; labelling can occur later in-product or via the [Label Documents Guide](label-documents-guide.md).

Never skip silently: state that the model is unscored and that labelling is the fix if fields come back wrong.
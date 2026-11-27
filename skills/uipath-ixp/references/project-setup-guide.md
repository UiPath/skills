# Project Setup Guide

Run this workflow automatically for a **new** IXP project, including document labelling and initial metrics. Deployment is optional and separate: [Deployment Guide](deployment-guide.md).

> **Wrong page if the project already exists.** Run `uip ixp documents upload <project-name> <file>` — see [CLI Reference § Uploading documents](cli-reference.md#uploading-documents-to-an-existing-project).

## Step 1 — Create the Project

Use the user-provided name; otherwise generate a temporary name (for example, `ixp_project_NNNN`) and rename it in Step 3 after determining the document type. `<folder-path>` is filtered to supported document files — see [CLI Reference § Supported document files](cli-reference.md#supported-document-files).

**Option A — Auto-suggest taxonomy (default):**

```bash
uip ixp projects create "<name>" <folder-path> --output json
```

When the user specifies what to extract, add `-d`:

```bash
uip ixp projects create "<name>" <folder-path> -d "<what to extract>" --output json
```

This uploads documents and suggests taxonomy from their content and, when provided, the description.

**Option B — Blank project + import taxonomy from file:**

When taxonomy comes from a user file or another project, run:

```bash
uip ixp projects create "<name>" <folder-path> --skip-taxonomy --output json
uip ixp projects import-taxonomy <project-name> <taxonomy-file> --output json
```

The CLI accepts:

- `{ "field_types": [...], "label_group": {...} }`: suggestion format, expected only from the user because no CLI command writes it to disk.
- `{ "entity_defs": [...], "label_groups": [...] }`: import format from a user file or copied taxonomy. `projects get-taxonomy` returns these under `dataset` (`{ status, dataset: { entity_defs, label_groups } }`); `import-taxonomy` requires the inner `dataset` object at the **top level** (for example, `jq .Data.dataset`), not the whole response.

**Option C — Empty project (no documents, no taxonomy):**

When the user requests a blank or empty project without documents, omit `<folder-path>` and run:

```bash
uip ixp projects create "<name>" --output json
```

Stop after Step 1; there are no documents to label.

Use `ProjectName` from the create output for all later commands. It is the lowercase slug with UUID and `-ixp` suffix, not the Title. Create the working directory:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,payloads}
```

## Step 2 — Configure the Model

Before labelling, inspect 2–3 sample document images. Run:

```bash
uip ixp documents list <project-name> --output json
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

View each with the **Read tool**, using one full Read per document and **no `pages` parameter**; it returns text and image natively. Choose:

| Document characteristics | Pre-processing | Model |
|---|---|---|
| Simple documents, no tables | `none` | `gemini_2_5_flash` |
| Simple or multiple tables | `table_mini` | `gemini_2_5_flash` |
| Complex nested tables, merged cells, or multi-page tables | `table` | `gemini_2_5_flash` |
| Very long documents (100+ pages) | `none` or `table_mini` | `gemini_2_5_pro` |

Apply the selected configuration:

```bash
uip ixp projects configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --output json
```

**Default recommendation:** `--model gemini_2_5_flash --preprocessing table_mini` for most invoice/document types.

## Step 3 — Name the Project

Use the Step 1 taxonomy to assign a descriptive title:

```bash
uip ixp projects update-title <project-name> "Vendor Invoices" --output json
```

Skip this step when the user supplied a meaningful name in Step 1.

## Step 4 — Label All Documents

**Default:** follow the [Label Documents Guide](label-documents-guide.md) and label every document.

Labelling is optional: it produces the **project score** (`get-metrics` reports nothing until documents are confirmed), but is not required for a callable model, whose trained version appears on its own within seconds of `projects create`. Skip labelling only when:

- **The model unblocks a larger build in this session:** another deliverable (such as a flow or automation) is waiting on a callable model, and no score, metrics, or accuracy target was named. Deploy per the [Deployment Guide](deployment-guide.md) and resume the build. The canonical case is the inbound `uipath-maestro-flow` handoff (see *When NOT to Use This Skill* in [SKILL.md](../SKILL.md)).
- **The user opts out:** the user says to skip labelling or that somebody else will handle it. Stop after Step 3 and hand over the project name; labelling can occur later in-product or via the [Label Documents Guide](label-documents-guide.md).

Never skip silently: state that the model is unscored and that labelling fixes incorrect fields.

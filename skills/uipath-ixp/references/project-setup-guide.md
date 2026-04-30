# Project Setup Guide

Complete workflow for creating a new IXP project, labelling all documents, and getting initial metrics. Run all steps end-to-end automatically.

## Step 1 — Create the Project

If the user provides a name, use it. If not, generate a temporary name (e.g., `ixp_project_NNNN` with a random number) — the project will be renamed in Step 3 after the taxonomy reveals the document type.

**Option A — Auto-suggest taxonomy (default):**

```bash
uip ixp projects create "<name>" <folder-path> --output json
```

If the user specified what to extract, add `-d` for a better taxonomy suggestion:

```bash
uip ixp projects create "<name>" <folder-path> -d "<what to extract>" --output json
```

This uploads documents and auto-suggests a taxonomy based on the document content (and the description if provided).

**Option B — Blank project + import taxonomy from file:**

If the user provides a taxonomy file, create a blank project and import separately:

```bash
uip ixp projects create "<name>" <folder-path> --skip-taxonomy --output json
uip ixp projects import-taxonomy <project-name> <taxonomy-file> --output json
```

The taxonomy file can be in either format — the CLI auto-detects based on which keys are present:

- `{ "field_types": [...], "label_group": {...} }` — use when importing a taxonomy suggested by a previous `project create` run
- `{ "entity_defs": [...], "label_groups": [...] }` — use when importing a taxonomy file provided by the user, or cloning from an existing project (exported via `uip ixp projects get-taxonomy`)

Use the `ProjectName` from the create output for all subsequent commands. This is the lowercase slug with UUID and `-ixp` suffix (e.g., `my_invoices-f1afa9ef-ixp`), NOT the Title.

Create the working directory using the returned `ProjectName`:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
```

## Step 2 — Configure the Model

Before labelling, configure the extraction model based on what the documents look like. Download 2-3 sample document images and view them:

```bash
uip ixp documents list <project-name> --output json
uip ixp documents get-image <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/sample.png --output json
```

View with the **Read tool**, then decide:

| Document characteristics | Pre-processing | Model |
|--------------------------|---------------|-------|
| Simple documents, no tables | `none` | `gemini_2_5_flash` |
| Documents with simple tables or multiple tables | `table_mini` | `gemini_2_5_flash` |
| Complex nested tables, merged cells, multi-page tables | `table` | `gemini_2_5_flash` |
| Very long documents (100+ pages) | `none` or `table_mini` | `gemini_2_5_pro` |

Apply the configuration:

```bash
uip ixp projects configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --attribution model \
  --output json
```

**Default recommendation:** `--model gemini_2_5_flash --preprocessing table_mini --attribution model` — works well for most invoice/document types.

## Step 3 — Name the Project

Based on the taxonomy from Step 1 (e.g., if it has "Invoice Details", "Line Items", "Bill-To" → it's an invoices project), give the project a descriptive title:

```bash
uip ixp projects update-title <project-name> "Vendor Invoices" --output json
```

Skip this step if the user already provided a meaningful name in Step 1.

## Step 4 — Label All Documents

Follow the [Label Documents Guide](label-documents-guide.md) to label every document in the project.

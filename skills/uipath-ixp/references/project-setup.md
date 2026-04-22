# Project Setup Guide

Complete workflow for creating a new IXP project, labelling all documents, and getting initial metrics. Run all steps end-to-end automatically.

## Step 1 — Create the Project

If the user provides a name, use it. If not, generate a temporary name (e.g., `ixp_project_NNNN` with a random number) — the project will be renamed in Step 3 after the taxonomy reveals the document type.

```bash
mkdir -p /tmp/ixp
uip ixp project create "<name>" <folder-path> --description "<what to extract>" --output json
```

Use the `ProjectName` from the output for all subsequent commands. This is the lowercase slug with UUID and `-ixp` suffix (e.g., `my_invoices-f1afa9ef-ixp`), NOT the Title.

## Step 2 — Configure the Model

Before labelling, configure the extraction model based on what the documents look like. Download 2-3 sample document images and view them:

```bash
uip ixp document list <project-name> --output json
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp/sample.png --output json
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
uip ixp project configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --attribution model \
  --output json
```

**Default recommendation:** `--model gemini_2_5_flash --preprocessing table_mini --attribution model` — works well for most invoice/document types.

## Step 3 — Name the Project

After the taxonomy has been imported, look at the suggested label groups and field names to understand what type of documents these are. Then give the project a descriptive title:

```bash
uip ixp project taxonomy <project-name> --output json
```

Based on the taxonomy (e.g., if it has "Invoice Details", "Line Items", "Bill-To" → it's an invoices project), rename:

```bash
uip ixp project rename <project-name> "Vendor Invoices" --output json
```

Skip this step if the user already provided a meaningful name in Step 1.

## Step 4 — Label All Documents

Follow the [Label Documents Guide](label-documents.md) to label every document in the project.

## Step 5 — Show Metrics

After all documents are labelled, wait ~2 minutes for re-evaluation, then:

```bash
uip ixp project metrics <project-name> --output json
```

Check that `ModelVersion` has advanced. If not, wait another 60 seconds and retry.

Report project score, quality rating, and per-field F1/precision/recall. Highlight:

- Fields with F1 < 0.5 that need prompt improvement
- Typed fields (Date, Monetary Quantity) at F1 = 0 — likely a format mismatch. Re-label using the value as-written in the document.

If the user wants to improve scores, follow the [Improve Prompts Guide](improve-prompts.md).

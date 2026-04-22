# Project Setup Guide

Complete workflow for creating a new IXP project, labelling all documents, and getting initial metrics. Run all steps end-to-end automatically.

## Step 1 — Create the Project

```bash
mkdir -p /tmp/ixp
uip ixp project create "<name>" <folder-path> --description "<what to extract>" --output json
```

Use the `ProjectName` from the output for all subsequent commands. This is the lowercase slug with UUID and `-ixp` suffix (e.g., `my_invoices-f1afa9ef-ixp`), NOT the Title.

## Step 2 — Label All Documents

Follow the [Label Documents Guide](label-documents.md) to label every document in the project.

## Step 3 — Show Metrics

After all documents are labelled, wait ~2 minutes for server-side retraining, then:

```bash
uip ixp project metrics <project-name> --output json
```

Check that `ModelVersion` has advanced. If not, wait another 60 seconds and retry.

Report project score, quality rating, and per-field F1/precision/recall. Highlight:

- Fields with F1 < 0.5 that need prompt improvement
- Typed fields (Date, Monetary Quantity) at F1 = 0 — likely a format mismatch. Re-label using the value as-written in the document.

If the user wants to improve scores, follow the [Improve Prompts Guide](improve-prompts.md).

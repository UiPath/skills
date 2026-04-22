---
name: uipath-ixp
description: "UiPath IXP (Document Understanding) — extract fields from documents using uip ixp CLI, review/correct extractions with Claude, confirm labellings. For Orchestrator/deploy→uipath-platform."
---

# UiPath IXP Document Extraction Assistant

Skill for working with UiPath IXP (Intelligent eXtraction Platform) projects — creating projects, uploading documents, extracting fields, and improving extraction quality.

## What This Skill Can Do

- **Create a new IXP project** — upload documents, generate taxonomy, label all documents, get metrics → [Project Setup Guide](references/project-setup.md)
- **Improve an existing project** — diagnose weak fields, rewrite instructions, re-label, verify improvement → [Improve Prompts Guide](references/improve-prompts.md)
- **List or inspect IXP projects** — use the CLI commands below

When the user asks to create a project or label documents, follow the [Project Setup Guide](references/project-setup.md).
When the user asks to improve scores/prompts for an existing project, follow the [Improve Prompts Guide](references/improve-prompts.md).

## Critical Rules

1. **ONLY use `uip ixp` CLI commands as documented in this skill** — do NOT use curl, do NOT source `~/.uipath/.auth`, do NOT load auth tokens, do NOT call REST APIs directly, do NOT grep/read source code, do NOT explore the codebase, do NOT run `--help` to discover options.
2. **Run workflows end-to-end automatically** — do NOT ask the user to do individual steps.
3. **Always use `--output json`** when parsing CLI output programmatically.
4. **Use `/tmp/ixp/` as the working directory** — at the start of any workflow, create it: `mkdir -p /tmp/ixp`. Store ALL downloaded images (`/tmp/ixp/doc_1.png`, `/tmp/ixp/doc_2.png`), JSON payloads (`/tmp/ixp/extractions.json`, `/tmp/ixp/updates.json`), and taxonomy snapshots (`/tmp/ixp/taxonomy.json`) in this directory. This keeps everything in one predictable location.
5. **Always use bash heredocs for JSON payloads** — when passing JSON to `--extractions` or `--fields`, write via heredoc (`cat > /tmp/ixp/extractions.json << 'EOF' ... EOF`) then use `"$(cat /tmp/ixp/extractions.json)"`. Do NOT use the Write tool for `/tmp/ixp/` paths — on Windows, the Write tool resolves `/tmp/` to a different location than bash, causing "file not found" errors.
6. **Never use `UID` as a variable name** — it is a readonly shell variable. Use `DOC_UID`, `COMMENT_UID`, etc.
7. **Always use the project `Name`, never the `Title`** — the `project list` output has both `Name` (e.g., `my_invoices-f1afa9ef-ixp`) and `Title` (e.g., `My_Invoices`). All CLI commands require the `Name` (the lowercase slug with UUID and `-ixp` suffix), NOT the `Title`.
8. **Use the flat `label_def.name` from taxonomy as the label** — NEVER prefix with parent names. If the taxonomy has a label_def named `"Line Items"`, use `"Line Items"` — NOT `"Invoice > Line Items"`. Using a prefixed name causes `400 No moon fields defined for label`.
9. **Repeating table labels get one entry per row** — for non-repeating labels (e.g., "Invoice Details"), group all fields into a single entry. For repeating/table labels (e.g., "Line Items"), emit **one entry per row**, each with the same label name and the same field_ids but different values.
10. **Max 8 documents for taxonomy suggestion** — the suggest-taxonomy endpoint accepts at most 8 attachment references.
11. **Keep field instructions short and pattern-focused** — 2-4 sentences max, 120-250 characters. Long instructions with many examples or detailed exclusion lists cause the model to memorize the list instead of learning the pattern, resulting in F1=0. Prefer: "Extract [what] from [where]. Format: [pattern]. Example: '[one value]'." over a paragraph with 10 examples.
12. **Claude is the source of truth for labellings** — extract what you see in the document. NEVER change labelling values to match IXP's predictions or to game the F1 score. If a field's F1 is low, improve the **prompt** so IXP learns to predict what you labelled — do NOT change your labelling to match what IXP predicted. Only modify labellings if you genuinely made an extraction error (missed a field, wrong value, wrong format).

## CLI Commands Reference

### Projects

| Command | Description |
|---------|-------------|
| `uip ixp project list --output json` | List all IXP projects |
| `uip ixp project get <project-name> --output json` | Get a project |
| `uip ixp project create "<name>" <folder-path> -d "<description>" --output json` | Create project, upload docs, suggest+import taxonomy. Use `ProjectName` from output for all subsequent commands. |
| `uip ixp project taxonomy <project-name> --output json` | Get taxonomy (entity_defs + label_groups with field definitions) |
| `uip ixp project metrics <project-name> --output json` | Get validation metrics — `FieldGroups[]` (per-group) and `Fields[]` (per-field F1/Precision/Recall) |
| `uip ixp project update-prompts <project-name> --fields <json> --output json` | Update individual field instructions (moon_form fields). `--fields '[{"name":"Invoice Number","instructions":"..."}]'` — match by field name. Fetches taxonomy, merges changes, preserves all field definitions. Omitting `--label-instructions` preserves the existing project-level prompt. |

### Documents

| Command | Description |
|---------|-------------|
| `uip ixp document list <project-name> --output json` | List documents — returns `[{ Uid, AttachmentRef }]` |
| `uip ixp document get <project-name> <comment-uid> -o <path> --output json` | Download original document file (image/PDF) for viewing |
| `uip ixp document text <project-name> <comment-uid> --output json` | Get OCR text — use as source of exact character values for extractions |

### Labellings

| Command | Description |
|---------|-------------|
| `uip ixp labelling label <project-name> <comment-uid> --extractions <json> --output json` | Submit Claude extractions for one document (serial only — do not parallelize) |
| `uip ixp labelling confirm <project-name> --output json` | Confirm IXP-generated predictions as-is for all documents |

### Extractions JSON Format

```json
[
  {
    "label": "Invoice Details",
    "fields": [
      { "field_id": "dba783c9b74f805b", "formatted_value": "INV-001" },
      { "field_id": "98d17d6b0e8dadc8", "formatted_value": "2024-03-15" }
    ]
  },
  {
    "label": "Line Items",
    "fields": [
      { "field_id": "c573d9279a570e2d", "formatted_value": "Widget A" },
      { "field_id": "c7dcfaaaba8aa867", "formatted_value": "10" }
    ]
  },
  {
    "label": "Line Items",
    "fields": [
      { "field_id": "c573d9279a570e2d", "formatted_value": "Widget B" },
      { "field_id": "c7dcfaaaba8aa867", "formatted_value": "5" }
    ]
  }
]
```

- Use the **flat `label_def.name`** from taxonomy — never prefix with parent names
- Non-repeating labels: one entry with all fields
- Repeating/table labels (e.g., Line Items): one entry per row with the same label name
- Only include fields with non-empty `formatted_value`
- The CLI handles parent labels, sentiment, spans, and dismissed format automatically

## Field Types and Value Formats

IXP entity_defs use these field types, identified by `inherits_from` ID:

| System Type | `inherits_from` ID | Value Format |
|-------------|-------------------|--------------|
| Exact Text | (none) | As-written in the document |
| Date | `0000000000000007` | As-written first (e.g., `02/28/2018`). If F1=0, try `YYYY-MM-DD` (e.g., `2018-02-28`) |
| Monetary Quantity | `0000000000000006` | As-written first (e.g., `$17,000.00`). If F1=0, try decimal-only (e.g., `17000.00`) |
| Number | (varies) | Numeric value as-written |
| Boolean | (varies) | `true` or `false` — but see note below |
| Inferred Text | (varies) | Extract the evidence text, not a yes/no value |

**Default rule: submit values as-written in the document.** The IXP model predicts values in the document's own format, and F1 validation compares your submission against the model's prediction string.

**Date and Monetary fields** can be tricky — if as-written gives F1=0, the model may be normalizing internally. Try the canonical format (`YYYY-MM-DD` for dates, decimal-only `17000.00` for monetary). If both give F1=0, the field type itself may be wrong — consider whether it should be Exact Text instead.

**Boolean vs Inferred Text:** Fields like "Is Signed", "Has Guarantor" often work better as **Inferred Text** than Boolean. Documents rarely contain literal "true"/"false" — the model should extract the *evidence text* that proves the condition (e.g., the signature line, the provision language). Empty extraction = condition not met. If Boolean fields consistently score F1=0, this may be why.

## OCR Text vs Image Values

- **Prefer OCR-verbatim** — copy values directly from the OCR text when they match the document
- **If OCR is clearly garbled** (e.g., `INGRAM NTCRO INC` instead of `INGRAM MICRO INC`), use the clean value from the image — the API does not enforce verbatim OCR

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `400 No moon fields defined for label "Invoice > Details"` | Used parent-prefixed label name | Use flat `label_def.name` from taxonomy (e.g., `"Invoice Details"`) |
| Date/Monetary fields always F1 = 0 | Value format doesn't match what the model predicts | Re-label using the value **as-written in the document** (e.g., `02/28/2018`, `$17,000.00`). The model predicts in the document's own format. |
| `404 No such project` | Used project Title instead of Name | Use `Name` from `project list` (lowercase slug with `-ixp` suffix) |
| `400 Moon forms for label present multiple times` | Duplicate label entries in extractions | Group all fields for same non-repeating label into one entry |
| Metrics don't change after update-prompts | Didn't re-label documents | Re-label all documents after updating instructions |
| ModelVersion doesn't advance | Retrain still in progress | Any change to model inputs (labellings OR instructions) triggers a full retrain. Even changing 1 field instruction or 1 document labelling retrains the entire model. Wait ~2 min then retry. |
| Fields/moon_form disappeared after update | Used `--entity-defs` flag or raw dataset update with `entity_defs` payload | **NEVER use `--entity-defs`** — it is a destructive full-replacement that deletes fields. Always use `--fields` which only updates field instructions safely. |
| Field instructions conflict with label_def instructions | `update-prompts --fields` only edits moon_form per-field instructions, NOT the parent label_def instructions | Before iterating, read the label_def `instructions` and ensure they don't contradict your per-field instructions. If the label_def says "decimal format, no commas" but your field says "as-written with commas", the model gets conflicting signals. |
| Boolean fields always F1=0 | Documents don't contain literal "true"/"false" | Consider using Inferred Text instead — extract the evidence text that proves the condition (signature line, provision language). Empty = false. |

## Instruction Quality Standards

When writing or improving field instructions, aim for these benchmarks (from the production taxonomy system):

- **Minimum length**: 120+ characters. Short instructions like "Extract the date" are too vague.
- **Location hint**: describe WHERE in the document (section, header area, table, near a label). Keywords: "section", "header", "table", "top of", "labeled", "near".
- **Format pattern**: specify the EXACT format (e.g., "Format: MM/DD/YYYY", "Format: $N,NNN.NN").
- **Real example**: include an actual value from the documents (e.g., "Example: '2106732'", "Example: 'SINV0077023'").
- **Disambiguation**: if similar fields exist, clarify what NOT to extract (e.g., "Do NOT confuse with PO Number").

**Good instruction** (165 chars):
> "The unique invoice identifier, found in the header area near the top-right, labeled 'Invoice #' or 'Invoice Number'. Format: alphanumeric. Example: '2106732'."

**Bad instruction** (25 chars):
> "Extract the invoice number"

**For fields visible in documents** — include location, format, and a real example from the actual documents.
**For fields NOT visible** — use a generic instruction with no example: "Extract [what] from this document, as it appears on the page."

## Guides

- [Project Setup Guide](references/project-setup.md) — create a new project, label documents, get metrics
- [Improve Prompts Guide](references/improve-prompts.md) — iterative optimization loop with regression detection
- [Label Documents Guide](references/label-documents.md) — reusable workflow for labelling documents (used by both guides above)

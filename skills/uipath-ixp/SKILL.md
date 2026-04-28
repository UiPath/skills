---
name: uipath-ixp
description: "UiPath IXP (Document Understanding) — review IXP predictions with Claude, confirm valid fields, improve prompts, publish models. For Orchestrator/deploy→uipath-platform."
---

# UiPath IXP Document Extraction Assistant

Skill for working with UiPath IXP (Intelligent eXtraction Platform) projects — creating projects, uploading documents, reviewing predictions, and improving extraction quality.

## What This Skill Can Do

- **Create a new IXP project** — upload documents, generate or import taxonomy, review predictions, confirm valid fields, get metrics → [Project Setup Guide](references/project-setup.md)
- **Improve an existing project** — diagnose weak fields, rewrite instructions, review new predictions, verify improvement → [Improve Prompts Guide](references/improve-prompts.md)
- **Publish a model** — pin a trained model version, tag it as live/staging, set a description
- **List or inspect IXP projects** — use the CLI commands below

When the user asks to create a project or label documents, follow the [Project Setup Guide](references/project-setup.md). If the user provides a taxonomy file, use `--skip-taxonomy` and `import-taxonomy` (Option B in the guide).
When the user asks to improve scores/prompts for an existing project, follow the [Improve Prompts Guide](references/improve-prompts.md).

## Critical Rules

1. **ONLY use `uip ixp` CLI commands as documented in this skill** — do NOT use curl, do NOT call REST APIs directly, do NOT grep/read source code, do NOT explore the codebase.
2. **Run workflows end-to-end automatically** — do NOT ask the user to do individual steps.
3. **Always use `--output json`** when parsing CLI output programmatically.
4. **Use `/tmp/ixp/<project-name>/` as the working directory with this structure:**
   ```
   /tmp/ixp/<project-name>/
   ├── docs/         # Document images (doc_1.png, doc_2.png, …) — downloaded once, reused across sessions
   ├── text/         # OCR text files (doc_1.json, doc_2.json, …) — downloaded once, reused across sessions
   ├── taxonomies/   # Taxonomy snapshots (v1.json, v2.json, …) — new version after each update-prompts
   └── prompts/      # Instruction update payloads (field_updates.json, group_updates.json, …)
   ```
   At the start of any workflow: `mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}`. If the directory already exists from a previous session, **reuse existing files** — do not re-download documents or OCR text that are already present. Do NOT use the Write tool for `/tmp/ixp/` paths — on Windows it resolves to a different location than bash.
5. **Use heredocs for `--fields`/`--groups`** — for `update-prompts --fields` and `--groups`, use heredocs (`cat > /tmp/ixp/<project-name>/prompts/field_updates.json << 'EOF' ... EOF`) then `"$(cat /tmp/ixp/<project-name>/prompts/field_updates.json)"`.
6. **Never use `UID` as a variable name** — it is a readonly shell variable. Use `DOC_ID`, `DOCUMENT_ID`, etc.
7. **Always use the project `Name`, never the `Title`** — the `project list` output has both `Name` (e.g., `my_invoices-f1afa9ef-ixp`) and `Title` (e.g., `My_Invoices`). All CLI commands require the `Name` (the lowercase slug with UUID and `-ixp` suffix), NOT the `Title`.
8. **Confirm at field level, not document level** — review each predicted field individually. Confirm only the fields that are correct using `labelling confirm --fields`. Fields with wrong predictions are left unannotated. Fields with OCR-mangled values can be corrected using `--corrections` (keeps the prediction's document reference but fixes the text).
9. **Do NOT manually extract values** — Claude does not construct extractions JSON or use `labelling label`. All labelling goes through `labelling confirm` with predictions from IXP.
10. **Max 8 documents for taxonomy suggestion** — the suggest-taxonomy endpoint accepts at most 8 attachment references.
11. **Keep field instructions short and pattern-focused** — 2-4 sentences max, 120-250 characters. Long instructions with many examples or detailed exclusion lists cause the model to memorize the list instead of learning the pattern, resulting in F1=0. Prefer: "Extract [what] from [where]. Format: [pattern]. Example: '[one value]'." over a paragraph with 10 examples.
12. **Claude is the reviewer, not the extractor** — IXP generates predictions, Claude validates them. For each document, review predicted field values against the document image and OCR text. Confirm correct fields (`labelling confirm --fields`), correct OCR-mangled values (`--corrections`), and skip wrong fields. Do NOT manually extract values. If a field's F1 is low, improve the **prompt** so IXP predicts better values.

## CLI Commands Reference

### Projects

| Command | Description |
|---------|-------------|
| `uip ixp project list --output json` | List all IXP projects |
| `uip ixp project get <project-name> --output json` | Get a project |
| `uip ixp project create "<name>" <folder-path> [-d "<description>"] [--skip-taxonomy] --output json` | Create project and upload docs. By default suggests+imports taxonomy. `-d` provides context for better taxonomy suggestion. Use `--skip-taxonomy` to create a blank project (import taxonomy separately). Use `ProjectName` from output. |
| `uip ixp project import-taxonomy <project-name> <file> --output json` | Import taxonomy from a local JSON file. Accepts `{ field_types, label_group }` or `{ entity_defs, label_groups }` format. |
| `uip ixp project rename <project-name> "<new-title>" --output json` | Update the display title of a project |
| `uip ixp project taxonomy <project-name> --output json` | Get taxonomy (entity_defs + label_groups with field definitions) |
| `uip ixp project metrics <project-name> --output json` | Get validation metrics — `FieldGroups[]` (per-group) and `Fields[]` (per-field F1/Precision/Recall) |
| `uip ixp project configure-model <project-name> [options] --output json` | Configure extraction model. Options: `--model` (gemini_2_5_flash/gemini_2_5_pro/gpt_4o_2024_05_13), `--preprocessing` (none/table_mini/table), `--attribution` (model/rules), `--temperature`, `--top-p`, `--seed`, `--frequency-penalty` |
| `uip ixp project update-prompts <project-name> --fields <json> [--groups <json>] --output json` | Update field and/or field group instructions. `--fields` (required): per-field updates `[{"name":"Invoice Number","instructions":"..."}]`. `--groups` (optional): label_def updates `[{"name":"Invoice","instructions":"..."}]`. `--label-instructions` (optional): project-level prompt. |
| `uip ixp project list-models <project-name> --output json` | List all model versions and tags. Returns `Models[]` (Version, Pinned, TrainedTime) and `Tags[]` (Name, Version). |
| `uip ixp project publish <project-name> --output json` | Publish (pin) the latest model version. Options: `--model-version <N>` (specific version, default: latest), `--description "<text>"` (set description), `--tag <name>` (assign tag: "live", "staging", or custom). |

### Documents

| Command | Description |
|---------|-------------|
| `uip ixp document list <project-name> --output json` | List documents — returns `[{ DocumentId, AttachmentRef }]` |
| `uip ixp document image <project-name> <document-id> -o <path> --output json` | Download original document file (image/PDF) for viewing |
| `uip ixp document text <project-name> <document-id> -o <path> --output json` | Get OCR text and save to file — use to cross-reference predicted values against the document |

### Labellings

| Command | Description |
|---------|-------------|
| `uip ixp labelling predictions <project-name> [document-id] --output json` | Get IXP model predictions for all documents (or a single document). Returns predicted labels with `FieldId`, `FieldName`, and `FormattedValue`. |
| `uip ixp labelling confirm <project-name> <document-id> [--fields <ids>] [--corrections <json>] --output json` | Confirm predictions for a document. `--fields "id1,id2,id3"` confirms only those fields. `--corrections '[{"field_id":"...","value":"..."}]'` overrides OCR-mangled values while keeping the prediction's document references. |

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Metrics don't change after update-prompts | Re-evaluation hasn't completed | Wait ~2 minutes for retrain. |
| ModelVersion doesn't advance | Retrain still in progress | Any change to model inputs (labellings OR instructions) triggers a full retrain. Wait ~2 min then retry. |
| Field instructions conflict with label_def instructions | `update-prompts --fields` only edits moon_form per-field instructions, NOT the parent label_def instructions | Before iterating, read the label_def `instructions` and ensure they don't contradict your per-field instructions. |

## Instruction Quality Standards

When writing or improving field instructions, focus on **what** to extract and **where** to find it. Do NOT specify format — the entity_def (field type) already handles that.

- **Minimum length**: 120+ characters. Short instructions like "Extract the date" are too vague.
- **Location hint**: describe WHERE in the document (section, header area, table, near a label). Keywords: "section", "header", "table", "top of", "labeled", "near".
- **Real example**: include an actual value from the documents (e.g., "Example: '2106732'", "Example: 'SINV0077023'").
- **Disambiguation**: if similar fields exist, clarify what NOT to extract (e.g., "Do NOT confuse with PO Number").
- **No format patterns**: do NOT include "Format: MM/DD/YYYY" or similar — the entity_def type (Date, Monetary, Text) already defines the format. Adding format in instructions creates conflicting signals.

**Good instruction** (145 chars):
> "The unique invoice identifier, found in the header area near the top-right, labeled 'Invoice #' or 'Invoice Number'. Example: '2106732'."

**Bad instruction** (25 chars):
> "Extract the invoice number"

**For fields visible in documents** — include location and a real example from the actual documents.
**For fields NOT visible** — use a generic instruction with no example: "Extract [what] from this document, as it appears on the page."

## Guides

- [Project Setup Guide](references/project-setup.md) — create a new project, label documents, get metrics
- [Improve Prompts Guide](references/improve-prompts.md) — iterative optimization loop with regression detection
- [Label Documents Guide](references/label-documents.md) — reusable workflow for labelling documents (used by both guides above)

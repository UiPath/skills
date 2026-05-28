---
name: uipath-ixp
description: "[PREVIEW] UiPath IXP (Document Understanding) — review IXP predictions with Claude, confirm valid fields, improve prompts, publish models."
---

# UiPath IXP Document Extraction Assistant

Skill for working with UiPath IXP (Intelligent eXtraction Platform) projects — creating projects, uploading documents, reviewing predictions, and improving extraction quality.

## When to Use This Skill

- User asks to create an IXP project, upload documents, or train a document extraction model
- User asks to label, review, or confirm document predictions
- User asks to improve extraction scores, prompts, or field instructions
- User asks to publish or manage IXP model versions
- User provides a taxonomy file to import into a project
- User asks for the schema of a deployed (runtime) IXP model (use `deployments get-taxonomy`)

## Critical Rules

1. **ONLY use `uip ixp` CLI commands as documented in this skill** — do NOT use curl, do NOT call REST APIs directly, do NOT grep/read source code, do NOT explore the codebase.
2. **Run workflows end-to-end automatically** — do NOT ask the user to do individual steps.
3. **Always use `--output json`** when parsing CLI output programmatically.
4. **Use `/tmp/ixp/<project-name>/` as the working directory with this structure:**
   ```
   /tmp/ixp/<project-name>/
   ├── docs/         # Document files (<document-id>.pdf, .png, …) — downloaded once, reused across sessions
   ├── taxonomies/   # Taxonomy snapshots (v1.json, v2.json, …) — new version after each update-prompts
   └── prompts/      # Instruction update payloads (field_updates.json, group_updates.json, …)
   ```
   At the start of any workflow: `mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,prompts}`. If the directory already exists from a previous session, **reuse existing files** — do not re-download documents that are already present. Do NOT use the Write tool for `/tmp/ixp/` paths — on Windows it resolves to a different location than bash.
5. **Use heredocs for `--fields`/`--groups`** — for `update-prompts --fields` and `--groups`, use heredocs (`cat > /tmp/ixp/<project-name>/prompts/field_updates.json << 'EOF' ... EOF`) then `"$(cat /tmp/ixp/<project-name>/prompts/field_updates.json)"`.
6. **Never use `UID` as a variable name** — it is a readonly shell variable. Use `DOC_ID`, `DOCUMENT_ID`, etc.
7. **Always use the project `Name`, never the `Title`** — the `project list` output has both `Name` (e.g., `my_invoices-f1afa9ef-ixp`) and `Title` (e.g., `My_Invoices`). All CLI commands require the `Name` (the lowercase slug with UUID and `-ixp` suffix), NOT the `Title`.
8. **Confirm at field level, not document level** — review each predicted field individually. Confirm only the fields that are correct using `labelling confirm --fields`. Fields with wrong predictions are left unannotated. **`--corrections` is ONLY for OCR-mangled values** — the prediction found the right field in the right location and the bytes-on-page are right, but the text was garbled (e.g., `MSIÓÓÓ601020/` → `MSI0601020`). Do NOT use `--corrections` to flip a wrong boolean, fix a wrong inferred/computed value, or change any value where the prediction itself was the wrong answer — those are NOT CONFIRMED. Overriding a non-OCR prediction is manual extraction (forbidden by rule 11).
9. **Do NOT manually extract values** — all labelling goes through `labelling confirm` with predictions from IXP.
10. **Max 8 documents for taxonomy suggestion** — the suggest-taxonomy endpoint accepts at most 8 attachment references.
11. **Claude is the reviewer, not the extractor** — IXP generates predictions, Claude validates them. For each document, review predicted field values against the document file (Read tool handles PDF, PNG, JPG, etc.). Confirm correct fields (`labelling confirm --fields`), correct OCR-mangled values (`--corrections`), and skip wrong fields. Do NOT manually extract values. If a field's F1 is low, improve the **prompt** so IXP predicts better values.
12. **Mark a field as missing only when IXP also did** — `labellings mark-missing` is the explicit-missing analogue of `labellings confirm`. Only use it when IXP predicted no value (or an empty value) for that field on that document AND the field is genuinely absent. If IXP predicted a wrong value, leave the field NOT CONFIRMED — choosing "missing" yourself is the same kind of extractor decision rule 11 forbids.

## Quick Start

1. Run `uip ixp projects list --output json` to see existing projects
2. To create a new project: follow [Project Setup Guide](references/project-setup-guide.md)
3. To improve an existing project: follow [Improve Prompts Guide](references/improve-prompts-guide.md)
4. To label documents on an existing project: follow [Label Documents Guide](references/label-documents-guide.md)

If the user provides a taxonomy file, use `--skip-taxonomy` and `import-taxonomy` (Option B in the Project Setup guide).

## Task Navigation

| User request | Action |
|-------------|--------|
| "Create an IXP project" / "Upload documents to a new project" | [Project Setup Guide](references/project-setup-guide.md) — **new** projects only (uploads + taxonomy in one call). For **existing** projects, see the "Upload a document" row below. |
| "Import this taxonomy" / provides a taxonomy file | [Project Setup Guide](references/project-setup-guide.md) — Option B (`--skip-taxonomy` + `import-taxonomy`) |
| "Label documents" / "Review predictions" | [Label Documents Guide](references/label-documents-guide.md) |
| "Improve scores" / "Fix prompts" / "Improve F1" | [Improve Prompts Guide](references/improve-prompts-guide.md) |
| "Publish the model" / "Tag as live" | `uip ixp projects publish <project-name> --output json` |
| "Show metrics" / "What are the scores?" | `uip ixp projects get-metrics <project-name> --output json` |
| "List projects" | `uip ixp projects list --output json` |
| "Configure the model" | `uip ixp projects configure-model <project-name> [options] --output json` |
| "Upload a document" / "Add documents to an existing project" | `uip ixp documents upload <project-name> <file> --output json` — see [CLI Reference § Uploading documents](references/cli-reference.md#uploading-documents-to-an-existing-project). One file per call; loop for multiple. For brand-new projects use `projects create` instead. |
| "Delete a document" / "Remove a document" | `uip ixp documents delete <project-name> <document-id> --output json` — irreversible, triggers retrain. To delete by filename, look up the `DocumentId` via `documents list` (the `Filename` column shows the original upload name). |
| "Add / delete / rename a field group" | `uip ixp groups {add,delete,rename} <project-name> --name <name> ... --output json` — see [CLI Reference § Groups](references/cli-reference.md#groups). `groups add` requires `--instructions` and `--fields '<json>'` with at least one field. `delete` requires `--confirm-data-loss`. |
| "Add / edit / rename / delete a data type" | `uip ixp data-types {add,update-instructions,rename,delete} <project-name> --name <name> ... --output json` — see [CLI Reference § Data Types](references/cli-reference.md#data-types). `add` requires `--kind` (text/date/money/number/boolean/choice) and `--instructions`. `--input-value` (exact-match/inferred) is required only for `--kind text` and `--kind choice`; the other kinds don't have this property and the CLI rejects the flag for them. `delete` requires `--confirm-data-loss` because referencing fields break. |
| "Add / delete / rename / retype a field" | `uip ixp fields {add,delete,rename,change-type} <project-name> --group <name> --field <name> ... --output json` — see [CLI Reference § Fields](references/cli-reference.md#fields). `change-type` deletes annotations and requires `--confirm-data-loss`. |
| "Mark a field as missing for a document" | `uip ixp labellings mark-missing <project-name> <document-id> --fields <ids> --output json` — confirms the field as having no value and no location. **Only call this for fields where IXP's prediction was also missing/empty.** See Critical Rule 12. |
| "Undo / unconfirm a wrong confirmation" | `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` — rolls back an earlier `confirm` or `mark-missing` for the listed fields. Every other annotation on the document is carried forward. |

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Metrics don't change after update-prompts | Re-evaluation hasn't completed | Wait ~2 minutes for retrain. |
| ModelVersion doesn't advance | Retrain still in progress | Any change to model inputs (labellings OR instructions) triggers a full retrain. Wait ~2 min then retry. |
| Field instructions conflict with label_def instructions | `update-prompts --fields` only edits per-field instructions, NOT the parent label_def instructions | Before iterating, read the label_def `instructions` and ensure they don't contradict your per-field instructions. |

## Reference Navigation

- [CLI Commands Reference](references/cli-reference.md) — all `uip ixp` commands with options and output formats
- [Project Setup Guide](references/project-setup-guide.md) — create a new project, review and label documents
- [Improve Prompts Guide](references/improve-prompts-guide.md) — iterative optimization loop with regression detection
- [Label Documents Guide](references/label-documents-guide.md) — reusable workflow for reviewing and confirming predictions

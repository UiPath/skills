---
name: uipath-ixp
description: "[PREVIEW] UiPath IXP (Document Understanding) — TRIGGER for raw IXP project work: create/import taxonomy, upload documents, review IXP predictions with Claude, confirm valid fields, improve prompts, publish/manage models, and inspect a deployed model taxonomy. DO NOT TRIGGER for Maestro Flow / `.flow` questions, adding IxP/document-extraction nodes to a Flow, or asking what IxP models are available in Maestro; use `uipath-maestro-flow` for those because it lists Flow-callable models through the Maestro registry."
---

# UiPath IXP Document Extraction Assistant

Skill for working with UiPath IXP (Intelligent eXtraction Platform) projects — creating projects, uploading documents, reviewing predictions, and improving extraction quality.

## When to Use This Skill

- User asks to create an IXP project, upload documents, or train a document extraction model
- User asks to label, review, or confirm document predictions
- User asks to improve extraction scores, prompts, or field instructions
- User asks to publish or manage IXP model versions
- User provides a taxonomy file to import into a project
- User asks for the project taxonomy at a specific trained model version — what the schema looked like when version N was published (use `deployments get-taxonomy <project-name> --version <N>`)

**Do not use this skill** when the user is working in Maestro Flow / `.flow`, wants to add an IxP or document-extraction node to a flow, or asks what IxP models are available in Maestro. Those requests belong to `uipath-maestro-flow`, which uses the flow registry (`uip maestro flow registry search "uipath.ixp"`) rather than IXP project commands.

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
5. **Use heredocs for `--updates`** — for `fields update-prompts --updates` and `groups update-prompts --updates`, use heredocs (`cat > /tmp/ixp/<project-name>/prompts/field_updates.json << 'EOF' ... EOF`) then `"$(cat /tmp/ixp/<project-name>/prompts/field_updates.json)"`.
6. **Never use `UID` as a variable name** — it is a readonly shell variable. Use `DOC_ID`, `DOCUMENT_ID`, etc.
7. **Always use the project `Name`, never the `Title`** — the `project list` output has both `Name` (e.g., `my_invoices-f1afa9ef-ixp`) and `Title` (e.g., `My_Invoices`). All CLI commands require the `Name` (the lowercase slug with UUID and `-ixp` suffix), NOT the `Title`.
8. **Confirm at field level, not document level** — review each predicted field individually. Confirm only the fields that are correct using `labelling confirm --fields`. Fields with wrong predictions are left unannotated. **`--corrections` is ONLY for OCR-mangled values** — the prediction found the right field in the right location and the bytes-on-page are right, but the text was garbled (e.g., `MSIÓÓÓ601020/` → `MSI0601020`). Do NOT use `--corrections` to flip a wrong boolean, fix a wrong inferred/computed value, or change any value where the prediction itself was the wrong answer — those are NOT CONFIRMED. Overriding a non-OCR prediction is manual extraction (forbidden by rule 11).
9. **Do NOT manually extract values** — all labelling goes through `labelling confirm` with predictions from IXP.
10. **Max 8 documents for taxonomy suggestion** — the suggest-taxonomy endpoint accepts at most 8 attachment references.
11. **Claude is the reviewer, not the extractor** — IXP generates predictions, Claude validates them. For each document, review predicted field values against the document file (Read tool handles PDF, PNG, JPG, etc.). Confirm correct fields (`labelling confirm --fields`), correct OCR-mangled values (`--corrections`), and skip wrong fields. Do NOT manually extract values. If a field's F1 is low, improve the **prompt** so IXP predicts better values.
12. **Confirm a field as missing by listing it in `confirm --fields`, only when IXP also predicted nothing** — `labellings confirm --fields f1,f2,f3` treats every listed field uniformly: if IXP predicted a value, it's confirmed; if IXP predicted nothing for a listed field, a missing marker is written. The explicit listing IS the confirmation that the empty state is intentional. Only include a field in `--fields` for the missing case when IXP itself predicted no value (or an empty value) AND the field is genuinely absent from the document. If IXP predicted a wrong value, leave the field NOT CONFIRMED (omit it from `--fields`) — choosing "missing" yourself is the same kind of extractor decision rule 11 forbids. Use `labellings mark-missing` only as a fallback when `confirm --fields` is a no-op for a field you expected it to handle — this happens when the field has a prior annotation but doesn't appear in the current `get-predictions` output for that document (e.g., model behavior or the taxonomy changed between iterations). In that case, `mark-missing` reaches the stale annotation and overwrites it with a missing marker; `confirm` can't.

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
| "Mark a field as missing for a document" | Include the field's id in `uip ixp labellings confirm <project-name> <document-id> --fields <ids> --output json` alongside any content fields you're confirming. When IXP's prediction for that field is empty, the explicit listing writes a missing marker; when it has content, the content is confirmed. **Only list a field for the missing case if IXP also predicted nothing for it.** See Critical Rule 12. Use `labellings mark-missing` only as a fallback when `confirm --fields` is a no-op for a field you expected it to handle — typically a field with a prior annotation that the current prediction no longer includes (model or taxonomy changed between iterations). |
| "Undo / unconfirm a wrong confirmation" | `uip ixp labellings unconfirm <project-name> <document-id> --fields <ids> --output json` — rolls back an earlier `confirm` or `mark-missing` for the listed fields. Every other annotation on the document is carried forward. |
| "Set overall extraction instructions" / "Update project prompt" | `uip ixp projects update-prompt <project-name> --prompt "<text>" --output json` — replaces the taxonomy-wide prompt (the "Overall extraction instructions" field in the IXP UI). Distinct from `fields update-prompts` (per-field) and `groups update-prompts` (per-field-group). |

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Metrics don't change after a prompt update | Re-evaluation hasn't completed | Wait ~2 minutes for retrain. |
| ModelVersion doesn't advance | Retrain still in progress | Any change to model inputs (labellings OR instructions) triggers a full retrain. Wait ~2 min then retry. |
| Field instructions conflict with label_def instructions | `fields update-prompts` only edits per-field instructions, NOT the parent label_def instructions | Before iterating, read the label_def `instructions` and update them with `groups update-prompts` if they contradict the per-field prompts. |

## Reference Navigation

- [CLI Commands Reference](references/cli-reference.md) — all `uip ixp` commands with options and output formats
- [Project Setup Guide](references/project-setup-guide.md) — create a new project, review and label documents
- [Improve Prompts Guide](references/improve-prompts-guide.md) — iterative optimization loop with regression detection
- [Label Documents Guide](references/label-documents-guide.md) — reusable workflow for reviewing and confirming predictions

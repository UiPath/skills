---
confidence: medium
signatures:
  - kind: message
    value: "Command Failed"
    note: "generic Export to PDF / Save Document as PDF failure — most common cause is a missing output directory; lowercase 'Command failed' on Documents.Open → word-open-sharepoint-url-com-command-failed.md"
exclusions:
  - "invalid or un-suffixed output path → export-pdf-output-path-format.md"
  - "busy/locked Word COM session (COMException or hang) → export-pdf-com-hang.md"
---

# Export to PDF — "Command Failed" Because the Output Directory Doesn't Exist

## Context

What this looks like:
- Activity `Export to PDF` / `Save Document as PDF` (`UiPath.Word.Activities.WordExportToPdf`) faults with a **generic `Command Failed`** error (no specific cause in the message)
- The output `.pdf` is never written

What can cause it:
- The output path points at a **folder that does not exist** on the execution machine. `WordExportToPdf` does **not** auto-create intermediate directories — if the target folder isn't there, the underlying save fails and surfaces only as a generic `Command Failed`.

What to look for:
- The output path's folder vs what exists on the robot host — a path like `C:\Output\2026\Invoices\file.pdf` where `C:\Output\2026\Invoices\` was never created.
- A dynamically built output folder (date-stamped, per-customer) that is assumed to exist but isn't created by any prior step.

## Investigation

1. Read the `Export to PDF` node from the `.xaml` and capture the literal output path expression. Resolve it to a concrete path for the failing run.
2. Check whether the **parent folder** of that path exists on the execution machine (ask the user / someone with host access if off-host). A missing parent folder is the cause.
3. Confirm no earlier activity in the workflow creates that folder.

## Resolution

- **Create the folder before exporting** — add a **Create Folder** activity (target = the output directory) **immediately before** the `Word Application Scope` / export step, so the directory is built dynamically at runtime. `Create Folder` is a no-op if the folder already exists, so it is safe on every run.
- **Or build the path from a guaranteed-existing root** — point the output at a directory the robot always has (e.g. the project output folder), or have the provisioning step pre-create the target tree.
- After adding `Create Folder`, re-run and confirm the `.pdf` is written.

> The generic `Command Failed` carries no detail — a missing output directory is the most common cause, but also rule out an invalid/un-suffixed path (see [export-pdf-output-path-format.md](./export-pdf-output-path-format.md)) and a busy/locked Word COM session (see [export-pdf-com-hang.md](./export-pdf-com-hang.md)).

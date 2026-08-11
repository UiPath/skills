---
confidence: high
---

# O365 Files — Download conversion or destination error

## Context

What this looks like — a download/export operation faults on the item type, the PDF conversion, or the local destination (not on resolving the remote item). All are package-fixed messages thrown as `Office365Exception` from the shared download/export service, so the exception type is `Office365Exception` on **both** the Connections and legacy activities:

- `Folders cannot be downloaded with this activity. Please input a different DriveItem.` — the configured item is a folder.
- `Cannot convert the item into PDF format. The supported source extensions are: csv, doc, docx, odp, ods, odt, pot, potm, potx, pps, ppsx, ppsxm, ppt, pptm, pptx, rtf, xls, xlsx.` — PDF conversion requested for an unsupported source type.
- `Local File Path should point to a folder or directly to a .pdf file.` — PDF export destination has a non-`.pdf` file extension.
- `File should have a name: '<name>'.` — the destination filename reduces to empty; can also surface wrapped as `Value cannot be null. (Parameter 'File should have a name: ...')`.
- `Cannot locate file. Please ensure that you have proper permissions to access it.` — the parent drive of a **shared** item could not be resolved with the current permissions (shared-with-me items whose parent isn't accessible).

What activities can produce this error:
- **Download File** (`DownloadFileConnections`) — including its convert-to-PDF option.
- Legacy **Download File** (`DownloadFile`) and **Export As PDF** (`ExportAsPdf`).
- Copy/Download paths operating on shared items (the `Cannot locate file ...` form).

What can cause it:
- **Folder bound where a file is required** — upstream search returned a folder, or a browse selection points at a folder.
- **Unsupported conversion source** — e.g., `.txt`, `.png`, `.msg` with PDF conversion enabled; only the listed Office/text formats convert.
- **Destination misconfiguration** — local path ends in a non-`.pdf` filename for PDF export, or composes to an empty filename.
- **Shared-item permission gap** — the item was shared item-only; the connection cannot resolve its parent drive.

> **Different cause, do not apply this playbook:**
> - `The resource could not be found.` / `A file with the specified ID does not exist.` — the remote item doesn't resolve; use [drive-item-not-found.md](./drive-item-not-found.md).
> - `Multiple items with the name <name> found ...` — local destination name conflict; use [download-multiple-items-name-conflict.md](./download-multiple-items-name-conflict.md).

## Resolution

The message identifies the misconfiguration; no further investigation is needed. Fix per message:

1. **Folder input:** point the activity at a file — to download a folder's contents, iterate with **For Each File/Folder** (`ForEachFileFolderConnections`) and download per file.
2. **Unsupported PDF source:** only the listed extensions convert. Disable conversion for other types or convert upstream (e.g., download raw, convert locally).
3. **Non-`.pdf` destination:** set the local path to a folder or a filename ending in `.pdf`.
4. **Empty filename:** inspect the expression composing the destination name — ensure it yields a non-empty name for every input.
5. **Shared-item permission gap (`Cannot locate file ...`):** have the owner share the containing folder (not just the file) or grant the connection's account access to the parent; then re-run.

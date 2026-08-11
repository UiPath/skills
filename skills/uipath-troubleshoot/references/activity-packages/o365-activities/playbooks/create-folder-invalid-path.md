---
confidence: high
---

# O365 Files — Create Folder invalid name or path

## Context

What this looks like — **Create Folder** (`CreateFolderConnections`) faults on its own input validation before or while walking the target path. All surface as `Office365Exception`:

- `Value cannot be null. (Parameter 'Folder name')` — `FolderCreationMode = FolderName` but the name argument is empty/null.
- `Value cannot be null. (Parameter 'Folder path')` — `FolderCreationMode = FolderPath` but the path argument is empty/null.
- `Value cannot be null. (Parameter 'Parent folder')` — parent selection mode is "use existing" but the bound parent item is null or not a resolvable folder reference.
- `Folder path must contain at least one segment.` — the path is non-empty but reduces to zero segments after splitting (e.g., only separators). May carry a `(Parameter 'FolderPath')` suffix.
- `Folder path segment '<segment>' cannot have leading or trailing whitespace.` — a path segment has surrounding spaces. May carry a `(Parameter 'FolderPath')` suffix.
- `Cannot create folder path: '<segment>' is a file, not a folder.` — an intermediate segment of the path already exists as a **file**, so the folder chain cannot be created through it.

The failure is deterministic — same configuration, same fault, no dependency on Graph-side state except the segment-is-a-file case.

What can cause it:
- **Empty/null name or path argument** — the bound variable is empty at runtime (unassigned, or an expression that evaluates to empty for some inputs).
- **Null parent item** — the parent folder variable comes from an upstream lookup that matched nothing.
- **Path built with stray separators or padded segments** — string composition producing `folder1/ folder2` or `//folder`.
- **A file already occupying a path segment name** — the path expects `Reports/2024` to be folders but `Reports` (or `2024`) exists as a file.

> **Different cause, do not apply this playbook:**
> - `The specified item name already exists.` — the final folder already exists with `ConflictResolution = Fail`; use [item-name-already-exists.md](./item-name-already-exists.md).
> - `The resource could not be found.` / `Cannot find item configured with connection ...` — the configured **parent** folder doesn't resolve; use [drive-item-not-found.md](./drive-item-not-found.md).

## Resolution

The message names the defective input; no further investigation is needed. Fix the configuration:

1. **For `Value cannot be null. (Parameter '<name>')`:** read the named property on the activity in the workflow source. If bound to a variable, trace why it's empty at runtime (unassigned, conditional, empty upstream output) and fix the assignment; for `Parent folder`, also confirm the upstream lookup actually returned a folder.
2. **For segment errors (`at least one segment` / `leading or trailing whitespace`):** inspect the composed path value — trim each segment and remove duplicate/trailing separators where the path is built from variables.
3. **For `'<segment>' is a file, not a folder.`:** check OneDrive/SharePoint at the parent location — rename/move the conflicting file, or change the folder path to avoid the name.

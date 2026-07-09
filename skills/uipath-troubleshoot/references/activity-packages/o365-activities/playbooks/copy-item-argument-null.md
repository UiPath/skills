---
confidence: high
---

# O365 Files — Copy Item null DriveItem input

## Context

What this looks like — the legacy **Copy Item** (`CopyItem`) activity faults with a raw:

- `System.ArgumentNullException: Value cannot be null. (Parameter 'DriveItem')`

The activity checks its `DriveItem` input at the start of execution and throws when the bound variable is `null`. Legacy activity — the exception escapes unwrapped.

What can cause it:
- **Upstream lookup matched nothing.** The variable bound to `DriveItem` is the output of an upstream `FindFilesAndFolders` / get-item activity that found no match — `FindFilesAndFolders` leaves its `First` output unset when the search returns zero results, so the variable stays `null`.
- **Variable never assigned** — the output binding on the upstream activity is missing, or the assignment sits in a conditional branch that didn't run.

What to look for:
- Which variable is bound to the activity's `DriveItem` property, and which upstream activity is supposed to populate it.
- Whether the upstream search criteria can legitimately match nothing for some inputs (intermittent fault = data-dependent empty result).

> **Different cause, do not apply this playbook:**
> - A null `Destination` / parent is **not** an error for this activity — it falls back to the OneDrive root. Only the `DriveItem` parameter faults.
> - `Value cannot be null. (Parameter '<localized property name>')` from a **Connections** activity is a missing required input on that activity (wrapped form) — read that activity's configuration, e.g. [create-folder-invalid-path.md](./create-folder-invalid-path.md) for Create Folder.
> - `The resource could not be found.` — the item reference was non-null but doesn't resolve; use [drive-item-not-found.md](./drive-item-not-found.md).

## Resolution

The error is unambiguous; the `DriveItem` input was `null` at runtime. Fix the producer, then guard:

1. **Trace the variable bound to `DriveItem`** back to its producing activity and confirm the output binding is set and the producer actually ran before Copy Item.
2. **If the producer is a search (`FindFilesAndFolders`):** the search matched nothing — verify the search folder, filename filter, and search mode against what's actually in OneDrive/SharePoint, and fix the criteria.
3. **Add a null guard** (If `DriveItem Is Nothing`) between the lookup and Copy Item, handling the no-match case explicitly (skip, log, or business exception) instead of letting the copy fault.

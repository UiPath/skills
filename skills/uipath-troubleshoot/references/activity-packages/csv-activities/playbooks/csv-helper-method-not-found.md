---
confidence: high
---

# Append / Write CSV — "Method not found: 'CsvHelper...'"

## Context

What this looks like:
- A CSV activity (`Append To CSV` / `Write CSV` / `Read CSV`) faults with `Method not found: 'Void CsvHelper.CsvWriter..ctor(...)'` (or another `CsvHelper.*` member / type-load error).
- Or `Read CSV` faults with `Unable to load document` (or a generic load/assembly error) on a file that **worked flawlessly before** — the change was a Studio or package upgrade, not the file.
- The failure is at the **first CSV activity that runs** (or at compile), before any row is meaningfully processed — not a data error.

What can cause it:
- A **`CsvHelper` version conflict.** `CsvHelper.dll` is bundled in `UiPath.System.Activities` (which provides the CSV activities) and in other packages that also ship it — notably `UiPath.Excel.Activities` and `UiPath.IntelligentOCR.Activities`. When two of these are at versions that ship **incompatible `CsvHelper` builds**, the CSV activity is compiled against one `CsvHelper` API but binds the other at runtime — so the constructor/method signature it calls does not exist, and .NET throws `Method not found` (or, on `Read CSV`, fails to load the document).
- Typically surfaces after a **Studio upgrade** or after one package was upgraded (or added) without the other, leaving the project with two packages that disagree on `CsvHelper`. A previously-working file that now throws `Unable to load document` after such an upgrade is the same dependency conflict.

What to look for:
- The installed versions of **`UiPath.System.Activities`** and **`UiPath.Excel.Activities`** in `project.json` — are they from compatible release lines, or did one get upgraded independently?
- Whether the error names a `CsvHelper` type/member (the signature of a binding conflict) rather than a file or data error.

## Investigation

1. Read the error from job evidence. Confirm it is a `Method not found` / type-load error naming a **`CsvHelper`** member at a CSV activity (not a file-lock or DataTable error — those are different playbooks).
2. Read `project.json` `dependencies` and note the versions of `UiPath.System.Activities` and `UiPath.Excel.Activities`.
3. A mismatch (e.g. an old System.Activities with a newer Excel.Activities, or vice versa) is the conflict — both bundle `CsvHelper` and the resolved assembly satisfies only one.

## Resolution

- **Align the two packages:** open **Manage Packages** in Studio and upgrade **both** `UiPath.System.Activities` and `UiPath.Excel.Activities` to their latest stable versions (from the same release line) so their bundled `CsvHelper` requirements match, then rebuild/republish.
- **If a Studio/package upgrade broke a previously-working file** (`Unable to load document`): **downgrade or upgrade `UiPath.Excel.Activities`** to a version whose bundled `CsvHelper` matches `UiPath.System.Activities` again — realigning the shared dependency restores the load.
- **If only one package needs the upgrade functionally:** still bring the other to a compatible version — leaving them on divergent lines re-introduces the conflict. Check `UiPath.IntelligentOCR.Activities` too if the project uses it — it also bundles `CsvHelper`.
- **If a stale restore keeps the bad assembly:** clear the local NuGet cache (`%userprofile%\.nuget\packages`) and restore again to force a clean dependency rebuild, in case an old `CsvHelper` is being reused from cache.
- **Confirm:** after aligning, the CSV activity binds a single consistent `CsvHelper` and the `Method not found` disappears on re-run.

This is a high-confidence dependency fix: the error names a `CsvHelper` member, and a `UiPath.System.Activities` / `UiPath.Excel.Activities` version split in `project.json` is the conflict.

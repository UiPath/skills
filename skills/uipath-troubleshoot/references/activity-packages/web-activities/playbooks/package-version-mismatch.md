---
confidence: medium
---

# Web Activities — Package / Studio Version Mismatch (design-time)

## Context

What this looks like:
- A **design-time** failure in Studio — the project fails to open, validate, or the **HTTP Request wizard** ("Configure" on the activity) throws — with one of:
  - `System.MissingMethodException: Method not found: 'Void UiPath.Web.Activities...'` (or a similar `Method not found` on a `UiPath.Web.Activities` / `UiPath.WebAPI.Activities` type)
  - `HTTP Request` / `HTTP Client` shows as a **missing/unknown activity** ("Activity could not be loaded"), or the package fails to restore
  - The wizard opens then errors on **Configure**, while the same call runs fine at execution time on another machine
- The process **has not necessarily run** — this reproduces when opening / validating / configuring in Studio, not as an Orchestrator job fault.

What causes it:
- **`UiPath.WebAPI.Activities` version incompatible with the installed Studio.** A package built for a newer Studio (e.g. `1.11.1` requires Studio `22.4+`) loaded on an older Studio (e.g. `21.10`) → the wizard/activity calls a member the older Studio assemblies do not expose → `Method not found`. Documented UiPath KB.
- **Version skew across the project's own dependency set** — `UiPath.WebAPI.Activities` bumped in isolation while `UiPath.System.Activities` stays on an older line, so the resolved Web assembly binds against an older System runtime. (Same class as the UI Automation `dependency-version-conflict`, Signature A — for that package see `../../ui-automation/playbooks/dependency-version-conflict.md`.)
- **Legacy vs modern HTTP Request confusion.** The activity was renamed/reworked across the package line: the **legacy** HTTP Request ships in `UiPath.WebAPI.Activities` **earlier than `2.0.0-preview`**; the **modern** HTTP Request ships in `2.0.0-preview`+, and the **current** HTTP Request in **`2.3.0`+**. A workflow authored against one line, opened with the other package installed, can show missing-member / missing-activity errors.

What to look for:
- **`project.json` `dependencies`** — the pinned `UiPath.WebAPI.Activities` version AND `UiPath.System.Activities` version.
- **`project.json` `studioVersion`** (and the Studio version in the user's report) — the package's minimum-Studio requirement vs the installed Studio.
- **Whether the exception is `MissingMethodException` / `Method not found`** — this means the assembly **loaded** but a member is **absent** (a version-mismatch hallmark), NOT that a file is missing.

## Distinguish from the runtime assembly-load failure

`MissingMethodException` / `Method not found` at **design time** is NOT the runtime `System.IO.FileNotFoundException` / `FileLoadException` "**Could not load file or assembly 'UiPath.WebAPI.Activities'**" fault (works in Studio, fails on the robot because the robot's NuGet cache / Orchestrator feed cannot supply the pinned version). If the symptom is the runtime assembly-load fault, the fix is clearing the robot NuGet cache / republishing against a resolvable feed — do NOT apply the version-alignment fix below.

## Investigation

1. **Confirm it is design-time.** No faulted Orchestrator job; the error appears on open / validate / wizard-Configure. `uip or jobs list ... --state Faulted --output json` returns empty for this process.
2. **Read the dependency set from source.** Open `project.json`: capture `UiPath.WebAPI.Activities`, `UiPath.System.Activities`, and `studioVersion`.
3. **Compare against the installed Studio.** Determine the package's minimum Studio requirement (Manage Packages shows it) and whether the installed Studio meets it. A package ahead of the Studio line is the primary suspect.
4. **Confirm the exception class.** `MissingMethodException` / `Method not found` → member absent → version mismatch (this playbook). "Could not load file or assembly" → missing assembly → see the runtime distinction above.

## Resolution

- **Align the package to the installed Studio.** In **Manage Packages**, set `UiPath.WebAPI.Activities` to a version whose minimum-Studio requirement the installed Studio satisfies (upgrade the package, or upgrade Studio to the line the package needs).
- **Update foundational packages together.** Move `UiPath.WebAPI.Activities` and `UiPath.System.Activities` to the same mutually compatible, latest-stable line — do not bump one in isolation. Reopen / revalidate the workflow.
- **Match the HTTP Request line to the workflow.** If the workflow was authored against the current HTTP Request, ensure `UiPath.WebAPI.Activities >= 2.3.0`; if it must stay on the legacy activity, keep the package below `2.0.0-preview`.
- Do NOT clean the NuGet cache / republish for a design-time `Method not found` — the assembly loads; a member is missing. Cache cleaning is the fix for the runtime assembly-load fault only.

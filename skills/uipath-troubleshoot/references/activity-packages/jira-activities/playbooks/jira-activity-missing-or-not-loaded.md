---
confidence: medium
---

# Jira Activity — Missing Or Could Not Be Loaded Properly

## Context

What this looks like:
- In Studio (design time): a Jira activity shows `This activity is either missing or could not be loaded properly. Verify that the package which contains this activity is installed.` — often after opening or migrating an older project.
- At runtime: the job faults loading the activity with a `System.IO.FileLoadException` or `System.TypeLoadException` naming a transitive assembly — classically **RestSharp** — e.g. `Could not load file or assembly 'RestSharp, Version=…' or one of its dependencies. The located assembly's manifest definition does not match the assembly reference.`
- The `UiPath.Jira.Activities` package **is** installed and listed in `project.json`, yet the activity will not bind.

What can cause it:
- **Transitive dependency conflict (RestSharp or similar).** The legacy `UiPath.Jira.Activities` pack pins specific versions of underlying libraries (notably **RestSharp**). When another package in the same project pins a **different** RestSharp version, only one assembly wins at restore/runtime; if it is not the version the Jira pack was built against, the Jira activity's reference no longer resolves and it fails to load.
- **Migration runtime mismatch.** Moving an older project into a modern Studio / runtime (e.g. Windows-Legacy → Windows) changes the dependency graph; the legacy pack's pinned dependencies may no longer be satisfiable, producing the same load failure.

What to look for:
- The faulted/missing assembly name and version in the error (`RestSharp, Version=…`).
- Other packages in `project.json` that also depend on RestSharp or other shared transitive libraries (web/HTTP packages, other connectors).
- Whether the project was recently migrated to a newer target framework or Studio version.

## Investigation

1. Read the error. A design-time `This activity is either missing or could not be loaded properly` or a runtime `FileLoadException` / `TypeLoadException` on a transitive assembly (not an `Authentication information is invalid` or `Response was not recognized as JSON`) routes here.
2. From `project.json`, confirm `UiPath.Jira.Activities` is present, then list the other package dependencies and look for any that also pull in **RestSharp** (or whichever assembly the error names).
3. Identify the version collision: the version the Jira pack was built against vs the version another package forces. The runtime loads one; the mismatch is the cause.
4. Note whether the failure appeared right after a project migration or a package upgrade — that pins when the graph changed.

## Resolution

- **Resolve the version conflict (if the project must keep the classic pack):** align the conflicting dependency so the version the Jira pack needs is the one that loads — pin/upgrade/downgrade the **other** package, or remove the package that forces the incompatible RestSharp. Restore and re-validate that the Jira activity loads.
- **Preferred — migrate off the legacy scope:** the durable fix is to move the Jira logic from the classic `UiPath.Jira.Activities` scope to the **Integration Service** Jira connector activities. The connector uses a managed OAuth connection instead of an in-workflow scope and does not carry the legacy in-project transitive dependencies, so it is not subject to this RestSharp class of conflict. This is the recommended path for new work and when the version conflict cannot be resolved cleanly in-project.

After either fix, re-open the workflow in Studio (the activity should load) and re-run; a successful load + first call confirms it.

This is medium-confidence: the load error and a visible RestSharp version collision in `project.json` strongly indicate the dependency conflict, but the exact conflicting package and whether a clean in-project pin exists vary per project — confirm the dependency graph before committing to a pin vs a migration.

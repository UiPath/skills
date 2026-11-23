# Microsoft.Activities.Extensions Package Guide

> **Owner review pending.** Pre-filled from the migrator source (`UiPath.Upgrade.MicrosoftActivitiesExtensions`). Extend the three hooks; keep their headings.

Extension `MicrosoftActivitiesExtension`. Applies when `project.json` lists `Microsoft.Activities.Extensions` or `Microsoft.Activities`. These community packages have no Windows-framework release; the extension removes them and replaces the supported activities with Invoke Code (the table below says which). Do not pre-scan the XAML: the `analyze` run reports every affected activity per file.

## Hook 1 — Before analyze

### What the extension does

1. Removes `Microsoft.Activities.Extensions` / `Microsoft.Activities` from `project.json`.
2. Rewrites the XAML namespaces that pointed at those assemblies.
3. Replaces each supported activity with an `InvokeCode` activity in the project's expression language.
4. Adds or upgrades `UiPath.System.Activities` to at least `25.6.1` (25.10.1 writes `25.10.3`, without brackets).

| Classic activity | Replacement |
|---|---|
| Add To Dictionary, Clear Dictionary, Get From Dictionary, Key Exists In Dictionary, Remove From Dictionary | Invoke Code with working dictionary code |
| Get Instance Id, Invoke Workflow, Load Activity, Load Assembly | **Not migrated on 25.10.1**: reported as `UNSUPPORTED-MICROSOFT-ACTIVITY` (error, one result per activity type, the type named only in the message). The whole workflow holding one is copied unchanged while the package is still removed, so it does not load after migration (`Cannot create unknown type …`) and must be rewritten by hand before the build passes |
| Delay Until DateTime, Delay Until Time, Load And Invoke Workflow | Only observed inside such skipped workflows; treat them as not migrated until measured on their own |

### Flags

None.

### Stop conditions specific to this package

None.

## Hook 2 — Triage

Rule IDs: `MICROSOFT-ACTIVITY-MIGRATION-SUCCESS` (note, one per rewritten activity), `UNSUPPORTED-MICROSOFT-ACTIVITY` (error, one per unsupported activity type and file), `MICROSOFT-NAMESPACE-UPDATE` (note, per file), `MICROSOFT-ACTIVITIES-EXTENSIONS-PACKAGE-REMOVAL` and `ADD-OR-UPDATE-UIPATH-SYSTEM` (project notes). The summarizer counts them: rewrites as migrated, unsupported types as needs-attention items, the package notes on the `Packages:` line. Every unsupported activity is manual work, and so is the whole workflow holding it (Hook 3).

## Hook 3 — After upgrade

1. Workflows the tool skipped: every `UNSUPPORTED-MICROSOFT-ACTIVITY` result names one. Confirm in the output:

   ```bash
   grep -rln "assembly=Microsoft.Activities.Extensions" --include=*.xaml "<OUTPUT_DIR>"
   ```

   Each hit still references the removed package and fails to load at build (`Cannot create unknown type …`). List each under manual work as **Critical**, with the UiPath replacement for its activities (Invoke Workflow File for Invoke Workflow, Delay for the delay activities, a hand rewrite for Get Instance Id, Load Assembly and Load Activity); the build cannot pass until the workflow is rewritten.
2. Dictionary replacements compile as generated; note them once in the report as changed constructs.

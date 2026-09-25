# Microsoft.Activities.Extensions Package Guide

> **Owner review pending.** Pre-filled from the migrator source (`UiPath.Upgrade.MicrosoftActivitiesExtensions`). Extend the three hooks; keep their headings.

Extension `MicrosoftActivitiesExtension`. Applies when `project.json` lists `Microsoft.Activities.Extensions` or `Microsoft.Activities`. These community packages have no Windows-framework release; the extension removes them and replaces their activities with Invoke Code. Do not pre-scan the XAML: the `analyze` run reports every affected activity per file.

## Hook 1 — Before analyze

### What the extension does

1. Removes `Microsoft.Activities.Extensions` / `Microsoft.Activities` from `project.json`.
2. Rewrites the XAML namespaces that pointed at those assemblies.
3. Replaces each supported activity with an `InvokeCode` activity in the project's expression language.
4. Adds or upgrades `UiPath.System.Activities` to at least `25.6.1`.

| Classic activity | Replacement |
|---|---|
| Add To Dictionary, Clear Dictionary, Get From Dictionary, Key Exists In Dictionary, Remove From Dictionary | Invoke Code with working dictionary code |
| Delay Until DateTime, Delay Until Time, Get Instance Id, Invoke Workflow, Load Activity, Load And Invoke Workflow, Load Assembly | Invoke Code containing **guidance comments only**; no implementation |

### Flags

None.

### Stop conditions specific to this package

None.

## Hook 2 — Triage

Rule IDs for this extension are listed in `tool.driver.rules` of the analyze log; classify by level. Every guidance-only replacement is manual work: the generated Invoke Code does nothing until implemented.

## Hook 3 — After upgrade

1. Find guidance-only placeholders:

   ```bash
   grep -rln "InvokeCode" --include=*.xaml "<OUTPUT_DIR>" | xargs grep -ln -E "DelayUntil|GetInstanceId|InvokeWorkflow|LoadActivity|LoadAndInvokeWorkflow|LoadAssembly"
   ```

   List each under manual work with the UiPath replacement the comment suggests (for example Invoke Workflow File for Invoke Workflow, Delay for the delay activities).
2. Dictionary replacements compile as generated; note them once in the report as changed constructs.

# SARIF Triage Guide

How to turn a migrator SARIF log into a status, a summary table, and stop decisions. Run the summarizer first; read this guide to interpret it and to handle rules the summarizer does not classify.

## Run the summarizer

```bash
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade" --json
```

- Accepts a `.sarif` file or a folder; for a folder it picks the newest `*.sarif`.
- Handles UTF-8 and UTF-16 input (PowerShell 5.1 redirection writes UTF-16) and skips stray log lines the tool prints before the JSON.
- `--json` output carries `effectiveVersions`: per package, the version the tool moved from and to. Compare `UiPath.UIAutomation.Activities` with the requested `<UIA_VERSION>`.
- Default output is a Markdown summary; `--json` prints the full classification for programmatic use.
- Node is always present where `uip` is installed.

## SARIF shape the tool produces

| Path | Content |
|---|---|
| `runs[0].tool.driver.rules[]` | `id`, `shortDescription.text`, `fullDescription.text`, `defaultConfiguration.level`, `helpUri` |
| `runs[0].results[]` | `ruleId`, `level` (`error` / `warning` / `note`), `message.text`, `locations[0].physicalLocation.artifactLocation.uri` (workflow file), `properties` |
| `results[].properties` (extension results) | `sourceActivity`, `destinationActivity`, `activityType`, `activityGuid`, `propertyName` |
| `runs[0].properties.outputPath` | `<OUTPUT_DIR>` for `upgrade` runs |
| `runs[0].invocations[0]` | Start and end time; the `.log` file is attached as the stdout artifact |

## Status mapping

The tool's own summary has three outcomes. Derive them from results, never from the exit code:

| Status | Condition |
|---|---|
| `failed` | Any `error`-level result whose rule is a core critical rule: `PROJECT-LOAD`, `XAML-WORKFLOW-PARSE`, `RESTORE-MISSING-PACKAGE`, `RESTORE-INCOMPATIBLE-PACKAGE`, `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED`, `ASSEMBLY-LOAD`, `WORKFLOW-LOAD`, `PROJECT-COPY`. Also when the log ends before `WORKFLOW-VALIDATION-*` rules appear: the pipeline aborted |
| `partial` | Any other `error` or `warning` result, **or** any rule that means an activity was left classic, partially migrated, needs manual action, or has a type issue, whatever its level. The UIA extension reports unmigrated activities (`UIAUTOMATION-ACTIVITY-MIGRATION-ERROR-<Reason>`) at note level |
| `success` | Only informational results and nothing left to do |

`partial` is the normal outcome of a migration that did its job. Do not present it as a failure; present the counts. The tool's own console summary is level-based and would call a run with unmigrated activities a success; the summarizer does not.

## Core rule IDs

| Rule | Level | Meaning | Action |
|---|---|---|---|
| `PROJECT-LOAD` | error | `project.json` unreadable or invalid | Stop. Show the message |
| `PROJECT-FRAMEWORK-UPDATE` | note | Legacy → Windows applied | Report |
| `XAML-WORKFLOW-PARSE` | error | A workflow is not well-formed XAML | Stop for that run; name the file |
| `RESTORE-PACKAGE-UPGRADE` | note | Dependency moved to a Windows-compatible version | Report old → new per package |
| `RESTORE-PACKAGE` | note / warning | Restore detail | Report only when warning |
| `RESTORE-MISSING-PACKAGE` | error | Package or version not found on any reachable feed | Stop condition. Tenant library → feed hand-off; typo or retired package → user decision; the resolved `--uia-package-version` not on the feed → re-resolve |
| `RESTORE-INCOMPATIBLE-PACKAGE` | error | No Windows-compatible version exists | Stop condition. Package must be replaced by hand after migration; offer `--ignore-missing-dependencies` with consequences |
| `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED` | error | A Legacy library dependency must be migrated and published first | Critical Rule 9. Stop |
| `ASSEMBLY-LOAD` | error | Restored assembly failed to load | Stop. Usually a feed or disk problem; show the log path |
| `REPAIR_LOCAL_ASSEMBLIES` | warning | Generated assemblies (global variables, entities, web services) could not be rebuilt | Report; expect type errors in workflows using them |
| `TYPE-CHECK` / `TYPE-MISSING` | warning | A referenced type could not be resolved | Report per file. Common with dynamically generated types; the workflow will fail to compile |
| `REFERENCES-FIX` | note | Assembly and namespace references rewritten | Report count only |
| `OBSOLETE-UIPATH-CORE-REPLACEMENT` | note | Obsolete `UiPath.Core` references replaced | Report count only |
| `WORKFLOW-LOAD` | error | Workflow could not be loaded into the object model; activity migrators skipped it | Report per file as not migrated |
| `WORKFLOW-VALIDATION-SUCCESS` | note | Workflow validates | Count |
| `WORKFLOW-VALIDATION-ISSUE` | warning | Validation issue in the migrated workflow | Carry into Step 5 verification |
| `WORKFLOW-COMPILATION-ERROR` | error | Expression compilation failed | Carry into Step 5; classify as partial, not failed |
| `PROJECT-COPY` | error | Output could not be written | Stop. Disk or path issue |

Extension rule families:

| Prefix | Extension | Guide |
|---|---|---|
| `UIAUTOMATION-*` | UI Automation | [packages/uia-guide.md § Hook 2](packages/uia-guide.md#hook-2--triage) |
| `<CLASSIC-ACTIVITY>-ACTIVITY-MIGRATION` (e.g. `SEND-EMAIL-ACTIVITY-MIGRATION`) | Mail, GSuite, Office 365 | [packages/mail-guide.md](packages/mail-guide.md), [packages/gsuite-guide.md](packages/gsuite-guide.md) |
| Rules listed by `--help` for the Microsoft extension | Microsoft.Activities.Extensions | [packages/microsoft-activities-guide.md](packages/microsoft-activities-guide.md) |

Unknown rule: read its `shortDescription` and `fullDescription` in `tool.driver.rules` and classify by level.

## Stop conditions

Apply after `analyze`, in this order:

1. `status: failed` → stop, show the failing messages and the `.log` path.
2. `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED` → stop (libraries first).
3. `RESTORE-MISSING-PACKAGE` or `RESTORE-INCOMPATIBLE-PACKAGE` → stop, offer the feed hand-off or `--ignore-missing-dependencies` as an explicit user decision.
4. Any package guide stop condition (each guide's Hook 2 lists them).
5. Otherwise continue to `upgrade` without asking.

After `upgrade`, `failed` means stop and report. `partial` and `success` continue to verification.

## Summary table

Present this after every run. Fill from the summarizer output.

```markdown
| Area | Count | Detail |
|---|---|---|
| Framework | 1 | Legacy → Windows |
| Package versions | N | UiPath.UIAutomation.Activities 21.10.6 → 25.10.40; UiPath.Excel.Activities 2.12.3 → 2.24.4 |
| Activities migrated | N | per extension |
| Activities not migrated | N | per file: activity, reason |
| Manual action required | N | per file: activity, message |
| Type or compile issues | N | per file |
| Missing packages | N | package ids |
```

For each not-migrated or action-required item keep `file`, `sourceActivity` (or `activityType`), and the reason suffix of the rule ID or the message text. That list becomes the "Manual work" section of the final report.

## Reading results by hand

When the summarizer cannot run, use Node inline:

```bash
node -e "const s=JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));const c={};for(const r of s.runs[0].results){const k=r.ruleId+' ['+(r.level||'note')+']';c[k]=(c[k]||0)+1}console.log(c)" "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
```

Never open the `.sarif` in the conversation unfiltered: logs for large projects run to megabytes.

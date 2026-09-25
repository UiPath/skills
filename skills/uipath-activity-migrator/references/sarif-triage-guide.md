# SARIF Triage Guide

How to turn a migrator SARIF log into a status, a summary table, and stop decisions. Run the summarizer first; read this guide to interpret it and to handle rules the summarizer does not classify.

## Run the summarizer

```bash
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade/analyze-latest.sarif" --out "<PROJECT_DIR>/.upgrade/analyze-latest.md"
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade" --json
```

- Accepts a `.sarif` file or a folder; for a folder it picks the newest `*.sarif`.
- Handles UTF-8 and UTF-16 input (PowerShell 5.1 redirection writes UTF-16) and skips stray log lines the tool prints before the JSON.
- stdout is short by design: status, counts (migrated, left classic, needs attention, blockers), blockers, and what needs attention grouped by reason and by file. Items appear inline only when there are ten or fewer. It scales to hundreds of workflows because it never prints one line per activity.
- A `failed` without blockers and every `unknown` carry a `Reason:` line under the status line. A "Step failures" section lists steps that threw as a whole at warning level (`Step failed: <Step> - <exception>`): the run continued without them, and an extension step there migrated nothing in this run.
- "Left classic" counts the UIA activities the tool did not migrate. They compile and run as classic; the report carries them as a count, and the `--out` file's "UIA not migrated" section is their list. "Needs attention" counts activities, not results: every activity partially migrated, every activity or property warning (these become `[PostMigration Action Required]` annotations in the XAML and are where the post-migration work lives), productivity results left unmigrated or warned, and per-file type issues. The tool often emits two results per finding: one whose bare rule id carries the prose and one whose suffixed rule id carries the reason; the pairing is bare versus suffixed, at any level. Both lines count per activity, so they share the header's denominator. "By reason" sums above it only when one activity has several distinct reasons, which counts under each.
- `--out <file>` writes the full per-item report (every list, rule counts). That file and the tool's own HTML report are the drill-down; the chat report points at them.
- `--json` prints the full classification, including `effectiveVersions` (per package, from → to; compare `UiPath.UIAutomation.Activities` with `<UIA_VERSION>`), `attention.byReason` / `attention.byFile`, `leftClassic` in the same shape, and `uia.migratedItems`: one `{file, activity, guid, type}` per activity the tool rewrote, the ledger the runtime verification guide attributes a failure against.
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
| `failed` | Any `error`-level result with no file location: the tool's own stop rule, so the run ended there (project load, restore, assembly load, project copy, or a core step that threw, reported as rule `ERROR` with a `Step failed: <Step> - <exception>` message). Also any project-level stop condition an extension reports at warning level, and a log without validation results that carries error-level results |
| `partial` | Any other `error` or `warning` result, **or** any rule that means an activity was left classic, partially migrated, needs manual action, or has a per-file issue, whatever its level. The UIA extension reports unmigrated activities (`UIAUTOMATION-ACTIVITY-MIGRATION-ERROR-<Reason>`) at note level. A whole step that threw at warning level (rule `WARNING`, no file) is `partial` too: the run went on without that step |
| `success` | Only informational results and nothing left to do |
| `unknown` | No results at all, or no validation result and no `PROJECT-COPY` without any error-level result. Three causes, named on the summarizer's `Reason:` line: a project without workflows, the Validate step threw as a whole (`Step failed: ValidateWorkflowStep`), or a newer tool build that reports validation under rule ids the summarizer does not know, listed under rules outside the known families. Handle exactly like `failed`: stop and report the reason. It has not occurred in any recorded run |

`partial` is the normal outcome of a migration that did its job. Do not present it as a failure; present the counts. The tool's own console summary is level-based and would call a run with unmigrated activities a success; the summarizer does not.

## Core rules: policy by category

Core rules come from the tool build and their set changes with it; do not keep a list. The meaning of any rule is its `fullDescription` in `tool.driver.rules` and the result's `message.text`. What to do about it follows from its category:

1. **Restore failures** (`RESTORE-MISSING-PACKAGE`, `RESTORE-INCOMPATIBLE-PACKAGE`, `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED`): stop conditions with a user decision; see [Stop conditions](#stop-conditions).
2. **Any error-level result with no file location**: the tool stopped the run there (project load, restore, assembly load, project copy, or a core step that threw, rule `ERROR` with `Step failed: <Step> - <exception>`). Status `failed`; show the message and the `.log` path; stop.
3. **Per-file issues** at `warning` or `error`: unresolved types, generated assemblies that could not be rebuilt, a workflow that could not be parsed or loaded, compilation or validation problems, and a workflow a step could not process (rule `ERROR` or `WARNING` with a file, message `Error processing workflow …`). Status `partial`; list per file and carry them into Step 5 verification. A workflow that failed this way was skipped by every later step, the activity migrators included, and copied unchanged: report it as not migrated.
4. **Whole-step failures at `warning` level** (rule `WARNING`, `Step failed: <Step> - <exception>`, no file): the run continued without that step. For an extension step this means the extension migrated nothing in this run; report it under needs attention with its message, and never read the absence of that extension's results as "nothing to migrate".
5. **Notes**: framework flip, package moves (`RESTORE-PACKAGE-UPGRADE` and the extensions' `*-PACKAGE-UPGRADE` / `*-PACKAGE-MIGRATION` rules), reference fixes, validation success. Counts and the package-version row only.

The summarizer applies the same categories, so its `status` and `blockers` already reflect them.

Extension rule families:

| Prefix | Extension | Guide |
|---|---|---|
| `UIAUTOMATION-*` | UI Automation | [packages/uia-guide.md § Hook 2](packages/uia-guide.md#hook-2--triage) |
| `<CLASSIC-ACTIVITY>-ACTIVITY-MIGRATION` (e.g. `SEND-EMAIL-ACTIVITY-MIGRATION`) | Mail, GSuite, Office 365 | [packages/mail-guide.md](packages/mail-guide.md), [packages/gsuite-guide.md](packages/gsuite-guide.md) |
| Rules listed by `--help` for the Microsoft extension | Microsoft.Activities.Extensions | [packages/microsoft-activities-guide.md](packages/microsoft-activities-guide.md) |

Unknown rule: read its `shortDescription` and `fullDescription` in `tool.driver.rules` and classify by level.

## Stop conditions

Apply after `analyze`, in this order:

1. The summarizer exits 2 (`cannot parse …` or `no .sarif files`) → the tool wrote no log: the process died or rejected the command line. The cause is in `<PROJECT_DIR>/.upgrade/analyze-latest.err` and the exit code. Fix it and rerun analyze; a crash is not yours to fix, so stop and report it with the `.err` content.
2. `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED` → stop (libraries first).
3. `RESTORE-MISSING-PACKAGE` or `RESTORE-INCOMPATIBLE-PACKAGE` → stop, offer the feed hand-off or `--ignore-missing-dependencies` as an explicit user decision.
4. Any package guide stop condition (each guide's Hook 2 lists them).
5. `status: failed` or `status: unknown` for any other reason → stop, show the blockers or the `Reason:` line and the `.log` path.
6. Otherwise continue to `upgrade` without asking.

After `upgrade`, a summarizer parse failure, `failed`, or `unknown` means stop and report; `<OUTPUT_DIR>` may be partially written, so delete or rename it before any rerun (Step 1 forbids reusing it silently). `partial` and `success` continue to verification.

## What goes into the report

Success is a single line with counts. Activities left classic are a count on that line, never lines; the `--out` file's "UIA not migrated" section is their list. Detail exists only for what needs attention, and only grouped: by reason (`VariableSelector ×9, ClassicExceptionsInTryCatch ×2`) and by file (the few files with most items). The full per-item list lives in the `--out` file; the tool's HTML report is the per-activity drill-down. Never paste per-activity lists into the chat for a project of any size; list items inline only when there are ten or fewer.

## Reading results by hand

When the summarizer cannot run, use Node inline:

```bash
node -e "const s=JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));const c={};for(const r of s.runs[0].results){const k=r.ruleId+' ['+(r.level||'note')+']';c[k]=(c[k]||0)+1}console.log(c)" "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
```

Never open the `.sarif` in the conversation unfiltered: logs for large projects run to megabytes.

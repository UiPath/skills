# SARIF Triage Guide

How to turn a migrator SARIF log into a status, a summary table, and stop decisions. Run the summarizer first; read this guide to interpret it and to handle rules the summarizer does not classify.

## Run the summarizer

```bash
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade/analyze-latest.sarif" --out "<PROJECT_DIR>/.upgrade/analyze-latest.md"
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade" --json
```

- Accepts a `.sarif` file or a folder; for a folder it picks the newest `*.sarif`.
- Handles UTF-8 and UTF-16 input (PowerShell 5.1 redirection writes UTF-16) and skips stray log lines the tool prints before the JSON.
- Warning-level results carry no `level` field: the tool's SARIF library omits the default level, and SARIF's default is `warning`. The summarizer applies that default; a raw read that treats a missing level as `note` hides every warning.
- stdout is short by design: status, counts (migrated, left classic, needs attention, blockers), blockers, and what needs attention grouped by reason and by file. Items appear inline only when there are ten or fewer. It scales to hundreds of workflows because it never prints one line per activity.
- A `failed` without blockers and every `unknown` carry a `Reason:` line under the status line. A "Step failures" section lists steps that threw as a whole at warning level (`Step failed: <Step> - <exception>`): the run continued without them, and an extension step there migrated nothing in this run.
- "Left classic" counts the UIA activities the tool did not migrate. They compile and run as classic; the report carries them as a count, and the `--out` file's "UIA not migrated" section is their list. "Needs attention" counts activities, not results: every activity partially migrated, every activity or property warning (these become `[PostMigration Action Required]` annotations in the XAML and are where the post-migration work lives), productivity results left unmigrated or warned, and per-file type issues. The tool often emits two results per finding: one whose bare rule id carries the prose and one whose suffixed rule id carries the reason; the pairing is bare versus suffixed, at any level. Both lines count per activity, so they share the header's denominator. "By reason" sums above it only when one activity has several distinct reasons, which counts under each.
- `--out <file>` writes the full per-item report (every list, rule counts). That file and the tool's own HTML report are the drill-down; the chat report points at them.
- `--json` prints the full classification, including `effectiveVersions` (per package, from → to, with `unchanged: true` when the project already held the target or a newer version, and `requested` plus `minimum` when the tool raised a lower request to its minimum; compare `UiPath.UIAutomation.Activities` with `<UIA_VERSION>`), `attention.byReason` / `attention.byFile`, `leftClassic` in the same shape, and `uia.migratedItems`: one `{file, activity, guid, type}` per activity the tool rewrote, the ledger the runtime verification guide attributes a failure against.
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
| `partial` | Anything the summarizer lists, whatever the result levels: an activity left classic, partially migrated or migrated with a warning; a needs-attention item (per-file issue, restore issue the user chose to ignore, action required, productivity warning, a warning or error from an unknown rule on a workflow file); or a whole step that threw at warning level (rule `WARNING`, no file), since the run went on without that step. The UIA extension reports unmigrated activities (`UIAUTOMATION-ACTIVITY-MIGRATION-ERROR-<Reason>`) at note or warning level. A warning that lands in no list, such as a version raised to the tool minimum or an extension's summary line, is informational and does not make the run partial |
| `success` | Only informational results and nothing left to do |
| `unknown` | No results at all, or no validation result and no `PROJECT-COPY` without any error-level result. Three causes, named on the summarizer's `Reason:` line: a project without workflows, the Validate step threw as a whole (`Step failed: ValidateWorkflowStep`), or a newer tool build that reports validation under rule ids the summarizer does not know, listed under rules outside the known families. Handle exactly like `failed`: stop and report the reason. It has not occurred in any recorded run |

`partial` is the normal outcome of a migration that did its job. Do not present it as a failure; present the counts. The tool's own console summary is level-based and would call a run with unmigrated activities a success; the summarizer does not.

## Core rules: policy by category

Core rules come from the tool build and their set changes with it; do not keep a list. The meaning of any rule is its `fullDescription` in `tool.driver.rules` and the result's `message.text`. What to do about it follows from its category:

1. **Restore failures** (`RESTORE-MISSING-PACKAGE`, `RESTORE-INCOMPATIBLE-PACKAGE`, `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED`): stop conditions with a user decision, in the SKILL.md Step 3 table.
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

SKILL.md applies them: the table in Step 3 after `analyze`, the paragraph in Step 4 after `upgrade`. Both key on the classification in this guide: `status`, `blockers`, the `Reason:` line and the rule IDs. This guide adds no condition of its own.

## What goes into the report

The rules are SKILL.md Step 6. What this guide adds: the summarizer's short summary is already in report shape (counts, by reason, by file, items inline only when there are ten or fewer), and the `--out` file and the tool's HTML report are the drill-down the report points at. Never paste per-activity lists into the chat for a project of any size.

## Reading results by hand

When the summarizer cannot run, use Node inline:

```bash
node -e "const s=JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));const c={};for(const r of s.runs[0].results){const k=r.ruleId+' ['+(r.level||'warning')+']';c[k]=(c[k]||0)+1}console.log(c)" "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
```

Never open the `.sarif` in the conversation unfiltered: logs for large projects run to megabytes.

---
name: uipath-activity-migrator
description: "UiPath Activity Migrator — migrate Windows-Legacy RPA projects (`project.json` with `targetFramework: Legacy`, classic `ui:` activities) to the Windows framework and modern activities with the standalone `UiPath.Upgrade.exe` (`analyze` / `upgrade` / `bulk`). Windows only. Acquires the tool when missing, resolves the target UIAutomation package line, runs analyze then upgrade into a sibling folder, verifies with `uip rpa build`, triages the SARIF report. Classic UI Automation→modern UIA, Outlook classic→Microsoft 365, GSuite classic→modern, Microsoft.Activities.Extensions→Invoke Code. Authoring or editing Legacy `.xaml`→uipath-rpa. Migration-readiness review without running the tool→uipath-review. Runtime failures after migration→uipath-troubleshoot. Maestro `instance migrate`→the Maestro skills."
when_to_use: "User says 'migrate activities', 'migrate this project', 'upgrade from Windows-Legacy', 'convert classic to modern activities', 'modernize this workflow', 'run the Activity Migrator', 'UiPath.Upgrade.exe', 'legacy to Windows', 'activity migration report'. NOT for writing new Legacy workflows (→uipath-rpa), `uip solution deploy upgrade`, or Maestro instance migration."
---

# UiPath Activity Migrator

Drive the standalone Activity Migrator (`UiPath.Upgrade.exe`) end to end: acquire, analyze, upgrade, verify, report. The tool converts a Windows-Legacy project to the Windows framework and rewrites classic activities into their modern equivalents. It runs without Studio. It requires Windows and the .NET Desktop Runtime 8.

<!--skill-flavor:host-availability-extra:start-->

<!--skill-flavor:host-availability-extra:end-->

> **Read referenced files in full.** This SKILL.md is a router. Before running `analyze`, open and read the whole package guide for every classic package the project uses (see [Package Routing](#package-routing)). Package guides add flags, config files, triage rules, and post-migration steps that the core workflow does not know.

`<SKILL_DIR>` below is the folder that contains this SKILL.md. `<PROJECT_DIR>` is the absolute path of the folder holding `project.json`. `<OUTPUT_DIR>` is the migrated copy, a sibling folder, `<PROJECT_DIR>_Upgraded` by default.

## When to Use This Skill

- User wants to **migrate**, **upgrade**, **convert**, or **modernize** a Windows-Legacy project or its classic activities
- User wants classic **UI Automation** activities rewritten as modern activities
- User wants to **run the Activity Migrator** or mentions `UiPath.Upgrade.exe`
- User wants a **migration dry run** or **migration report** produced by the tool (`analyze`)
- User wants classic **Outlook** mail, classic **GSuite**, or **Microsoft.Activities.Extensions** activities migrated

Do not use for: authoring or editing Legacy workflows (uipath-rpa, Legacy mode), a readiness review that does not run the tool (uipath-review), diagnosing runtime failures of an already-migrated project (uipath-troubleshoot), `uip solution deploy upgrade`, or Maestro `instance migrate`.

## Critical Rules

1. **Windows only.** Check the OS before anything else. On macOS or Linux, stop and tell the user to run the migration from a Windows machine that holds the project. The tool is a .NET 8 desktop process and cannot run elsewhere.
2. **Never run the tool in console mode.** Always pass `--output-format sarif` and redirect stdout to a file. Console mode opens an HTML report in the browser and prints no machine-readable result.
3. **Never trust the exit code.** The tool exits 0 whether the migration succeeded, partially succeeded, or failed. Status comes only from the SARIF results, classified per [sarif-triage-guide.md](references/sarif-triage-guide.md).
4. **Analyze before upgrade, every time.** Run `analyze`, triage it, and only then run `upgrade`. When the analyze triage shows no stop condition, proceed to `upgrade` without asking.
5. **Never write into the source project.** `upgrade` writes to a fresh sibling folder. Never point `--output-path` at `<PROJECT_DIR>`, never copy the output back over the source, never delete the source. The tool's own `.upgrade/` report folder inside the source is the only thing it writes there.
6. **Never pass secrets through the agent.** Do not type `--orchestrator-pat` or `--orchestrator-application-secret` values yourself. When a tenant feed is required, rely on the tool's fallback to the local Studio or Robot connection; if that fails, hand the user the complete command with `<PLACEHOLDER>` values to run themselves.
7. **Resolve the target UIAutomation package line explicitly.** When the project uses `UiPath.UIAutomation.Activities`, resolve the latest stable patch of a release line per [Step 2](#step-2--resolve-the-target-package-line) and pass it as `--uia-package-version=<UIA_VERSION>`. Extension options bind only in the `--name=value` form; the space-separated form parses without error and is silently ignored. Accept the tool default only when the feed is unreachable, and say so in the report. Never raise the UIAutomation package on the migrated output to reach the requested line: the migration logic ships inside the package, and the output must stay on the version that produced it.
8. **Verify with the modern CLI.** Migration is not done until `uip rpa build` passes on `<OUTPUT_DIR>`, or the remaining errors are reported as manual work after the bounded fix loop in [verification-guide.md](references/verification-guide.md).
9. **Libraries first.** When analyze reports `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED`, stop. Tell the user to migrate and publish that library to the feed before migrating this project. The tool cannot order dependencies.
10. **Bounded loops.** At most 3 build-fix iterations in Step 5. Then report what remains.
11. **Disclose telemetry once.** The tool sends usage telemetry to UiPath and has no opt-out flag. State this in the preflight summary.

## Workflow

### Step 0 — Preflight and acquire the tool

Run the acquisition script for the current shell. It locates a cached tool, downloads and extracts it when missing, checks the .NET Desktop Runtime 8, and prints one JSON object on its last stdout line.

```bash
bash "<SKILL_DIR>/scripts/ensure-migrator.sh"
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>/scripts/ensure-migrator.ps1"
```

| `status` | Action |
|---|---|
| `ok` | Record `exe` as `<MIGRATOR_EXE>` and `version`. Continue. |
| `error`, `code: not-windows` | Rule 1. Stop. |
| `error`, `code: runtime-missing` | Tell the user to install the .NET Desktop Runtime 8 (link in the script message). Stop. |
| `error`, `code: download-failed` | Proxy or offline machine. Give the manual steps from [acquisition-guide.md § Manual placement](references/acquisition-guide.md#manual-placement). Stop. |
| any other `error` | Show `message`. Stop. |

Then list the active extensions once. Their flags appear under the command's options:

```bash
"<MIGRATOR_EXE>" analyze --help
```

Summarize to the user in two lines: tool version and location, telemetry disclosure (Rule 11).

### Step 1 — Discover the project

1. Resolve `<PROJECT_DIR>`: the folder containing `project.json`. If several exist under the working directory, ask which one, unless the user named it. For "migrate everything in this repo", see [cli-reference.md § bulk](references/cli-reference.md#bulk).
2. Read `project.json` and record: `targetFramework`, `expressionLanguage`, `studioVersion`, `dependencies`. `Legacy` (or absent) is the primary case. `Windows` projects still qualify when they hold classic activities; tell the user the framework step will be a no-op.
3. Match `dependencies` against the [Package Routing](#package-routing) table. Read every matching package guide in full now.
4. Pick `<OUTPUT_DIR>`: the user's choice, else `<PROJECT_DIR>_Upgraded`. If it already exists, ask whether to delete it or use a different name. Never reuse it silently: the tool merges into an existing folder.
5. If the project is under git, run `git status --short` in it and mention uncommitted changes in the report. Do not commit or stash.

### Step 2 — Resolve the target package line

Only when `UiPath.UIAutomation.Activities` is a dependency. Rationale and details: [packages/uia-guide.md § Resolve the target line](references/packages/uia-guide.md#resolve-the-target-line).

1. If the user named a line or version ("migrate to 26.10", "use 25.10.40"), resolve that and skip the question.
2. Otherwise resolve the candidate lines from the official UiPath NuGet feed. The script needs no project and no login. Do not use `uip rpa packages versions` here: the headless Studio host it starts refuses to open Legacy projects.

   ```bash
   node "<SKILL_DIR>/scripts/resolve-package-lines.mjs" --package UiPath.UIAutomation.Activities --min 25.10.21 --studio-version "<STUDIO_VERSION>"
   ```

   Output: the two most recent LTS lines (`<year>.10`) with their highest stable patch, plus `recommended` and `reason`. The recommendation is the line matching the project's `studioVersion` when it is a candidate, otherwise the newest line.
3. Ask once with `AskUserQuestion`: recommended line first, labeled `(Recommended)`, each option showing `<line>.x → <version>` and the note that robots and Studio must run that release line.
4. If the script prints `error` (feed unreachable), use the tool default without asking and record "target version: tool default (feed unreachable)" for the report.

Record the chosen version as `<UIA_VERSION>`.

### Step 3 — Analyze

Assemble `<PACKAGE_FLAGS>` from every package guide read in Step 1 (Hook 1 sections). Then:

```bash
mkdir -p "<PROJECT_DIR>/.upgrade"
"<MIGRATOR_EXE>" analyze --project-path "<PROJECT_DIR>" --uia-package-version=<UIA_VERSION> --output-format sarif <PACKAGE_FLAGS> > "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
```

Omit `--uia-package-version` when the project has no UIAutomation dependency. The summarizer prints status, package changes, per-family counts, blockers, and per-file lists. Show the user the summary table.

Check the effective UIAutomation version in the "Package versions" row against `<UIA_VERSION>`. When they differ, the flag did not bind. The usual cause is the space-separated form (`--uia-package-version 25.10.39`), which the tool accepts and ignores; fix the command to the `=` form and rerun analyze. If the effective version still differs, stop and ask the user whether to proceed on the effective version or abort: the migrated workflows are produced by the migration service inside that package version, so the output must stay on it. Never raise the dependency on the output afterwards to reach the requested line. Then apply the stop conditions from [sarif-triage-guide.md § Stop conditions](references/sarif-triage-guide.md#stop-conditions):

| Analyze outcome | Action |
|---|---|
| No stop condition | Continue to Step 4 without asking. |
| `RESTORE-MISSING-PACKAGE` / `RESTORE-INCOMPATIBLE-PACKAGE` | Stop. Explain which package, offer the Orchestrator-feed command with placeholders (Rule 6) or `--ignore-missing-dependencies` with its consequences. Rerun analyze after the user acts. |
| `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED` | Rule 9. Stop. |
| Package guide stop condition | Follow the guide. |
| `status: failed` for any other reason | Stop. Show the failing rule messages and the `.upgrade` log path. |

### Step 4 — Upgrade

Same flags as the analyze run, plus the output path:

```bash
"<MIGRATOR_EXE>" upgrade --project-path "<PROJECT_DIR>" --output-path "<OUTPUT_DIR>" --uia-package-version=<UIA_VERSION> --output-format sarif <PACKAGE_FLAGS> > "<PROJECT_DIR>/.upgrade/upgrade-latest.sarif"
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<PROJECT_DIR>/.upgrade/upgrade-latest.sarif"
```

Confirm `<OUTPUT_DIR>/project.json` exists and its `targetFramework` is `Windows`. If the summary status is `failed`, report and stop; do not retry with different flags unless a package guide says so.

### Step 5 — Verify

Follow [verification-guide.md](references/verification-guide.md). In short:

```bash
uip rpa build "<OUTPUT_DIR>" --output json
```

Build passes: continue. Build fails: validate the offending files, fix per the guide's rules, rebuild, at most 3 iterations (Rule 10). Package guides list build errors that call for a rerun of Step 4 with an extra flag rather than a hand fix. If `uip` is unavailable, skip verification and say so prominently in the report.

### Step 6 — Post-migration and report

1. Run every matching package guide's Hook 3 section (annotations, delegated fix skills, manual follow-ups).
2. Report with this shape:

```markdown
## Migration result: <status>
- Source: <PROJECT_DIR> (untouched; `.upgrade/` report folder added)
- Output: <OUTPUT_DIR> — targetFramework Windows, build <passed|failed|not verified>
- Target UIAutomation version: <UIA_VERSION or "tool default">
- Report: <PROJECT_DIR>/.upgrade/<name>-<id>.html (+ .sarif; log: project-<id>.log)

| Area | Migrated | Not migrated | Needs manual action |
|---|---|---|---|

### Manual work
- <file>: <activity> — <why> — <what to do>

### Next steps
- Open the output with Studio 2024.10 or later; commit `<OUTPUT_DIR>` as the new project.
- <package-specific runtime prerequisites>
```

## Package Routing

Match `project.json` dependencies to guides. Every guide has three hook sections the workflow calls: **Hook 1** (flags and config before analyze), **Hook 2** (triage rules for that extension's SARIF results), **Hook 3** (post-migration steps). Adding a package to this skill means adding one guide with those three sections and one row here.

| Dependency in `project.json` | Classic signal in `.xaml` | Extension name (`--help`) | Guide |
|---|---|---|---|
| `UiPath.UIAutomation.Activities` | `<ui:Click`, `<ui:TypeInto`, `<ui:OpenBrowser`, `<ui:UiElementExists` and other `ui:` activities | `UiAutomationActivities` | [packages/uia-guide.md](references/packages/uia-guide.md) |
| `UiPath.Mail.Activities` | `SendOutlookMail`, `GetOutlookMailMessages` and other `*Outlook*` activities | `MailActivities` | [packages/mail-guide.md](references/packages/mail-guide.md) |
| `UiPath.GSuite.Activities` (classic line) | `GSuiteApplicationScope`, `GetMailMessages`, `ReadRange` under the GSuite namespace | `GSuiteActivities` (preview-gated) | [packages/gsuite-guide.md](references/packages/gsuite-guide.md) |
| `Microsoft.Activities.Extensions`, `Microsoft.Activities` | `AddToDictionary`, `GetFromDictionary`, `InvokeWorkflow` under the Microsoft namespace | `MicrosoftActivitiesExtension` | [packages/microsoft-activities-guide.md](references/packages/microsoft-activities-guide.md) |

The framework flip, package restore, reference fixing, and type checking are core steps and run for every project with no routing.

## Reference Navigation

| File | Read when |
|---|---|
| [acquisition-guide.md](references/acquisition-guide.md) | Step 0 fails, the machine is offline or behind a proxy, or the user asks where the tool lives or how to update it |
| [cli-reference.md](references/cli-reference.md) | You need a flag not shown above, `bulk` mode, Orchestrator feed options, or output semantics |
| [sarif-triage-guide.md](references/sarif-triage-guide.md) | Every analyze and upgrade run: status mapping, core rule IDs, stop conditions, summarizer usage |
| [verification-guide.md](references/verification-guide.md) | Step 5: build and validate loop, expected warnings, fix policy, Studio version requirements |
| [packages/uia-guide.md](references/packages/uia-guide.md) | Project depends on `UiPath.UIAutomation.Activities` |
| [packages/mail-guide.md](references/packages/mail-guide.md) | Project depends on `UiPath.Mail.Activities` |
| [packages/gsuite-guide.md](references/packages/gsuite-guide.md) | Project depends on classic `UiPath.GSuite.Activities` |
| [packages/microsoft-activities-guide.md](references/packages/microsoft-activities-guide.md) | Project depends on `Microsoft.Activities.Extensions` or `Microsoft.Activities` |
| `scripts/ensure-migrator.{sh,ps1}` | Step 0. Behavioral twins; change both together |
| `scripts/summarize-sarif.mjs` | Steps 3 and 4. Node script, no dependencies |
| `scripts/resolve-package-lines.mjs` | Step 2 and package guides. Lists release lines of a package from the official feed; no project or login needed |

## Anti-patterns

- Running `UiPath.Upgrade.exe` without `--output-format sarif`, or reading its exit code as a verdict
- Running `upgrade` without an `analyze` triage first, or pointing `--output-path` at the source project
- Pasting a PAT or client secret into a command line
- Hand-converting classic activities in XAML instead of letting the tool do it, or "finishing" activities the tool left classic by rewriting them blind
- Accepting the tool's default UIAutomation version when the feed was reachable
- Passing an extension option space-separated (`--uia-package-version 25.10.39`); only `--uia-package-version=25.10.39` binds
- Raising the UIAutomation package on the migrated output with `uip rpa packages install` to reach the requested line; the output must stay on the version whose migration service produced it
- Resolving package versions with `uip rpa packages versions` against a Legacy project; the headless Studio host cannot open it
- Skipping the package guides and passing no package flags for a project that uses Outlook classic or GSuite classic activities
- Declaring success because `upgrade` finished, without `uip rpa build` on the output
- Editing the SARIF summary by hand instead of rerunning the summarizer after a rerun

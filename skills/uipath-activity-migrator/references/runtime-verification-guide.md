# Runtime Verification Guide

Step 6 of the workflow, after the build passed. A run of the migrated project, performed only after the user says yes, shows whether the output runs and attributes a failure to the migration or to something else. When the failure is migration-related, the fix and rerun loop below repairs it one fix at a time, each behind one yes/no. The build verification guide proves the output compiles; this guide is the only runtime evidence the skill produces.

## Offer

Offer the run when all of these hold:

- the build passed;
- `uip` is available;
- the routed packages are UIA only: a project routed to the Mail, GSuite or Microsoft.Activities guide gets no offer;
- `project.json` has `"outputType": "Process"`; a library has nothing to run.

Ask one yes/no question: run `<MAIN>` in `<OUTPUT_DIR>` once now, against the real applications on this machine? Default no. Do not propose durations or time limits. When `<MAIN>` declares `In` arguments without defaults, ask for their values in the same question or skip the run.

| Placeholder | Meaning |
|---|---|
| `<MAIN>` | The `main` entry of `project.json` |
| `<RUN_LOG>` | `<PROJECT_DIR>/.upgrade/run-latest.log`, or `<MIGRATED_DIR>/.upgrade/run-latest.log` in fix-only mode |
| `<LEDGER>` | The summarizer's `--json` output for the upgrade SARIF: `uia.migratedItems` lists every activity the tool rewrote, `uia.notMigrated` and `uia.partial` those it left classic |

## Starting state

The run drives real applications, and a rerun must start from the state the first run started from.

1. **Before the first run**, take the baseline:
   1. Take a top-level snapshot with the UIA package's Window Baseline procedure (§ Window Baseline of the package guide `ui-automation-guide.md`).
   2. The guide ships inside the package: always at `%USERPROFILE%\.nuget\packages\uipath.uiautomation.activities\<version>\content\docs\` once Step 5 restored the project, `<version>` being the exact `UiPath.UIAutomation.Activities` version in `<OUTPUT_DIR>/project.json`; and at `<OUTPUT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/` once Studio or a run has materialized it there. Neither folder's presence decides whether the snapshot works; only the snapshot command's own answer does.
   3. Its snapshot CLI is a `uip rpa` command: run it with the `env -u UIPATH_STUDIO_PID` prefix and `--project-dir "<OUTPUT_DIR>"` like every other one, with a folder under the scratchpad for its artifacts.
   4. The snapshot CLI needs the UIAutomation package's CLI support. When it answers that it requires the `UiPath.UIAutomation.CLI` package, as 25.10 targets do, there is no snapshot: note the applications and URLs the project's XAML names instead, continue, and use the "Without a snapshot" branch of item 2 from then on.
   5. With a snapshot, the baseline is the titles, processes and URLs in the snapshot file, never the refs, which every capture re-mints. Keep the baseline for the whole loop.
   6. Never infer window state from `Get-Process` or any other process listing: they report processes, not windows, and hide every window but one of a browser.
2. **Before every rerun**, restore the starting state. The project's applications are what the XAML names in any activity, whatever the activity type: every `app=` attribute in a selector, every executable name in a property, every URL in a property; the run log's `Audit: Using … App` lines confirm which of them the run drove.

   **With a snapshot:**
   1. Capture again and diff against the baseline, following the same section's "Diff and close leaked windows" part.
   2. A new window or a new browser tab whose title, process or URL the project's XAML in `<OUTPUT_DIR>` accounts for is a leftover of the failed run: close it by its ref from the latest snapshot, a tab ref for a tab, so a leaked tab inside the user's own browser window goes without touching that window.
   3. A new window or tab that no XAML property accounts for, for example one started by a script or command activity, is listed and left to the user.
   4. Any other new window is the user's, opened while the skill worked: never close it, never mention it.

   **Without a snapshot:**
   1. Before every rerun tell the user which applications and URLs the failed run drove, taken from the run log's `Audit: Using … App` lines, and ask them to close what it left open before confirming the rerun.
   2. The skill closes nothing itself and never lists processes.
3. **What the skill cannot restore.** A baseline window that is gone, or an application the project attaches to that is not running or not signed in, is something the skill cannot restore. Stop, tell the user what is missing, and rerun only after the user confirms it is back.

## Run

```bash
env -u UIPATH_STUDIO_PID uip rpa run --file-path "<MAIN>" --project-dir "<OUTPUT_DIR>" --output json > "<RUN_LOG>" 2>&1
```

1. Every `uip rpa` command in this skill runs with the host Studio pin cleared, `env -u UIPATH_STUDIO_PID`, as the blocks show; here it matters most. Inside Studio's integrated terminal that variable makes the rpa tool run the workflow in the user's Studio and open `<OUTPUT_DIR>` there first; a project other than the one already open replaces it and ends the terminal session. Cleared, the run goes to the headless Studio.
2. Never pass `--skip-build`. It assumes the headless Studio instance built the project itself; `uip rpa build` runs outside that instance, so the first run fails with "The Main.xaml workflow cannot be found".
3. Pass `--project-dir` with the same absolute spelling on every command in this guide. The headless Studio keys its instance on that string; another spelling starts a second instance.
4. The command blocks until the workflow completes or faults, however long that takes, and streams the workflow's log into `<RUN_LOG>` as `[Information] <message>` lines before the verdict JSON.
   - Run it in the background when the host supports that and wait for it to finish.
   - Without background execution, run it in the foreground with the longest timeout the host allows; a client killed by that timeout leaves the execution running (rule 7).
5. Progress while waiting:
   - `env -u UIPATH_STUDIO_PID uip rpa instances list --output json` lists the instance whose `ProjectDirectory` is `<OUTPUT_DIR>` (compare case-insensitively) with `ExecutionStatus: "ToolExecution"` while the run is in flight and `"Available"` once it ended.
   - The tail of `<RUN_LOG>` names the last logged step.
   - Wait for the host's completion notification when it provides one; otherwise check the tail of `<RUN_LOG>` and `instances list` no more than once a minute, and never loop on `sleep`.
   - Never probe with `debug break` or `debug continue`: both return `Success` with or without a session, and both block for the length of the current activity.
6. Never run this check with `debug start`. The debugger stops at every exception an activity throws, whether or not a Try Catch handles it, and holds the session, so a stopped session says nothing about whether the workflow fails. If a log ever shows `Suspended on exception`, cancel with rule 7 at once; that run is void and is repeated with `run`.
7. Stop the run only when the user asks or when the client was killed. Killing the client does not stop the execution; cancel it:

   ```bash
   env -u UIPATH_STUDIO_PID uip rpa execution cancel --project-dir "<OUTPUT_DIR>" --output json
   ```

   "Execution stop requested." means it was still running; "No Helm instance with a running execution found." means it had ended. Run this cancel once after every run whatever the outcome; it is harmless when nothing runs.
8. Repairs happen only through the fix and rerun loop below, one fix per run, each behind one yes/no. Outside the loop, do not edit the output, do not rework a selector, do not rerun.
9. Never run or validate the source project `<PROJECT_DIR>` through the headless Studio during the check or the loop. The migrator keeps the source's `projectId` on the output, and the host has been seen validating the migrated XAML when pointed at the source folder. The classic project's behavior is established by the user's own run of it, not by the skill.

## Verdict

Read `Data` by key presence; its shape varies with the CLI build. The outer `Result: "Success"` reports the CLI call, not the workflow. The duration is the `execution ended in: <hh:mm:ss>` log line.

| Outcome | Signal | Next |
|---|---|---|
| Passed | No errors (`HasErrors: false` or `errors: []`) and no exception (`ErrorMessage: null` or `output: "Session ended"`) | Report |
| Passed, not clean | The log reports that the healing agent recovered an activity: that activity's target did not resolve as migrated | The activity goes under Needs attention by name |
| Failed | `HasErrors: true` with an `ErrorMessage` whose lines `Source: <activity display name>`, `Message: <text>` and `Exception Type: <type>` name the failure; newer builds carry the same in `errors[]` with `output: "Execution aborted…"`. The log also names it, as `'<activity>' execution failed with exception <type>` | Attribution |
| Not a verdict: build failure | Compile errors at start: `Compile` log entries at `Error` level, or `errorName: "ERROR"` | Back to the fix loop of the build verification guide |
| Not a verdict: cancelled or killed | A run cancelled by the user or killed before any of the above | Yields only the last logged step |

## Attribution

For a failed run, take the failing activity and its file and look them up:

| Where it is | Verdict | What the report says |
|---|---|---|
| `uia.migratedItems` | migration-related | Selector carries the `.ToStringWithDelimiter()` marker: the post-migration fix guide is the fix. Otherwise quote the activity's `[PostMigration Action Required]` annotation, or the nearest ancestor's, with the exception |
| `uia.notMigrated` or `uia.partial` | not migration-related | Left classic by the tool; the exception is pre-existing or environmental |
| Neither, or no failing activity named | not migration-related | The exception as is |

- Several activities with that display name in the file: list them and say the run does not tell them apart.
- In fix-only mode there is no `<LEDGER>`: a failure at an activity that carried a marker or a `[PostMigration Action Required]` annotation is migration-related; anything else is reported without attribution.
- When the loop ends without a pass, applications the last run opened may still be open; say so.

## Fix and rerun loop

The loop runs only for a failure attributed to the migration; anything else is reported and the loop does not start. `<N>` counts the fixes applied so far.

1. Before proposing any fix:
   1. **Evidence.** Read the failing activity and its enclosing constructs in both projects: the classic form in `<PROJECT_DIR>` says what the workflow intended, its configuration and what the flow does next; the migrated form in `<OUTPUT_DIR>` and the tool's annotation say what the migration changed. The difference between the two is part of the evidence for every fix, alongside the exception and the annotation, and the fix restores the classic intent with modern constructs, never by reintroducing the classic activity.
   2. **Grounding.** Take the first source that applies:

      | Signal | Ground the fix on |
      |---|---|
      | (a) The failing activity's selector carries the marker | The post-migration fix guide's procedure, its scan, classification and confirmation included |
      | (b) A `[PostMigration Action Required]` annotation on the failing activity or on one of its ancestors names an action, such as moving the child outside the generated card or setting the target's Window selector | That action |
      | (c) Nothing grounded applies | One hypothesis formed from the evidence, which is the exception type and message, the tool's warning on the construct, and the difference between the classic activity in `<PROJECT_DIR>` and its migrated form in `<OUTPUT_DIR>`. A hypothesis is labelled as such in the question and in the report |

   3. **Limits.** Every fix, grounded or not, is a minimal targeted edit; it never invents or rewrites a selector value, never touches a marker selector, and never changes a package version.
   4. **Sources.** Facts a fix needs beyond the run's verdict and the two projects' files come only from the packages the project resolved: the versions in `<OUTPUT_DIR>/project.json` and the resolved set in `<OUTPUT_DIR>/.local/AllDependencies.json`, read under `%USERPROFILE%\.nuget\packages\<package>\<version>\`. Never another cached version, never a scan across versions. A text match inside a binary is a mention, not a definition; confirm a definition from the assembly's metadata or the source. When those sources do not answer, ask the user.
2. Ask one yes/no question: what will change, in which file and activity, and why it should remove this failure. Yes means apply and run again. No ends the loop; report.
3. Before editing a file, copy it to `<PROJECT_DIR>/.upgrade/runtime-fixes/<N>/<relative path>` (fix-only mode: `<MIGRATED_DIR>/.upgrade/runtime-fixes/<N>/<relative path>`). Apply the edit, validate the file with the build guide's validate command, rebuild with the build guide, restore the starting state, run again.
4. Read the new verdict:
   - Passed: the loop ends. Rewrite the `[PostMigration Action Required]` annotation of each construct a fix changed to `Remediated by uipath-activity-migrator on <date>: <what changed>`, the fix guide's convention, then validate and rebuild once more; this is part of the fix, not a Verified healthy rewrite. Report.
   - Failed in the same place, meaning same file, same activity display name and same exception type: the fix did not work. Ask one question with the options side by side: undo the fix and stop; undo the fix and apply the next one; keep the fix and apply the next one. The next fix is named in the option: the next grounded source, else a hypothesis different from the one that failed. Undo restores the backup, then validates and rebuilds. When no next fix exists, the only option is undo and stop, and the failure is reported as manual work.
   - Failed somewhere else: the fix stands; go back to step 1 for the new failure.
5. After 3 fixes, stop and ask whether to continue; each yes allows 3 more. The user's no ends the loop.

## Report

- The report block is the Runtime check block of the Step 6 template in SKILL.md.
- A run that passed first time is the one line `Passed in <duration>` and nothing else; a pass after the loop is `Passed on run <n> after <k> <fix or fixes>`.
- The workflow's own log output and observations about how the workflow behaves elsewhere, under a debugger for instance, are never report material.
- Fixes applied by the loop go under Fixes applied, each tagged with its fix number `<N>`, the backup folder's number, and its source: fix guide, annotation or hypothesis; the Remediated annotation belongs to that fix's line, and the "annotations rewritten to Verified healthy" line counts only the fix guide's healthy findings.
- Undone fixes are a count on the Runtime check line, never lines.
- When the run passed, drop the "run the main workflow once in Debug" next step; the Studio version line stays.
- Package-specific runtime prerequisites still come from each package guide's Hook 3.

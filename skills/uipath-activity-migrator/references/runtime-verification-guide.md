# Runtime Verification Guide

Step 6 of the workflow, after the build passed. One run of the migrated project, performed only after the user says yes, shows whether the output runs and attributes a failure to the migration or to something else. The build verification guide proves the output compiles; this guide is the only runtime evidence the skill produces.

## Offer

Offer the run when all of these hold: the build passed, `uip` is available, the routed packages are UIA only (a project routed to the Mail, GSuite or Microsoft.Activities guide gets no offer), and `project.json` has `"outputType": "Process"`; a library has nothing to run. Ask one yes/no question: run `<MAIN>` in `<OUTPUT_DIR>` once now, against the real applications on this machine? Default no. Do not propose durations or time limits. When `<MAIN>` declares `In` arguments without defaults, ask for their values in the same question or skip the run.

Placeholders: `<MAIN>` is the `main` entry of `project.json`. `<RUN_LOG>` is `<PROJECT_DIR>/.upgrade/run-latest.log`, or `<MIGRATED_DIR>/.upgrade/run-latest.log` in fix-only mode. `<LEDGER>` is the summarizer's `--json` output for the upgrade SARIF: `uia.migratedItems` lists every activity the tool rewrote, `uia.notMigrated` and `uia.partial` those it left classic.

## Run

```bash
uip rpa debug start --file-path "<MAIN>" --project-dir "<OUTPUT_DIR>" --output json > "<RUN_LOG>" 2>&1
```

1. Never pass `--skip-build`. It assumes the headless Studio instance built the project itself; `uip rpa build` runs outside that instance, so the first run fails with "The Main.xaml workflow cannot be found".
2. Pass `--project-dir` with the same absolute spelling on every command in this guide. The headless Studio keys its instance on that string; another spelling starts a second instance.
3. The command blocks until the workflow ends, however long that takes, and streams the workflow's log into `<RUN_LOG>` as `[Information] <message>` lines. Run it in the background when the host supports that and wait for it to finish. Without background execution, run it in the foreground with the longest timeout the host allows; a client killed by that timeout leaves the execution running (rule 5).
4. Progress while waiting: `uip rpa instances list --output json` lists the instance whose `ProjectDirectory` is `<OUTPUT_DIR>` (compare case-insensitively) with `ExecutionStatus: "ToolExecution"` while the run is in flight and `"Available"` once it ended; the tail of `<RUN_LOG>` names the last logged step. Never probe with `debug break` or `debug continue`: both return `Success` with or without a session, and both block for the length of the current activity.
5. Stop the run only when the user asks or when the client was killed. Killing the client does not stop the execution; cancel it:

   ```bash
   uip rpa execution cancel --project-dir "<OUTPUT_DIR>" --output json
   ```

   "Execution stop requested." means it was still running; "No Helm instance with a running execution found." means it had ended. Run this cancel once after every run whatever the outcome; it is harmless when nothing runs.
6. Observe, never repair. Do not edit the output, do not rework a selector, do not rerun with changes. The only fix path is the post-migration fix guide, and only for marker findings.

## Verdict

Read `Data` by key presence; its shape varies with the CLI build. Passed: no errors (`HasErrors: false` or `errors: []`) and no exception (`ErrorMessage: null` or `output: "Session ended"`). Failed: an exception, whose text starts with `Source: <activity display name>` or sits in `DebugDetails` as `Activity` and `WorkflowFile`. The outer `Result: "Success"` reports the CLI call, not the workflow. Two outcomes are not verdicts: compile errors at start (`Compile` log entries at `Error` level, or `errorName: "ERROR"`) are a build failure and go back to the fix loop of the build verification guide; a cancelled or killed run yields only the last logged step. The duration is the `execution ended in: <hh:mm:ss>` log line.

## Attribution

For a failed run, take the failing activity and its file and look them up:

| Where it is | Verdict | What the report says |
|---|---|---|
| `uia.migratedItems` | migration-related | Selector carries the `.ToStringWithDelimiter()` marker: run the post-migration fix guide. Otherwise quote the activity's `[PostMigration Action Required]` annotation with the exception |
| `uia.notMigrated` or `uia.partial` | not migration-related | Left classic by the tool; the exception is pre-existing or environmental |
| Neither, or no failing activity named | not migration-related | The exception as is |

Several activities with that display name in the file: list them and say the run does not tell them apart. In fix-only mode there is no `<LEDGER>`: a failure at an activity that carried a marker or a `[PostMigration Action Required]` annotation is migration-related; anything else is reported without attribution. Applications the run opened may still be open; say so when the run failed or was stopped.

## Report

The report block is the Runtime check block of the Step 6 template in SKILL.md. When the run passed, drop the "run the main workflow once in Debug" next step; the Studio version line stays. Package-specific runtime prerequisites still come from each package guide's Hook 3.

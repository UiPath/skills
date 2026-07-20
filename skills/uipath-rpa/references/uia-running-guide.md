# Running UI Automation Workflows

**Always use `uip rpa debug start`** (not `uip rpa run`) when running workflows with UI automation. A debug session pauses on error instead of tearing down the application, leaving the UI state available for inspection. The command returns as soon as that happens — `DebugState: "Suspended"` with the exception and locals in `DebugDetails` — so act on the response instead of waiting for the run to end (see [debugging.md § The stable-state debug loop](debugging.md#the-stable-state-debug-loop-headless)).

**Every debug run** must follow this procedure to prevent stale windows from accumulating or being reused in a dirty state:

1. **Record the window baseline** — list top-level windows via the UIA snapshot CLI and note which w-refs and titles are already present. Procedure: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/window-baseline-guide.md`.
2. **Run the workflow:**
   ```bash
   uip rpa debug start --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
   ```
   If the run fails, [Runtime Selector Failure Recovery](#runtime-selector-failure-recovery) spawns the `uia-improve-selector` subagent — this is the **only** correct recovery path. Do not hand-edit selectors in the XAML file.
3. **When done** (success or failure) — **cancel the debug session:**
   ```bash
   uip rpa execution cancel --project-dir "<PROJECT_DIR>" --output json
   ```
4. **List windows again** via the UIA snapshot CLI.
5. **Diff before vs after.** Any window present now that was NOT in the baseline was opened by the workflow. Close each such window via the `uip rpa uia interact` CLI (diff and close procedure: the window-baseline guide from step 1).

Skipping steps 4-5 causes the next run's open-if-not-open behavior to reuse a stale window in whatever state it was left in, or -- if the selector doesn't match -- to spawn a duplicate instance.

## Known failure — `Project build failed. Error code: 1` while `validate` and `build` pass

`uip rpa debug start` / `run` fails its internal "Compiling files" step with a bare `Project build failed. Error code: 1` (all log entries from `Compile`, no `CS####`, no file/line), while per-file `validate`, standalone `build`, and Studio all pass. `--skip-build` does not bypass it. The CLI output is opaque — read the real exception from `%LOCALAPPDATA%\UiPath\Logs\<date>_UiPath.Studio.log` (or `<date>_Execution.log`):

```
System.InvalidOperationException: The project contains C# source files but the JIT library produced no coded-workflow assembly
```

**Cause:** `{PROJECT_DIR}/.local/.codedworkflows/` exists in a project with **no coded workflow files** (no `.cs` with `[Workflow]`/`[TestCase]`). Headless `uip rpa` commands scaffold the folder, and Object Repository registration can leave only the generated `ObjectRepository.cs` descriptor surface in it — the run executor's JIT then detects C# sources, produces no coded-workflow assembly from them (a descriptor class is not a workflow), and aborts before any activity runs.

**Fix:**
1. Confirm the project has no coded workflow files: `grep -rl "\[Workflow\]\|\[TestCase\]" --include="*.cs" "<PROJECT_DIR>"` (excluding `.local/`) returns nothing.
2. Delete `{PROJECT_DIR}/.local/.codedworkflows/` and re-run. The folder is generated state; Studio regenerates it when a real coded surface exists.
3. Do NOT delete it in projects that have coded workflows — there it is required (see the package guide's Finding Descriptors section for regeneration).

Deleting authored XAML, variables, or `.objects/` data does NOT clear this failure — the trigger is the `.local/.codedworkflows/` folder, not workflow content.

## Advanced Debugging — Profiling

For advanced debugging, add `--profiling` to collect insightful per-activity execution data, timings, and before- and after-execution screenshots:

```bash
uip rpa debug start --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json --profiling
```

Use the before-execution screenshot to confirm the application/element started in the correct state, and the after-execution one to validate the expected outcome. Each screenshot's filename is recorded in the run's `.uistat` file; the image sits in the `Screenshots` folder in the same directory as that `.uistat` file. See [debugging.md § Profiling Workflow Performance](debugging.md#profiling-workflow-performance) for details.

## Runtime Selector Failure Recovery

"UI element not found", "UI element is invalid", element not on screen -- these surface at runtime, not during static validation. They occur when a selector was captured against one app state but the DOM changed by the time the activity executes.

When a workflow fails at runtime with a selector error:

1. **The app is already in the right state.** The debug session paused at the failing activity, so the app's current DOM reflects the state that activity needs to target.
2. **Identify the failing element** -- read the error to find which descriptor/element failed.
3. **Read the window selector** -- from the Object Repository files, find the screen's selector that scopes the failing element.
4. **Run the `uia-improve-selector` skill in recover mode.** Read `<PROJECT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-improve-selector/USAGE.md`, pick the appropriate invocation form for this context, run the staging CLI command from that form, spawn a subagent with the Agent tool to run the skill in recover mode against the staged folder, then run the write-back CLI command from the same form to persist the recovered selector.
5. **Clean up and re-run** -- follow the procedure above (stop, diff, close leaked windows, re-run).

Repeat until the workflow completes successfully. Each failure advances the app to the next problematic state, making recovery self-correcting.

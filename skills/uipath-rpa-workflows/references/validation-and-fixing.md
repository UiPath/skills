# Validation & Fixing (Phase 3 Details)

Detailed procedures for package resolution, dynamic types, debugging, iteration, and smoke testing.

## Package Error Resolution

```
Read: file_path="{projectRoot}/project.json"     -> check current dependencies

Bash: uip rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities"}]' --use-studio
```

Omit `version` to automatically resolve the latest compatible version (preferred — gets newest docs and features). Only pin a specific version when you have a reason to (e.g., known compatibility constraint).

**If `install-or-update-packages` fails:**
- **Package not found**: Verify the exact package ID — check spelling, use `uip rpa find-activities --use-studio` to discover the correct package name from an activity's assembly
- **Network/feed error**: The user may need to check their NuGet feed configuration in Studio settings

## Resolving Dynamic Activity Custom Types

Dynamic activities (e.g., Integration Service connectors) retrieved via `uip rpa get-default-activity-xaml --use-studio` (with `--activity-type-id`) may use **JIT-compiled custom types** for their input/output properties. After the activity is added to the workflow, when you need to discover the property names and CLR types of these custom entities (e.g., to populate an `Assign` activity targeting a custom type property, or to create a variable of a custom type), read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

## Focus Activity for Debugging

When `get-errors` returns an error referencing a specific activity (by IdRef or DisplayName), use `focus-activity` to highlight it in the Studio designer. This helps the user see the problematic activity in context and verify fixes visually:

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1" --use-studio

# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity --use-studio
```

This is especially useful when:
- An error references an activity and you want the user to confirm the context
- You've made a fix and want to show the user which activity was modified
- The error is ambiguous and you need to verify which activity instance is affected

## Iteration Loop

```
REPEAT:
  1. uip rpa get-errors --file-path "path/to/workflow.xaml" --output json --use-studio
  2. IF 0 errors (or errors cannot be resolved automatically) -> EXIT to Phase 4
  3. Identify highest-priority error category
  4. Apply appropriate fix
  5. (Optional) Focus the fixed activity: uip rpa focus-activity --activity-id "..." --use-studio
  6. GOTO 1

DO NOT stop until all activities are resolved (recognized).
DO NOT obsess on one error. If it can't be resolved, skip it, continue, and defer to an user action through an informative, step-by-step message at the end.
DO NOT skip validation steps.
DO NOT assume edits worked without checking.
DO NOT bundle multiple fixes in one iteration. Fix the root cause, re-run, verify. Never add a speculative change alongside the actual fix — changing two things at once makes it impossible to tell which one resolved the issue or whether the extra change introduced a new problem.
```

Expect multiple iteration cycles for complex workflows.

## Smoke Test (Optional but Recommended)

**Important:** `get-errors` (Studio validation) and `run-file` (runtime compilation) use different validation paths. Some errors — such as invalid enum values on activity properties — pass Studio validation but fail at runtime. Always treat the smoke test as a critical validation step, not just an optional extra.

After reaching 0 errors, optionally run the workflow to catch runtime errors (wrong credentials, missing files, logic bugs) that static validation cannot detect:

```bash
# Run with default arguments:
uip rpa run-file --file-path "Workflows/MyWorkflow.xaml" --output json --use-studio

# Run with input arguments:
uip rpa run-file --file-path "Workflows/MyWorkflow.xaml" --input-arguments '{"recipientEmail": "test@example.com", "subject": "Test"}' --output json --use-studio

# Run with verbose logging for debugging:
uip rpa run-file --file-path "Workflows/MyWorkflow.xaml" --log-level Verbose --output json --use-studio
```

**When to run:**
- The workflow has no compilation errors but you want to verify runtime behavior
- The workflow involves file I/O, API calls, or data transformations that could fail at runtime
- The user specifically asks to test the workflow

**When NOT to run:**
- The workflow has side effects (sends emails, modifies databases, calls external APIs) — warn the user first
- The workflow requires interactive input (UI automation, attended triggers)
- Compilation errors still exist (fix those first)

If `run-file` reveals runtime errors, analyze the output and loop back to fix them.

## Running UI Automation Workflows

**Always use `--command StartDebugging`** (not `StartExecution`) when running workflows with UI automation. A debug session pauses on error instead of tearing down the application, leaving the UI state available for inspection.

**Every debug run** must follow this procedure to prevent stale windows from accumulating or being reused in a dirty state:

1. **Record the window baseline:**
   ```bash
   servo targets
   ```
   Note which windows (w-refs and titles) are already present.
2. **Run the workflow:**
   ```bash
   uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command StartDebugging --output json --use-studio
   ```
3. **When done** (success or failure) — **stop the debug session:**
   ```bash
   uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command Stop --output json --use-studio
   ```
4. **List windows again:**
   ```bash
   servo targets
   ```
5. **Diff before vs after.** Any window present now that was NOT in the baseline was opened by the workflow. Close it:
   ```bash
   servo window <w-ref> Close
   ```

Skipping steps 4–5 causes the next run's `Open(IfNotOpen)` to reuse a stale window in whatever state it was left in, or — if the selector doesn't match — to spawn a duplicate instance.

## Runtime Selector Failures (UI Automation)

"UI element not found", "UI element is invalid", element not on screen — these surface at runtime, not during static validation. They occur when a selector was captured against one app state but the DOM changed by the time the activity executes (e.g., switching from round-trip to one-way re-renders the form, invalidating selectors for subsequent elements).

When a workflow fails at runtime with a selector error:
1. **The app is already in the right state.** The debug session paused at the failing activity, so the app's current DOM reflects the state that activity needs to target.
2. **Read the failing activity's current selector** from the XAML (the `FullSelectorArgument` or OR reference's selector).
3. **Read the window selector** from the ApplicationCard's TargetApp (the OR reference's scope selector, or the inline `ScopeSelectorArgument`).
4. **Run the `uia-improve-selector` skill in recover mode** by spawning a subagent with the Agent tool. The prompt must include: the `uia-improve-selector` SKILL.md path (find it under the UIA activity-docs skills folder), the project folder, `--mode recover`, `--window <windowSelector>`, and `--partial <failingPartialSelector>`. The subagent reads the skill, re-analyzes the live DOM in its current state, and returns a corrected selector.
5. **Update the OR element** with the recovered selector, or update the inline selector in the XAML.
6. **Clean up and re-run** — follow the "Running UI Automation Workflows" procedure above (stop, diff, close leaked windows, re-run).

Repeat until the workflow completes successfully. Each failure advances the app to the next problematic state, making recovery self-correcting.

# Running UI Automation Workflows

**Always use `--command StartDebugging`** (not `StartExecution`) when running workflows with UI automation. A debug session pauses on error instead of tearing down the application, leaving the UI state available for inspection.

**Every debug run** must follow this procedure to prevent stale windows from accumulating or being reused in a dirty state:

1. **Record the window baseline** — list top-level windows via `uip rpa uia snapshot inspect` and note which w-refs and titles are already present. Full flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.
2. **Run the workflow:**
   ```bash
   uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command StartDebugging --output json   ```
   If the run fails, [`uia-selector-recovery.md`](uia-selector-recovery.md) spawns the `uia-improve-selector` subagent — this is the **only** correct recovery path. Do not hand-edit selectors in the XAML file.
3. **When done** (success or failure) — **stop the debug session:**
   ```bash
   uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command Stop --output json   ```
4. **List windows again** via `uip rpa uia snapshot inspect`.
5. **Diff before vs after.** Any window present now that was NOT in the baseline was opened by the workflow. Close each such window via `uip rpa uia interact window` (see `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md` for the exact close-action flags).

Skipping steps 4-5 causes the next run's open-if-not-open behavior to reuse a stale window in whatever state it was left in, or -- if the selector doesn't match -- to spawn a duplicate instance.

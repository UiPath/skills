# Running UI Automation Workflows

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

Skipping steps 4-5 causes the next run's open-if-not-open behavior to reuse a stale window in whatever state it was left in, or -- if the selector doesn't match -- to spawn a duplicate instance.

If a selector error occurs during the debug run, see [uia-selector-recovery.md](uia-selector-recovery.md) for the recovery procedure.

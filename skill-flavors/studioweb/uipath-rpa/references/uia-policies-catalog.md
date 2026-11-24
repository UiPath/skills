<!--skill-flavor:window-cleanup:start-->
4. **Hand the cleanup to the user.** Studio Web has no UI Automation CLI, so this host cannot list windows, reset an app, or close a window. After a failed or cancelled run, tell the user which apps the workflow drove. Ask them to check each one and undo only what the run changed, using cancel, close without saving, or navigate back. They must not save, submit, or confirm anything. Windows and state that were already open before the run belong to the user and stay as they are.

Skipping this hand-off leaves the next run's open-if-not-open behavior to reuse a stale window in whatever state it was left in, or to spawn a duplicate instance if the selector does not match.
<!--skill-flavor:window-cleanup:end-->

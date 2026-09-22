# Final Resolution — Connection Not Resolved (DAP-GE-3000): Connection Deleted

## Summary

An Orchestrator unattended job (`TokenRefreshFailedJob`) in the Solution folder
`Shared/uipath-rpa-isActivities/TokenRefreshFailed_DAPRuntime` faulted with
Integration Service error **`DAP-GE-3000` (FailedToGetConnection)** —
*"Failed to retrieve connection. Consider using a different connection. -
Connection [989fd9d2-4b07-443e-86e3-ed6f1b00079b] is invalid or you do not have
access to it"* — at the ConnectorActivity **"Create Folder"** in `Main.xaml`.

## Root cause

The **Box** connection the process is bound to **no longer exists** — it was
**deleted**:

- The job's `ResourceOverwrites` binds the "Create Folder" activity to Box
  connection `989fd9d2-4b07-443e-86e3-ed6f1b00079b` in folder
  `b262689d-e2a9-4c1a-8e68-04382a7fff76`.
- `uip is connections ping 989fd9d2-...` returns **HTTP 404 — "Connection is
  invalid or you do not have access to it"** (the connection does not exist).
- `uip is connections list --folder-key b262689d-...` shows **only the Freshdesk
  connection** remains; the Box connection is gone.
- `uip is connections list` (tenant-wide) shows **zero Box connections** anywhere.

Integration Service resolves the bound connection before calling the provider;
because the connection ID points to a deleted connection, resolution fails with
`DAP-GE-3000` and the job never reaches Box.

This is distinct from a *disabled* connection (`DAP-GE-3005`): there the
connection still exists and can be re-authenticated. Here the connection is
**gone**, so re-authenticating the old ID is impossible — a new connection must
be created and the process re-bound to it.

## Evidence the root cause is correct (not just the symptom)

- Job `Info` and `jobs logs --level Error` both carry `DAP-GE-3000` with the
  inner `ConnectionHttpException` (HTTP at `ConnectionService.GetConnectionAsync`)
  — failure is at connection *resolution*, before any provider request.
- Ping of the bound connection returns **404**, not "disabled/Failed" — proving
  non-existence, not a disabled state.
- The bound folder no longer contains a Box connection, and no Box connection
  exists tenant-wide — corroborating deletion.

## Fix (create a new connection, then re-bind)

1. **Create a new Box connection** in the bound folder
   (`Shared/uipath-rpa-isActivities`, `b262689d-...`) using connector
   `uipath-box-box`, and authenticate it (OAuth). The new connection gets a
   **new connection ID** (the deleted ID `989fd9d2-...` cannot be revived).
2. **Re-bind** the "Create Folder" activity to the new connection and
   **republish** the process — the binding must point at the new connection's ID,
   otherwise the job keeps failing against the deleted ID.
3. Ensure the `TokenRefreshFailed_DAPRuntime` folder runs the newly published
   version.

**Verification (expected outcome):** after creating the new Box connection
(State `Enabled`, pings active) and re-binding + republishing, a re-run of
`TokenRefreshFailedJob` completes **Successfully** — the `DAP-GE-3000` error no
longer appears and the job resolves the new connection.

## Prevention

Avoid deleting connections that deployed processes depend on. If a connection
must be replaced, re-bind and republish dependent processes to the new
connection. For production, monitor connection existence/health so a removed
connection is caught before a scheduled run faults.

# Final Resolution — Connection Disabled (DAP-GE-3005) on Box "Create Folder"

## Summary

An Orchestrator unattended job (`TokenRefreshFailedJob`) in the Solution folder
`Shared/uipath-rpa-isActivities/TokenRefreshFailed_DAPRuntime` faulted with
Integration Service error **`DAP-GE-3005` (ConnectionDisabled)** —
*"Connection is disabled. Please enable the connection to continue."* — at the
ConnectorActivity **"Create Folder"** in `Main.xaml`.

> Note: the folder is *named* `TokenRefreshFailed_DAPRuntime`, but the actual
> emitted runtime code is `DAP-GE-3005` (ConnectionDisabled), **not**
> `DAP-GE-3004` (token refresh). The diagnosis must follow the emitted error
> code and connection state, not the folder label.

## Root cause

The **Box** connection bound to the failing activity was in a non-usable state:

- Connection: `989fd9d2-4b07-443e-86e3-ed6f1b00079b` (connector `uipath-box-box` /
  "Box"), account `original_email@test.com`,
  owner `replacement_email@test.com`, bound to folder
  `b262689d-e2a9-4c1a-8e68-04382a7fff76`.
- `uip is connections ping 989fd9d2-...` returned **Failure / ConnectionNotEnabled
  / status: `Failed`**.
- The connection list for the bound folder reported State **`Failed`** with the
  warning *"Connection(s) not enabled … Only Enabled connections can be used for
  operations."*

Integration Service resolves the connection **before** issuing the provider call;
finding it disabled/failed, it threw `DAP-GE-3005` and the job never reached Box.

The `Failed` state (rather than a plain manual disable) indicates the connection
was **auto-disabled following an OAuth re-authentication / token-refresh failure**.
This is the meaningful link to the folder's name: the underlying trigger was an
auth/token failure on the Box connection, which the runtime then surfaces as
"connection disabled."

## Evidence the root cause is correct (not just the symptom)

- Job `Info` and `jobs logs --level Error` both carry `DAP-GE-3005` with the
  stack `ConnectionService.GetConnectionAsync(...)` — failure is at connection
  resolution, before any provider request.
- `ResourceOverwrites` on the job binds the "Create Folder" activity to
  connection `989fd9d2-...` in folder `b262689d-...`.
- Ping of that exact connection returns `ConnectionNotEnabled` / `Failed`.
- Timeline rules out first-time misconfiguration: the same process ran
  **Successful at 08:07Z**, then faulted at **10:51Z** and **11:49Z** after the
  connection entered `Failed`.

## Fix (applied and verified)

Because the state was `Failed` (auth failure), re-enabling alone is insufficient —
the connection must be **re-authenticated**, otherwise it would fail again:

```
uip is connections edit 989fd9d2-4b07-443e-86e3-ed6f1b00079b
```

(or re-connect the Box connection in the Integration Service UI). If Box had
revoked the app authorization, re-authorize the UiPath app in the Box account
first, then re-authenticate.

**Verification (done by the user):**
- After re-authentication, `uip is connections ping 989fd9d2-...` returns
  **`Success / ConnectionPing`** (connection Enabled).
- The job was re-run and completed **Successful** (run `2524b63d-0730-4feb-9e5a-fc9a7f7a23f1`,
  2026-06-19T12:21:56Z → 12:22:02Z), confirming the fix.

## Prevention

For production connections, add connection health monitoring so OAuth token /
refresh expiry is caught before a scheduled run faults.

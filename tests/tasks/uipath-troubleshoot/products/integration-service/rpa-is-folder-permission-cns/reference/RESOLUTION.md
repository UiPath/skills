# Final Resolution

## Root Cause
The unattended `InvoiceSync` job faults because the **robot account does not
have the `Connections.View` permission on the `Shared/Finance` folder**
(folder key `7c9e1f22-5b3a-4d48-9e10-6a2b8c4d0e5f`) where the "Outlook - Finance Ops" Integration Service
connection (`8d2f4a6b-3c5e-4710-92a4-b6c8d0e2f4a6`) lives. Connection Service rejects the robot's token
fetch with **HTTP 403, error code `CNS1045`**, which the connector activity
surfaces as `DAP-GE-3000` at "Send Invoice Email". Studio runs succeed because
they execute under the developer's identity, which has the folder permission —
the robot account does not.

## Evidence the root cause is correct
- Job log error names the exact cause: *"The robot does not have the
  Connections.View permission in the folder where this connection lives"*,
  with the folder key `7c9e1f22-5b3a-4d48-9e10-6a2b8c4d0e5f` and `ErrorCode: CNS1045` (TraceId
  `7f3a9c1e5b2d48f6a0c4e8b2d6f0a3c5`).
- `uip is connections ping 8d2f4a6b-3c5e-4710-92a4-b6c8d0e2f4a6` returns **Success / Enabled** — the
  connection and its OAuth grant are healthy, ruling out expired
  authentication (`CNS1008`) and a deleted connection (404-class).
- The connection exists in `Shared/Finance`, not in the job's
  `Shared/Finance/InvoiceOps` folder — the failure is folder-permission
  scoping, not a missing connection.
- Debug-vs-unattended split: user identity works, robot identity fails —
  the signature of a robot-account folder-permission gap.

## Fix
1. In Orchestrator, open the **`Shared/Finance`** folder → Settings → Manage
   access, and grant the unattended robot account (the machine/robot running
   `InvoiceSync`) the **`Connections.View`** permission (via its role or a
   direct folder assignment).
2. Alternatively, move the "Outlook - Finance Ops" connection into a folder
   where the robot already holds `Connections.View`
   (e.g. `Shared/Finance/InvoiceOps`) and rebind if needed.
3. Re-run the job. No connection changes are required.

**Explicitly wrong fixes:** re-authenticating the connection (it is healthy —
`ping` succeeds), recreating the connection, or editing the workflow. The
failure is authorization on the robot's side, not the connection's state.

## Verification
After the grant, the next unattended run of `InvoiceSync` proceeds past
"Send Invoice Email" (the token fetch returns 200 instead of 403/CNS1045).

## Prevention
When deploying processes that use folder-scoped connections, verify the
executing robot account holds `Connections.View` on the folder that hosts
each referenced connection — debug success under a developer identity does
not prove the robot can resolve the connection.

# Final Resolution

## Root Cause

Confirmed Salesforce playbook cause:

> The Salesforce token was revoked or refresh policy, audience, environment, instance, or Run As identity is wrong.

The `LeadImport` job faults because the **"Salesforce - CRM" Integration
Service connection (`5a7b9c1d-2e4f-4608-a1b3-c5d7e9f0a2b4`) is no longer in an authorized state**: the
provider rejected the token refresh with `invalid_grant` ("expired
access/refresh token"), so Connection Service returns **HTTP 400, error code
`CNS1008`** on every token fetch, which the "Create Contact" connector
activity surfaces as `DAP-GE-3000`. The OAuth grant behind the connection
expired or was revoked (typically a password change, admin session
revocation, or provider-side token-lifetime policy) — which is why the job
ran fine for weeks and then failed with no workflow change.

The exact connector key is `uipath-salesforce-sfdc`, so the diagnosis must use
the Salesforce authentication branch after the common Connection Service
signal. `CNS1008`, `invalid_grant`, the failed connection state, and prior
successful runs isolate the revoked/expired grant branch; they do not prove an
audience, environment, instance, Run As, app-approval, API-permission, or
workflow-input defect.

## Evidence the root cause is correct
- Job log error: *"Connection [5a7b9c1d-2e4f-4608-a1b3-c5d7e9f0a2b4] is not in an authorized state.
  Please re-authenticate the connection to continue."* with
  `ErrorCode: CNS1008` and the provider's `invalid_grant` detail (TraceId
  `3c5e7a9b1d2f46a8c0b2d4f6a8c0e1b3`).
- `uip is connections list` shows the connection in **State: Failed**.
- `uip is connections ping 5a7b9c1d-2e4f-4608-a1b3-c5d7e9f0a2b4` fails with HTTP 400 / `CNS1008` and the
  CLI itself instructs re-authentication.
- The connection exists in the job's folder and the robot resolved it (400,
  not 403/404) — permissions and connection location are NOT the problem.

## Fix
1. Have the connection owner (`crm.admin@acmecorp.test`) **re-authenticate**
   the "Salesforce - CRM" connection: Integration Service → Connections →
   reconnect, or `uip is connections edit 5a7b9c1d-2e4f-4608-a1b3-c5d7e9f0a2b4`.
2. If Salesforce rejects the new authorization, have a Salesforce admin check
   the connected/external app and refresh-token policy for this principal;
   do not broaden API/object permissions because the failure occurs during
   token refresh before an object operation.
3. Confirm the connection returns to **Enabled** (ping succeeds).
4. Re-run the `LeadImport` job.

**Explicitly wrong fixes:** recreating/deleting the connection (unnecessary —
re-auth restores it and preserves bindings), granting folder permissions
(the robot already resolves the connection), or editing the workflow.

## Verification
After re-authentication, `uip is connections ping 5a7b9c1d-2e4f-4608-a1b3-c5d7e9f0a2b4` returns Success /
Enabled and the next run proceeds past "Create Contact".

## Prevention
Watch for connections drifting to `Failed` state after provider-side
credential events (password rotations, admin revocations). A connection that
"worked for weeks" and fails with `CNS1008`/`invalid_grant` always needs
re-authentication by its owner, not reconfiguration.

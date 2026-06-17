# Tenant Operations Troubleshooting

Diagnostic workflows for async tenant lifecycle operations and service provisioning issues.

## Playbook 11: Tenant Operation Stuck or Failed

**Symptom:** `tenants create`, `update`, `delete`, `enable`, or `disable` returned an `operationId` but the operation has not reached a terminal state.

1. Poll the operation:
   ```bash
   uip admin organizations operation get "<OPERATION_ID>" --output json
   ```

2. Interpret the status:
   - **`Pending` / `Running` / `InProgress`** → still in progress. Auto-poll 3x at 5-second intervals (Rule 18). If still non-terminal after 3 polls, present options to user (wait longer, retry, escalate) — never loop indefinitely.
   - **`Succeeded`** → operation completed. Verify the result:
     ```bash
     uip admin tenants get "<TENANT_ID>" --output json
     ```
   - **`Failed`** → inspect `Data.error` and `Data.message` in the response for the failure reason
   - **`Cancelled`** → operation was cancelled server-side; may need to retry

3. Common failure causes:
   - **Region unavailable** → the requested region may be at capacity or not support the required services. Try a different region: `uip admin organizations regions list --output json`
   - **Required services not available** → some services are region-specific. Check available catalog: `uip admin tenants services list-available --region "<REGION>" --output json`
   - **Backend timeout** → transient infrastructure issue. Retry the operation.
   - **Quota exceeded** → org has hit the maximum tenant count. Contact support.

4. Do NOT auto-retry failed mutations — present the error to the user and let them decide.

## Playbook 12: Service Provisioning No-Op

**Symptom:** `tenants services disable` or `remove` returned Success but the service is still showing as Enabled.

1. Verify current state:
   ```bash
   uip admin tenants services list --tenant-id "<TENANT_ID>" --output json
   ```

2. Check if the service is platform-pinned. These services return Success on `disable`/`remove` but the state never changes — this is a known CLI behavior, not an error:
   - Orchestrator
   - Maestro
   - Connections (Integration Service)
   - Data Service (Data Fabric)
   - Insights
   - Test Manager

3. For platform-pinned services: CLI cannot disable/remove them. Redirect user to the UiPath Portal for management of these core services.

4. For non-pinned services: if state didn't change despite Success response:
   - Check if the operation is async — some service mutations return `operationId`:
     ```bash
     uip admin organizations operation get "<OPERATION_ID>" --output json
     ```
   - Re-list to verify: `tenants services list --tenant-id "<TENANT_ID>" --output json`
   - The service may have dependencies preventing removal. Check if other services depend on it.

5. Always re-list after any service mutation (Rule 22) — do not trust the Success response alone.

# Running and Monitoring Maestro Processes

Guide for finding deployed processes, running them, and monitoring job execution.

## Find the Deployed Process

After a successful deployment, locate the folder and process.

### Step 1: Find the Folder

List folders and find the one matching your project:

```bash
uip or folders list --filter "contains(FullyQualifiedName, '<projectName>_folder')" --output json
```

**Record from the response:**
- `Key` — Folder GUID (used as `folderKey`)
- `Id` — Folder numeric ID

### Step 2: List Processes

List Maestro processes in the folder (`--folder-key` is **required**):

```bash
uip maestro process list --folder-key "<folderKey>" --output json
```

**Record from the response:**
- `processKey` — Process GUID
- `releaseKey` — Release GUID
- `folderKey` — Folder GUID

**Note:** If the process is not found immediately after deployment, wait a few seconds and re-list — deployment activation may take a moment.

## Run a Maestro Process

Execute the process using the keys from the previous step:

```bash
uip maestro process run "<processKey>" "<folderKey>" \
  --release-key "<releaseKey>" \
  --output json
```

**Record from the response:**
- `jobKey` — Job GUID (used for monitoring)

### Pre-run Checklist

Before running, verify:
- Deployment status is `DeploymentSucceeded` / `SuccessfulInstall` / `SuccessfulActivate`
- The process appears in `maestro process list`
- The user has explicitly consented to execution (Maestro jobs run real automations)

## Monitor Job Execution

### Option 1: Stream Traces (Preferred)

```bash
uip maestro job traces "<jobKey>" --output json
```

Traces provide real-time execution details. However, they may fail or be unavailable for some jobs.

### Option 2: Poll Job Status (Fallback)

If traces are unavailable, poll the job status. The `--folder-key` is **required**:

```bash
uip maestro job status "<jobKey>" --folder-key "<folderKey>" --output json
```

### Understanding Job Status Response

The response has two levels:
1. **Outer `Result`** — Whether the API call itself succeeded (`"Success"`)
2. **Inner `Data.state`** — The actual job execution state

**Always check `Data.state`**, not the outer `Result`.

### Job States

| State | Meaning | Action |
|-------|---------|--------|
| `Successful` | Job completed successfully | Report `startTime`, `endTime`, and duration |
| `Faulted` | Job failed | Report error from `Data.info` |
| `Pending` | Job queued, not started | Wait 10-15 seconds and poll again |
| `Running` | Job in progress | Wait 10-15 seconds and poll again |

### Polling Strategy

- Poll interval: 10-15 seconds
- Maestro jobs with gateways may take longer than simple flows
- If a job stays in `Pending` or `Running` for more than 5 minutes, warn the user

### Handling Faulted Jobs

When a job enters the `Faulted` state:

1. Check `Data.info` for the error message
2. Suggest checking traces for additional details: `uip maestro job traces "<jobKey>"`
3. Common causes:
   - Missing robot or unattended license
   - BPMN definition errors
   - Gateway configuration issues
   - Downstream process failures

## Complete Monitoring Example

```bash
# Run the process
uip maestro process run "<processKey>" "<folderKey>" \
  --release-key "<releaseKey>" \
  --output json

# Try traces first
uip maestro job traces "<jobKey>" --output json

# If traces fail, poll status
uip maestro job status "<jobKey>" --folder-key "<folderKey>" --output json

# If still running, wait and poll again
sleep 15
uip maestro job status "<jobKey>" --folder-key "<folderKey>" --output json
```

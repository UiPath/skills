# Orchestrator Eval Schedules

Create, manage, and replace scheduled evaluation runs for low-code agents published as Orchestrator packages.

Use eval schedules to run evaluations on a recurring cron basis against a published package. The schedule triggers the eval set automatically — no manual `run-offline-evals` invocation needed. For ad-hoc runs, see [orchestrator-eval-run.md](orchestrator-eval-run.md).

## Prerequisites

- The agent package must be published to Orchestrator (via `uip solution deploy` or Studio)
- The eval set must exist for the workload and process key
- You need the `ORCHESTRATOR.JOBS.CREATE` permission on the target folder

## Create a Schedule

```bash
uip or eval schedule create \
  --process-key <deployment-guid> \
  --workload-id <workload-guid> \
  --eval-set-id <eval-set-guid> \
  --folder-key <folder-guid> \
  --cron "<five-field-cron>" \
  [--tenant <tenant-name>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (deployment GUID) — identifies the Orchestrator release |
| `--workload-id` | Yes | Workload ID (GUID) — the agent/process workload to evaluate |
| `--eval-set-id` | Yes | Eval set ID (GUID) — the evaluation set to run on each trigger |
| `--folder-key` | Yes | Orchestrator folder key (GUID). Use `uip or folders list` to find keys |
| `--cron` | Yes | Five-field cron expression in UTC (e.g. `"0 9 * * *"` for daily at 9 AM) |
| `--tenant` | No | UiPath tenant name |

### Example

```bash
uip or eval schedule create \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --workload-id "a1b2c3d4-0000-0000-0000-000000000001" \
  --eval-set-id "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04" \
  --folder-key "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e" \
  --cron "0 9 * * *" \
  --output json
```

### Output

```json
{
  "Result": "Success",
  "Code": "EvalScheduleCreated",
  "Data": {
    "ScheduleId": "b2c3d4e5-0000-0000-0000-000000000001",
    "WorkloadId": "a1b2c3d4-0000-0000-0000-000000000001",
    "ProcessKey": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
    "FolderKey": "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e",
    "EvalSetId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04",
    "CronExpression": "0 9 * * *",
    "Status": "active",
    "CreatedAt": "2026-08-01T10:00:00Z"
  }
}
```

## List Schedules

```bash
uip or eval schedule list \
  --process-key <deployment-guid> \
  [--tenant <tenant-name>] \
  --output json
```

Returns all non-deleted schedules for the process key that you have folder access to.

### Output

```json
{
  "Result": "Success",
  "Code": "EvalScheduleList",
  "Data": [
    {
      "ScheduleId": "b2c3d4e5-0000-0000-0000-000000000001",
      "WorkloadId": "a1b2c3d4-0000-0000-0000-000000000001",
      "ProcessKey": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
      "FolderKey": "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e",
      "EvalSetId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04",
      "CronExpression": "0 9 * * *",
      "Status": "active",
      "CreatedAt": "2026-08-01T10:00:00Z"
    }
  ]
}
```

## Get Schedule Details

```bash
uip or eval schedule get <schedule-id> \
  --process-key <deployment-guid> \
  [--tenant <tenant-name>] \
  --output json
```

### Output

```json
{
  "Result": "Success",
  "Code": "EvalScheduleDetails",
  "Data": {
    "ScheduleId": "b2c3d4e5-0000-0000-0000-000000000001",
    "WorkloadId": "a1b2c3d4-0000-0000-0000-000000000001",
    "ProcessKey": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
    "FolderKey": "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e",
    "EvalSetId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04",
    "CronExpression": "0 9 * * *",
    "Status": "active",
    "CreatedAt": "2026-08-01T10:00:00Z",
    "UpdatedAt": "2026-08-01T12:00:00Z"
  }
}
```

`UpdatedAt` is included only if the schedule has been updated.

## Update (Replace) a Schedule

Update the cron expression, eval set, or both on an existing schedule:

```bash
uip or eval schedule update <schedule-id> \
  --process-key <deployment-guid> \
  [--eval-set-id <new-eval-set-guid>] \
  [--cron "<new-cron-expression>"] \
  [--folder-key <guid>] \
  [--tenant <tenant-name>] \
  --output json
```

At least one of `--eval-set-id` or `--cron` must be provided. The folder key is immutable after creation — `--folder-key` must match the original value.

### Example — replace the eval set on an existing schedule

```bash
uip or eval schedule update "b2c3d4e5-0000-0000-0000-000000000001" \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --eval-set-id "aaaabbbb-cccc-dddd-eeee-ffffffffffff" \
  --output json
```

### Example — change cron to run every 6 hours

```bash
uip or eval schedule update "b2c3d4e5-0000-0000-0000-000000000001" \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --cron "0 */6 * * *" \
  --output json
```

### Output

```json
{
  "Result": "Success",
  "Code": "EvalScheduleUpdated",
  "Data": {
    "ScheduleId": "b2c3d4e5-0000-0000-0000-000000000001",
    "WorkloadId": "a1b2c3d4-0000-0000-0000-000000000001",
    "ProcessKey": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
    "FolderKey": "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e",
    "EvalSetId": "aaaabbbb-cccc-dddd-eeee-ffffffffffff",
    "CronExpression": "0 */6 * * *",
    "Status": "active",
    "CreatedAt": "2026-08-01T10:00:00Z",
    "UpdatedAt": "2026-08-02T14:00:00Z"
  }
}
```

## Pause a Schedule

```bash
uip or eval schedule pause <schedule-id> \
  --process-key <deployment-guid> \
  [--tenant <tenant-name>] \
  --output json
```

Pauses the Temporal cron schedule. The schedule retains its configuration and can be resumed later.

### Output

```json
{
  "Result": "Success",
  "Code": "EvalSchedulePaused",
  "Data": {
    "ScheduleId": "b2c3d4e5-0000-0000-0000-000000000001",
    "Status": "paused"
  }
}
```

## Resume a Schedule

```bash
uip or eval schedule resume <schedule-id> \
  --process-key <deployment-guid> \
  [--tenant <tenant-name>] \
  --output json
```

### Output

```json
{
  "Result": "Success",
  "Code": "EvalScheduleResumed",
  "Data": {
    "ScheduleId": "b2c3d4e5-0000-0000-0000-000000000001",
    "Status": "active"
  }
}
```

## Delete a Schedule

```bash
uip or eval schedule delete <schedule-id> \
  --process-key <deployment-guid> \
  [--tenant <tenant-name>] \
  --output json
```

Permanently removes the schedule and its Temporal cron. This cannot be undone.

### Output

```json
{
  "Result": "Success",
  "Code": "EvalScheduleDeleted",
  "Data": {
    "ScheduleId": "b2c3d4e5-0000-0000-0000-000000000001"
  }
}

## Typical Workflow — Create and Replace

1. **Create** an initial eval schedule:

   ```bash
   uip or eval schedule create \
     --process-key "$PROCESS_KEY" \
     --workload-id "$WORKLOAD_ID" \
     --eval-set-id "$EVAL_SET_ID" \
     --folder-key "$FOLDER_KEY" \
     --cron "0 9 * * 1" \
     --output json
   ```

2. **Run ad-hoc** to validate immediately (uses the runtime eval command):

   ```bash
   uip or eval run-offline-evals \
     --process-key "$PROCESS_KEY" \
     --items '[{"input": "hello"}]' \
     --evaluators '[{"id": "ev-1", "evaluatorTypeId": "5", "evaluatorConfig": {}}]' \
     --output json
   ```

3. **Check results** by process key:

   ```bash
   # List all eval set runs for this process
   uip or eval run list --process-key "$PROCESS_KEY" --output json

   # Get details + per-item results for a specific run
   uip or eval run get "$EVAL_SET_RUN_ID" --process-key "$PROCESS_KEY" --output json
   uip or eval run results "$EVAL_SET_RUN_ID" --process-key "$PROCESS_KEY" --output json
   ```

4. **Replace** the eval set when test cases change:

   ```bash
   uip or eval schedule update "$SCHEDULE_ID" \
     --process-key "$PROCESS_KEY" \
     --eval-set-id "$NEW_EVAL_SET_ID" \
     --output json
   ```

5. **Delete** and recreate when the process key changes (new deployment):

   ```bash
   uip or eval schedule delete "$OLD_SCHEDULE_ID" \
     --process-key "$OLD_PROCESS_KEY" \
     --output json

   uip or eval schedule create \
     --process-key "$NEW_PROCESS_KEY" \
     --workload-id "$WORKLOAD_ID" \
     --eval-set-id "$EVAL_SET_ID" \
     --folder-key "$FOLDER_KEY" \
     --cron "0 9 * * 1" \
     --output json
   ```

## Cron Expression Format

Five-field UTC cron (minute, hour, day-of-month, month, day-of-week):

| Pattern | Meaning |
|---------|---------|
| `0 9 * * *` | Daily at 9:00 AM UTC |
| `0 */6 * * *` | Every 6 hours |
| `0 9 * * 1` | Every Monday at 9:00 AM UTC |
| `30 2 1 * *` | 1st of every month at 2:30 AM UTC |

Special characters `#` and `?` are not supported. Month names (`JAN`–`DEC`) and day names (`SUN`–`SAT`) are allowed.

## Schedule Statuses

| Status | Meaning |
|--------|---------|
| `active` | Schedule is running on its cron |
| `paused` | Schedule is suspended; use `resume` to reactivate |
| `deleted` | Schedule has been permanently removed (not returned by `list`) |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Auth expired | Run `uip login` |
| `404 Not Found` | Schedule or eval set not found for the given process key | Verify IDs with `uip or eval schedule list` |
| `CronExpression must be a valid five-field cron expression` | Invalid cron syntax | Use standard 5-field format, no `#` or `?` |
| `ExecutionConfig.ProcessKey must match the route processKey` | Mismatched process key | Ensure `--process-key` is consistent |
| `FolderKey is immutable after schedule creation` | Tried to change folder via update | Delete and recreate the schedule with the new folder |
| `Eval set not found for workload` | Eval set doesn't belong to this workload/process | Verify eval set ownership |

## Anti-patterns

- **Don't create duplicate schedules for the same eval set.** Each schedule triggers independently; duplicate schedules waste compute and produce confusing results.
- **Don't forget to update the schedule when you publish a new eval set.** The schedule runs the eval set ID it was created with. If you create a new eval set, update the schedule to point to it.
- **Don't use sub-minute intervals.** The cron expression supports minute granularity; more frequent runs will be rejected.

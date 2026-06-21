# Wait-for-Connector Condition — Planning

## When to Use

- Stage or task should activate when an **external connector event** fires (email received, Teams message, webhook, etc.)
- The condition waits for a specific Integration Service event rather than a task or stage completion
- Common for ExceptionStages that activate on external signals (customer responds via email, support ticket updated, etc.)

## Spec Recognition

Look for phrases like:
- "Wait for email from customer"
- "Activate when Teams message received"
- "Triggered by webhook"
- "Listen for Outlook event"
- "Wait for connector event"

## Planning Output Format

```
## T80: Add stage entry condition for "Pending with customer" — wait for Teams message
- rule-type: wait-for-connector
- connector-key: uipath-microsoft-teams
- operation: NEW_MESSAGE_IN_CHANNEL
- connection-name: <connection name from spec or registry>
- isInterrupting: true
- order: after T79
- verify: Confirm Result: Success
```

## Required Information from Spec

| Field | Source |
|-------|--------|
| `connector-key` | The Integration Service connector (e.g., `uipath-microsoft-teams`, `uipath-microsoft-outlook365`) |
| `operation` | The specific event to listen for (e.g., `NEW_MESSAGE_IN_CHANNEL`, `MAIL_RECEIVED`) |
| `connection-name` | The connection name configured in Integration Service |
| `isInterrupting` | Whether this entry should interrupt the current stage (typically `true` for exception handling) |

## Registry Lookup

During planning, use:

```bash
uip case registry get-connector --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json

uip case registry get-connection --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Record in `registry-resolved.json`:
- `uiPathActivityTypeId` (the trigger type ID)
- `connectionId` (from `Connections[]` in get-connection response)
- `folderKey` (from the connection)
- `objectName` (from the trigger metadata)

## Condition Scopes

`wait-for-connector` can appear in:

| Scope | Location | Common use |
|-------|----------|------------|
| Stage entry | `stage.data.entryConditions[]` | ExceptionStage activated by external event |
| Task entry | `task.entryConditions[]` | Task waits for external signal before starting |
| Stage exit | `stage.data.exitConditions[]` | Stage exits when external event fires |

## Implementation Reference

See [impl.md](impl.md) for the full JSON schema and CLI enrichment steps.

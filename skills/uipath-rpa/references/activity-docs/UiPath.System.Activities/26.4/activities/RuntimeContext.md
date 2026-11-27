# Manual Trigger

`UiPath.Core.Activities.ManualTrigger`

Contains job info such as Process name, Workflow name, User Name, User Email and Timestamp.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Get Current Job Info | `OutArgument` | `CurrentJobInfo` | An object containing runtime information about the current job, including process name, process version, workflow name, robot name, folder name, user email, and execution mode. |

## XAML Example

```xml
<ui:ManualTrigger
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Manual Trigger"
    Result="{x:Reference jobInfo}" />
```

## Notes

- **Type: integration trigger.** `uip rpa activities find` returns `isTrigger: true, triggerType: "integration"` (the event source is the user clicking "Run" in Orchestrator or Assistant — categorized with the other Orchestrator-managed triggers even though no external system is involved). No `ConnectionId` required.
- **Placement: strict.** Place `Manual Trigger` as the first activity in the workflow's root `Sequence`. Do **NOT** wrap in `ui:TriggerScope`. The handler — the work to execute on each manual start — is the rest of the `Sequence` that follows.
- See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md) for the full placement contract.
- The trigger fires when a user manually starts the associated process from Orchestrator or the UiPath Assistant.
- `ManualTrigger` inherits from `GetCurrentJobInfo` — the `Result` output is identical to the one produced by the **Get Current Job Info** activity.
- No scheduling or queue configuration is required.

# Re-sync Solution Project

`UiPath.Pipelines.Activities.ResyncSolutionProject`

Re-syncs a solution project with Orchestrator. Note: Components may be removed if they are no longer available in the source.

Calls the Solutions API to synchronize the specified project, then polls the sync status until a terminal state is reached. The `SolutionSyncOption` controls which properties are updated.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionProjectName` | Solution project name | `InArgument` | `string` | Yes | — | — | Name of the solution project to be synced. |
| `SolutionSyncOption` | Sync option | `InArgument` | `SolutionProjectSyncOption` | No | `Sync` | — | Controls which properties to sync. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## SolutionProjectSyncOption Enum

| Value | Display Name | Description |
|-------|-------------|-------------|
| `Sync` (0) | Read-only properties | Syncs read-only properties to source value. Configurable properties are not updated. |
| `Reset` (1) | All properties | Syncs all properties to source value. Existing edits are overridden. |

## XAML Example

```xml
<pip:ResyncSolutionProject
    Tenant="[tenant]"
    SolutionProjectName="MySolutionProject"
    SolutionSyncOption="{x:Static pip:SolutionProjectSyncOption.Sync}"
    DisplayName="Re-sync Solution Project" />
```

## Notes

- `Tenant` and `SolutionProjectName` are required.
- `SolutionSyncOption` defaults to `Sync` (read-only properties only).
- Throws `SolutionProjectSyncException` if sync fails or if polling times out with `InProgress` status.
- Deleted source components may be removed from Orchestrator during re-sync.
- Inherits from `BaseSolutionsActivity`.

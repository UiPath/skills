# Stage

`UiPath.Pipelines.Activities.Stage`

Container activity for reporting pipeline stage status to Automation Ops - Pipelines.

`Stage` wraps its child activity body in a `TryCatch`. On success it calls `EndStage` (reporting success telemetry to AutomationOps); on failure it calls `ErrorStage` (reporting the error) and then re-throws the exception. This makes pipeline stage execution visible in the AutomationOps Pipelines dashboard.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Body

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Activities` | Activities | `ActivityDelegate` | The activities to execute inside this stage. Drop activities here. |

> `Stage` does **not** inherit from `CicdBaseActivity` — it inherits directly from `Activity`. It has no `ContinueOnError`, `TimeoutMS`, or `Tenant` arguments of its own; those are handled by the individual activities inside it.

## XAML Example

```xml
<pip:Stage DisplayName="Build Stage">
    <pip:Stage.Activities>
        <ActivityAction>
            <ActivityAction.Handler>
                <Sequence>
                    <pip:Clone RepoUrl="[repoUrl]" RepositoryPath="[repoPath]" />
                    <pip:Build RepositoryPath="[repoPath]" PackagePath="[packagePath]" />
                </Sequence>
            </ActivityAction.Handler>
        </ActivityAction>
    </pip:Stage.Activities>
</pip:Stage>
```

## Notes

- `Stage` is a `sealed` class; it cannot be subclassed.
- Stage lifecycle events (`StartStage`, `EndStage`, `ErrorStage`) are reported automatically to the AutomationOps service and appear on the Automation Ops - Pipelines dashboard.
- If any child activity throws, `ErrorStage` is called with the exception and the exception is re-thrown. The `Stage` activity itself does not swallow errors.
- Nesting `Stage` activities is not recommended; each `Stage` represents a discrete named pipeline step.

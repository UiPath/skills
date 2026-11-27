# Workflow Placeholder

`UiPath.Core.Activities.Placeholder`

Adds a placeholder into the workflow.

**Package:** `UiPath.System.Activities`
**Category:** Workflow.Control

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Description` | Description | `string` | *(localised initial value)* | A free-text label describing what should be implemented here. Displayed as a multiline text block in the designer. |

## XAML Example

```xml
<ui:Placeholder DisplayName="Workflow Placeholder"
    Description="TODO: implement this step"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

`Placeholder` must be placed inside a `Sequence`. A validation error is raised if the direct parent is not a `Sequence`.

At runtime the activity logs an informational message indicating that the placeholder was executed and then completes successfully without doing any work. It is intended as a design-time marker for steps that have not yet been implemented.

The `Description` property is not mapped to a workflow argument — it is a plain string property stored directly on the activity.

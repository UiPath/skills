# Comment

`UiPath.Core.Activities.Comment`

Adds a comment into the workflow.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Text` | Text | `string` | — | The comment text displayed on the activity in the designer canvas. |

## XAML Example

```xml
<ui:Comment
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Comment"
    Text="This section handles the invoice extraction logic." />
```

## Notes

- **Comment** is a design-time annotation activity. It executes at runtime (it is a `CodeActivity`) but performs no meaningful operation — its sole purpose is to surface the `Text` note on the designer canvas.
- The `Text` property is a plain `string`, not an `InArgument`, so it does not support VB/C# expressions; only literal text is accepted.
- Use `Comment` to document intent, assumptions, or maintenance notes directly inside a workflow without affecting execution.

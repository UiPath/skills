# Disabled Activities

`UiPath.Core.Activities.CommentOut`

A container where you can add activities that won't be executed at runtime.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

This activity has no configurable input or output properties. All activities placed inside the container are silently skipped at runtime.

## XAML Example

```xml
<ui:CommentOut
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Disabled Activities">
  <ui:CommentOut.Body>
    <Sequence DisplayName="Ignored activities">
      <!-- Disabled activities go here -->
    </Sequence>
  </ui:CommentOut.Body>
</ui:CommentOut>
```

## Notes

- Activities placed inside `CommentOut` are serialized in XAML but the `Execute` method does nothing — the body is never executed.
- Use this activity to temporarily disable a block of logic without deleting it, similar to commenting out code.

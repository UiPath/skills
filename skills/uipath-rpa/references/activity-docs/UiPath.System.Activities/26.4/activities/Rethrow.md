# Rethrow

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.Rethrow`

Re-raises the exception currently being handled by an enclosing `TryCatch.Catch`. Preserves the original stack trace.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

`Rethrow` exposes no input, output, or configuration properties.

## XAML Example

```xml
<Rethrow xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
         DisplayName="Rethrow" />
```

## Notes

- **`Rethrow` is only valid inside a `Catch.Action` body** (anywhere down the activity tree, not necessarily a direct child). Using it outside a `Catch` raises a runtime `InvalidOperationException`.
- Use `Rethrow` to preserve the original exception's stack trace after side-effect work in the `Catch` body (logging, cleanup, partial rollback). Use `Throw new <Type>(...)` instead when you want to translate the exception to a different type.
- `Rethrow` does not need to be the last activity in a `Catch` body — anything after it is unreachable, but Studio's validator does not flag this. Place `Rethrow` last.
- `activities get-default-xaml` for `Rethrow` returns `<Rethrow />` (already correct — no properties exist).
- `Rethrow` is a leaf activity. Its parent `Catch.Action` body must be `<Sequence>`-wrapped per Rule 24.

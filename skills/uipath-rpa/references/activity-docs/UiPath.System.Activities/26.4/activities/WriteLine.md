# Write Line

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.WriteLine`

Writes a text expression to a text writer, followed by a newline. Defaults to writing to `Console.Out`, which appears in the Studio Output panel and in `uip rpa run` stdout.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | No | empty string | The text to write. |
| `TextWriter` | Text Writer | `InArgument` | `TextWriter` | No | `Console.Out` | The target writer. Almost never set explicitly — the default is correct for both Studio and `uip rpa run`. |

## XAML Example

```xml
<WriteLine xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
           xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
           DisplayName="Write Line">
  <WriteLine.Text>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="$&quot;processed {count} items&quot;" />
    </InArgument>
  </WriteLine.Text>
</WriteLine>
```

## Notes

- Prefer `LogMessage` over `WriteLine` for any output that must be visible in Orchestrator. `WriteLine` writes only to the local stdout; `LogMessage` also publishes to the Orchestrator logs page.
- Do **not** set `TextWriter` unless the workflow legitimately needs to write somewhere other than stdout (e.g., a custom file stream). The default is correct for every Studio and runner context.
- For C# XAML projects, use `<CSharpValue x:TypeArguments="x:String">...</CSharpValue>` inside the `InArgument`; do not use VB bracket shorthand.
- `activities get-default-xaml` for `WriteLine` returns `<WriteLine />` only — both arguments are invisible to the CLI.
- `WriteLine` is a leaf activity. It does **not** require a `<Sequence>` wrap around itself; it only requires that its parent slot (e.g., `If.Then`) is wrapped in `<Sequence>` per Rule 24.

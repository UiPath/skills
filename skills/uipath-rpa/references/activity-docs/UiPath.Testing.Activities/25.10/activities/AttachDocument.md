# Attach Document

Attaches a file to the currently running Test Case in Orchestrator. The attached document becomes accessible in the test case's execution details in Orchestrator, useful for including screenshots, reports, or evidence files.

**Class:** `UiPath.Testing.Activities.AttachDocument`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `FilePath` | `InArgument<String>` | Yes | The full path to the file to attach to the test case. |
| `Tags` | `InArgument<IEnumerable<String>>` | No | Optional tags to associate with the attached document in Orchestrator. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<Boolean>` | No | `false` | If `true`, execution continues when the activity throws an error. |

---

## XAML Example

```xml
<!-- Attach a file without tags -->
<uta:AttachDocument
  DisplayName="Attach Document"
  FilePath="&quot;C:\Reports\TestReport.pdf&quot;"
  ContinueOnError="False" />

<!-- Attach a file with tags -->
<uta:AttachDocument
  DisplayName="Attach Evidence Screenshot"
  FilePath="[screenshotPath]"
  Tags="[New String() {&quot;evidence&quot;, &quot;screenshot&quot;}]" />
```

# Create New PowerPoint Document

`UiPath.Presentations.Activities.PptDocumentCreateNew`

Creates a new PowerPoint document at the specified location, optionally based on a template.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FilePath` | Path | InArgument | `string` | Yes | | | The path for the new PowerPoint presentation |
| `UseTemplate` | Use Template | Property | `bool` | | `false` | | When enabled, creates the presentation using a template. When disabled, creates a blank presentation |
| `TemplatePath` | Template Path | InArgument | `string` | Conditional | | | Path to a PowerPoint template file (.potx, .potm, .pptx, .pptm). Visible and required when `UseTemplate` is true and local path mode is selected |
| `TemplateResource` | Template Resource | InArgument | `IResource` | Conditional | | | File resource used as template. Visible and required when `UseTemplate` is true and resource mode is selected |
| `PreserveTemplateMetadata` | Preserve Template Metadata | Property | `bool` | | `true` | | When enabled, preserves author/creator info from the template. When disabled, replaces with current user. Visible only when `UseTemplate` is true |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ConflictResolution` | Conflict Behavior | `ConflictBehavior` | `Replace` | What to do if a file already exists at the specified path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Presentation` | Presentation | `IResource` | The generated PowerPoint presentation as a file resource |

## Valid Configurations

**Mode A — Blank presentation**: Leave `UseTemplate` as `false`. Only `FilePath` is required.

**Mode B — From template (local path)**: Set `UseTemplate` to `true`, provide `TemplatePath`. `TemplateResource` is hidden.

**Mode C — From template (resource)**: Set `UseTemplate` to `true`, provide `TemplateResource`. `TemplatePath` is hidden.

### Conditional Properties

- **`TemplatePath`** / **`TemplateResource`** — Only visible when `UseTemplate` is `true`. Mutually exclusive (switched via designer menu). The visible one becomes required.
- **`PreserveTemplateMetadata`** — Only visible when `UseTemplate` is `true`.

### Enum Reference

**`ConflictBehavior`**: `Replace` (Replace existing file), `Fail` (Fail if file exists), `Skip` (Skip if file exists, return existing path)

## XAML Example

**Create blank presentation:**
```xml
<pres:PptDocumentCreateNew
    DisplayName="Create New Presentation"
    FilePath="[&quot;C:\Output\report.pptx&quot;]"
    ConflictResolution="Replace"
    Presentation="[newPresentation]" />
```

**Create from template:**
```xml
<pres:PptDocumentCreateNew
    DisplayName="Create From Template"
    FilePath="[&quot;C:\Output\report.pptx&quot;]"
    UseTemplate="True"
    TemplatePath="[&quot;C:\Templates\corporate.pptx&quot;]"
    PreserveTemplateMetadata="True"
    Presentation="[newPresentation]" />
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
- Output `Presentation` is an `IResource` handle that can be passed to other portable PowerPoint activities via `PathResource`

# Create New Document

`UiPath.Word.Activities.DocumentCreateNew`

Creates a new Word document at the specified file path.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | Path | InArgument | `string` | Yes | | The path where the new document will be created |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ConflictResolution` | Conflict Behavior | `ConflictBehavior` | `Replace` | Determines behavior when a file with the same name already exists |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Document` | Document | `IResource` | A resource reference to the newly created document. Can be passed to other activities that accept file resources |

### Enum Reference

**`ConflictBehavior`**: `Replace` (replaces the existing file), `Fail` (fails if file exists), `Skip` (skips creation, uses existing file)

## XAML Example

```xml
<ui:DocumentCreateNew
    DisplayName="Create New Document"
    FilePath="[outputPath]"
    ConflictResolution="Replace"
    Document="[createdDocument]" />
```

## Notes

- Cross-platform activity (works on both Windows and Linux)
- Unlike other Document* activities, this activity only accepts `FilePath` (not `PathResource`)
- The `Document` output (`IResource`) can be passed as `PathResource` input to subsequent Document* activities

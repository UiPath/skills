# Disable Track Changes

`UiPath.Word.Activities.DocumentDisableTrackChanges` (cross-platform)
`UiPath.Word.Activities.WordDisableTrackChanges` (Windows)

Disables track changes on a Word document. New edits will no longer be tracked as revisions.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Availability

| Platform | Activity | Available |
|----------|----------|-----------|
| Windows | `WordDisableTrackChanges` | Yes |
| Cross-platform | `DocumentDisableTrackChanges` | No (hidden — `browsable: false`) |

The cross-platform variant is implemented but not yet exposed in UiPath Studio. It is hidden from the activity panel via `browsable: false` in the portable metadata. Only the Windows variant is available for use at this time.

## Properties

### Cross-Platform (`DocumentDisableTrackChanges`)

#### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Conditional | | Full path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Conditional | | A file resource reference to the Word document |

Mutually exclusive — provide exactly one (see Valid Configurations).

No additional properties. Cross-platform simply removes tracking from the document settings.

### Windows (`WordDisableTrackChanges`)

**Required Scope:** `WordApplicationScope`

#### Options

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Password` | Password | InArgument | `string` | No | | Password required to unprotect a document that was protected with TrackForEveryone. If the document is not protected, this property is ignored. |

## Valid Configurations

**Cross-platform:** Supports two input modes (mutually exclusive via OverloadGroups):

**Mode A — Local Path**: Set `FilePath` to the document path.
**Mode B — Resource**: Set `PathResource` to a file resource reference.

Only one of `FilePath` or `PathResource` should be set.

**Windows:** No mutually exclusive groups. `Password` is an independent optional property.

## XAML Example

**Cross-platform:**

```xml
<ui:DocumentDisableTrackChanges
    DisplayName="Disable Track Changes"
    FilePath="[documentPath]" />
```

**Windows (inside Word Application Scope):**

```xml
<ui:WordDisableTrackChanges
    DisplayName="Disable Track Changes"
    Password="[optionalPassword]" />
```

## Notes

- **Windows:** If the document was protected with a password via Enable Track Changes (`TrackForEveryone`), provide the same password in `Password` to unprotect and disable tracking. Throws an exception if the document is protected and no password (or an incorrect password) is provided.
- **Cross-platform:** Removes the `<w:trackRevisions>` element from the document's internal `settings.xml`. No password support.
- Must be placed inside a **Word Application Scope** when using the Windows variant.
- The cross-platform variant works on both Windows and Linux robots without requiring Microsoft Word to be installed.

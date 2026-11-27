# Enable Track Changes

`UiPath.Word.Activities.DocumentEnableTrackChanges` (cross-platform)
`UiPath.Word.Activities.WordEnableTrackChanges` (Windows)

Enables track changes on a Word document. All user edits will be tracked as revisions.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Availability

| Platform | Activity | Available |
|----------|----------|-----------|
| Windows | `WordEnableTrackChanges` | Yes |
| Cross-platform | `DocumentEnableTrackChanges` | No (hidden — `browsable: false`) |

The cross-platform variant is implemented but not yet exposed in UiPath Studio. It is hidden from the activity panel via `browsable: false` in the portable metadata. Only the Windows variant is available for use at this time.

## Properties

### Cross-Platform (`DocumentEnableTrackChanges`)

#### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Conditional | | Full path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Conditional | | A file resource reference to the Word document |

Mutually exclusive — provide exactly one (see Valid Configurations).

No additional properties. Cross-platform always enables tracking for all users.

### Windows (`WordEnableTrackChanges`)

**Required Scope:** `WordApplicationScope`

#### Options

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TrackingScope` | Tracking scope | Property | `TrackingScope` | No | `TrackForEveryone` | Specifies the scope of track changes. TrackForEveryone protects the document so all users must track changes. TrackForMe enables tracking for the current user only. |
| `Password` | Password | InArgument | `string` | No | | Optional password used to protect the document when TrackForEveryone scope is selected. |

#### TrackingScope Enum Values

| Value | Description |
|-------|-------------|
| `TrackForEveryone` | Protects the document so all users must track their changes. Optionally password-protected. |
| `TrackForMe` | Enables tracking for the current user only, without document protection. |

## Valid Configurations

**Cross-platform:** Supports two input modes (mutually exclusive via OverloadGroups):

**Mode A — Local Path**: Set `FilePath` to the document path.
**Mode B — Resource**: Set `PathResource` to a file resource reference.

Only one of `FilePath` or `PathResource` should be set.

**Windows:** No mutually exclusive groups. `TrackingScope` and `Password` are independent optional configuration properties.

## XAML Example

**Cross-platform:**

```xml
<ui:DocumentEnableTrackChanges
    DisplayName="Enable Track Changes"
    FilePath="[documentPath]" />
```

**Windows (inside Word Application Scope):**

```xml
<ui:WordEnableTrackChanges
    DisplayName="Enable Track Changes"
    TrackingScope="TrackForEveryone"
    Password="[optionalPassword]" />
```

## Notes

- **Windows — TrackForEveryone:** Protects the document via `Document.Protect(wdAllowOnlyRevisions)` so all users must track changes. An optional `Password` can lock the protection.
- **Windows — TrackForMe:** Sets `Document.TrackRevisions = true` for the current user only, without document protection.
- **Cross-platform:** Modifies the document's internal `settings.xml` to add the `<w:trackRevisions>` element. Always tracks for everyone (no scope option). No `Password` support.
- Must be placed inside a **Word Application Scope** when using the Windows variant.
- The cross-platform variant works on both Windows and Linux robots without requiring Microsoft Word to be installed.

# Manage PDF Password

`UiPath.PDF.Activities.PDF.ManagePDFPassword`

Sets, changes, or removes the user and/or owner password on a PDF file. At least one password field must be provided. The activity writes the resulting file to the path specified by `OutputFileName` (or a generated default path) and returns it as an `ILocalResource` via `OutputFile`.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileName` | File (local path) | InArgument | `string` | Yes* | | | The local file path of the source PDF. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | InArgument | `IResource` | Yes* | | | The file resource to read from. Mutually exclusive with `FileName`. |
| `OldUserPassword` | OldUserPassword | InArgument | `string` | | `null` | | The current user password of the PDF. Required if the file is protected with a user password. |
| `NewUserPassword` | NewUserPassword | InArgument | `string` | | `null` | | The new user password to set. Leave empty to remove the user password. |
| `OldOwnerPassword` | OldOwnerPassword | InArgument | `string` | | `null` | | The current owner (permissions) password. Must be supplied to gain owner rights when changing passwords. |
| `NewOwnerPassword` | NewOwnerPassword | InArgument | `string` | | `null` | | The new owner password to set. Leave empty to remove the owner password. |
| `OutputFileName` | Output File Path | InArgument | `string` | | | | Full path where the modified PDF will be saved. If not specified, a default path is generated automatically. |

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutputFile` | Output File | `ILocalResource` | The resulting modified PDF file as a local resource. |

## Notes

- `FileName` and `ResourceFile` are mutually exclusive (`[OverloadGroup]`). Provide exactly one.
- At least one of the four password arguments (`OldUserPassword`, `NewUserPassword`, `OldOwnerPassword`, `NewOwnerPassword`) must be set; providing none is a validation error.
- The user password and owner password must not be identical.
- If the file is protected with a user password, either `OldUserPassword` or `OldOwnerPassword` must be supplied to open it.
- Owner rights are required to change passwords. If the supplied password does not grant owner rights, the activity throws.

## XAML Example

```xml
<pdf:ManagePDFPassword
    DisplayName="Manage PDF Password"
    FileName="[inputFilePath]"
    OldUserPassword="[currentPassword]"
    NewUserPassword="[newPassword]"
    OutputFileName="[outputFilePath]"
    OutputFile="[outputFile]" />
```

> Namespace prefix `pdf` maps to `clr-namespace:UiPath.PDF.Activities.PDF;assembly=UiPath.PDF.Activities`.

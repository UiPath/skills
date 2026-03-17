# SetPDFPassword

Sets or changes the password on a PDF file.

```xml
<uisaps:SetPDFPassword
    CurrentManagePassword="{x:Null}"
    CurrentOpenPassword="{x:Null}"
    NewManagePassword="{x:Null}"
    ResultFileName="{x:Null}"
    DisplayName="Set PDF Password"
    ExportedPdf="[exportedPdf]"
    NewOpenPassword="[password]"
    PdfFile="[LocalResource.FromPath(filePath)]" />
```

- `ExportedPdf` — output `upr:ILocalResource` variable
- `NewOpenPassword` — string expression for the new open password
- `CurrentOpenPassword` / `CurrentManagePassword` — set when changing password on an already-protected PDF; `{x:Null}` otherwise
- `NewManagePassword` — optional; `{x:Null}` when not needed
- `ResultFileName` — optional output file name; `{x:Null}` to use default

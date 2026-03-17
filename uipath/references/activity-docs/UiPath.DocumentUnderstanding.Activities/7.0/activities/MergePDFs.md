# MergePDFs

Merges multiple PDF files into one. Use `IndividualPdfFiles` nested property to specify files inline, or `CollectionPdfFiles` to pass a variable.

```xml
<uisapm:MergePDFs
    CollectionPdfFiles="{x:Null}"
    DisplayName="Merge PDFs"
    ExportedPdf="[mergedPdf]"
    ResultFileName="[mergedDocumentName]">
  <uisapm:MergePDFs.IndividualPdfFiles>
    <scg:List x:TypeArguments="InArgument(upr:IResource)" Capacity="4">
      <InArgument x:TypeArguments="upr:IResource">[LocalResource.FromPath(firstFilePath)]</InArgument>
      <InArgument x:TypeArguments="upr:IResource">[LocalResource.FromPath(secondFilePath)]</InArgument>
    </scg:List>
  </uisapm:MergePDFs.IndividualPdfFiles>
</uisapm:MergePDFs>
```

- `IndividualPdfFiles` — nested property; `List<InArgument<IResource>>` for inline file list
- `CollectionPdfFiles` — attribute alternative; `IEnumerable(Of IResource)` variable; `{x:Null}` when using `IndividualPdfFiles`
- `ExportedPdf` — output `upr:ILocalResource` variable
- `ResultFileName` — optional name for the merged PDF file

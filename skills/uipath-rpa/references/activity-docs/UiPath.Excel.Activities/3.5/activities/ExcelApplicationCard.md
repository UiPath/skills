### ExcelApplicationCard — Scope Container

All modern `ueab:` activities must be nested inside `ExcelApplicationCard`.

```xml
<ueab:ExcelApplicationCard
    Password="{x:Null}"
    ReadFormatting="{x:Null}"
    SensitivityLabel="{x:Null}"
    DisplayName="Use Excel file"
    ResizeWindow="None"
    SensitivityOperation="None"
    WorkbookPath="[InFilePath]">
  <ueab:ExcelApplicationCard.Body>
    <ActivityAction x:TypeArguments="ue:IWorkbookQuickHandle">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ue:IWorkbookQuickHandle" Name="Excel" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- nested ueab: activities here -->
      </Sequence>
    </ActivityAction>
  </ueab:ExcelApplicationCard.Body>
</ueab:ExcelApplicationCard>
```

The delegate argument name is `"Excel"` by convention. Sheet references use `Excel.Sheet("SheetName")`.
Optional: `CreateNewFile="False"` to prevent creating the file if it doesn't exist.

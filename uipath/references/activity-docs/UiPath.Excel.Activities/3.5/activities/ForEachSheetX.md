### ForEachSheetX

Iterates sheets in a workbook. Same two-argument pattern as `ExcelForEachRowX` but with `WorksheetQuickHandle`:

```xml
<ueab:ForEachSheetX
    DisplayName="For Each Excel Sheet"
    Workbook="[Excel]">
  <ueab:ForEachSheetX.Body>
    <ActivityAction x:TypeArguments="ue:WorksheetQuickHandle, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="ue:WorksheetQuickHandle" Name="CurrentSheet" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do">
        <!-- Access sheet name: CurrentSheet.Name -->
      </Sequence>
    </ActivityAction>
  </ueab:ForEachSheetX.Body>
</ueab:ForEachSheetX>
```

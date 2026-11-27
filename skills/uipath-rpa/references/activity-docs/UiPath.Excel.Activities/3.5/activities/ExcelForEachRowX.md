### ExcelForEachRowX

Requires **two** delegate arguments — `Argument1` (row handle) and `Argument2` (index):

```xml
<ueab:ExcelForEachRowX
    DisplayName="For each row in Sheet1"
    EmptyRowBehavior="Stop"
    HasHeaders="True"
    Range="[Excel.Sheet(&quot;Sheet1&quot;)]"
    SaveAfterEachRow="False">
  <ueab:ExcelForEachRowX.Body>
    <ActivityAction x:TypeArguments="ue:CurrentRowQuickHandle, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="ue:CurrentRowQuickHandle" Name="CurrentRow" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do">
        <!-- Access cell value: CurrentRow.ByField("ColumnName") or CurrentRow.ByIndex(0) -->
      </Sequence>
    </ActivityAction>
  </ueab:ExcelForEachRowX.Body>
</ueab:ExcelForEachRowX>
```

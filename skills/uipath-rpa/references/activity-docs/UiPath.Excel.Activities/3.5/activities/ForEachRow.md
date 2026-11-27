### ForEachRow (classic)

**Style:** Classic (`ui:`) — Standalone, No Scope

One delegate argument of type `DataRow`:

```xml
<ui:ForEachRow
    ColumnNames="{x:Null}"
    CurrentIndex="{x:Null}"
    DataTable="[dtData]"
    DisplayName="For Each Row">
  <ui:ForEachRow.Body>
    <ActivityAction x:TypeArguments="sd:DataRow">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="sd:DataRow" Name="CurrentRow" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- Access: CurrentRow("ColumnName").ToString() -->
      </Sequence>
    </ActivityAction>
  </ui:ForEachRow.Body>
</ui:ForEachRow>
```

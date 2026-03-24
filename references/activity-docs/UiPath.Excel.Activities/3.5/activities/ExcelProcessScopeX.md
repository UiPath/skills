### ExcelProcessScopeX — Optional Outer Process Scope

An optional process-level container that can wrap one or more `ExcelApplicationCard` instances. All attributes default to `{x:Null}`:

```xml
<ueab:ExcelProcessScopeX
    DisplayAlerts="{x:Null}"
    ExistingProcessAction="{x:Null}"
    FileConflictResolution="{x:Null}"
    LaunchMethod="{x:Null}"
    LaunchTimeout="{x:Null}"
    MacroSettings="{x:Null}"
    ProcessMode="{x:Null}"
    ShowExcelWindow="{x:Null}"
    DisplayName="Excel process scope">
  <ueab:ExcelProcessScopeX.Body>
    <ActivityAction x:TypeArguments="ui:IExcelProcess">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ui:IExcelProcess" Name="ExcelProcessScopeTag" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- ExcelApplicationCard goes here -->
      </Sequence>
    </ActivityAction>
  </ueab:ExcelProcessScopeX.Body>
</ueab:ExcelProcessScopeX>
```

Note: the body type argument is `ui:IExcelProcess` (from `xmlns:ui`), not a `ue:` type.

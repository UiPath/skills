### RunMacro

Executes a VBA macro in the presentation. Arguments are passed via nested `RunMacroArgument` children.

```xml
<p:RunMacro
    DisplayName="Run Macro"
    MacroName="[&quot;MacroName&quot;]"
    Presentation="[PowerPoint]"
    Result="[macroResult]">
  <p:RunMacro.Body>
    <ActivityAction>
      <Sequence DisplayName="Arguments">
        <p:RunMacroArgument ArgumentValue="[&quot;arg1&quot;]" DisplayName="Argument 1" />
        <p:RunMacroArgument ArgumentValue="[&quot;arg2&quot;]" DisplayName="Argument 2" />
      </Sequence>
    </ActivityAction>
  </p:RunMacro.Body>
</p:RunMacro>
```

- `MacroName` — VBA function name
- `Result` — output `String` variable with macro return value
- Body contains one `RunMacroArgument` per argument

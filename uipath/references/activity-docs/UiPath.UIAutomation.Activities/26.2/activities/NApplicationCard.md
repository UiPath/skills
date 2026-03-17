### NApplicationCard — full template

```xml
<!-- Opens/attaches to a web browser or desktop app window.
     All UI activities MUST be nested inside this card's Body. -->
<uix:NApplicationCard
    AttachMode="ByInstance"
    DisplayName="Chrome — Login Page"
    HealingAgentBehavior="Job"
    OpenMode="[UiPath.UIAutomationNext.Enums.NAppOpenMode.IfNotOpen]"
    ScopeGuid="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V2">

  <uix:NApplicationCard.Body>
    <ActivityAction x:TypeArguments="x:Object">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:Object" Name="WSSessionData" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- child activities go here -->
      </Sequence>
    </ActivityAction>
  </uix:NApplicationCard.Body>

  <uix:NApplicationCard.TargetApp>
    <!-- Reference = Screen reference from .objects/ directory metadata -->
    <uix:TargetApp Area="0, 0, 0, 0" Reference="<screen-reference>" Version="V2">
      <uix:TargetApp.Arguments>
        <InArgument x:TypeArguments="x:String" />
      </uix:TargetApp.Arguments>
      <uix:TargetApp.WorkingDirectory>
        <InArgument x:TypeArguments="x:String" />
      </uix:TargetApp.WorkingDirectory>
    </uix:TargetApp>
  </uix:NApplicationCard.TargetApp>
</uix:NApplicationCard>
```

### NClick — click a UI element

```xml
<!-- Single left-click on a button.
     ActivateBefore: brings app to foreground before clicking.
     InteractionMode: Simulate = programmatic (preferred for web).
                      HardwareEvents = real mouse (for some desktop apps).
                      SameAsCard = inherit the card's mode. -->
<uix:NClick
    ActivateBefore="True"
    ClickType="Single"
    DisplayName="Click 'Submit'"
    HealingAgentBehavior="SameAsCard"
    InteractionMode="Simulate"
    KeyModifiers="None"
    MouseButton="Left"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V5">

  <uix:NClick.Target>
    <!-- Element reference from .objects/ directory metadata -->
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="b2c3d4e5-f6a7-8901-bcde-f12345678901"
        Reference="<submit-button-element-reference>" />
  </uix:NClick.Target>
</uix:NClick>
```

**NClick with post-click verification** (verify a new element appears after click):
```xml
<uix:NClick
    ActivateBefore="True"
    ClickType="Single"
    DisplayName="Click 'Apply For New Account'"
    HealingAgentBehavior="SameAsCard"
    InteractionMode="SameAsCard"
    KeyModifiers="None"
    MouseButton="Left"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V5">

  <uix:NClick.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="c3d4e5f6-a7b8-9012-cdef-123456789012"
        Reference="<apply-button-element-reference>" />
  </uix:NClick.Target>

  <!-- VerifyOptions: checks that a target APPEARS after the click -->
  <uix:NClick.VerifyOptions>
    <uix:VerifyExecutionOptions DisplayName="Verification target" Mode="Appears">
      <uix:VerifyExecutionOptions.Retry>
        <InArgument x:TypeArguments="x:Boolean" />
      </uix:VerifyExecutionOptions.Retry>
      <uix:VerifyExecutionOptions.Target>
        <!-- Element that should appear on the NEXT screen after navigation -->
        <uix:TargetAnchorable
            DesignTimeRectangle="0, 0, 0, 0"
            Guid="d4e5f6a7-b8c9-0123-defa-234567890123"
            Reference="<next-screen-heading-element-reference>" />
      </uix:VerifyExecutionOptions.Target>
      <uix:VerifyExecutionOptions.Timeout>
        <InArgument x:TypeArguments="x:Double" />
      </uix:VerifyExecutionOptions.Timeout>
    </uix:VerifyExecutionOptions>
  </uix:NClick.VerifyOptions>
</uix:NClick>
```

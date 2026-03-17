### NTypeInto — type text into an input field

```xml
<!-- Types text into a text field.
     ActivateBefore: brings app to foreground.
     ClickBeforeMode: Single = click the field once before typing (clears focus issues).
     EmptyFieldMode: SingleLine = clears the field before typing.
     ClipboardMode: Never = type character by character (more reliable than paste). -->
<uix:NTypeInto
    ActivateBefore="True"
    ClickBeforeMode="Single"
    ClipboardMode="Never"
    DisplayName="Type Into 'Email'"
    EmptyFieldMode="SingleLine"
    HealingAgentBehavior="SameAsCard"
    InteractionMode="Simulate"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Text="[InUserEmail]"
    Version="V5">

  <uix:NTypeInto.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="e5f6a7b8-c9d0-1234-efab-345678901234"
        Reference="<email-input-element-reference>" />
  </uix:NTypeInto.Target>
</uix:NTypeInto>
```

**NTypeInto with VerifyOptions** (verify typed text appears):
```xml
<uix:NTypeInto
    ActivateBefore="True"
    ClickBeforeMode="Single"
    ClipboardMode="Never"
    DisplayName="Type Into 'Account Number'"
    EmptyFieldMode="SingleLine"
    HealingAgentBehavior="SameAsCard"
    InteractionMode="SameAsCard"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Text="[InAccountNumber]"
    Version="V5">

  <uix:NTypeInto.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="f6a7b8c9-d0e1-2345-fabc-456789012345"
        Reference="<account-number-input-element-reference>" />
  </uix:NTypeInto.Target>

  <uix:NTypeInto.VerifyOptions>
    <!-- ExpectedText="[Nothing]" means verify element appears, not a specific value -->
    <uix:VerifyExecutionTypeIntoOptions DisplayName="{x:Null}" ExpectedText="[Nothing]" Mode="Appears">
      <uix:VerifyExecutionTypeIntoOptions.Retry>
        <InArgument x:TypeArguments="x:Boolean" />
      </uix:VerifyExecutionTypeIntoOptions.Retry>
      <uix:VerifyExecutionTypeIntoOptions.Timeout>
        <InArgument x:TypeArguments="x:Double" />
      </uix:VerifyExecutionTypeIntoOptions.Timeout>
    </uix:VerifyExecutionTypeIntoOptions>
  </uix:NTypeInto.VerifyOptions>
</uix:NTypeInto>
```

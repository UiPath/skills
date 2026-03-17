### NSetText — set text programmatically (without click/typing simulation)

```xml
<!-- Sets text in a field via API injection; faster than NTypeInto but
     may not fire JavaScript onChange events in some web apps.
     Use for desktop apps or when NTypeInto is unreliable. -->
<uix:NSetText
    DisplayName="Set Text 'Email'"
    HealingAgentBehavior="SameAsCard"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Text="[InUserEmail]"
    Version="V5">

  <uix:NSetText.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="a7b8c9d0-e1f2-3456-abcd-567890123456"
        Reference="<email-input-element-reference>" />
  </uix:NSetText.Target>
</uix:NSetText>
```

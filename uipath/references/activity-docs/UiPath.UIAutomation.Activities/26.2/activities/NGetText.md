### NGetText — extract text from a UI element

```xml
<!-- Reads visible text from an element and stores it in a variable.
     TextString: the output variable (must be declared in scope). -->
<uix:NGetText
    DisplayName="Get Text 'Account Name'"
    HealingAgentBehavior="SameAsCard"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    TextString="[createdAccountName]"
    Version="V5">
  <uix:NGetText.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="a3b4c5d6-e7f8-9012-abcd-123456789012"
        Reference="<account-name-label-element-reference>" />
  </uix:NGetText.Target>
</uix:NGetText>
```

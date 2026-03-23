### NCheck — check or uncheck a checkbox

```xml
<!-- Checks a checkbox. Action="Check" | "Uncheck" | "Toggle" -->
<uix:NCheck
    Action="Check"
    DisplayName="Check 'Remember Me'"
    HealingAgentBehavior="SameAsCard"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V5">
  <uix:NCheck.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="d0e1f2a3-b4c5-6789-defa-890123456789"
        Reference="<remember-me-checkbox-element-reference>" />
  </uix:NCheck.Target>
</uix:NCheck>
```

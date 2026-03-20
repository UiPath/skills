### NCheckState — verify element existence (app state check)

`NCheckState` checks whether a UI element is present/visible. It is the primary pattern for **conditional branching** and **login/navigation verification** in UIA workflows.

**CRITICAL rules for NCheckState:**
- `HealingAgentBehavior` must be `"Disabled"` (verification should not auto-heal)
- Both `IfExists` and `IfNotExists` branches MUST be present (even if empty)
- Do NOT nest `NApplicationCard` inside `NCheckState` branches — keep all actions in the same card scope

**Standard pattern: throw on failure**
```xml
<!-- Verifies that an expected element appeared; throws if it did not.
     Use this after any navigation, form submission, or state change. -->
<uix:NCheckState
    DisplayName="Check App State — 'Confirmation Banner' (verify action succeeded)"
    HealingAgentBehavior="Disabled"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V5">

  <!-- What to do when the target IS found -->
  <uix:NCheckState.IfExists>
    <Sequence DisplayName="Target appears">
      <!-- Success path: continue workflow, optionally log -->
      <ui:LogMessage Level="Info"
          Message="Action succeeded — confirmation banner visible"
          DisplayName="Log success" />
    </Sequence>
  </uix:NCheckState.IfExists>

  <!-- What to do when the target is NOT found -->
  <uix:NCheckState.IfNotExists>
    <Sequence DisplayName="Target does not appear">
      <!-- Failure path: throw to surface error to caller -->
      <Throw
          Exception="[New Exception(&quot;Action failed — confirmation banner not visible&quot;)]"
          DisplayName="Throw on missing confirmation" />
    </Sequence>
  </uix:NCheckState.IfNotExists>

  <!-- The element to look for -->
  <uix:NCheckState.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="e1f2a3b4-c5d6-7890-efab-901234567890"
        Reference="<confirmation-banner-element-reference>" />
  </uix:NCheckState.Target>
</uix:NCheckState>
```

**Variant: capture boolean result into a variable** (used in RetryScope conditions):
```xml
<!-- Exists="[myBoolVar]" outputs true/false into a variable instead of branching.
     Still requires IfExists/IfNotExists branches (can be empty Sequences). -->
<uix:NCheckState
    CheckVisibility="True"
    DisplayName="Check App State — login success indicator"
    Exists="[loginSucceeded]"
    HealingAgentBehavior="Disabled"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V5">
  <uix:NCheckState.IfExists>
    <Sequence DisplayName="Target appears" />
  </uix:NCheckState.IfExists>
  <uix:NCheckState.IfNotExists>
    <Sequence DisplayName="Target does not appear" />
  </uix:NCheckState.IfNotExists>
  <uix:NCheckState.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="f2a3b4c5-d6e7-8901-fabc-012345678901"
        Reference="<welcome-message-element-reference>" />
  </uix:NCheckState.Target>
</uix:NCheckState>
```

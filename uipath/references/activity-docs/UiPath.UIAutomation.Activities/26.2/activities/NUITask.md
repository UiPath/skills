### NUITask — ScreenPlay (AI-driven interaction)

Use `NUITask` **only** when none of the specific activities above cover the action, or when the user explicitly requests ScreenPlay. It uses AI to interpret a natural-language description and perform the interaction.

```xml
<!-- NUITask (ScreenPlay): AI executes the Task description as UI actions.
     Must be inside an NApplicationCard just like any other UIA activity. -->
<uix:NUITask
    DisplayName="ScreenPlay — Accept cookie banner"
    HealingAgentBehavior="SameAsCard"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Task="Click the Accept Cookies button if it appears on the page"
    Version="V2" />
```

**Rule:** If an action can be done with `NClick`, `NTypeInto`, `NSelectItem`, etc., use those instead of `NUITask`. `NUITask` is a fallback for complex or unpredictable UI interactions.

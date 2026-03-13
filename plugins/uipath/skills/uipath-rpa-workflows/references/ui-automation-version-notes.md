# UI Automation — Version-Specific Notes

This file documents version-specific differences in `UiPath.UIAutomation.Activities` property support. Always use `uipcli rpa get-default-activity-xaml` to confirm the exact properties for your installed version.

---

## 24.10.x (confirmed on 24.10.6)

### NApplicationCard

**Default XAML from `get-default-activity-xaml`:**
```xml
<uix:NApplicationCard AttachMode="ByInstance" ScopeGuid="..." Version="V2">
  <uix:NApplicationCard.Body>
    <ActivityAction x:TypeArguments="x:Object">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:Object" Name="WSSessionData" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do" />
    </ActivityAction>
  </uix:NApplicationCard.Body>
  <uix:NApplicationCard.TargetApp>
    <uix:TargetApp Area="0, 0, 0, 0" Version="V1" />
  </uix:NApplicationCard.TargetApp>
</uix:NApplicationCard>
```

**Properties NOT available in 24.10.x:**
| Property | Notes |
|----------|-------|
| `HealingAgentBehavior` | Does not exist on `NApplicationCard` or child activities (`NTypeInto`, `NClick`, etc.). Omit entirely. |
| `OpenMode` | Does not exist. The card attaches by instance only. |
| `InteractionMode` | Does not exist on the card. May not exist on child activities either — check with `get-default-activity-xaml`. |
| `CloseMode` | Not in default XAML. May exist but is not set by default. |

**Properties available:**
- `AttachMode` — `"ByInstance"`
- `ScopeGuid` — unique GUID per card
- `Version` — `"V2"`
- `DisplayName` — set by Studio on save

### TargetApp (24.10.x)

**Version:** `V1` (NOT `V2`)

**Properties NOT available:**
| Property | Notes |
|----------|-------|
| `WorkingDirectory` | Does not exist. Omit `<uix:TargetApp.WorkingDirectory>` entirely. |
| `Arguments` | Does not exist. Omit `<uix:TargetApp.Arguments>` entirely. |

**Minimal form:**
```xml
<uix:TargetApp Area="0, 0, 0, 0" Reference="<screen-reference>" Version="V1" />
```

Studio enriches this on save with `Selector`, `Title`, `FilePath`, `ContentHash`, `IconBase64`, `InformativeScreenshot`, etc.

### NTypeInto (24.10.x)

**Default XAML from `get-default-activity-xaml`:**
```xml
<uix:NTypeInto ActivateBefore="True" ClickBeforeMode="Single"
    DisplayName="Type Into" EmptyFieldMode="SingleLine" Version="V4">
  <uix:NTypeInto.VerifyOptions>
    <uix:VerifyExecutionTypeIntoOptions DisplayName="{x:Null}" Mode="Appears">
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

**Version:** `V4` (NOT `V5`)

**Properties NOT available in 24.10.x:**
| Property | Notes |
|----------|-------|
| `HealingAgentBehavior` | Does not exist. Omit. |
| `ClipboardMode` | Does not exist. Omit. |
| `InteractionMode` | Does not exist on NTypeInto. Omit. |
| `ScopeIdentifier` | Not in default XAML, but **Studio auto-adds it on save** to match the parent card's `ScopeGuid`. You can include it manually or let Studio add it. |

**Properties available:**
- `ActivateBefore` — `"True"`
- `ClickBeforeMode` — `"Single"` (click field before typing)
- `EmptyFieldMode` — `"SingleLine"` (clear field before typing)
- `Text` — the text to type (string literal or `[variable]`)
- `Version` — `"V4"`
- `VerifyOptions` — included by default

### NClick (24.10.x)

Verify with `get-default-activity-xaml`. Expected differences from the main reference:
- `Version`: likely `V4` (not `V5`)
- `HealingAgentBehavior`: likely does not exist
- `InteractionMode`: likely does not exist
- `ScopeIdentifier`: auto-added by Studio

### NCheckState (24.10.x)

Verify with `get-default-activity-xaml`. Expected differences:
- `Version`: likely `V4` (not `V5`)
- `HealingAgentBehavior`: likely does not exist (but was originally documented as `"Disabled"` — verify)

---

## 25.x+ (anticipated)

Properties like `HealingAgentBehavior`, `ClipboardMode`, `InteractionMode`, `OpenMode`, and `WorkingDirectory` on `TargetApp` are expected in newer versions. The main `ui-automation.md` reference documents these. When upgrading, re-run `get-default-activity-xaml` for each activity to discover newly available properties.

---

## General Rule

**Always run `uipcli rpa get-default-activity-xaml --activity-class-name "..."` before writing UIA XAML.** The default output is the ground truth for the installed version. Properties that don't exist in the installed version will cause `"Could not find member"` validation errors.

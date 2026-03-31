# UI Automation (UIA) Reference

Comprehensive guide for generating and editing UiPath UIAutomationNext XAML workflows. Covers activity templates, Object Repository integration, interaction patterns, and complete examples with annotated XAML.

**Version note:** This reference targets `UiPath.UIAutomation.Activities` **25.10+**. For packages **below 25.10** (e.g. 24.10.x), several properties documented here do not exist — consult **[version-notes.md](./version-notes.md)** for version-specific differences and always verify with `uip rpa get-default-activity-xaml --use-studio`.

---

## Package and Namespace Requirements

**NuGet package:** `UiPath.UIAutomation.Activities` (latest stable)

**Required `xmlns` declaration** on every UIA workflow:
```xml
xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"
```
Also needed when using `RetryScope` or `LogMessage`:
```xml
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

**Required entries in `TextExpression.NamespacesForImplementation`:**
```xml
<x:String>UiPath.UIAutomationNext.Enums</x:String>
<x:String>UiPath.UIAutomationCore.Contracts</x:String>
<x:String>UiPath.UIAutomationNext.Models</x:String>
<x:String>UiPath.UIAutomationNext.Activities</x:String>
<x:String>UiPath.Shared.Activities</x:String>
<x:String>UiPath.Platform.ObjectLibrary</x:String>
<x:String>UiPath.Platform.SyncObjects</x:String>
<x:String>UiPath.UIAutomationNext.Contracts</x:String>
<x:String>UiPath.UIAutomationNext.Models.CV</x:String>
```

**Required entries in `TextExpression.ReferencesForImplementation`:**
```xml
<AssemblyReference>UiPath.UIAutomationNext.Activities</AssemblyReference>
<AssemblyReference>UiPath.UiAutomation.Activities</AssemblyReference>
<AssemblyReference>UiPath.Platform</AssemblyReference>
```

---

## Object Repository: Discovery and Usage

**CRITICAL RULE: ALWAYS use object references discovered from the `.objects/` directory. NEVER invent, copy from examples, or guess reference strings.**

### Capturing New UI Targets

When the Object Repository is empty or missing targets for the workflow, use the CLI indication tools to let the user point at UI elements. This captures selectors and stores them in the `.objects/` directory:

```bash
# Step 1: Indicate the application/screen (user points at the app window)
uip rpa indicate-application --name "MyBankingApp --use-studio"

# Step 2: Read .objects/ to find the Screen reference for use as --parent-id
# IMPORTANT: --parent-name can fail if duplicate App names exist (e.g. from a failed
# prior indicate-application call that left an orphan). Always prefer --parent-id.

# Step 3: Indicate elements within that screen (user points at each element)
uip rpa indicate-element --name "UsernameField" --activity-class-name "UiPath.UIAutomation.Activities.TypeInto" --parent-id "<screen-reference> --use-studio"
uip rpa indicate-element --name "LoginButton" --activity-class-name "UiPath.UIAutomation.Activities.ClickX" --parent-id "<screen-reference> --use-studio"
```

**Indication pitfalls:**
- `indicate-application` can fail on first call (e.g. project still loading) but still **partially write** to `.objects/`, leaving an orphan App entry with a malformed reference (leading `/` without library prefix). If this happens, delete the orphan folder from `.objects/` and re-run.
- `indicate-element --parent-name` resolves by name and can match the wrong App if duplicates exist. **Always prefer `--parent-id`** with the Screen reference from `.objects/` metadata.
- After indication, always re-read `.objects/` to confirm the full hierarchy (App → AppVersion → Screen → Element) was created.

After indication, the `.objects/` directory is populated with metadata and selectors. Proceed to Step 1 below to read them.

### Step 1 — Retrieve objects

Explore the `.objects/` directory to discover available UI objects:
```
Glob: pattern="**/*" path="{projectRoot}/.objects/"
```
Then read the metadata JSON files found to obtain the object tree (apps, screens, elements and their references).

Returns a tree like:
```json
[
  {
    "name": "My Banking App",
    "type": "App",
    "reference": "xV5KVHstv0-fcV1vk2ZIEw/vIYGGPE33E64nJ9QZgUhcQ",
    "children": [
      {
        "name": "Home",
        "type": "Screen",
        "reference": "xV5KVHstv0-fcV1vk2ZIEw/nxHpmlVD_km8gL2dKa2TcQ",
        "children": [
          { "name": "Loans",  "type": "Element", "reference": "xV5KVHstv0-fcV1vk2ZIEw/n7CV3Admb0KY-wvxtbV5AQ" },
          { "name": "Products", "type": "Element", "reference": "xV5KVHstv0-fcV1vk2ZIEw/qIhEvO1U60G3Bo6a--0Xig" }
        ]
      },
      {
        "name": "Form",
        "type": "Screen",
        "reference": "xV5KVHstv0-fcV1vk2ZIEw/N1PiQEisu0mElDdOoPaYUA",
        "children": [
          { "name": "Email",  "type": "Element", "reference": "xV5KVHstv0-fcV1vk2ZIEw/fO9UAt3c9EKCF5OI_5HITg" },
          { "name": "Submit", "type": "Element", "reference": "xV5KVHstv0-fcV1vk2ZIEw/-BlNATqgMk2Y7O7qFDw5WA" }
        ]
      }
    ]
  }
]
```

### Step 2 — Map references to activities

| Object type | Where to use the reference |
|-------------|---------------------------|
| **Screen** | `NApplicationCard.TargetApp.Reference` — identifies which screen/window this card attaches to |
| **Element** | `NClick.Target.TargetAnchorable.Reference`, `NTypeInto.Target.TargetAnchorable.Reference`, etc. |
| **App** | **Never use directly** — the App reference is the tree root; use Screen or Element children only |

### Step 3 — Screen grouping rule

Every `NApplicationCard` targets **one Screen** from the object repo. All UI activities inside it must target **Elements that belong to that same Screen** (or screens reachable from it without navigating away). When the user's actions require interacting with elements from a **different Screen**, create a **new** `NApplicationCard` for those actions.

---

## Core Architecture: NApplicationCard

`NApplicationCard` is the scope container for all UI automation. It opens/attaches to an application window, then executes nested activities inside `.Body`.

### Key attributes

| Attribute | Meaning |
|-----------|---------|
| `ScopeGuid` | **New random GUID** you generate for each card (e.g. `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`). Must be unique per card. |
| `AttachMode` | `"ByInstance"` — attaches to a running instance of the app |
| `OpenMode` | `"[UiPath.UIAutomationNext.Enums.NAppOpenMode.IfNotOpen]"` — opens the app only if not already running |
| `HealingAgentBehavior` | `"Job"` on the card; `"SameAsCard"` on child activities; `"Disabled"` on `NCheckState` |
| `Version` | Always `"V2"` for the card |
| `CloseMode` | Omit (defaults to never-close) unless explicitly needed |
| `InteractionMode` | Optional card-level default; child activities may override with `SameAsCard` to inherit |

### ScopeGuid / ScopeIdentifier binding — CRITICAL

Every child activity that targets a UI element (`NClick`, `NTypeInto`, `NCheckState`, etc.) **must** have `ScopeIdentifier` set to the **same value** as the parent `NApplicationCard.ScopeGuid`.

```
NApplicationCard  ScopeGuid="abc-123"
  └── NTypeInto   ScopeIdentifier="abc-123"   ← must match
  └── NClick      ScopeIdentifier="abc-123"   ← must match
  └── NCheckState ScopeIdentifier="abc-123"   ← must match
```

### TargetApp structure (object repo)

Use this minimal form whenever a Screen reference is available from the `.objects/` directory:

```xml
<uix:NApplicationCard.TargetApp>
  <!-- Reference = Screen reference (NOT App reference) from .objects/ directory metadata -->
  <uix:TargetApp Area="0, 0, 0, 0" Reference="<screen-reference>" Version="V2">
    <uix:TargetApp.Arguments>
      <InArgument x:TypeArguments="x:String" />
    </uix:TargetApp.Arguments>
    <uix:TargetApp.WorkingDirectory>
      <InArgument x:TypeArguments="x:String" />
    </uix:TargetApp.WorkingDirectory>
  </uix:TargetApp>
</uix:NApplicationCard.TargetApp>
```

For browser automation, also add `Url` and `BrowserType` (optional when using object repo):
```xml
<uix:TargetApp Area="0, 0, 0, 0" Reference="<screen-reference>"
               Url="https://example.com/login" BrowserType="Chrome" Version="V2">
```

### TargetApp structure (no object repo — raw selector)

Use only when the object repo has no matching entry:
```xml
<uix:TargetApp Selector="&lt;html app='chrome.exe' title='My Page' /&gt;"
               Url="https://example.com" BrowserType="Chrome"
               Area="-2569, -9, 2578, 1398" Version="V2">
  <uix:TargetApp.Arguments>
    <InArgument x:TypeArguments="x:String" />
  </uix:TargetApp.Arguments>
  <uix:TargetApp.WorkingDirectory>
    <InArgument x:TypeArguments="x:String" />
  </uix:TargetApp.WorkingDirectory>
</uix:TargetApp>
```

### TargetAnchorable structure (object repo — minimal)

Use for any child activity target when the element reference is available:
```xml
<!-- Element from object repo: just Reference + Guid + DesignTimeRectangle -->
<uix:TargetAnchorable
    DesignTimeRectangle="0, 0, 0, 0"
    Guid="<new-random-guid>"
    Reference="<element-reference>" />
```

### TargetAnchorable structure (no object repo — raw selector)

Use only when no object repo entry exists:
```xml
<uix:TargetAnchorable
    BrowserURL="example.com/page"
    ContentHash="<hash>"
    DesignTimeRectangle="100, 200, 300, 40"
    ElementType="InputBox"
    ElementVisibilityArgument="Interactive"
    FullSelectorArgument="&lt;webctrl id='email' tag='INPUT' /&gt;"
    Guid="<new-random-guid>"
    Reference="<element-reference>"
    ScopeSelectorArgument="&lt;html app='chrome.exe' title='My Page' /&gt;"
    SearchSteps="Selector"
    Version="V6"
    WaitForReadyArgument="Interactive" />
```

---

## Expression Syntax in UIA Workflows

Most UIA projects use **VB.NET expressions** (check for `Microsoft.VisualBasic` in namespaces).

| Value type | XAML attribute value | Example |
|------------|---------------------|---------|
| Variable / argument | `"[varName]"` | `Text="[InUserEmail]"` |
| Hardcoded string literal | plain text, no brackets | `Text="admin@example.com"` |
| VB string interpolation | `"[$&quot;Hello {name}&quot;]"` | `Message="[$&quot;Done: {count}&quot;]"` |
| Boolean true | `"True"` | `ActivateBefore="True"` |
| Enum | `"[EnumType.Value]"` | `OpenMode="[UiPath.UIAutomationNext.Enums.NAppOpenMode.IfNotOpen]"` |

For C# projects (no `Microsoft.VisualBasic` namespace): use `CSharpValue`/`CSharpReference` wrappers as documented in `xaml-basics-and-rules.md`.

---

## Interaction Modes

| Mode | When to use |
|------|------------|
| `Simulate` | Web browsers — programmatic injection. Fast, works without window focus. |
| `HardwareEvents` | Desktop apps (WinForms, WPF) requiring real mouse/keyboard input. |
| `DebuggerApi` | Chrome/Edge DevTools Protocol. Use when Simulate fails on certain SPAs. |
| `SameAsCard` | Child activity inherits the mode set on the parent `NApplicationCard`. |

Set `InteractionMode` on the `NApplicationCard` and use `SameAsCard` on most child activities for consistency. Override individual activities only when needed.

---

## Wait and Verify Options

### WaitForReadyArgument

Controls how long an activity waits for the element to be ready before acting:
- `"Interactive"` — waits until the element is clickable/editable (most inputs)
- `"None"` — acts immediately (buttons/links that don't need ready state)
- `"Complete"` — waits for full page load (slower but thorough)

Only set `WaitForReadyArgument` when using raw selectors (TargetAnchorable with full selector). With object repo minimal form, omit it.

### VerifyOptions

Attach to `NClick`, `NTypeInto`, or `NKeyboardShortcuts` to assert a post-action state:
- `Mode="Appears"` — asserts the target element appears after the action
- `Mode="Vanishes"` — asserts the target element disappears after the action

This is lighter than a full `NCheckState` and is used for inline verification of critical navigation steps.

---

## Pattern: Retry with NCheckState

Use `ui:RetryScope` (`UiPath.System.Activities`) to retry a block up to N times. Structure:

- `RetryScope.ActivityBody` — `ActivityAction` wrapping an `NApplicationCard` with the steps to retry.
- `RetryScope.Condition` — `ActivityFunc<x:Boolean>` containing its own `NApplicationCard` (fresh `ScopeGuid`) with a single `NCheckState` that sets `Exists="[conditionResult]"` and has empty `IfExists`/`IfNotExists` branches. The `DelegateOutArgument` named `conditionResult` propagates the boolean back to `RetryScope`.

Key constraints:
- The `NApplicationCard` inside `Condition` must have its **own unique `ScopeGuid`** — never share the body card's guid.
- Declare `retryInterval` as a `Variable x:TypeArguments="x:TimeSpan"` in the enclosing `Sequence` and pass it to `RetryInterval`.
- `NCheckState` in the condition must have `HealingAgentBehavior="Disabled"` and `CheckVisibility="True"`.

---

## Pattern: Handling Unreliable Selectors

Triggered by: `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException: Could not find the user-interface (UI) element for this action.`

Use one of these two approaches when a selector may be stale or an element is conditionally absent.

### Option A — NCheckState Pre-check (preferred)

Check if the element exists before acting. Prevents `NodeNotFoundException` from being thrown.

```xml
<!-- Declare: <Variable x:TypeArguments="x:Boolean" Name="elementExists" Default="False" /> -->

<uix:NCheckState
    CheckVisibility="True"
    DisplayName="Check App State — verify element before acting"
    Exists="[elementExists]"
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
        Guid="b2c3d4e5-f6a7-8901-bcde-f12345678901"
        Reference="<element-reference>" />
  </uix:NCheckState.Target>
</uix:NCheckState>

<If DisplayName="If Element Exists">
  <If.Condition>
    <InArgument x:TypeArguments="x:Boolean">[elementExists]</InArgument>
  </If.Condition>
  <If.Then>
    <Sequence DisplayName="Element found — interact">
      <!-- NClick / NTypeInto / etc. -->
    </Sequence>
  </If.Then>
  <If.Else>
    <Sequence DisplayName="Element not found">
      <ui:LogMessage Level="Warn"
          DisplayName="Log NodeNotFoundException avoided"
          Message="Element not found — selector may be stale. Skipping." />
    </Sequence>
  </If.Else>
</If>
```

### Option B — TryCatch Wrapper

Attempt the action and catch only `NodeNotFoundException`. All other exceptions (app state, permissions, timeouts) rethrow normally so they are not silently swallowed.

**Requires:**
- `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`
- `xmlns:uixe="clr-namespace:UiPath.UIAutomationNext.Exceptions;assembly=UiPath.UIAutomationNext.Contracts"`
  *(If this causes a type-resolution error, verify the assembly name by reading the JIT schema at `.project/JitCustomTypesSchema.json` and grepping XAML files for the correct namespace.)*

```xml
<TryCatch DisplayName="Try — Click 'Submit' (handle NodeNotFoundException)">
  <TryCatch.Try>
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
        <uix:TargetAnchorable
            DesignTimeRectangle="0, 0, 0, 0"
            Guid="c3d4e5f6-a7b8-9012-cdef-123456789012"
            Reference="<submit-button-element-reference>" />
      </uix:NClick.Target>
    </uix:NClick>
  </TryCatch.Try>
  <TryCatch.Catches>
    <!-- Selector miss: log and continue -->
    <Catch x:TypeArguments="uixe:NodeNotFoundException">
      <ActivityAction x:TypeArguments="uixe:NodeNotFoundException">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="uixe:NodeNotFoundException" Name="ex" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Handle NodeNotFoundException">
          <ui:LogMessage Level="Warn"
              DisplayName="Log NodeNotFoundException"
              Message="NodeNotFoundException — element not found. Selector may be stale. Skipping." />
        </Sequence>
      </ActivityAction>
    </Catch>
    <!-- All other exception types propagate automatically — no explicit catch needed -->
  </TryCatch.Catches>
</TryCatch>
```

### Decision Guide

| Situation | Use |
|-----------|-----|
| Element may or may not be present | `NCheckState` pre-check |
| Must attempt action first | `TryCatch` wrapper |
| Multiple UIA steps that may all fail | `TryCatch` around the block |
| Need retry on failure | `NCheckState` inside `RetryScope` |

---

## Pattern: Multi-Screen Workflows

When a workflow interacts with elements across **multiple screens** (pages), emit one `NApplicationCard` per screen, placed **sequentially at the same level** — never nested. Each card must:

- Have its own unique `ScopeGuid`
- Have `TargetApp.Reference` set to the **Screen** reference for that screen (from the `.objects/` directory metadata)
- Contain only `NClick`/`NTypeInto`/etc. targeting elements that belong to that screen

Use `NCheckState` at the start of each subsequent card to verify the expected screen loaded before interacting with its elements.

---

## Rules Summary

| Rule | Detail |
|------|--------|
| **Always explore the `.objects/` directory first** | Never invent or copy reference strings — read them from `.objects/` metadata JSON files |
| **TargetApp.Reference = Screen reference** | Never use the App-level reference in TargetApp |
| **ScopeIdentifier must match ScopeGuid** | Every child activity's `ScopeIdentifier` equals the parent card's `ScopeGuid` |
| **Each screen → one NApplicationCard** | Never mix elements from different screens in one card |
| **Never nest NApplicationCard inside NApplicationCard** | Flat structure; new card for each screen transition |
| **HealingAgentBehavior: "Disabled" on NCheckState** | Verification targets must not be healed |
| **NCheckState always has IfExists AND IfNotExists** | Both branches are mandatory, even if empty |
| **Do not place NClick/NTypeInto outside NApplicationCard** | All UIA actions must be scoped |
| **Use NUITask (ScreenPlay) only as last resort** | Prefer specific activities; NUITask for unpredictable UI only |
| **For verifications, use NCheckState not NUITask** | Testing activities use `UiPath.Testing.Activities.Verify*` prefix |
| **Generate a fresh GUID for each new NApplicationCard** | Never reuse ScopeGuid across cards |
| **Expression syntax (VB): variables use `[varName]`** | Literals are plain text; string interpolation is `[$"text {var}"]` |

---

## Common UIA Pitfalls

**1. Wrong reference type in TargetApp**
- `TargetApp.Reference` must be a **Screen** reference, not an App reference. Check object repo structure carefully.

**2. ScopeIdentifier mismatch**
- Activities inside Card A with `ScopeIdentifier` pointing to Card B's `ScopeGuid` will throw at runtime. Always ensure they match.

**3. NCheckState without both branches**
- Omitting `IfExists` or `IfNotExists` causes a compile error. Always include both, even as empty `<Sequence>` elements.

**4. Nested NApplicationCard**
- Putting an `NApplicationCard` inside another card's Body causes runtime issues. For multi-screen flows, put all cards sequentially at the same level.

**5. Wrong Guid for activity instance**
- The `Guid` attribute on `TargetAnchorable` is a per-activity-instance identifier — it must be unique across all activities in the workflow. Generate a new random GUID for every target.

**6. Using App reference for TargetApp**
- The App-level reference (root of the object tree) cannot be used in `TargetApp`. It must be one of its Screen children.

**7. NUITask inside RetryScope condition**
- The condition of `RetryScope` must use `NCheckState` (with `Exists=`) returning a boolean, not `NUITask`.

**8. Missing namespace for `ui:` activities**
- `RetryScope` and `LogMessage` require `xmlns:ui="http://schemas.uipath.com/workflow/activities"`. Without it, the workflow won't compile.

**9. Object Repository is empty**
- If `.objects/` has no entries, you cannot build UIA workflows with object references. Use `uip rpa indicate-application --use-studio` and `uip rpa indicate-element --use-studio` to capture UI targets first, then re-read `.objects/` to get the reference strings.

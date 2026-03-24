# UI Automation Guide for RPA Workflows

Quick reference for UI automation in XAML/RPA workflows using UiPath UIAutomation activities.

> **For full activity details:** always check `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/` first. If unavailable, fall back to the bundled reference at `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/activities/` (pick the version folder closest to what is installed in the project).

**Required package:** `UiPath.UIAutomation.Activities`

---

## Key Concepts

### Application Card (Use Application/Browser)

Every UI automation workflow starts with an **Application Card** (`uix:NApplicationCard`) that opens or attaches to a desktop application or web browser. All UI activities (Click, TypeInto, GetText, etc.) must be placed inside an Application Card scope.

### Target Configuration

Each UI activity targets an element via the **Target** property, which includes:
- **Selector** — XML path that uniquely identifies the UI element
- **Anchor** — optional nearby reference element for more robust targeting
- **CV (Computer Vision)** — fallback visual targeting using screenshots
- **Fuzzy selector** — tolerant matching for dynamic attributes

### Object Repository

The Object Repository stores reusable screen and element definitions in the `.objects/` directory. **CRITICAL: ALWAYS use object references discovered from `.objects/`. NEVER invent or guess reference strings.**

---

## Configuring Targets (Primary Approach)

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: snapshot capture, element discovery, selector generation, selector improvement, and OR registration.

The UIA activity-docs version folder contains the skill files. Discover them by globbing:
```
Glob: pattern="**/*.md" path="../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/"
```
These are **reference docs to read and follow** — they are NOT invocable as slash commands via the Skill tool. Read the relevant `.md` file and follow its steps using the `uip rpa` CLI commands directly.

To configure a target, read and follow the `uia-configure-target` skill:
- **Window + element:** `--window <description> --element <description>`
- **Window only:** `--window <description>`

The skill will search the Object Repository for existing matches before creating new entries, generate selectors from the live application tree, and return the OR reference IDs.

### Applying OR References to XAML

After `uia-configure-target` returns reference IDs, apply them to the XAML by setting the `Reference` attribute on the target objects. The `Reference` attribute links the XAML to the OR entry so Studio can sync selector changes. **Selectors are still required** — `Reference` does not replace them.

**On `TargetApp`** (screen reference → from `uia-configure-target --window`):
```xml
<uix:TargetApp
    Reference="<screen_ref_id>"
    Selector="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    Version="V2" />
```

**On `TargetAnchorable`** (element reference → from `uia-configure-target --window --element`):
```xml
<uix:TargetAnchorable
    FullSelectorArgument="&lt;uia automationid='btn1' name='Submit' /&gt;"
    Reference="<element_ref_id>"
    ScopeSelectorArgument="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    SearchSteps="Selector"
    Version="V6" />
```

When an element is reused across multiple activities, use the same `Reference` value on each `TargetAnchorable`. Studio will populate design-time metadata (`ContentHash`, `DesignTimeRectangle`, `Guid`, etc.) automatically when it opens the file — you do not need to set these.

See [Target.md](../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/activities/common/Target.md#using-object-repository-references-in-xaml) for full details.

---

## Low-Level Indication Tools (Alternative)

If you cannot use `uia-configure-target` (e.g., the skill docs are unavailable), you can fall back to the raw indication CLI commands. These require user interaction (clicking on the target element) and produce less robust selectors:

```bash
# Indicate a screen (creates App automatically if none exists)
uip rpa indicate-application --name "Dashboard" --project-dir "<PROJECT_DIR>" --format json

# Indicate an element on a screen
uip rpa indicate-element --name "SubmitButton" --parent-id "r-xxxxx/zzzzz" --activity-class-name "Click" --project-dir "<PROJECT_DIR>" --format json
```

After indication, re-read `.objects/` metadata to get the reference strings for use in XAML.

---

## Common Activities

| Activity | Description |
|----------|-------------|
| **Use Application/Browser** | Opens/attaches to a desktop app or browser — required scope for all UI actions |
| **Click** | Clicks a specified UI element |
| **Type Into** | Enters text in a text box or input field |
| **Get Text** | Extracts text from a UI element |
| **Select Item** | Selects an item from a dropdown |
| **Check/Uncheck** | Toggles a checkbox |
| **Keyboard Shortcuts** | Sends keyboard shortcuts to a UI element |
| **Check App State** | Verifies if a UI element exists (conditional branching) |
| **Take Screenshot** | Captures a screenshot of an app or element |
| **Extract Table Data** | Extracts tabular data from a web page or application |
| **ScreenPlay** | AI-powered UI task execution (last resort for brittle selectors) |

---

## Common Pitfalls

- **Wrong xmlns for UIA activities** — use `xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"` (schema URI). Do NOT use `xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=..."` (CLR namespace) — it fails to resolve `TargetApp`, `TargetAnchorable`, and the `Body` property. Activity doc XAML examples may show the CLR namespace; always replace with the schema URI.
- **Missing Body/ActivityAction on NApplicationCard** — child activities must be placed inside `Body > ActivityAction > Sequence`, not directly as children. The `OCREngine` `ActivityFunc` is also required. Always use `get-default-activity-xaml` for `NApplicationCard` to get the correct structural skeleton.
- **Missing `ScopeSelectorArgument` on `TargetAnchorable`** — every child activity (Click, GetText, etc.) must have `ScopeSelectorArgument` set to the window selector on its `TargetAnchorable`, even when inside an `NApplicationCard` scope. Without it, the activity cannot find the target element at runtime (`NodeNotFoundException`). See [common-pitfalls.md](common-pitfalls.md) for details.
- **Using `CSharpValue` for selector strings** — selector properties (`FullSelectorArgument`, `ScopeSelectorArgument`, `Selector`) accept plain XML-escaped strings as attribute values. Do NOT wrap them in `CSharpValue` expressions. See [xaml-basics-and-rules.md](xaml-basics-and-rules.md) for the correct pattern.
- **Wrong Object Repository references** — never copy references from examples; always discover from `.objects/`
- **SelectItem on web dropdowns** — may fail on custom `<select>` elements; use Type Into as a workaround
- **ScreenPlay overuse** — UITask/ScreenPlay is non-deterministic and slow; use proper selectors first

---

## More Information

- **Full XAML activity reference:** `.local/docs/packages/UiPath.UIAutomation.Activities/` → fallback: `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/activities/`
- **Per-activity docs:** individual `.md` files in the `activities/` folder (e.g., `Click.md`, `TypeInto.md`, `ApplicationCard.md`)
- **Selector & target sub-skills and extras:** glob `../../references/activity-docs/UiPath.UIAutomation.Activities/**/*.md` to discover what's available
- **XAML basics:** [xaml-basics-and-rules.md](xaml-basics-and-rules.md)
- **Common pitfalls:** [common-pitfalls.md](common-pitfalls.md)

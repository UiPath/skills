# UI Automation Guide for RPA Workflows

XAML-specific patterns for UI automation using UiPath UIAutomation activities.

### Prerequisites

See [../shared/uia-prerequisites.md](../shared/uia-prerequisites.md).

**Required package:** `UiPath.UIAutomation.Activities`

> **For full activity details:** always check `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/` first. If unavailable, fall back to the bundled reference at `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/activities/` (pick the version folder closest to what is installed in the project).

@../shared/ui-automation-guide.md

---

## Key Concepts

### Application Card (Use Application/Browser)

Every UI automation workflow starts with an **Application Card** (`uix:NApplicationCard`) that opens or attaches to a desktop application or web browser. All UI activities (Click, TypeInto, GetText, etc.) must be placed inside an Application Card scope.

### Target Configuration

Follow [uia-configure-target-workflows.md](../shared/uia-configure-target-workflows.md) to generate the Application Card's `TargetApp` and each activity's `TargetAnchorable`. The skill returns ready-to-use XAML attributes — copy them exactly into your workflow:

- **Screen XAML** → goes into `<uix:NApplicationCard.TargetApp>` as a `<uix:TargetApp ... />` element
- **Element XAML** → goes into `<uix:NGetText.Target>` (or Click, TypeInto, etc.) as a `<uix:TargetAnchorable ... />` element

When an element is reused across multiple activities, use the same returned XAML snippet for each one.

### Multi-Step UI Flows

See [../shared/uia-multi-step-flows.md](../shared/uia-multi-step-flows.md).

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
| **ScreenPlay** | AI-powered UI task execution (last resort — non-deterministic and slow) |

---

## XAML-Specific Pitfalls

- **Missing `xmlns:uix`** — every UIA workflow needs `xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"` on the root `<Activity>` element

---

## More Information

- **Per-activity docs:** individual `.md` files in the `activities/` folder (e.g., `Click.md`, `TypeInto.md`, `ApplicationCard.md`)
- **XAML basics:** [xaml-basics-and-rules.md](xaml-basics-and-rules.md)
- **Common pitfalls:** [common-pitfalls.md](common-pitfalls.md)

# UI Automation Guide for RPA Workflows

Quick reference for UI automation in XAML/RPA workflows using UiPath UIAutomation activities.

### Prerequisites

See [../shared/uia-prerequisites.md](../shared/uia-prerequisites.md).

**Required package:** `UiPath.UIAutomation.Activities`

> **For full activity details:** always check `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/` first. If unavailable, fall back to the bundled reference at `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/activities/` (pick the version folder closest to what is installed in the project).

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

---

## Configuring Targets (Object Repository)

See [../shared/uia-configure-target-workflows.md](../shared/uia-configure-target-workflows.md) for the full configure-target workflow, rules, indication fallback, and multi-step UI flows.

The skill returns ready-to-use XAML snippets — use them directly in your workflow. When an element is reused across multiple activities, use the same returned snippet for each one.

### Multi-Step UI Flows (Advancing Application State)

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
| **ScreenPlay** | AI-powered UI task execution (last resort for brittle selectors) |

---

## Common Pitfalls

- **Missing `xmlns:uix`** — every UIA workflow needs `xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"`
- **Wrong Object Repository references** — never copy references from examples; always use `uia-configure-target` to get them
- **SelectItem on web dropdowns** — may fail on custom `<select>` elements; use Type Into as a workaround
- **ScreenPlay overuse** — UITask/ScreenPlay is non-deterministic and slow; use proper selectors first

---

## More Information

- **Per-activity docs:** individual `.md` files in the `activities/` folder (e.g., `Click.md`, `TypeInto.md`, `ApplicationCard.md`)
- **XAML basics:** [xaml-basics-and-rules.md](xaml-basics-and-rules.md)
- **Common pitfalls:** [common-pitfalls.md](common-pitfalls.md)

# UI automation guide

Read this file when: you are building UI automation workflows with Click, Type Into, Get Text, or other UIAutomation activities.

### Prerequisites

See [../shared/uia-prerequisites.md](../shared/uia-prerequisites.md).

Required package: `UiPath.UIAutomation.Activities`

For full activity details, check `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/` first. Fallback: `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/activities/`.

## Key concepts

**Application Card** (`NApplicationCard`): every UI workflow starts with this scope. All UI activities must be inside it.

**Target**: each UI activity targets an element via Selector, Anchor, CV (Computer Vision), or Fuzzy selector.

## Configuring targets

See [../shared/uia-configure-target-workflows.md](../shared/uia-configure-target-workflows.md) for the full configure-target workflow.

For multi-step UI flows: [../shared/uia-multi-step-flows.md](../shared/uia-multi-step-flows.md).

## Common activities

| Activity | Description |
|----------|-------------|
| Use Application/Browser | Opens/attaches to app or browser (required scope) |
| Click | Clicks a UI element |
| Type Into | Enters text in an input field |
| Get Text | Extracts text from a UI element |
| Select Item | Selects from a dropdown |
| Check/Uncheck | Toggles a checkbox |
| Keyboard Shortcuts | Sends keyboard shortcuts |
| Check App State | Verifies element existence (conditional branching) |
| Extract Table Data | Extracts tabular data from web/app |

## Common pitfalls

- Missing `xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"` causes namespace errors.
- Never copy Object Repository references from examples. Always use `uia-configure-target`.
- `SelectItem` may fail on custom web dropdowns. Use Type Into as workaround.
- ScreenPlay/UITask is non-deterministic and slow. Use proper selectors first.

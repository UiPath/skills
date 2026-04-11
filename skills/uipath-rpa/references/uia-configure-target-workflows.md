# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: snapshot capture, element discovery, selector generation, selector improvement, and OR registration.

## Prerequisite: Ensure Application State with Servo

Before running `uia-configure-target`, the target application must be visible and showing the correct screen/page. **Use Servo to bring the app into the desired state before any capture.**

This is critical for **multi-page web apps** where the URL wildcard (e.g., `url='https://example.com/*'`) matches multiple browser tabs, causing `snapshot capture` to non-deterministically grab the wrong page.

```bash
# 1. List windows/tabs to find the application
servo targets

# 2. If the app is not open, launch it, then re-run servo targets

# 3. Take a screenshot to verify current state
servo screenshot <b-ref or w-ref>

# 4. If on the wrong page/screen, navigate using Servo:
servo snapshot <b-ref>
servo type <url-bar-ref> "https://example.com/target-page" --clear-before
servo type <url-bar-ref> "[k(enter)]"
# Or click navigation elements to reach the target screen:
servo click <nav-element-ref>

# 5. Close unwanted tabs that share the same URL pattern
# (prevents wildcard conflicts during snapshot capture)

# 6. Re-screenshot to confirm correct state before proceeding
servo screenshot <b-ref or w-ref>
```

**Multi-page web app loop:** When automating multiple pages on the same site, the workflow is:

```
For each page:
  1. Servo → navigate browser to the page URL, verify correct page is showing
  2. uia-configure-target → configure screen + elements for this page
  3. Record the screen and element reference IDs
  4. Repeat for the next page
```

**Wildcard URL trap:** `get-default-selector` generates URL wildcards like `url='https://example.com/*'`. If multiple tabs match this pattern, `snapshot capture` picks whichever matches first (non-deterministic). Always ensure only ONE matching tab is active before capture.

## Execution Model

**Execute `uia-configure-target` steps inline in the main conversation.** Do NOT delegate the entire skill to a subagent. The skill's internal steps already spawn their own subagents.

Why this matters:
- **OR references** must be visible in the main conversation to build the final workflow XAML.
- **Context continuity** — the main conversation tracks which screens and elements are already registered, which avoids duplicate captures and keeps the workflow build coherent.

Read the SKILL.md, then execute each TARGET step yourself. Only spawn `Agent` where the skill explicitly says to (create-selector, improve-selector).

## Skill Location

The UIA skills and activity docs live in the project's local docs folder. Discover them by globbing:
```
Glob: pattern="**/*.md" path="{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/"
```
These are **reference docs to read and follow** — they are NOT invocable as slash commands via the Skill tool. Read the relevant `.md` file and follow its steps using the `uip rpa` CLI commands directly.

## Invocation

To configure a target, read and follow the `uia-configure-target` skill:

- **TargetAnchorable** (element within a window — Click, TypeInto, GetText, etc.):
  `--window <description> --elements <description>`
- **TargetApp** (window only — Use Application/Browser):
  `--window <description>`

To configure multiple elements on the same screen in a single invocation, separate them with `|`. This captures the window once and reuses it for all elements:
`--window <description> --elements "element one | element two | element three"`

The skill will search the Object Repository for existing matches before creating new entries, generate selectors from the live application tree, and register everything in the OR. After completion, retrieve the target references for your workflow.

## Rules

**Do NOT manually call low-level `uip rpa uia` CLI commands** (`snapshot capture`, `snapshot filter`, `selector-intelligence get-default-selector`) to build selectors outside of the skill flow. These are internal tools used *by* the skill — calling them directly skips selector improvement and OR registration, producing fragile selectors that aren't tracked in the project.

**Do NOT launch the target application before running `uia-configure-target`.** The skill's first steps capture the top-level window tree and search for the app. Only if the app is not found in the window list should you launch it — and then re-run the capture. Launching preemptively creates duplicate instances and risks targeting the wrong window.

## Indication Fallback Commands

> **Use these only when `uia-configure-target` is unavailable** (e.g., skill docs missing) **or when elements appear only after user interaction** (e.g., a compose form that opens after clicking a button). These require the user to physically click on the target.

**Workflow:** indicate the screen first, then indicate elements within it.

```bash
# 1. Indicate a screen (creates App automatically if none exists)
uip rpa indicate-application --name "<ScreenName>" --description "<ScreenDescription>" --project-dir "<PROJECT_DIR>" --output json --use-studio

# 2. Indicate elements on that screen (use --parent-id from step 1 result's Data.reference)
uip rpa indicate-element --name "<ElementName>" --activity-class-name "<TypeInto|Click|GetText|...>" --parent-id "<screen-reference>" --project-dir "<PROJECT_DIR>" --output json --use-studio

# 3. Retrieve OR entries after indication
uip rpa uia object-repository get-screen-xaml --reference-id "<screen-reference>"
uip rpa uia object-repository get-element-xaml --reference-id "<element-reference>"
```

Both commands return `{ "Data": { "reference": "..." } }` — use that reference ID for subsequent commands and OR lookups. After indication, Studio regenerates Object Repository files; re-read them to get descriptor paths for your workflow.

<details>
<summary>Full parameter reference</summary>

**indicate-application** — creates a Screen entry in the Object Repository.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | No (recommended) | Screen name (e.g. `"LoginScreen"`) |
| `--parent-id` | No | AppVersion reference ID. Prefer over `--parent-name`. |
| `--parent-name` | No | AppVersion name. Unreliable if names are non-unique. |
| `--activity-class-name` | No | Activity class (e.g. `"UiPath.UIAutomationNext.UI.App"`) |
| `--description` | No | Description for the screen |

When no App exists in `.objects/`, omit `--parent-id` and `--parent-name` — the command creates App + AppVersion automatically. When adding to an existing App, provide `--parent-id` with the **AppVersion** reference.

**indicate-element** — creates an Element entry under an existing Screen.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | Yes | Element name (e.g. `"UsernameField"`) |
| `--parent-id` | One required | Screen reference ID (from `indicate-application` result or OR) |
| `--parent-name` | One required | Alternative — matches by screen name |
| `--activity-class-name` | Yes | Interaction type: `"TypeInto"`, `"Click"`, `"GetText"`, etc. |
| `--description` | No | Description for the element |

**`indicate-application` troubleshooting:**

| Error | Cause | Recovery |
|-------|-------|----------|
| `"No application version found matching parentId=..."` | AppVersion reference is stale or App was never created | Re-read `.objects/` metadata for fresh reference. If no App exists, call `indicate-application` without `--parent-id` — it creates the App automatically |
| `.objects/` has subdirectories but no `.metadata` files | Corrupted/incomplete App from a failed creation | Clear orphan directories and run `indicate-application` without `--parent-id` |

</details>

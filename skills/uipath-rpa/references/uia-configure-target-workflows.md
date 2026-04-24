# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: snapshot capture, element discovery, selector generation, selector improvement, and OR registration.

## Execution Model

**Execute `uia-configure-target` steps inline in the main conversation.** Do NOT delegate the entire skill to a subagent. The skill's internal steps already spawn their own subagents.

Why this matters:
- **OR references** must be visible in the main conversation so they can be attached to workflow activities as the workflow is created — either inline (for single-file workflows) or handed off to write agents (for multi-screen pipelines). See [uia-target-attachment-guide.md](uia-target-attachment-guide.md).
- **Context continuity** — as the main conversation proceeds, it already knows which screens and elements are registered: the references were returned in earlier turns, and the OR itself is queryable via `object-repository get-screens` / `get-elements`. This is what "knowing what's registered" means here — the in-conversation state plus live OR queries — so duplicate captures are avoided and the workflow build stays coherent.

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

**Do NOT manually call low-level `uip rpa uia` CLI commands** (`snapshot capture`, `snapshot filter`, `selector-intelligence get-default-selector`) to build selectors outside of the skill flow. These are internal tools used *by* the skill — calling them directly skips selector improvement and OR registration, producing fragile selectors that aren't registered in the Object Repository.

**Do NOT launch the target application before running `uia-configure-target`.** The skill's first steps capture the top-level window tree and search for the app. Only if the app is not found in the window list should you launch it — and then re-run the capture. Launching preemptively creates duplicate instances and risks targeting the wrong window.

## Indication Fallback Commands

> **Use these only when `uia-configure-target` is unavailable** (e.g., skill docs missing) **or when elements appear only after user interaction** (e.g., a compose form that opens after clicking a button). These require the user to physically click on the target.

**Workflow:** indicate the screen first, then indicate elements within it.

```bash
# 1. Indicate a screen (creates App automatically if none exists)
uip rpa indicate-application --name "<ScreenName>" --description "<ScreenDescription>" --project-dir "<PROJECT_DIR>" --output json
# 2. Indicate elements on that screen (use --parent-id from step 1 result's Data.reference)
uip rpa indicate-element --name "<ElementName>" --activity-class-name "<TypeInto|Click|GetText|...>" --parent-id "<screen-reference>" --project-dir "<PROJECT_DIR>" --output json
```

Both commands return `{ "Data": { "reference": "..." } }` — use that reference ID for OR lookups and target attachment. After indication, Studio regenerates Object Repository files. For coded workflows, re-read `ObjectRepository.cs` to get descriptor paths. For XAML workflows, attach each reference to its activity per [uia-target-attachment-guide.md](uia-target-attachment-guide.md).

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

## Interacting with a Registered Target

After TARGET-8 returns an OR reference ID, you can drive that target directly from the main conversation using `uia interact` — no servo snapshot, no second ref system. This is the preferred way to advance the application state to the next screen when building multi-step flows.

```bash
# Click using the OR reference ID returned by create-screen / create-elements
uip rpa uia interact click --reference-id "<OR_REFERENCE_ID>"

# Type into a target using the OR reference ID
uip rpa uia interact type --reference-id "<OR_REFERENCE_ID>" --text "hello"
```

Alternate input forms:
- `--definition-file-path "<WORK_FOLDER>/Target_N_Definition.json"` — use the definition file (useful before OR registration)
- `--window-selector "<html ... />" --partial-selector "<webctrl ... />"` — raw selectors (ad-hoc, no OR entry)

See [uia-multi-step-flows.md](uia-multi-step-flows.md) for when to use `uia interact` vs servo and the full capture loop.

## Attaching Targets to Workflow Activities

Once targets are registered in the OR (via `uia-configure-target` or indication fallback), attach them to XAML activities per [uia-target-attachment-guide.md](uia-target-attachment-guide.md).

### Multi-Screen Workflows

For XAML workflows spanning multiple screens, use the parallel authoring pipeline. The main conversation passes only OR reference IDs to each write agent — no XAML snippets. The agent handles attachment itself per the shared guide.

See [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md) for prompt templates and the chained dependency model.

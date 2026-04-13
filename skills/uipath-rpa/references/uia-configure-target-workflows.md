# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: snapshot capture, element discovery, selector generation, selector improvement, and OR registration.

## Execution Model

**Execute `uia-configure-target` steps inline in the main conversation.** Do NOT delegate the entire skill to a subagent. The skill's internal steps already spawn their own subagents.

Why this matters:
- **OR references** must be visible in the main conversation so they can be embedded into workflow activities as the workflow is created.
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

```

Both commands return `{ "Data": { "reference": "..." } }` — use that reference ID to retrieve XAML snippets and for OR lookups. After indication, Studio regenerates Object Repository files. For coded workflows, re-read `ObjectRepository.cs` to get descriptor paths. For XAML workflows, use the reference IDs to retrieve XAML snippets and embed them into activities as the workflow is created — see **Embedding OR Entries in XAML Activities** below.

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

## Embedding OR Entries in XAML Activities

After registering targets in the Object Repository (via `uia-configure-target` or indication fallback), retrieve the XAML snippets and embed them directly when creating the workflow. This is more reliable than post-creation linking because it works regardless of intermediate validation errors.

### 1. Get the screen XAML for the ApplicationCard

```bash
uip rpa uia object-repository get-screen-xaml \
  --reference-id "<SCREEN_REFERENCE_ID>" \
  --project-dir "<PROJECT_DIR>"
```

Returns a `<TargetApp>` element. Embed it inside the ApplicationCard:

```xml
<uix:NApplicationCard.TargetApp>
  <!-- paste the returned <TargetApp ... /> here (remove the xmlns attribute — it's inherited from the uix prefix) -->
</uix:NApplicationCard.TargetApp>
```

### 2. Get element XAML for UI activities

```bash
uip rpa uia object-repository get-elements-xaml \
  --reference-ids "<REF_1>,<REF_2>,<REF_3>" \
  --project-dir "<PROJECT_DIR>"
```

Returns `<TargetAnchorable>` elements, one per reference ID, separated by `=== Element Name ===` headers. Embed each inside its activity's `.Target` property:

```xml
<uix:NClick ...>
  <uix:NClick.Target>
    <!-- paste the returned <TargetAnchorable ... /> here (remove the xmlns attribute) -->
  </uix:NClick.Target>
</uix:NClick>

<uix:NTypeInto ...>
  <uix:NTypeInto.Target>
    <!-- paste the returned <TargetAnchorable ... /> here -->
  </uix:NTypeInto.Target>
</uix:NTypeInto>

<uix:NGetText ...>
  <uix:NGetText.Target>
    <!-- paste the returned <TargetAnchorable ... /> here -->
  </uix:NGetText.Target>
</uix:NGetText>
```

| Parameter | Source |
|-----------|--------|
| `<SCREEN_REFERENCE_ID>` | OR screen reference returned by `uia-configure-target` or `indicate-application` |
| `<REF_1>,<REF_2>,...` | Comma-separated OR element references returned by `uia-configure-target` or `indicate-element` |

When an element is used by multiple activities (e.g., the same field clicked and then typed into), use the same `<TargetAnchorable>` snippet in each activity's `.Target` property.

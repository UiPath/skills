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

## Selector & Target Configuration Sub-Skills

For creating, fixing, and configuring selectors and targets, use the CLI commands directly:

```bash
# Indicate a screen (creates App automatically if none exists in .objects/)
uip rpa indicate-application --name "<ScreenName>" --project-dir "<PROJECT_DIR>" --format json

# Indicate an element on a screen (use --parent-id from the indicate-application result)
uip rpa indicate-element --name "<ElementName>" --parent-id "<screen-reference>" --activity-class-name "<ActivityType>" --project-dir "<PROJECT_DIR>" --format json
```

> **Extra references:** The UIA activity-docs version folder may contain additional guides for selector creation, target configuration, CV targeting, and selector improvement. Discover them by globbing:
> ```
> Glob: pattern="**/*.md" path="../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/"
> ```
> These are **reference docs to read and follow** — they are NOT invocable as slash commands via the Skill tool. Read the relevant `.md` file and follow its instructions manually using the CLI commands.

---

## Capturing New UI Targets

When the Object Repository is empty or missing targets for the workflow, use the CLI indication tools:

```bash
# Indicate a screen (creates App automatically if none exists)
uip rpa indicate-application --name "Dashboard" --project-dir "<PROJECT_DIR>" --format json

# Indicate a screen under an existing App
uip rpa indicate-application --name "Dashboard" --parent-id "r-xxxxx/yyyyy" --project-dir "<PROJECT_DIR>" --format json

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

- **Missing `xmlns:uix`** — every UIA workflow needs `xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"`
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

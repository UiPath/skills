# UI Automation Guide

Quick reference for UI automation in UiPath workflows — covers both coded workflows (C#) and XAML/RPA workflows.

## Prerequisites

See [uia-prerequisites.md](uia-prerequisites.md).

**Required package:** `UiPath.UIAutomation.Activities`

> **For full activity details:** check `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`.

---

## Pre-flight: Window Baseline

Before configuring any target or writing any UIA workflow, list top-level windows **once** via `uip rpa uia snapshot inspect` to check whether the target app is open. Full flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. Two outcomes:

- **Target window present** → proceed directly to `uia-configure-target`; it will attach.
- **Target window absent** → launch the app yourself, then proceed directly to `uia-configure-target`; the skill picks up the new window as part of its own capture.

Do not re-inspect or keep polling after the initial check — subsequent capture and attach are `uia-configure-target`'s job. This single pre-flight exists only to drive the launch decision.

**Never use `Get-Process`, `tasklist`, `ps`, WMI, window-title scraping, or any other OS-level process command** to infer app state. They report processes, not UIA-visible windows; they miss background apps and name-mismatched binaries; and they produce wrong launch decisions.

---

## Capturing from Manual Test Steps

When the source is a Test Manager test case, a PDD, or any written list of "Click X / Enter Y / Select Z / Verify W" steps, treat each interaction step as a capture target before writing any workflow code.

1. **Inventory.** Read every step. Each interaction (`Click`, `Enter`, `Type`, `Select`, `Choose`, `Verify visible`, `Read`) maps to **one** Object Repository element. Note: assertions ("Verify text contains X") still need an OR element to read from.
2. **Group by screen state.** Sort steps into screen batches — every step before an action that advances the UI (submit, navigate, dialog confirm) belongs to the current screen; the next batch starts after the advance.
3. **Build the checklist** — three columns per row: `manual step → element name → screen`. Lock the count before opening the app. If the user later adds requirements, capture deltas, do not re-inventory the whole thing.
4. **Capture screen by screen.** Pre-flight Window Baseline (above) → run `uia-configure-target` for the current screen's batch → register each element in the OR before advancing → use the UIA interact CLI to advance → repeat. The "Complete-then-advance" rule from [uia-configure-target-workflows.md § Multi-Step UI Flows](uia-configure-target-workflows.md#multi-step-ui-flows) is mandatory; never advance with elements still un-registered.
5. **Then code.** With every checklist row registered in the OR, write the `.cs` / `.xaml` workflow that calls them in step order. Authoring-phase prerequisites (analyzer rules, project context discovery) run NOW, not earlier.

> Coverage check: after capture, every checklist row must have a matching `Descriptors.<App>.<Screen>.<Element>` path (coded) or OR reference (XAML). Rows without a match indicate a missed capture or an obsolete manual step — reconcile before writing code.

---

## Terminology — what "screen" means

"Screen" appears across UIA docs in three distinct senses. Know which one a passage uses before acting on it.

| Sense | Used in | What it is | Boundary / identity |
|-------|---------|------------|---------------------|
| **Capture screen** | XAML Multi-Screen Authoring (below), [uia-configure-target-workflows.md § Multi-Step UI Flows](uia-configure-target-workflows.md#multi-step-ui-flows) | A distinct UI state that requires its own `uia-configure-target` pass because the app has to be advanced (via the `uip rpa uia interact` CLI) between captures. | Bounded by app advancement — everything captured before the next advance is one capture screen. |
| **OR screen** | Object Repository CLI, `.objects/` layout, `Descriptors.<App>.<Screen>.<Element>`, [uia-configure-target-workflows.md](uia-configure-target-workflows.md) | A data-model entity in the Object Repository, registered via `create-screen` / matched via `get-screens`. | Identified by its window selector. |
| **Screen handle** (coded only) | "Screen Handle Affinity" under § For Coded Workflows | A runtime `UiTargetApp` returned by `uiAutomation.Open` / `Attach`, bound to one OR screen. | Element descriptors are valid only on the handle for their own OR screen. |

**These senses are independent.** Multiple capture screens can map to one OR screen when they share a window selector (e.g., several URLs under the same browser tab if the window selector is URL-neutral). Conversely, one OR screen can produce many screen handles at runtime (one per `Open`/`Attach` call).

**The Multi-Screen Authoring section (§ For XAML Workflows) uses the capture-screen sense.** "2 or more distinct screens" there means 2 or more distinct UI states requiring separate captures — regardless of how many OR screen entries end up getting created.

---

## Mandatory: Generate Targets Before Writing Any UI Code

Before writing ANY target — whether C# (`uiAutomation.Open(...)`, `Descriptors.App.Screen.Element`) or XAML (`<uix:TargetApp>`, `<uix:TargetAnchorable>`):

1. **NEVER hand-write selectors.** Hand-written selectors will have invalid syntax, wrong attribute names, missing required attributes (`SearchSteps`, `ContentHash`, `Reference`), or target the wrong element. They fail validation or break at runtime.
2. **NEVER guess selector attributes** from HTML/DOM structure, element tag names, or CSS classes. Selectors are generated from the live application tree by probing elements — not from source code inspection.
3. **ALWAYS follow the target configuration steps** from [uia-configure-target-workflows.md](uia-configure-target-workflows.md). Use the returned XAML/references exactly as provided. Do not modify selectors, content hashes, or reference IDs.
4. **NEVER substitute external browser automation for UIA.** Do not use PowerShell, Selenium, Playwright, Chrome DevTools Protocol, raw DOM JavaScript, HTTP form posts, or `InvokeCode` to drive a browser/app when the user asked for a UiPath RPA automation. Use those tools only for non-UI setup, diagnostics, or data preparation; the visible application interaction must remain in UiPath UIA activities or coded `uiAutomation` calls backed by Object Repository descriptors.
5. **Use UiPath UIA for exploration.** App/window discovery, UI probing, selector discovery, and target capture must use the UI Automation skills and `uip rpa uia` CLI flows (`uip rpa uia snapshot inspect`, `uia-configure-target`, `uip rpa uia interact`, Object Repository capture). Full flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. Do not use Playwright, Selenium, DOM inspection, process lists, or ad hoc scripts to decide what UI targets/selectors to author.

> This gate applies regardless of how simple the target seems. Even a `<webctrl tag='BODY' />` selector will fail validation without proper attributes. The cost of running target configuration is always lower than debugging hand-written selectors.

---

## Common UIA Pitfalls

- **SelectItem on web dropdowns** — `SelectItem` may fail on custom `<select>` elements. Workaround: use `TypeInto` instead.
- **ScreenPlay overuse** — UITask/ScreenPlay is non-deterministic and slow. Always try proper selectors first.
- **Wrong Object Repository references** — never copy references from examples or other projects. Always use `uia-configure-target` to generate them for the current application state.
- **Using `InjectJsScript` instead of standard activities** — do NOT use `InjectJsScript` when standard UI activities (GetText, Click, TypeInto, ExtractTableData, etc.) with configured targets would work. `InjectJsScript` is a last resort — it's hard to debug, fragile to page changes, and bypasses the Object Repository.
- **Hallucinated keyboard shortcuts instead of UIA targets** — do NOT send keyboard shortcuts (`Ctrl+S`, `Alt+F4`, `Tab` navigation, menu mnemonics, etc.) as a substitute for clicking or typing into a real UI element. `Click` and `TypeInto` against configured targets are deterministic, survive layout changes, and are observable in logs; guessed shortcuts depend on focus, locale, and version. Reserve keyboard shortcuts for genuinely hotkey-only operations (commands with no clickable surface) and confirm the shortcut exists in the live app — never infer from OS convention or muscle memory.
- **Unnecessary `Delay` activities before UIA actions** — UIA activities (`NClick`, `NTypeInto`, `NSelectItem`, `NGoToUrl`, etc.) have embedded target-finding resilience: they retry the selector lookup for a configurable timeout before failing. A `Delay` placed in front of a UIA activity to "let the UI settle" is almost always redundant and inflates workflow runtime without changing correctness. Include `Delay` only when ALL of: the wait is NOT for a UI element that a following UIA activity will target; a concrete non-retry reason exists (post-action animation with no UIA anchor, fixed-duration business pause, background job the UI doesn't reflect); and the caller can state in one sentence why the next UIA activity's built-in retry is insufficient.
- **`Cannot send input ... outside of screen bounds` on hover-revealed elements** — pop-up menu items, autocomplete entries, and dropdown rows that only appear after a hover/click frequently fail under the default input method. Switch the affected activity (or its UIA interact CLI counterpart) to a simulated input method. Available input-method values: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

---

## Configuring Targets (Object Repository)

See [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the full configure-target workflow, rules, indication fallback, and multi-step UI flows.

### Multi-Step UI Flows (Advancing Application State)

See [uia-configure-target-workflows.md § Multi-Step UI Flows](uia-configure-target-workflows.md#multi-step-ui-flows).

---

## Running & Debugging

See [uia-debug-workflow.md](uia-debug-workflow.md).

### Runtime Selector Failures

See [uia-selector-recovery.md](uia-selector-recovery.md).

---

## UIA Activity-Docs Discovery

The UIA activity-docs version folder may contain additional guides (selector creation, target configuration, CV targeting, selector improvement). Discover them by globbing: `Glob: pattern="**/*.md" path="activity-docs/UiPath.UIAutomation.Activities/{closest}/"`. These are **reference docs to read and follow** — they are NOT invocable as slash commands. Read the relevant `.md` file and follow its steps using the `uip rpa` CLI commands directly.

---

## For Coded Workflows

**Service accessor:** `uiAutomation` (type `IUiAutomationAppService`)

For coded-specific API: `.local/docs/packages/UiPath.UIAutomation.Activities/`.

### Workflow Pattern

1. **Open** or **Attach** to an application screen — returns a `UiTargetApp` handle.
2. Use the `UiTargetApp` handle to perform element interactions (Click, TypeInto, GetText, etc.).
3. The `UiTargetApp` is `IDisposable` — use `using` blocks or dispose manually.

### Screen Handle Affinity (Critical)

> "Screen" in this section means the **OR screen** sense (see § Terminology) — the Object Repository entity addressed as `Descriptors.<App>.<Screen>.<Element>`. It is NOT the capture-screen sense used by the Multi-Screen Authoring section below.

**Each `UiTargetApp` handle is bound to a specific OR screen.** Element descriptors can ONLY be used with the handle for the OR screen they belong to. Using a descriptor from OR Screen A on a handle attached to OR Screen B will fail with `"Target name 'X' is not part of the current screen."`.

```csharp
// CORRECT — use Home elements on the homeScreen handle
var homeScreen = uiAutomation.Open(Descriptors.MyApp.Home);
homeScreen.Click(Descriptors.MyApp.Home.Products);   // OK

// Then attach to the next screen for its elements
var formScreen = uiAutomation.Attach(Descriptors.MyApp.Form);
formScreen.TypeInto(Descriptors.MyApp.Form.Email, "test@example.com");  // OK

// WRONG — using a Home element on the Form screen handle
formScreen.Click(Descriptors.MyApp.Home.Loans);  // FAILS
```

**When navigating multi-screen flows:** perform all interactions for one screen before attaching to the next.

### Target Resolution

Each method on `UiTargetApp` accepts targets in multiple forms:
- **`string target`** — a target name defined in the Object Repository screen.
- **`IElementDescriptor elementDescriptor`** — a strongly-typed Object Repository descriptor (e.g., `Descriptors.MyApp.LoginScreen.Username`).
- **`TargetAnchorableModel target`** — accessed via the `UiTargetApp` indexer: `app["targetName"]` or `app[Descriptors.MyApp.Screen.Element]`.
- **`RuntimeTarget target`** — a runtime target returned by `GetChildren` or `GetRuntimeTarget`.

### Finding Descriptors (Mandatory)

**MANDATORY for any workflow that uses `uiAutomation.*` calls.** Follow this decision tree in **strict order** — stop at the first step that yields the descriptor you need.

> **CRITICAL:** Steps 1 → 2 → 3 → 4 MUST be followed sequentially. NEVER skip to Step 4 (UITask).

#### Step 1 — Check the project's Object Repository

Read `<PROJECT_DIR>/.local/.codedworkflows/ObjectRepository.cs`. This file contains a `Descriptors` class with the hierarchy `Descriptors.<App>.<Screen>.<Element>`.

> **Generation requires Studio Desktop.** `ObjectRepository.cs` is regenerated only when Studio Desktop detects a coded workflow file (`.cs` with `[Workflow]` / `[TestCase]`) and reconciles it against the OR — `uip rpa build` alone does NOT regenerate it. If the file is missing or stale after registering elements:
> 1. Confirm Studio Desktop is running against the project (start it with `uip rpa start-studio --project-dir "<PROJECT_DIR>"` if needed).
> 2. Ensure at least one `.cs` coded workflow exists in the project — Studio only triggers regeneration when it sees a coded surface that needs descriptors.
> 3. Save / re-open the project in Studio Desktop to force a regen pass.
>
> A pure-CLI flow with no Studio Desktop attached will not produce `ObjectRepository.cs`. Plan for a Studio Desktop step in any workflow that depends on `Descriptors.*`.

**Important:** Add the ObjectRepository using statement:
```csharp
using <ProjectNamespace>.ObjectRepository;
```

#### Step 2 — Check UILibrary NuGet packages

Look in `project.json` → `dependencies` for packages matching `*.UILibrary`, `*.ObjectRepository`, `*.Descriptors`, or `*.UIAutomation`. Inspect with `uip rpa inspect-package`.

For UILibrary packages, use the **package** namespace, not the project namespace:
```csharp
using <PackageNamespace>.ObjectRepository;
```

#### Step 3 — Configure the target

See [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the full configure-target workflow.

After the skill completes, re-read `ObjectRepository.cs` and search for the returned reference IDs to find the exact `Descriptors.<App>.<Screen>.<Element>` paths.

#### Step 4 — UITask / ScreenPlay (last resort only)

ScreenPlay (`UITask`) is an AI-powered agent that performs UI interactions without precise selectors. Use it **only** when Step 3 selectors are genuinely unreliable.

### Coded-Specific Pitfalls

- **Missing ObjectRepository using** — without `using <ProjectNamespace>.ObjectRepository;`, you get `CS0103: The name 'Descriptors' does not exist in the current context`
- **Screen handle mismatch** — using an element descriptor on the wrong screen handle causes `"Target name 'X' is not part of the current screen."` Always use the correct handle for each screen's elements.

---

## For XAML Workflows

For XAML-specific activity details: `.local/docs/packages/UiPath.UIAutomation.Activities/`.

### Multi-Screen Authoring

> "Screen" in this section means the **capture-screen** sense (see § Terminology) — a distinct UI state that requires its own `uia-configure-target` pass because the app has to be advanced between captures. It is NOT the OR-screen sense. A workflow that ends up with one OR screen entry can still be multi-screen here — what matters is the number of capture passes separated by `uip rpa uia interact` CLI advances, not the number of `.objects/` screen entries that get created.

For workflows spanning multiple capture screens, add each screen's activities to the workflow as its targets are registered in the OR. All UI activities belong inside the `NApplicationCard` scope. Validate with `get-errors` after each batch. See [uia-configure-target-workflows.md § Multi-Step UI Flows](uia-configure-target-workflows.md#multi-step-ui-flows) for the capture loop and the Complete-then-advance rule.

### Key Concepts

#### Application Card (Use Application/Browser)

Every UI automation workflow starts with an **Application Card** (`uix:NApplicationCard`) that opens or attaches to a desktop application or web browser. All UI activities (Click, TypeInto, GetText, etc.) must be placed inside an Application Card scope.

#### Target Configuration

Follow [uia-configure-target-workflows.md](uia-configure-target-workflows.md) to register the Application Card's screen and each activity's elements in the Object Repository. Then write plain activities (NApplicationCard, NClick, NTypeInto, ...) with unique `sap2010:WorkflowViewState.IdRef` attributes and no `.Target` children, and attach targets per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

Do NOT hand-write `<uix:TargetApp>` or `<uix:TargetAnchorable>` XAML from scratch. Attach targets per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md` — never fabricate them.

### Common Activities

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

### XAML-Specific Pitfalls

- **Missing `xmlns:uix`** — every UIA workflow needs `xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"` on the root `<Activity>` element

### More Information

- **Per-activity docs:** individual `.md` files in the `activities/` folder (e.g., `Click.md`, `TypeInto.md`, `ApplicationCard.md`)
- **XAML basics:** [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md)
- **Common pitfalls:** [xaml/common-pitfalls.md](xaml/common-pitfalls.md)

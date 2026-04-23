# UI Automation Guide

Quick reference for UI automation in UiPath workflows — covers both coded workflows (C#) and XAML/RPA workflows.

## Prerequisites

See [uia-prerequisites.md](uia-prerequisites.md).

**Required package:** `UiPath.UIAutomation.Activities`

> **For full activity details:** check `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`.

---

## Terminology — what "screen" means

"Screen" appears across UIA docs in three distinct senses. Know which one a passage uses before acting on it.

| Sense | Used in | What it is | Boundary / identity |
|-------|---------|------------|---------------------|
| **Pipeline screen** | XAML Multi-Screen Gate (below), [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md), [uia-multi-step-flows.md](uia-multi-step-flows.md) | A distinct UI state that requires its own `uia-configure-target` pass because the app has to be advanced (servo / `uia interact`) between captures. | Bounded by app advancement — everything captured before the next advance is one pipeline screen. |
| **OR screen** | Object Repository CLI, `.objects/` layout, `Descriptors.<App>.<Screen>.<Element>`, [uia-configure-target-workflows.md](uia-configure-target-workflows.md) | A data-model entity in the Object Repository, registered via `create-screen` / matched via `get-screens`. | Identified by its window selector. |
| **Screen handle** (coded only) | "Screen Handle Affinity" under § For Coded Workflows | A runtime `UiTargetApp` returned by `uiAutomation.Open` / `Attach`, bound to one OR screen. | Element descriptors are valid only on the handle for their own OR screen. |

**These senses are independent.** Multiple pipeline screens can map to one OR screen when they share a window selector (e.g., several URLs under the same browser tab if the window selector is URL-neutral). Conversely, one OR screen can produce many screen handles at runtime (one per `Open`/`Attach` call).

**The Multi-Screen Gate (§ For XAML Workflows) uses the pipeline-screen sense.** "2 or more distinct screens" there means 2 or more distinct UI states requiring separate captures — regardless of how many OR screen entries end up getting created.

---

## Mandatory: Generate Targets Before Writing Any UI Code

Before writing ANY target — whether C# (`uiAutomation.Open(...)`, `Descriptors.App.Screen.Element`) or XAML (`<uix:TargetApp>`, `<uix:TargetAnchorable>`):

1. **NEVER hand-write selectors.** Hand-written selectors will have invalid syntax, wrong attribute names, missing required attributes (`SearchSteps`, `ContentHash`, `Reference`), or target the wrong element. They fail validation or break at runtime.
2. **NEVER guess selector attributes** from HTML/DOM structure, element tag names, or CSS classes. Selectors are generated from the live application tree by probing elements — not from source code inspection.
3. **ALWAYS follow the target configuration steps** from [uia-configure-target-workflows.md](uia-configure-target-workflows.md). Use the returned XAML/references exactly as provided. Do not modify selectors, content hashes, or reference IDs.

> This gate applies regardless of how simple the target seems. Even a `<webctrl tag='BODY' />` selector will fail validation without proper attributes. The cost of running target configuration is always lower than debugging hand-written selectors.

---

## Common UIA Pitfalls

- **SelectItem on web dropdowns** — `SelectItem` may fail on custom `<select>` elements. Workaround: use `TypeInto` instead.
- **ScreenPlay overuse** — UITask/ScreenPlay is non-deterministic and slow. Always try proper selectors first.
- **Wrong Object Repository references** — never copy references from examples or other projects. Always use `uia-configure-target` to generate them for the current application state.
- **Launching the app before configuring targets** — do NOT launch the target application before running `uia-configure-target`. The skill captures the window tree first and only launches if the app isn't found. Launching preemptively risks targeting the wrong window.
- **Using `InjectJsScript` instead of standard activities** — do NOT use `InjectJsScript` when standard UI activities (GetText, Click, TypeInto, ExtractTableData, etc.) with configured targets would work. `InjectJsScript` is a last resort — it's hard to debug, fragile to page changes, and bypasses the Object Repository.

---

## Configuring Targets (Object Repository)

See [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the full configure-target workflow, rules, indication fallback, and multi-step UI flows.

### Multi-Step UI Flows (Advancing Application State)

See [uia-multi-step-flows.md](uia-multi-step-flows.md).

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

> "Screen" in this section means the **OR screen** sense (see § Terminology) — the Object Repository entity addressed as `Descriptors.<App>.<Screen>.<Element>`. It is NOT the pipeline-screen sense used by the Multi-Screen Gate below.

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

Read `<PROJECT_DIR>/.local/.codedworkflows/ObjectRepository.cs`. This file is auto-generated by Studio and contains a `Descriptors` class with the hierarchy `Descriptors.<App>.<Screen>.<Element>`.

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

### Multi-Screen Gate (MANDATORY)

> "Screen" in this section means the **pipeline-screen** sense (see § Terminology) — a distinct UI state that requires its own `uia-configure-target` pass because the app has to be advanced between captures. It is NOT the OR-screen sense. A workflow that ends up with one OR screen entry can still be multi-screen here — what triggers the gate is the number of capture passes separated by servo / `uia interact` advances, not the number of `.objects/` screen entries that get created.

If this workflow requires **2 or more distinct capture passes** (i.e., 2 or more pipeline screens) via `uia-configure-target`, you **MUST** use the parallel authoring pipeline in [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md). Do NOT fall through to the single-pass patterns below. Single pipeline screen only → skip the pipeline and author in one pass.

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

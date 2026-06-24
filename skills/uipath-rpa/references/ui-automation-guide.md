# UI Automation Guide

Quick reference for UI automation in UiPath workflows — covers both coded workflows (C#) and XAML/RPA workflows.

## Prerequisites

[uia-prerequisites.md](uia-prerequisites.md) MUST be read IN FULL first.

**Required package:** `UiPath.UIAutomation.Activities`

> **For full activity details:** check `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`.

---

## Pre-flight: Window Baseline

Before configuring any target or writing any UIA workflow, list top-level windows **once** via the UIA snapshot CLI to check whether the target app is open. Subcommand and flags: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. Two outcomes:

- **Target window present** → proceed directly to `uia-configure-target`; it will attach.
- **Target window absent** → launch the app yourself, then proceed directly to `uia-configure-target`; the skill picks up the new window as part of its own capture.

Do not re-inspect or keep polling after the initial check — subsequent capture and attach are `uia-configure-target`'s job. This single pre-flight exists only to drive the launch decision.

**Never use `Get-Process`, `tasklist`, `ps`, WMI, window-title scraping, or any other OS-level process command** to infer app state. They report processes, not UIA-visible windows; they miss background apps and name-mismatched binaries; and they produce wrong launch decisions.

---

## Capturing from Manual Test Steps

When the source is a Test Manager test case, a PDD, or any written list of "Click X / Enter Y / Select Z / Verify W" steps, treat each interaction step as a capture target before writing any workflow code.

1. **Inventory.** Read every step. Each interaction (`Click`, `Enter`, `Type`, `Select`, `Choose`, `Verify visible`, `Read`) maps to **one** Object Repository element. Note: assertions ("Verify text contains X") still need an Object Repository element to read from.
2. **Group by screen state.** Sort steps into screen batches — every step before an action that advances the UI (submit, navigate, dialog confirm) belongs to the current screen; the next batch starts after the advance.
3. **Build the checklist** — three columns per row: `manual step → element name → screen`. Lock the count before opening the app. If the user later adds requirements, capture deltas, do not re-inventory the whole thing.
4. **Capture screen by screen.** Pre-flight Window Baseline (above) → run `uia-configure-target` for the current screen's batch → register each element in the Object Repository before advancing → use the UIA interact CLI to advance → repeat. The "Complete-then-advance" rule from [uia-configure-target-workflows.md § Multi-Step UI Flows](uia-configure-target-workflows.md) is mandatory; never advance with elements still un-registered.
5. **Then code.** With every checklist row registered in the Object Repository, write the `.cs` / `.xaml` workflow that calls them in step order. Authoring-phase prerequisites (analyzer rules, project context discovery) run NOW, not earlier.

> Coverage check: after capture, every checklist row must have a matching `Descriptors.<App>.<Screen>.<Element>` path (coded) or Object Repository reference (XAML). Rows without a match indicate a missed capture or an obsolete manual step — reconcile before writing code.

---

## Terminology — what "screen" means

"Screen" appears across UIA docs in three distinct senses. Know which one a passage uses before acting on it.

| Sense | Used in | What it is | Boundary / identity |
|-------|---------|------------|---------------------|
| **Capture screen** | XAML Multi-Screen Authoring (below), [uia-configure-target-workflows.md § Multi-Step UI Flows](uia-configure-target-workflows.md) | A distinct UI state that requires its own `uia-configure-target` pass because the app has to be advanced (via the `uip rpa uia interact` CLI) between captures. | Bounded by app advancement — everything captured before the next advance is one capture screen. |
| **Object Repository screen** | Object Repository CLI, `.objects/` layout, `Descriptors.<App>.<Screen>.<Element>`, [uia-configure-target-workflows.md](uia-configure-target-workflows.md) | A data-model entity in the Object Repository, registered and matched via the Object Repository CLI. | Identified by its window selector. |
| **Screen handle** (coded only) | "Screen Handle Affinity" under § For Coded Workflows | A runtime `UiTargetApp` returned by `uiAutomation.Open` / `Attach`, bound to one Object Repository screen. | Element descriptors are valid only on the handle for their own Object Repository screen. |

**These senses are independent.** Multiple capture screens can map to one Object Repository screen when they share a window selector (e.g., several URLs under the same browser tab if the window selector is URL-neutral). Conversely, one Object Repository screen can produce many screen handles at runtime (one per `Open`/`Attach` call).

**The Multi-Screen Authoring section (§ For XAML Workflows) uses the capture-screen sense.** "2 or more distinct screens" there means 2 or more distinct UI states requiring separate captures — regardless of how many Object Repository screen entries end up getting created.

---

## Placeholder-Selector Stub Pattern

Sometimes you must generate a UI automation workflow without live app access — the app is not installed on the build machine, the agent has no GUI, or the user has explicitly deferred target capture to a developer who will run Indicate later. In that case, the workflow ships with placeholder selectors. The pattern below is the **only** acceptable shape.

### Rule

When live capture is unavailable, write the **real** UIA activity (XAML `<NApplicationCard>` / `<NTypeInto>` / `<NClick>` / `<NGetText>` / etc., or coded `uiAutomation.Open` / `Attach` / `TypeInto` / `Click`) with the target descriptor's selector left as a placeholder and a `TODO Indicate` marker embedded in the activity's `DisplayName` (XAML) or in a `// TODO[Indicate]` comment immediately adjacent to the call (coded).

Do **NOT** replace the activity itself with a `Log` call.

### Why this matters

A `Log("LoginWorkflow: type username")` stub:

- Passes `uip rpa validate` (no UIA activity, no selectors to validate).
- Passes `uip rpa build` (just a string in a Log activity).
- Runs cleanly via `uip rpa run` (the Log activity emits a message).
- **Does nothing.** The workflow looks complete to the validator, looks complete to a CI smoke test, and silently fails to perform the actual automation.

A real `<uix:NTypeInto>` activity with placeholder selector + `TODO Indicate` marker:

- Build/validate may surface "selector incomplete" warnings — useful, since they tell the developer what is left to do.
- The activity is wired into the workflow's control flow, package dependencies, scope, and Object Repository registration plumbing. The developer's only remaining work is **Indicate**.
- The TODO marker is visible in Studio's designer pane and grep-able in the file.
- The cost of "what does this stub actually need from the developer?" drops from "read this carefully and infer" to "click Indicate on the marked activities."

### XAML example

```xml
<uix:NApplicationCard ApplicationWindow="{x:Null}"
                      DisplayName="TODO Indicate — Use Application/Browser (ACME WI app)"
                      sap2010:WorkflowViewState.IdRef="NApplicationCard_1">
    <uix:NApplicationCard.Body>
        <Sequence sap2010:WorkflowViewState.IdRef="Sequence_1">
            <uix:NTypeInto DisplayName="TODO Indicate — Type Username"
                           Text="[in_Username]"
                           sap2010:WorkflowViewState.IdRef="NTypeInto_1" />
            <uix:NTypeInto DisplayName="TODO Indicate — Type Password"
                           Text="[in_Password]"
                           sap2010:WorkflowViewState.IdRef="NTypeInto_2" />
            <uix:NClick DisplayName="TODO Indicate — Click Login"
                        sap2010:WorkflowViewState.IdRef="NClick_1" />
            <uix:NGetText DisplayName="TODO Indicate — Read WIID field"
                          Text="[out_WIID]"
                          sap2010:WorkflowViewState.IdRef="NGetText_1" />
        </Sequence>
    </uix:NApplicationCard.Body>
</uix:NApplicationCard>
```

What this gives the developer:
- `NApplicationCard` is in the right place (entry point of the screen).
- Three `NTypeInto` / `NClick` / `NGetText` are wired into the Sequence in the right order.
- `Text` arguments are bound to the right input/output variables.
- Each activity's `DisplayName` is `TODO Indicate — <human description>`. Studio shows this on the canvas; the developer clicks each and runs Indicate.
- Once Indicate is run, `DisplayName` is updated, `Target` becomes a real descriptor, and the workflow is shippable.

What you must NOT do:

```xml
<!-- WRONG: replaces the actual activity with a log stub -->
<ui:LogMessage Message="LoginWorkflow: type username" Level="Info" />
<!-- TODO[selectors]: replace this with an actual TypeInto activity once capture is done -->
```

That XAML compiles, validates, runs — and does nothing. A re-run of the build pipeline at a later date silently ships the same broken automation.

### Coded example

```csharp
[Workflow]
public void Execute(string in_Username, string in_Password, out string out_WIID)
{
    // TODO[Indicate]: attach to the ACME WI app — replace placeholder with Descriptors.<App>.<Screen>
    using var app = uiAutomation.Open(/* TODO[Indicate]: Descriptors.AcmeWi.Login */);

    // TODO[Indicate]: target the Username field
    app.TypeInto(/* TODO[Indicate]: Descriptors.AcmeWi.Login.Username */ "username-placeholder", in_Username);

    // TODO[Indicate]: target the Password field
    app.TypeInto(/* TODO[Indicate]: Descriptors.AcmeWi.Login.Password */ "password-placeholder", in_Password);

    // TODO[Indicate]: target the Login button
    app.Click(/* TODO[Indicate]: Descriptors.AcmeWi.Login.LoginButton */ "login-button-placeholder");

    // TODO[Indicate]: target the WIID readout field on the next screen
    using var home = uiAutomation.Attach(/* TODO[Indicate]: Descriptors.AcmeWi.Home */);
    out_WIID = home.GetText(/* TODO[Indicate]: Descriptors.AcmeWi.Home.WIIDField */ "wiid-field-placeholder");
}
```

What this gives the developer:
- The actual `uiAutomation.Open` / `Attach` / `TypeInto` / `Click` / `GetText` calls are in the right order with the right argument bindings.
- Every `TODO[Indicate]` marker tells the developer the exact descriptor to wire up.
- The placeholder string argument lets the project build and `uip rpa packages inspect` succeed; once Indicate runs and `Descriptors.<App>.<Screen>.<Element>` exists, replace the placeholder string with the descriptor reference.

What you must NOT do:

```csharp
[Workflow]
public void Execute(string in_Username, string in_Password, out string out_WIID)
{
    // TODO[selectors]: replace these with real uiAutomation calls once Object Repository is populated
    Log("LoginWorkflow: type username " + in_Username);
    Log("LoginWorkflow: type password");
    Log("LoginWorkflow: click Login");
    Log("LoginWorkflow: read WIID");
    out_WIID = "";
}
```

This compiles, validates, runs, and does nothing. It is the most expensive kind of stub.

### When the rule does NOT apply

- **Live capture is available.** Run `uia-configure-target` / Indicate first; the workflow ships with real descriptors. No stub pattern needed.
- **The activity is not UI.** Logging is fine for actual logging steps (e.g., "Log the transaction ID before processing"). The rule applies only to UI-interaction steps that, in a finished workflow, would be `NTypeInto` / `NClick` / `NGetText` / etc.

### Acceptance check

Before declaring a stub-mode workflow done, re-read every UI-interaction step in the PDD / SDD and confirm that the workflow contains a **real UIA activity** (XAML element or coded `uiAutomation.*` call) for each one — not a Log call. Grep for `Log\(` and `LogMessage` inside the workflow body; for every match, verify it represents an actual logging step, not a substitute for a UI action.

---

## Mandatory: Generate Targets Before Writing Any UI Code

Before writing ANY target — whether C# (`uiAutomation.Open(...)`, `Descriptors.App.Screen.Element`) or XAML (`<uix:TargetApp>`, `<uix:TargetAnchorable>`):

1. **NEVER hand-write selectors.** Hand-written selectors will have invalid syntax, wrong attribute names, missing required attributes (`SearchSteps`, `ContentHash`, `Reference`), or target the wrong element. They fail validation or break at runtime.
2. **NEVER guess selector attributes** from HTML/DOM structure, element tag names, or CSS classes. Selectors are generated from the live application tree by probing elements — not from source code inspection.
3. **ALWAYS follow the target configuration steps** from [uia-configure-target-workflows.md](uia-configure-target-workflows.md). Use the returned XAML/references exactly as provided. Do not modify selectors, content hashes, or reference IDs.
4. **NEVER substitute external browser automation for UIA.** Do not use PowerShell, Selenium, Playwright, Chrome DevTools Protocol, raw DOM JavaScript, HTTP form posts, or `InvokeCode` to drive a browser/app when the user asked for a UiPath RPA automation. Use those tools only for non-UI setup, diagnostics, or data preparation; the visible application interaction must remain in UiPath UIA activities or coded `uiAutomation` calls backed by Object Repository descriptors.
5. **Use UiPath UIA for exploration.** App/window discovery, UI probing, selector discovery, and target capture must use the UI Automation skills and the `uip rpa uia` CLI flows (the UIA snapshot CLI, `uia-configure-target`, the `uip rpa uia interact` CLI, Object Repository capture). Subcommands and flags: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. Do not use Playwright, Selenium, DOM inspection, process lists, or ad hoc scripts to decide what UI targets/selectors to author.

> This gate applies regardless of how simple the target seems. Even a `<webctrl tag='BODY' />` selector will fail validation without proper attributes. The cost of running target configuration is always lower than debugging hand-written selectors.

### Don't override a step whose purpose is to replace your judgment

When a procedure exists specifically to check something against ground truth, doing it by your own judgment instead — because that seems faster or "low-risk" — defeats the point: your call is verified against nothing. It is also false economy, since a shortcut that silently produces a wrong result costs far more to debug later than the step would have cost up front. Being terse and following the steps are not in tension — cut narration and redundant round-trips, never the correctness step itself.

---

## Common UIA Pitfalls

- **SelectItem on web dropdowns** — use `SelectItem` for native HTML `<select>` elements (deterministic). It fails on custom dropdown widgets (div/`<ul>`/ARIA hierarchies that only *look* like a `<select>`) — there, click to open and click the option, or use `TypeInto`. Detail: [uia-elements-interaction-guide.md § Web Controls](uia-elements-interaction-guide.md).
- **ScreenPlay overuse** — UITask/ScreenPlay is non-deterministic and slow. Always try proper selectors first.
- **Wrong Object Repository references** — never copy references from examples or other projects. Always use `uia-configure-target` to generate them for the current application state.
- **Using `InjectJsScript` instead of standard activities** — do NOT use `InjectJsScript` when standard UI activities (GetText, Click, TypeInto, ExtractTableData, etc.) with configured targets would work. `InjectJsScript` is a last resort — it's hard to debug, fragile to page changes, and bypasses the Object Repository.
- **Hallucinated keyboard shortcuts instead of UIA targets** — do NOT send keyboard shortcuts (`Ctrl+S`, `Alt+F4`, `Tab` navigation, menu mnemonics, etc.) as a substitute for clicking or typing into a real UI element. `Click` and `TypeInto` against configured targets are deterministic, survive layout changes, and are observable in logs; guessed shortcuts depend on focus, locale, and version. Reserve keyboard shortcuts for genuinely hotkey-only operations (commands with no clickable surface) and confirm the shortcut exists in the live app — never infer from OS convention or muscle memory.
- **Chaining keystrokes in one `NKeyboardShortcuts` after one navigates away faults on a stale node.** The activity resolves its `Target` **once**; if the first shortcut destroys/replaces that element (a navigation key that changes the view), a second shortcut chained in the same activity (multi-shortcut `Shortcuts` string or `DelayBetweenShortcuts`) hits the stale node and throws `InvalidNodeException: "The UI element is invalid..."`. Example: Explorer `Alt+Up` (go to parent, auto-selecting the current folder) + `Alt+Enter` (open Properties) in one activity targeting "Items View" — `Alt+Up` navigates, then `Alt+Enter` faults on the destroyed node. **Fix:** use **separate** `NKeyboardShortcuts` activities so the follow-up **re-resolves** its target against the new screen, plus a small `DelayBefore` to let it settle.
- **Unnecessary `Delay` activities before UIA actions** — UIA activities (`NClick`, `NTypeInto`, `NSelectItem`, `NGoToUrl`, etc.) have embedded target-finding resilience: they retry the selector lookup for a configurable timeout before failing. A `Delay` placed in front of a UIA activity to "let the UI settle" is almost always redundant and inflates workflow runtime without changing correctness. Include `Delay` only when ALL of: the wait is NOT for a UI element that a following UIA activity will target; a concrete non-retry reason exists (post-action animation with no UIA anchor, fixed-duration business pause, background job the UI doesn't reflect); and the caller can state in one sentence why the next UIA activity's built-in retry is insufficient. A button that is present but **disabled** during async validation/load/refresh is a separate case retry does not cover — use the activity's `DelayBefore`/`DelayAfter` *properties* (not a `Delay` activity): [uia-elements-interaction-guide.md § Web Controls](uia-elements-interaction-guide.md).
- **`Cannot send input ... outside of screen bounds` on hover-revealed elements** — pop-up menu items, autocomplete entries, and dropdown rows that only appear after a hover/click frequently fail under the default input method. Switch the affected activity (or its UIA interact CLI counterpart) to a simulated input method. Available input-method values: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.
- **`HealingAgentBehavior` enum split between card and child activities.** `NApplicationCard` (Use Application/Browser) accepts `NHealingAgentBehavior` — values `Job`, `Disabled`, `RecommendationOnly`. Child activities (`NClick`, `NTypeInto`, `NCheckState`, etc.) accept `NChildHealingAgentBehavior`, which adds `SameAsCard`. Putting `SameAsCard` on the card itself fails with `Failed to create a 'HealingAgentBehavior' from the text 'SameAsCard'`. When introducing a new card (e.g., a nested card for a sign-in subprocess), set its `HealingAgentBehavior` to `Job`/`Disabled`/`RecommendationOnly` — never copy the value from a child activity. Confirm via `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/activities/common/NHealingAgentBehavior.md` and `NChildHealingAgentBehavior.md`.

---

## Control-Specific Interaction Patterns

> **MANDATORY — read and apply before authoring.** Before writing any `TypeInto`, `SelectItem`, or `Click` (XAML `NTypeInto` / `NSelectItem` / `NClick`, or coded `uiAutomation.*`) against a captured target, classify the control. If **any** target is a date / time input, a dropdown, or a button that can be disabled during async work, you MUST read [uia-elements-interaction-guide.md](uia-elements-interaction-guide.md) IN FULL and apply it **before** authoring that activity — the same bar as target capture ([§ Configuring Targets](#configuring-targets-object-repository)). The correct technique is type-specific and documented there: a date field must be typed in its **displayed** format (not ISO) via a key-event method, dropdowns split into native (`SelectItem`) vs. custom (click-to-open), and async-disabled buttons need `DelayBefore`. Apply the documented method up front — do not guess a value (e.g. ISO into a date field) and iterate against the running app.

After a target is captured, these control types need type-specific handling to drive correctly:

- **Date / formatted date-time inputs** — type the field's **displayed** format (e.g. en-US `MM/DD/YYYY`), not the ISO `value`.
- **Dropdowns** — native HTML `<select>` → `SelectItem`; custom widgets → click-to-open + click option / `TypeInto`.
- **Buttons disabled during async ops** — present but `disabled` during validation/load/refresh; use the activity's `DelayBefore`/`DelayAfter` properties (not a `Delay` activity).

Patterns are organized by UI technology (currently web controls, `webctrl`): [uia-elements-interaction-guide.md](uia-elements-interaction-guide.md).

---

## Configuring Targets (Object Repository)

[uia-configure-target-workflows.md](uia-configure-target-workflows.md) MUST be read IN FULL first — it covers the configure-target workflow, rules, indication fallback, and multi-step UI flows.

### Multi-Step UI Flows (Advancing Application State)

Procedure: [uia-configure-target-workflows.md § Multi-Step UI Flows](uia-configure-target-workflows.md) — the capture loop and Complete-then-advance rule.

---

## Object Repository as a Published UI Library

Selector breakage is the #1 maintenance cost in UI automation. A **UI Library** is a published library project whose Object Repository ships inside the `.nupkg` — descriptors defined once, consumed by every automation against the same application. Fix a descriptor once, bump the version, and all consumers inherit the fix.

### Hierarchy and naming

```
Application (InvoicePortal)
  └── Screen (LoginPage)
      └── Element (UsernameField)
```

- Reference form: `App.Screen.Element` — `InvoicePortal.LoginPage.UsernameField`
- Business-meaningful PascalCase element names: `SubmitOrderButton`, not `Button32`
- One descriptor per distinct UI element; screens mirror the application's logical screens

### Extract-and-publish pattern

Precondition: the source project has captured descriptors (`.objects/` content). If it has none, capture targets first ([§ Configuring Targets](#configuring-targets-object-repository)) — there is nothing to promote, and hand-writing descriptors is forbidden.

1. Develop the first process against its **local** Object Repository, configuring targets as usual ([§ Configuring Targets](#configuring-targets-object-repository)).
2. Promote the reusable descriptors into a dedicated UI Library project — a library project ([library-authoring-guide.md](library-authoring-guide.md)) holding the shared Object Repository; pack and upload per [library-authoring-guide.md § Pack & Publish](library-authoring-guide.md). Concrete Object Repository manipulation steps: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`.
3. **One UI Library per corporate application** (SAP, Salesforce, Workday) — an update to one app's selectors must not force re-deployment of another's.
4. New automations against that application consume the UI Library from the start. Process-specific one-off descriptors stay in the local Object Repository.

### Consumption

Install the UI Library as a package dependency; its descriptors appear under **UI Libraries** in the Object Repository and are targetable like local descriptors. Coded workflows resolve them via [§ Finding Descriptors Step 2](#step-2--check-uilibrary-nuget-packages). Selector updates propagate by bumping the dependency version — no per-workflow changes.

### Update rules — MANDATORY

1. **Update descriptors in place — NEVER delete-and-re-add an element.** The element-to-activity link is identity-based; deleting the element severs it and every consumer activity bound to it breaks, even if a same-named element is re-created.
2. **Version by SemVer** ([library-authoring-guide.md § Versioning](library-authoring-guide.md)): selector fix without renaming = patch; element/screen rename or restructure = breaking = major.
3. **Promote accepted healing fixes.** When a selector recovery ([§ Runtime Selector Failure Recovery](#runtime-selector-failure-recovery)) is accepted in a workflow that consumes a shared UI Library, apply the fix in the UI Library and bump the version — do not re-fix the same selector consumer by consumer.

---

## Running UI Automation Workflows

**Always use `uip rpa debug start`** (not `uip rpa run`) when running workflows with UI automation. A debug session pauses on error instead of tearing down the application, leaving the UI state available for inspection.

**Every debug run** must follow this procedure to prevent stale windows from accumulating or being reused in a dirty state:

1. **Record the window baseline** — list top-level windows via the UIA snapshot CLI and note which w-refs and titles are already present. Subcommand and flags: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.
2. **Run the workflow:**
   ```bash
   uip rpa debug start --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
   ```
   If the run fails, [Runtime Selector Failure Recovery](#runtime-selector-failure-recovery) spawns the `uia-improve-selector` subagent — this is the **only** correct recovery path. Do not hand-edit selectors in the XAML file.
3. **When done** (success or failure) — **cancel the debug session:**
   ```bash
   uip rpa execution cancel --project-dir "<PROJECT_DIR>" --output json
   ```
4. **List windows again** via the UIA snapshot CLI.
5. **Diff before vs after.** Any window present now that was NOT in the baseline was opened by the workflow. Close each such window via the `uip rpa uia interact` CLI (see `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md` for the close subcommand and its flags).

Skipping steps 4-5 causes the next run's open-if-not-open behavior to reuse a stale window in whatever state it was left in, or -- if the selector doesn't match -- to spawn a duplicate instance.

### Runtime Selector Failure Recovery

"UI element not found", "UI element is invalid", element not on screen -- these surface at runtime, not during static validation. They occur when a selector was captured against one app state but the DOM changed by the time the activity executes.

When a workflow fails at runtime with a selector error:

1. **The app is already in the right state.** The debug session paused at the failing activity, so the app's current DOM reflects the state that activity needs to target.
2. **Identify the failing element** -- read the error to find which descriptor/element failed.
3. **Read the window selector** -- from the Object Repository files, find the screen's selector that scopes the failing element.
4. **Run the `uia-improve-selector` skill in recover mode.** Read `<PROJECT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-improve-selector/USAGE.md`, pick the appropriate invocation form for this context, run the staging CLI command from that form, spawn a subagent with the Agent tool to run the skill in recover mode against the staged folder, then run the write-back CLI command from the same form to persist the recovered selector.
5. **Clean up and re-run** -- follow the [Running UI Automation Workflows](#running-ui-automation-workflows) procedure (stop, diff, close leaked windows, re-run).

Repeat until the workflow completes successfully. Each failure advances the app to the next problematic state, making recovery self-correcting.

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

> "Screen" in this section means the **Object Repository screen** sense (see § Terminology) — the Object Repository entity addressed as `Descriptors.<App>.<Screen>.<Element>`. It is NOT the capture-screen sense used by the Multi-Screen Authoring section below.

**Each `UiTargetApp` handle is bound to a specific Object Repository screen.** Element descriptors can ONLY be used with the handle for the Object Repository screen they belong to. Using a descriptor from Object Repository Screen A on a handle attached to Object Repository Screen B will fail with `"Target name 'X' is not part of the current screen."`.

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

> **Generation requires Studio Desktop.** `ObjectRepository.cs` is regenerated only when Studio Desktop detects a coded workflow file (`.cs` with `[Workflow]` / `[TestCase]`) and reconciles it against the Object Repository — `uip rpa build` alone does NOT regenerate it. If the file is missing or stale after registering elements:
> 1. Confirm Studio Desktop is running against the project (start it with `uip rpa studio start --project-dir "<PROJECT_DIR>"` if needed).
> 2. Ensure at least one `.cs` coded workflow exists in the project — Studio only triggers regeneration when it sees a coded surface that needs descriptors.
> 3. Save / re-open the project in Studio Desktop to force a regen pass.
>
> A pure-CLI flow with no Studio Desktop attached will not produce `ObjectRepository.cs`. Plan for a Studio Desktop step in any workflow that depends on `Descriptors.*`.

When `ObjectRepository.cs` is missing or stale (see above), enumerate the project's registered apps/screens/elements as JSON with `uip rpa object-repository get` ([cli-reference.md § object-repository](cli-reference.md#object-repository)) — it reads the saved Object Repository without a Studio Desktop regen. Use it to confirm a screen/element exists before authoring; the strongly-typed `Descriptors.<App>.<Screen>.<Element>` reference still comes from `ObjectRepository.cs`.

**Important:** Add the ObjectRepository using statement:
```csharp
using <ProjectNamespace>.ObjectRepository;
```

#### Step 2 — Check UILibrary NuGet packages

Look in `project.json` → `dependencies` for packages matching `*.UILibrary`, `*.ObjectRepository`, `*.Descriptors`, or `*.UIAutomation`. Inspect with `uip rpa packages inspect`.

To list the apps/screens/elements a library actually exposes — not just its assembly API — read its Object Repository directly with `uip rpa object-repository get-library` ([cli-reference.md § object-repository](cli-reference.md#object-repository)), pointing at the library `.nupkg` path(s).

For UILibrary packages, use the **package** namespace, not the project namespace:
```csharp
using <PackageNamespace>.ObjectRepository;
```

#### Step 3 — Configure the target

[uia-configure-target-workflows.md](uia-configure-target-workflows.md) MUST be read IN FULL first.

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

> "Screen" in this section means the **capture-screen** sense (see § Terminology) — a distinct UI state that requires its own `uia-configure-target` pass because the app has to be advanced between captures. It is NOT the Object Repository screen sense. A workflow that ends up with one Object Repository screen entry can still be multi-screen here — what matters is the number of capture passes separated by `uip rpa uia interact` CLI advances, not the number of `.objects/` screen entries that get created.

For workflows spanning multiple capture screens, add each screen's activities to the workflow as its targets are registered in the Object Repository. All UI activities belong inside the `NApplicationCard` scope. Validate with `validate` after each batch. [uia-configure-target-workflows.md](uia-configure-target-workflows.md) MUST be read IN FULL first (see § Multi-Step UI Flows for the capture loop and the Complete-then-advance rule).

### Key Concepts

#### Application Card (Use Application/Browser)

Every UI automation workflow starts with an **Application Card** (`uix:NApplicationCard`) that opens or attaches to a desktop application or web browser. All UI activities (Click, TypeInto, GetText, etc.) must be placed inside an Application Card scope.

> **Default to ONE Application Card — choose simplicity.** A single `ByInstance` card (the default) covers the *entire* application instance: main window, dialogs, pop-ups, menus, and owned child windows. Add a second or nested card **only** to reach a genuinely *different* application (a different process/instance), or when `ByInstance` provably fails to attach to or find an owned window. Do **NOT** add a card per window, per dialog, or per Object Repository screen. More cards = more scope to keep aligned and more failure surface, for no benefit when the windows share one instance.

##### Window Attach Mode

`NApplicationCard` attaches via the `AttachMode` property (type `NAppAttachMode`, default `ByInstance`), which controls where inner activities search for their targets. Change it per the Application Card docs in the package docs (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/activities/ApplicationCard.md`).

**`ByInstance` — Application Instance (default, preferred).** The card finds the window from its selector, then attaches to ALL windows of that application instance (main window, dialogs, child windows). Per activity: it locates the target window among the instance's windows using the activity target's **scope selector**, then searches the target inside that window.

Use when the app opens separate windows (e.g. a dialog) — one card covers all of them; no second card needed. An activity whose scope selector targets the dialog window finds its element there.

```xml
<uix:NApplicationCard AttachMode="ByInstance" DisplayName="Use App (Invoice app)"
                      sap2010:WorkflowViewState.IdRef="NApplicationCard_1" Version="V2">
    <uix:NApplicationCard.Body>
        <Sequence sap2010:WorkflowViewState.IdRef="Sequence_1">
            <!-- scope selector targets the main window -->
            <uix:NClick DisplayName="Click New Invoice" sap2010:WorkflowViewState.IdRef="NClick_1" />
            <!-- scope selector targets the dialog window of the same instance -->
            <uix:NTypeInto DisplayName="Type amount in dialog" Text="[in_Amount]"
                           sap2010:WorkflowViewState.IdRef="NTypeInto_1" />
        </Sequence>
    </uix:NApplicationCard.Body>
</uix:NApplicationCard>
```

**`SingleWindow` — Single Window (only if Application Instance fails).** The card attaches ONLY to the window from its selector. A target in any other window of the same application (parent, child, dialog) is NOT found. The activity target's scope selector is **always** ignored in this mode. Use only when `ByInstance` fails to attach.

```xml
<uix:NApplicationCard AttachMode="SingleWindow" DisplayName="Use App (single window)"
                      sap2010:WorkflowViewState.IdRef="NApplicationCard_2" Version="V2">
    <uix:NApplicationCard.Body>
        <Sequence sap2010:WorkflowViewState.IdRef="Sequence_2">
            <!-- only targets in THIS window resolve; scope selector is ignored -->
            <uix:NClick DisplayName="Click Save" sap2010:WorkflowViewState.IdRef="NClick_2" />
        </Sequence>
    </uix:NApplicationCard.Body>
</uix:NApplicationCard>
```

##### One application instance = one card (even with multiple Object Repository screens)

The Object Repository registers a separate **screen** for every distinct window selector — a dialog, pop-up, or child window with its own title is captured as its own Object Repository screen. This is expected and does **NOT** mean you need a card per screen. **Object Repository screens ≠ Application Cards.** The number of Object Repository screens is driven by window selectors; the number of cards is driven by how many distinct *applications* you touch.

With `ByInstance`, a single card hosts activities scoped to several Object Repository screens as long as those windows belong to the same application instance. Each activity's scope selector locates the right window *within* the instance — the card's own selector does not need to match any one screen. Owned dialogs and pop-ups are part of the target application, so a correctly scoped activity validates and runs under the one card; you do **not** need a dedicated card to avoid an "indicated element does not belong to the target application/browser" error.

**Example — MS Paint File ▸ Open ▸ Cancel.** Clicking *File* then *Open* spawns the Win32 **Open** dialog (`#32770`), a separate top-level window the Object Repository captures as its own screen (`title='Open'`), distinct from the main window (`title='*Paint*'`). Because the dialog is an owned window of the same `mspaint.exe` instance, all three clicks (File, Open, Cancel) go in **one** `ByInstance` card. The File-menu pop-up needs no card of its own — and neither does the Open dialog. Adding a nested card for the dialog is unnecessary complexity.

Do not nest a card just because the Object Repository captured a second screen, or to "keep scope and selector aligned" — `ByInstance` already aligns each activity to its window by scope selector. Reach for a second card only after the [escalation gate below](#nesting-application-cards) applies.

##### Nesting Application Cards

> **Nest cards only for genuinely different applications** — e.g. copying a value from App A into App B, two separate processes. For dialogs, pop-ups, menus, and child windows of the *same* application instance, use a single `ByInstance` card (see [§ One application instance = one card](#one-application-instance--one-card-even-with-multiple-object-repository-screens)). Reach for a nested card on the same instance **only** if `ByInstance` provably fails to attach to or find the owned window — not because the Object Repository captured it as a separate screen.

Application Cards can nest; a UI Automation activity can run inside any Application Card on its parent chain. To switch back and forth between two applications, nest two Application Cards and put all UI Automation activities inside the bottom-most one, attaching each activity to the correct card.

Each `NApplicationCard` carries a `ScopeGuid`. A child activity attaches to a specific card by setting its `ScopeIdentifier` equal to that card's `ScopeGuid` — this is how an activity inside the inner card targets the outer card's application. Change an activity's attached card per the Application Card docs in the package docs.

**IMPORTANT:** ONLY activities that have a target configured and set can have a `ScopeIdentifier`. If an activity does not have a target, do NOT add `ScopeIdentifier` to it.

Example — copy a value from App A and paste it into App B. Outer card → App A, inner (nested) card → App B; both activities live in the inner card. The read sets `ScopeIdentifier` to App A's `ScopeGuid`; the write sets it to App B's. Repeat to move back and forth — no card re-entry between switches.

```xml
<uix:NApplicationCard AttachMode="ByInstance" DisplayName="App A (source)"
                      ScopeGuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                      sap2010:WorkflowViewState.IdRef="NApplicationCard_1" Version="V2">
    <uix:NApplicationCard.Body>
        <Sequence sap2010:WorkflowViewState.IdRef="Sequence_1">
            <uix:NApplicationCard AttachMode="ByInstance" DisplayName="App B (target)"
                                  ScopeGuid="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
                                  sap2010:WorkflowViewState.IdRef="NApplicationCard_2" Version="V2">
                <uix:NApplicationCard.Body>
                    <Sequence sap2010:WorkflowViewState.IdRef="Sequence_2">
                        <!-- ScopeIdentifier = App A card's ScopeGuid → reads from App A (outer) -->
                        <uix:NGetText DisplayName="Get value from App A" Text="[out_Value]"
                                      ScopeIdentifier="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                                      sap2010:WorkflowViewState.IdRef="NGetText_1" Version="V5" />
                        <!-- ScopeIdentifier = App B card's ScopeGuid → pastes into App B (inner) -->
                        <uix:NTypeInto DisplayName="Type value into App B" Text="[out_Value]"
                                       ScopeIdentifier="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
                                       sap2010:WorkflowViewState.IdRef="NTypeInto_1" Version="V5" />
                    </Sequence>
                </uix:NApplicationCard.Body>
            </uix:NApplicationCard>
        </Sequence>
    </uix:NApplicationCard.Body>
</uix:NApplicationCard>
```

> GUIDs above are illustrative placeholders. A card's `ScopeGuid` is generated by `uip rpa activities get-default-xaml` (the starter XAML for `NApplicationCard`) — do not hand-author it. To attach an activity to a card, set the activity's `ScopeIdentifier` to that card's `ScopeGuid`.

#### Target Configuration

[uia-configure-target-workflows.md](uia-configure-target-workflows.md) MUST be read IN FULL first — it covers registering the Application Card's screen and each activity's elements in the Object Repository. Then write plain activities (NApplicationCard, NClick, NTypeInto, ...) with unique `sap2010:WorkflowViewState.IdRef` attributes and no `.Target` children, and attach targets per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

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

> **Before authoring `TypeInto` / `SelectItem` / `Click`:** reading [§ Control-Specific Interaction Patterns](#control-specific-interaction-patterns) is mandatory.

### XAML-Specific Pitfalls

- **Missing `xmlns:uix`** — every UIA workflow needs `xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"` on the root `<Activity>` element

### More Information

- **Per-activity docs:** individual `.md` files in the `activities/` folder (e.g., `Click.md`, `TypeInto.md`, `ApplicationCard.md`)
- **XAML basics:** [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md)
- **Common pitfalls:** [xaml/common-pitfalls.md](xaml/common-pitfalls.md)

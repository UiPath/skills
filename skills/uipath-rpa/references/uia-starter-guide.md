# UIA Starter Guide

Read this file IN FULL before any UI-automation work (Rule 7). Then:

1. **Verify prerequisites** — minimum package version and upgrade-consent rules: SKILL.md § UIA Prerequisites. If the package cannot be installed, use the [Placeholder-Selector Stub Pattern](#placeholder-selector-stub-pattern) below.
2. **Read the UIA package's authoring guide IN FULL** — `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`, including the mode-specific section (For Coded Workflows or For XAML Workflows). It owns authoring — window baseline, target capture, common pitfalls, control-specific interaction, Application Card patterns — and routes to the package's task guides and references. It ships with the package: if the package is installed but the file is absent, the installed version predates it — treat as below the minimum version (SKILL.md § UIA Prerequisites).

The sections below are the UIA policies this skill owns: running/debugging UIA workflows, the deliverable shape when live capture is unavailable, and publishing Object Repository descriptors as a shared UI Library.

---

## Running UI Automation Workflows

**Always use `uip rpa debug start`** (not `uip rpa run`) when running workflows with UI automation. A debug session pauses on error instead of tearing down the application, leaving the UI state available for inspection. The command returns as soon as that happens — `DebugState: "Suspended"` with the exception and locals in `DebugDetails` — so act on the response instead of waiting for the run to end (see [debugging.md § The stable-state debug loop](debugging.md#the-stable-state-debug-loop-headless)).

**Every debug run** must follow this procedure to prevent stale windows from accumulating or being reused in a dirty state:

1. **Record the window baseline** — list top-level windows via the UIA snapshot CLI and note which w-refs and titles are already present. Procedure: the package guide's § Window Baseline (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`).
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
5. **Diff before vs after.** Any window present now that was NOT in the baseline was opened by the workflow. Close each such window via the `uip rpa uia interact` CLI (diff and close procedure: the package guide's § Window Baseline).

Skipping steps 4-5 causes the next run's open-if-not-open behavior to reuse a stale window in whatever state it was left in, or -- if the selector doesn't match -- to spawn a duplicate instance.

### Advanced Debugging — Profiling

For advanced debugging, add `--profiling` to collect insightful per-activity execution data, timings, and before- and after-execution screenshots:

```bash
uip rpa debug start --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json --profiling
```

Use the before-execution screenshot to confirm the application/element started in the correct state, and the after-execution one to validate the expected outcome. Each screenshot's filename is recorded in the run's `.uistat` file; the image sits in the `Screenshots` folder in the same directory as that `.uistat` file. See [debugging.md § Profiling Workflow Performance](debugging.md#profiling-workflow-performance) for details.

### Runtime Selector Failure Recovery

"UI element not found", "UI element is invalid", element not on screen -- these surface at runtime, not during static validation. They occur when a selector was captured against one app state but the DOM changed by the time the activity executes.

When a workflow fails at runtime with a selector error:

1. **The app is already in the right state.** The debug session paused at the failing activity, so the app's current DOM reflects the state that activity needs to target.
2. **Identify the failing element** -- read the error to find which descriptor/element failed.
3. **Read the window selector** -- from the Object Repository files, find the screen's selector that scopes the failing element.
4. **Run the `uia-improve-selector` skill in recover mode.** Read the package's improve-selector guide (routed from the package guide § Documentation), pick the appropriate invocation form for this context, run the staging CLI command from that form, spawn a subagent with the Agent tool to run the skill in recover mode against the staged folder, then run the write-back CLI command from the same form to persist the recovered selector.
5. **Clean up and re-run** -- follow the procedure above (stop, diff, close leaked windows, re-run).

Repeat until the workflow completes successfully. Each failure advances the app to the next problematic state, making recovery self-correcting.

---

## Placeholder-Selector Stub Pattern

Sometimes you must generate a UI automation workflow without live app access — the app is not installed on the build machine, the agent has no GUI, the user has explicitly deferred target capture to a developer who will run Indicate later, or the UIA package cannot be installed (Rule 7a). In that case, the workflow ships with placeholder selectors. The pattern below is the **only** acceptable shape. It requires no UIA package or CLI — that is the point.

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

- Build/validate surface the unconfigured targets ("Target or Input UI Element must be set" — hard errors in current packages) — useful, since they tell the developer what is left to do. A stub-mode deliverable therefore does NOT reach a clean `build`; its acceptance bar is that the ONLY remaining validate/build errors are the expected unconfigured-target ones.
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

Precondition: the source project has captured descriptors (`.objects/` content). If it has none, capture targets first (the package guide's § Configuring Targets) — there is nothing to promote, and hand-writing descriptors is forbidden.

1. Develop the first process against its **local** Object Repository, configuring targets as usual (§ Configuring Targets in the package guide).
2. Promote the reusable descriptors into a dedicated UI Library project — a library project ([library-authoring-guide.md](library-authoring-guide.md)) holding the shared Object Repository; pack and upload per [library-authoring-guide.md § Pack & Publish](library-authoring-guide.md). Concrete Object Repository manipulation steps: the package's Object Repository reference (routed from the package guide § Documentation).
3. **One UI Library per corporate application** (SAP, Salesforce, Workday) — an update to one app's selectors must not force re-deployment of another's.
4. New automations against that application consume the UI Library from the start. Process-specific one-off descriptors stay in the local Object Repository.

### Consumption

Install the UI Library as a package dependency; its descriptors appear under **UI Libraries** in the Object Repository and are targetable like local descriptors. Coded workflows resolve them via the package guide's § Finding Descriptors Step 2 (UILibrary NuGet packages). Selector updates propagate by bumping the dependency version — no per-workflow changes.

### Update rules — MANDATORY

1. **Update descriptors in place — NEVER delete-and-re-add an element.** The element-to-activity link is identity-based; deleting the element severs it and every consumer activity bound to it breaks, even if a same-named element is re-created.
2. **Version by SemVer** ([library-authoring-guide.md § Versioning](library-authoring-guide.md)): selector fix without renaming = patch; element/screen rename or restructure = breaking = major.
3. **Promote accepted healing fixes.** When a selector recovery ([§ Runtime Selector Failure Recovery](#runtime-selector-failure-recovery)) is accepted in a workflow that consumes a shared UI Library, apply the fix in the UI Library and bump the version — do not re-fix the same selector consumer by consumer.

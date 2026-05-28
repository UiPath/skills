# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full per-element flow: capturing the application, discovering elements, generating selectors, improving them, registering them in the OR.

This doc owns the **orchestration** — when to invoke the skill, how to advance between screens in a multi-page workflow, how to attach OR targets to XAML, and the special-case patterns. It does not own the per-element procedure; that lives in the `uia-configure-target` skill's `SKILL.md` inside the UIA package: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md`.

It also does not own the **selector authoring rules** (NEVER hand-write, parameterized selectors, what `interact get-all` is for, the stability model). Those live in [ui-automation-guide.md § Mandatory: Generate Targets Before Writing Any UI Code](ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code).

> **Working directory:** run every `uip rpa uia` CLI call from the project directory — the folder containing `project.json`.

---

## Before you start

- **Execute the skill inline in the main conversation.** Do not delegate the whole `uia-configure-target` flow to a subagent. The skill's internal steps already spawn their own subagents where needed (e.g. for selector improvement). OR references returned by the skill must remain visible to the orchestrating turn so they can be attached to activities as the workflow is built. Context continuity matters — the in-conversation state plus live OR queries are how you know what's already registered, so duplicate captures are avoided and the workflow build stays coherent.
- **Read the skill files before running.** `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md` is the procedure; `USAGE.md` is the invocation reference (TargetAnchorable, TargetApp, the batch `|` pattern for multiple elements per screen). These are reference docs to read and follow — not invocable as slash commands.
- **Check the unsupported-activities list** in `USAGE.md` first. If the activity you need to target is on it, skip `uia-configure-target` and use the [Indication fallback](#indication-fallback) instead.
- **Do not bypass the skill** by calling its internal `uip rpa uia` CLIs (the capture, resolve, improve, and OR-registration commands the skill orchestrates). Calling them outside the skill flow skips selector improvement and OR registration, leaving fragile selectors that aren't in the OR. The skill's SKILL.md defines the proper flow; anything outside it is out of bounds. Same principle, narrower scope: see [ui-automation-guide.md § Mandatory](ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code) for the broader selector authoring rules.

---

## The per-screen loop

A **capture screen** is one UI state that needs its own `uia-configure-target` pass. Each interaction that advances the UI to a new state (click, submit, navigate, dialog confirm) starts a new capture screen. Terminology: [ui-automation-guide.md § Terminology](ui-automation-guide.md#terminology--what-screen-means).

For each capture screen in your workflow, do these four things in order:

### 1. Confirm the app is in the right state

The skill captures whatever is currently on screen. Before invoking it, the target window must be open, visible, and showing the elements you want to register. Use [Pre-flight: Window Baseline](ui-automation-guide.md#pre-flight-window-baseline) once at the start of the session to confirm the app is up.

### 2. Invoke `uia-configure-target` for all elements on this screen

One invocation per screen, with every element passed in the skill's batched-elements form (concrete syntax in the skill's `USAGE.md`). The skill's full per-element procedure is in its `SKILL.md`. The selector authoring rules the skill enforces — capture → resolve → assess → improve via resolver retry or subagent, never via hand-edit or attributes read off the interact CLI's attribute readout — are in [ui-automation-guide.md § Mandatory](ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code). Do not duplicate that procedure here; run the skill.

**Per-screen batching is mandatory.** The OR CLI's entry points are batched, and the skill uses them:

- **One snapshot per screen.** The capture is shared by screen registration and element registration; re-capturing per element is wasted work and may pull a shifted DOM.
- **One element-registration call per screen.** The skill passes all per-element definition files at once. Do not invoke per-element.
- **One element-XAML retrieval per screen.** Same shape.
- **Cross-screen batching is not exposed.** N screens = N invocations of the skill, gated by the UI advance in step 3.

Concrete subcommand and flag names live in `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. This doc owns only the per-screen call-count shape.

### 3. Advance the UI to the next screen via `uip rpa uia interact`

After all elements for the current screen are registered, use `uip rpa uia interact` (click, type, focus, …) to advance the app. Only the verbs needed to reach the next state you want to capture — open a menu, click an item, type then press Enter. Read `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md` for flag details rather than improvising from `--help`.

**Rules for this step:**

- **Complete-then-advance.** Finish ALL `uia-configure-target` calls for the current screen — including OR registration — before advancing. Interactions change state irreversibly; if you advance early, prior-state elements may no longer be visible and registration will fail.
- **`interact` is for advancing, not for testing.** Do not use it to verify that a button works, check what an autocomplete returns, or probe the app. That belongs in the run phase. Repeated probing also costs fresh snapshots you'll then have to manage.
- **`interact` is also not for selector authoring.** Do not read attributes via `interact get-all` and hand-write or edit a selector — the configure-target flow's job is selector construction, and the authoring rules in [ui-automation-guide.md § Mandatory](ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code) apply.
- **Do not use `uip rpa run` with partial workflows to advance UI state.** The workflow lifecycle may close the target app on exit. `interact` is stateless: one action, app stays in the resulting state.
- **Refs survive within a screen, die on advance.** `interact` resolves refs against the most recent snapshot. Within the current `uia-configure-target` capture, refs (`e28`, `b3`, etc.) stay live across multiple `interact` calls; running `uip rpa uia snapshot inspect` just to re-mint refs for an unchanged UI is wasted work. After the UI actually advances (or you re-run `snapshot capture`), all prior refs are dead — `interact` on a stale ref silently no-ops.

### 4. Repeat

Go back to step 1 with the new screen. Continue until every workflow target is in the OR. Each round respects Complete-then-advance — everything for one screen is fully registered before the next `interact`.

---

## Attaching targets to XAML

Once targets are registered in the OR, attach them to XAML activities. Concrete subcommands, flags, and response shapes for both paths: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

Two attachment paths exist; they are **not** interchangeable for agent-authored XAML:

- **Embed path — DEFAULT for agent-authored XAML.** Inline the OR-resolved target XAML as a child of the consuming activity element directly in the file you just wrote. Works on cold files — the project does not need to be loaded in Studio's in-memory designer. This is the only path that reliably works for XAML the agent has just generated or edited from disk.
- **Link path — only for files already loaded in Studio Desktop's designer.** Resolves an OR entry against an activity reference inside Studio's loaded workflow model. Requires the workflow to be open and parsed by Studio Desktop (not Studio Helm / headless). Use this only when the user has the file open in the designer or an existing Studio session already loaded the project.

When generating a new XAML file or editing one that has not been opened in Studio Desktop in this session, take the embed path. Do not attempt the link path on cold XAML — it produces resolution failures that look like activity-id / display-name mismatches but are actually "the file isn't in Studio's model yet" (see [§ CLI pitfalls](#cli-pitfalls)).

**After `link-screen` runs.** The linker writes a literal `Url=` into the `TargetApp` it injects. On Main's `NApplicationCard` (the one that opens the browser), restore the `Url` to your variable expression (e.g. `[in_Url]`). On sub-workflow `NApplicationCard`s (which only attach, never open), delete the injected `Url` attribute — Main already owns the open.

For workflows spanning multiple capture screens, add each screen's activities to the XAML as its OR references become available — one batch per screen, aligned with Complete-then-advance. Validate after each batch.

---

## Special cases

### Hidden / transient elements (dropdowns, popovers, autocomplete)

When an element only exists in the DOM after a user-style interaction (a dropdown that hasn't been opened, an autocomplete result that hasn't been triggered), element registration rejects it with *"No UI element matched the provided partial selector"* even though the element appears in the captured tree. The registration step probes the live DOM; the element is captured in the tree but not yet *visible* to that probe.

Treat the open-parent action as part of the capture loop, not as a test: use the UIA interact CLI to drive the parent UI open, re-capture the snapshot, then re-run the skill against the new ref. This is the [Complete-then-advance](#3-advance-the-ui-to-the-next-screen-via-uip-rpa-uia-interact) rule applied at sub-screen granularity — opening a dropdown is an advance, and you re-capture before configuring its contents. Concrete commands: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

> **Use the live-snapshot capture verb, not the focus-stealing inspect verb, for transient UI.** The inspect verb collapses dropdowns, side panels, autocomplete lists, and similar transient UI before the tree is written.

### Cross-process helper dialogs (sign-in, OAuth, system pop-ups)

Some apps spawn a separate process for sign-in, consent, or system dialogs:

- Microsoft Store sign-in opens in `WWAHost.exe` (not `WinStore.App.exe`)
- Office desktop sign-in / Microsoft Account flows hosted in `WWAHost.exe` or `Microsoft.AAD.BrokerPlugin`
- OAuth pop-ups launched by an enterprise app into the system browser
- Save / Open / Print / UAC dialogs hosted by `consent.exe`, `dllhost.exe`, etc.

When inner UIA activities target one of these helper processes while the outer `NApplicationCard` scopes the original app, validation fails with:

```
The indicated element does not belong to the target application/browser.
```

The validator compares each child target's `ScopeSelectorArgument` against the parent card's `TargetApp` selector — different `app=` values trigger this error every time, even when the runtime selectors are correct.

**Pattern: nest a second `NApplicationCard` for the helper process.** Wrap the activities that target the helper process in their own `NApplicationCard` scoped to that process. Use a wildcard title (`title='*'`) when the helper presents multiple sub-dialogs (e.g., "Sign in" → "Enter password" → "Stay signed in?") so a single nested card covers them all.

```xml
<!-- Outer: original app -->
<uix:NApplicationCard ScopeGuid="<outer-guid>" Version="V2" HealingAgentBehavior="Job" ...>
  <uix:NApplicationCard.TargetApp>
    <uix:TargetApp Selector="&lt;wnd app='WinStore.App.exe' title='Microsoft Store' /&gt;" Version="V2" />
  </uix:NApplicationCard.TargetApp>
  <uix:NApplicationCard.Body>
    <ActivityAction x:TypeArguments="x:Object">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:Object" Name="WSSessionData" />
      </ActivityAction.Argument>
      <Sequence>
        <!-- Activity that triggers the helper-process launch (still in outer scope) -->
        <uix:NClick ScopeIdentifier="<outer-guid>" ... DisplayName="Click Sign In" ... />

        <!-- Inner: helper process (nested card) -->
        <uix:NApplicationCard ScopeGuid="<inner-guid>" Version="V2" HealingAgentBehavior="Job" ...>
          <uix:NApplicationCard.TargetApp>
            <uix:TargetApp Selector="&lt;wnd app='WWAHost.exe' title='*' /&gt;" Version="V2" />
          </uix:NApplicationCard.TargetApp>
          <uix:NApplicationCard.Body>
            <ActivityAction x:TypeArguments="x:Object">
              <ActivityAction.Argument>
                <DelegateInArgument x:TypeArguments="x:Object" Name="WSSessionDataInner" />
              </ActivityAction.Argument>
              <Sequence>
                <!-- Activities here use ScopeIdentifier="<inner-guid>" -->
                <uix:NTypeInto ScopeIdentifier="<inner-guid>" ... />
                <uix:NClick   ScopeIdentifier="<inner-guid>" ... />
              </Sequence>
            </ActivityAction>
          </uix:NApplicationCard.Body>
        </uix:NApplicationCard>

        <!-- Back in outer scope after the helper closes -->
        <uix:NCheckState ScopeIdentifier="<outer-guid>" ... DisplayName="Verify Signed In" ... />
      </Sequence>
    </ActivityAction>
  </uix:NApplicationCard.Body>
</uix:NApplicationCard>
```

**Rules:**

1. **One `NApplicationCard` per process.** Every direct or transitive child activity must target the same `app=` as its enclosing card's `TargetApp`. If activities target two processes, you need two cards.
2. **Each card has its own `ScopeGuid`.** Child activities reference their card via `ScopeIdentifier="<that-card's-ScopeGuid>"`. When moving an activity from one card to another, update `ScopeIdentifier` — `validate` will not catch a mismatched value, but the activity will run against the wrong scope at runtime.
3. **Card-level `HealingAgentBehavior`** uses `NHealingAgentBehavior` (`Job` / `Disabled` / `RecommendationOnly`) — not `SameAsCard`. Details: [ui-automation-guide.md § Common UIA Pitfalls](ui-automation-guide.md#common-uia-pitfalls).
4. **Use `title='*'`** on the helper-process card only when multiple sub-dialogs share the same `app=` and you want a single scope to span them. If sub-dialogs have stable, distinct titles AND only the outer `app=` is shared with the host app (rare), prefer a separate card per dialog so failures localize cleanly.

**Capturing targets for the helper process.** The helper window is a separate UIA-visible window once it appears. Standard per-screen loop applies: trigger the launch via `interact`, run `uia-configure-target` against the helper window, register elements, continue. Treat the helper process as its own capture screen under Complete-then-advance.

### Indication fallback

Use indication when an element appears only after a real user click that `uia-configure-target`'s automated capture can't reproduce — different from the [Hidden / transient elements](#hidden--transient-elements-dropdowns-popovers-autocomplete) case above, where `interact click` on the parent is enough. Indication requires the user to physically click on the target.

Workflow steps, response shape, downstream OR regeneration for coded vs XAML, and pointers to the full CLI flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/indication-fallback-workflow.md`.

---

## CLI pitfalls

Runtime symptoms that have wasted entire capture sessions. Canonical flag list, accepted values, and artifact filenames for every UIA subcommand: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

- **Filter mode of the UIA snapshot CLI fails with a missing-argument error.** It requires a target definition file argument in addition to the folder argument.
- **Selector resolution rejects bare element refs (`Invalid --refs entry`).** Each ref must be paired with the definition file that owns it.
- **OR element-creation rejects inline JSON.** The OR CLI consumes pre-written per-element definition files only. Generate the definition files first, then invoke create-elements with their paths.
- **UIA interact actions reject discovery and global flags (`unknown option`).** Interact subcommands accept only interaction-shape flags. Folder, ref, and project-dir style flags belong to other UIA subcommand families.
- **`interact` on a stale e-ref silently no-ops.** No error, no message — the click just doesn't happen. After `snapshot capture` (or after any UI advance), all prior refs are dead; re-grep `tree.md` for the element and use its new ref.
- **`create-elements` rejects a hidden element with *"No UI element matched"*** — the selector is fine; the element is in the DOM but not visible to the live probe. Open the parent UI first (see [Hidden / transient elements](#hidden--transient-elements-dropdowns-popovers-autocomplete)), then re-capture and re-register.
- **Link path against a cold XAML file fails with `Could not retrieve the activity from the workflow`.** This means the target file is not loaded in Studio Desktop's in-memory designer model — not that the activity-id, display name, or reference ID are wrong. Stop after the **first** failure; do not iterate through activity-id / display-name / property-name variations. Switch to the embed path (see [§ Attaching targets to XAML](#attaching-targets-to-xaml)). The link path is reserved for files that an active Studio Desktop session has already opened and parsed; XAML the agent has just written from disk does not qualify.

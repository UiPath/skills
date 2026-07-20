# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: capturing the application, discovering elements, generating selectors, improving them, and registering them in the OR.

> **Working directory:** run every `uip rpa uia` CLI call from the project directory — the folder containing `project.json`.

## Execution Model

Two invariants, regardless of mode:

- **OR references reach the authoring context per screen** — they are attached to workflow activities as the workflow is created. See `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.
- **One context owns capture state end to end** — which screens and elements are registered (earlier-turn references + live OR queries), so duplicate captures are avoided and the build stays coherent.

Two modes satisfy them. Choose once, at first capture need:

- **Team mode — MANDATORY when available.** Availability check, run it now: `SendMessage` appears in your tool list (deferred listings count) and `Agent` supports named background agents. Available → delegate the whole capture plan to a dedicated capture agent that runs it autonomously and reports at the end, while the main agent scaffolds in parallel: [§ Team Capture Protocol](#team-capture-protocol).
- **Inline mode — only when the check fails.** Execute `uia-configure-target` steps inline in the main conversation, one agent in both roles, sequentially: complete capture before authoring (fast-path order); when building incrementally across screens (§ Multi-Screen Workflows below), confine authoring to screen boundaries — never emit authoring calls between capture calls within a screen. The parallel-scaffolding pattern in the protocol is team-mode only; with one agent it interleaves capture and authoring and degrades both.

Never fire-and-forget the whole capture to a one-shot subagent — a single end-of-run dump violates both invariants.

Whichever agent executes capture: read the SKILL.md, then execute each step of the internal procedure yourself. Only spawn `Agent` where the skill explicitly says to.

## Team Capture Protocol

Roles:

- **Main agent** — owns workflow structure, activity choice, semantic element names, all user interaction, target attachment, validation. Never touches the live app while capture runs, and reads no UIA package CLI docs except the target-attachment guide — every `uip rpa uia` operation belongs to the capture agent.
- **Capture agent** — persistent background agent. Owns the live app: launch verification, every capture judgment (selector quality, anchors), every state advance. Executes this doc's capture sections plus the package capture docs (§ Invocation) under the same rules as inline mode — including Complete-then-advance (§ Multi-Step UI Flows).

### Sequence

1. **Main:** verify UIA prerequisites (SKILL.md Rule 7a). Ensure the project exists with the UIA package installed — the capture agent's CLI runs from the project directory and its docs ship with the package. For a new project, run `uip rpa init` and known `packages install` before kickoff; do not write `project.json` while capture runs.
2. **Main:** build the screen plan — target inventory grouped by screen state, one intended action and one semantic name per element (SKILL.md § Capture-First Fast Path, step 2).
3. **Main:** spawn the capture agent (named, background) with the kickoff payload. Then work in parallel: spawn project-context discovery as a background agent (SKILL.md § Precondition — integrate the returned document on arrival), read remaining authoring references, scaffold the workflow in screen order as real activities with placeholder targets (SKILL.md § Placeholder-Selector Stub Pattern).
4. **Capture agent, first:** verify the app is running and launch it if absent, per the kickoff's app identity — its procedure's window scan doubles as the baseline. A missing app or launch failure is an escalation, not a fallback.
5. **Capture agent:** execute the whole screen plan autonomously — Complete-then-advance per capture screen (§ Multi-Step UI Flows), full skill flow through OR registration for every planned element. Resolve minor mismatches (element renamed/moved, different control than planned, benign extra dialog) with capture-side judgment and record each divergence for the final report. No progress messages, no acks — mid-run messages to the main agent are ONLY the blocking escalations below. If the main agent sends a plan update mid-run, apply it from the next capture screen onward; reply only if it asks a question.
6. **Capture agent, when the plan is exhausted:** send the final report (below) and WAIT. The main agent may request follow-up captures (missed elements); handle them and re-report. Terminate on the main agent's release message.
7. **Main, on the final report:** re-align the workflow to the divergence log (structure/activity changes), link every screen's refs (§ Attaching Targets; batched per screen), per-file validate. Release the capture agent once linking is complete and validated. Project-level `build` runs only after capture ends.

### Kickoff payload (main → capture)

- Project directory; app identity and how to launch it, plus current launch state if known — verifying/launching is the capture agent's first step.
- The screen plan. Names apply verbatim at registration — the capture agent never renames. Unplanned-but-required elements: capture, flag in the report.
- Reading list: this document; the package capture skill SKILL.md + USAGE.md (§ Invocation).
- The final-report contract, the autonomy rule (resolve-and-record minor mismatches; escalate only blockers), and the escalation list below.

### Final report (capture → main)

- App reference + every screen reference + element references, names as given, grouped by OR screen (note which capture screens consolidated into one OR screen).
- Per element: selector quality (strict/fuzzy) and live-observed control facts (e.g. list control with items vs click-to-open, disabled-during-async).
- **Divergence log** — every point where configured reality differs from the plan: element absent/renamed/different control, judgment substitutions, extra states or dialogs encountered. The main agent re-aligns the workflow from this log.
- Structural discoveries: separate-process helper window (different `app=` → main nests a card, § Cross-Process Helper Dialogs).
- The app's current window state, so the main agent can run the workflow without its own UIA scan.
- Activity suggestions are advisory — activity choice stays with the main agent.

### Escalations (capture → main; main mediates the user)

- A blocking plan discrepancy — the planned flow cannot proceed on the actual UI (navigation path missing, unplanned gate such as a login). Minor mismatches are resolve-and-record, never escalations.
- Indication fallback required (user must physically click): pause, report, wait for the main agent.
- Upgrade consent, persistent scan failures, locked session: report to the main agent — never silently fall back, never bypass the main agent to reach the user.

## Invocation

The `uia-configure-target` skill lives at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/` — read `SKILL.md` for the internal procedure and `USAGE.md` for invocation modes (TargetAnchorable, TargetApp, and the batch `|` pattern for multiple elements on the same screen). These are **reference docs to read and follow** — they are NOT invocable as slash commands via the Skill tool.

**Locating the skill file.** The package ID is constant, so the path above is fixed — the reliable way to open it is a direct `Read` of `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md`. If you use `Glob` to find it instead, the pattern **must start with** `**/` — `Glob` matches the pattern against each hit's path relative to the working directory, not relative to the `path` argument, so a pattern that begins with a literal folder name matches nothing:

- ✅ `Glob(path=".../UiPath.UIAutomation.Activities", pattern="**/uia-configure-target/SKILL.md")`
- ❌ `Glob(path=".../UiPath.UIAutomation.Activities", pattern="skills/uia-configure-target/SKILL.md")` — returns "No files found" even though the file exists.

A `Glob` miss is not evidence the skill is absent; never infer availability from it — the installed package version in `project.json` is the source of truth (see [uia-prerequisites.md](uia-prerequisites.md)).

Before invoking, check the unsupported-activities list in `USAGE.md`. If the activity you need to target is on that list, skip `uia-configure-target` for it and use the [Indication Fallback](#indication-fallback) instead.

## Rules

**Do NOT manually call the internal `uip rpa uia` CLIs** that `uia-configure-target` uses to build selectors. These are internal tools used *by* the skill — calling them directly skips selector improvement and OR registration, producing fragile selectors that aren't registered in the Object Repository. The skill's SKILL.md defines the proper flow; anything outside that flow is out of bounds.

## Multi-Step UI Flows

Some UI elements only become visible after interacting with earlier elements (e.g., a compose form appears after clicking "New mail", a confirmation dialog appears after submitting). Since `uia-configure-target` works from the current screen state, you need to **advance the application to each state** before capturing its elements.

> **CRITICAL: Complete-then-advance.** Finish ALL `uia-configure-target` calls for elements visible in the current screen state — including OR registration (the full skill flow) — before advancing to the next state. Interactions change the app state irreversibly. If you advance before registering, elements from the previous state may no longer be visible, causing OR registration to fail.
>
> **Do NOT use the `uip rpa uia interact` CLI to "test" element interactions** (e.g., verifying autocomplete behavior, checking what happens when you click a button) during the capture phase. Testing happens later, when running the completed workflow. During capture, these commands are ONLY for advancing the app to the next screen so you can capture the newly revealed elements.

### Advancing UI State

After registering an element in the Object Repository, advance to the next screen by interacting with it (or a sibling element) via the `uip rpa uia interact` CLI. Interact here **only to move the app to the next state you need to capture** — as many verbs as that legitimately takes (e.g. open a menu then click an item, or type then press Enter), never to map the app ahead of need or to verify behavior (see complete-then-advance above). Read `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. Read it rather than improvising from `--help`. Do not use `interact` to read attributes and hand-write or edit a selector; selector construction and improvement are the configure-target flow's job.

**Reuse refs from the current `uia-configure-target` capture — do not re-inspect.** The `uip rpa uia interact` CLI resolves element refs against the most recent snapshot in memory regardless of which CLI wrote it (the two write to different folders, but the snapshot is shared). Pass the same e-refs (`e28`, `e35`, etc.) directly to the interact subcommands. Re-running the UIA snapshot CLI just to re-mint refs for an unchanged UI is wasted work — the refs you have are still live.

Re-inspect (or re-capture via the UIA snapshot CLI) only when the UI has actually advanced since the last capture; refs from a pre-advance snapshot will not resolve against the new state. Subcommands and flags: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

### Capture Loop

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to OR registration for each element. Do not stop after getting a raw selector.
2. **Advance the UI** to the next state via the `uip rpa uia interact` CLI.
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill flow).
4. **Repeat** until all workflow targets are registered in the OR.

**One Object Repository screen per window selector — not per capture screen.** After an advance, compare the new state's window selector against the OR screens already registered this session: same selector (single-page app, same window showing new content) → register the new elements under the EXISTING OR screen; different selector (new window, dialog, separate process) → new OR screen. Senses table: [ui-automation-guide.md § Terminology](ui-automation-guide.md#terminology--what-screen-means).

**Do NOT use `uip rpa run` with partial workflows to advance UI state** — the workflow lifecycle may close the target application when execution ends. The `uip rpa uia interact` CLI is stateless: it performs one action and leaves the app in the resulting state.

### Per-Screen Batching (call-count discipline)

Per screen, use the batched entry points the OR CLI already exposes — one round-trip that handles all elements at once, not N round-trips. This is the largest single source of wasted calls in capture sessions.

- **One snapshot per screen, shared by every consumer.** Capture the screen's DOM snapshot once and pass that same snapshot folder to both the screen-registration call and the element-registration call. Re-capturing per element is wasted work and may pull a stale or shifted DOM if the app moved between captures.
- **One element-registration call per screen.** The OR CLI's element-registration entry point accepts a list of element-definition file paths in a single invocation; pass every element of the current screen at once. Do not loop one-element-per-call.
- **One element-XAML retrieval per screen.** When fetching the embedding XAML for elements you just registered, the OR CLI's element-XAML retrieval entry point accepts a list of reference IDs; pass them all at once. Do not loop one-id-per-call.
- **Screen-XAML retrieval is per-screen.** That entry point is single-target by design — one extra call per screen, not per element.
- **Cross-screen batching is not currently exposed.** N screens = N rounds of the steps above, gated by `interact`-driven state advances.

Concrete subcommands, flag names, and accepted argument shapes for each batched entry point: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. The package owns the syntax; this skill owns only the per-screen call-count shape above.

## Cross-Process Helper Dialogs (Sign-in, OAuth, System Pop-ups)

Some apps spawn a **separate process** for sign-in, consent, or system dialogs — not just a new window in the same app. Examples:

- Microsoft Store sign-in opens in `WWAHost.exe` (not `WinStore.App.exe`)
- Office desktop sign-in / Microsoft Account flows hosted in `WWAHost.exe` or `Microsoft.AAD.BrokerPlugin`
- OAuth pop-ups launched by an enterprise app into the system browser
- Save / Open / Print / UAC dialogs hosted by `consent.exe`, `dllhost.exe`, etc.

When inner UIA activities target one of these helper processes while the outer `NApplicationCard` scopes the original app, validation fails with:

```
The indicated element does not belong to the target application/browser.
```

The validator compares each child target's `ScopeSelectorArgument` against the parent card's `TargetApp` selector — different `app=` values trigger this error every time, even when the runtime selectors are correct.

> **First, confirm it is actually a separate process.** This whole section applies **only** when the helper runs in a *different process* — a different `app=`. Before nesting anything, compare the secondary window's captured `ScopeSelectorArgument` with the outer card's `TargetApp`: **different `app=` → nest a card (Pattern below); same `app=` → reuse the existing card (next).** A separate top-level window is *not*, by itself, a reason to add a card.

### Same-Process Secondary Windows — Reuse the Card (Do NOT Nest)

Most dialogs, property sheets, Win32 common dialogs (`#32770`: Open / Save / Print / Properties), pop-ups, and child windows belong to the **same process** as the app that spawned them — same `app=`, only a different `cls=` / `title=`. These do **not** get their own card.

With the default `AttachMode="ByInstance"`, one `NApplicationCard` attaches to the **whole application instance**, not a single window. Each child activity finds its target window *within* that instance from its own `ScopeSelectorArgument` — so an activity whose scope selector names the dialog resolves there even though the card's `TargetApp` names the main window. A second card buys nothing and adds another scope to keep aligned.

The `app=`-keyed validation check above does not trip here either: the same `app=` on child and card means no "does not belong to the target application/browser" error. That error is about a different *process*, never a different *window* of the same process.

**Example — MS Paint File ▸ Open ▸ Cancel.** Clicking *File* then *Open* spawns the Win32 **Open** dialog (`#32770`), a separate top-level window the Object Repository captures as its own screen. The *Cancel* button's `ScopeSelectorArgument` is `<wnd app='mspaint.exe' cls='#32770' title='Open' />`, while the Paint card's `TargetApp` is `<wnd app='mspaint.exe' cls='MSPaintApp' title='*Paint*' />`. Same `app=` → the Open dialog is already reachable from the **existing** Paint card under `ByInstance`, so all three clicks (File, Open, Cancel) go in **one** card. The File-menu pop-up needs no card of its own, and neither does the Open dialog. Adding a second card is wrong: do not nest it, and do not claim a single card "would fail validation" — same-process windows pass the `app=` check, and `ByInstance` spans the instance's windows. See [ui-automation-guide.md § One application instance = one card](ui-automation-guide.md#one-application-instance--one-card-even-with-multiple-object-repository-screens).

Use the nested-card pattern below **only** when the secondary window is a genuinely separate process.

### Pattern: Nest a Second `NApplicationCard` for the Helper Process

Wrap the activities that target the helper process in their own `NApplicationCard` scoped to that process. Use a wildcard title (`title='*'`) when the helper presents multiple sub-dialogs (e.g., "Sign in" → "Enter password" → "Stay signed in?") so a single nested card covers them all.

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

1. **One `NApplicationCard` per process — not per window.** Every direct or transitive child activity must target the same `app=` as its enclosing card's `TargetApp`. Two *processes* (different `app=`) need two cards; two *windows* of the same process — dialogs, pop-ups, `#32770` common dialogs — share **one** card under `ByInstance` (see § Same-Process Secondary Windows). Do not add a card just because a secondary top-level window appeared.
2. **Each card has its own `ScopeGuid`.** Child activities reference their card via `ScopeIdentifier="<that-card's-ScopeGuid>"`. When moving an activity from one card to another, update `ScopeIdentifier` — `validate` will not catch a mismatched value, but the activity will run against the wrong scope at runtime.
3. **Card-level `HealingAgentBehavior`** uses `NHealingAgentBehavior` (`Job`/`Disabled`/`RecommendationOnly`) — not `SameAsCard`. Details: [ui-automation-guide.md § Common UIA Pitfalls](ui-automation-guide.md).
4. **Use `title='*'`** on the helper-process card only when multiple sub-dialogs share the same `app=` and you want a single scope to span them. If sub-dialogs have stable, distinct titles AND only the outer `app=` is shared with the host app (rare), prefer a separate card per dialog so failures localize cleanly.

### Capturing Targets for Helper Processes

The helper process is a separate UIA-visible window once it appears, so the standard capture loop applies — pre-flight Window Baseline → trigger the launch (e.g., click "Sign In") via `uip rpa uia interact` → run `uia-configure-target` against the helper window → register elements → continue. Treat the helper process as its own capture screen under the Complete-then-advance rule above; do not try to capture helper-process elements through the host app's window selector.

## Indication Fallback

> **Use indication when elements appear only after user interaction** (e.g., a compose form that opens after clicking a button), so `uia-configure-target`'s automated capture cannot see them. Indication requires the user to physically click on the target.

Workflow steps, response shape, downstream OR regeneration for coded vs XAML, and pointers to the full CLI flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/indication-fallback-workflow.md`.

## Attaching Targets to Workflow Activities

Once targets are registered in the OR (via `uia-configure-target` or indication fallback), attach them to XAML activities per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`. That doc owns the concrete subcommands, flags, and response shapes for both attachment paths.

**Path-choice policy (this skill's scope — which path to take, not how to invoke it).** The attachment guide describes two paths:

- **Link path — DEFAULT.** Attach OR entries to activities by their `sap2010:WorkflowViewState.IdRef` — screen first, then all element targets in one batched call. The file does not need to be open in Studio.
- **Embed fallback — per-reference, only on a link failure.** If a link call fails for a specific reference, inline that reference's OR-resolved target XAML as a child of the consuming activity element — scoped to only the failed reference, not the whole screen.

Take the link path first. On a link failure for a reference, drop straight to the embed fallback for that one reference — do not iterate through activity-id / display-name variations (see § CLI Pitfalls). The package attachment guide is source-of-truth when it diverges from this skill (per SKILL.md).

Link calls rewrite the workflow file on disk — re-read it before any subsequent `Edit`; pre-link file state is stale.

### Multi-Screen Workflows

For XAML workflows spanning multiple capture screens, add each screen's activities to the workflow as its OR references become available. Each batch aligns with the Complete-then-advance rule in § Multi-Step UI Flows — everything configured before the next `uip rpa uia interact` advance belongs to one batch. Validate with `validate` after each batch. In team mode all batches arrive with the final report — link them in the same per-screen batched shape, validating per batch. Attach each target per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

## CLI Pitfalls

Runtime symptoms that have wasted entire capture sessions. Canonical flag list, accepted values, and artifact filenames for every UIA subcommand: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

- **Filter mode of the UIA snapshot CLI fails with a missing-argument error.** It requires a target definition file argument in addition to the folder argument.
- **Selector resolution rejects bare element refs (`Invalid --refs entry`).** Each ref must be paired with the definition file that owns it.
- **OR element-creation rejects inline JSON.** The OR CLI consumes pre-written per-element definition files only. Generate the definition files first, then invoke create-elements with their paths.
- **UIA interact actions reject discovery and global flags (`unknown option`).** Interact subcommands accept only interaction-shape flags. Folder, ref, and project-dir style flags belong to other UIA subcommand families.
- **A link call fails with `Could not retrieve the activity from the workflow`.** Not an activity-id / display-name / reference-ID problem — do not iterate on those. Stop after the **first** failure for that reference and use the embed fallback (see § Attaching Targets to Workflow Activities).

# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: capturing the application, discovering elements, generating selectors, improving them, and registering them in the OR.

> **Working directory:** run every `uip rpa uia` CLI call from the project directory — the folder containing `project.json`.

## Execution Model

**Execute `uia-configure-target` steps inline in the main conversation.** Do NOT delegate the entire skill to a subagent. The skill's internal steps already spawn their own subagents.

Why this matters:
- **OR references** must be visible in the main conversation so they can be attached to workflow activities as the workflow is created. See `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.
- **Context continuity** — as the main conversation proceeds, it already knows which screens and elements are registered: the references were returned in earlier turns, and the OR itself is queryable via the OR CLI. This is what "knowing what's registered" means here — the in-conversation state plus live OR queries — so duplicate captures are avoided and the workflow build stays coherent.

Read the SKILL.md, then execute each step of the internal procedure yourself. Only spawn `Agent` where the skill explicitly says to.

## Invocation

The `uia-configure-target` skill lives at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/` — read `SKILL.md` for the internal procedure and `USAGE.md` for invocation modes (TargetAnchorable, TargetApp, and the batch `|` pattern for multiple elements on the same screen). These are **reference docs to read and follow** — they are NOT invocable as slash commands via the Skill tool.

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

**Reuse refs from the current `uia-configure-target` capture — do not re-inspect.** The `uip rpa uia interact` CLI resolves element refs against the most recent snapshot in memory regardless of which CLI wrote it (the two write to different folders, but the snapshot is shared). Pass the same e-refs (`e28`, `e35`, etc.) directly to `uip rpa uia interact click`/`type`/`select`. Running `uip rpa uia snapshot inspect` just to re-mint refs for an unchanged UI is wasted work — the refs you have are still live.

Re-inspect (or re-run `uip rpa uia snapshot capture`) only when the UI has actually advanced since the last capture; refs from a pre-advance snapshot will not resolve against the new state. Full flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

### Capture Loop

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to OR registration for each element. Do not stop after getting a raw selector.
2. **Advance the UI** to the next state via the `uip rpa uia interact` CLI.
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill flow).
4. **Repeat** until all workflow targets are registered in the OR.

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

1. **One `NApplicationCard` per process** — every direct or transitive child activity must target the same `app=` as its enclosing card's `TargetApp`. If activities target two processes, you need two cards.
2. **Each card has its own `ScopeGuid`.** Child activities reference their card via `ScopeIdentifier="<that-card's-ScopeGuid>"`. When moving an activity from one card to another, update `ScopeIdentifier` — `validate` will not catch a mismatched value, but the activity will run against the wrong scope at runtime.
3. **Card-level `HealingAgentBehavior`** uses `NHealingAgentBehavior` (`Job`/`Disabled`/`RecommendationOnly`) — not `SameAsCard`. Details: [ui-automation-guide.md § Common UIA Pitfalls](ui-automation-guide.md#common-uia-pitfalls).
4. **Use `title='*'`** on the helper-process card only when multiple sub-dialogs share the same `app=` and you want a single scope to span them. If sub-dialogs have stable, distinct titles AND only the outer `app=` is shared with the host app (rare), prefer a separate card per dialog so failures localize cleanly.

### Capturing Targets for Helper Processes

The helper process is a separate UIA-visible window once it appears, so the standard capture loop applies — pre-flight Window Baseline → trigger the launch (e.g., click "Sign In") via `uip rpa uia interact` → run `uia-configure-target` against the helper window → register elements → continue. Treat the helper process as its own capture screen under the Complete-then-advance rule above; do not try to capture helper-process elements through the host app's window selector.

## Indication Fallback

> **Use indication when elements appear only after user interaction** (e.g., a compose form that opens after clicking a button), so `uia-configure-target`'s automated capture cannot see them. Indication requires the user to physically click on the target.

Workflow steps, response shape, downstream OR regeneration for coded vs XAML, and pointers to the full CLI flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/indication-fallback-workflow.md`.

## Attaching Targets to Workflow Activities

Once targets are registered in the OR (via `uia-configure-target` or indication fallback), attach them to XAML activities per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`. That doc owns the concrete subcommands, flags, and response shapes for both attachment paths.

**Path-choice policy (this skill's scope — which path to take, not how to invoke it).** The attachment guide describes two paths; they are not interchangeable for agent-authored XAML:

- **Embed path — DEFAULT for agent-authored XAML.** Inline the OR-resolved target XAML as a child of the consuming activity element directly in the file you just wrote. Works on cold files — the project does not need to be loaded in Studio's in-memory designer. This is the only path that reliably works for XAML the agent has just generated or just edited from disk.
- **Link path — only for files already loaded in Studio Desktop's designer.** Resolves an OR entry against an activity reference inside Studio's loaded workflow model. Requires the workflow to be open and parsed by Studio Desktop (not Studio Helm / headless). Use this only when the user has the file open in the designer or an existing Studio session already loaded the project.

When generating a new XAML file or editing one that has not been opened in Studio Desktop in this session, take the embed path. Do not attempt the link path on cold XAML — it produces resolution failures that look like activity-id / display-name mismatches but are actually "the file isn't in Studio's model yet" (see § CLI Pitfalls).

### Multi-Screen Workflows

For XAML workflows spanning multiple capture screens, add each screen's activities to the workflow as its OR references become available. Each batch aligns with the Complete-then-advance rule in § Multi-Step UI Flows — everything configured before the next `uip rpa uia interact` advance belongs to one batch. Validate with `validate` after each batch. Attach each target per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

## CLI Pitfalls

Runtime symptoms that have wasted entire capture sessions. Canonical flag list, accepted values, and artifact filenames for every UIA subcommand: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

- **Filter mode of the UIA snapshot CLI fails with a missing-argument error.** It requires a target definition file argument in addition to the folder argument.
- **Selector resolution rejects bare element refs (`Invalid --refs entry`).** Each ref must be paired with the definition file that owns it.
- **OR element-creation rejects inline JSON.** The OR CLI consumes pre-written per-element definition files only. Generate the definition files first, then invoke create-elements with their paths.
- **UIA interact actions reject discovery and global flags (`unknown option`).** Interact subcommands accept only interaction-shape flags. Folder, ref, and project-dir style flags belong to other UIA subcommand families.
- **Link path against a cold XAML file fails with `Could not retrieve the activity from the workflow`.** This means the target file is not loaded in Studio Desktop's in-memory designer model — not that the activity-id, display name, or reference ID are wrong. Stop after the **first** failure; do not iterate through activity-id / display-name / property-name variations. Switch to the embed path (see § Attaching Targets to Workflow Activities). The link path is reserved for files that an active Studio Desktop session has already opened and parsed; XAML the agent has just written from disk does not qualify.

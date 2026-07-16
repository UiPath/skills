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

**Locating the skill file.** The package ID is constant, so the path above is fixed — the reliable way to open it is a direct `Read` of `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md`. If you use `Glob` to find it instead, the pattern **must start with** `**/` — `Glob` matches the pattern against each hit's path relative to the working directory, not relative to the `path` argument, so a pattern that begins with a literal folder name matches nothing:

- ✅ `Glob(path=".../UiPath.UIAutomation.Activities", pattern="**/uia-configure-target/SKILL.md")`
- ❌ `Glob(path=".../UiPath.UIAutomation.Activities", pattern="skills/uia-configure-target/SKILL.md")` — returns "No files found" even though the file exists.

A `Glob` miss is not evidence the skill is absent; never infer availability from it — the installed package version in `project.json` is the source of truth (see [ui-automation-guide.md § Prerequisites](ui-automation-guide.md)).

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

### Multi-Screen Workflows

For XAML workflows spanning multiple capture screens, add each screen's activities to the workflow as its OR references become available. Each batch aligns with the Complete-then-advance rule in § Multi-Step UI Flows — everything configured before the next `uip rpa uia interact` advance belongs to one batch. Validate with `validate` after each batch. Attach each target per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

## Driving Captured Controls

How to *drive* a captured UI element correctly — type-specific handling that selector capture alone does not cover. Assumes the target is already registered in the Object Repository; this covers interaction technique, not capture.

Patterns grouped by scope: technology-specific controls first (web), then cross-technology patterns.

### Web Controls (`webctrl`)

Applies to browser elements — elements whose captured selector uses the `webctrl` tag.

#### Date and formatted date-time inputs

Date / formatted date-time inputs must be driven with a **key-event input method**, so the value typed must match the field's **displayed** format. Detect that format, format the value to match, then type it. Try typing WITHOUT emptying the field first; keep emptying as a fallback.

1. **Use a key-event input method — type the displayed format, not the ISO `value`.** In scope: native `<input type="date">` inputs, and framework date-time pickers that *look* like a date field but are built from a more complex structure (divs/spans or several `<input>` parts). Their displayed format and canonical `value` are frequently **different**: a native `<input type="date">` stores `2026-06-19` but renders `06/19/2026` (en-US locale). Drive them with **Chromium API (`DebuggerApi`)** (preferred for browsers) or **Hardware Events** — these dispatch real key events into the control's segmented / composite UI, so the typed string must match the **rendered** format (e.g. en-US native date input → `MM/DD/YYYY`), NOT the ISO value. You must therefore detect how the field is actually printed — step 2.

   **Do NOT use Simulate for date inputs.** Simulate only sets the element's underlying value; it does not dispatch the `input` / `change` events the control's validation and framework data-binding depend on, so the date often fails to register or commit.

2. **Detect the displayed format at design time — never assume, and never trust `value`.** Resolve it *while authoring* — during capture, when the snapshot's element refs (`e5`, …) are live — and bake the result into the workflow. Do not add a runtime read for a format fixed for the target app. This read determines the value to type; it is NOT selector construction (that stays the `uia-configure-target` flow's job).

   Read from the live element with one of three strategies — **stop at the first that yields the displayed format**. Ordered by typical web reliability; the raw attribute is **last** because `value` reports the canonical/ISO form, which often does not match what is rendered:

   | # | Strategy | Use when | Trade-off |
   |---|----------|----------|-----------|
   | 1 | **Inject JavaScript** — interact CLI browser-eval verb, element-scoped (`(el) => …`). Read `type`, `placeholder`, a framework picker's sub-input values / internal state, shadow DOM. For a **native date input** the rendered segments are not in the DOM (`value` is ISO) and a locale guess (`navigator.language` / `Intl`) only reflects the *content-language* preference — which can differ from the browser/OS **UI locale** that actually renders the picker — so treat it as a hint and confirm with strategy 2. | Reliable for framework pickers whose format is exposed in the DOM (`placeholder` / sub-input values). | Web only; fragile to page changes. Locale guess may not match a native date picker. |
   | 2 | **Screenshot** — interact CLI screenshot verb on the element/window; read the rendered placeholder/value visually. | JS cannot derive it (canvas-rendered, opaque widget), or to read/confirm the rendered order for a **native date input** (the reliable read — strategy 1's locale guess can diverge). | Non-deterministic (visual interpretation). |
   | 3 | **Read the attribute** — interact CLI attribute-read verbs (`get <ref> <attribute>` for one; `get-all <ref>` to dump all). A `placeholder` (e.g. `MM/DD/YYYY`) is a good explicit hint **when present**. | A `placeholder` / explicit format attribute exists. | Deterministic, but `value` and the accessibility value are the **canonical/ISO** form — they may NOT match the displayed format. Never infer the typing format from `value` alone for a native date input. |

   **Validate the command before running it.** Verb names, positional-argument order, and flags are owned by the package — confirm each against `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md` before use. Do NOT author these commands from memory; names and argument order may differ from this table.

3. **Format the date string to match** the resolved displayed format before typing — e.g. for an en-US native date input, convert ISO `2026-07-01` → `07/01/2026`.
4. **Type the formatted value — try WITHOUT emptying the field first** (`NTypeInto` property `EmptyField` left false). Emptying is not forbidden: if the field keeps stale/residual content or the value is not replaced cleanly, retry with the field emptied (`EmptyField=true`). Confirm the exact property name/default in `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/activities/NTypeInto.md`.

Why try without emptying first: native date inputs and framework date-time pickers maintain a segmented / internal value. Clearing (`EmptyField`, or `Ctrl+A`+`Delete`) can leave the control in a partial state or trip its validation, so typing the correctly-formatted value over the field usually lets the control's own input handling replace the content cleanly. If it does not — stale value remains, or the input rejects the overlaid text — empty the field and type again.

```xml
<uix:NTypeInto DisplayName="Type Invoice Date"
               Text="[formattedDate]"
               EmptyField="False"
               sap2010:WorkflowViewState.IdRef="NTypeInto_1" />
```

```csharp
// First attempt: EmptyField false → field is not cleared before typing.
// Fallback if content isn't replaced cleanly: set EmptyField true.
formScreen.TypeInto(Descriptors.MyApp.Form.InvoiceDate, formattedDate);
```

---

### All UI Technologies

Patterns that apply to any captured control regardless of UI stack (web, desktop, Java, etc.).

#### Dropdowns, lists, and comboboxes

Whether `SelectItem` (`NSelectItem`) can drive a control does **not** depend on its UI technology,
tag, or role — a native HTML `<select>`, a WinForms/WPF combo box, a Java list, a SAP dropdown, and
a div/ARIA combobox are all candidates. **Don't classify it from the captured selector — query the
control's `items` attribute for its selectable options** (the read verb is in
`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`):

- **`items` lists options** → the control is selectable; `SelectItem` will drive it — pass one of the
  listed values. No need to capture the individual option elements or open the list first.
- **`items` empty/absent** → not a real option-list control. Fall back to click-to-open + click the
  option (capture both as OR targets), or `TypeInto` for type-ahead / filter combos.

Read the `items` attribute to learn the valid values, and the `selecteditem` / `selecteditems`
attribute to confirm the result after selecting (the cli-reference above shows how to read them).

The rule is general: verified against a control with no native `<select>` (a Lightning picklist
rendered as a `role="combobox"` button) and applies identically to desktop, Java, and SAP option
lists — so an option-list control needs **no option-element capture at all**.

#### Debugging a failed interaction with an element

When an interaction fails or faults and the selector still looks correct, suspect the interaction itself changed the element. It can make the app **remount** the target as a new DOM node (e.g. a search box that re-mounts on focus, or a click that expands a dropdown/popup). The activity resolved the *old* node; the next action then hits the now-detached one and faults with `InvalidNodeException: "The UI element is invalid..."` — distinct from "not found" / "click failed". A compound action inside one activity is the classic case: `TypeInto`'s built-in click-before-typing, whose pre-click detaches the field it's about to type into.

**Diagnostic tell:** the selector still resolves, and input mode / delay changes do nothing — it is a re-resolution problem, not timing.

**Fix:** split the interactions into **separate** activities (e.g. `Click` then `TypeInto`) so the second **re-resolves** its target against the new node.

#### Buttons disabled during async operations

A button can be present and matched by its selector yet `disabled` while the application validates a form, loads, or refreshes data.

This is distinct from the late-appearing-target case in [§ Common UIA Pitfalls](ui-automation-guide.md): that pitfall is about a target that *appears* after a delay — the UIA activity's target-finding retry already handles appearance. Retry does NOT cover enabled state — the activity finds the disabled button immediately and clicks a dead control. Check App State does not help either: it waits for an element to appear/disappear, not to become enabled.

Mitigation: set `DelayBefore` (and/or `DelayAfter`) on the click so the async operation has time to enable the button before the click fires. These are properties ON the activity — NOT the standalone `Delay` activity the pitfall warns against.

- Use `DelayBefore` only when the button has an observable disabled→enabled transition driven by validation / load / refresh.
- Keep it as small as reliably works — it is a fixed wait that runs on every execution. It raises the odds the button is enabled at click time; it is not a guarantee.

```xml
<uix:NClick DisplayName="Click Submit (form validates first)"
            DelayBefore="1"
            sap2010:WorkflowViewState.IdRef="NClick_1" />
```

```csharp
// Set the click options' delay-before; confirm the option name and unit in
// {PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/activities/NClick.md
formScreen.Click(Descriptors.MyApp.Form.Submit, new NClickOptions { DelayBefore = 1 });
```

Confirm property names, defaults, and time units against the installed `NTypeInto.md` / `NClick.md` activity docs — do not author UIA property surfaces from memory (SKILL.md Rule 21).

## CLI Pitfalls

Runtime symptoms that have wasted entire capture sessions. Canonical flag list, accepted values, and artifact filenames for every UIA subcommand: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

- **Filter mode of the UIA snapshot CLI fails with a missing-argument error.** It requires a target definition file argument in addition to the folder argument.
- **Selector resolution rejects bare element refs (`Invalid --refs entry`).** Each ref must be paired with the definition file that owns it.
- **OR element-creation rejects inline JSON.** The OR CLI consumes pre-written per-element definition files only. Generate the definition files first, then invoke create-elements with their paths.
- **UIA interact actions reject discovery and global flags (`unknown option`).** Interact subcommands accept only interaction-shape flags. Folder, ref, and project-dir style flags belong to other UIA subcommand families.
- **A link call fails with `Could not retrieve the activity from the workflow`.** Not an activity-id / display-name / reference-ID problem — do not iterate on those. Stop after the **first** failure for that reference and use the embed fallback (see § Attaching Targets to Workflow Activities).

---
confidence: medium
---

# Type Into (NTypeInto) — Text Corrupted, Not Typed, or Method-Not-Found

## Context

`Type Into` in the Modern design experience is internally `NTypeInto` (assembly
`UiPath.UIAutomationNext.Activities`, shipped in the `UiPath.UIAutomation.Activities` package). This
playbook is the entry point for "my Type Into isn't working." It **owns** two failure modes that no
other UI Automation playbook covers, and **routes** the rest.

Owned here:

1. **Text integrity — the value typed is wrong.** Characters are missing, scrambled, duplicated, or
   out of order; or nothing is typed at all because the input method is not honored by the target
   technology. The activity usually reports **Successful** — the fault surfaces downstream (a Get Text
   / verification log showing the corrupted value, a rejected form, a wrong record).
2. **`Method not found: 'Void UiPath.UIAutomationNext.Activities...'`** — a compile/runtime error that
   appears during validation or on a robot after a dependency change. The `UiPath.UIAutomation.Activities`
   package version the workflow was built against does not match the version restored in the current
   environment (assembly version skew).

Routed elsewhere (do NOT diagnose here):

| Signal on the `NTypeInto` | Route to |
|---|---|
| `SelectorNotFoundException` / `UiElementNotFoundException` / "Could not find the user-interface (UI) element" | [selector-failure-manual.md](./selector-failure-manual.md) (+ healing variants) |
| `RuntimeTimeoutException` / element never appeared within the timeout | [timeout-issue.md](./timeout-issue.md) |
| `NodeAmbiguousException` (matched more than one field) | [ambiguous-selector.md](./ambiguous-selector.md) |
| `UiNodeDisabledElementException` (field found but disabled) | [disabled-element.md](./disabled-element.md) |
| Job `Successful`, **nothing** typed, effect never landed, no downstream corruption of a *typed* value | [click-silent-no-op.md](./click-silent-no-op.md) |
| `VerifyActivityExecutionException` — Verify Execution WAS configured and its text-match post-condition threw | [verify-execution-failure.md](./verify-execution-failure.md) |
| `UiAutomationException: "Cannot send input to UI element because it is outside of screen bounds."` | [click-coordinate-off-screen.md](./click-coordinate-off-screen.md) |

> Boundary vs [click-silent-no-op.md](./click-silent-no-op.md): that playbook is for **nothing landed**
> (no character reached the field). This playbook is for **something landed but it is wrong** — partial
> or scrambled text. If both a silent no-op and text corruption are plausible, confirm which by reading
> the downstream value: empty = silent no-op; garbled/partial = here.

### What text corruption looks like

- Job/instance `State = Successful`; typically **zero** Error logs. The keystrokes were sent; the field
  captured them wrong.
- A downstream Get Text, Log Message, or business record shows the entered value dropped characters,
  reordered them, or duplicated them (e.g. field should read `1234-5678-9012` but reads `1345-6789-012`
  or `134-5678-9012`).
- Intermittent across runs — the same workflow types correctly on a fast machine and corrupts on a
  loaded/laggy one.

### What causes text corruption

- **`InteractionMode = HardwareEvents` typing faster than the target accepts.** HardwareEvents drives
  the physical keyboard; on a lagging or throttled application the field misses keystrokes or receives
  them out of order. `DelayBetweenKeys` defaulting to `0`/very low is the usual trigger. **Primary cause
  of scrambled/dropped characters.**
- **Focus stolen mid-type** — a popup, autocomplete dropdown, or window activation grabbed focus after
  the first keystrokes, so the tail of the string went elsewhere. `Activate` fighting an
  already-focused window can also drop the leading characters.
- **Input method not honored by the target technology** — `Simulate` / `SendWindowMessages` post a
  message-level event that Java, SAP, and some legacy Win32/Citrix targets never process, so nothing
  (or only part) is typed. (Full no-effect with no corruption → [click-silent-no-op.md](./click-silent-no-op.md).)
- **Field not cleared** — `EmptyField` off / no `ClickBeforeTyping`, so the new text concatenates onto a
  pre-filled value and reads as "duplicated/extra characters" rather than the clean value.

### What "Method not found" looks like

- `Method not found: 'Void UiPath.UIAutomationNext.Activities.<Type>.<Member>(...)'` raised at Studio
  validation, on build, or at the first `NTypeInto` on a robot — **after** a dependency was
  upgraded/downgraded or the project moved to a machine with a different package version.
- The `.xaml` and selectors are fine; the activity simply cannot bind to a method signature that does
  not exist in the `UiPath.UIAutomationNext.Activities` assembly that was actually restored.
- Fails after updating Studio dependencies, or fails on the robot / in Unattended while working in the
  authoring Studio (Debug) — a classic "works on my machine" version skew.

## Investigation

Source-required for the text-corruption family — resolve the project per SKILL.md §5.4 before
concluding.

1. Classify by symptom first:
   - A `Method not found: 'Void UiPath.UIAutomationNext.Activities...'` string anywhere (Error List,
     build output, robot log) → **dependency skew** (§Resolution B). Skip the runtime steps.
   - `State = Successful` + a downstream value that is *present but wrong* → **text corruption**
     (§Resolution A).
2. For text corruption, capture the job and its full Info logs (`uip or jobs logs <jobKey> --output json`)
   and confirm zero Error logs (`--level Error`). Find the downstream line/output that shows the
   corrupted value and compare it to the intended input — establish *how* it is wrong (dropped /
   reordered / duplicated / partial). Without this runtime proof the corruption claim is unconfirmed
   (§6 runtime-evidence gate) — say so rather than asserting from source alone.
3. Open the workflow source. On the `NTypeInto` read: `InteractionMode`
   (`Simulate` / `ChromiumAPI` / `SendWindowMessages` / `HardwareEvents`), `DelayBetweenKeys`,
   `Activate` / `ActivateBefore`, `EmptyField`, `ClickBeforeTyping`, and the `Text` expression.
4. Open the enclosing scope (`NApplicationCard` / Use Application/Browser) and read the target
   **technology** (`app='java.exe'` / `javastate` = Java; `saplogon.exe` / `sapwnd` = SAP; Chromium +
   HTML = browser). Cross-check the input-method × technology support only when the pairing looks
   unsupported: `uip docsai ask "Which Type Into input methods are supported for <technology> targets in UiPath UI Automation?" --source docs`.
5. For dependency skew, read `project.json` dependencies and compare the `UiPath.UIAutomation.Activities`
   version against the version present in the environment that fails (robot/other machine). The skew
   between them is the root cause.

The root cause is WHY the text is wrong (input method too fast / focus lost / method-signature skew) —
not merely "Type Into failed." A confirmed finding names the activity, the property (or the package
version pair), and the specific defect.

## Resolution

### (A) Text corrupted / not typed correctly

Walk from the top; stop at the first branch that matches.

1. **Scrambled / dropped / out-of-order characters with `InteractionMode = HardwareEvents`** — the
   robot types faster than the application accepts. Increase **`DelayBetweenKeys`** (start at `20`ms,
   raise to `50`ms for a laggy target). If throughput allows, switch `InteractionMode` to **`Simulate`**
   (or **`ChromiumAPI`** for a modern browser) — these send the whole string at once and do not depend
   on per-key timing, eliminating the race. Also uncheck **`Activate`** if the window is already focused
   (re-activation can drop leading keys).
2. **Nothing / only part typed, target is Java / SAP / legacy Win32/Citrix** — `Simulate` /
   `SendWindowMessages` are not honored there. Switch `InteractionMode` to **`HardwareEvents`** (works
   regardless of framework; requires an interactive, foreground session).
3. **Value has extra/duplicated characters** — the field was not cleared. Set **`EmptyField = True`** (or
   enable `ClickBeforeTyping` + a clear) so the new text replaces the old.
4. **Focus lost mid-type** — set `ActivateBefore = True` (or add a Click/Activate on the field first),
   and add a Check App State so the field is settled before typing.
5. **Last resort — the field rejects simulated keypresses entirely** — replace `Type Into` (`NTypeInto`)
   with **`Set Text` (`NSetText`)**, which injects the string directly into the element's value property
   and bypasses keystroke simulation. Do this only after the input-method options above fail; Set Text
   does not fire per-key events some apps rely on.

### (B) Method not found — dependency version skew

The workflow was compiled against one `UiPath.UIAutomation.Activities` version and a **different**
version was restored where it runs. Align them:

1. Open **Manage Packages** → Project Dependencies. Read the installed `UiPath.UIAutomation.Activities`
   version.
2. Set it to a single stable version that is **consistent across every environment** (authoring Studio,
   the robot, and any other machine that runs the project) — upgrade or downgrade so they match. Pin the
   exact version in `project.json` rather than a floating range.
3. Restore/rebuild (`mustRestoreAllDependencies`), reopen, and re-validate. The `Method not found` clears
   once the restored assembly exposes the method signature the `.xaml` was built against.
4. Do NOT rebuild the `.xaml` or re-indicate the target — the activity and selector are intact; only the
   package version conflicts.

> Approval gate (SKILL.md §1.10): (A) branches and (B) are edits to the user's workflow / project
> dependencies. Present the concrete change (file, activity, current vs proposed property or package
> version) and get explicit approval before editing.

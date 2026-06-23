# UI Elements Interaction Guide

How to *drive* a captured UI element correctly — type-specific handling that selector capture alone does not cover.

**Read [ui-automation-guide.md](ui-automation-guide.md) in full first (Rule 7).** This guide assumes the target is already captured in the Object Repository; it covers interaction technique, not capture.

Patterns are grouped by scope: technology-specific controls first (web), then cross-technology patterns.

---

## Web Controls (`webctrl`)

Applies to browser elements — elements whose captured selector uses the `webctrl` tag.

### Date and formatted date-time inputs

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

### Dropdowns — native `<select>` vs custom widgets

Branch on what the control actually is:

| Control | How to drive |
|---------|--------------|
| **Native `<select>`** (real HTML `<select>` / `<option>`) | `SelectItem`, passing the option text. Deterministic. |
| **Custom dropdown** (div/`<ul>`/`<li>`/ARIA hierarchy that only *looks* like a dropdown — no `<select>` tag) | `SelectItem` fails. Click to open, then `Click` the option element (capture both as OR targets). Use `TypeInto` for type-ahead / filter combos. |

Tell them apart from the captured selector: a native control's element carries `tag='SELECT'`; a custom widget resolves to `DIV`/`UL`/`LI`/`SPAN`, typically with `role='combobox'` / `'listbox'` / `'option'`.

---

## All UI Technologies

Patterns that apply to any captured control regardless of UI stack (web, desktop, Java, etc.).

### Buttons disabled during async operations

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

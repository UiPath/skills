---
confidence: medium
---

# Classic Type Into — Wrong, Incomplete, or Appended Text

## Context

A classic `Type Into` (`UiPath.Core.Activities.TypeInto`) found its target field and posted the
keystrokes, but the field's **resulting value is wrong** — characters appended to what was already
there, dropped/garbled characters, or the literal text interpreted as key commands. The text DID land
somewhere; it is just not the value that was intended. This is the Type-Into counterpart of the modern
`NTypeInto` text-mismatch cases.

Distinct from the other classic paths — route those elsewhere:
- **Nothing was entered at all** (field unchanged, no keystrokes took) → [click-silent-no-op.md](./click-silent-no-op.md) (covers `Click` / `Type Into` / `Send Hotkey` no-ops).
- **`SelectorNotFoundException`** (field never located) → [ui-element-not-found.md](./ui-element-not-found.md).
- **`ElementOperationException`** (field found but not editable — disabled, read-only, occluded) → [ui-element-interaction-failed.md](./ui-element-interaction-failed.md).
- **`ActivityTimeoutException`** → [ui-activity-timeout.md](./ui-activity-timeout.md).
- **`"Only one of the {0} and {1} options can be set"`** (both `SimulateType` and `SendWindowMessages` set) → [ui-activity-configuration-error.md](./ui-activity-configuration-error.md).
- **Wrong value entered, nothing threw** → **this playbook.** Route here via `summary.md` (top level) § No-signature routing ("Job/run Successful but the action had no effect or output is wrong").

What this looks like:
- Job/instance `State = Successful`; **zero** Error-level logs.
- Downstream evidence the written value is wrong: a business/Info log, a read-back `Get Text`, or a
  later validation/parse showing a value that differs from the `Text` the activity was given —
  commonly the intended text **prefixed or suffixed by other characters**, truncated, or missing
  characters.
- The failing activity is a classic `Type Into` carrying a `Text` (or `SecureText`) argument.

What can cause it:
- **Field not cleared → new text appended.** Classic `Type Into` only clears the field first when
  `EmptyField = True`. Unset/`False` on a field that already holds a value (an edit form pre-filled
  with the current value, a default, a prior iteration's text) → the typed text is **concatenated**
  onto the existing content. Primary cause of a "value has extra characters at the front/back" report.
- **Input method drops or reorders characters.** `SimulateType` / `SendWindowMessages` are not honored
  by some Java, SAP, Citrix, and legacy Win32 targets — characters are dropped or the value is set
  partially. Default (hardware) typing that is too fast can also drop characters on a slow field
  (no `DelayBetweenKeys`).
- **Literal text interpreted as key commands.** Text containing `[k(...)]` hotkey tokens, or special
  characters (`+ ^ % ( ) { }`) under `SendWindowMessages`, is actioned as keystrokes instead of typed
  literally; an embedded newline/tab can submit or leave the field early.
- **Field masking / autocomplete / validation rewrites the value.** An input mask reformats, an
  autocomplete dropdown selects a different suggestion, or client-side validation strips characters.
- **Focus / activation lost** so the first characters land in the wrong control (no `ActivateBefore` /
  `ClickBeforeTyping`).

What to look for:
- The classic `Type Into`'s `Text`/`SecureText` value, and its `EmptyField`, `SimulateType`,
  `SendWindowMessages`, `ClickBeforeTyping`, `ActivateBefore`, `DelayBetweenKeys` properties. Source-required.
- The value actually written (Info/business logs, a read-back `Get Text`) vs. the intended `Text` —
  the difference (extra prefix/suffix, dropped chars, reformatted) points to the cause.
- The target **technology** (from the full selector) when characters are dropped — Java/SAP/Citrix
  implicate the input method.

## Investigation

1. Confirm the job is `Successful` with zero Error logs (an exception routes to a sibling playbook,
   above). Fetch Error logs and Info logs separately.
2. From runtime Info/business logs (or a read-back), establish the **value actually written** and
   compare it to the `Text` the activity was configured with.
3. Read the classic `Type Into` source: capture `Text`/`SecureText`, `EmptyField`, `SimulateType`,
   `SendWindowMessages`, `ClickBeforeTyping`, `ActivateBefore`, `DelayBetweenKeys`, and the full
   selector (for target technology).
4. Match the difference to a cause:
   - Written = existing/default value **+** intended text → field not cleared (`EmptyField` unset).
   - Written is partial / characters dropped/reordered → input method vs. target technology, or
     typing too fast.
   - Special characters/hotkey tokens acted as keys, or the form submitted early → literal-text
     interpretation.
   - Written value reformatted / different suggestion → mask / autocomplete / validation.
5. Confirm the field's pre-existing content (edit form, default, prior loop iteration) when append is
   suspected.

## Resolution

- **If the field was not cleared (append):** set `EmptyField = True` on the `Type Into` (or prepend an
  explicit clear — `ClickBeforeTyping` plus a select-all/delete such as `[k(ctrl)]a[k(del)]`) so the
  field is empty before typing. Re-run and confirm the written value matches the intended `Text`.
- **If the input method dropped/garbled characters:** use **Default** (hardware) typing for
  Java/SAP/Citrix/legacy targets (clear `SimulateType`/`SendWindowMessages`); for a slow field add a
  small `DelayBetweenKeys`.
- **If literal text was interpreted as keys:** disable `SendWindowMessages` for text carrying special
  characters, or escape/split the value so `[k(...)]`-style tokens and `+^%(){}` are typed literally;
  remove embedded newline/tab unless an early submit is intended.
- **If a mask/autocomplete/validation rewrote the value:** account for the mask (type the value in the
  format the field expects) or dismiss/handle the autocomplete before continuing.
- **If focus was lost:** enable `ActivateBefore` / `ClickBeforeTyping` so the field is focused first.
- **Verify after fixing.** Classic `Type Into` has no post-write verification — add a read-back
  `Get Text` (or use the modern `Type Into` with Verify Execution) to assert the field value going
  forward.

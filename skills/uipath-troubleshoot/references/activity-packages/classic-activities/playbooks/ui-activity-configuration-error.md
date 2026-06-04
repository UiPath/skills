---
confidence: high
---

# UI Activity Configuration Error — Invalid Property Combination

## Context

A classic UI activity failed validation because of an invalid combination of properties — not a
runtime/element problem. These surface as a validation error in Studio (red icon) or as an
`ArgumentException` at the very start of the activity, before any element is touched.

What this looks like:
- "Only one of the {0} and {1} options can be set." — two mutually-exclusive options are both
  enabled (for example `SimulateClick`/`SimulateType` together with `SendWindowMessages` on `Click`
  or `Type Into`)
- A scope validation error stating that both a `Selector` and a `Browser`/`Window` were provided, or
  that neither was provided, on `Attach Browser` / `Attach Window`
- An `Open Browser` validation error about the communication method (e.g. WebDriver is only available
  for certain browsers, or a custom browser requires WebDriver)
- A leaf activity reports `ElementNotSetException` / "The target Element was not specified for this
  activity" (often `---> UninitializedNodeException: The UiElement is not initialized`) at
  `Target.FindByElement` / `ValidateSearchArgs` — yet the leaf's OWN `Selector` is set. Here the leaf
  is the symptom; the originating fault is the enclosing scope failing to produce a context window.
- The activity fails immediately/identically on every run, regardless of the application state

What can cause it:
- Two input methods enabled at once (Simulate + Window Messages) on the same input activity
- A scope activity given both an explicit `Browser`/`Window` object and a `Selector` (they are
  alternatives, not both)
- A scope given neither a `Browser`/`Window` nor a `Selector`
- A scope given the WRONG selector shape for its type — e.g. a browser `html` selector
  (`<html app='...' title='...' />`) on a desktop `Open Application`, or a desktop/`wnd` selector on a
  browser scope — plus a null `ApplicationWindow`/`Browser`. The scope resolves no top-level window, so
  its context-window `UiElement` is never initialized and every child activity faults upstream of its
  own selector.
- `SearchScope` set together with an explicit `Browser`/`Window` object
- A communication method incompatible with the chosen browser type on `Open Browser`

What to look for:
- The full text of the validation/argument error — it names the two conflicting options
- The relevant boolean/input-method properties and scope inputs on the failing activity

## Investigation

1. Read the validation/argument error message — it identifies the two conflicting options or the
   incompatible setting by name.
2. Open the failing activity's properties and inspect the named inputs (input-method booleans, or
   `Selector` vs `Browser`/`Window`, or browser type vs communication method).
3. Confirm the failure is configuration-driven: it reproduces identically every run and occurs before
   any element interaction.
4. If the faulting activity is a LEAF (Click, Type Into, …) reporting "no target" but its own
   `Selector` IS set: read the enclosing scope. Check its selector shape vs. its type (browser `html`
   vs. desktop/`wnd`) and whether `ApplicationWindow`/`Browser` is null. A stack that throws
   `UninitializedNodeException` inside `Target.FindByElement` and surfaces at `ScopeActivity.OnFaulted`
   means the uninitialized node is the SCOPE's context window, not the leaf's target.

## Resolution

- **If two input methods are both enabled:** disable one so only a single input method is active.
- **If a scope has both a Selector and a Browser/Window:** keep one — either pass the
  `Browser`/`Window` object or supply the `Selector`, not both.
- **If a scope has neither:** provide one of them so the scope has a target.
- **If the scope has the wrong selector shape for its type (uninitialized context window):** fix the
  SCOPE, not the leaf. For a browser target use a browser scope (`Use Application/Browser`,
  `Open Browser`, `Attach Browser`); for a desktop target give the `Open Application` a native
  top-level-window selector plus a valid `ApplicationWindow`. Leave the leaf's intact selector alone.
- **If SearchScope conflicts with an explicit Browser/Window:** remove `SearchScope` when passing the
  object directly.
- **If the browser type and communication method are incompatible:** choose a supported combination
  (a communication method the selected browser supports, or a browser the method supports).

## What to present

When the fault is scope-side (leaf reported "no target" but the real cause is the enclosing scope),
state the contrast explicitly so the user fixes the right node:
- The leaf's OWN selector is intact/valid — do not change it.
- The ORIGINATING fault is the scope failing to produce a context window; name the misconfigured scope
  and its offending inputs (selector shape vs. type, null window).
- The fix targets the scope. The leaf "no target" message is the downstream symptom, not the cause.

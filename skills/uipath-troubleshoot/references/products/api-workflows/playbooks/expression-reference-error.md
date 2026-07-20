---
confidence: high
---

# `<name> is not defined` at Runtime (Expression Reference Error)

## Context

What this looks like:
- Run fails with `ReferenceError: <name> is not defined` (e.g. `currentItem is not defined`, `PASS is not defined`)
- `uip api-workflow validate` reports `Status: Valid` — static validation does NOT resolve JS identifier bindings, so this class of fault only surfaces at run time

What can cause it:
- **Loop iterator without `$` prefix.** A ForEach declares `for.each: "currentItem"`, but the body references it as `${currentItem}` instead of `${$currentItem}`. The executor binds the iterator as the global `$currentItem` — the `$` is part of the identifier — so the unprefixed name has no binding. Same for `for.at` (`$currentItemIndex`) and `catch.as` (`$error`).
- **Reading the iterator from the wrong place.** `$context.variables.<iteratorName>` — the executor does not put the iterator there.
- **Unwrapped string literal after a Studio Web save.** An `Assign.set` / `Response` / If `when` literal written as `"PASS"` is normalized by the designer to `"${PASS}"`, turning the literal into a bare identifier reference that has no binding. (Author-side fix belongs to `uipath-api-workflow`; here it explains the runtime error.)

What to look for:
- The exact undefined name in the error vs. the `for.each` / `for.at` / `catch.as` declarations
- Whether the failing expression uses a plain word where a `$`-prefixed identifier or a `${'literal'}` was intended

## Investigation

1. Reproduce: `uip api-workflow run <Workflow.json> --no-auth --input-arguments '<inputs>' --output json` — note the undefined `<name>`.
2. Grep the workflow for `<name>` and compare against the enclosing loop's `for.each`/`for.at` (or catch's `as`). If the declaration is `"currentItem"` and the usage is `${currentItem}`, the `$` prefix is missing.
3. If `<name>` is a value the author intended as a literal string (e.g. `PASS`), it is an unwrapped-literal fault — the reference should be `${'PASS'}`.

## Resolution

- **If a loop iterator / index / catch var:** prefix every reference with `$` — `${$currentItem}`, `${$currentItemIndex}`, `${$error}`. The `$` is a literal character in the identifier, not expression syntax. Re-run to confirm.
- **If an unwrapped literal:** wrap it as a JS string inside the expression — `${'PASS'}`. Numbers/booleans and real references (`${$context.variables.X}`) need no change.
- Always re-run AND re-validate after the fix. For the full authoring rules, the `uipath-api-workflow` skill owns the designer-roundtrip catalog.

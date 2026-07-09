---
confidence: medium
---

# Select Item — Container Has No Items

## Context

A `Select Item` activity (`NSelectItem`) located its target dropdown/list/combo box, but that container held no selectable items at the moment of the action.

What this looks like:
- Exception class: `UiNodeHasNoItemsException`
- Friendly message: `The target container does not have any items.`
- The container WAS found (this is not a selector-not-found) — it is simply empty.

What can cause it:
- The list is populated by an earlier step (a filter, a dependent dropdown, an API/data load) that did not run, returned nothing, or had not finished when `Select Item` ran.
- A dependent control: the second dropdown only fills after the first is set, and the first was never set.
- A timing gap — the action ran before the items rendered.
- The activity targets the wrong container (a placeholder/empty list rather than the populated one).

What to look for:
- Confirm the exception is `UiNodeHasNoItems` (container found, empty) — not `NodeNotFound` (a Select Item whose target resolved only via a non-primary search step also surfaces as `NodeNotFound`; that is a selector concern — see the selector-failure playbooks).
- Trace what is supposed to fill this container before the activity runs.

## Investigation

1. From the failed job, capture the exception, the `Select Item` activity, and the workflow.
2. Identify the step that should populate the container (filter, dependent selection, data/API load) and confirm it ran and produced items.
3. Check ordering/timing: did `Select Item` run before the populate step completed or before items rendered?
4. Confirm the targeted container is the one that gets populated, not an empty placeholder.

## Resolution

- **Upstream populate didn't run / returned nothing:** fix that step — it is the originating fault (the dependent control wasn't set, the query returned no rows, the load failed). `Select Item` cannot choose from an empty list.
- **Timing:** wait for the items before selecting — add a `Check App State` (Element Exists) on a list item, so `Select Item` runs only once the container is populated.
- **Wrong container:** retarget `Select Item` to the populated control.

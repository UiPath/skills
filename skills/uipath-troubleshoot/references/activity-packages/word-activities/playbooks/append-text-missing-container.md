---
confidence: high
---

# Append Text — "Activity is valid only inside WordApplicationScope"

## Context

What this looks like:
- The App-Integration **`Append Text`** activity (`UiPath.Word.Activities.WordAppendText`) shows a **design-time validation error** / faults with `Activity is valid only inside WordApplicationScope` (or "must be placed inside a Use Word File")
- The error fires before any text is appended

What can cause it:
- The App-Integration `Append Text` has **no file input of its own** — it appends to the document held open by a surrounding `Word Application Scope` / `Use Word File`. Dropped **outside** that container, it is invalid.

What to look for:
- Whether the `Append Text` node sits inside a `Word Application Scope` / `Use Word File` in the `.xaml`, or loose in the sequence.
- Whether it's the **App-Integration** `Append Text` (needs a container) or the **standalone** `Append Text` under the **Word Document** category (takes its own file path).

## Investigation

1. Read the workflow `.xaml`. Confirm the `Append Text` node is the App-Integration activity and whether it is nested inside a `Word Application Scope` / `Use Word File`.
2. Note whether the failure is design-time (validation) or runtime invalid-context — both point at the same missing-container cause.

## Resolution

- **Append to an open document** — place the `Append Text` activity **inside** a `Word Application Scope` (or `Use Word File`) that opens the target document, strictly within its **Do** body. The activity then appends to the container's open document.
- **Append without a scope / without opening MS Word** — use the standalone **`Append Text`** under the **Word Document** category instead, which takes the **file path directly** in its own properties (no container, no Word install needed).
- **Pick the surface deliberately** — App-Integration `Append Text` (scoped, Interop) for workflows already inside a Word scope; standalone Word Document `Append Text` for a one-off append by path.

> Same container-vs-standalone pattern as [read-text-missing-container.md](./read-text-missing-container.md) — the App-Integration Word activities need a scope; the Word Document ones take a path.

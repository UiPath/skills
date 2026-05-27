---
confidence: medium
---

# Selector Failure — Scope Container Attached to Wrong Page/Window

## Context

A UI Automation activity faulted with a selector-not-found exception (`NodeNotFoundException`, `SelectorNotFoundException`, `UiElementNotFoundException`) but the inner selector itself is correct for its intended page. The actual defect is in the **enclosing scope container** — `NApplicationCard`, `NBrowser`, `Use Application/Browser`, `NWindow`, `Attach Browser`, `Attach Window` — which attached to a different application instance, browser tab, or page than the inner selector targets.

What this looks like:
- The inner selector is structurally sound and would resolve on the intended page.
- The runtime "closest matches" in the exception belong to a completely different page, locale, or site than the inner selector expects.
- The scope container has a permissive attach configuration that allows reuse of an unintended existing window/tab.

What can cause it:
- `AttachMode=ByInstance` + default `OpenMode=IfNotOpen`: the container reuses any existing window of the configured app instead of opening the intended URL.
- `TargetApp.Selector` is permissive (e.g., `<html app='msedge.exe' title='Google' />` matches google.com, google.ro, google.de — any tab whose title contains "Google").
- `TargetApp.Url` points at a homepage or generic landing page, but the inner selector targets a deeper route that requires navigation.
- No `Navigate Browser` / `Go To URL` activity between scope attach and the inner selector to drive the attached browser to the right page.

## Investigation

1. Locate the faulted activity in the workflow source by `IdRef`, then walk up to its **enclosing scope container**.
2. Read these scope-container attributes from the XAML:
   - `AttachMode` (`ByProcessName`, `ByInstance`, `SingleWindow`)
   - `OpenMode` (`IfNotOpen`, `Always`, `Never`). Absent = `IfNotOpen` default.
   - `TargetApp.Selector` — the window/tab the container attempts to attach to.
   - `TargetApp.Url` (browsers) — the URL the container opens when it does open the app.
3. Compare against the inner activity's intended target:
   - If the inner selector's `BrowserURL` / page-scoped attribute names a deeper route than `TargetApp.Url`, the scope cannot reach the inner target without explicit navigation.
   - If `TargetApp.Selector` is loose (matches multiple tabs/pages) and `OpenMode=IfNotOpen`, the container will reuse whichever matching tab is already open — typically not the one the developer intended.
4. Cross-check the runtime exception's `closest matches`: if they belong to a different page than the inner selector expects, the scope landed on the wrong page.

## Resolution

Fix the scope container, not the inner selector. Choose ONE:

- **Force the container to navigate to the intended page on every run** — set the scope's `OpenMode=Always` (Studio: "Open in browser: Always") and set `TargetApp.Url` to the inner selector's intended page URL. The container always lands on the right page; the inner selector resolves.
- **Tighten the scope's window/tab match** — replace `TargetApp.Selector` with a selector specific to the intended page (e.g., `title='Doodles - Google'` instead of `title='Google'`), keeping `OpenMode=IfNotOpen`. The container only reuses the correct tab.
- **Insert a `Navigate Browser` / `Go To URL` activity before the inner selector** — keep the current scope, but explicitly drive the attached browser to the intended page before the click/extract. Use when the same scope must service multiple pages in sequence.
- **Re-record the inner selector against the page the scope actually attaches to** — only when the design intent is to operate on the page the container lands on and the original selector was authored against the wrong page.

Do NOT "fix" the inner selector (adding wildcards, switching to `automationId`, etc.) when the scope is the actual defect. Selector hardening masks the misconfig and leaves the same trap for future activities inside the same scope.

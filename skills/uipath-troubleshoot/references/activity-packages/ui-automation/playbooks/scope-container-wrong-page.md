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

**Silent variant (no exception).** The wrong-page attach can also produce **no fault at all**: the inner activity runs against the wrong page, its target never matches, yet the job ends `Successful` and the action never happened. This is the "the job succeeded but the button was never clicked" report. It occurs when the miss cannot surface as an exception — e.g. `Simulate` input plus an **absent or target-less Verify Execution** (a `VerifyOptions` with a Mode set but no verification target is inert — "nothing to check" — so the no-op passes silently). There is no exception and no "closest matches" to read; diagnose from source — the scope shape plus the inner activity's Verify Execution config — not from logs. On a silent run the **inert Verify is the confirmed cause of the silent success** (and, when HA was enabled, of why HA never engaged); the **wrong-page attach is only the *likely, unproven* miss cause** — with no exception/closest-matches there is no runtime evidence of which page attached, so do NOT report the scope as a confirmed root cause.

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
5. **Silent variant — job `Successful` but the action did not happen.** There is no exception to anchor on. Read the inner activity's **Verify Execution** (`VerifyOptions`) from the XAML: a Mode set with **no verification target** (and default/empty Retry/Timeout) is inert and cannot catch a no-op. Combined with the permissive scope shape from steps 2–3, an inert Verify is the silent-no-op signature — the wrong-page attach succeeded and the unverified inner activity passed without acting.

## Resolution

Fix the scope container, not the inner selector. Choose ONE:

- **Force the container to navigate to the intended page on every run** — set the scope's `OpenMode=Always` (Studio: "Open in browser: Always") and set `TargetApp.Url` to the inner selector's intended page URL. The container always lands on the right page; the inner selector resolves.
- **Tighten the scope's window/tab match** — replace `TargetApp.Selector` with a selector specific to the intended page (e.g., `title='Doodles - Google'` instead of `title='Google'`), keeping `OpenMode=IfNotOpen`. The container only reuses the correct tab.
- **Insert a `Navigate Browser` / `Go To URL` activity before the inner selector** — keep the current scope, but explicitly drive the attached browser to the intended page before the click/extract. Use when the same scope must service multiple pages in sequence.
- **Re-record the inner selector against the page the scope actually attaches to** — only when the design intent is to operate on the page the container lands on and the original selector was authored against the wrong page.

**Silent variant — fix priority differs from the faulting case.** With no fault you cannot confirm *why* the click missed (wrong page / fragile selector / timing) — there is no runtime evidence. So the **primary, immediately-actionable fix is to configure Verify Execution** on the inner activity with a real expected-outcome target (an element that exists only after the click) so the next run **faults** instead of silently passing — that makes the failure visible AND surfaces the closest-matches / HA data that will finally prove the miss cause. Configure/enable Verify; never remove or weaken an existing `VerifyOptions`. The four scope fixes above address the *likely* miss but stay **unconfirmed until a fault is produced** — apply them as the follow-up once Verify reveals the real cause, not as the confirmed root-cause fix. Editing the user's workflow XAML is interactive — confirm via `AskUserQuestion` before the edit; do not auto-apply.

**Healing Agent angle — only when HA was activated on the job.** This applies only if `AutopilotForRobots.Enabled = true` AND `HealingEnabled = true` (recommendation or self-healing) and the user expected HA to help. HA engages only on a **fault**; the inert Verify produced none, so HA correctly had nothing to act on. The empty (~22-byte) healing archive and a `Healing agent is disabled for the current job` log line are the **no-trigger state — NOT a configuration or license gate**. Configuring the Verify target is also what gives HA a fault to engage on next time. If instead HA was disabled at the process/job level, the un-helped click is an enablement issue → [selector-failure-healing-disabled.md](./selector-failure-healing-disabled.md), not this silent-no-op path.

Do NOT "fix" the inner selector (adding wildcards, switching to `automationId`, etc.) when the scope is the actual defect. Selector hardening masks the misconfig and leaves the same trap for future activities inside the same scope.

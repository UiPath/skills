---
confidence: high
---

# Selector Failure — Healing Agent Disabled

## Context

A UI automation activity failed because its selector didn't match any element in the live UI tree. Healing Agent was not enabled on the process, so no automated recovery data is available.

What this looks like:
- SelectorNotFoundException, UiElementNotFoundException, ElementNotInteractableException, or NodeNotFoundException during activity execution
- AutopilotForRobots shows Enabled: false or HealingEnabled: false (or field absent)

What can cause it:
- Target application UI changed (redesign, update, dynamic content)
- Element attribute became dynamic (index shifted, name changed per session)
- Element hidden behind an overlay, popup, or dialog
- Wrong application window targeted
- **Wrong-page scope (authoring defect)** — the parent `NApplicationCard` / `Attach Browser` / scope wrapper's `TargetApp.Url` (or `TargetApp.Selector` title) mismatches the child Click's expected page. Common subcase: `AttachMode=ByInstance` + a permissive title selector latch the card onto a pre-existing tab on the wrong page, and the card contains no navigation activity before the click. The selector itself is fine — it just runs against the wrong page.

## Investigation

1. Confirm UIAutomation failure via trace spans (activity types: `UiPath.UIAutomationNext.*`, `UiPath.UIAutomation.*`, `UiPath.Core.Activities.Click`, etc.)
2. If trace unavailable, infer from exception type (SelectorNotFoundException is definitively UI)
3. TimeoutException is ambiguous — only classify as UI if trace confirms UI activity type
4. **Decide whether wrong-page scope is plausible from CLI evidence alone.** Strong signal: the exception's closest-match list contains elements from a clearly different page than the failing activity targets — different language locale, different site section, different element family. Weak signal: closest matches are similar to the target. **Eliminating signal:** if the exception's stack or job traces show that other activities in the same parent scope wrapper executed successfully before the failing one, wrong-page-scope is **ruled out** — the scope is attached to the right page; only the failing element is the problem.
5. **If wrong-page scope is plausible, ask the user for the project source path.** Use `AskUserQuestion` to request the path to the project (folder containing the workflow files). Explain that the parent scope wrapper's configuration needs to be inspected against the failing activity's target to confirm or eliminate the wrong-page-scope hypothesis. **Do not glob, search, or assume a project path.** If the user declines or has no path: skip step 6 and mark the wrong-page-scope hypothesis as unverified.
6. **Only if the user supplied a project path**, inspect the parent scope wrapper (`NApplicationCard`, `Attach Browser`, `Open Application`, etc.):
   - Read the workflow file named in the exception's activity stack from the user-supplied path
   - Find the failing activity inside its parent scope wrapper
   - Extract `TargetApp.Url`, `TargetApp.Selector`, and `AttachMode` from the parent scope
   - Extract the failing activity's `Target.BrowserURL` (or `ScopeSelectorArgument`)
   - Count navigation activities (`NGoToUrl`, `NavigateBrowser`, `OpenBrowser`, `NGoToUrlX`) inside the scope wrapper before the failing activity
   - **Wrong-page-scope is confirmed** when ALL of these hold: parent `TargetApp.Url` ≠ child `Target.BrowserURL`, navigation activity count = 0, and the closest-match list confirms a different page
7. **Only conclude "stale selector / UI changed"** when wrong-page scope has been ruled out (or marked unverified because no source was supplied) AND the closest matches contain elements with similar `aaname`/`class` from the intended page

## Resolution

Branch by what the investigation identified:

**If wrong-page scope (authoring defect):**
- Insert a navigation activity (`Go To URL` / `Navigate Browser` / `NGoToUrl`) inside the parent scope before the failing activity, targeting the click's expected URL — OR
- Repoint the parent scope's `TargetApp.Url` to the click's expected page AND tighten `TargetApp.Selector` (title) to match the destination page — OR
- Change `AttachMode` from `ByInstance` to one that opens/navigates rather than only attaching to a pre-existing window
- Re-record the click on the page the scope actually attaches to, if the scope page is the intended one

**If stale selector / UI changed:**
- Re-indicate the element in Studio and update the Object Repository descriptor
- Prefer stable attributes (role, automationId, aria-label) over numeric/generated suffixes
- Add a FuzzySelector and/or anchor

**Always:**
- Enable Healing Agent on the process so future drift is captured automatically.
- Note: Enabling HA does not fix wrong-page-scope defects — HA recovers selectors against the live page, but if the live page is the wrong page, HA has no correct target to recover toward.

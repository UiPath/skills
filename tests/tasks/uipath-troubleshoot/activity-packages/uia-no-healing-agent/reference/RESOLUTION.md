# Final Resolution

Here's the root-cause analysis:

---

**Root Cause:** Authoring-time corruption of the click target's `aria-label` selector attribute — the value `'Simt că am noroccccccccccc'` (ten extra `c` characters appended) does not match any real element on the Google homepage, so the Click activity cannot resolve its target and faults.

**What went wrong:** The Click 'Simt că am noroc' activity in `Google.xaml` failed with a `NodeNotFoundException` because its selector's only identifying attribute (`aria-label`) is a typo of the real button label.

**Why:** When the ERN job ran, the `Edge Google` browser scope attached correctly to `https://www.google.com/`, so the inner click had a valid page to resolve against. The click then attempted to match `<webctrl aria-label='Simt că am noroccccccccccc' tag='INPUT' type='submit' .../>`. The `aria-label` value is the only distinguishing identifier in the selector — `tag='INPUT'` and `type='submit'` are non-unique on the Google form, and the `css-selector` is a positional DOM path with no class/id anchors. Because no DOM element on the page carries that corrupted `aria-label`, the selector resolution failed and `NodeNotFoundException` was thrown. The activity was authored with only the `Selector` search step (no Strict / Fuzzy fallback), so there was no second chance. Separately, the ERN release had Healing Agent disabled (`AutopilotForRobots.Enabled=false`, `HealingEnabled=false`), which is why no automated recovery data, selector suggestions, or screenshots were captured — and why six prior faulted ERN runs over May 21–25 produced no diagnostic trail to surface this defect earlier.

**Evidence**

### UI Automation (Root Cause)
- Faulted activity: **Click 'Simt că am noroc'** (`UiPath.UIAutomationNext.Activities.NClick`) inside scope **Edge Google** (`NApplicationCard`), in `Google.xaml`.
- Exception: `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at `TargetCommonLogic.GetSearchResultAsync` → `NClick.SearchAndSetTargetAsync` → `NClick.ExecuteAsync` → `NApplicationCard.OnFault`, single Error log entry at `2026-05-25T10:39:06.234Z`.
- Selector (verbatim from `Google.xaml`):
  `<webctrl aria-label='Simt că am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />`
- Activity DisplayName in the same XAML: `Click 'Simt că am noroc'` — the canonical un-corrupted button label is right there in the workflow, alongside the corrupted selector. The selector's `aria-label` has ten extra `c` characters compared to the DisplayName.
- `SearchSteps='Selector'` — no Strict and no Fuzzy fallback authored.
- No `Check App State` / `Wait For Element` / `Navigate Browser` precedes the Click — `Sequence 'Do'` contains the Click as its only child.
- Scope is correctly configured (eliminates "wrong page"): `TargetApp.Url='https://www.google.com/'` matches inner `BrowserURL='google.com'`.

### Orchestrator (Propagation)
- Folder: **Shared** (Standard). Job: **ERN** (Key `91d543d2-1b71-4233-a94a-a1389014c998`, Id 65108299), Attended/StudioPro, machine `MOCK-HOST`, started `2026-05-25T10:38:34.457Z`, Faulted at `2026-05-25T10:39:07.183Z`, `EntryPointPath=Google.xaml`.
- **Autopilot for robots — Healing Agent: Off** at the release level (`AutopilotForRobots = { Enabled: false, HealingEnabled: false }`). No recovery selectors, fuzzy suggestions, or fault screenshots were captured.
- Six prior faulted ERN runs in Shared over May 21–25 — recurring pattern.

**Immediate fix**

### UI Automation (Root Cause)
1. **Fix the corrupted `aria-label`** on `NClick_1` in `Google.xaml`.
   - Where: ``, `Target.FullSelectorArgument`. Replace `aria-label='Simt că am noroccccccccccc'` with `aria-label='Simt că am noroc'` (or wildcard `aria-label='Simt că am noroc*'`).
   - Validate: `uip rpa validate --file-path "" --output json`.
   - Source: `selector-failure-manual.md` § Resolution.

2. *Optional:* add a `Check App State` precondition before the Click — `Sequence 'Do'` currently has no readiness guard.

### Orchestrator (Propagation)
1. **Enable Healing Agent** on the ERN release so any future selector regression captures recovery data automatically.
   - Where: Orchestrator → Folders → **Shared** → Processes → **ERN** → Edit → Autopilot for robots → enable Healing Agent.
   - Source: `selector-failure-healing-disabled.md` § Resolution.

2. After the selector fix is published, **restart** job `91d543d2-1b71-4233-a94a-a1389014c998` to confirm the fix.

**Preventive fix**

1. **UI Automation** — audit other selectors in the ERN project for single-attribute identification, purely positional CSS paths, and missing `SelectorThenFuzzy` fallbacks. Multiple stable anchors + Fuzzy would have absorbed a 10-character typo automatically.
2. **Orchestrator** — set up Alerts (State = All) or enable the daily Email Alerts Dashboard so a recurrence pattern like the six ERN faults surfaces on day 1, not day 5.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Resolution |
|---|------------|------------|--------|-------------|------------|
| H1 | Healing Agent disabled on the ERN release, so no auto-recovery captured | High | Confirmed | No (parallel condition) | Enable HA; restart job |
| H2 | `Edge Google` scope attached to the wrong tab/page | Medium | Eliminated | No | N/A |
| H3 | Inner click `aria-label` is corrupted — `'Simt că am noroccccccccccc'` vs real `'Simt că am noroc'` | Medium | Confirmed (depth-verified) | **Yes** | Replace `aria-label` with `'Simt că am noroc'` (or wildcard) |

---

Now the post-presentation actions. Two interactive resolutions to apply:

**Action 1 — Apply corrected selector to Click 'Simt că am noroc' in Google.xaml**

Source: `selector-failure-manual.md` § Resolution (bullets 1 and 2)

```
Failed selector (current, corrupted — from , activity NClick_1):
<webctrl aria-label='Simt că am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />

Proposed corrected selector (exact-match fix — restores canonical button text):
<webctrl aria-label='Simt că am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />

Proposed corrected selector (wildcard variant — absorbs future diacritic/localization tweaks):
<webctrl aria-label='Simt că am noroc*' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />
```

⚠️ Healing Agent was disabled on this release (`AutopilotForRobots.Enabled=false, HealingEnabled=false`) — the corrected selector was derived from the workflow's own DisplayName (`Click 'Simt că am noroc'`) and was **not validated against a live recovered selector at runtime**. Validate after applying.

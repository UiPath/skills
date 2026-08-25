# Final Resolution

Here is the investigation result.

---

**Root Cause:** The classic `Attach Browser` scope (`UiPath.Core.Activities.BrowserScope`) named
`Attach Browser 'Chrome portal'` in `Main.xaml` faulted at scope startup with a
`System.Runtime.InteropServices.COMException` — **"Invalid access to memory location."
(HRESULT `0x800703E6`)**, wrapped as `BrowserOperationException`. This is an **environmental COM
conflict** between UiPath's classic background browser engine and the runtime the robot executed on —
NOT a selector, extension, browser-not-installed, or flow-ordering defect. The classic browser engine
could not marshal against the browser on the unattended production robot.

**What went wrong:** The scheduled **unattended** `PortalReconciliation` job on machine `MOCK-HOST`
faulted ~7 seconds after starting, at the `BrowserScope` (`Attach Browser`) as it tried to attach to
Chrome (`UiNode.SetForeground` → COM `0x800703E6`). The same process had run **Successfully** the day
before as an **attended** run on a different machine (`DEV-BOX`) — the failure is environment-specific.

**Why (full causal chain):**
- `Main.xaml` contains a classic `ui:BrowserScope` (`Attach Browser`, `BrowserType=Chrome`) with a
  valid top-level selector (`<html app='chrome.exe' title='Reconciliation Portal*' />`, already
  wildcarded) wrapping a single `Get Text 'balance'` whose `webctrl` selector is also valid. Source
  contains **no** selector defect, no missing scope, and no configuration conflict.
- At run time the scope threw before any child ran: `BrowserOperationException ---> COMException
  (0x800703E6): "Invalid access to memory location."` at
  `BrowserScope.AttachToBrowser → UiNode.SetForeground`. This is the classic UI engine failing a COM
  call while attaching — an environmental fault, not a locate/selector failure (no
  `SelectorNotFoundException`, no `ActivityTimeoutException`, and the ~7 s duration is far below the
  30 s child timeout, so it is not a wait timeout).
- The failing run was **Unattended** (`Type=Unattended`, `RequiresUserInteraction=false`,
  `Source=Schedule`) on `MOCK-HOST`; the last **successful** run was **Attended** on `DEV-BOX`. The
  COM `SetForeground`/marshalling failure appearing only on the unattended prod robot is the signature
  of an environment mismatch — display-scaling (DPI), user-access/integrity-level, or a
  non-interactive session — between the machine the automation was authored/last succeeded on and the
  machine it runs on.
- Orchestrator recorded the Faulted state; a scheduled unattended job is not auto-recovered.

**Evidence**

### classic-activities (Root Cause)
- Faulting activity: `Attach Browser 'Chrome portal'` (`ui:BrowserScope`,
  `UiPath.Core.Activities.BrowserScope`) in `Main.xaml`.
- Exception (from `or jobs get` Info + `or jobs logs`): `UiPath.Core.Activities.BrowserOperationException`
  `---> System.Runtime.InteropServices.COMException (0x800703E6): "Invalid access to memory location."`
  thrown at `UiNode.SetForeground → BrowserScope.AttachToBrowser → BrowserScope.Execute`.
- Source rules out the sibling causes: the scope's `Selector` is present and wildcarded; the child
  `Get Text 'balance'` `Target.Selector` is valid; the scope is not empty; the package
  (`UiPath.UIAutomation.Activities 22.4.3`) is present. No `SelectorNotFoundException`,
  `BrowserOperationException`-extension text, or `ActivityTimeoutException`.
- Activity tree on the stack matches the XAML: `BrowserScope → Sequence 'Reconcile' → DynamicActivity 'Main'`.

### orchestrator (environment delta / propagation)
- Faulted job: `7c4e0b9a-3f21-4d88-a6b2-19e5c3d40f77`, process `PortalReconciliation`, folder `Finance`,
  package `UiPath.UIAutomation.Activities 22.4.3`. Running `2026-07-15T02:15:04Z` → Faulted
  `2026-07-15T02:15:11Z` (~7 s). `Type=Unattended`, `Source=Schedule`, machine `MOCK-HOST`.
- Prior run `1b90d6f2-8c44-4a1e-b7d3-6f0a2e9c5511` was **Successful**, `Type=Attended`, machine
  `DEV-BOX`, the day before. Same process, different environment → environment-specific failure.

**Immediate fix (environment — recommendation only; no local file to edit)**

Align the runtime robot's environment with the machine the automation succeeded on. Present these as
recommendations for the user / platform team — do not apply them:

1. **Match display-scaling (DPI)** between the development/attended machine (`DEV-BOX`) and the
   unattended production robot (`MOCK-HOST`) so the classic engine's coordinate/marshalling
   assumptions hold.
2. **Run the browser and the Robot at the same privilege / integrity level** — do not mix an elevated
   browser with a non-elevated Robot (or vice versa).
3. **Ensure the unattended robot runs in an interactive, unlocked session** (a real desktop, not a
   Session-0 / locked / disconnected session), which the classic browser engine requires.

**Strategic fix (source — approval-gated, delegate to uipath-rpa)**

4. **Migrate the classic `Attach Browser` to the modern `Use Application/Browser` container.**
   `BrowserScope` is the classic design experience; `Use Application/Browser` uses unified targets and
   handles background crashes and container/COM faults natively, which is the durable fix when these
   environmental COM faults recur. Present the change and get approval before delegating the edit to
   `uipath-rpa`.

**What is NOT the cause (rule-outs):**
- Not a selector / element-not-found problem — the selectors are valid and no
  `SelectorNotFoundException` was thrown.
- Not a timeout — the fault fired at ~7 s, well under the 30 s child timeout; no
  `ActivityTimeoutException`.
- Not "cannot communicate with the browser" / a missing-or-corrupt extension
  (`BrowserOperationException` extension family) — the leaf signal is a COM `0x800703E6`
  marshalling fault, not an extension-channel loss.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The BrowserScope selector or the child Get Text selector is broken (selector drift / element not found) | Medium | Rejected | No | Source shows both selectors valid and wildcarded; no `SelectorNotFoundException` in logs | Disproven from source + logs |
| H2 | Classic `BrowserScope` hit an environmental COM fault — `COMException 0x800703E6` "Invalid access to memory location" at `UiNode.SetForeground` while attaching, on the unattended prod robot only | Medium | Confirmed | **Yes** | COMException `0x800703E6` at `BrowserScope.AttachToBrowser`; fault at ~7 s (not a timeout); failed unattended on `MOCK-HOST`, succeeded attended on `DEV-BOX` | Align display-scaling / privilege / interactive session across machines; strategically migrate to Use Application/Browser |

---

The immediate remediation is environment/platform configuration (recommendation only). The strategic
source change — migrating `Attach Browser` to `Use Application/Browser` in `Main.xaml` — is
approval-gated and, if approved, delegated to `uipath-rpa`.

# Final Resolution

---

**Root Cause:** The classic `Word Application Scope` in `Main.xaml` drives
the Microsoft Word Interop API. The new unattended robot host (MOCK-HOST)
cannot create the `Word.Application` COM class, so the scope faults at
startup with `REGDB_E_CLASSNOTREG` (0x80040154) before the document is
touched. The host either has no desktop Word installed, runs an
Office/robot bitness mismatch, or has a damaged Office COM registration.

**What went wrong:** The `DocGenerator` job (started
2026-06-08T09:12:04Z) faulted ~2.4 seconds after launch when its
`Word Application Scope` tried to start Word. The runtime error was
`Retrieving the COM class factory for component with CLSID
{000209FF-0000-0000-C000-000000000046} failed due to the following error:
80040154 Class not registered (REGDB_E_CLASSNOTREG)`. The process ran
successfully on the developer machine (which has Word) and only began
faulting after it was moved to the new unattended robot - corroborating a
host-environment cause rather than a workflow defect.

**Why:** Classic Word activities (`Word Application Scope`) launch a real
WINWORD.EXE through COM Interop. COM cannot instantiate `Word.Application`
unless a registered desktop Word installation is present on the machine,
reachable by the robot's Windows user, and at a bitness compatible with
the robot process. Web/online Word does not satisfy Interop. On a fresh
unattended VM, Linux robot, or container with no Office installed - or one
where Office and the robot process disagree on bitness - the scope faults
at startup with `REGDB_E_CLASSNOTREG`.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: DocGenerator -- Faulted at 2026-06-08T09:12:06.480Z (ran for ~2.4 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: Contract Generation (key `a1b2c3d4-e5f6-4071-8293-a4b5c6d7e801`)
- Final error: `Retrieving the COM class factory for component with CLSID {000209FF-0000-0000-C000-000000000046} failed ... 0x80040154 (REGDB_E_CLASSNOTREG)` -> `Main.xaml` -> `WordApplicationScope "Word Application Scope"` -> `Sequence "Main Sequence"`

### Word Activities (Root Cause)
- Activity surface: classic `UiPath.Word.Activities.WordApplicationScope` (Interop / COM)
- CLSID `{000209FF-0000-0000-C000-000000000046}` is `Word.Application` - the class COM could not register because desktop Word is not usable on MOCK-HOST.
- The fault is at scope startup (the document body never executes), which is the signature of a missing/unusable Word install rather than a corrupt-file, file-path, or package problem.

---

**Immediate fix:**

The agent could not confirm the host's Word install from Orchestrator
alone. The cause is unambiguous from the HRESULT, but the exact remediation
depends on the host state. Hand the user the host checks and the fix paths.

### Host check (Contract Generation / MOCK-HOST, as the robot's Windows user)
1. Confirm whether Microsoft Word (desktop) is installed:
   `Control Panel > Programs and Features` (look for Microsoft Office /
   Microsoft 365), or run
   `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\winword.exe'`
   in PowerShell. Expect it to be **absent** - that confirms the cause.
2. If Word IS installed, capture its bitness (`File > Account > About Word`)
   and compare it against the robot process bitness.

### Fix path A -- install desktop Word (if absent)
- Install Microsoft Word (or the full Office / Microsoft 365 desktop
  suite) on MOCK-HOST under a license the robot's Windows user can
  activate, then re-run. Interop requires a registered desktop Word;
  online/web Word does not satisfy it.

### Fix path B -- fix bitness / repair COM registration (if Word is present)
- If a 32-bit/64-bit Office-vs-robot mismatch exists, reinstall Office at
  the matching bitness (preferred: 64-bit Office for 64-bit robots).
- If bitness matches but COM is still unregistered, run the Office Repair
  tool (`Control Panel > Programs and Features > Microsoft Office >
  Change > Repair`; Online Repair re-registers the COM components).

- **Source:** `word-activities/playbooks/word-scope-com-not-installed.md`

> Note: there is no in-place workaround on a host where desktop Word
> cannot run - `Word Application Scope` requires a registered desktop Word.

---

**Preventive fix:**

1. **Robot host provisioning** -- standardize the unattended robot image to
   include desktop Word at the same bitness as the robot if any process in
   the portfolio uses `Word Application Scope`.
   - **Why:** "Works on dev, fails on the robot" is a recurring class of
     failure when the robot image diverges from developer machines.
   - **Who:** Platform / robot host team.

2. **Studio** -- where the design experience supports it, prefer the modern
   `Use Word File` activity for clearer behavior, but note it still needs
   desktop Word for most operations.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Desktop Word is not usable on the unattended robot host (not installed, bitness mismatch, or damaged COM registration); classic Word Application Scope cannot create the Word.Application COM object | High | Confirmed | Yes | `REGDB_E_CLASSNOTREG` on CLSID for `Word.Application` at scope startup + "worked on dev, broke after move to new robot" | Install desktop Word on the host, fix the Office/robot bitness mismatch, or repair the Office COM registration |

---

Would you like the exact host commands to confirm the Word install and its
bitness on MOCK-HOST, or help cleaning up the `.local/investigations/` folder?

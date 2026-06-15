---
confidence: high
---

# Word Application Scope — Error Opening Document / Word Not Installed (COM Interop)

## Context

What this looks like:
- Activity `Word Application Scope` (`UiPath.Word.Activities.WordApplicationScope`) faults the moment it tries to open the document, before reading or writing any content
- Error message contains one of: `Error opening document, make sure Word application is installed`, `Could not load file or assembly 'Microsoft.Office.Interop.Word'`, `Retrieving the COM class factory for component with CLSID {000209FF-0000-0000-C000-000000000046} failed`, `80040154 (REGDB_E_CLASSNOTREG)`, or `Cannot create an instance of Microsoft.Office.Interop.Word.ApplicationClass`

What can cause it:
- `Word Application Scope` drives the **Microsoft Word Interop API** — it launches a real WINWORD.EXE via COM. The scope cannot establish that COM connection when:
  - Desktop Word is not installed on the execution host (only the web/online version is available, a Linux robot, a stripped-down VM, or a container image)
  - A **bitness conflict** between Office and the robot process — 32-bit Office against a 64-bit robot (or vice versa) — so cross-bitness COM marshaling fails to create the class factory
  - Office is installed but its COM registration is damaged (failed update, partial install)

What to look for:
- `REGDB_E_CLASSNOTREG` / `make sure Word application is installed` is the signature of "no usable desktop Word for Interop" — it is an environment fault, not a workflow defect.

## Investigation

1. Read the faulted node from the workflow `.xaml` and confirm it is `Word Application Scope` (classic Interop) rather than the modern `Use Word File` surface.
2. Confirm desktop Microsoft Word is installed on the execution machine. Ask the user (or someone with access to the robot host, signed in as the robot's Windows user) to check `Control Panel > Programs and Features` for a Microsoft Office / Microsoft 365 entry, or run `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\winword.exe'` in PowerShell. Web/online Word does not satisfy Interop.
3. Capture the Office bitness (`File > Account > About Word`) and compare it against the robot process bitness. A 32-bit/64-bit mismatch is a common cause when Word *is* installed but the scope still faults at startup.
4. Confirm the robot type. Linux robots and many cloud/container unattended hosts have no Word and cannot run Interop activities at all.

## Resolution

- **If Word is not installed** — install the desktop Microsoft Word (or full Office / Microsoft 365 desktop suite) on the execution machine under a license the robot's Windows user can activate, then re-run.
- **If only web/online Office is present** — the online edition cannot back Interop. Install the desktop suite, or migrate the workflow to the modern `Use Word File` surface where the operation supports it.
- **If Office and robot bitness differ** — reinstall Office at the same bitness as the robot (preferred: 64-bit Office for 64-bit robots), or run the robot under the matching bitness.
- **If Office is installed at matching bitness but COM is still unregistered** — run the Office Repair tool: `Control Panel > Programs and Features > Microsoft Office > Change > Repair` (Online Repair re-registers the COM components).
- **If Word cannot be installed on the host** (Linux robot, locked-down VM, container) — re-architect to avoid Interop. There is no in-place workaround; `Word Application Scope` requires a registered desktop Word.

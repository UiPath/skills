# Final Resolution

Investigation complete. Here is the finding:

---

**Root Cause:** The "GitHub Desktop" Use Application/Browser scope in `DesktopApp.xaml` has a hard-coded `File path` pointing at a developer-machine install location — `C:\Users\original_user\AppData\Local\GitHubDesktop\app-3.5.12\githubdesktop2.exe` — that does not exist on the robot machine MOCK-HOST. Because the scope is set to open the app (no `Open` mode set, so it defaults to "If not open"), it tried to launch that exact executable, the file was not there, and the scope threw `ApplicationOpenException` before any activity inside it could run.

**What went wrong:** Job for process **ERN** (folder **Shared**) faulted at the "GitHub Desktop" Use Application/Browser scope because the configured application path does not resolve on the machine that ran the job.

**Why:** The "GitHub Desktop" scope's target application `File path` is pinned to a per-user, version-specific path (`...\GitHubDesktop\app-3.5.12\githubdesktop2.exe`) under the developer's own profile. The scope has no `Open` mode attribute, which defaults to **If not open** — so on every run the scope attempts to start that executable itself. On robot machine MOCK-HOST that exact file is absent (GitHub Desktop not installed there, or installed under a different `app-x.y.z` version folder / different user profile), so the launch path (`IsOpenApplicationEnabled → ActivateApplicationAsync → NApplicationCard.OpenOrAttach → GetMainWindowByTargetApp`) failed immediately with `UiPath.UIAutomationNext.Exceptions.ApplicationOpenException: Could not open target application. Specified file path ... does not refer to an existing file.` The job faulted ~1.4 seconds after entering Running, before the scope's single inner activity (the "Click 'Changes'" Click) ever executed. This is contained entirely within the UI Automation layer; Orchestrator only dispatched the job.

**Evidence:**

### UI Automation (Root Cause)
- Faulted activity: the **"GitHub Desktop"** Use Application/Browser scope (`NApplicationCard`) in `DesktopApp.xaml`, the job's entry point — not an inner element activity.
- Exception (identical across job Info, Error log, and trace root span): `UiPath.UIAutomationNext.Exceptions.ApplicationOpenException: Could not open target application. Specified file path C:\Users\original_user\AppData\Local\GitHubDesktop\app-3.5.12\githubdesktop2.exe does not refer to an existing file.`
- Scope target `File path` read verbatim from `DesktopApp.xaml` (lines 112–119): `C:\Users\original_user\AppData\Local\GitHubDesktop\app-3.5.12\githubdesktop2.exe` — character-for-character identical to the path in the runtime error. `Arguments` and `WorkingDirectory` are empty.
- Scope has **no `Open` mode attribute** set; absent `Open` mode defaults to **If not open**, so the scope launches the app. The exception class is `ApplicationOpenException` (launch attempted and failed), not `ApplicationNotFound` (the "Never" case) and not `WrongTargetApplicationException`.
- Runtime .NET stack originates at `DriverApplicationService.IsOpenApplicationEnabled → ActivateApplicationAsync → NApplicationCard.OpenOrAttach → GetMainWindowByTargetApp` — the launch code path.
- The scope's only inner activity, the **"Click 'Changes'"** Click, never executed: no Click frame in the stack, no per-activity trace. Job history: Running 2026-06-05T07:34:54.750Z → Faulted 2026-06-05T07:34:56.183Z (~1.4s).
- Job: key `e4237b15-1574-4c7a-8657-fe0b0be2aa75` (Id 66152281), process ERN, folder Shared (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`), Attended/Agent, machine MOCK-HOST, `ErrorCode=Robot`, `HealingEnabled=false`.
- Open gap (non-blocking): direct filesystem inspection of MOCK-HOST was not possible; the runtime "does not refer to an existing file" detail is treated as authoritative for that machine.

**Immediate fix:**

### UI Automation (Root Cause)
1. Open `DesktopApp.xaml` and correct the "GitHub Desktop" scope's target application `File path` so it resolves on the robot machine — point it at the install location actually present on MOCK-HOST, or deploy GitHub Desktop to that machine. Prefer an environment-agnostic path over the hard-coded developer path.
  - Why: the scope's `File path` is `C:\Users\original_user\AppData\Local\GitHubDesktop\app-3.5.12\githubdesktop2.exe`, and the runtime reports that exact file "does not refer to an existing file" on MOCK-HOST; this is the missing/moved-executable cause.
  - Where: `C:\Users\original_user\Documents\UiPath\ERN\DesktopApp.xaml` → the "GitHub Desktop" Use Application/Browser activity → Target → **File path** (the `TargetApp.FilePath` at lines 112–119).
  - Who: RPA developer.
  - Source: `application-open-failed.md` § Resolution ("File path wrong/missing on the robot").
2. Do **not** change `Open` to "Never" to sidestep the launch — that only converts this into an `ApplicationNotFound` when the app is absent. Fix the launch itself (step 1).
  - Why: the scope currently launches the app (no `Open` mode → defaults to "If not open"); switching to "Never" would not make GitHub Desktop present, it would just change the exception.
  - Where: same scope, `Open` mode setting.
  - Who: RPA developer.
  - Source: `application-open-failed.md` § Resolution (final note).

**Preventive fix:**

1. UI Automation — Replace the hard-coded per-user, version-pinned executable path with an environment-agnostic reference, so the scope resolves regardless of which machine or GitHub Desktop version is installed.
  - Why: the failing path embeds both the developer's user profile (`C:\Users\original_user\...`) and a specific app version (`app-3.5.12`); both break on any other machine and on any GitHub Desktop update. Use a stable launcher (e.g., the version-independent `GitHubDesktop.exe` stub UpdateExe maintains under `%LocalAppData%\GitHubDesktop`), a config asset/argument supplying the path per environment, or rely on attaching to an already-open window rather than launching by absolute path.
  - Where: `DesktopApp.xaml` → "GitHub Desktop" scope → Target → **File path** / `Arguments`.
  - Who: RPA developer.
  - Source: `application-open-failed.md` § Resolution ("Prefer an environment-agnostic path over a hard-coded developer path").
2. UI Automation — Standardize the robot environment so the target application is reliably installed on every machine that runs ERN, and verify it is present on MOCK-HOST.
  - Why: the runtime reports the executable absent on MOCK-HOST; correcting only the XAML path will still fail if the app is genuinely not installed there.
  - Where: robot machine MOCK-HOST (and any other machine in the ERN execution pool) — install/deploy GitHub Desktop to the path the workflow targets.
  - Who: platform team / admin.
  - Source: `application-open-failed.md` § Resolution ("...or deploy the application to the robot").

**Investigation summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The "GitHub Desktop" Use Application/Browser scope in `DesktopApp.xaml` launches the app (no `Open` mode → defaults to "If not open"), but its `File path` `...\app-3.5.12\githubdesktop2.exe` does not exist on robot machine MOCK-HOST, so the scope threw `ApplicationOpenException` before any inner activity ran. | High | Confirmed | Yes | `ApplicationOpenException: ...does not refer to an existing file` (job Info, Error log, trace root span); XAML `File path` matches the runtime path verbatim with no `Open` mode attribute; launch-path .NET stack; inner "Click 'Changes'" never ran; faulted ~1.4s into job `e4237b15-...` on MOCK-HOST, `ErrorCode=Robot`. | Correct the scope's `File path` to a location present on the robot (or deploy the app there); do not switch `Open` to "Never". Long term, replace the hard-coded developer/version-pinned path and standardize the robot environment. |

---

The playbook's resolution is a direct-edit fix (no interactive recovery flow — Healing was disabled on this job), so there's nothing for me to auto-apply with your approval.

What would you like next?

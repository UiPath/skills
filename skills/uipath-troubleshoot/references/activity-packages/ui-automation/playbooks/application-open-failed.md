---
confidence: high
---

# Application Could Not Open — Launch Attempted and Failed

## Context

A `Use Application/Browser` scope (the `NApplicationCard` activity) was configured to **open** the target application — `Open` is `IfNotOpen` or `Always` (anything other than `Never`) — and the launch attempt failed. The scope throws `ApplicationOpenException` before any inner `NClick` / `NTypeInto` / `NGetText` runs, so the inner activities never execute.

What this looks like:
- Exception class: `ApplicationOpenException`
- Friendly message: `Could not open target application.`
- The faulted activity is the `Use Application` / `Use Browser` / Application Card scope, not an inner element activity.
- The scope's `Open` mode is `IfNotOpen` or `Always` (NOT `Never`) — the scope tried to start the app itself.

What can cause it:
- The `File path` / `Arguments` point at an executable that is missing, moved, or not installed on the robot machine.
- The application started but its window never appeared within the scope timeout (slow cold start, splash screen, license/activation dialog that blocks startup).
- A login, consent, or "another instance is running" dialog intercepts the launch.
- For browsers: the browser is not installed, or the WebDriver/browser extension required by the chosen browser type could not be initialized.
- The robot lacks the rights to launch the process (elevation required, blocked by policy).

What to look for:
- Confirm the exception is `ApplicationOpenException`, not `ApplicationNotFound` (that one is the `Open = Never` case — the scope was told not to launch; use the application-not-found playbook) and not `WrongTargetApplicationException` (the scope reached a different app — see wrong-target-application).
- Read the scope's `File path`, `Arguments`, and `Open` mode from the workflow source.
- Check the robot/environment: is the executable present at that path on the machine that ran the job? Was the app already mid-launch?

## Investigation

1. From the failed job, capture the exception class, message, and the scope activity's name and workflow file.
2. Open the workflow and read the scope's `Target application` settings: `File path`, `Arguments`, `Open` mode, and the application/window selector.
3. Verify the `File path` resolves on the robot machine (correct install location, drive, and bitness). A path that exists on the developer machine but not the robot is the most common cause.
4. Check whether the launch is blocked: look for a login/activation/consent dialog the app shows on first start, or a "running as a different user / elevation" requirement.
5. For a browser scope: confirm the browser is installed and the browser type matches; confirm the browser extension / WebDriver could initialize.
6. Check timing: if the app cold-starts slowly, the window may not be ready before the scope timeout expires.

## Resolution

- **File path wrong/missing on the robot:** correct `File path` (and `Arguments`) to the install location present on the robot, or deploy the application to the robot. Prefer an environment-agnostic path over a hard-coded developer path.
- **Launch blocked by a startup dialog:** the dialog is the originating fault — handle it deterministically (dismiss/sign in before the scope, or configure the app to skip it), rather than retrying the open blindly.
- **Permissions/elevation:** run the robot with the rights the app needs, or configure the app to start without elevation.
- **Browser not installed / WebDriver issue:** install the matching browser, align the browser type, and ensure the required extension/WebDriver is available on the robot.
- **Slow cold start:** raise the scope timeout to cover the app's genuine startup time. Do not raise it blindly — confirm the app does eventually open.

Do not switch `Open` to `Never` to avoid the launch — that only converts this into an `ApplicationNotFound` when the app is absent. Fix the launch itself.

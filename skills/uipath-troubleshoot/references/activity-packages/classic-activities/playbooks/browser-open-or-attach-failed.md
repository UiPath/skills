---
confidence: medium
---

# Browser Could Not Open or Attach

## Context

A classic browser activity failed to open, attach to, or close a browser, throwing a browser
operation error (`BrowserOperationException`) or an invalid-browser error. Applies to `Open Browser`,
`Attach Browser` (Browser Scope), and `Close Tab`.

What this looks like:
- `BrowserOperationException`, or an error indicating the browser is invalid / not available
- `Open Browser` fails to start the browser, or starts it but the automation cannot communicate with
  it
- `Close Tab` / `Attach Browser` fails because there is no live browser to act on

What can cause it:
- The selected browser is not installed on the robot machine, or is a different major version than
  expected
- The UiPath browser extension is missing, disabled, or not allowed by browser/enterprise policy
- The browser type does not match the communication method (e.g. a custom browser, or WebDriver,
  used with an unsupported browser)
- The browser process crashed, was closed by the user/another step, or never finished launching
- `Attach Browser`/`Close Tab` run against a browser that is no longer open (a previous step closed
  it, or it was never opened in this execution)
- Profile/user-data conflicts prevent a new browser instance from starting

What to look for:
- Which browser and communication method the activity is configured for
- Whether that browser is installed and the UiPath extension is enabled on the robot machine
- Whether a browser instance was actually open and still alive when the failing activity ran
- Whether the same workflow opened the browser earlier and whether that open succeeded

## Investigation

1. Identify the failing activity and its configured browser type and communication method.
2. Confirm the browser is installed on the robot machine and note its version.
3. Verify the UiPath browser extension is installed and enabled for that browser, and not blocked by
   policy.
4. For `Attach Browser`/`Close Tab`, trace back to where the browser was opened — confirm it opened
   successfully and was still alive at the point of failure.
5. Check for browser/communication-method incompatibility (custom browser, or WebDriver, with an
   unsupported browser type) — see [ui-activity-configuration-error.md](./ui-activity-configuration-error.md).
6. Check robot logs / event log for a browser crash around the failure time.

## Resolution

- **If the browser is not installed or wrong version:** install/repair the supported browser version
  on the robot machine.
- **If the extension is missing/disabled/blocked:** install and enable the UiPath browser extension;
  allow it through browser or enterprise policy.
- **If `Attach`/`Close` ran with no live browser:** fix the flow so the browser is opened (and its
  open verified) before attaching or closing; handle the case where a prior step closed it.
- **If the browser crashed mid-run:** address the crash cause (resources, conflicting profile,
  incompatible version) and re-open the browser cleanly.
- **If browser type and communication method are incompatible:** correct the configuration per
  [ui-activity-configuration-error.md](./ui-activity-configuration-error.md).

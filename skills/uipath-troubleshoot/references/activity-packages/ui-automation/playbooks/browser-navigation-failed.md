---
confidence: medium
---

# Go To URL — Navigation Failed

## Context

A `Go To URL` activity (`NGoToUrl`) could not navigate the attached browser to the requested address. The browser context was reached, but the navigation itself failed or the URL was not usable.

What this looks like:
- One of these signatures during a `Go To URL`:
  - `Required argument 'URL' was not provided.` — the `Url` input was empty/whitespace at runtime.
  - `Requested URL is invalid, value is null.` (`BrowserInvalidURLException`)
  - `Failed to navigate to the specified URL.` (`BrowserFailedToNavigateToUrlException`)
  - For a local file address on a Chromium browser: `Failed to open the indicated local URL.\nPlease go to "Extensions" and enable "Allow access to file URLs".`

What can cause it:
- The `Url` value is empty at runtime — typically a variable/expression that an earlier step was supposed to populate but didn't.
- The URL is malformed (missing scheme, stray characters).
- The site/host is unreachable from the robot (network, DNS, proxy, certificate).
- No browser is attached — `Go To URL` runs outside a live `Use Browser` context.
- A local `file://` URL is used with a Chromium browser whose extension does not have "Allow access to file URLs" enabled.

What to look for:
- Confirm the faulting activity is `Go To URL`.
- Read where the `Url` value comes from (literal vs variable) and what it evaluates to.
- Check whether a `Use Browser` scope is active around the activity.

## Investigation

1. From the failed job, capture which of the messages above appeared and the `Go To URL` activity + workflow.
2. Read the `Url` input. If it is a variable/expression, trace the upstream step that should produce it; an empty value means that step did not run or returned nothing.
3. If the URL is present, validate its format (scheme + host).
4. Confirm a `Use Browser` scope encloses the activity and was attached at this point.
5. For navigation failures on a present, well-formed URL: check robot-side reachability (network/proxy/cert) to that host.
6. For a `file://` URL on Chromium: check the "Allow access to file URLs" extension permission.

## Resolution

- **Empty `Url`:** fix the upstream step that should produce the value — do not hard-code a literal to paper over a missing producer unless the URL is genuinely static.
- **Malformed URL:** correct the address (include the scheme).
- **Site unreachable:** resolve the robot-side connectivity/proxy/certificate issue to that host.
- **No browser attached:** ensure `Go To URL` runs inside a live `Use Browser` scope.
- **Local file URL on Chromium:** enable "Allow access to file URLs" for the automation extension on that browser.

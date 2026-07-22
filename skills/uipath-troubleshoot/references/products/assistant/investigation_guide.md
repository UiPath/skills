# UiPath Assistant Investigation Guide

Read `overview.md` for the two-log architecture and evidence model before this guide.

## Rules for this domain

1. **Anchor on the reported symptom before opening any log.** A log is a wall of noise; know what you are looking for first. If the user hasn't said what happened, ask in one sentence: what they tried, what they saw, roughly when.
2. **A stack trace with a function name beats log grepping.** If the user can paste one (e.g. `at InteractiveConnectFlow.SignIn`), use it to route straight to the matching playbook via `summary.md`.
3. **Never grep blindly for "error".** Every archive holds hundreds of benign errors (offline-state noise, expected shutdown IPC timeouts). Correlate to the anchored symptom, not to the string `error`.
4. **Mind the timezones.** `Robot.log` is machine-local with an offset (e.g. `+03:00`); `combined.log` is usually UTC. Convert before correlating timestamps across the two files.
5. **Never speculate past the evidence.** A timeout means "timeout — likely network"; do not guess DNS vs proxy vs firewall without data. Ask for `curl`/network output instead.
6. **Never assume the archive is complete.** Users often paste only the first N lines. If the symptom should have left a trace and you can't find it, ask for the full file.

## Step 1 — Ask for high-value artifacts if the archive is thin

`combined.log` captures only main-process logs. These often pinpoint the cause in seconds when the log alone can't:

- **DevTools console output** — renderer-side errors, unhandled rejections, stack traces with function names (never reach `combined.log`).
- **HAR file / Network tab** — failed HTTP calls with status codes, request/response bodies, timings.
- **Screenshot / recording** of the error toast or dialog, plus the **exact on-screen error text** (usually more specific than what reached disk).

## Step 2 — Scan combined.log first

The Electron/Assistant side: user clicks, IPC routes invoked, UI state transitions. Fastest way to see *what the user did* and *how the app responded*.

Look for:
- The IPC route matching the reported action — `/robot/interactiveConnectSignIn` (sign-in), `/robot/connectToServer` (orchestrator connect), `/process/start` (run a process).
- The `result` field on `Finished running handler` lines — `false` / `null` / missing often means a silent failure.
- Repeated identical calls within seconds → the user clicking over and over because nothing happens.
- `channel/*/robotUserStatus` and `channel/*/robotStatus` messages — Offline/Connected state transitions.
- Any `error` / `isError: true` entries **on the anchored route** (Rule 3).

Note the timestamps of the failing actions — you will correlate them with `Robot.log`.

## Step 3 — Cross-reference Robot.log

The native Robot service (C#/.NET). Apply the timezone rule (Rule 4) before matching timestamps.

Look for:
- `[ERROR]` entries near the failing-action timestamp.
- Stack traces with `UiPath.Service.*` or `UiPath.RobotJS.*` namespaces — the class name (e.g. `InteractiveConnectFlow.SignIn`, `CloudConnectFlow.TryOpenFlow`) tells you exactly which flow failed.
- The failing HTTP endpoint — note the host. `cloud.uipath.com` (production), another UiPath cloud environment, or an on-prem Orchestrator URL tells you which environment the app is pointed at.

Route the exception class/endpoint to the matching playbook via `summary.md`.

## Step 4 — Attribute the flow and decide the next action

If `Robot.log` names a class/method (e.g. `InteractiveConnectFlow.SignIn`), use the flow name and namespace (`overview.md` § Reading the named flow) to attribute the failure to a layer and route to the matching playbook via `summary.md`.

Then split on where the root cause lives:

- **User-side cause** (network, VPN/proxy/firewall, DNS, wrong environment, tenant/license/assignment) — the playbook's resolution steps apply; give the user the exact fix and commands to verify.
- **Product-side cause** — the evidence points at a defect inside the Assistant or Robot itself, not anything the user controls. Capture the exact trace (flow name, exception, timestamps) and report it to UiPath support; do not speculate past what the log shows.

## Data correlation

Before concluding from any log line, verify it matches the reported problem:

- **Symptom** — the route/exception is the action the user reported (sign-in vs connect vs start), not a nearby unrelated error.
- **Timestamp** — the line falls in the window the user described, after the timezone conversion (Rule 4).
- **Environment** — the endpoint host matches the tenant the user is on.

If it doesn't match: discard it and keep looking. Do not attribute the failure to the first `[ERROR]` you find.

## Presenting

Deliver a concise report (see also `references/presenting.md`):
1. **Root cause** — one specific sentence (e.g. "DNS resolution of `cloud.uipath.com` timing out — VPN not connected").
2. **Evidence** — the specific log line(s) with file path and line number; clickable links where possible (`[Robot.log:1229](file:///.../Robot.log)`).
3. **What to try** — ordered by likelihood, with exact commands where applicable (`curl`, `nslookup`, etc.).
4. **Any UX bug worth filing separately** — e.g. a silent 30s failure with no error toast, even when the underlying cause is external.

---
name: uipath-assistant-diagnostics
description: "Diagnose UiPath Assistant desktop-app failures from a diagnostic archive (ExportDiagnoseArchive folder, combined.log, or Robot.log). Use when a user shares Assistant logs and wants the root cause of sign-in failures, orchestrator connection issues, missing or unstartable processes, or crashes. Anchor on the reported symptom, scan combined.log (Electron/IPC side) first, correlate Robot.log (native .NET Robot service — watch the timezone offset), then drill into Assistant/Robot/Orchestrator/Identity source when a log names a flow. Trigger on phrases like 'a user reported', 'check this diagnostic archive', 'here is the log', or any mention of combined.log / Robot.log. For platform-side causal investigation via the uip CLI (jobs, queues, connectors, cloud resources)→uipath-troubleshoot."
---

# Diagnose a UiPath Assistant diagnostic archive

The user has shared a diagnostic archive (or a log from one) and wants the root cause of a reported UiPath Assistant issue — sign-in failures, orchestrator connection problems, missing processes, crashes, etc.

## When to Use This Skill

- The user shares an `ExportDiagnoseArchive` folder, a `combined.log`, or a `Robot.log`.
- They paste a stack trace, error toast text, or DevTools console output from the Assistant desktop app.
- Phrases like "a user reported", "check this diagnostic archive", "here's the log".

Do NOT use for platform/cloud causal investigation driven by the `uip` CLI (job faults, queue items, connectors, tenant resources) — that is `uipath-troubleshoot`.

## Critical Rules

1. **Anchor on the reported symptom before opening any log.** Logs are a wall of noise; know what you are looking for first. If the user hasn't said what happened, ask in one sentence (what they tried, what they saw, roughly when).
2. **A stack trace with a function name beats log grepping.** If the user can paste one (e.g. `at connectToOrchestrator`), skip straight to source search (Step 4).
3. **Never grep blindly for "error".** Every archive has hundreds of benign errors (offline-state noise, expected shutdown IPC timeouts). Correlate to the anchored symptom instead.
4. **Mind the timezones.** `Robot.log` uses machine-local time with an offset (e.g. `+03:00`); `combined.log` is usually UTC. Convert before correlating timestamps across the two files.
5. **Never speculate past the evidence.** A timeout means "timeout — likely network"; do not guess DNS vs proxy vs firewall without data. Ask for `curl`/network output instead.
6. **Never assume the archive is complete.** Users often paste only the first N lines. If the symptom should have left a trace and you can't find it, ask for the full file.

## Workflow

### Step 1 — Ask for high-value artifacts if the archive alone is thin

The archive's `combined.log` captures only main-process logs. These often pinpoint the cause in seconds when the log alone can't:

- **DevTools console output** — renderer-side errors, unhandled rejections, stack traces with function names (never land in combined.log).
- **HAR file / Network tab** — failed HTTP calls with status codes, request/response bodies, timings.
- **Screen recording / screenshot** of the error toast or dialog, plus the **exact on-screen error text** (usually more specific than what reached disk).

### Step 2 — Scan combined.log first

`combined.log` is the Electron/Assistant side: user clicks, IPC routes invoked, UI state transitions. Fastest way to see *what the user did* and *how the app responded*.

Look for:
- The IPC route matching the reported action (`/robot/interactiveConnectSignIn` for sign-in, `/robot/connectToServer` for orchestrator connect, `/process/start` for running a process).
- The `result` field on `Finished running handler` lines — `false` / `null` / missing often means a silent failure.
- Repeated identical calls within seconds → the user clicking over and over because nothing happens.
- `channel/*/robotUserStatus` and `channel/*/robotStatus` messages — Offline/Connected state transitions.
- Any `error` / `isError: true` entries.

Note the timestamps of the failing actions — you'll correlate them with Robot.log.

### Step 3 — Cross-reference Robot.log

`Robot.log` is the native Robot service (C#, .NET). Apply the timezone rule (Critical Rule 4).

Look for:
- `[ERROR]` entries near the failing-action timestamp.
- Stack traces with `UiPath.Service.*` or `UiPath.RobotJS.*` namespaces — the class name (e.g. `InteractiveConnectFlow.SignIn`, `CloudConnectFlow.TryOpenFlow`) tells you exactly which flow failed.
- Common root causes:
  - `TaskCanceledException` / `HttpClient.Timeout` → network reachability (DNS, VPN, proxy, firewall).
  - `HttpRequestException` on `/discovery_` or `/identity_` → OAuth/OIDC flow can't reach cloud.
  - `401` / `403` from backend → token/permission issue.
  - `NU1101` / package errors → NuGet feed unreachable.
- The failing HTTP endpoint is gold — note the host. `cloud.uipath.com`, `alpha.uipath.com`, `staging.uipath.com`, or an on-prem Orchestrator URL tells you the environment.

### Step 4 — Drill into source when a log names a specific flow

If Robot.log names a class/method (e.g. `InteractiveConnectFlow.SignIn at line 86`) and you need to understand what it should do or why it returned a given value:

**Assistant code (`UiPath/Assistant` repo).** If checked out locally, search it (grep/glob). Typical hotspots:
- `projects/electron-host/src/server/controllers/` — IPC route handlers.
- `projects/electron-host/src/providers/robot/` — bridge to the native Robot service.
- `projects/shared/angular/src/providers/services/` — UI-side services.

**Robot code (`UiPath/Studio` repo, under a `Robot/` subdirectory).** Check if it's local:
```bash
ls ~/projects/Studio 2>/dev/null || ls ~/repos/Studio 2>/dev/null
```
If found, `git -C <path> checkout develop && git -C <path> pull`, then grep its `Robot/` subtree. If not local, search GitHub:
```bash
gh search code --owner UiPath "InteractiveConnectFlow.SignIn" --repo UiPath/Studio
gh api repos/UiPath/Studio/contents/Robot/UiPath.Service/UserServices/InteractiveConnectFlow.cs
```

**Other repos** when the issue crosses service boundaries:
- **Orchestrator** — `UiPath/Orchestrator` for 4xx/5xx from `/odata/*` or `/api/*`.
- **Identity** — `UiPath/Identity.Service` for OAuth / token / `/identity_/*` issues.

Confirm a repo name with `gh search repos UiPath/<guess>` if unsure.

### Step 5 — Report findings

Deliver a concise report:
1. **Root cause** — one specific sentence (e.g. "DNS resolution of `cloud.uipath.com` timing out — VPN not connected").
2. **Evidence** — the specific log line(s) with file path and line number; clickable markdown links where possible (`[Robot.log:1229](file:///.../Robot.log)`).
3. **What to try** — ordered by likelihood, with exact commands where applicable (`curl`, `dscacheutil`, etc.).
4. **Any UX bug worth filing separately** — e.g. a silent 30s failure with no error toast, even when the underlying cause is external.

## What NOT to Do

- **Don't grep blindly for "error"** — anchor on the symptom first (Critical Rule 3).
- **Don't mix up timezones** when correlating timestamps across the two log files.
- **Don't speculate past the evidence** — report what the log proves, then ask for the data that would confirm the next hypothesis.
- **Don't assume the archive is complete** — ask for the full file when an expected trace is missing.

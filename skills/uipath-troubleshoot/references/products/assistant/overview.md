# UiPath Assistant (Desktop)

Windows desktop app end users run to sign in, connect to Orchestrator, and start/stop the automations (processes) assigned to them. When it fails, the user exports a **diagnostic archive** and shares it — this domain diagnoses that archive.

## Architecture

Two layers, two logs:

```
UiPath Assistant (Electron)
  ├── Angular renderer        ← the UI the user clicks (DevTools console lives here)
  └── main process            ← IPC routing, app lifecycle          → combined.log
        │  (local IPC)
        ▼
  UiPath Robot service (native .NET)                                → Robot.log
        │  (HTTPS)
        ▼
  Orchestrator · Identity/cloud · NuGet feeds
```

- **`combined.log`** — Electron/main-process side: user clicks, which IPC route was invoked, `result` fields, UI status transitions. Usually UTC. Shows *what the user did* and *how the app responded*.
- **`Robot.log`** — native Robot service (C#/.NET): the actual sign-in / connect / package / process work. **Machine-local time with an offset** (e.g. `+03:00`) — convert before correlating with `combined.log`.

## Evidence model

Diagnosis is **on-disk log files + the reported symptom** — there is **no `uip` CLI job/trace/log surface** for the Assistant desktop app (unlike Orchestrator jobs). The "raw data" is the archive files the user already shared, plus higher-value artifacts you ask for (DevTools console, HAR, screenshots). Do not fabricate `uip` commands for this domain.

Archive shape: an `ExportDiagnoseArchive` folder (or a loose `combined.log` / `Robot.log`) produced by the Assistant's **Help → Export diagnostic data** action.

## Dependencies

- **Orchestrator** — the tenant the Assistant connects to; process list, job start. 4xx/5xx here → cross-reference the `orchestrator` domain.
- **Identity / cloud** — OAuth/OIDC sign-in (`/identity_/*`, `/discovery_*`). Auth failures surface here.
- **NuGet feeds** — process packages download from Orchestrator/feed on first start. Feed-unreachable → `NU1101` / package errors.
- **Network** — VPN, proxy, firewall, DNS between the machine and cloud/on-prem Orchestrator.

## Reading the named flow

`Robot.log` traces name the flow that failed (class/method, e.g. `InteractiveConnectFlow.SignIn`, `CloudConnectFlow.TryOpenFlow`) — that name, plus the namespace, tells you which layer to attribute the failure to without needing product source:

- **`UiPath.Service.*` / `UiPath.RobotJS.*`** in `Robot.log` — the native Robot service (sign-in, Orchestrator connect, package/process work).
- **IPC routes** in `combined.log` (`/robot/*`, `/process/*`) — the Assistant Electron app.

Use the flow name to route to the right playbook via `summary.md` and to describe the failing step precisely in your report. If the evidence points at a defect inside the Assistant or Robot itself — not the user's network, configuration, or tenant — capture the exact trace and report it to UiPath support.

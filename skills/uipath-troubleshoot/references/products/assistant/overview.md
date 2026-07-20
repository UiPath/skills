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

## Source repositories (for drill-down)

When a log names a specific flow and you need to know what it should do:

- **`UiPath/Assistant`** — the Electron app. IPC route handlers (`projects/electron-host/src/server/controllers/`), Robot bridge (`projects/electron-host/src/providers/robot/`), UI services (`projects/shared/angular/src/providers/services/`).
- **`UiPath/Studio`** (`Robot/` subtree) — the native Robot service. Flow classes like `InteractiveConnectFlow`, `CloudConnectFlow`.
- **`UiPath/Orchestrator`** — 4xx/5xx from `/odata/*` or `/api/*`.
- **`UiPath/Identity.Service`** — OAuth / token / `/identity_/*` issues.

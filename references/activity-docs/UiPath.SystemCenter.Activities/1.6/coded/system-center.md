# System Center Activities API Reference

Reference for the `systemCenter` service from `UiPath.SystemCenter.Activities` package.

**Required package:** `"UiPath.SystemCenter.Activities": "[1.0.0]"`

**Auto-imported namespaces:** `UiPath.SystemCenter.Core`, `UiPath.Core`, `UiPath.SystemCenter.Models`

**Service accessor:** `systemCenter` (type `ISystemCenterService`)

---

## Architecture

The System Center API uses a factory pattern with a single sub-service:

1. **`ISystemCenterService`** — Top-level service accessed via the `systemCenter` accessor. Creates `IRunbookService` instances.
2. **`IRunbookService`** — Provides all runbook operations (get servers, get/start/stop runbooks, manage jobs and instances).

All operations require an `ISystemCenterClientProvider` for authentication to the System Center Orchestrator.

### Accessing the Service

```csharp
// Create the runbook service with a System Center client provider
IRunbookService runbookService = systemCenter.RunbookService(clientProvider);

// Now use runbookService to manage runbooks
RunbookServer[] servers = await runbookService.GetRunbookServers();
```

---

## Key Model Types

| Type | Description |
|---|---|
| `ISystemCenterClientProvider` | System Center authentication/client provider (from `UiPath.SystemCenter.Interfaces`) |
| `RunbookServer` | Represents a System Center Orchestrator runbook server |
| `Runbook` | Represents a runbook definition |
| `RunbookInstance` | Represents a running instance of a runbook |
| `RunbookJob` | Represents a runbook job (started execution) |

---

For the full API reference, see [api.md](api.md).

For complete coded workflow examples, see [examples.md](examples.md).

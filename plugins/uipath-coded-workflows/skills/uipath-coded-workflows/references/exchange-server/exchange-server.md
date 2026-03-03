# Exchange Server Activities API Reference

Reference for the `exchangeserver` service from `UiPath.ExchangeServer.Activities` package.

**Required package:** `"UiPath.ExchangeServer.Activities": "[1.0.0]"`

**Auto-imported namespaces:** `UiPath.ExchangeServer`

**Service accessor:** `exchangeserver` (type `IExchangeServerService`)

---

## Architecture

The Exchange Server API uses a two-layer factory pattern:

1. **`IExchangeServerService`** — Top-level service accessed via the `exchangeserver` accessor. Acts as a factory that creates `IExchangeService` instances.
2. **`IExchangeService`** — Provides the actual mailbox operations (create, delete, enable/disable archive).

All operations are executed via PowerShell remoting. You must provide an `IPowerShellRemoteService` to establish the remote session to the Exchange Server.

### Accessing the Service

```csharp
// Create the exchange service with a PowerShell remote connection
IExchangeService exchangeService = exchangeserver.ExchangeService(powerShellRemoteService);

// Now use exchangeService to manage mailboxes
exchangeService.CreateMailbox(...);
```

---

## Key Type Reference

| Type | Description |
|---|---|
| `IExchangeServerService` | Top-level service factory. Accessed via `exchangeserver` |
| `IExchangeService` | Mailbox operations service (create, delete, archive) |
| `IPowerShellRemoteService` | PowerShell remote session provider (from `UiPath.ExchangeServer`). Implements `IDisposable`. Has method `ICollection<PSObject> RunScript(string script)` |

---

For the full API reference, see [api.md](api.md).

For complete coded workflow examples, see [examples.md](examples.md).

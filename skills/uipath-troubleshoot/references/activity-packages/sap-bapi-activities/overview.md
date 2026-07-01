# SAP BAPI Activities

Activities from the `UiPath.SAP.BAPI.Activities` package for calling SAP BAPIs / RFC function modules directly over the SAP .NET Connector (NCo / RFC protocol) — no SAP GUI involved. Work runs inside a **SAP Application Scope** (`SapApplicationScope`) that opens an RFC connection; child **Invoke BAPI** (`InvokeBAPI` / `InvokeSapBapi`) activities call a named BAPI through that connection. `SapOpenConnection` / `SapCloseConnection` manage a reusable connection.

## How These Activities Work

1. **Connection.** `SapApplicationScope` (or `SapOpenConnection`) builds an `RfcDestination` from the connection parameters (host/system, client, user, password, language, and any advanced RFC parameters) and opens an RFC connection to the SAP system. Failure here is a connectivity / logon / parameter problem — the BAPI never runs.
2. **BAPI metadata lookup.** Before invoking, the connector retrieves the BAPI's interface (`BAPI_GET_INTERFACE` style metadata) to build its parameters. A BAPI name that doesn't exist (or that the user can't access) fails at this step.
3. **Invoke.** `Invoke BAPI` calls the function module and marshals import/export parameters and tables.

Failures surface as plain framework/connector exceptions carrying a fixed resource string — there is no single SAP-specific wrapper for all of them:

- `SAP.Middleware.Connector.*` NCo exceptions surfaced via `SapConnectionService.Connect` — `RfcConfigurationException` (config/params, e.g. `Not any kind of host is specified`), `RfcCommunicationException` (unreachable), `RfcLogonException` (credentials). Sometimes a UiPath-layer `System.Exception` with a resource string (`Connection could not be created.`, `Cannot create sap connection, connection info params are not set`).
- `UiPath.SAP.BAPI.Utilities.SapActivityException` for invalid advanced parameters.
- `UiPath.SAP.BAPI.SapBapiExceptions.UnSupportedBapiException` (carries an `ErrorCode`) when the BAPI has nested complex types the activity can't marshal.
- `System.TimeoutException` (often wrapping an `RfcCommunicationException`) when the RFC call/connection times out.

## Key Activities

- **SAP Application Scope** (`UiPath.SAP.BAPI.Activities.SapApplicationScope`) — opens the RFC connection for its child activities.
- **Invoke BAPI** (`UiPath.SAP.BAPI.Activities.InvokeBAPI` / `InvokeSapBapi`) — call a named BAPI / RFC function module.
- **Open / Close SAP Connection** (`SapOpenConnection` / `SapCloseConnection`) — manage a reusable connection.

## Common Failure Patterns

- **Connection / logon failure** — NCo `RfcConfigurationException` (e.g. `Not any kind of host is specified`) / `RfcCommunicationException` / `RfcLogonException`, or UiPath-layer `Connection could not be created.` / `Cannot create sap connection, connection info params are not set` / `Missing mandatory field: <field> for connection` / `Advanced Parameters has invalid parameter <param>...` (`SapActivityException`), or `System.TimeoutException`. See [sap-connection-failed.md](./playbooks/sap-connection-failed.md).
- **BAPI not found / not named** — `Function: <name> could not be created` (the BAPI doesn't exist in the connected system or the user can't access it) or `BAPI name is null or empty`. See [sap-bapi-not-found.md](./playbooks/sap-bapi-not-found.md).
- **Unsupported BAPI** — `Unsupported BAPI. Contains nested complex types.` (`UnSupportedBapiException`). See [sap-unsupported-bapi.md](./playbooks/sap-unsupported-bapi.md).

> **Connection-configuration** failures (missing params, invalid advanced parameter) ARE reproducible locally with no SAP system — the SAP .NET Connector rejects the destination before any network call. **BAPI lookup / unsupported-BAPI** failures need a live SAP connection (the scope must connect first). Either way, diagnosis is evidence-based from the faulted job's exception text + the connection/BAPI configuration.

## Package

NuGet: `UiPath.SAP.BAPI.Activities` · Exceptions: `UiPath.SAP.BAPI.Utilities.SapActivityException`, `UiPath.SAP.BAPI.SapBapiExceptions.UnSupportedBapiException`

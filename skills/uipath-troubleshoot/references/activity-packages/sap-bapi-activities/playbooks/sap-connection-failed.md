---
confidence: medium
---

# SAP — Connection / logon failure

## Context

A SAP BAPI activity faults while opening the RFC connection (`SAP Application Scope` / `Open SAP Connection`), before any BAPI runs. The cause is the connection parameters, SAP system reachability, or the logon — never the BAPI itself.

What this looks like — the fault often comes straight from the SAP .NET Connector (NCo), `SAP.Middleware.Connector.*`, via `SapConnectionService.Connect`:

- `SAP.Middleware.Connector.RfcConfigurationException: Not any kind of host is specified` — **verified**: no application server / message server was configured (empty/missing connection parameters). Thrown by `RfcDestination.CheckConfiguration()` before any network call. Other `RfcConfigurationException` variants name the specific missing/invalid field the same way.
- `SAP.Middleware.Connector.RfcCommunicationException` — the host is specified but unreachable (wrong host/port/route, network/firewall, SNC mismatch, or the SAP system is down).
- `SAP.Middleware.Connector.RfcLogonException` — reached the system but logon was rejected (wrong/expired password, locked user, wrong client, missing RFC authorization).
- `Advanced Parameters has invalid parameter <param>. Connection cannot be established.` (`UiPath.SAP.BAPI.Utilities.SapActivityException`) — an advanced RFC parameter is malformed/unrecognized (a UiPath-layer check).
- UiPath-layer messages `Connection could not be created.` / `Cannot create sap connection, connection info params are not set` / `Missing mandatory field: <field> for connection` (`System.Exception`) may appear when the UiPath connection layer catches the failure before NCo — treat them as the same connection-config family.
- `System.TimeoutException` — the connection (or a subsequent RFC call) timed out (network, host down, or saturated).

What can cause it:
- **SAP system unreachable** — wrong host/system id/port, network/firewall/SNC route, or the SAP system is down.
- **Logon rejected** — wrong/expired password, locked SAP user, or the RFC user lacks logon/RFC authorization.
- **Incomplete / invalid parameters** — a mandatory connection field is empty, or an advanced RFC parameter is invalid.
- **Timeout** — host not answering (network/host) or an overloaded SAP system.

What to look for:
- All of these fire from the connection/scope, not the `Invoke BAPI` call. The **NCo exception class is the discriminator**: `RfcConfigurationException` = a config/parameter gap (fix the connection inputs — e.g. `Not any kind of host is specified` means no server set); `RfcCommunicationException` = reachability; `RfcLogonException` = credentials/authorization. `Connection could not be created.` / `TimeoutException` need the connection parameters and SAP-side context to narrow.

> **Different cause — do not apply this playbook:**
> - `Function: <name> could not be created` / `BAPI name is null or empty` → the connection opened; the BAPI lookup failed → use [sap-bapi-not-found.md](./sap-bapi-not-found.md).
> - `Unsupported BAPI. Contains nested complex types.` → the BAPI choice is incompatible → use [sap-unsupported-bapi.md](./sap-unsupported-bapi.md).

## Investigation

1. **Confirm the failure is at the scope/open-connection step** (`SapApplicationScope.Connect` → `SapConnectionService.Connect`; exception is an `RfcConfigurationException`/`RfcCommunicationException`/`RfcLogonException`, a UiPath connection string, `SapActivityException`, or `TimeoutException`) — the BAPI never ran.
2. **Read the NCo exception class + message** to classify: config (`RfcConfigurationException`, e.g. `Not any kind of host is specified`), reachability (`RfcCommunicationException`), or logon (`RfcLogonException`). Then capture the connection parameters — SAP host/system id, client, user, language, advanced RFC parameters (do not expose the password).
3. **For `RfcConfigurationException` / `params not set` / `Missing mandatory field`:** identify the empty/invalid connection field.
4. **For `RfcCommunicationException` / `Connection could not be created.` / `TimeoutException`:** with the Basis/SAP team, check whether the SAP system was reachable in the failure window. **For `RfcLogonException`:** check whether the RFC user is locked / has the wrong password / lacks authorization.

## Resolution

- **If `RfcConfigurationException` (e.g. `Not any kind of host is specified`) / `params are not set` / `Missing mandatory field: <field>`:** supply the missing connection parameter(s) on the SAP Application Scope — at minimum an Application Server (host + system number) or a Message Server, plus client/user/password.
- **If `Advanced Parameters has invalid parameter <param>`:** correct or remove the invalid advanced RFC parameter.
- **If `RfcCommunicationException` / `Connection could not be created.`:** verify host/system id, client, port/route, and SNC/SSL settings; with the SAP admin, confirm the system is up. Recheck network/firewall reachability from the robot host.
- **If `RfcLogonException`:** with the SAP admin, confirm the RFC user can log on (unlock the user / reset credentials / grant RFC authorization; verify the client).
- **If `System.TimeoutException`:** confirm SAP host reachability and load; increase the connection/RFC timeout if the SAP side is legitimately slow; retry transient communication timeouts. Treat as a config problem only if it recurs consistently.

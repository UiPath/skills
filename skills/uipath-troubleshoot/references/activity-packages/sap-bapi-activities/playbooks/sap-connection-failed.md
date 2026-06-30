---
confidence: medium
---

# SAP — Connection / logon failure

## Context

A SAP BAPI activity faults while opening the RFC connection (`SAP Application Scope` / `Open SAP Connection`), before any BAPI runs. The cause is the connection parameters, SAP system reachability, or the logon — never the BAPI itself.

What this looks like:

- `Connection could not be created.` (`System.Exception`) — the RFC connection to the SAP system could not be opened. Generic: host/system unreachable, wrong port/route, SNC/SSL mismatch, wrong client, or a rejected logon (wrong/expired password, locked user, missing RFC authorization). The message does **not** name which.
- `Cannot create sap connection, connection info params are not set` (`System.Exception`) — the connection was attempted with no/empty connection parameters.
- `Missing mandatory field: <field> for connection` — a required connection field (host/system, client, user, etc.) is empty.
- `Advanced Parameters has invalid parameter <param>. Connection cannot be established.` (`UiPath.SAP.BAPI.Utilities.SapActivityException`) — an advanced RFC parameter is malformed/unrecognized.
- `System.TimeoutException` — the connection (or a subsequent RFC call) timed out; frequently wraps an `RfcCommunicationException` (the SAP host didn't answer in time — network, host down, or saturated).

What can cause it:
- **SAP system unreachable** — wrong host/system id/port, network/firewall/SNC route, or the SAP system is down.
- **Logon rejected** — wrong/expired password, locked SAP user, or the RFC user lacks logon/RFC authorization.
- **Incomplete / invalid parameters** — a mandatory connection field is empty, or an advanced RFC parameter is invalid.
- **Timeout** — host not answering (network/host) or an overloaded SAP system.

What to look for:
- All of these fire from the connection/scope, not the `Invoke BAPI` call. `Cannot create sap connection ... params are not set` / `Missing mandatory field` = a configuration gap (fix the connection inputs). `Connection could not be created.` / `TimeoutException` = reachability or logon — needs the connection parameters and SAP-side context to narrow.

> **Different cause — do not apply this playbook:**
> - `Function: <name> could not be created` / `BAPI name is null or empty` → the connection opened; the BAPI lookup failed → use [sap-bapi-not-found.md](./sap-bapi-not-found.md).
> - `Unsupported BAPI. Contains nested complex types.` → the BAPI choice is incompatible → use [sap-unsupported-bapi.md](./sap-unsupported-bapi.md).

## Investigation

1. **Confirm the failure is at the scope/open-connection step** (exception is a connection string, `SapActivityException`, or `TimeoutException`) — the BAPI never ran.
2. **Capture the connection parameters** — SAP host/system id, client, user, language, advanced RFC parameters (do not expose the password).
3. **For `Cannot create sap connection ... params are not set` / `Missing mandatory field`:** identify the empty field.
4. **For `Connection could not be created.` / `TimeoutException`:** with the Basis/SAP team, check whether the SAP system was reachable in the failure window and whether the RFC user is locked / unauthorized. Determine if a `TimeoutException` wraps an `RfcCommunicationException` (reachability) vs. a slow BAPI.

## Resolution

- **If `Cannot create sap connection ... params are not set` / `Missing mandatory field: <field>`:** supply the missing connection parameter(s) on the SAP Application Scope / connection.
- **If `Advanced Parameters has invalid parameter <param>`:** correct or remove the invalid advanced RFC parameter.
- **If `Connection could not be created.`:** verify host/system id, client, port/route, and SNC/SSL settings; with the SAP admin, confirm the system is up and the RFC user can log on (unlock the user / reset credentials / grant RFC authorization as needed). Recheck network/firewall reachability from the robot host.
- **If `System.TimeoutException`:** confirm SAP host reachability and load; increase the connection/RFC timeout if the SAP side is legitimately slow; retry transient communication timeouts. Treat as a config problem only if it recurs consistently.

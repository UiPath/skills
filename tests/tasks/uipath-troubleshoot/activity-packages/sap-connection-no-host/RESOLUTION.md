# Final Resolution

**Fault:** The `SapOrderSync` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.SAP.BAPI.Activities.SapApplicationScope`** ("SAP Application Scope") while opening the RFC connection, and surfaces as `SAP.Middleware.Connector.RfcConfigurationException`.

**Root cause:** The **SAP connection is not configured** — no application server (host + system number) or message server was provided, so the SAP .NET Connector rejects the destination before any network call. The actionable signature is `SAP.Middleware.Connector.RfcConfigurationException: Not any kind of host is specified`, thrown from `RfcDestination.CheckConfiguration()` via `SapConnectionService.Connect`. This is a connection-configuration gap, not a SAP-side problem — the connection never left the robot.

**Fix:** Configure the SAP Application Scope's connection parameters — at minimum an **Application Server** (host + System Number) *or* a **Message Server** (with Logon Group / System ID), plus **Client**, **User**, and **Password** (and Language). Then re-run.

**Must NOT attribute the root cause to:**
- The **BAPI / Invoke BAPI** — the scope never opened a connection, so no BAPI ran. This is not `Function: <name> could not be created` or `Unsupported BAPI...`.
- A **SAP system outage / unreachable host** — that would be `RfcCommunicationException`; here `RfcConfigurationException: Not any kind of host is specified` means no host was even specified (the request never left the robot).
- A **logon / credentials problem** — that would be `RfcLogonException`; this is a missing-configuration error, before logon.
- A **timeout**, a network/firewall issue, or a workflow-logic bug.

A correct answer identifies that **the SAP Application Scope has no connection configured (`RfcConfigurationException: Not any kind of host is specified`)** and recommends filling in the connection parameters (Application/Message Server + client/user/password). It must read the configuration signature rather than blaming the BAPI, a SAP outage, credentials, or the workflow logic.

# Final Resolution

**Fault:** The `SapMasterDataLoad` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.SAP.BAPI.Activities.SapApplicationScope`** ("SAP Application Scope") while opening the connection, and surfaces as `UiPath.SAP.BAPI.Utilities.SapActivityException`.

**Root cause:** The scope's **Advanced Parameters contain an unsupported RFC parameter key**. The UiPath connection layer parses the advanced parameters and, on encountering a key it doesn't recognize, rejects the connection before any network call. The actionable signature is `UiPath.SAP.BAPI.Utilities.SapActivityException: Advanced Parameters has invalid parameter <key>. Connection cannot be established.` (here `<key>` = `BOGUSKEY`), thrown from `SapConnectionService.OverideWithAdvancedParameters`.

**Fix:** Remove or correct the invalid advanced parameter on the SAP Application Scope — the named key (`BOGUSKEY`) is not a supported RFC config parameter. Use only valid SAP .NET Connector RFC parameter names in the Advanced Parameters field (`key=value;` pairs).

**Must NOT attribute the root cause to:**
- The **BAPI / Invoke BAPI** — the scope never connected; no BAPI ran.
- A **missing host / unconfigured connection** — that would be `SAP.Middleware.Connector.RfcConfigurationException: Not any kind of host is specified`; this is specifically an *advanced-parameter* validation failure (`SapActivityException`), which the UiPath layer checks before the NCo host check.
- A **SAP outage / unreachable host** (`RfcCommunicationException`), a **logon/credentials** problem (`RfcLogonException`), a timeout, or a workflow-logic bug.

A correct answer identifies that **an unsupported advanced RFC parameter (`<key>`) caused the SAP Application Scope to reject the connection (`SapActivityException: Advanced Parameters has invalid parameter <key>...`)** and recommends removing/correcting that advanced parameter. It must read the advanced-parameter signature rather than blaming the BAPI, host reachability, logon, or the workflow logic.

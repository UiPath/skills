# SAP BAPI Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity is a SAP BAPI activity (`UiPath.SAP.BAPI.Activities.SapApplicationScope`, `...InvokeBAPI` / `InvokeSapBapi`, `...SapOpenConnection`). Do not confuse it with SAP GUI scripting activities (a different package and code path).
- **SAP system / connection** — the SAP system (host/system id, client) in evidence is the one the user is asking about. A different system/client = different authorizations and a different BAPI catalog.
- **BAPI name** — the function module in the error is the one the user invoked.
- **Workflow file** — the error originates from the workflow the user references.
- **Timestamp** — the failure occurred in the reported window (load-bearing for a transient SAP/network outage vs. a config problem).

If the data doesn't match: discard it.

## Domain-Specific Data Gathering

1. **Locate the failing phase from the exception.**
   - Connection resource strings (`Connection could not be created.`, `Cannot create sap connection, connection info params are not set`, `Missing mandatory field: ...`) or `System.TimeoutException` → the **SAP Application Scope / Open Connection** failed; the BAPI never ran.
   - `Function: <name> could not be created` / `BAPI name is null or empty` → **metadata lookup**: the BAPI name is wrong/empty or inaccessible.
   - `Unsupported BAPI. Contains nested complex types.` (`UnSupportedBapiException`) → the **BAPI choice** is incompatible with the activity.
2. **Read the message verbatim.** These are fixed resource strings — match the literal text, not a paraphrase. `Connection could not be created.` is a generic RFC open failure; the *reason* (host unreachable, bad client, logon rejected) is not in the message — it must come from the connection parameters and any inner `RfcCommunicationException` / SAP system log.
3. **For a `TimeoutException`,** determine whether it wraps an `RfcCommunicationException` (network/host reachability) versus a long-running BAPI (the SAP side is slow). Check timestamp/window for a transient outage.
4. **Connection vs. authorization.** `Connection could not be created.` can be a wrong host/port/SNC *or* a rejected logon (locked user, wrong password, no RFC authorization). `Function: <name> could not be created` can be a genuinely missing BAPI *or* the user lacking authorization to that function module. The exception alone doesn't separate these — the SAP system log / Basis team does.

## Testing Prerequisites

> Connection-configuration failures (missing params, invalid advanced parameter) are rejected before any network call; BAPI-lookup / unsupported-BAPI failures occur only after the connection opens. Diagnosis is evidence-based from the faulted job.

1. **Activity identity** — `SapApplicationScope` vs `InvokeBAPI`/`InvokeSapBapi` vs `SapOpenConnection`, with the display name.
2. **Exception type + message** — `System.Exception` (connection string) vs `SapActivityException` vs `UnSupportedBapiException` vs `TimeoutException`, verbatim.
3. **Connection parameters** — SAP host/system id, client, user, language, and any advanced RFC parameters (without exposing the password).
4. **BAPI name** — the function module the activity invoked.
5. **SAP-side context** — whether the SAP system was reachable in the window, and whether the RFC user is locked / lacks authorization (Basis/SAP admin input).
6. **Package version** — `UiPath.SAP.BAPI.Activities` version.

---
confidence: high
---

# SAP — Unsupported BAPI (nested complex types)

## Context

The connection opened and the BAPI was found, but the activity rejects it because its interface contains **nested complex types** (structures/tables nested inside other structures/tables) that the connector cannot marshal to/from workflow arguments.

What this looks like:

- `Unsupported BAPI. Contains nested complex types.` — thrown as `UiPath.SAP.BAPI.SapBapiExceptions.UnSupportedBapiException` (carries an `ErrorCode`). Raised while building the BAPI's parameter model when a structure or table parameter has a nested complex member.

What can cause it:
- **The chosen BAPI's signature is too complex for the activity** — one or more import/export/table parameters nest complex types. This is a property of that specific function module, not a transient or environmental error. It fails deterministically every run for that BAPI.

What to look for:
- The exception **type is `UnSupportedBapiException`** with the literal `Unsupported BAPI. Contains nested complex types.` — this is a capability limit of the Invoke BAPI activity, not a connection, authorization, or input problem. Re-running, re-authorizing, or fixing inputs will not help.

> **Different cause — do not apply this playbook:**
> - `Connection could not be created.` / `TimeoutException` → connection failure → use [sap-connection-failed.md](./sap-connection-failed.md).
> - `Function: <name> could not be created` / `BAPI name is null or empty` → BAPI lookup / naming → use [sap-bapi-not-found.md](./sap-bapi-not-found.md).

## Investigation

1. **Confirm the exception type** is `UnSupportedBapiException` with `Unsupported BAPI. Contains nested complex types.` — this conclusively identifies the cause; no further data is needed to attribute it.
2. **Identify the BAPI** so an alternative can be chosen.

## Resolution

- **If `Unsupported BAPI. Contains nested complex types.`:** the Invoke BAPI activity cannot handle this function module's nested-complex signature. Use a different, flatter BAPI that exposes the same data without nested complex parameters, or call the function module through another mechanism (e.g. a custom RFC/code component or a wrapper BAPI on the SAP side that flattens the structure). This is not fixable by reconfiguring the existing activity.

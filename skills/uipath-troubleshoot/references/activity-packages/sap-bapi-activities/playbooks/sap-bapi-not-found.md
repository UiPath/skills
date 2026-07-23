---
confidence: medium
---

# SAP — BAPI not found or not named

## Context

The RFC connection opened, but the connector could not resolve the BAPI / RFC function module to invoke — its metadata lookup failed because the name doesn't exist in the connected SAP system (or the user can't access it), or no BAPI name was supplied at all.

What this looks like:

- `Function: <name> could not be created` (`System.Exception`, resource `ErrorMsgRfcFunctionNotCreated`) — the connector asked the SAP system for the function module's interface and the system did not return it. The function module name is wrong, doesn't exist in this system/client, or the RFC user lacks authorization to it.
- `BAPI name is null or empty` (resource `ErrorEmptyBapi`) — the activity ran with no BAPI name configured (empty argument or an upstream variable that produced no value).

What can cause it:
- **Wrong / non-existent BAPI name** — a typo, or a function module that exists in a different SAP system/release but not the connected one.
- **Authorization** — the RFC user can connect but is not authorized to that function module, so metadata retrieval fails.
- **Empty BAPI argument** — the BAPI name wasn't set, or an upstream expression produced an empty string.

What to look for:
- `Function: <name> could not be created` names the function module — confirm it against the connected system's BAPI catalog. The message alone doesn't separate "doesn't exist" from "not authorized" — that needs the SAP system / Basis team. `BAPI name is null or empty` is purely a missing-argument case.

> **Different cause — do not apply this playbook:**
> - `Connection could not be created.` / `Cannot create sap connection ...` / `TimeoutException` → the connection never opened → use [sap-connection-failed.md](./sap-connection-failed.md).
> - `Unsupported BAPI. Contains nested complex types.` → the BAPI exists but is incompatible with the activity → use [sap-unsupported-bapi.md](./sap-unsupported-bapi.md).

## Investigation

1. **Confirm the connection opened** (no connection-string/timeout exception) and the failure is the BAPI lookup.
2. **Capture the BAPI name** the activity tried to invoke.
3. **For `Function: <name> could not be created`:** with the SAP/Basis team, confirm whether that function module exists in the connected system/client and whether the RFC user is authorized to call it.
4. **For `BAPI name is null or empty`:** trace the BAPI-name argument / upstream variable.

## Resolution

- **If `Function: <name> could not be created` and the BAPI doesn't exist in this system:** correct the BAPI name (check spelling and that it exists in the connected system/release); point the activity at the right SAP system/client if it was connecting to the wrong one.
- **If `Function: <name> could not be created` and the BAPI exists but isn't accessible:** have the SAP admin grant the RFC user authorization to that function module.
- **If `BAPI name is null or empty`:** set the BAPI name on the Invoke BAPI activity; with explicit user approval, fix the upstream expression if it came from an empty variable.

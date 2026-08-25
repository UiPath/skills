# UiPath SAP BAPI Activities - Legacy Reference

## Overview
SAP system integration via BAPI (Business API) remote function calls. Package: `UiPath.SAP.BAPI.Activities`.

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `SapApplicationScope` | Connection container (NativeActivity) | AppServer, SystemNumber, Client, StatefulConnection |
| `SapOpenConnection` | Explicit connection | (within scope) |
| `SapCloseConnection` | Cleanup | (within scope) |
| `InvokeSapBapi` | Execute BAPI function | BapiName, SelectedArgumentList, OptionalArguments, AllArguments |
| `InvokeBAPI` | Legacy variant | Similar to InvokeSapBapi |

### SapApplicationScope Arguments
- `AppServer` (string) - SAP application server hostname
- `SystemNumber` (string) - SAP system number (e.g., "00")
- `Client` (string) - SAP client ID (e.g., "800")
- `StatefulConnection` (bool) - Session mode (stateful vs stateless)

### InvokeSapBapi Arguments
- `BapiName` (string) - RFC function module name
- `BapiDescription` (string) - Display metadata
- `SelectedArgumentList` (IList\<BapiArgumentUiModel\>) - Dynamic parameters
- Return types: BapiReturn, BapiReturn1, BapiReturn2

---

## Critical Gotchas

1. **SAP .NET Connector (NCo) must be installed** on the machine - not bundled
2. **BAPI metadata discovery is slow** on first access (requires live SAP connection)
3. **Dynamic argument handling** - BapiArgumentUiModel maps types via DataTypeEnum
4. **Return structure varies by BAPI** - Bapi_Ret1 vs Bapi_Ret2 have different fields
5. **Must run within SapApplicationScope** - constraint enforced
6. **Designer wizard requires live SAP connection** at design time for BAPI selection
7. **StatefulConnection** - if true, SAP maintains session context between calls
8. **DataTable results** for table-type BAPI parameters
9. **Authorization** - SAP user must have RFC authorization for called BAPIs
10. **Transaction handling** - BAPI_TRANSACTION_COMMIT must be called explicitly for stateful changes

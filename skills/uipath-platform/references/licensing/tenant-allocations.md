# Tenant License Allocations

Allocate account-pool license units (`UNATT`, `RU`, `PLTU`, `NONPR`, etc.) to tenants, or inspect tenant reservations and consumption.

> Run `uip platform tenants licenses get --help` or `uip platform tenants licenses set --help` for full options.

## When to Use

- Provision, resize, or rebalance tenant allocations.
- Audit per-tenant `allocated` versus `consumed`.
- Increase tenant capacity for CI/CD or load testing.

## Prerequisites

1. Run `uip login status`. If unauthenticated, ask the user to run `uip login` (interactive browser flow).
2. Have org admin permissions to allocate licenses.
3. Obtain the target tenant GUID with `uip or settings list --tenant <name>` or from the Automation Cloud portal.

## Commands

| Command | Purpose |
|---|---|
| `uip platform tenants licenses get <tenant-key>` | Read allocation, availability, and consumption by product code. |
| `uip platform tenants licenses set <tenant-key> --input <path>` | Overlay product quantities onto existing tenant service licenses. |

## 1. Inspect Current Allocation

Run:

```bash
uip platform tenants licenses get <TENANT_KEY> --output json
```

The result contains one row per product in the active interval (`startDate` <= current time <= `endDate`):

```json
{"Result":"Success","Code":"TenantLicenses","Data":[{"code":"PLTU","name":"Platform Units","allocated":300,"availableForAllocation":4700,"allocatedAcrossOtherTenants":0,"totalUnitsInAccount":5000,"consumed":50,"startDate":"2023-11-14T22:13:20.000Z","endDate":"2027-09-15T18:40:00.000Z"}]}
```

- `allocated`: units reserved for this tenant.
- `availableForAllocation`: units free in the account pool.
- `allocatedAcrossOtherTenants`: units reserved for other tenants.
- `totalUnitsInAccount`: purchase total; equals `allocated + availableForAllocation + allocatedAcrossOtherTenants`.
- `consumed`: units used by running jobs; a subset of `allocated`.
- `startDate` / `endDate`: bundle window in ISO 8601.

## 2. Prepare the Input File

Create a JSON array of absolute target quantities:

```json
[{"code":"UNATT","quantity":10},{"code":"PLTU","quantity":500}]
```

Validate that:

- `code` is a non-empty string.
- `quantity` is a finite, non-negative number; zero sets the allocation to zero.
- Each `code` already exists on the tenant's current service licenses; `set` cannot introduce product codes.

## 3. Apply the Allocation

> **Diagnosing, not fixing? Stop here.** Do not run `set` while explaining unexpected behavior or reproducing the user's command. `set` mutates production by overlaying and potentially overwriting the state being diagnosed. A seemingly disconnected CLI is not permission to try it; an unauthenticated command is not guaranteed to fail if credentials resolve. Read `get`, cite the documented semantics in [Gotchas](#gotchas) and `set --help`, and let the user authorize any fix.

Run:

```bash
uip platform tenants licenses set <TENANT_KEY> --input ./delta.json --output json
```

`set` uses `mergeProducts` overlay semantics:

1. The CLI reads the tenant's current per-service allocation.
2. Each input `quantity` replaces the current value for that `code`.
3. Omitted existing codes retain their quantities.
4. Each code is routed to its owning service license (orchestrator, dataservice, etc.).
5. Repeating identical input is idempotent and safe to retry.

The result contains one row per product on each touched service license:

```json
{"Result":"Success","Code":"TenantLicensesSet","Data":[{"serviceType":"orchestrator","code":"UNATT","name":"Unattended Robot","quantity":10},{"serviceType":"orchestrator","code":"PLTU","name":"Platform Units","quantity":500}]}
```

## 4. Verify

Run:

```bash
uip platform tenants licenses get <TENANT_KEY> --output json
```

Confirm that `allocated` matches the requested quantities.

## Error Conditions

| Error | Cause | Resolution |
|---|---|---|
| `No service licenses found for tenant '<key>'` | Wrong tenant GUID or no provisioned services. | Verify the tenant key with `uip or` or the portal. |
| `Cannot route product code(s) for tenant '<key>': <code>` | Code is not on the tenant's service licenses. | Add the SKU through the UiPath portal, then run `set` again. |
| `Ambiguous routing for tenant '<key>': '<code>' (matches service types: ...)` | Code exists on multiple tenant service licenses. | Resolve the duplicate in the portal or through support, then retry. |
| `Invalid input JSON. "quantity" must be a finite, non-negative number.` | Invalid input file. | Fix the JSON; `quantity` must be ≥ 0. |
| `Error connecting to the License Resource Manager.` | Expired authentication or network issue. | Run `uip login` again. |

## Gotchas

- **Never run `set` while diagnosing.** Reproducing a user's `set` is still a mutation and overwrites evidence. See [Step 3](#3-apply-the-allocation).
- **`quantity` is absolute, not delta.** `{"code":"UNATT","quantity":5}` sets the tenant to 5; it does not add 5. Run `get` first to establish the starting value.
- **Codes are overlaid, not replaced.** Omitted existing codes retain their quantities; use `quantity: 0` to zero a code.
- **New product codes cannot be added.** Provision a missing SKU through the portal first.
- **`availableForAllocation: 0`** means the account pool is exhausted. Reduce another tenant's allocation or purchase additional units before allocating more.
- **`consumed` lags real time.** Accountant-side aggregation may take minutes to update after a job completes.
- **Bundle windows matter.** `get` omits products outside the active interval; an expired bundle will not appear even if it historically had `allocated > 0`.

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [User & Group Licenses](user-licenses-allocations.md) — per-user/group bundle assignment (separate from tenant allocation)
- [Consumables Report](consumables-report.md) — track consumption drawn from tenant pools
- [Setup Environment](../orchestrator/setup-environment.md) — `uip or licenses toggle` for Orchestrator-scoped slot assignment
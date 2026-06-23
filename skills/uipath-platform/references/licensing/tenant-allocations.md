# Tenant License Allocations

Allocate license units (`UNATT`, `RU`, `PLTU`, `NONPR`, etc.) from the account pool to specific tenants, and inspect what each tenant currently has reserved and consumed.

> For full option details, run `uip platform tenants licenses get --help` or `... set --help`.

---

## When to Use

- Provisioning a new tenant with a runtime allocation (e.g., 5 Unattended Robots)
- Rebalancing licenses across tenants (move 10 RU from dev to prod)
- Auditing per-tenant `allocated` vs `consumed` to find under- or over-provisioned tenants
- Scripting CI/CD pipeline that bumps tenant capacity before a load test

## Prerequisites

1. Authenticated — verify with `uip login status`; if not, ask the user to run `uip login` (interactive browser flow)
2. Org admin permissions to allocate licenses
3. Tenant key (GUID) of the target tenant — discover with `uip or settings list --tenant <name>` or the Automation Cloud portal

---

## Commands

| Command | What it does |
|---------|--------------|
| `uip platform tenants licenses get <tenant-key>` | Read current allocation, availability, and consumption per product code |
| `uip platform tenants licenses set <tenant-key> --input <path>` | Overlay per-product quantities onto the tenant's existing service licenses |

---

## Step 1: Inspect Current Allocation

```bash
uip platform tenants licenses get <TENANT_KEY> --output json
```

Returns one row per product currently in an active interval (current time falls between `startDate` and `endDate`):

```json
{
  "Result": "Success",
  "Code": "TenantLicenses",
  "Data": [
    {
      "code": "PLTU",
      "name": "Platform Units",
      "allocated": 300,
      "availableForAllocation": 4700,
      "allocatedAcrossOtherTenants": 0,
      "totalUnitsInAccount": 5000,
      "consumed": 50,
      "startDate": "2023-11-14T22:13:20.000Z",
      "endDate": "2027-09-15T18:40:00.000Z"
    }
  ]
}
```

Field reference:

| Field | Meaning |
|-------|---------|
| `allocated` | Units currently reserved for this tenant |
| `availableForAllocation` | Units still free in the account pool (could be moved to this or any tenant) |
| `allocatedAcrossOtherTenants` | Units reserved for other tenants |
| `totalUnitsInAccount` | Account purchase total. Equals `allocated + availableForAllocation + allocatedAcrossOtherTenants` |
| `consumed` | Units actually used by running jobs (subset of `allocated`) |
| `startDate` / `endDate` | Bundle window in ISO 8601 |

## Step 2: Prepare the Input File

Create a JSON array of product entries with absolute target quantities:

```json
[
  {"code": "UNATT", "quantity": 10},
  {"code": "PLTU", "quantity": 500}
]
```

Validation rules:
- `code` must be a non-empty string
- `quantity` must be a finite, non-negative number (zero is allowed — sets the allocation to zero)
- Each `code` must already exist on the tenant's current service licenses (cannot introduce new product codes)

## Step 3: Apply the Allocation

```bash
uip platform tenants licenses set <TENANT_KEY> --input ./delta.json --output json
```

Overlay semantics (`mergeProducts`):
1. CLI reads the tenant's current per-service allocation
2. For each input entry, the listed `quantity` replaces the current value for that `code`
3. Codes already on the tenant but **not** in the input keep their current quantity
4. The CLI auto-routes each code to the service license that owns it (orchestrator, dataservice, etc.)
5. Re-running the same input is idempotent — safe to retry

Returns one row per product per touched service license:

```json
{
  "Result": "Success",
  "Code": "TenantLicensesSet",
  "Data": [
    {"serviceType": "orchestrator", "code": "UNATT", "name": "Unattended Robot", "quantity": 10},
    {"serviceType": "orchestrator", "code": "PLTU", "name": "Platform Units", "quantity": 500}
  ]
}
```

## Step 4: Verify

Re-run `get` and confirm the new `allocated` values match the input.

```bash
uip platform tenants licenses get <TENANT_KEY> --output json
```

---

## Error Conditions

| Error | Cause | Resolution |
|-------|-------|------------|
| `No service licenses found for tenant '<key>'` | Wrong tenant GUID, or tenant has no provisioned services | Verify the tenant key against `uip or` or the portal |
| `Cannot route product code(s) for tenant '<key>': <code>` | The product code is not already present on this tenant's service licenses | The CLI cannot introduce new codes. Use the UiPath portal to add the SKU first, then re-run `set` |
| `Ambiguous routing for tenant '<key>': '<code>' (matches service types: ...)` | Same code exists on more than one of the tenant's service licenses | Resolve the duplicate allocation in the portal or via support, then retry |
| `Invalid input JSON. "quantity" must be a finite, non-negative number.` | Bad input file | Fix the JSON; `quantity` must be ≥ 0 |
| `Error connecting to the License Resource Manager.` | Auth expired or network issue | Re-run `uip login` |

---

## Gotchas

- **`quantity` is absolute, not delta.** `{"code":"UNATT","quantity":5}` sets the tenant to 5 — it does not add 5 to the current value. Read `get` first to know the starting point.
- **Codes are overlay, not replace.** A product already on the tenant but missing from the input keeps its current quantity. To zero out a code, include it explicitly with `quantity: 0`.
- **Cannot add new product codes.** If a tenant doesn't have `AIU` on its service licenses, you cannot introduce it via `set`. Provision the SKU through the portal first.
- **`availableForAllocation: 0`** means the account pool is exhausted. To allocate more to this tenant, first reduce another tenant's allocation or purchase additional units.
- **`consumed` lags real-time.** It reflects accountant-side aggregation; expect minutes of delay after a job completes.
- **Bundle window matters.** `get` filters out products outside the currently active interval — an expired bundle won't appear even if `allocated > 0` historically.

---

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [User & Group Licenses](user-licenses-allocations.md) — per-user/group bundle assignment (separate from tenant allocation)
- [Consumables Report](consumables-report.md) — track consumption drawn from tenant pools
- [Setup Environment](../orchestrator/setup-environment.md) — `uip or licenses toggle` for Orchestrator-scoped slot assignment

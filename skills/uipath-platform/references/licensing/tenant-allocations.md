# Tenant License Allocations

Allocate account-pool license units (`UNATT`, `RU`, `PLTU`, `NONPR`, etc.) to tenants and inspect reserved or consumed units. For full options, run `uip platform tenants licenses get --help` or `... set --help`.

## When to Use

Use this skill to provision runtime capacity, rebalance licenses, audit `allocated` versus `consumed`, or raise capacity for a CI/CD load test.

## Prerequisites

1. Run `uip login status`; if unauthenticated, ask the user to run `uip login` (interactive browser flow).
2. Require org admin permissions.
3. Obtain the target tenant key (GUID) with `uip or settings list --tenant <name>` or from the Automation Cloud portal.

## Commands

- `uip platform tenants licenses get <tenant-key>` — read allocation, availability, and consumption by product code.
- `uip platform tenants licenses set <tenant-key> --input <path>` — overlay product quantities on existing tenant service licenses.

## Step 1: Inspect Current Allocation

Run:

```bash
uip platform tenants licenses get <TENANT_KEY> --output json
```

The response has one row per product in an active interval (current time is between `startDate` and `endDate`):

```json
{"Result":"Success","Code":"TenantLicenses","Data":[{"code":"PLTU","name":"Platform Units","allocated":300,"availableForAllocation":4700,"allocatedAcrossOtherTenants":0,"totalUnitsInAccount":5000,"consumed":50,"startDate":"2023-11-14T22:13:20.000Z","endDate":"2027-09-15T18:40:00.000Z"}]}
```

- `allocated`: units reserved for this tenant.
- `availableForAllocation`: units free in the account pool.
- `allocatedAcrossOtherTenants`: units reserved for other tenants.
- `totalUnitsInAccount`: purchase total; equals `allocated + availableForAllocation + allocatedAcrossOtherTenants`.
- `consumed`: units used by running jobs, a subset of `allocated`.
- `startDate` / `endDate`: bundle window in ISO 8601.

## Step 2: Prepare the Input File

Create a JSON array of absolute target quantities:

```json
[{"code":"UNATT","quantity":10},{"code":"PLTU","quantity":500}]
```

Validate that `code` is a non-empty string, `quantity` is a finite, non-negative number (zero is allowed and sets allocation to zero), and every `code` already exists on the tenant's current service licenses. New product codes cannot be introduced.

## Step 3: Apply the Allocation

**When diagnosing rather than fixing, stop here and do not run `set`, even to reproduce the user's command.** `set` mutates production and overwrites prior-state evidence; an apparently disconnected CLI is not permission to try it, and an unauthenticated command is not guaranteed to fail. Read `get`, cite [Gotchas](#gotchas) and `set --help`, and let the user authorize any fix.

Run:

```bash
uip platform tenants licenses set <TENANT_KEY> --input ./delta.json --output json
```

`mergeProducts` semantics:

1. The CLI reads current per-service allocations.
2. Each input `quantity` replaces the current value for its `code`.
3. Omitted existing codes retain their quantities.
4. The CLI auto-routes each code to its owning service license (orchestrator, dataservice, etc.).
5. Re-running identical input is idempotent and safe to retry.

The response has one row per product per touched service license:

```json
{"Result":"Success","Code":"TenantLicensesSet","Data":[{"serviceType":"orchestrator","code":"UNATT","name":"Unattended Robot","quantity":10},{"serviceType":"orchestrator","code":"PLTU","name":"Platform Units","quantity":500}]}
```

## Step 4: Verify

Re-run `get` and confirm that `allocated` matches the input:

```bash
uip platform tenants licenses get <TENANT_KEY> --output json
```

---

## Error Conditions

| Error | Cause | Resolution |
|-------|-------|------------|
| `No service licenses found for tenant '<key>'` | Wrong tenant GUID, or tenant has no provisioned services | Verify the tenant key against `uip or` or the portal |
| `Cannot route product code(s) for tenant '<key>': <code>` | Product code is absent from the tenant's service licenses | The CLI cannot introduce codes; add the SKU in the UiPath portal, then re-run `set` |
| `Ambiguous routing for tenant '<key>': '<code>' (matches service types: ...)` | Code exists on more than one tenant service license | Resolve the duplicate allocation in the portal or via support, then retry |
| `Invalid input JSON. "quantity" must be a finite, non-negative number.` | Invalid input file | Fix the JSON; `quantity` must be ≥ 0 |
| `Error connecting to the License Resource Manager.` | Auth expired or network issue | Re-run `uip login` |

---

## Gotchas

- **Never run `set` while diagnosing.** Reproducing the user's command mutates state; see [Step 3](#step-3-apply-the-allocation).
- **`quantity` is absolute, not delta.** `{"code":"UNATT","quantity":5}` sets the tenant to 5; run `get` first to know the starting point.
- **Codes are overlaid, not replaced.** Omitted existing codes retain their quantities; include `quantity: 0` to zero one.
- **New product codes cannot be added.** If `AIU` is absent from the tenant's service licenses, provision the SKU through the portal first.
- **`availableForAllocation: 0`** means the account pool is exhausted; reduce another tenant's allocation or purchase additional units.
- **`consumed` lags real time.** It reflects accountant-side aggregation and may take minutes after a job completes.
- **Bundle window matters.** `get` omits products outside the active interval; an expired bundle won't appear even if historically `allocated > 0`.

---

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [User & Group Licenses](user-licenses-allocations.md) — per-user/group bundle assignment, separate from tenant allocation
- [Consumables Report](consumables-report.md) — consumption drawn from tenant pools
- [Setup Environment](../orchestrator/setup-environment.md) — `uip or licenses toggle` for Orchestrator-scoped slot assignment
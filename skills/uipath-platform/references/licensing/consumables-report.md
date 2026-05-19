# Consumables Report

Report consumption of consumable license units (`AIU`, `AGU`, `RU`, `PLTU`, `HEAL`, `SPR`, `LU`, etc.) across the organization. Three report shapes: account-wide summary, daily breakdown by service, folder breakdown.

> For full option details, run `uip platform licenses consumables get --help`.

---

## When to Use

- Monthly chargeback / cost-allocation reporting per tenant
- Capacity planning: confirm allocated vs consumed before bundle renewal
- Drill into which folders are driving consumption of a specific unit (`folders` mode)
- Daily trend analysis for a specific tenant × unit (`daily` mode)
- Compare consumption across tenant pool vs overflow into org pool

## Prerequisites

1. Authenticated: `uip login`
2. Org admin permissions to read account product allocations
3. For `daily` / `folders` modes: know the target tenant name and consumable unit code

---

## Modes

| Mode | Scope | Required Flags | Output |
|------|-------|----------------|--------|
| `summary` (default) | All active consumables × all tenants (or one tenant if `--tenant`) | None | One row per consumable × tenant; allocation + pool consumption columns |
| `daily` | One tenant × one unit, day-by-day | `--tenant`, `--unit`, `--start-date`, `--end-date` | One row per (date, service) |
| `folders` | One tenant × one unit, broken down by folder | `--tenant`, `--unit`, `--start-date`, `--end-date` | One row per folder |

---

## Mode 1: Summary

Default mode. Iterates every active consumable in the account.

```bash
# All consumables, all tenants, each consumable's bundle window
uip platform licenses consumables get --output json

# Scope to one tenant
uip platform licenses consumables get --tenant "<TENANT_NAME>" --output json

# Override every consumable's window with a custom date range
uip platform licenses consumables get \
  --start-date 2026-04-01 --end-date 2026-04-30 --output json
```

```json
{
  "Result": "Success",
  "Code": "LicensesConsumablesSummary",
  "Data": [
    {
      "code": "AIU",
      "name": "AI Units",
      "totalUnitsInAccount": 5000,
      "allocated": 1200,
      "consumedFromOrgWithoutTenant": 30,
      "startDate": "2023-11-14T22:13:20.000Z",
      "endDate": "2027-09-15T18:40:00.000Z",
      "tenantId": "296b7134-6691-43db-b48a-2d95ed3ab031",
      "tenantName": "default",
      "consumedFromTenantPool": 800,
      "consumedFromOrgPool": 150
    }
  ]
}
```

Field reference:

| Field | Meaning |
|-------|---------|
| `code` / `name` | Product code and friendly name |
| `totalUnitsInAccount` | Account purchase total for this consumable |
| `allocated` | Account-level allocation |
| `consumedFromOrgWithoutTenant` | Consumption not attributable to any tenant (zero when `--tenant` is set) |
| `startDate` / `endDate` | Window in effect — bundle window by default, override range if `--start-date`/`--end-date` provided |
| `tenantId` / `tenantName` | Per-tenant breakdown |
| `consumedFromTenantPool` | Drawn from the tenant's reserved allocation |
| `consumedFromOrgPool` | Drawn from the remaining account pool (overflow) |

Row-shape rules:
- **No `--tenant`, consumption across multiple tenants**: one row per (consumable, tenant)
- **No `--tenant`, no tenant consumption**: single row per consumable with `tenantId: null`, `tenantName: ""`, and pool columns zeroed; `consumedFromOrgWithoutTenant` may be non-zero
- **With `--tenant`**: one row per consumable for that tenant. Consumables with zero tenant activity still appear with zeroed pool columns

## Mode 2: Daily Breakdown

```bash
uip platform licenses consumables get \
  --mode daily \
  --tenant "<TENANT_NAME>" \
  --unit AIU \
  --start-date 2026-04-01 \
  --end-date 2026-04-30 \
  --output json
```

```json
{
  "Result": "Success",
  "Code": "LicensesConsumablesDaily",
  "Data": [
    {
      "code": "AIU",
      "name": "AI Units",
      "tenantId": "296b7134-6691-43db-b48a-2d95ed3ab031",
      "tenantName": "default",
      "date": "2026-04-15",
      "service": "orchestrator",
      "consumedAmount": 24
    }
  ]
}
```

`date` is `YYYY-MM-DD`. One row per (date, service) inside the range. `service` is the service that emitted the consumption (e.g., `orchestrator`, `aicenter`, `dataservice`).

## Mode 3: Folder Breakdown

```bash
uip platform licenses consumables get \
  --mode folders \
  --tenant "<TENANT_NAME>" \
  --unit AIU \
  --start-date 2026-04-01 \
  --end-date 2026-04-30 \
  --output json
```

```json
{
  "Result": "Success",
  "Code": "LicensesConsumablesFolders",
  "Data": [
    {
      "code": "AIU",
      "name": "AI Units",
      "tenantId": "296b7134-6691-43db-b48a-2d95ed3ab031",
      "tenantName": "default",
      "folderKey": "11111111-1111-1111-1111-111111111111",
      "folderName": "Shared",
      "parentFolderKey": null,
      "consumedBySelf": 42,
      "processCountSelf": 3
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `folderKey` / `folderName` | Folder GUID and display name |
| `parentFolderKey` | Parent GUID for nested folders; `null` at the root |
| `consumedBySelf` | Consumption attributed to this folder only — does not include descendants |
| `processCountSelf` | Distinct processes in this folder that contributed |

Aggregate descendants client-side if needed — the API returns per-folder rows only.

---

## Flag Reference

| Flag | Required In | Default | Notes |
|------|-------------|---------|-------|
| `--mode <summary\|daily\|folders>` | All modes | `summary` | Determines output shape |
| `--tenant <name>` | `daily`, `folders` | All tenants | Matched by exact tenant name |
| `--unit <code>` | `daily`, `folders` | All consumables | Case-insensitive product code (`AIU`, `aiu`, `Aiu` all match) |
| `--start-date <iso>` | `daily`, `folders` | Bundle window | ISO 8601 (e.g., `2026-04-01` or `2026-04-01T00:00:00Z`) |
| `--end-date <iso>` | `daily`, `folders` | Bundle window | ISO 8601, must be strictly after `--start-date` |

Date range rules:
- `--start-date` and `--end-date` must be passed together; passing only one is rejected
- Both must parse as valid ISO 8601
- `startDate >= endDate` is rejected
- In `summary` mode, the range overrides each consumable's own bundle window
- In `daily` / `folders` modes, the range is required

---

## Error Conditions

| Error | Cause | Resolution |
|-------|-------|------------|
| `Invalid --mode '<value>'.` | Mode is not summary/daily/folders | Use one of the three allowed values |
| `--mode daily requires: --tenant, --unit, --start-date, --end-date.` | Missing required flag(s) for the mode | Pass all four |
| `--start-date and --end-date must be provided together.` | Only one of the pair was supplied | Pass both, or omit both |
| `Invalid --start-date: '<value>'.` | Date doesn't parse as ISO 8601 | Use `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` |
| `--start-date must be strictly before --end-date.` | Range is empty or inverted | Provide a non-empty forward range |
| `Tenant '<name>' not found in the current organization.` | No tenant with that exact name | Check spelling against `uip login tenant list`; available tenants are listed in the error |
| `Unit '<code>' is not an active consumable in this organization.` | Code is not a consumable, or its bundle window is not currently active | Error lists available codes; pick one of those |

---

## Gotchas

- **`summary` reports every active consumable.** It is potentially heavy on large accounts — scope with `--tenant` or `--unit` when iterating.
- **Bundle window vs override.** With no `--start-date`/`--end-date`, every consumable in the summary uses its own window — rows can have different date ranges. The override applies the same range to all rows.
- **`consumedFromOrgWithoutTenant` is zero under `--tenant`.** The CLI suppresses cross-tenant pool numbers when scoped to a single tenant; only `consumedFromTenantPool` and `consumedFromOrgPool` are populated.
- **`consumedAmount` and `consumedBySelf` are point-in-time totals over the requested range** — not running totals. Re-running the same query later returns the same value once the window has closed.
- **`--unit` is case-insensitive**, but other code references (`tenant licenses set`) are exact-case — don't carry the assumption.
- **No pagination.** `daily` and `folders` modes return all rows in one response. For very large windows or folder counts, consider narrower ranges.
- **`folders` mode is non-recursive.** `consumedBySelf` excludes child folders. Reconstruct the tree yourself if you need rolled-up totals.
- **`PLTU` is dual-purpose.** It appears in both runtime allocation (`tenants licenses get`) and consumables reporting. Same code, different reporting axes.

---

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [Tenant Allocations](tenant-allocations.md) — set the allocations these reports consume from
- [User & Group Licenses](user-licenses-allocations.md) — user-bundle allocation (separate license type)
- [Full CLI command reference](../uip-commands.md)

# Consumables Report

Report organization-wide consumption of consumable license units (`AIU`, `AGU`, `RU`, `PLTU`, `HEAL`, `SPR`, `LU`, etc.) as account summary, daily service, or folder breakdown.

> For full option details, run `uip platform licenses consumables get --help`.

## Command Shape

Run the single report verb:

```bash
uip platform licenses consumables get [--mode <summary|daily|folders>] [flags] --output json
```

1. `get` is mandatory; `uip platform licenses consumables` alone prints group help.
2. `summary`, `daily`, and `folders` are `--mode` values, never subcommands or positionals.
3. `summary` is the default: omit `--mode` or pass `--mode summary`.

| Wrong | Right |
|-------|-------|
| `uip platform licenses consumables --output json` (missing `get`) | `uip platform licenses consumables get --output json` |
| `uip platform licenses summary` (verb does not exist) | `uip platform licenses consumables get --output json` |
| `uip platform licenses consumables get summary` (mode as positional) | `uip platform licenses consumables get --mode summary --output json` |

## When to Use

Use for monthly tenant chargeback/cost allocation, renewal capacity planning, folder investigation (`folders`), tenant × unit daily trends (`daily`), or tenant-pool versus organization-pool overflow comparisons.

## Prerequisites

1. Verify authentication with `uip login status`; if unauthenticated, ask the user to run `uip login` (interactive browser flow).
2. Have org-admin permission to read account product allocations.
3. For `daily` or `folders`, know the exact tenant name and consumable unit code.

## Modes

| Mode | Scope and required flags | Output |
|---|---|---|
| `summary` (default) | All active consumables × all tenants, or one tenant with `--tenant`; no required flags | One row per consumable × tenant; allocation and pool-consumption columns |
| `daily` | One tenant × one unit, day by day; requires `--tenant`, `--unit`, `--start-date`, `--end-date` | One row per (date, service) |
| `folders` | One tenant × one unit, by folder; requires `--tenant`, `--unit`, `--start-date`, `--end-date` | One row per folder |

## Mode 1: Summary

Run:

```bash
uip platform licenses consumables get --output json
uip platform licenses consumables get --tenant "<TENANT_NAME>" --output json
uip platform licenses consumables get \
  --start-date 2026-04-01 --end-date 2026-04-30 --output json
```

```json
{"Result":"Success","Code":"LicensesConsumablesSummary","Data":[{"code":"AIU","name":"AI Units","totalUnitsInAccount":5000,"allocated":1200,"consumedFromOrgWithoutTenant":30,"startDate":"2023-11-14T22:13:20.000Z","endDate":"2027-09-15T18:40:00.000Z","tenantId":"296b7134-6691-43db-b48a-2d95ed3ab031","tenantName":"default","consumedFromTenantPool":800,"consumedFromOrgPool":150}]}
```

- `code`/`name`: product code/friendly name; `totalUnitsInAccount`: account purchase total; `allocated`: account-level allocation.
- `consumedFromOrgWithoutTenant`: unattributed consumption; zero with `--tenant`.
- `startDate`/`endDate`: bundle window, or the `--start-date`/`--end-date` override.
- `tenantId`/`tenantName`: tenant breakdown.
- `consumedFromTenantPool`: tenant reserved allocation; `consumedFromOrgPool`: remaining account pool (overflow).

Rows are: (1) one per (consumable, tenant) without `--tenant` when tenants consumed; (2) one per consumable without tenant consumption, with `tenantId: null`, `tenantName: ""`, and zeroed pool columns (`consumedFromOrgWithoutTenant` may be non-zero); or (3) one per consumable for the selected tenant, including zero-activity consumables with zeroed pool columns.

## Mode 2: Daily Breakdown

Run:

```bash
uip platform licenses consumables get \
  --mode daily --tenant "<TENANT_NAME>" --unit AIU \
  --start-date 2026-04-01 --end-date 2026-04-30 --output json
```

```json
{"Result":"Success","Code":"LicensesConsumablesDaily","Data":[{"code":"AIU","name":"AI Units","tenantId":"296b7134-6691-43db-b48a-2d95ed3ab031","tenantName":"default","date":"2026-04-15","service":"orchestrator","consumedAmount":24}]}
```

`date` is `YYYY-MM-DD`; rows are one per (date, service) in the range. `service` identifies the emitting service (for example, `orchestrator`, `aicenter`, or `dataservice`).

## Mode 3: Folder Breakdown

Run:

```bash
uip platform licenses consumables get \
  --mode folders --tenant "<TENANT_NAME>" --unit AIU \
  --start-date 2026-04-01 --end-date 2026-04-30 --output json
```

```json
{"Result":"Success","Code":"LicensesConsumablesFolders","Data":[{"code":"AIU","name":"AI Units","tenantId":"296b7134-6691-43db-b48a-2d95ed3ab031","tenantName":"default","folderKey":"11111111-1111-1111-1111-111111111111","folderName":"Shared","parentFolderKey":null,"consumedBySelf":42,"processCountSelf":3}]}
```

`folderKey`/`folderName` are the folder GUID/display name; `parentFolderKey` is the parent GUID or `null` at root; `consumedBySelf` excludes descendants; `processCountSelf` counts distinct contributing processes. The API returns per-folder rows only; aggregate descendants client-side when needed.

## Flag Reference

| Flag | Required in | Default | Notes |
|---|---|---|---|
| `--mode <summary\|daily\|folders>` | All modes | `summary` | Selects output shape |
| `--tenant <name>` | `daily`, `folders` | All tenants | Exact tenant-name match |
| `--unit <code>` | `daily`, `folders` | All consumables | Case-insensitive product code (`AIU`, `aiu`, `Aiu` all match) |
| `--start-date <iso>` | `daily`, `folders` | Bundle window | ISO 8601, such as `2026-04-01` or `2026-04-01T00:00:00Z` |
| `--end-date <iso>` | `daily`, `folders` | Bundle window | ISO 8601; strictly after `--start-date` |

`--start-date` and `--end-date` must be supplied together; either alone is rejected. Both must be valid ISO 8601, and `startDate >= endDate` is rejected. In `summary`, the range overrides every consumable's bundle window; in `daily` and `folders`, it is required.

## Error Conditions

| Error | Cause | Resolution |
|---|---|---|
| `Invalid --mode '<value>'.` | Value is not `summary`, `daily`, or `folders` | Use an allowed value |
| `--mode daily requires: --tenant, --unit, --start-date, --end-date.` | A required daily flag is missing | Pass all four |
| `--start-date and --end-date must be provided together.` | Only one date was supplied | Pass both or omit both |
| `Invalid --start-date: '<value>'.` | Date is not ISO 8601 | Use `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` |
| `--start-date must be strictly before --end-date.` | Range is empty or inverted | Provide a non-empty forward range |
| `Tenant '<name>' not found in the current organization.` | No exact tenant-name match | Check spelling with `uip login tenant list`; the error lists available tenants |
| `Unit '<code>' is not an active consumable in this organization.` | Code is not consumable or its bundle window is inactive | Select an available code listed in the error |

## Gotchas

- `summary` reports every active consumable and can be heavy on large accounts; scope with `--tenant` or `--unit` when iterating.
- Without dates, each summary row uses its own bundle window, so ranges can differ; an override applies one range to all rows.
- With `--tenant`, `consumedFromOrgWithoutTenant` is zero; only `consumedFromTenantPool` and `consumedFromOrgPool` are populated.
- `consumedAmount` and `consumedBySelf` are point-in-time totals for the requested range, not running totals; after the window closes, repeating the query returns the same value.
- `--unit` is case-insensitive, unlike other code references such as `tenant licenses set`, which are exact-case.
- There is no pagination: `daily` and `folders` return all rows in one response. Use narrower ranges for very large windows or folder counts.
- `folders` is non-recursive; `consumedBySelf` excludes child folders. Reconstruct the tree for rolled-up totals.
- `PLTU` is dual-purpose: it appears in runtime allocation (`tenants licenses get`) and consumables reporting, which use different reporting axes.

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [Tenant Allocations](tenant-allocations.md) — set the allocations these reports consume from
- [User & Group Licenses](user-licenses-allocations.md) — user-bundle allocation (separate license type)
- [Full CLI command reference](../uip-commands.md)
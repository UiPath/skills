# Licensing (`uip platform`)

Manage UiPath organization licensing — tenant allocations, user/group bundle assignments, and consumables reporting.

> For full option details on any command, use `--help` (e.g., `uip platform tenants licenses get --help`).

---

## Common Flags

All `uip platform` licensing commands share a set of cross-cutting options:

| Flag | Scope | Purpose |
|------|-------|---------|
| `--organization <account-id>` | All commands | Override org account GUID. Defaults to org from current login. |
| `--output json` | All commands | Emit structured JSON. Always use when parsing programmatically. |
| `--input <path>` | `set` commands | Path to JSON file with the desired allocation. Body shape differs per command — see each workflow doc. |
| `--limit <n>` | `groups rules` list commands | Max results to return (default 50). |
| `--offset <n>` | `groups rules` list commands | Results to skip (default 0). |
| `--sort-by <field>` | `groups rules` list commands | Sort field (e.g. `name`). |
| `--sort-order <Asc\|Desc>` | `groups rules` list commands | Sort direction. Exact strings `Asc` or `Desc` (case-sensitive). |

**Response envelope.** All commands emit `{Result, Code, Data, ...}`. `Code` identifies the payload (`TenantLicenses`, `UserLicensesSet`, `GroupRules`, `LicensesConsumablesSummary`, etc.). Paginated commands add a `Pagination` block — increment `--offset` by `--limit` until `Returned < Limit`.

---

## Workflow References

| Workflow | File | Covers |
|----------|------|--------|
| Tenant Allocations | [tenant-allocations.md](tenant-allocations.md) | `tenants licenses get/set` — allocate license units to tenant pools |
| User & Group Licenses | [user-licenses-allocations.md](user-licenses-allocations.md) | `users licenses get/set/available`, `groups rules get/details/set` — assign bundles directly or via group rules |
| Consumables Report | [consumables-report.md](consumables-report.md) | `licenses consumables get --mode {summary,daily,folders}` — consumption reporting |

---

## Key Concepts

### License Hierarchy

```
Account (organization)
  +-- Total units in account (purchased pool)
        +-- Tenant allocations         Reserved per tenant from account pool
        |     +-- Tenant pool consumption    Jobs consume from tenant reservation
        |     +-- Org pool consumption       Jobs overflow to remaining account pool
        +-- User bundles               Per-seat licenses (RPA Developer, Attended, etc.)
              +-- Direct assignment    Allocated to a specific user
              +-- Group rule lease     Inherited from a group rule with optional quota
```

Tenant allocations and user bundles are **separate license types**. A tenant runs unattended jobs against its runtime allocation (`UNATT`, `RU`, `PLTU`); a developer uses a user-bundle license (`RPADEVPRONU`) to log into Studio.

### Product Codes

Product codes are the SKU identifier used everywhere in the CLI. The `friendlyName()` helper maps them to readable names:

| Code | Friendly Name | Type |
|------|---------------|------|
| `RU` | Robot Units | Runtime |
| `AIU` | AI Units | Consumable |
| `AGU` | Agent Units | Consumable |
| `PLTU` | Platform Units | Runtime/consumable |
| `TEU` | Test Execution Units | Runtime |
| `UNATT` | Unattended Robot | Runtime |
| `UNATT-HOSTING` | Unattended Hosting Robot | Runtime |
| `NONPR` | NonProduction Robot | Runtime |
| `TAUNATT` | Test Automation Unattended Robot | Runtime |
| `APPTESTR` | App Test Robot | Runtime |
| `HEAL` / `HEALTEST` | Heals / Test Heals | Consumable |
| `SPR` | ScreenPlay Runs | Consumable |
| `FCCU` | Financial Crimes Units | Consumable |
| `MRSU` | Medical Record Summarization Units | Consumable |
| `LU` | Lending Units | Consumable |
| `DSU` | Data Service Units | Consumable |
| `PERFTEST` / `PERFTEST-RUNTIME` | Performance Testing | Runtime |

User-bundle codes (e.g., `RPADEVPRONU`, `ATTUNU`, `TSTNU`) are not in the `friendlyName` table — they pass through unchanged.

Unknown codes are returned verbatim; this is not an error.

### Behavior Details

Each concept is covered authoritatively in the linked workflow guide:

- **Lease source: direct vs group** — `users licenses get` tags each row with `source`. See [user-licenses-allocations.md](user-licenses-allocations.md).
- **Quotas in group rules** — `groups rules set` accepts optional `quota` per entry. See [user-licenses-allocations.md](user-licenses-allocations.md).
- **Bundle window vs custom date range** — each consumable has its own window; `--start-date`/`--end-date` overrides. See [consumables-report.md](consumables-report.md).
- **Idempotent tenant allocation** — `tenants licenses set` is an overlay, not a delta. See [tenant-allocations.md](tenant-allocations.md).

---

## REST API Fallback

When the CLI does not cover an operation, use the License Resource Manager / License Accountant APIs directly with a stored token from `~/.uipath/.auth`. See [orchestrator.md - REST API](../orchestrator/orchestrator.md) for the auth pattern.

---

## Related

- **Orchestrator licenses** — `uip or licenses` covers Orchestrator-scoped license toggles (license slots assigned to user/robot pairs in folders). See [Setup Environment](../orchestrator/setup-environment.md).
- **Tenant settings** — `uip or settings` covers tenant operational settings (timezone, alerts, trigger behavior), not licensing. See [Tenant Admin](../orchestrator/tenant-admin.md).
- **Full CLI command reference** — [uip-commands.md](../uip-commands.md)

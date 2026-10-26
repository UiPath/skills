# Licensing (`uip platform`)

Manage UiPath organization licensing: tenant allocations, user/group bundle assignments, and consumables reporting. Run `--help` for full option details, such as `uip platform tenants licenses get --help`.

## Common Flags

| Flag | Scope | Purpose |
|------|-------|---------|
| `--organization <account-id>` | All commands | Override the organization account GUID; defaults to the current login's organization. |
| `--output json` | All commands | Emit structured JSON; always use for programmatic parsing. |
| `--input <path>` | `set` commands | JSON file containing the desired allocation; its body shape varies by command. |
| `--limit <n>` | `groups rules` list commands | Maximum results; default 50. |
| `--offset <n>` | `groups rules` list commands | Results to skip; default 0. |
| `--sort-by <field>` | `groups rules` list commands | Sort field, such as `name`. |
| `--sort-order <Asc\|Desc>` | `groups rules` list commands | Exact, case-sensitive values: `Asc` or `Desc`. |

Every command emits `{Result, Code, Data, ...}`; `Code` identifies the payload (`TenantLicenses`, `UserLicensesSet`, `GroupRules`, `LicensesConsumablesSummary`, etc.). Paginated commands add `Pagination`; increment `--offset` by `--limit` until `Returned < Limit`.

Save a response by redirecting stdout only: `uip platform ... --output json > available.json`. Never send `2>&1` into the artifact: `groups rules details` writes its rule summary to stderr, so merged streams make the file unparsable. Capture stderr separately with `2> details.err`. Never hand-assemble the artifact; it must be one raw, independently parseable envelope.

## Workflow References

| Workflow | File | Covers |
|----------|------|--------|
| Tenant Allocations | [tenant-allocations.md](tenant-allocations.md) | `tenants licenses get/set` — allocate license units to tenant pools |
| User & Group Licenses | [user-licenses-allocations.md](user-licenses-allocations.md) | `users licenses get/set/available`, `groups rules get/details/set` — direct or group-rule bundle assignment |
| Consumables Report | [consumables-report.md](consumables-report.md) | `licenses consumables get --mode {summary,daily,folders}` — consumption reporting; `get` is mandatory and summary/daily/folders are `--mode` values, not subcommands (there is no `licenses summary` verb) |
| Diagnose | [diagnose/CAPABILITY.md](diagnose/CAPABILITY.md) | Symptom-first triage for entitlement gaps, ineffective allocations, and incorrect reports; layer-first ladder plus failure-mode lookup |

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

Tenant allocations and user bundles are separate license types. Tenants run unattended jobs against runtime allocation (`UNATT`, `RU`, `PLTU`); developers use user-bundle licenses such as `RPADEVPRONU` to log into Studio.

### Product Codes

Product codes are CLI SKU identifiers. The `friendlyName()` helper maps them to readable names:

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

User-bundle codes, including `RPADEVPRONU`, `ATTUNU`, and `TSTNU`, are not in the `friendlyName` table and pass through unchanged. Unknown codes are returned verbatim, not as errors.

### Behavior Details

See the linked workflow guides for authoritative details:

- **Lease source: direct vs group:** `users licenses get` tags each row with `source`; see [user-licenses-allocations.md](user-licenses-allocations.md).
- **Quotas in group rules:** `groups rules set` accepts optional `quota` per entry; see [user-licenses-allocations.md](user-licenses-allocations.md).
- **Bundle window vs custom date range:** each consumable has its own window; `--start-date`/`--end-date` overrides it; see [consumables-report.md](consumables-report.md).
- **Idempotent tenant allocation:** `tenants licenses set` is an overlay, not a delta; see [tenant-allocations.md](tenant-allocations.md).

## REST API Fallback

When the CLI does not cover an operation, use the License Resource Manager / License Accountant APIs directly with a stored token from `~/.uipath/.auth`. See [orchestrator.md - REST API](../orchestrator/orchestrator.md) for the auth pattern.

## Related

- **Orchestrator licenses** — `uip or licenses` covers Orchestrator-scoped license toggles (license slots assigned to user/robot pairs in folders). See [Setup Environment](../orchestrator/setup-environment.md).
- **Tenant settings** — `uip or settings` covers tenant operational settings (timezone, alerts, trigger behavior), not licensing. See [Tenant Admin](../orchestrator/tenant-admin.md).
- **Full CLI command reference** — [uip-commands.md](../uip-commands.md)
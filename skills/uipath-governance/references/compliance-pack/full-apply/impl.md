# Full Apply — Configure All Recommended Settings

Applies the entire compliance standard in one command. Backend creates and deploys all recommended settings.

**Note:** This configures settings recommended by ISO 42001. Your organization's auditor determines compliance status — UiPath does not certify compliance.

## Bounded execution — run once, then stop

This flow is fixed-length: ~5 commands. Run each command **exactly once** and reuse its saved output. Never re-run a discovery command to "double-check", and never loop per clause or per product. The sections below (Pre-condition → Confirmation → Apply → Verify → Report) are these steps in order — do not repeat any of them.

1. `catalog get <packId>` → `catalog.json` (once). Source for all name/impact lookups.
2. `state coverage tenant $ID <packId>` → `coverage.json` (once). The single posture snapshot — parse it one time; do not re-run coverage to rebuild a file you already have.
3. Build `posture_plan.txt` from `catalog.json` + `coverage.json` in memory — no new commands.
4. **Guardrail — nothing to apply:** if `Summary.NewCount == 0`, write the summary files with `applyPerformed: false` and STOP. Do NOT call `state enable`.
5. **Apply once:** `state enable tenant $ID <packId>`. One backend call configures ALL recommended settings. Do NOT loop per product/clause and do NOT run `synthesize-formdata` — that helper is partial-apply only and has no role in full apply.
6. **Verify once:** `state get tenant $ID <packId>` — the single post-apply check.
7. Write `report.json` and finish. After this first verify, STOP: no extra coverage, no re-synthesis, no further diagnostics.

**Stop conditions** — exit immediately when any holds:

- `Summary.NewCount == 0` (already fully applied).
- One `state enable` + one `state get` already completed.
- You have already parsed the current coverage snapshot — reuse it, never re-fetch.

Automated / non-interactive run (prompt says e.g. "do not prompt for confirmation"): skip the y/n Confirmation gate and run the ordered steps directly — do not stall waiting for input.

## Pre-condition

Coverage (posture analysis) has been run and presented. At least one policy has `status: "new"`.

## Confirmation

Build this table from `catalog.clauses[].editorialPolicies[].controls[]` filtered to products where `coverage.deploymentPolicies[].status == "new"`. Group settings by impact. For settings needing user-supplied values (flagged by `synthesize-formdata` notEmpty warnings), list them with a plain-English prompt.

```
Configure ISO 42001 settings on <tenantName>?

┌──────────┬─────────────────────────────────────────────────────┐
│ Impact   │ Settings                                            │
├──────────┼─────────────────────────────────────────────────────┤
│ High     │ <comma-separated displayNames of High settings,     │
│ (<N>)    │ truncated to first 3 + "N more">                    │
├──────────┼─────────────────────────────────────────────────────┤
│ Medium   │ <comma-separated displayNames, first 3 + "N more">  │
│ (<N>)    │                                                     │
├──────────┼─────────────────────────────────────────────────────┤
│ Low (<N>)│ <comma-separated displayNames>                      │
└──────────┴─────────────────────────────────────────────────────┘

⚠ <N> settings need values from you:
  • <controlDisplayName>  — <plain-English prompt for the value>
  • ...
(omit the ⚠ section if no settings need user-supplied values)

Proceed? (y/n)
```

Require `y`. Halt on anything else.

## Apply

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state enable tenant $TENANT_ID <packId> --output json
```

`state enable` is idempotent — safe to call even if partially applied.

## Verify

```bash
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Parse `Data.active` (must be `true`) and `Data.policies[]` (policy UUIDs created).

## Report

```
ISO 42001 settings configured on <tenantName> ✓

SUMMARY
┌───────────────────────────────────┬───────────┐
│ Settings before                   │ <N> / <T> │
│ Settings after                    │ <T> / <T> │
│ High impact settings configured   │ <N>       │
└───────────────────────────────────┴───────────┘

⚠ Manual configuration needed:
┌──────────────────────┬──────────────────────────────────────────────┐
│ Control              │ Where                                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ <controlDisplayName> │ <configLocation from catalog>                │
└──────────────────────┴──────────────────────────────────────────────┘
(omit the ⚠ table if no SKIPped controls)

Applied by: <UIPATH_USER from ~/.uipath/.auth>  ·  <tenantName>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
```

## report.json (compact run summary — write once)

When the request asks for a machine-readable summary file, write exactly this shape once, at the end:

```json
{
  "packId": "iso-42001-2023",
  "packVersion": "<catalog Data.PackVersion>",
  "posture": {
    "preApplyCoverage": {
      "notYetAppliedSettings": "<Summary.NewCount before apply>",
      "totalSettings": "<Summary.TotalCount>"
    },
    "postApplyVerification": {
      "active": "<Data.active from the single state get>",
      "appliedSettings": "<in-place policy count after apply>",
      "totalSettings": "<Summary.TotalCount>"
    }
  },
  "applyPerformed": true
}
```

Counts come straight from the single coverage snapshot (pre) and the single `state get` (post) — never recompute by re-running commands. `applyPerformed` is `false` only on the `NewCount == 0` guardrail path.

## Org-scope deployment (all tenants)

When the user says "apply to all tenants", "organization-wide", or "entire org", configure each tenant individually.

> **Note:** `state enable organization` is exposed by the CLI but is not implemented on the backend — calling it has no effect. The correct approach is to iterate over all tenants in the org and call `state enable tenant` for each one.

### Step 1 — Discover all tenants in the org

```bash
uip login tenant list --output json > "$SESSION_TEMP/tenants.json"
```

Parse `Data[].TenantName` and `Data[].TenantId` for the list of tenants.

### Step 2 — Run posture analysis per tenant

For each tenant, run coverage to understand current state:

```bash
uip gov compliance-packs state coverage tenant <tenantId> <packId> --output json
```

Aggregate results: note how many tenants have gaps vs are already fully Applied.

### Step 3 — Confirmation

```
Configure ISO 42001 settings across all tenants in <UIPATH_ORGANIZATION_NAME>?

Tenants to configure:
  <tenantName1> — <N> settings Not Applied
  <tenantName2> — <N> settings Not Applied
  <tenantName3> — already fully Applied (will skip)

<totalTenantsToConfig> tenants will be configured. Your auditor determines compliance status.
Continue? (y/n)
```

Require `y`. Halt on anything else. Skip tenants where `NewCount == 0` (all settings already Applied).

### Step 4 — Enable per tenant

For each tenant with gaps, call enable individually:

```bash
for each tenant with NewCount > 0:
  uip gov compliance-packs state enable tenant <tenantId> <packId> --output json
```

### Step 5 — Verify

```bash
for each configured tenant:
  uip gov compliance-packs state get tenant <tenantId> <packId> --output json
```

### Report

```
ISO 42001 settings configured across <N> tenants in <UIPATH_ORGANIZATION_NAME> ✓

┌──────────────────┬──────────────────┐
│ Tenant           │ Status           │
├──────────────────┼──────────────────┤
│ <tenantName1>    │ Applied ✓        │
│ <tenantName2>    │ Applied ✓        │
│ <tenantName3>    │ Already Applied  │
└──────────────────┴──────────────────┘

Applied by: <user>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
```

## Error handling

| Error | Action |
|---|---|
| `state enable` → 4xx | Halt. Report error verbatim. Do NOT retry. |
| `state enable` → 5xx AND `"Retry": "RetryWillNotFix"` | Halt. Report error verbatim. Do NOT retry — the server explicitly flagged retrying as futile. |
| `state enable` → 5xx (transient, no `RetryWillNotFix`) | Retry once after a short pause. If it fails again, halt and report. |
| `Data.active != true` after enable | Unexpected — ask user to run `state get` manually and report the output. |

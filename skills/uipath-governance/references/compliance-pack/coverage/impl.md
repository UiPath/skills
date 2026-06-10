# Coverage — Posture Analysis

Compares the pack's recommended settings against what is currently deployed on the tenant. Does NOT require the pack to be enabled first. Does NOT certify compliance — it identifies which settings from the standard are not yet configured.

## Command

**Pre-condition:** `$SESSION_TEMP/catalog.json` must exist — run `catalog get` first (see `catalog/impl.md`). Coverage joins with catalog data to display meaningful control names.

```bash
SESSION_TEMP="${SESSION_TEMP:-$(mktemp -d)}"  # Windows PS5+: if (-not $env:SESSION_TEMP) { $env:SESSION_TEMP = Join-Path $env:TEMP ('compliance-' + [guid]::NewGuid().ToString('N').Substring(0,8)) ; New-Item $env:SESSION_TEMP -ItemType Directory | Out-Null }
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state coverage tenant $TENANT_ID <packId> --output json \
  > "$SESSION_TEMP/coverage.json"
```

## Parse the response

`Data.deploymentPolicies[].status`:
- `"new"` — this product's settings are not yet configured per standard recommendations; `state enable` will configure them
- `"in-place"` — settings already deployed; no change needed

`Data.clauses[].status`:
- `"needs-policies"` — at least one contributing policy is `"new"`
- `"in-place"` — all contributing policies already deployed

`Data.summary.newCount` — if 0, all recommended settings are already configured.

## Posture plan presentation

Join coverage API data with catalog data to resolve control names and clause names:
- `coverage.deploymentPolicies[].status` — `"new"` or `"in-place"` per product
- `catalog.clauses[].editorialPolicies[].productIdentifier` — maps controls to products
- Control is ✓ if its product's `deploymentPolicy.status == "in-place"`
- Control is ✗ if its product's `deploymentPolicy.status == "new"`

Progress bar: `▓` per configured control, `░` per gap, max 5 chars (e.g. 2/5 = `▓▓░░░`, 4/4 = `▓▓▓▓▓`).

**Biggest risk area:** clause with most ✗ High-impact controls.
**Quickest win:** clause with only 1-2 gap controls AND at least one is High impact.

Terminology rules:
- Use "controls" NOT "settings" in output
- Use plain-English clause names (from `clauses[].clauseName`) in headlines; clause IDs (e.g. A.6.2.8) as secondary reference in DETAILS only
- Use `controls[].displayName` as control name, NOT product identifiers
- "already configured" for ✓ rows, NOT "in-place"
- Never say "compliance gaps" — say "controls not yet configured"
- Never claim the tenant IS compliant

Render the following format:

```
ISO 42001 Posture — <tenantName>  ·  <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY
┌─────────────────────────┬──────────────────────────────────────┐
│ Overall coverage        │ <inPlaceCount> / <totalCount> controls  (<pct>%)  │
│ Clauses fully covered   │ <clausesInPlace> / <totalClauses>                │
│ Clauses with gaps       │ <clausesWithGaps> / <totalClauses>               │
├─────────────────────────┼──────────────────────────────────────┤
│ 🔴 High impact gaps     │ <highGapCount> controls  across <highClauseCount> clauses  │
│ 🟡 Medium impact gaps   │ <medGapCount> controls   across <medClauseCount> clauses   │
│ 🟢 Low impact gaps      │ <lowGapCount> controls   across <lowClauseCount> clauses   │
├─────────────────────────┼──────────────────────────────────────┤
│ Biggest risk area       │ <clauseName with most High-impact gaps>          │
│ Quickest win            │ <clauseName with fewest gaps AND ≥1 High control>│
└─────────────────────────┴──────────────────────────────────────┘

Fix all gaps with: 'Apply ISO 42001 controls'
Fix priority gaps: 'Apply High impact ISO 42001 controls'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLAUSES WITH GAPS  (<N> of <total>)

  <clauseName>                                       <inPlace>/<total> <bar>
  ┌───────────────────────────────────┬─────────────────────┬────────┐
  │ Control                           │ Recommendation      │ Impact │
  ├───────────────────────────────────┼─────────────────────┼────────┤
  │ ✗ <controlDisplayName>            │ <recommendedSetting>│ High   │
  │ ✓ <controlDisplayName>            │ already configured  │ Medium │
  └───────────────────────────────────┴─────────────────────┴────────┘

  [repeat per clause with gaps]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FULLY COVERED  (<N> of <total>)  ✓
┌────────────────────────────────────────┬──────────┐
│ Clause                                 │ Controls │
├────────────────────────────────────────┼──────────┤
│ <clauseName>                           │ X / X  ✓ │
└────────────────────────────────────────┴──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Configure all <N> remaining controls? (y/n)
Or ask: 'Just fix the High impact gaps'
        'Apply only <specific area> controls'
        'What does [clause name] require?'
```

## All controls already configured

If `summary.newCount == 0`:

```
All ISO 42001 controls are already configured on <tenantName>.
42 / 42 controls  ·  14 / 14 clauses fully covered ✓

To remove them: 'Remove ISO 42001 controls'
```

Do NOT call `state enable` in this case.

## Never cache

Always run fresh before presenting a posture plan. Coverage reflects live tenant state.

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

Join coverage with catalog data to give meaningful context. For each "new" product, show High-impact controls from `catalog.clauses[].editorialPolicies[].controls[]` where `impact == "High"` and `productIdentifier` matches.

See `assets/examples/gap-plan-example.md` for the rendered format.

**Language reminder:** Present this as "settings recommended by the standard that are not yet configured" — not as "compliance gaps". The customer's auditor determines actual compliance status.

## All settings already configured

If `summary.newCount == 0`:
"All ISO 42001 recommended settings are already configured on `<tenantName>`. To remove them: 'Disable ISO 42001 settings'."

Do NOT call `state enable` in this case.

## Never cache

Always run fresh before presenting a posture plan. Coverage reflects live tenant state.

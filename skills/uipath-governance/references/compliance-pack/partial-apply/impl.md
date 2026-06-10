# Partial Apply — Implementation

Synthesizes and deploys AOPS policies for the NLP-matched clause/product subset only. Used when the user asked for specific controls rather than the full pack.

**Note:** This configures a subset of ISO 42001 recommended settings. Your organization's auditor determines compliance status.

## Inputs from planning.md

- `targetClauseIds` — comma-separated ISO clauseIds matched from catalog
- `targetProducts` — list of productIdentifiers matched from catalog

## Step 1: Synthesize formData overrides per product

For each `productIdentifier` in `targetProducts`:

```bash
# Read the session dir written by catalog get — same unique dir across all tool calls.
SESSION_TEMP=$(cat "$HOME/.uipath-compliance-current-session")
```
```powershell
# Windows PowerShell
$tmpDir = (Get-Content "$env:TEMP\uipath-compliance-current-session.txt" -Raw).Trim()
```

```bash
# Write synthesize-formdata.mjs to disk first — script at references/compliance-pack/scripts/synthesize-formdata.md
node "$SESSION_TEMP/synthesize-formdata.mjs" \
  --catalog    "$SESSION_TEMP/catalog.json" \
  --product    "<productIdentifier>" \
  --clause-ids "<clauseId1,clauseId2,...>" \
  --out        "$SESSION_TEMP/overrides/<product>.json"
```

Exit 3 = no contributions for this product in these clauses → skip it, continue.

## Step 1b: Collect user-specific values (if any)

After running `synthesize-formdata.mjs`, check stdout for `⚠` warning lines indicating controls that need org-specific values.

For each warned key, ask the user before proceeding:

```
Some recommended settings require values specific to your organization.

⚠ allowed-urls (UIAutomation Allowed URLs):
  Which URLs should UIAutomation be allowed to access?
  Enter as comma-separated list, or SKIP to configure manually in the Admin console later.
  → 
```

Accept responses:
- Non-empty list → write the parsed array into `$SESSION_TEMP/overrides/<product>.json` at the warned key path before moving to Step 2
- `SKIP` → leave the key absent from overrides; surface it in the AOps review gate (Step 4) as a setting that needs manual configuration, with the control's `configLocation` from catalog

**Writing collected values into overrides (example for URL list):**

```bash
node -e "
  const fs = require('fs');
  const p = '$SESSION_TEMP/overrides/Robot.json';
  const o = JSON.parse(fs.readFileSync(p, 'utf8'));
  o['allowed-urls'] = ['https://example.com', 'https://api.example.com'];
  fs.writeFileSync(p, JSON.stringify(o, null, 2));
"
```

## Step 2: Bootstrap template defaults (one call per targetProduct)

Use `products/` as the output dir — this matches the AOps plugin's `$SESSION_DIR/products/` layout so `$SESSION_TEMP` doubles as `SESSION_DIR` for the handoff in Step 4.

Fetch only the products being configured — **do NOT use `template list`** (that fetches all 14 products; partial apply touches 1–2).

```bash
# Bash — one call per product
for product in "${targetProducts[@]}"; do
  mkdir -p "$SESSION_TEMP/products/$product"
  uip gov aops-policy template get "$product" \
    --output-form-data "$SESSION_TEMP/products/$product/form-data.json" \
    --output json
done
```
```powershell
# Windows PowerShell
foreach ($product in $targetProducts) {
  New-Item -ItemType Directory -Force "$tmpDir\products\$product" | Out-Null
  uip gov aops-policy template get $product `
    --output-form-data "$tmpDir\products\$product\form-data.json" `
    --output json
}
```

## Step 3: Merge overrides onto template defaults

```bash
# Write merge-overrides.mjs to disk first — script at references/compliance-pack/scripts/merge-overrides.md
node "$SESSION_TEMP/merge-overrides.mjs" \
  --base      "$SESSION_TEMP/products/<product>/form-data.json" \
  --overrides "$SESSION_TEMP/overrides/<product>.json" \
  --out       "$SESSION_TEMP/merged/<product>.json" \
  --summary
```

## Step 4: Hand off to AOps for policy creation (one product at a time)

The compliance pack is the source of what values to set. The AOps plugin is the create mechanic. For each product where merge succeeded:

**Pre-conditions already satisfied:**
- Bootstrap is done — `$SESSION_TEMP/products/<ProductName>/` holds the templates (AOps `SESSION_DIR` = `$SESSION_TEMP`)
- Policy data is already fully composed at `$SESSION_TEMP/merged/<product>.json`

**Handoff instruction to AOps (`aops-policy-manage-guide.md` — Create flow):**

1. **Skip bootstrap** (already done). Set `SESSION_DIR = $SESSION_TEMP`.
2. **Case A** — product already known. Skip intent inference.
3. **Skip form.io traversal** — policy data is already composed. Copy `$SESSION_TEMP/merged/<product>.json` to `$SESSION_TEMP/aops-policy-data.json`.
4. **Policy name:** `iso-42001-2023-<scopeToken>-<product-kebab>` — see Internal policy naming note below.
5. **Proceed to review gate** (AOps Critical Rules #15/#16):
   - AOps compares `aops-policy-data.json` against `products/<product>/form-data.json` defaults — the diff is exactly the compliance pack-recommended controls for the targeted clauses, nothing more.
   - Show the confirmation gate using this template:

```
Configure ISO 42001 controls on <tenantName>?

<clauseName>  (<clauseId>)
┌───────────────────────────────────┬─────────────────────┬────────┐
│ Control                           │ Recommendation      │ Impact │
├───────────────────────────────────┼─────────────────────┼────────┤
│ <controlDisplayName>              │ <recommendedSetting>│ High   │
│ <controlDisplayName>              │ <recommendedSetting>│ Medium │
└───────────────────────────────────┴─────────────────────┴────────┘
[repeat table per clause if multiple clauses matched]

<N> controls  ·  <productDisplayName> only
Other products will NOT be affected.

⚠ Some controls need manual configuration after apply:
  • <controlDisplayName>  →  <configLocation from catalog>
(omit ⚠ block if no SKIPped controls)

These controls improve your posture towards ISO 42001 requirements.
Proceed? (y/n)
```

Build control rows from: `catalog.clauses[].editorialPolicies[].controls[]` filtered to `targetClauseIds` and `targetProducts`. Use `controls[].displayName` as control name, `controls[].recommendedSetting` as recommendation, `controls[].impact` as impact.

Require y. Halt on anything else.

> **Internal policy naming:** `iso-42001-2023-<scopeToken>-<product-kebab>` — scopeToken per product: `aitl` (AITrustLayer), `dev` (Development), `robot` (Robot), `asst` (Assistant), `stw` (StudioWeb), `is` (IntegrationService); per clause subset: `a628` (A.6.2.8), `a92` (A.9.2); per impact subset: `high`.
6. On `yes` → AOps runs `aops-policy create` → **return the policy UUID to partial apply**.
7. On failure or skip → log product as `skipped`, continue to next product.

**Collect all policy UUIDs** from successful creates before proceeding to Step 5.

## Step 5: Deploy to tenant — single consolidated call

`deployment tenant configure` is a FULL REPLACE. Always read current state first.

```bash
uip gov aops-policy deployment tenant get $TENANT_ID --output json \
  > "$SESSION_TEMP/current-assignments-raw.json"
```

**Windows (PowerShell):** Read the session dir from the sentinel file written by `catalog get` — never use a fixed hardcoded path (that causes cross-session contamination). `$tmpDir = (Get-Content "$env:TEMP\uipath-compliance-current-session.txt" -Raw).Trim()`

Build the new assignments array using Node.js to handle PascalCase CLI output and correct JSON serialization. Write a script `$SESSION_TEMP/merge-assignments.mjs`:

```js
import fs from 'node:fs';
const tmpDir = process.argv[2];
// Read from file — avoids PowerShell inline-JSON quoting issues (see Fix 2 below)
const policyEntries = JSON.parse(fs.readFileSync(`${tmpDir}/policy-entries.json`, 'utf8'));
const raw = JSON.parse(fs.readFileSync(`${tmpDir}/current-assignments-raw.json`, 'utf8'));
// Data.tenantPolicies contains the assignments — NOT Data itself
const existing = (raw.Data?.tenantPolicies ?? [])
  .map(p => ({
    productIdentifier:     p.ProductIdentifier,
    licenseTypeIdentifier: p.LicenseTypeIdentifier,
    // Explicit presence check preserves null ("No Policy" pin) — avoids null??undefined→undefined
    // which causes JSON.stringify to drop the key and the API to reject with "must be string or null"
    policyIdentifier: 'PolicyIdentifier' in p ? p.PolicyIdentifier : (p.policyIdentifier ?? null),
  }))
  .filter(p => !policyEntries.some(e => e.product === p.productIdentifier));
for (const e of policyEntries) {
  existing.push({ productIdentifier: e.product, licenseTypeIdentifier: e.licenseType, policyIdentifier: e.policyId });
}
fs.writeFileSync(`${tmpDir}/new-assignments.json`, JSON.stringify(existing, null, 2));
console.log(`Written ${existing.length} entries`);
```

**Fix 2 — Write policy entries to a file instead of passing inline JSON.** PowerShell mangles single-quoted JSON arguments passed to Node — routing through a file avoids all quoting issues on both platforms.

Write `policy-entries.json` first:
```bash
# Bash
printf '%s' '[{"product":"AITrustLayer","licenseType":"NoLicense","policyId":"<uuid>"}]' \
  > "$SESSION_TEMP/policy-entries.json"
```
```powershell
# Windows PowerShell
'[{"product":"AITrustLayer","licenseType":"NoLicense","policyId":"<uuid>"}]' |
  Set-Content "$tmpDir\policy-entries.json" -NoNewline
```

Update the script to read from file instead of argv[3] — change the line `const policyEntries = JSON.parse(process.argv[3]);` to:
```js
const policyEntries = JSON.parse(fs.readFileSync(`${tmpDir}/policy-entries.json`, 'utf8'));
```

Then run:
```bash
node "$SESSION_TEMP/merge-assignments.mjs" "$SESSION_TEMP"
```
```powershell
# Windows PowerShell
node "$tmpDir\merge-assignments.mjs" $tmpDir
```

licenseType per product: `AITrustLayer→NoLicense`, `Development→Development`, `StudioWeb→Development`, `Robot→Attended`, `Assistant→NoLicense`, `Integration Service→NoLicense`

**Input file format** — only 3 fields; `tenantIdentifier` and `tenantName` are added by the CLI from its own arguments, not from the file:
```json
[
  { "productIdentifier": "<p>", "licenseTypeIdentifier": "<l>", "policyIdentifier": "<uuid-or-null>" }
]
```

```bash
uip gov aops-policy deployment tenant configure $TENANT_ID \
  --tenant-name "$TENANT_NAME" \
  --input       "$SESSION_TEMP/new-assignments.json" \
  --output json
```

## Step 6: Write local deploy record

```json
{
  "packId":      "iso-42001-2023",
  "applyMode":   "partial",
  "scopeToken":  "<scopeToken>",
  "clauseIds":   ["<matched clauseIds>"],
  "products":    ["<productIdentifiers>"],
  "appliedAt":   "<ISO timestamp>",
  "tenantId":    "<UIPATH_TENANT_ID>",
  "tenantName":  "<UIPATH_TENANT_NAME>",
  "policies": [
    { "product": "AITrustLayer", "policyId": "<uuid>", "policyName": "<name>" }
  ]
}
```

File: `$HOME/uipath-governance/audit/deploy-records/deploy-record-iso-42001-2023-<scopeToken>-<timestamp>.json`

## Report (after successful apply)

```
ISO 42001 controls configured on <tenantName>.

┌───────────────────────────────────┬───────────┐
│ Controls configured               │ <N>       │
│ Clauses addressed                 │ <N>       │
│ High impact controls              │ <N>       │
└───────────────────────────────────┴───────────┘

⚠ Manual configuration needed:
┌──────────────────────┬──────────────────────────────────────────────┐
│ Control              │ Where                                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ <controlDisplayName> │ <configLocation>                             │
└──────────────────────┴──────────────────────────────────────────────┘
(omit ⚠ table if no SKIPped controls)

Applied by: <UIPATH_USER from ~/.uipath/.auth>  ·  <tenantName>  ·  <date>

To configure all ISO 42001 controls: 'Apply the full ISO 42001 pack'
```

## Error handling

| Error | Action |
|---|---|
| `synthesize-formdata.mjs` exit 3 | Skip that product. Log: "No recommended settings found for <product> in selected clauses." Continue. |
| `aops-policy create` → 4xx | Halt. Record remaining as `status: "skipped"`. Write deploy record. |
| `deployment tenant configure` → 4xx | Halt. Write deploy record with `status: "failed"`. Report error. |

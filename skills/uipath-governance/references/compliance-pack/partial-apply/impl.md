# Partial Apply — Implementation

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Synthesizes and deploys AOPS policies for the NLP-matched clause/product subset only. Used when the user asked for specific settings rather than the full standard.

**Note:** This configures a subset of ISO 42001 recommended settings. Your organization's auditor determines compliance status.

## Inputs from planning.md

- `targetClauseIds` — comma-separated ISO clauseIds matched from catalog
- `targetProducts` — list of productIdentifiers matched from catalog

## Step 0: Get the pack catalog first (required)

The `synthesize-formdata` script reads `catalog.json`, so `catalog get` MUST run before Step 1. If `$SESSION_TEMP/catalog.json` does not exist yet, run it now (see `catalog/impl.md`):

```bash
uip gov compliance-packs catalog get <packId> --output json > "$SESSION_TEMP/catalog.json"
```

Do not synthesize, hand-roll formData, or default any value without this file — the catalog is the only source of which controls exist and which are org-specific.

## Step 1: Synthesize formData overrides per product

Run the shipped [`synthesize-formdata`](synthesize-formdata-guide.md) script (args, exit codes, and warning handling are in that guide) — it is the ONLY sanctioned way to build formData overrides, and it surfaces the `notEmpty` prompts in Step 1b. Do NOT hand-roll a substitute or default the values; running it is mandatory even when every org-specific value will be answered SKIP.

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
# Run the shipped script in place (do NOT recreate it). See synthesize-formdata-guide.md.
# <SKILL_DIR> = the folder containing this skill's SKILL.md.
node "<SKILL_DIR>/scripts/synthesize-formdata.mjs" \
  --catalog    "$SESSION_TEMP/catalog.json" \
  --product    "<productIdentifier>" \
  --clause-ids "<clauseId1,clauseId2,...>" \
  --out        "$SESSION_TEMP/overrides/<product>.json"
```

Exit 3 = no contributions for this product in these clauses → skip it, continue.

## Step 1b: Collect user-specific values (if any)

After running `synthesize-formdata`, check **stderr** for `⚠` warning lines. (The script uses `console.warn`, which writes to stderr.) Each line names the control key and its required-operator class — branch on the class, do NOT treat every `⚠` line as a value prompt:

- **`notEmpty`** — an org-specific value the user must supply. Prompt for it (below).
- **`exists`** — an access-policy check, not a formData value; there is nothing to type. Surface it as a manual-configuration note in the Step 4 review gate; do NOT prompt.
- **unknown operator** — surface as a manual-configuration note; do NOT prompt.

Detection is by operator class (matched from the script's structured warning), not a fixed message string — new controls with the same class are handled automatically.

For each `notEmpty` key, ask the user before proceeding:

```
Some recommended settings require values specific to your organization.

⚠ allowed-urls (UIAutomation Allowed URLs):
  Which URLs should UIAutomation be allowed to access?
  Enter as comma-separated list, or SKIP to configure manually in the Admin console later.
  → 
```

Accept responses:
- Non-empty list → write the parsed array into `$SESSION_TEMP/overrides/<product>.json` at the warned key path before moving to Step 2
- `SKIP` → leave the key absent from overrides; surface it in the AOps review gate (Step 4) as a setting that needs manual configuration, with the setting's `configLocation` from catalog

**Do not proceed to Step 2 until every `notEmpty` prompt is resolved** — each answered with a value or an explicit SKIP. Never continue the apply with placeholder or default values while a required value is still outstanding. Run the `synthesize-formdata` script once per product: the warnings from that single run are the complete list — do not re-run it to re-check.

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

Run the shipped [`merge-overrides`](merge-overrides-guide.md) script (merge rules and exit codes are in that guide).

```bash
# Run the shipped script in place (do NOT recreate it). See merge-overrides-guide.md.
# <SKILL_DIR> = the folder containing this skill's SKILL.md.
node "<SKILL_DIR>/scripts/merge-overrides.mjs" \
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
   - AOps compares `aops-policy-data.json` against `products/<product>/form-data.json` defaults — the diff is exactly the compliance standard-recommended settings for the targeted clauses, nothing more.
   - Show the confirmation gate using this template:

```
Configure ISO 42001 settings on <tenantName>?

<clauseName>  (<clauseId>)
┌───────────────────────────────────┬─────────────────────┬────────┐
│ Setting                           │ Recommendation      │ Impact │
├───────────────────────────────────┼─────────────────────┼────────┤
│ <controlDisplayName>              │ <recommendedSetting>│ High   │
│ <controlDisplayName>              │ <recommendedSetting>│ Medium │
└───────────────────────────────────┴─────────────────────┴────────┘
[repeat table per clause if multiple clauses matched]

<N> settings  ·  <productDisplayName> only
Other products will NOT be affected.

⚠ Some settings need manual configuration after apply:
  • <controlDisplayName>  →  <configLocation from catalog>
(omit ⚠ block if no SKIPped settings)

These settings improve your posture towards ISO 42001 requirements.
Proceed? (y/n)
```

Build setting rows from: `catalog.clauses[].editorialPolicies[].controls[]` filtered to `targetClauseIds` and `targetProducts`. Use `controls[].displayName` as setting name, `controls[].recommendedSetting` as recommendation, `controls[].impact` as impact.

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
// CLI returns PascalCase — dual-case handles both PascalCase and camelCase variants.
// TenantPolicies must be resolved before mapping, otherwise existing resolves to []
// and deployment configure silently wipes all current tenant pins (full replace!).
const policies = raw.Data?.TenantPolicies ?? raw.Data?.tenantPolicies ?? [];
const existing = policies
  .map(p => ({
    productIdentifier:     p.ProductIdentifier     ?? p.productIdentifier,
    licenseTypeIdentifier: p.LicenseTypeIdentifier ?? p.licenseTypeIdentifier,
    // Preserve null ("No Policy" pin) — dropping the key causes the API to reject with "must be string or null"
    policyIdentifier: p.PolicyIdentifier !== undefined ? p.PolicyIdentifier : (p.policyIdentifier ?? null),
  }))
  .filter(p => !policyEntries.some(e => e.product === p.productIdentifier));
for (const e of policyEntries) {
  existing.push({ productIdentifier: e.product, licenseTypeIdentifier: e.licenseType, policyIdentifier: e.policyId });
}
fs.writeFileSync(`${tmpDir}/new-assignments.json`, JSON.stringify(existing, null, 2));
console.log(`Written ${existing.length} entries`);
```

Write `policy-entries.json` first (avoids PowerShell inline-JSON quoting issues):
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

## Report (after successful apply)

```
ISO 42001 settings configured on <tenantName>.

┌───────────────────────────────────┬───────────┐
│ Settings configured               │ <N>       │
│ Clauses addressed                 │ <N>       │
│ High impact settings              │ <N>       │
└───────────────────────────────────┴───────────┘

⚠ Manual configuration needed:
┌──────────────────────┬──────────────────────────────────────────────┐
│ Control              │ Where                                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ <controlDisplayName> │ <configLocation>                             │
└──────────────────────┴──────────────────────────────────────────────┘
(omit ⚠ table if no SKIPped settings)

Applied by: <UIPATH_USER from ~/.uipath/.auth>  ·  <tenantName>  ·  <date>

To configure all ISO 42001 settings: 'Apply the full ISO 42001 standard'
```

## Error handling

| Error | Action |
|---|---|
| Any compliance-packs call (e.g. `catalog get`) → **403 / Forbidden** | Org not enrolled in the Compliance Standards preview — stop, do not retry. Show the opt-in message. See [preview-gate.md](../preview-gate.md). |
| `synthesize-formdata.mjs` exit 3 | Skip that product. Log: "No recommended settings found for <product> in selected clauses." Continue. |
| `aops-policy create` → 4xx | Halt. Report error verbatim. Do NOT retry. |
| `deployment tenant configure` → 4xx | Halt. Report error verbatim. |

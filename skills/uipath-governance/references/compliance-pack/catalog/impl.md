# Catalog — Pack Discovery and Detail

## Discover available packs

```bash
uip gov compliance-packs catalog list --output json
```

Parse `Data.packs[]`. Present each pack:
- `packName` / `packLongName`
- `packVersion`
- `summary.clauseCount`, `summary.controlCount`, `summary.deploymentPolicyCount`

## Get full pack detail

```bash
# Create a unique session dir and persist the path to disk so it survives between tool calls.
# Every downstream plugin reads this file to find the shared session dir.
SESSION_TEMP=$(mktemp -d)
echo "$SESSION_TEMP" > "$HOME/.uipath-compliance-current-session"
uip gov compliance-packs catalog get <packId> --output json > "$SESSION_TEMP/catalog.json"
```

```powershell
# Windows PowerShell — env vars don't persist between tool calls; write the path to a file instead.
$tmpDir = Join-Path $env:TEMP ('compliance-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Force $tmpDir | Out-Null
$tmpDir | Set-Content "$env:TEMP\uipath-compliance-current-session.txt" -NoNewline
uip gov compliance-packs catalog get <packId> --output json | Set-Content "$tmpDir\catalog.json"
```

Save to `$SESSION_TEMP/catalog.json` (Bash) or `$tmpDir\catalog.json` (Windows). This file feeds all downstream plugins. Always run this step **before** `state coverage`, `partial-apply`, or `query` — those plugins resolve the session dir from the sentinel file.

Key fields in `Data`:

| Field | Used by |
|---|---|
| `packId` | All state commands |
| `deploymentPolicies[].productIdentifier` | Coverage + apply: which products are covered |
| `deploymentPolicies[].productDisplayName` | User-facing product name |
| `clauses[].clauseId` | Partial apply: clause filtering |
| `clauses[].clauseName` | User-facing clause name |
| `clauses[].editorialPolicies[].productIdentifier` | Maps clause to product |
| `clauses[].editorialPolicies[].controls[].displayName` | NLP matching + query display |
| `clauses[].editorialPolicies[].controls[].impact` | `"High"` / `"Medium"` / `"Low"` |
| `clauses[].editorialPolicies[].controls[].recommendedSetting` | What value will be configured |
| `clauses[].editorialPolicies[].controls[].configLocation` | Where to find it in the UI |
| `clauses[].editorialPolicies[].contributions[].key` | formData property key (dotted path) |
| `clauses[].editorialPolicies[].contributions[].required` | Operator → synthesize-formdata.mjs |

## List currently configured packs

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state list tenant $TENANT_ID --output json
```

Parse `Data[]` — each entry has `packId`, `packVersion`, `active` (bool), `lastToggledAt`. Present active packs to the user:

```
Compliance packs configured on <tenantName>:

  ISO 42001 (iso-42001-2023 v3.0.0) — Active since <lastToggledAt>

No other compliance packs are currently active.
```

If the array is empty: "No compliance packs are currently configured on this tenant."

## Pack ID lookup

| User says | packId |
|---|---|
| "ISO 42001" / "ISO/IEC 42001" / "AI Management System" | `iso-42001-2023` |
| Unrecognised standard | Run `catalog list`, present options, ask user to choose |

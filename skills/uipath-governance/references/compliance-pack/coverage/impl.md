# Coverage — Posture Analysis

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Compares the compliance standard's recommended settings against what is currently deployed on the tenant. Does NOT require the standard to be enabled first. Does NOT certify compliance — it identifies which settings from the standard are not yet configured.

## Command

**Pre-condition:** `$SESSION_TEMP/catalog.json` must exist — run `catalog get` first (see `catalog/impl.md`). Coverage joins with catalog data to display meaningful setting names.

```bash
# Read the session dir written by catalog get — never create a new one here.
SESSION_TEMP=$(cat "$HOME/.uipath-compliance-current-session")
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state coverage tenant $TENANT_ID <packId> --output json \
  > "$SESSION_TEMP/coverage.json"
```

```powershell
# Windows PowerShell
$tmpDir = (Get-Content "$env:TEMP\uipath-compliance-current-session.txt" -Raw).Trim()
$tenantId = (Select-String '^UIPATH_TENANT_ID=(.+)' "$env:USERPROFILE\.uipath\.auth").Matches[0].Groups[1].Value
uip gov compliance-packs state coverage tenant $tenantId <packId> --output json |
  Set-Content "$tmpDir\coverage.json"
```

## Parse the response

CLI output is **PascalCase**. Field names below are exactly as returned by `state coverage`.

`Data.DeploymentPolicies[].Status`:
- `"new"` — this product's settings are not yet configured; `state enable` will configure them — display as **Not Applied** to the user
- `"in-place"` — settings already deployed; no change needed — display as **Applied** to the user

`Data.Clauses[].Status`:
- `"needs-policies"` — at least one contributing policy is `"new"` — display as **Needs Manual Configuration** to the user
- `"in-place"` — all contributing policies already deployed — display as **Applied** to the user

`Data.Summary.NewCount` — if 0, all recommended settings are already configured.

## Posture plan presentation

Join coverage API data with catalog data to resolve setting names and clause names:
- `coverage.Data.DeploymentPolicies[].Status` — `"new"` or `"in-place"` per product
- `catalog.Data.Clauses[].EditorialPolicies[].ProductIdentifier` — maps settings to products
- Setting is Applied (✓) if its product's `Status == "in-place"`
- Setting is Not Applied (✗) if its product's `Status == "new"`

Progress bar: `▓` per configured setting, `░` per gap, max 5 chars (e.g. 2/5 = `▓▓░░░`, 4/4 = `▓▓▓▓▓`).

**Biggest risk area:** clause with most ✗ High-impact settings.
**Quickest win:** clause with only 1-2 gap settings AND at least one is High impact.

Terminology rules:
- Use "settings" NOT "controls" in output
- Use plain-English clause names (from `clauses[].clauseName`) in headlines; clause IDs (e.g. A.6.2.8) as secondary reference in DETAILS only
- Use `controls[].displayName` as setting name, NOT product identifiers
- **NEVER write raw API status strings** (`in-place`, `new`, `not-deployed`, `fully-deployed`, `needs-policies`) in user-facing display output (posture_plan.txt, chat responses, report summaries) — translate EVERY occurrence before writing
  - `"in-place"` → **Applied** (or ✓)
  - `"new"` → **Not Applied** (or ✗)
- **`coverage.json` is an internal session file** — save it as the raw `--output json` CLI response. Raw API values (`"in-place"`, `"new"`) are CORRECT and expected in this file. Do NOT translate status values when writing coverage.json.
- Never say "compliance gaps" — say "settings not yet configured"
- Never claim the tenant IS compliant

Render the following format:

```
ISO 42001 Posture — <tenantName>  ·  <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY
┌─────────────────────────┬──────────────────────────────────────┐
│ Overall coverage        │ <inPlaceCount> / <totalCount> settings  (<pct>%)  │
│ Clauses fully covered   │ <clausesInPlace> / <totalClauses>                │
│ Clauses with gaps       │ <clausesWithGaps> / <totalClauses>               │
├─────────────────────────┼──────────────────────────────────────┤
│ 🔴 High impact gaps     │ <highGapCount> settings Not Applied  across <highClauseCount> clauses  │
│ 🟡 Medium impact gaps   │ <medGapCount> settings Not Applied   across <medClauseCount> clauses   │
│ 🟢 Low impact gaps      │ <lowGapCount> settings Not Applied   across <lowClauseCount> clauses   │
├─────────────────────────┼──────────────────────────────────────┤
│ Biggest risk area       │ <clauseName with most High-impact settings Not Applied>          │
│ Quickest win            │ <clauseName with fewest gaps AND ≥1 High setting>│
└─────────────────────────┴──────────────────────────────────────┘

Fix all gaps with: 'Apply ISO 42001 settings'
Fix priority gaps: 'Apply High impact ISO 42001 settings'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Needs Configuration  (<N> of <total>)

  <clauseName>                                       <inPlace>/<total> <bar>
  ┌───────────────────────────────────┬─────────────────────┬────────┐
  │ Setting                           │ Recommendation      │ Impact │
  ├───────────────────────────────────┼─────────────────────┼────────┤
  │ ✗ <controlDisplayName>            │ <recommendedSetting>│ High   │
  │ ✓ <controlDisplayName>            │ Applied             │ Medium │
  └───────────────────────────────────┴─────────────────────┴────────┘

  [repeat per clause with gaps]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Applied  (<N> of <total>)  ✓
┌────────────────────────────────────────┬──────────┐
│ Clause                                 │ Settings │
├────────────────────────────────────────┼──────────┤
│ <clauseName>                           │ X / X  ✓ │
└────────────────────────────────────────┴──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Configure all <N> remaining settings? (y/n)
Or ask: 'Just fix the High impact gaps'
        'Apply only <specific area> settings'
        'What does [clause name] require?'
```

## All settings applied

If `summary.newCount == 0`:

```
All ISO 42001 recommended settings are Applied on <tenantName>.
42 / 42 settings  ·  14 / 14 clauses fully covered ✓

To remove them: 'Remove ISO 42001 settings'
```

Do NOT call `state enable` in this case.

## Never cache

Always run fresh before presenting a posture plan. Coverage reflects live tenant state.

## Anti-patterns

- **Writing raw API status strings in user-facing display output** — `in-place`, `new`, `not-deployed`, `fully-deployed`, `needs-policies` must NEVER appear in user-facing display output (posture_plan.txt, chat responses, report summaries). Translate every status before writing. `coverage.json` is an internal session file — raw API values are correct there.
- **Partial translation** — translating the summary section but leaving raw values in the DETAILS or verification section. ALL sections must use the translated labels.
- **Quoting API values for context** — avoid notes like "Status is still 'new'". Rephrase to "AI Trust Layer shows as Not Applied" instead.

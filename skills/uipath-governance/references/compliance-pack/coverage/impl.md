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

`Data.Clauses[].Status` (per-control rollup):
- `"fully-deployed"` — every checkable setting satisfied — display as **Applied** (✓)
- `"partially-deployed"` — some but not all satisfied — display as **Partially Applied** (◐)
- `"not-deployed"` — none satisfied — display as **Not Applied** (✗)

`Data.Clauses[].controls[]` (per-setting; present on updated CLI) — the truthful per-setting view:
- `controlDisplayName` — setting name
- `productIdentifier` — owning product
- `impact` — `"High"` / `"Medium"` / `"Low"`
- `recommendedSetting` — the recommended value
- `status` — `"applied"` (✓) / `"not-applied"` (✗) / `"needs-manual-config"` (⚙, admin must set a value)

`Data.Summary.NewCount` — if 0, all recommended settings are already configured.

## Posture plan presentation

Build the per-setting table directly from `coverage.Data.Clauses[].controls[]` — do NOT derive setting state from product status:
- ✓ Applied — `control.status == "applied"`
- ✗ Not Applied — `control.status == "not-applied"`
- ⚙ Needs Manual Configuration — `control.status == "needs-manual-config"`

Per-clause counts come from the clause's own `controls[]` (or `deployedControlCount` / `checkableControlCount`). Product coverage (`DeploymentPolicies[].Status`) is a secondary, product-grain signal only — never project it onto individual settings.

**Graceful degrade:** if `Clauses[].controls` is absent (older CLI/server), fall back to the clause-grain view (`Clauses[].Status` fully/partially/not-deployed) and add a one-line note that per-setting detail needs an updated `uip` CLI. Never fabricate per-setting state.

Progress bar: `▓` per configured setting, `░` per gap, max 5 chars (e.g. 2/5 = `▓▓░░░`, 4/4 = `▓▓▓▓▓`).

**Biggest risk area:** clause with the most `not-applied` High-impact controls (`controls[].status == "not-applied" && impact == "High"`).
**Quickest win:** clause with the fewest non-applied controls (`not-applied` + `needs-manual-config`) AND at least one is High impact.

Terminology rules:
- Use "settings" NOT "controls" in output
- Use plain-English clause names (from `clauses[].clauseName`) in headlines; clause IDs (e.g. A.6.2.8) as secondary reference in DETAILS only
- Use `controls[].displayName` as setting name, NOT product identifiers
- **NEVER write raw API status strings** — product `in-place`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `applied`/`not-applied`/`needs-manual-config` — in user-facing display output (posture_plan.txt, chat responses, report summaries) — translate EVERY occurrence before writing
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
│ Overall coverage        │ <appliedControlCount> / <checkableControlCount> settings  (<pct>%)  │
│ Clauses fully covered   │ <clausesFullyDeployed> / <totalClauses>          │
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

  <clauseName>                                       <deployedControlCount>/<checkableControlCount> <bar>
  ┌───────────────────────────────────┬─────────────────────┬────────┐
  │ Setting                           │ Recommendation      │ Impact │
  ├───────────────────────────────────┼─────────────────────┼────────┤
  │ ✗ <controlDisplayName>            │ <recommendedSetting>│ High   │
  │ ⚙ <controlDisplayName>            │ <recommendedSetting>│ Medium │
  │ ✓ <controlDisplayName>            │ Applied             │ Medium │
  └───────────────────────────────────┴─────────────────────┴────────┘
  Marker = `control.status`: ✓ applied · ✗ not-applied · ⚙ needs-manual-config

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

- **Writing raw API status strings in user-facing display output** — product `in-place`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `applied`/`not-applied`/`needs-manual-config` — must NEVER appear in user-facing display output (posture_plan.txt, chat responses, report summaries). Translate every status before writing. `coverage.json` is an internal session file — raw API values are correct there.
- **Partial translation** — translating the summary section but leaving raw values in the DETAILS or verification section. ALL sections must use the translated labels.
- **Quoting API values for context** — avoid notes like "Status is still 'new'". Rephrase to "AI Trust Layer shows as Not Applied" instead.
- **Deriving per-setting state from product status** — use `Clauses[].controls[].status` (`applied`/`not-applied`/`needs-manual-config`). Never mark a setting Applied because its product is `in-place`.

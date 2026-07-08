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
- `status` — `"deployed"` (✓ Applied) / `"not-deployed"` (✗ Not Applied) / `"manual"` (⚙ Needs Manual Configuration — admin must set a value)

`Data.Clauses[].manualConfigChecks[]` (the actionable "what to set" detail behind every `status == "manual"` control) — join to a `controls[]` entry by `controlDisplayName`:
- `controlDisplayName` — the setting
- `productIdentifier` — owning product
- `expected` — the value the standard requires, as a predicate object (`{eq}` / `{gte}` / `{lte}` / `{contains}`); render human-readable (`{gte: 30}` → "at least 30", `{eq: true}` → "Enabled")
- `actual` — the value currently deployed on the tenant (absent / `null` when unset)

`Data.Summary` (PRODUCT-grain counts + a clause rollup — read these directly, do NOT recompute):
- `DeploymentPolicyCount` — total products the pack governs · `InPlaceCount` — products fully Applied · `NewCount` — products with any gap (if `0`, every product is fully in place)
- `ClauseSummary.FullyDeployedCount` / `PartiallyDeployedCount` / `NotDeployedCount` — the clause rollup driving the SUMMARY counts

`Data.PackId` / `ScopeLevel` / `ScopeTargetId` — identify the pack + tenant scope (internal; the user sees the tenant NAME from auth context, not the id).

Product display names come from `catalog.Data.DeploymentPolicies[].ProductDisplayName` (join by `ProductIdentifier`), NOT from the coverage payload.

## Posture plan presentation

Build the per-setting table directly from `coverage.Data.Clauses[].controls[]` — do NOT derive setting state from product status:
- ✓ Applied — `control.status == "deployed"`
- ✗ Not Applied — `control.status == "not-deployed"`
- ⚙ Needs Manual Configuration — `control.status == "manual"`

Per-clause counts come from the clause's own `controls[]` (or `deployedControlCount` / `checkableControlCount`). The SUMMARY clause counts come from `Data.Summary.ClauseSummary.*` directly.

For each ⚙ `manual` control, look up its `Data.Clauses[].manualConfigChecks[]` entry (match on `controlDisplayName`) and show what to change: **expected** value vs **currently** deployed value. This is the actionable detail — surface it, don't stop at the ⚙ marker.

Product coverage is a real secondary section, not just an internal signal: render `Data.DeploymentPolicies[]` (per-product ✓ Applied / ✗ Not Applied) with the `Data.Summary.InPlaceCount / DeploymentPolicyCount` headline — it is the grain `state enable` / apply operates on. Never project product status onto individual settings.

**Graceful degrade:** if `Clauses[].controls` is absent (older CLI/server), fall back to the clause-grain view (`Clauses[].Status` fully/partially/not-deployed) and add a one-line note that per-setting detail needs an updated `uip` CLI. Never fabricate per-setting state.

Progress bar: `▓` per configured setting, `░` per gap, max 5 chars (e.g. 2/5 = `▓▓░░░`, 4/4 = `▓▓▓▓▓`).

**Biggest risk area:** clause with the most `not-deployed` High-impact controls (`controls[].status == "not-deployed" && impact == "High"`).
**Quickest win:** clause with the fewest unapplied controls (`not-deployed` + `manual`) AND at least one is High impact.

Terminology rules:
- Use "settings" NOT "controls" in output
- Use plain-English clause names (from `clauses[].clauseName`) in headlines; clause IDs (e.g. A.6.2.8) as secondary reference in DETAILS only
- Use `controls[].displayName` as setting name, NOT product identifiers
- **NEVER write raw API status strings** — product `in-place`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `deployed`/`not-deployed`/`manual` — in user-facing display output (posture_plan.txt, chat responses, report summaries) — translate EVERY occurrence before writing
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
  Marker = `control.status`: ✓ deployed · ✗ not-deployed · ⚙ manual
  For each ⚙ row, add a sub-line from manualConfigChecks (expected vs actual):
    ⚙ <controlDisplayName> — set to <expected>; currently <actual, or "not set">

  [repeat per clause with gaps]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Applied  (<N> of <total>)  ✓
┌────────────────────────────────────────┬──────────┐
│ Clause                                 │ Settings │
├────────────────────────────────────────┼──────────┤
│ <clauseName>                           │ X / X  ✓ │
└────────────────────────────────────────┴──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Product coverage  (<inPlaceCount> / <deploymentPolicyCount> products Applied)
  ✓ <productDisplayName>   Applied       [DeploymentPolicies[].status == "in-place"]
  ✗ <productDisplayName>   Not Applied   [DeploymentPolicies[].status == "new"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Configure all <N> remaining settings? (y/n)
Or ask: 'Just fix the High impact gaps'
        'Apply only <specific area> settings'
        'What does [clause name] require?'
```

## All settings applied

If `Summary.NewCount == 0` (every product in-place) — equivalently `Summary.ClauseSummary.PartiallyDeployedCount == 0 && NotDeployedCount == 0`:

```
All ISO 42001 recommended settings are Applied on <tenantName>.
<deploymentPolicyCount> / <deploymentPolicyCount> products  ·  <fullyDeployedCount> / <totalClauses> clauses fully deployed ✓

To remove them: 'Remove ISO 42001 settings'
```

Do NOT call `state enable` in this case.

## Never cache

Always run fresh before presenting a posture plan. Coverage reflects live tenant state.

## Anti-patterns

- **Writing raw API status strings in user-facing display output** — product `in-place`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `deployed`/`not-deployed`/`manual` — must NEVER appear in user-facing display output (posture_plan.txt, chat responses, report summaries). Translate every status before writing. `coverage.json` is an internal session file — raw API values are correct there.
- **Partial translation** — translating the summary section but leaving raw values in the DETAILS or verification section. ALL sections must use the translated labels.
- **Quoting API values for context** — avoid notes like "Status is still 'new'". Rephrase to "AI Trust Layer shows as Not Applied" instead.
- **Deriving per-setting state from product status** — use `Clauses[].controls[].status` (`deployed`/`not-deployed`/`manual`). Never mark a setting Applied because its product is `in-place`.

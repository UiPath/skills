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

`Data.DeploymentPolicies[].Status` (product-grain; INTERNAL — never rendered to the user, never projected onto settings). Three disjoint values:
- `"in-place"` — product fully satisfied · `"needs-manual-config"` — deployed but ≥1 control still needs manual setup · `"new"` — nothing deployed for this product
- INTERNAL only; the user-facing posture is driven entirely by clauses + per-setting `controls[]`. Do NOT gate the all-applied case on `Summary.NewCount == 0` — with the disjoint counts a `needs-manual-config` product leaves `NewCount == 0` yet the pack is not fully applied.

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
- `DeploymentPolicyCount` — total products · three **disjoint** product tallies that sum to it: `InPlaceCount` (fully applied) + `NeedsManualConfigCount` (deployed, manual setup pending) + `NewCount` (nothing deployed). `NewCount == 0` does NOT mean fully applied — needs-manual-config products aren't counted in it.
- `ClauseSummary.FullyDeployedCount` / `PartiallyDeployedCount` / `NotDeployedCount` — the clause rollup driving the SUMMARY counts and the all-applied check

`Data.PackId` / `ScopeLevel` / `ScopeTargetId` — identify the pack + tenant scope (internal; the user sees the tenant NAME from auth context, not the id).

## Posture plan presentation

Build the per-setting table directly from `coverage.Data.Clauses[].controls[]` — do NOT derive setting state from product status:
- ✓ Applied — `control.status == "deployed"`
- ✗ Not Applied — `control.status == "not-deployed"`
- ⚙ Needs Manual Configuration — `control.status == "manual"`

Per-clause counts come from the clause's own `controls[]` (or `deployedControlCount` / `checkableControlCount`). The SUMMARY clause counts come from `Data.Summary.ClauseSummary.*` directly.

For each ⚙ `manual` control, look up its `Data.Clauses[].manualConfigChecks[]` entry (match on `controlDisplayName`) and show what to change: **expected** value vs **currently** deployed value. This is the actionable detail — surface it, don't stop at the ⚙ marker.

**Next-action suggestion (state-aware).** Choose the call-to-action from `Data.Summary.ClauseSummary`, evaluated IN THIS ORDER (first match wins — the cases overlap, so order matters) — NEVER suggest (re)applying a pack that is already enabled:
1. **All applied** (`PartiallyDeployedCount == 0 && NotDeployedCount == 0`): every clause fully deployed — render the [All settings applied](#all-settings-applied) block instead of the gap template below. Nothing to apply.
2. **Nothing applied yet** (`FullyDeployedCount == 0 && PartiallyDeployedCount == 0` — pack not enabled): the ONLY case where you suggest applying. Offer `'Apply ISO 42001 settings'`, `'Apply High impact ISO 42001 settings'`, or `'Apply only <specific area> settings'`.
3. **Already applied, gaps remain** (otherwise — pack enabled, `state enable` already ran, `PartiallyDeployedCount > 0 || NotDeployedCount > 0`): do NOT suggest reapplying the standard or applying a subset. Point the user at the residual settings that need attention:
   - If any ⚙ `manual` controls exist: `'Configure the manual ISO 42001 settings'` — the ⚙ items with expected/actual in DETAILS ARE the to-do list. When the user accepts, hand off to the AOps plugin to update the existing pack policy — see [Configuring manual settings (AOps handoff)](#configuring-manual-settings--aops-handoff).
   - Any remaining ✗ `not-deployed` settings (and the case where there are NO ⚙ manual settings, only ✗): their product's policy isn't fully in place — tell the user to configure those settings in the product's own settings; reapplying the pack will not set them. Never present an empty "configure the manual settings" prompt when there are zero ⚙ items.

Never render product coverage — product grain is internal only.

**Graceful degrade:** if `Clauses[].controls` is absent (older CLI/server), fall back to the clause-grain view (`Clauses[].Status` fully/partially/not-deployed) and add a one-line note that per-setting detail needs an updated `uip` CLI. Never fabricate per-setting state.

Progress bar: 5 cells scaled to the deployed ratio — filled = `round(deployedControlCount / checkableControlCount × 5)` `▓`, remainder `░` (2/5 → `▓▓░░░`, 1/4 → `▓░░░░`, 4/4 → `▓▓▓▓▓`).

A setting is a **gap** when its `status != "deployed"` — i.e. both `not-deployed` (✗) and `manual` (⚙) count as gaps in the impact tallies and per-clause counts (a manual setting is not yet applied).

**Biggest risk area:** clause with the most High-impact gap controls (`impact == "High" && status != "deployed"`).
**Quickest win:** clause with the fewest gap controls (`status != "deployed"`) AND at least one is High impact.

Terminology rules:
- Use "settings" NOT "controls" in output
- Use plain-English clause names (from `clauses[].clauseName`) in headlines; clause IDs (e.g. A.6.2.8) as secondary reference in DETAILS only
- Use `controls[].controlDisplayName` as setting name, NOT product identifiers
- **NEVER write raw API status strings** — product `in-place`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `deployed`/`not-deployed`/`manual` — in user-facing display output (posture_plan.txt, chat responses, report summaries) — translate EVERY occurrence before writing
  - `"in-place"` → **Applied** (or ✓)
  - `"new"` → **Not Applied** (or ✗)
- **`coverage.json` is an internal session file** — save it as the raw `--output json` CLI response. Raw API values (`"in-place"`, `"new"`) are CORRECT and expected in this file. Do NOT translate status values when writing coverage.json.
- Never say "compliance gaps" — say "settings not yet configured"
- Never claim the tenant IS compliant

Render this gap template ONLY for cases 2 and 3 above (gaps remain). For case 1 (all applied) use the [All settings applied](#all-settings-applied) block instead — never reach this template with zero gaps.

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

<call-to-action per Next-action suggestion (this template only renders for cases 2/3): case 2 (nothing applied) → 'Apply ISO 42001 settings' / 'Apply High impact ISO 42001 settings' / 'Apply only <specific area> settings'; case 3 (enabled, gaps remain) → 'Configure the manual ISO 42001 settings'>

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
Next action (state-aware — see "Next-action suggestion"):
  · pack already enabled / partial gaps → 'Configure the manual ISO 42001 settings'   ·   'What does [clause name] require?'
  · nothing applied yet                 → 'Apply ISO 42001 settings' (y/n)   ·   'Just fix the High impact gaps'   ·   'Apply only <specific area> settings'
```

## All settings applied

If `Summary.ClauseSummary.PartiallyDeployedCount == 0 && NotDeployedCount == 0` (every clause fully deployed). Do NOT use `Summary.NewCount == 0` for this — with disjoint product counts a `needs-manual-config` product leaves `NewCount == 0` while settings still need manual setup:

```
All ISO 42001 recommended settings are Applied on <tenantName>.
<fullyDeployedCount> / <totalClauses> clauses fully deployed  ·  all settings Applied ✓

To remove them: 'Remove ISO 42001 settings'
```

Do NOT call `state enable` in this case.

## Configuring manual settings — AOps handoff

When the user accepts `'Configure the manual ISO 42001 settings'` (offered ONLY in the already-applied / partial state), hand off to this skill's AOps policy mechanic to update the EXISTING deployed policy. Do NOT re-enable the pack (`state enable`) and do NOT create a new policy — the pack already deployed one policy per product; a `manual` setting is just an org-specific formData key on that policy that automation could not fill. This mutation happens on the **AOps branch** (Critical Rule 3: one branch per mutation).

Each ⚙ setting is a `Data.Clauses[].manualConfigChecks[]` entry: `{ productIdentifier, key, expected, actual }`. Group them by `productIdentifier` — one policy per product, updated once.

Per product:
1. **Resolve the pack's policy id for the product.** `uip gov aops-policy deployment tenant get <TENANT_ID> --output json` → the `TenantPolicies[]` entry whose `ProductIdentifier` matches → its `PolicyIdentifier`. Cross-check it belongs to the pack against `state get tenant <TENANT_ID> <packId>` `Policies[].ExternalPolicyId`.
2. **Collect the org-specific value(s).** `expected` is a predicate (`{eq}`/`{gte}`/`{lte}`/`{contains}`); `manual` means the concrete value is org-specific (an allowlist, a package set, a threshold). Ask the user, and confirm the value satisfies `expected`.
3. **Update via the AOps plugin.** Follow [`../../aops-policy/aops-policy-manage-guide.md`](../../aops-policy/aops-policy-manage-guide.md): `aops-policy get <PolicyIdentifier>` → set each `key` in the returned formData to the collected value (build `--input` per [`../../aops-policy/configure-aops-policy-data-guide.md`](../../aops-policy/configure-aops-policy-data-guide.md)) → `aops-policy update` (**full replacement** — pass `--identifier <PolicyIdentifier>` plus every existing field back: `--name`, `--product-name`, `--description`, `--priority`, `--availability`, `--input` — omitting any clears it, per [`../../aops-policy/aops-policy-commands.md`](../../aops-policy/aops-policy-commands.md)). Never call `state enable`.
4. **Receipt + confirm.** Show a post-update receipt (Critical Rule 6), then re-run coverage; each fixed ⚙ setting should flip to ✓ (`controls[].status == "deployed"`).

Graceful degrade: if the AOps guides are unavailable, present the ⚙ list (setting, expected, current) and tell the user to set each value on the product's deployed policy in Automation Ops — never leave the manual settings as a dead-end suggestion.

### User-facing output (shape to follow)

Ask for values — known recommended value → offer to confirm it; org-specific gate → ask for the value. Never show policy ids or CLI:

```
3 settings need a value only you can set — I'll update the existing ISO 42001 policies in place.

1. Studio Web — Publish Outside Personal Workspace  (AI system deployment · High)
   Recommended: Development only · currently: Anywhere        → set to recommended? (yes / other)
2. Workflow Analyzer — Required Packages  (Processes for responsible AI design · High)
   Requires a mandated package list · currently: not set      → which packages?
3. Model Governance — Third-Party AI Providers Allowlist  (Suppliers · Medium)
   Requires approved providers only · currently: All providers → which providers?
```

Review gate before applying:

```
Will change (3 existing policies — no re-apply of the standard):
  Studio Web — Publish Outside Personal Workspace       → Development only
  Workflow Analyzer — Required Packages                 → <user packages>
  Model Governance — Third-Party AI Providers Allowlist → <user providers>
Proceed? (y/n)
```

Receipt + re-check after applying:

```
✅ 3 settings configured on <tenantName> · by you · <date>
Clauses fully covered: 9 / 15  (was 7)  ·  Suppliers 2/5 → 3/5
Remaining gaps: ask 'What does [clause] require?'
```

## Never cache

Always run fresh before presenting a posture plan. Coverage reflects live tenant state.

## Anti-patterns

- **Writing raw API status strings in user-facing display output** — product `in-place`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `deployed`/`not-deployed`/`manual` — must NEVER appear in user-facing display output (posture_plan.txt, chat responses, report summaries). Translate every status before writing. `coverage.json` is an internal session file — raw API values are correct there.
- **Partial translation** — translating the summary section but leaving raw values in the DETAILS or verification section. ALL sections must use the translated labels.
- **Quoting API values for context** — avoid notes like "Status is still 'new'". Rephrase to "AI Trust Layer shows as Not Applied" instead.
- **Deriving per-setting state from product status** — use `Clauses[].controls[].status` (`deployed`/`not-deployed`/`manual`). Never mark a setting Applied because its product is `in-place`.

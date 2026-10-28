# Coverage — Posture Analysis

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Compares the compliance standard's recommended settings against what is currently deployed on the tenant. Does NOT require the standard to be enabled first. Does NOT certify compliance — it identifies which settings from the standard are not yet configured.

`<packId>` / `<packName>` below = the standard being checked, resolved via [`../catalog/impl.md` § Pack ID lookup](../catalog/impl.md#pack-id-lookup). Coverage is per standard — if the user asked about posture without naming one, resolve it there first; do not default to whichever pack is listed first.

## Command

**Pre-condition:** `$SESSION_TEMP/catalog.json` must exist — run `catalog get` first (see `catalog/impl.md`). The coverage response does NOT carry display names for clauses (`ClauseName` comes back null) — the plain-English clause names the template requires come from joining coverage `Clauses[].ClauseId` to catalog `Clauses[].ClauseId` → `ClauseName` in `catalog.json`.

```bash
# Read the session dir written by catalog get — never create a new one here.
SESSION_TEMP=$(cat "$HOME/.uipath-compliance-current-session")
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state coverage tenant $TENANT_ID <packId> --output json \
  > "$SESSION_TEMP/coverage.json"

# Whether the pack is APPLIED is a separate question from what is covered.
# Coverage cannot answer it (it runs pack-on or pack-off) — this can.
# A known pack that was never applied returns 200 with Active: false.
# A 404 means the packId itself is not usable (unknown, or a catalog stub
# with no bundle) — NOT "not applied"; check it against catalog list.
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json \
  > "$SESSION_TEMP/state.json"
```

```powershell
# Windows PowerShell
$tmpDir = (Get-Content "$env:TEMP\uipath-compliance-current-session.txt" -Raw).Trim()
$tenantId = (Select-String '^UIPATH_TENANT_ID=(.+)' "$env:USERPROFILE\.uipath\.auth").Matches[0].Groups[1].Value
uip gov compliance-packs state coverage tenant $tenantId <packId> --output json |
  Set-Content "$tmpDir\coverage.json"

# Applied-or-not is a separate question — coverage cannot answer it.
uip gov compliance-packs state get tenant $tenantId <packId> --output json |
  Set-Content "$tmpDir\state.json"
```

## Parse the response

CLI output is **PascalCase**. Field names below are exactly as returned by `state coverage`.

`Data.DeploymentPolicies[].Status` (product-grain; INTERNAL — never rendered to the user, never projected onto settings). Four disjoint values:
- `"in-place"` — product fully satisfied · `"needs-manual-config"` — deployed but ≥1 control still needs manual setup · `"unverifiable"` — pack active but the product's policy is missing (deleted out-of-band), so nothing can be checked · `"new"` — none of the standard's settings are in place for this product
- `"new"` does NOT mean "no policy". A product lands in `NewCount` either because nothing was ever deployed OR because a live policy has had **every** one of its controls changed away from the standard. In the second case the policy still exists, `PolicyId` is present, and `DriftedControls[]` is populated — the remedy is `restore`, not apply.
- INTERNAL only; the user-facing posture is driven entirely by clauses + per-setting `Controls[]`. Do NOT gate the all-applied case on `Summary.NewCount == 0` — with the disjoint counts a `needs-manual-config` product leaves `NewCount == 0` yet the pack is not fully applied.
- `PolicyId` may be **absent entirely** (not null) when the product has no live policy. Do not infer its presence from `Status` — a fully-drifted product is `"new"` and still carries a `PolicyId`. Any step that resolves a `PolicyId` must check for the key and skip the product when it is missing.

`Data.Clauses[].Status` (per-control rollup):
- `"fully-deployed"` — every checkable setting satisfied — display as **Applied** (✓)
- `"partially-deployed"` — some but not all satisfied, OR nothing satisfied yet but ⚙ manual configuration is pending — display as **Partially Applied** (◐). A clause showing `0/<n>` with this status is expected, not a data error: pending-manual controls keep a clause out of `"not-deployed"`.
- `"not-deployed"` — none satisfied — display as **Not Applied** (✗)

`Data.Clauses[].Controls[]` (per-setting; present on updated CLI) — the truthful per-setting view:
- `ControlDisplayName` — setting name
- `ControlId` — stable id; the join key to `DriftedControls[]`
- `ProductIdentifier` — owning product
- `Impact` — `"High"` / `"Medium"` / `"Low"`
- `RecommendedSetting` — the recommended value
- `Status` — `"deployed"` (✓ Applied) / `"not-deployed"` (✗ Not Applied) / `"manual"` (⚙ Needs Manual Configuration — admin must set a value)

`Data.Clauses[].ManualConfigChecks[]` (the actionable "what to set" detail behind every `Status == "manual"` control) — join to a `Controls[]` entry by `ControlId`, falling back to `ControlDisplayName` when `ControlId` is absent (pre-2.1.0 bundles omit it; the display name is always present):
- `ControlDisplayName` / `ControlId` — the setting
- `ProductIdentifier` — owning product
- `Key` — the policy formData key to set
- `Expected` — the value the standard requires, as a predicate object with a **PascalCase** operator key (`{Eq}` / `{Gte}` / `{Lte}` / `{Contains}`); render human-readable (`{Gte: 30}` → "at least 30", `{Eq: true}` → "Enabled")
  - **Only the operator key is really PascalCase.** Keys *inside* a `{Contains: [...]}` entry are policy formData keys, which the CLI has also PascalCased on the way out — the real ones are kebab-case (`CodeEmbeddedRulesConfigRules` is really `code-embedded-rules-config-rules`). Read them for display only. When writing a value back, take the key from `Key` and the shape from the policy's own `aops-policy get` output — never from these.
- `Actual` — the value currently deployed on the tenant (absent / `null` when unset)

`Data.DeploymentPolicies[].DriftedControls[]` — settings that WERE applied by the standard and have since been changed away from it. This is the only field that separates drift from never-applied: a drifted control shows up in `Clauses[].Controls[]` as `Status: "not-deployed"`, identical to one that was never deployed. Join by `ControlId`; when `ControlId` is absent (packs authored before bundle schema 2.1.0 omit it), fall back to `ControlDisplayName` — the server dedups drift rows by the same key.
- `ControlId` / `ControlDisplayName` — the setting
- `PackValueDisplay` — the value the standard expects, already display-ready
- `ImpactedClauseId` — the clause whose rollup this drift pulled down
- `UnmetSettings[]` — `{ Key, Expected, Actual }`, same predicate shape as `ManualConfigChecks` above

`Data.Summary` (PRODUCT-grain counts + a clause rollup — read these directly, do NOT recompute):
- `DeploymentPolicyCount` — total products · four **disjoint** product tallies that sum to it: `InPlaceCount` (fully applied) + `NeedsManualConfigCount` (deployed, manual setup pending) + `UnverifiableCount` (policy missing, nothing checkable) + `NewCount` (nothing deployed). `NewCount == 0` does NOT mean fully applied — needs-manual-config and unverifiable products aren't counted in it. Omitting `UnverifiableCount` makes the tallies not add up.
- `DriftedControlCount` — total drifted settings across all products. `> 0` is the signal to offer `restore` (see next-action case 3a).
- `ClauseSummary.FullyDeployedCount` / `PartiallyDeployedCount` / `NotDeployedCount` — the clause rollup driving the SUMMARY counts and the all-applied check

`Data.PackId` / `ScopeLevel` / `ScopeTargetId` — identify the pack + tenant scope (internal; the user sees the tenant NAME from auth context, not the id).

## Posture plan presentation

Build the per-setting table directly from `coverage.Data.Clauses[].Controls[]` — do NOT derive setting state from product status:
- ✓ Applied — `Control.Status == "deployed"`
- ✗ Not Applied — `Control.Status == "not-deployed"` AND its `ControlId` is NOT in any `DriftedControls[]`
- ⟳ Changed Since Applied — `Control.Status == "not-deployed"` AND its `ControlId` IS in some `DeploymentPolicies[].DriftedControls[]`
- ⚙ Needs Manual Configuration — `Control.Status == "manual"`

The ⟳ split matters: ✗ and ⟳ look identical in `Status`, but they have different fixes. ✗ needs the setting configured in the product; ⟳ is undone by one `state restore`. Never recommend hand-editing a ⟳ setting.

Per-clause counts come from the clause's own `Controls[]` (or `DeployedControlCount` / `CheckableControlCount`). The SUMMARY clause counts come from `Data.Summary.ClauseSummary.*` directly.

For each ⚙ `manual` control, look up its `Data.Clauses[].ManualConfigChecks[]` entry (match on `ControlId`, else `ControlDisplayName`) and show what to change: **`Expected`** value vs **`Actual`** deployed value. This is the actionable detail — surface it, don't stop at the ⚙ marker.

For each ⟳ drifted control, show the same expected-vs-actual line from its `UnmetSettings[]` (or `PackValueDisplay` when you only need the expected side).

**Next-action suggestion (state-aware).** Two INDEPENDENT axes decide the call-to-action. Read each from its own source — never derive one from the other:

- **Is the pack applied?** — `state get` → `Data.Active`. This is the ONLY authority.
- **What is covered?** — the coverage counts. Posture only.

Coverage compares the pack against **whatever policies the tenant already has**, applied or not (`Does NOT require the pack to be enabled`). So coverage numbers cannot tell you whether the pack is on, in either direction:
- Pack ON, every setting changed away → every product `new`, every clause `not-deployed`. Reads as "never applied", but the remedy is `restore`, and suggesting apply would run `state enable` on an enabled pack.
- Pack OFF, but the tenant's own pre-existing policies happen to satisfy part of the standard → `in-place` / `needs-manual-config` products and fully/partially-deployed clauses. Reads as "already applied", and the user asking to apply the standard gets told not to.

`DriftedControlCount > 0` and any `unverifiable` product each prove the pack IS active (both only exist on an active pack), but their absence proves nothing. Call `state get` — do not guess.

Evaluate IN THIS ORDER (first match wins):

1. **Pack NOT active** (`Data.Active == false`; a never-applied known pack returns 200 with `Active: false`, not a 404 — a 404 from `state get` means the packId itself is not usable, so re-check it against `catalog list` and stop) — the pack is not applied, whatever the coverage numbers say. Offer `'Apply <packName> settings'`, `'Apply High impact <packName> settings'`, or `'Apply only <specific area> settings'`. If coverage already shows partial or full clause coverage, that is the tenant's own policies coinciding with the standard, NOT the pack — say so plainly ("some of these settings already match what the standard recommends; applying it will manage them going forward") and still offer to apply. Never suppress the apply offer because coverage looks good.
2. **Pack active, everything covered** (`Data.Active == true` and `PartiallyDeployedCount == 0 && NotDeployedCount == 0`): render the [All settings applied](#all-settings-applied) block. Nothing to apply.
3. **Pack active, gaps remain** (`Data.Active == true`, otherwise): do NOT suggest reapplying the standard or applying a subset. Point the user at the residual settings, checking the drift case FIRST:
   - **3a. If `Summary.DriftedControlCount > 0` OR any product is `unverifiable`:** offer `'Reset the changed <packName> settings back to the standard'` — the ⟳ items ARE that list, and restore also RECREATES the missing policy behind any Cannot-Be-Checked product (it resets every live pack policy to the bundle's suggested values and recreates deleted ones). Hand off to [`../restore/impl.md`](../restore/impl.md), which owns the confirmation gate — including the warning that restore also resets any ⚙ manual values an admin has already configured. Do NOT tell the user to hand-edit a ⟳ setting, and do NOT route ⟳ items into the AOps handoff below — that is the remedy for ⚙, not for drift.
   - If any ⚙ `manual` controls exist: `'Configure the manual <packName> settings'` — the ⚙ items with expected/actual in DETAILS ARE the to-do list. When the user accepts, hand off to the AOps plugin to update the existing pack policy — see [Configuring manual settings (AOps handoff)](#configuring-manual-settings--aops-handoff). When 3a also applies, sequence restore FIRST, then the manual values — restore would overwrite manual values configured before it.
   - On an active pack there is no third remedy: a plain ✗ (not-deployed, not drifted) only occurs under a Cannot-Be-Checked product whose policy is missing — restore recreates it (3a). Never tell the user to configure an active pack's settings in the product's own UI. (Exception: an older server that doesn't return drift fields at all — then ✗ under an active pack is indistinguishable drift, and restore is still the remedy.)
   - Fallback, if that ever fails to hold — ✗ settings on an active pack with no drift and no Cannot-Be-Checked product: do NOT leave them unexplained. Offer restore anyway (it re-asserts the standard's values on every live policy) and say the settings are not in place for a reason the posture data doesn't explain.

   These are not exclusive — a tenant can have ⟳, ⚙, and ✗ at once. Offer each that applies, drift first.

   **Degraded-response check:** the server computes drift and `unverifiable` only when its own internal pack-state read succeeds; on failure it silently returns coverage WITHOUT them (products with deleted policies then show as `new`). The tell: on an active pack, a `new` product ALWAYS carries drifted controls — so `Active == true` plus a `new` product with `DriftedControlCount == 0` means the response is degraded. Re-run coverage before acting on it.

**If `state get` fails** (401 / 5xx, so `Active` is unknown): do NOT fall back to guessing from coverage counts. Present the posture, say the pack's applied state could not be read, and offer both directions rather than picking one.

Never render product coverage — product grain is internal only.

**Graceful degrade:** if `Clauses[].Controls[]` is missing across every clause (older CLI/server; note a single clause with an empty `Controls[]` is normal — surface-only clauses have no checkable controls), fall back to the clause-grain view (`Clauses[].Status` fully/partially/not-deployed) and add a one-line note that per-setting detail needs an updated `uip` CLI. Never fabricate per-setting state.

Progress bar: 5 cells scaled to the deployed ratio — filled = `round(DeployedControlCount / CheckableControlCount × 5)` `▓`, remainder `░` (2/5 → `▓▓░░░`, 1/4 → `▓░░░░`, 4/4 → `▓▓▓▓▓`).

A setting is a **gap** when its `Status != "deployed"` — i.e. `not-deployed` (✗), drifted (⟳) and `manual` (⚙) all count as gaps in the impact tallies and per-clause counts (a manual setting is not yet applied).

**Biggest risk area:** clause with the most High-impact gap controls (`Impact == "High" && Status != "deployed"`). Ties: the clause with the LOWER deployed ratio (`DeployedControlCount / CheckableControlCount` — furthest from done); still tied, the first in the order the API returned.
**Quickest win:** clause with the fewest gap controls (`Status != "deployed"`) AND at least one is High impact. Ties: the clause with the HIGHER deployed ratio (closest to done); still tied, the first in the order the API returned.
The two tie-breaks pull opposite ways on purpose — a single-clause tie must not name the same clause in both rows. If it still does (one clause is genuinely both), leave Quickest win blank rather than repeat it.

Terminology rules:
- Use "settings" NOT "controls" in output
- Use plain-English clause names (joined from `catalog.json` by `ClauseId` — see the pre-condition; coverage's own `ClauseName` is null) in headlines; clause IDs (e.g. A.6.2.8) as secondary reference in DETAILS only
- Use `Controls[].ControlDisplayName` as setting name, NOT product identifiers
- **NEVER write raw API status strings** — product `in-place`/`needs-manual-config`/`unverifiable`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `deployed`/`not-deployed`/`manual` — in user-facing display output (posture_plan.txt, chat responses, report summaries) — translate EVERY occurrence before writing
  - `"in-place"` → **Applied** (or ✓)
  - `"new"` → **Not Applied** (or ✗)
  - `"unverifiable"` → **Cannot Be Checked** — the product's policy is missing, so say the settings can't be verified. Never report an unverifiable product as Applied.
  - a drifted setting → **Changed Since Applied** (or ⟳) — never "not deployed"
- **`coverage.json` is an internal session file** — save it as the raw `--output json` CLI response. Raw API values (`"in-place"`, `"new"`) are CORRECT and expected in this file. Do NOT translate status values when writing coverage.json.
- Never say "compliance gaps" — say "settings not yet configured"
- Never claim the tenant IS compliant

Render this gap template ONLY for cases 1 and 3 above (pack not applied, or applied with gaps). For case 2 (active and fully covered) use the [All settings applied](#all-settings-applied) block instead — never reach this template with zero gaps.

```
<packName> Posture — <tenantName>  ·  <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY
┌─────────────────────────┬──────────────────────────────────────┐
│ Overall coverage        │ <appliedControlCount> / <checkableControlCount> settings  (<pct>%)  │
│ Clauses fully covered   │ <clausesFullyDeployed> / <totalClauses>          │
│ Clauses with gaps       │ <clausesWithGaps> / <totalClauses>               │
├─────────────────────────┼──────────────────────────────────────┤
│ 🔴 High impact gaps     │ <highGapCount> settings across <highClauseCount> clauses  │
│ 🟡 Medium impact gaps   │ <medGapCount> settings across <medClauseCount> clauses    │
│ 🟢 Low impact gaps      │ <lowGapCount> settings across <lowClauseCount> clauses    │
├─────────────────────────┼──────────────────────────────────────┤
│ Biggest risk area       │ <clauseName with most High-impact gap settings>  │
│ Quickest win            │ <clauseName with fewest gaps AND ≥1 High setting>│
└─────────────────────────┴──────────────────────────────────────┘

<call-to-action per Next-action suggestion (this template renders for cases 1 and 3): case 1 (pack not applied) → 'Apply <packName> settings' / 'Apply High impact <packName> settings' / 'Apply only <specific area> settings'; case 3 (applied, gaps remain) → in order: 'Reset the changed <packName> settings back to the standard' (when ⟳ settings or a Cannot-Be-Checked product exist), then 'Configure the manual <packName> settings' (when ⚙ settings exist)>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Needs Configuration  (<N> of <total>)

  <clauseName>                                       <deployedControlCount>/<checkableControlCount> <bar>
  ┌───────────────────────────────────┬─────────────────────┬────────┐
  │ Setting                           │ Recommendation      │ Impact │
  ├───────────────────────────────────┼─────────────────────┼────────┤
  │ ✗ <ControlDisplayName>            │ <RecommendedSetting>│ High   │
  │ ⟳ <ControlDisplayName>            │ <RecommendedSetting>│ High   │
  │ ⚙ <ControlDisplayName>            │ <RecommendedSetting>│ Medium │
  │ ✓ <ControlDisplayName>            │ Applied             │ Medium │
  └───────────────────────────────────┴─────────────────────┴────────┘
  Marker = `Control.Status` + drift join: ✓ deployed · ✗ not-deployed · ⟳ not-deployed AND in `DriftedControls[]` · ⚙ manual
  For each ⚙ row, add a sub-line from `ManualConfigChecks` (`Expected` vs `Actual`):
    ⚙ <ControlDisplayName> — set to <Expected>; currently <Actual, or "not set">
  For each ⟳ row, add a sub-line from `DriftedControls[].UnmetSettings[]`:
    ⟳ <ControlDisplayName> — standard expects <PackValueDisplay>; currently <Actual>
  Rendering `Actual` — never print it verbatim, whatever its type:
  - Scalar tokens (`yes`/`no`/`true`/`false`/`null`): translate into the vocabulary of
    the displayed recommendation (expected `{Eq: "yes"}`, actual `"no"`, under "Display
    EDR Status: Enabled" → "currently Disabled").
  - Arrays and objects (common — an `Expected` of `{Contains: [...]}` has an `Actual`
    that is the whole live array, often hundreds of characters): NEVER print the
    structure. Say whether the required entry is present: "currently not configured"
    when the array has no matching entry, or "configured, but not with the value the
    standard requires" when other entries exist. Dumping the array violates the
    no-raw-output rule.
  - Can't tell: "currently not set to the recommended value". Never the raw token.
  The Recommendation column, and the expected side of BOTH ⚙ and ⟳ sub-lines, always
  show the editorial value (`RecommendedSetting` / `PackValueDisplay`), never the raw
  predicate — the predicate is for machine comparison; the two can differ in units
  (e.g. "Development only" vs `{Eq: true}`).

  [repeat per clause with gaps]

  When any product is Cannot Be Checked (unverifiable), add ONE note after the last
  clause block, naming the affected ✗ settings without exposing product status values:
  "Note: the ✗ settings above (<their display names or products>) sit behind a policy
  that is missing from the tenant, so they can't currently be verified. Resetting the
  standard recreates that policy with the recommended values."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Applied  (<N> of <total>)  ✓
┌────────────────────────────────────────┬──────────┐
│ Clause                                 │ Settings │
├────────────────────────────────────────┼──────────┤
│ <clauseName>                           │ X / X  ✓ │
└────────────────────────────────────────┴──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next action (state-aware — see "Next-action suggestion"):
  · any ⟳ settings or Cannot-Be-Checked → 'Reset the changed <packName> settings back to the standard'
  · Active == true, partial gaps        → 'Configure the manual <packName> settings'   ·   'What does [clause name] require?'
  · nothing applied yet                 → 'Apply <packName> settings' (y/n)   ·   'Just fix the High impact gaps'   ·   'Apply only <specific area> settings'
```

## All settings applied

Next-action case 2 only: `state get` says `Data.Active == true` **AND** `Summary.ClauseSummary.PartiallyDeployedCount == 0 && NotDeployedCount == 0` (every clause fully deployed). Do NOT use `Summary.NewCount == 0` for this — with disjoint product counts a `needs-manual-config` product leaves `NewCount == 0` while settings still need manual setup:

```
All <packName> recommended settings are Applied on <tenantName>.
<fullyDeployedCount> / <totalClauses> clauses fully deployed  ·  all settings Applied ✓

To remove them: 'Remove <packName> settings'
```

Do NOT call `state enable` in this case.

**The `Active` half is not optional.** With full clause coverage but `Active == false`, the tenant's own policies happen to match the standard — the pack is not managing anything. Use case 1 instead: say the settings already line up, and still offer to apply. Never print "To remove them" for a pack that was never applied — there is nothing to remove.

## Configuring manual settings — AOps handoff

When the user accepts `'Configure the manual <packName> settings'` (offered ONLY in the already-applied / partial state), hand off to this skill's AOps policy mechanic to update the EXISTING deployed policy. Do NOT re-enable the pack (`state enable`) and do NOT create a new policy — the pack already deployed one policy per product; a `manual` setting is just an org-specific formData key on that policy that automation could not fill. This mutation happens on the **AOps branch** (Critical Rule 3: one branch per mutation).

Each ⚙ setting is a `Data.Clauses[].ManualConfigChecks[]` entry: `{ ProductIdentifier, Key, Expected, Actual }`. Group them by `ProductIdentifier` — one policy per product, updated once.

Per product:
1. **Resolve the pack's policy id for the product.** `uip gov aops-policy deployment tenant get <TENANT_ID> --output json` → the `TenantPolicies[]` entry whose `ProductIdentifier` matches → its `PolicyIdentifier`. Cross-check it belongs to the pack against `state get tenant <TENANT_ID> <packId>` `Policies[].ExternalPolicyId`.
2. **Collect the org-specific value(s).** `Expected` is a predicate (`{Eq}`/`{Gte}`/`{Lte}`/`{Contains}`); `manual` means the concrete value is org-specific (an allowlist, a package set, a threshold). Ask the user, and confirm the value satisfies `Expected`. For a `{Contains: [...]}` predicate, compare against the live policy's own formData from step 3's `aops-policy get` — the keys inside the predicate entry are CLI-PascalCased formData keys, not the real ones (see the `Expected` note above), so building an entry from them writes keys the policy does not have.
3. **Update via the AOps plugin.** Follow [`../../aops-policy/aops-policy-manage-guide.md`](../../aops-policy/aops-policy-manage-guide.md): `aops-policy get <PolicyIdentifier>` → set each `Key` in the returned formData to the collected value (build `--input` per [`../../aops-policy/configure-aops-policy-data-guide.md`](../../aops-policy/configure-aops-policy-data-guide.md)) → `aops-policy update` (**full replacement** — pass `--identifier <PolicyIdentifier>` plus every existing field back: `--name`, `--product-name`, `--description`, `--priority`, `--availability`, `--input` — omitting any clears it, per [`../../aops-policy/aops-policy-commands.md`](../../aops-policy/aops-policy-commands.md)). Never call `state enable`.
4. **Receipt + confirm.** Show a post-update receipt (Critical Rule 6), then re-run coverage; each fixed ⚙ setting should flip to ✓ (`Controls[].Status == "deployed"`).

Graceful degrade: if the AOps guides are unavailable, present the ⚙ list (setting, expected, current) and tell the user to set each value on the product's deployed policy in Automation Ops — never leave the manual settings as a dead-end suggestion.

### User-facing output (shape to follow)

Ask for values — known recommended value → offer to confirm it; org-specific gate → ask for the value. Never show policy ids or CLI:

```
3 settings need a value only you can set — I'll update the existing <packName> policies in place.

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

- **Writing raw API status strings in user-facing display output** — product `in-place`/`needs-manual-config`/`unverifiable`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `deployed`/`not-deployed`/`manual` — must NEVER appear in user-facing display output (posture_plan.txt, chat responses, report summaries). Translate every status before writing. `coverage.json` is an internal session file — raw API values are correct there.
- **Partial translation** — translating the summary section but leaving raw values in the DETAILS or verification section. ALL sections must use the translated labels.
- **Quoting API values for context** — avoid notes like "Status is still 'new'". Rephrase to "AI Trust Layer shows as Not Applied" instead.
- **Deriving per-setting state from product status** — use `Clauses[].Controls[].Status` (`deployed`/`not-deployed`/`manual`). Never mark a setting Applied because its product is `in-place`.
- **Treating a drifted setting as never-applied** — telling the user to go configure a ⟳ setting in the product's own settings. It was applied and then changed; `state restore` puts it back. Always join `Controls[]` to `DriftedControls[]` (by `ControlId`, falling back to `ControlDisplayName`) before writing a remedy.
- **Sending the user to the product's own settings UI for an active pack's gaps** — on an active pack every gap routes to `restore` (⟳ drift and missing policies) or the AOps handoff (⚙ manual). Hand-editing product settings is never the remedy while the pack manages them.
- **Summing only three product counts** — `InPlaceCount + NeedsManualConfigCount + NewCount` does NOT equal `DeploymentPolicyCount` when any product is `unverifiable`. Read the counts; never recompute a total from a subset.
- **Reading `PolicyId` on every product** — it can be absent when there is no live policy. Check for the key; never infer its presence from `Status` (a fully-drifted product is `"new"` and does have one).
- **Inferring whether the pack is applied from coverage numbers** — the single most damaging mistake here, and it fails in both directions. Zero coverage can mean an enabled pack whose settings were all changed away (remedy: `restore`, not apply). Partial or full coverage can mean the tenant's own pre-existing policies coincide with the standard while the pack is off (so the apply offer must still be made). Coverage runs pack-on or pack-off by design — read `Data.Active` from `state get` and nothing else.
- **Suppressing the apply offer because coverage looks good** — a user asking to apply a standard on a tenant that merely happens to satisfy part of it must still be offered the apply. Coincidental coverage is not an applied pack.

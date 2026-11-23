# Coverage — Posture Analysis

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Compares the compliance standard's recommended settings against what is currently deployed on the tenant. Does NOT require the standard to be enabled first. Does NOT certify compliance — it identifies which settings from the standard are not yet configured.

`<packId>` / `<packName>` below = the standard being checked, resolved via [`../catalog/impl.md` § Pack ID lookup](../catalog/impl.md#pack-id-lookup). Coverage is per standard — if the user asked about posture without naming one, resolve it there first; do not default to whichever pack is listed first.

The output mirrors the Compliance Standards page in the UiPath admin portal: three requirement counts (**Not applied** / **Needs configuration** / **Applied**), a **Policy Status** panel per product, the requirements listed under those headings, and an **Outside platform scope** list. Before the standard is applied — or while it is active but not enforced — it also shows what applying or enforcing will do: settings that will still need configuration, conflicts with existing policies, and which policies will be created or updated.

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

# Are Enforce/Observe modes on for this org? Decides whether to show a mode
# and whether the admin can keep a conflicting value (see "Modes").
# A 404 (older server) means off.
uip gov compliance-packs state settings --output json > "$SESSION_TEMP/settings.json"
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

uip gov compliance-packs state settings --output json | Set-Content "$tmpDir\settings.json"
```

**Modes** — `settings.json` `Data.ModeSelectionEnabled`. `true` (**modes on**): the pack runs in Enforce or Observe; an Enforce apply takes the admin's choice per conflict (current or standard); Observe writes nothing to the tenant's policies. `false`, or a failed / 404 `state settings` (**modes off**): no mode is shown, and applying gives every conflict the standard's value. Everything mode-related below applies only with modes on.

## Parse the response

CLI output is **PascalCase**. Field names below are exactly as returned by `state coverage`.

`Data.DeploymentPolicies[].Status` (product-grain; INTERNAL — never rendered to the user, never projected onto settings). Four disjoint values:
- `"in-place"` — product fully satisfied · `"needs-manual-config"` — deployed but ≥1 control still needs manual setup · `"unverifiable"` — pack active but the product's policy is missing (deleted out-of-band), so nothing can be checked · `"new"` — none of the standard's settings are in place for this product
- `"new"` does NOT mean "no policy". A product lands in `NewCount` either because nothing was ever deployed OR because a live policy has had **every** one of its controls changed away from the standard. In the second case the policy still exists, `PolicyId` is present, and `DriftedControls[]` is populated — the remedy is `restore`, not apply.
- INTERNAL only; the user-facing posture is driven entirely by clauses + per-setting `Controls[]`. Do NOT gate the all-applied case on `Summary.NewCount == 0` — with the disjoint counts a `needs-manual-config` product leaves `NewCount == 0` yet the pack is not fully applied.
- `PolicyId` may be **absent entirely** (not null) when the product has no live policy. Do not infer its presence from `Status` — a fully-drifted product is `"new"` and still carries a `PolicyId`. Any step that resolves a `PolicyId` must check for the key and skip the product when it is missing.

`Data.Clauses[].Status` (per-control rollup). The admin portal calls a clause a **requirement** — use that word in output — and these are its three headings:
- `"fully-deployed"` — every checkable setting satisfied — display as **Applied** (✓)
- `"partially-deployed"` — some but not all satisfied, OR nothing satisfied yet but ⚙ manual configuration is pending — display as **Needs configuration** (⚙). A clause showing `0/<n>` with this status is expected, not a data error: pending-manual controls keep a clause out of `"not-deployed"`.
- `"not-deployed"` — none satisfied — display as **Not applied** (✗)

`Data.Clauses[].CheckableControlCount` → "N UiPath settings" on the requirement's line; `DeployedControlCount` → how many are applied. Clauses with no mapped setting are not in coverage at all: they are `catalog.json` `Data.UnsupportedClauses[]` (`ClauseId`, `ClauseName`, `Description`) → **Outside platform scope**.

`Data.Clauses[].Controls[]` (per-setting; present on updated CLI) — the truthful per-setting view:
- `ControlDisplayName` — setting name
- `ControlId` — stable id; the join key to `DriftedControls[]`
- `ProductIdentifier` — owning product
- `Impact` — `"High"` / `"Medium"` / `"Low"`
- `RecommendedSetting` — the recommended value
- `Status` — `"deployed"` (✓ Applied) / `"not-deployed"` (✗ Not Applied) / `"manual"` (⚙ Needs Manual Configuration — admin must set a value)
- `StatusAfterApply` — **before an apply that writes the pack's policies only** (pack not active, or active but not enforced): the setting's status right after applying/enforcing; `"manual"` = will still need configuration. Absent once the pack is enforced, or on an older server.
- `PackSettings[]` (`Key`, `PackValue`) — what applying writes for this setting.
- `EnforcedBy[]` — existing policies that already meet this setting ("Already enforced by <policy>"), each with `PolicyName`, `LicenseTypes[].DisplayName` and `Lines[]`.

`Data.Clauses[].ManualConfigControlCountAfterApply` — sent with `StatusAfterApply`: how many of the clause's settings will still need configuration right after applying/enforcing.

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
- `Lines[]` — the same failing settings as display-ready text (`Current` = now, `Recommended` = the standard's value). Prefer them over `UnmetSettings[]` when present; follow the [line rules](#line-rules).

`Data.DeploymentPolicies[].Policies[]` — every live policy of the product in the license types the pack deploys to (one per license-type group): `PolicyId`, `PolicyName` (the live Aops name, which can carry a suffix such as "(12)"), `LicenseTypes[].DisplayName` (e.g. "RPA Developer"), its own `Status` and `DriftedControls[]`. Empty when the product has no live policy. For the **card title** use `catalog.json` `Data.DeploymentPolicies[].PolicyName` (join by `ProductIdentifier`), with `ProductDisplayName` for the "<ProductDisplayName> Policy" subtitle — never the live name.

**Conflicts** — existing policy values that applying/enforcing would change:
- `Data.ConflictStatus`: `"evaluated"` (`ConflictCount` can be trusted, may be 0) · `"unavailable"` (could not be checked — do not offer apply) · `"not-applicable"` (nothing to resolve: not tenant scope, a pack without values, or — modes off — a pack already enforced; say nothing about conflicts). An active pack in Observe or with no mode chosen still returns `"evaluated"`: its conflicts describe what enforcing would change. With modes on, a pack **already in Enforce** also returns `"evaluated"`: each setting changed since the apply (drift) is a conflict, and enforcing again with the admin's choices corrects it.
- `Data.Summary.ConflictCount` — total. `Data.Clauses[].ConflictCount` / `Conflicts[]` — per clause; a setting under several clauses is listed once, under the first.
- Each conflict: `ConflictId` (one per product and setting — sent back with the admin's choice on enable; internal, never shown), `ControlDisplayName`, `ProductIdentifier`, `PackValueDisplay`, and `Policies[]` — the existing policies that would change, each with `PolicyId`, `PolicyName`, `LicenseTypes[]` (`Identifier` — sent back for a choice per license type — and `DisplayName`) and `Lines[]`.
- `Settings[].CurrentValues[].OwnerPackIds` — other active, enforced standards whose policy holds that value. Name them (catalog names): `keep` keeps their value; `pack` writes this standard's, and their setting then shows as changed.
- A conflicting setting also shows as `Status: "not-deployed"` in `Controls[]`. Its remedy is applying/enforcing the standard, not restore and not the product UI.

**Apply plan** — `Data.ApplyPlan[]`, before an enforce apply only (absent otherwise): one entry per product and license type, `Action`: `"new"` (a new policy, named `PolicyName`; when `SourcePolicyId` is set it starts from that existing policy, `SourcePolicyName`, which is not changed) · `"update"` (a policy the standard created earlier, `PolicyName`, written in place — it can exist without being deployed, e.g. after the standard was turned off, so never call it one of the tenant's deployed policies). An older server sends `"create"`, `"copy"` or `"split"`: all three mean `"new"`. "Will be created" = every entry that is not `update`; "will be updated" = `update`. Count **entries, not products**: there is one entry per product and license type, so a product deployed to two license types (e.g. RPA Developer and Automation Developer) counts twice. The two numbers must add up to `ApplyPlan.length`.

### Line rules

`Lines[]` (conflicts, drift, enforced-by) carry `Key`, `Setting`, `Current`, `Recommended`, `IsMet`. `Current` / `Recommended` are display-ready; show them verbatim. `Setting` is the Policy Library label when one exists, otherwise the server falls back to the raw key:
- **Never print a raw key.** When a line's `Setting` equals its `Key`, don't show it. Group such lines under the setting's `ControlDisplayName` by change: `<n> settings, <Current values joined by "/"> → <Recommended>` (e.g. `Agent Guardrail — Prompt Injection Prevention: 3 settings, Not set/Disabled → Enabled`). A single unlabelled line becomes `<ControlDisplayName>: <Current> → <Recommended>`. Labelled lines show as `<Setting>: <Current> → <Recommended>`.
- **Every distinct change must appear.** Group only lines with the same `Recommended`; a different kind of change (e.g. `Both → Pre`, or a list value) gets its own line. Before printing, check that every `Lines[]` entry is covered by exactly one printed line.

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
- **Is it enforced?** (modes on only — with modes off there is no mode: skip this axis, case 3·0 and the mode in POLICY STATUS) — `state get` → `Data.Mode`, read only when `Active == true`: `"enforce"` → **Enforced** · `"audit"` → **Observe** · null or absent → **Mode not chosen** (runs as Observe until a mode is chosen). An active pack that is not enforced has live policies, but the runtime only simulates, and coverage still describes an enforce apply (`ConflictStatus`, `Conflicts[]`, `StatusAfterApply`, `ApplyPlan`). Never label it Enforced.
- **What is covered?** — the coverage counts. Posture only.

Coverage compares the pack against **whatever policies the tenant already has**, applied or not (`Does NOT require the pack to be enabled`). So coverage numbers cannot tell you whether the pack is on, in either direction:
- Pack ON, every setting changed away → every product `new`, every clause `not-deployed`. Reads as "never applied", but the remedy is `restore`, and suggesting apply would run `state enable` on an enabled pack.
- Pack OFF, but the tenant's own pre-existing policies happen to satisfy part of the standard → `in-place` / `needs-manual-config` products and fully/partially-deployed clauses. Reads as "already applied", and the user asking to apply the standard gets told not to.

`DriftedControlCount > 0` and any `unverifiable` product each prove the pack IS active (both only exist on an active pack), but their absence proves nothing. Call `state get` — do not guess.

Evaluate IN THIS ORDER (first match wins):

1. **Pack NOT active** (`Data.Active == false`; a never-applied known pack returns 200 with `Active: false`, not a 404 — a 404 from `state get` means the packId itself is not usable, so re-check it against `catalog list` and stop) — the pack is not applied, whatever the coverage numbers say. Offer `'Apply <packName> settings'`, `'Apply High impact <packName> settings'`, or `'Apply only <specific area> settings'`. If coverage already shows partial or full clause coverage, that is the tenant's own policies coinciding with the standard, NOT the pack — say so plainly ("some of these settings already match what the standard recommends; applying it will manage them going forward") and still offer to apply. Never suppress the apply offer because coverage looks good. Render the [If you apply](#if-you-apply--if-you-enforce) block with it. When `ConflictStatus == "unavailable"`, do NOT offer to apply in this run: show the `CONFLICTS NOT CHECKED` banner from [Conflicts with your existing policies](#conflicts-with-your-existing-policies).
2. **Pack active, everything covered** (`Data.Active == true` and `PartiallyDeployedCount == 0 && NotDeployedCount == 0`): render the [All settings applied](#all-settings-applied) block. Nothing to apply. If the pack is not enforced, add the [If you enforce](#if-you-apply--if-you-enforce) block and the enforce call-to-action from case 3.
3. **Pack active, gaps remain** (`Data.Active == true`, otherwise): do NOT suggest reapplying the standard or applying a subset. Point the user at the residual settings, checking the enforce and drift cases FIRST:
   - **3·0. If the pack is not enforced** (modes on, `Mode` is `"audit"`, null or absent): render the [If you enforce](#if-you-apply--if-you-enforce) block, and offer first: `'Enforce <packName>'`. On yes, hand off to [`../full-apply/impl.md` § Modes on](../full-apply/impl.md#modes-on) — it asks the mode and current or standard for every conflict. Every ✗ setting that is in `Conflicts[]` is covered by this offer. Do NOT route a conflict to restore or to the product UI.
   - **3a′. Modes on and the pack is Enforced, with conflicts** (`ConflictStatus == "evaluated"`, `ConflictCount > 0`): the conflicts are the drifted settings. Offer `'Correct the changed <packName> settings'` and hand off to [`../full-apply/impl.md` § Modes on](../full-apply/impl.md#modes-on) (Enforce again): for each one the admin chooses `pack` (put the standard's value back) or `keep` (accept the change). Settings kept on an earlier apply come back as conflicts too — say so. Use 3a for a Cannot-Be-Checked product.
   - **3a. If `Summary.DriftedControlCount > 0` OR any product is `unverifiable`** (and 3a′ does not cover it): `'Reset the changed <packName> settings back to the standard'` — the ⟳ items ARE that list, and restore also RECREATES the missing policy behind any Cannot-Be-Checked product (it resets every live pack policy to the bundle's suggested values and recreates deleted ones). Hand off to [`../restore/impl.md`](../restore/impl.md), which owns the confirmation gate — including the warning that restore also resets any ⚙ manual values an admin has already configured. Do NOT tell the user to hand-edit a ⟳ setting, and do NOT route ⟳ items into the AOps handoff below — that is the remedy for ⚙, not for drift.
   - If any ⚙ `manual` controls exist: `'Configure the manual <packName> settings'` — the ⚙ items with expected/actual in DETAILS ARE the to-do list. When the user accepts, hand off to the AOps plugin to update the existing pack policy — see [Configuring manual settings (AOps handoff)](#configuring-manual-settings--aops-handoff). When 3a also applies, sequence restore FIRST, then the manual values — restore would overwrite manual values configured before it.
   - On an active pack there is no third remedy: a plain ✗ (not-deployed, not drifted, not a conflict) only occurs under a Cannot-Be-Checked product whose policy is missing — restore recreates it (3a). Never tell the user to configure an active pack's settings in the product's own UI. (Exception: an older server that doesn't return drift fields at all — then ✗ under an active pack is indistinguishable drift, and restore is still the remedy.)
   - Fallback, if that ever fails to hold — ✗ settings on an active pack with no drift, no conflict and no Cannot-Be-Checked product: do NOT leave them unexplained. Offer restore anyway (it re-asserts the standard's values on every live policy) and say the settings are not in place for a reason the posture data doesn't explain.

   These are not exclusive — a tenant can have ⟳, ⚙, and ✗ at once. Offer each that applies: enforce first (3·0), then drift, then manual.

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
- Use "settings" NOT "controls", and "requirements" for clauses, in output
- Use plain-English clause names (joined from `catalog.json` by `ClauseId` — see the pre-condition; coverage's own `ClauseName` is null) in headlines; clause IDs (e.g. A.6.2.8) as secondary reference
- Use `Controls[].ControlDisplayName` as setting name, NOT product identifiers; use the catalog `PolicyName` / `ProductDisplayName` for policies, never product identifiers, policy ids or live policy names as titles
- Mode words: **Enforced**, **Observe**, **Mode not chosen**. Policy badges: **Stable**, **N drifted**, **Cannot Be Checked**
- **NEVER write raw API status strings** — product `in-place`/`needs-manual-config`/`unverifiable`/`new`; clause `fully-deployed`/`partially-deployed`/`not-deployed`; control `deployed`/`not-deployed`/`manual`; `ConflictStatus` `evaluated`/`unavailable`/`not-applicable`; `ApplyPlan` `create`/`copy`/`update`/`split`; mode `enforce`/`audit` — in user-facing display output (posture_plan.txt, chat responses, report summaries) — translate EVERY occurrence before writing
  - `"in-place"` → **Applied** (or ✓)
  - `"new"` → **Not Applied** (or ✗)
  - `"unverifiable"` → **Cannot Be Checked** — the product's policy is missing, so say the settings can't be verified. Never report an unverifiable product as Applied.
  - a drifted setting → **Changed Since Applied** (or ⟳) — never "not deployed"
- **`coverage.json` is an internal session file** — save it as the raw `--output json` CLI response. Raw API values (`"in-place"`, `"new"`) are CORRECT and expected in this file. Do NOT translate status values when writing coverage.json.
- Never say "compliance gaps" — say "settings not yet configured"
- Never claim the tenant IS compliant

**How to print it.** Output the template below as plain monospace text inside one fenced code block, filled in, in this section order — not a prose or bullet paraphrase of it. Never use HTML tags (`<details>`, `<summary>`, `<br>`, …): the CLI terminal shows them as raw text, and nothing collapses. Long sections are printed in full, never hidden. The conflict banner is always its own box on its own lines, never a bullet or a clause inside another sentence.

Render this template ONLY for cases 1 and 3 above (pack not applied, or applied with gaps). For case 2 (active and fully covered) use the [All settings applied](#all-settings-applied) block instead — never reach this template with zero gaps. It follows the admin portal page: requirement counts, policy status, then the requirements under their headings.

```
<packName> — <tenantName>  ·  <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIREMENTS
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ Not applied          │ Needs configuration  │ Applied              │
│ <NotDeployedCount>   │ <PartiallyDepl…Count>│ <FullyDeployedCount> │
└──────────────────────┴──────────────────────┴──────────────────────┘
<pack not active: "Not applied on this tenant yet." · active: nothing>

POLICY STATUS[ · <Enforced | Observe | Mode not chosen> — modes on only]  ·  <S> stable[ · <D> drifted][ · <U> cannot be checked]
  <catalog PolicyName>                      <ProductDisplayName> Policy   ● <Stable | N drifted | Cannot Be Checked>
  … one line per product
(active pack only; omit the panel when the pack is not active)

<YOUR DEPLOYED POLICIES block — see "Your deployed policies" below; always>

<WHAT HAPPENS TO YOUR AOPS POLICIES block, then the CONFLICTS section — see "If you apply / If you enforce" below; case 1, and any active pack that is not enforced>

IMPACT OF WHAT'S NOT APPLIED
  🔴 High    <highGapCount> settings across <highClauseCount> requirements
  🟡 Medium  <medGapCount> settings across <medClauseCount> requirements
  🟢 Low     <lowGapCount> settings across <lowClauseCount> requirements
  Biggest risk area: <clauseName with most High-impact gap settings>
  Quickest win:      <clauseName with fewest gaps AND ≥1 High setting>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Needs configuration  (<PartiallyDeployedCount> requirements)
UiPath settings are applied but these requirements also need manual configuration steps. Once completed, they will move to Applied.
  <ClauseId>  <clauseName>                        <CheckableControlCount> UiPath settings[ — waits on the conflicts above]
  … every requirement with this status

Not applied  (<NotDeployedCount> requirements)
Requirements not yet addressed by any UiPath settings.
  <ClauseId>  <clauseName>                        <CheckableControlCount> UiPath settings[ — waits on the conflicts above]

Applied  (<FullyDeployedCount> requirements)
Requirements fully addressed by UiPath recommended settings applied through this pack. No further action needed.
  <ClauseId>  <clauseName>                        <CheckableControlCount> UiPath setting(s)

Outside platform scope  (<count> requirements)
These requirements cannot be addressed through platform configuration. Your auditor will need independent organizational evidence.
  • <ClauseId> — <ClauseName>: <Description>
  (first 3, then "and <N> more")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILS  (per requirement with gaps; all of them on 'Show full details')
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
  For each ⟳ row, add a sub-line from `DriftedControls[].Lines[]` (per the line rules),
  falling back to `UnmetSettings[]` only when `Lines` is empty:
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
Next action (state-aware — see "Next-action suggestion"):
  · modes on, active, not enforced      → 'Enforce <packName>' (asks current or standard for every conflict)
  · modes on, Enforced, conflicts       → 'Correct the changed <packName> settings' (current or standard for each)
  · any ⟳ settings or Cannot-Be-Checked → 'Reset the changed <packName> settings back to the standard'
  · Active == true, ⚙ settings          → 'Configure the manual <packName> settings'   ·   'What does [clause name] require?'
  · nothing applied yet                 → 'Apply <packName> settings' (y/n)   ·   'Just fix the High impact gaps'   ·   'Apply only <specific area> settings'
```

Layout rules:
- **Do not compress the layout.** Every non-empty section (Needs configuration, Not applied, Applied) lists **every** requirement in it on its own line. Never merge requirements into "N other requirements", and never mention a requirement only inside the conflict table. The number of lines in a section must equal its count in the REQUIREMENTS row; check this before printing. Omit a section with zero entries (its count still shows in the REQUIREMENTS row).
- Append `— waits on the conflicts above` to a requirement whose remaining gaps are all conflicts: it has no ⚙ setting, and every one of its ✗ settings is in its `Conflicts[]` (`Clauses[].ConflictCount` equals its count of `Status == "not-deployed"` controls). A requirement with conflicts *and* other ✗ settings does not get the note. Count these from the data; never estimate.
- **POLICY STATUS is one line per product**, never a sentence: the catalog `PolicyName` verbatim (no shortening, no live-name suffix such as "(12)"), then `<ProductDisplayName> Policy`, then the badge. Two products can share a policy name (Studio and Studio Web); the subtitle tells them apart. Stable = product `in-place` or `needs-manual-config` with `DriftedControlCount == 0`; drifted = `DriftedControlCount > 0`; Cannot Be Checked = `unverifiable`. Only when a product has several entries in `Policies[]`, list each under its line as `<LicenseTypes[].DisplayName joined by ", ">: <live PolicyName>`.
- Drift: a product with `DriftedControlCount > 0` gets its ⟳ settings listed under its POLICY STATUS line (`<ControlDisplayName>` + its `Lines[]` per the [line rules](#line-rules) + `Requirement impacted by this drift: <clauseName> (<ImpactedClauseId>)`), as well as the ⟳ rows in DETAILS.

### If you apply / If you enforce

Rendered for case 1 (pack not applied) and for an active pack that is not enforced, as the WHAT HAPPENS TO YOUR AOPS POLICIES block followed by the CONFLICTS section, separated by a rule line so the conflicts never read as part of Observe:

```
WHAT HAPPENS TO YOUR AOPS POLICIES

  OBSERVE                                  (modes on only)
  No AOps policy is created, changed or deployed. <P1, P2 …> stay as they are. Agents that
  break a rule are reported, not blocked.

  ENFORCE                                  (modes off: APPLY)
  ✓ <count of Controls[].StatusAfterApply == "deployed"> settings will be applied · ⚙ <sum of Clauses[].ManualConfigControlCountAfterApply> will still need a value only you can set: <their ControlDisplayNames>
┌───────────────────┬────────────────┬───────┬──────────────────────┬──────────────────────────┐
│ Product           │ License type   │ Today │ On enforce           │ AOps policy after        │
│                   │                │       │                      │ enforce                  │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ <ProductDisplayNa │ <license       │ <P<i> │ <rule 3>             │ <ApplyPlan PolicyName>   │
│ me>               │ types>         │ | —>  │                      │                          │
└───────────────────┴────────────────┴───────┴──────────────────────┴──────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFLICTS — RESOLVE THEM TO ENFORCE        (modes off: CONFLICTS — REPLACED ON APPLY)
<CONFLICTS section — rendered exactly as in "Conflicts with your existing policies" below>
```

Worked example — ISO 27001 on a tenant with the two deployed policies (each merged row is one policy shared by both license types) shown under [Your deployed policies](#your-deployed-policies), modes on:

```
WHAT HAPPENS TO YOUR AOPS POLICIES

  OBSERVE
  No AOps policy is created, changed or deployed. P1 and P2 stay as they are. Agents that
  break a rule are reported, not blocked.

  ENFORCE
  ✓ 52 settings will be applied · ⚙ 5 will still need a value only you can set: Connector
    Allowlist, App Allowlist, App Blocklist, URL Allowlist, URL Blocklist
┌───────────────────┬────────────────┬───────┬──────────────────────┬──────────────────────────┐
│ Product           │ License type   │ Today │ On enforce           │ AOps policy after        │
│                   │                │       │                      │ enforce                  │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Assistant         │ Development,   │ —     │ Update, deploy       │ Assistant Governance and │
│                   │ Studio Pro     │       │                      │ Experience               │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Integration       │ No License     │ —     │ Create, deploy       │ Connector And Provider   │
│ Service           │                │       │                      │ Restrictions (11)        │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ AI Trust Layer    │ No License     │ P1    │ Update with P1's     │ AI Capabilities And      │
│                   │                │       │ values and your      │ Safety Governance        │
│                   │                │       │ C1–C15 choices;      │                          │
│                   │                │       │ deploy in place of   │                          │
│                   │                │       │ P1 (P1 not changed)  │                          │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Robot             │ Development,   │ —     │ Update, deploy       │ Runtime Access And       │
│                   │ Studio Pro     │       │                      │ Behavior Controls        │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Studio Web        │ No License     │ P2    │ Update in place (P2  │ Secure Development &     │
│                   │                │       │ is an ISO 27001      │ Code Quality Gates (10)  │
│                   │                │       │ policy)              │                          │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Studio            │ Development,   │ —     │ Update, deploy       │ Secure Development &     │
│                   │ Studio Pro     │       │                      │ Code Quality Gates       │
└───────────────────┴────────────────┴───────┴──────────────────────┴──────────────────────────┘
```

**What happens to your AOps policies — rules**

1. **OBSERVE first, then ENFORCE**, both whenever modes are on and the pack is not applied or not enforced (the admin picks the mode from this). Modes off: only the ENFORCE part, titled APPLY.
2. **OBSERVE** is one fixed paragraph, never a table: Observe writes nothing to the tenant's AOps policies. Name the deployed policies by `P<i>`; with none, drop the "stay as they are" sentence.
3. **ENFORCE table, columns fixed:** Product · License type · Today · On enforce · AOps policy after enforce. One row per `ApplyPlan[]` entry, in `DeploymentPolicies[]` order; entries merge into one row only when they are the **same policy** (`update` entries with the same `PolicyId`), their license types joined with ", ". Never merge `new` entries or different `PolicyId`s, even when their names match: each license type can have its own policy. Every entry is in exactly one row.
   - **Product** = catalog `ProductDisplayName`. **License type** = the license `DisplayName`(s).
   - **Today** = `P<i>` of the deployed policy in that product and license type (the `DeploymentPolicies[].Policies[]` entry whose `LicenseTypes[].Identifier` includes the entry's `LicenseTypeIdentifier`); none → `—`. The names are in [Your deployed policies](#your-deployed-policies); don't repeat them here.
   - **On enforce**: `update` of the Today policy → `Update in place (P<i> is a <packName> policy)` · `update` of another policy with a Today policy → `Update with P<i>'s values and your C…–C… choices; deploy in place of P<i> (P<i> not changed)` (name the conflict numbers only when P<i> has conflicts) · `update` with Today `—` → `Update, deploy` (an earlier apply of this standard left that policy in Policy Library, not deployed) · `new` from the Today policy (`SourcePolicyId`) → `Create from P<i> with your choices; deploy in place of P<i> (P<i> not changed)` · other `new` → `Create, deploy`. Modes off: the same, without "your choices".
   - **AOps policy after enforce** = the entry's `PolicyName` verbatim — the title the policy has in Policy Library after the apply. The server leaves `PolicyName` out for some `update` entries (a policy reused from an earlier apply). Then write the standard's own title for that product — `catalog.json` `Data.DeploymentPolicies[].PolicyName`, joined by `ProductIdentifier` — followed by `(<packName> policy from an earlier apply; its name in Policy Library may carry a suffix)` the first time, `(from an earlier apply)` after. For a `new` entry without a name: `New <catalog PolicyName>`. Never write "this standard's policy", "a policy", or an id.
4. The ✓ / ⚙ line: compute both numbers with the command below and name the ⚙ settings here once — not again elsewhere in the reply. Creates in the table (`Create…` rows' entries) + updates must equal `ApplyPlan.length`.

- The two counts come from `StatusAfterApply` and `ManualConfigControlCountAfterApply` only — never from `ManualConfigChecks[]` entries, keys or products. If `StatusAfterApply` is absent on every control (older server), drop the ✓ / ⚙ line rather than guess.
- **Compute all three numbers with a command — never count by reading the JSON.** Then check: will-be-applied + still-need-a-value = the total number of `Controls[]` entries, and created + updated = `ApplyPlan.length`. If either check fails, recompute; never print numbers that don't add up.
  ```bash
  jq '{applied: ([.Data.Clauses[].Controls[]? | select(.StatusAfterApply == "deployed")] | length),
       manual:  ([.Data.Clauses[].ManualConfigControlCountAfterApply // 0] | add),
       total:   ([.Data.Clauses[].Controls[]?] | length),
       created: ([.Data.ApplyPlan[]? | select(.Action != "update")] | length),
       updated: ([.Data.ApplyPlan[]? | select(.Action == "update")] | length)}' "$SESSION_TEMP/coverage.json"
  ```
  ```powershell
  $c = (Get-Content "$tmpDir\coverage.json" -Raw | ConvertFrom-Json).Data
  $ctl = @($c.Clauses | ForEach-Object { $_.Controls })
  [pscustomobject]@{ applied = @($ctl | Where-Object StatusAfterApply -eq 'deployed').Count
    manual = ($c.Clauses | Measure-Object ManualConfigControlCountAfterApply -Sum).Sum; total = $ctl.Count
    created = @($c.ApplyPlan | Where-Object Action -ne 'update').Count; updated = @($c.ApplyPlan | Where-Object Action -eq 'update').Count }
  ```
- No ApplyPlan (older server, or nothing to write): omit the ENFORCE table, keep the ✓ / ⚙ line.
- Conflict part: always the banner from [Conflicts with your existing policies](#conflicts-with-your-existing-policies) — ⚠ with the count and the per-policy blocks when there are conflicts, ✓ `0 CONFLICTS` when there are none, ⚠ `CONFLICTS NOT CHECKED` (and no apply offer) when `"unavailable"`, nothing when `"not-applicable"`.
- Modes on: the admin chooses current or standard for every conflict before an Enforce apply ([full-apply § Modes on](../full-apply/impl.md#modes-on)); Observe changes none of them. Modes off: applying takes the standard's value for every conflict — say so before any apply confirmation, and name the count.
- An `update` entry is a policy this standard created earlier; it is one of the tenant's deployed policies only when it is in `DeploymentPolicies[].Policies[]`.
- A ✗ setting that is a conflict is listed once, in the conflict list, not again with a separate explanation.

### Your deployed policies

Its own block, with the heavy border, always rendered right after REQUIREMENTS / POLICY STATUS, so the admin sees which of their policies the standard touches before anything else:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ YOUR DEPLOYED POLICIES                                                                       ┃
┃ <D> policies are deployed on <tenantName> in the products this standard covers.              ┃
┃                                                                                              ┃
┃ P<i>  "<live PolicyName>"                                                            <status>┃
┃     <ProductDisplayName> · <license types>                                                   ┃
┃ … two lines per deployed policy                                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ YOUR DEPLOYED POLICIES                                                                       ┃
┃ No policies are deployed on <tenantName> in the products this standard covers.               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

Worked example:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ YOUR DEPLOYED POLICIES                                                                       ┃
┃ 2 policies are deployed on appsdevDefault in the products this standard covers.              ┃
┃                                                                                              ┃
┃ P1  "aitl-23-nov-2026"                                                       ⚠ 15 conflicts  ┃
┃     AI Trust Layer · No License                                                              ┃
┃ P2  "Secure Development & Code Quality Gates (10)"                           ✓ no conflicts  ┃
┃     Studio Web · No License                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

- Two lines per entry of `DeploymentPolicies[].Policies[]`, numbered `P1`, `P2`, … in the order of the conflict section's `DEPLOYED POLICY P<i> of <D>` blocks (conflicting policies first), so `P<i>` is block `i`.
- First line: the live `PolicyName` in quotes, and on the right its status — `⚠ <n> conflicts` (distinct conflict numbers in its block) or `✓ no conflicts`; with `ConflictStatus` other than `"evaluated"`, no status. Second line: `<ProductDisplayName>` (catalog) · `LicenseTypes[].DisplayName` joined by ", ".
- Never print a policy id. Never fold the list into a sentence.

### Conflicts with your existing policies

A conflict is a setting that one of the tenant's **deployed** policies holds at a different value from the standard. Applying (or enforcing) the standard overwrites it, so before the admin says yes they must see, **per deployed policy**: which settings conflict, what the pack recommends, and what the policy applies today. Render this section exactly in this layout — do not restyle, merge, reorder columns or shorten it.

**The conflict count always opens this section in a banner**, so the admin sees at a glance whether applying changes any of their values. Pick the banner by `ConflictStatus` — never drop it, and never shrink it to a sentence:

| `ConflictStatus` / count | Banner | Then |
|---|---|---|
| `"evaluated"`, `ConflictCount > 0` | ⚠ `<ConflictCount> CONFLICTS` | the `DEPLOYED POLICY` blocks and the footer, below |
| `"evaluated"`, `ConflictCount == 0`, `<D> > 0` | ✓ `0 CONFLICTS`, "None of your <D> deployed policies …" | nothing more |
| `"evaluated"`, `ConflictCount == 0`, `<D> == 0` | ✓ `0 CONFLICTS`, "You have no deployed policies …" | nothing more |
| `"unavailable"` | ⚠ `CONFLICTS NOT CHECKED` | no apply offer in this run |
| `"not-applicable"` | no banner, no section | — |

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ✓  0 CONFLICTS WITH YOUR DEPLOYED POLICIES                                                   ┃
┃    None of your <D> deployed policies holds a value that differs from the standard.          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ✓  0 CONFLICTS WITH YOUR DEPLOYED POLICIES                                                   ┃
┃    You have no deployed policies in this standard's products.                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ⚠  CONFLICTS NOT CHECKED                                                                     ┃
┃    Couldn't check for conflicts with your deployed policies. Retry before applying.          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Layout**

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ⚠  <ConflictCount> CONFLICTS WITH YOUR DEPLOYED POLICIES — RESOLVE THEM TO ENFORCE           ┃
┃    In <C> of your <D> deployed policies, these settings differ from the standard.            ┃
┃    <modes on: To enforce, choose for each one: keep your current value, or use the standard's.>┃
┃    <          Observe changes none of them.>                                                 ┃
┃    <modes off: Applying the standard replaces them with the pack's recommended values.>      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

DEPLOYED POLICY P<i> of <D> · <ProductDisplayName> · "<live PolicyName>" · <license types>
[<On apply note — only for a "new" entry made from this policy, see rule 4>]
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C<k>  <ControlDisplayName>[ (×<n>)]                  │ <Recommended>    │ <Current>          │
│       ↳ <sub-setting>                                │ <Recommended>    │ <Current>          │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘

  <footer — modes off only:>
  Applying replaces every one of these values with the standard's. Keeping a current
  value needs Enforce/Observe modes, which are off for this organization.
```

**Worked example** — a tenant whose only deployed policy in the standard's products is one AI Trust Layer policy with 15 conflicts:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ⚠  15 CONFLICTS WITH YOUR DEPLOYED POLICIES — RESOLVE THEM TO ENFORCE                        ┃
┃    In 1 of your 1 deployed policies, these settings differ from the standard.                ┃
┃    To enforce, choose for each one: keep your current value, or use the standard's.          ┃
┃    Observe changes none of them.                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

DEPLOYED POLICY P1 of 1 · AI Trust Layer · "aitl-23-nov-2026" · No License
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C1  Agent Guardrail — Sensitive Data Exposure (×7)   │ Enabled          │ Disabled / Not set │
│ C2  Agent Guardrail — Prompt Injection (×6)          │ Enabled          │ Disabled / Not set │
│ C3  Agent Guardrail — Sentiment Detection (×2)       │ Enabled          │ Disabled           │
│       ↳ Execution stage                              │ Pre              │ Both               │
│       ↳ Sentiment threshold rule                     │ Negative · 0.7 · │ Negative · 0.7 ·   │
│                                                      │ Enabled          │ Not set            │
│ C4  Trace Management — Trace Data TTL                │ 7d               │ 30d                │
│       ↳ TTL enforcement                              │ Enabled          │ Disabled           │
│ C5  Trace Management — Input/Output Logging          │ Enabled          │ Disabled           │
│ C6  Product Toggles — Enable Agents                  │ Enabled          │ Disabled           │
│ C7  Product Toggles — Enable Coded Agents (×2)       │ Enabled          │ Disabled / Not set │
│ C8  Product Toggles — Enable Autopilot for Everyone  │ Enabled          │ Disabled           │
│ C9  Product Toggles — Enable Apps AI Features        │ Enabled          │ Disabled           │
│ C10 Product Toggles — Enable Document Understanding  │ Enabled          │ Disabled           │
│ C11 Product Toggles — Enable Communications Mining   │ Enabled          │ Disabled           │
│ C12 Document Understanding — Generative Classif.     │ Enabled          │ Disabled           │
│ C13 Document Understanding — Generative Extraction   │ Enabled          │ Disabled           │
│ C14 Agent Guardrail — Output Content Filtering (×6)  │ Enabled          │ Disabled / Not set │
│ C15 Communications Mining — External LLM Access      │ Enabled          │ Disabled           │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘
```

With several deployed policies, each one **with conflicts** gets its own `DEPLOYED POLICY P<i> of <D>` block in the same shape. A policy without conflicts gets no block: [Your deployed policies](#your-deployed-policies) already shows it as `✓ no conflicts`.

**Rules**

1. **Deployed policies** = every entry of `DeploymentPolicies[].Policies[]` (the tenant's live policies in the standard's products and license types). `<D>` is their count (numbered `P<i>` as in [Your deployed policies](#your-deployed-policies)); only policies with conflicts get a block. Order: policies with conflicts first (most conflicts first), then the rest in `DeploymentPolicies[]` order.
2. **Block header**, one line: `DEPLOYED POLICY P<i> of <D> · <ProductDisplayName> · "<live PolicyName>" · <LicenseTypes[].DisplayName joined by ", ">`. `ProductDisplayName` comes from the catalog (join on `ProductIdentifier`); the policy name is the **live** one in quotes — the admin knows their own policy by it. Never print a policy id.
3. **Conflicts of a policy** = every `Clauses[].Conflicts[]` entry whose `Policies[]` contains that `PolicyId`, using that entry's own `Lines[]`. `<C>` is the number of policies with at least one conflict. Rows follow clause order; there is no requirement column.
4. **On apply note**, from the `ApplyPlan[]` entries for that product whose `SourcePolicyId` is this policy's `PolicyId` (`Action` `"new"`; an older server's `"copy"` / `"split"`): `On apply: a new policy "<PolicyName>" is created from this one for <license type>, with your choices; this policy itself is not changed.` One note line per such entry. `"update"` or no entry → no note.
5. **Columns are fixed, in this order: Conflict · Pack recommended · Policy applied.** Conflict = the conflict's number, then `ControlDisplayName`. Number conflicts `C1`, `C2`, … once, by `ConflictId`, in clause order: a conflict that appears in several policy blocks (one per license-type group) keeps the same number in each. The numbers are what the admin answers with on enable; if too long, drop words from its end and mark the cut with `.` (`Generative Classif.`), never from the start (the product prefix tells the admin where to find it). Pack recommended = `Recommended`; Policy applied = `Current`.
6. **Values** from `Lines[]` per the [line rules](#line-rules): lines with the same `Recommended` collapse into one row, with `(×<n>)` after the setting when `n > 1` and their distinct `Current` values joined with ` / `. Each other distinct change of the same conflict is a `↳` sub-row, labelled with the line's `Setting` when it has a label, else the key's last segment as plain words (`traces-ttl-enforcement` → `TTL enforcement`, `sentiment-execution-stage` → `Execution stage`). Wrap a long value onto the next line inside its cell; never truncate a value.
7. **Count check before printing**: distinct conflict numbers = `Summary.ConflictCount` (a conflict in several blocks counts once); every `Lines[]` entry is covered by exactly one row or sub-row; the number of blocks = `<C>`.
8. **Banner and footer are fixed text.** The count goes in the banner's first line, in capitals with the word CONFLICTS, and the box uses the heavy border (`┏━┓ ┃ ┗━┛`) so it stands out from the light-bordered tables, and is the same width as them. Pick the banner's third line and the footer by modes (on / off). Modes on: no footer (the banner says it). Modes off: keep the footer.

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

Each ⚙ setting is a `Data.Clauses[].ManualConfigChecks[]` entry: `{ ProductIdentifier, Key, Expected, Actual }`. Group them by `ProductIdentifier`. A product can have several live policies, one per license-type group (`DeploymentPolicies[].Policies[]`): update each of them, once.

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
- **Labelling an active pack Enforced when its `Mode` is `"audit"` or null** — it is Observe / Mode not chosen, and its conflicts still apply.
- **Routing a conflict to restore or the product UI** — a ✗ setting in `Conflicts[]` is fixed by applying/enforcing the standard. Never say re-applying won't change it: applying takes the standard's value for every conflict.
- **Hiding conflicts before an apply** — when `ConflictCount > 0`, the user sees the list and the "replaces these values" warning before any `y`. Never offer apply when `ConflictStatus == "unavailable"`.
- **Counting settings left after apply from anything but `StatusAfterApply` / `ManualConfigControlCountAfterApply`** — counting `ManualConfigChecks[]` keys or products gives the wrong number.
- **Paraphrasing the template or using HTML** — prose bullets instead of the boxes, `<details>` / `<summary>` to fold sections, or the conflict result folded into a sentence ("…updated. There are no conflicts, because …"). Print the template; the banner gets its own box.
- **Vague policy labels** — "this standard's policy", "a pack policy", "the policy". Every policy cell names a policy: its `PolicyName`, `P<i>`, or the catalog title with "from an earlier apply".
- **Choosing for the admin** — picking Enforce or Observe, or current or standard for any conflict the admin's reply (directly, or through `all` / `rest` / a range) did not cover, because the user said "apply", or because the service treats a missing choice as pack. Ask; every conflict is covered by the admin's reply ([full-apply § Modes on](../full-apply/impl.md#modes-on)).
- **Compressing the layout** — "N other requirements", a requirement named only in the conflict list, or policies listed in a sentence. Every requirement and every policy gets its own line.
- **Printing raw formData keys or live policy names** — follow the line rules; card titles use the catalog `PolicyName`.

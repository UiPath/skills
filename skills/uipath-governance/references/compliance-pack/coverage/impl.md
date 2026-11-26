# Coverage — Posture Analysis

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

**Output:** print the template for the case (posture, Enable view, Observe view, Enforced view) filled in, in one fenced code block, with every section, box line and table row it defines. Never paraphrase it as prose or bullets, drop or merge sections, or add lines it doesn't have (SKILL.md critical rule 11). A preference for short answers applies to the text around it, not to the template.

Compares the compliance standard's recommended settings against what is currently deployed on the tenant. Does NOT require the standard to be enabled first. Does NOT certify compliance — it identifies which settings from the standard are not yet configured.

`<packId>` / `<packName>` below = the standard being checked, resolved via [`../catalog/impl.md` § Pack ID lookup](../catalog/impl.md#pack-id-lookup). Coverage is per standard — if the user asked about posture without naming one, resolve it there first; do not default to whichever pack is listed first.

The output mirrors the Compliance Standards page in the UiPath admin portal: three requirement counts (**Not applied** / **Needs configuration** / **Applied**), a **Policy Status** panel per product, the requirements listed under those headings, and an **Outside platform scope** list. Before the standard is applied — or while it is active but not enforced — it also shows what applying or enforcing will do: settings that will still need configuration, conflicts with existing policies, and which policies will be created or updated.

## Command

**Pre-condition:** `$SESSION_TEMP/catalog.json` must exist — run `catalog get` first (see `catalog/impl.md`). The coverage response does NOT carry display names for clauses (`ClauseName` comes back null) — the plain-English clause names the template requires come from joining coverage `Clauses[].ClauseId` to catalog `Clauses[].ClauseId` → `ClauseName` in `catalog.json`.

```bash
# Read the session dir written by catalog get — never create a new one here.
SESSION_TEMP=$(cat "$HOME/.uipath-compliance-current-session")
TENANT_ID=$(uip login status --output json | sed -n 's/.*"TenantId": *"\([^"]*\)".*/\1/p')
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
$tenantId = (uip login status --output json | ConvertFrom-Json).Data.TenantId
uip gov compliance-packs state coverage tenant $tenantId <packId> --output json |
  Set-Content "$tmpDir\coverage.json"

# Applied-or-not is a separate question — coverage cannot answer it.
uip gov compliance-packs state get tenant $tenantId <packId> --output json |
  Set-Content "$tmpDir\state.json"

uip gov compliance-packs state settings --output json | Set-Content "$tmpDir\settings.json"
```

**Modes** — `settings.json` `Data.ModeSelectionEnabled`. `true` (**modes on**): the pack runs in Enforce or Observe; an Enforce apply takes the admin's choice per conflict (keep the current value or update to the standard's recommendation); Observe writes nothing to the tenant's policies. `false`, or a failed / 404 `state settings` (**modes off**): no mode is shown, and applying gives every conflict the standard's value. Everything mode-related below applies only with modes on.

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

0. **Pack active in Observe** (modes on, `Data.Active == true`, `Data.Mode == "audit"`): render the [Observe view](./views.md#observe-view) in place of the template below and of the All settings applied block, then the next actions of case 3 (3·0 first: `'Enforce <packName>'` with its [If you enforce](./apply-and-conflicts.md#if-you-apply--if-you-enforce) block). A null or absent `Mode` (Mode not chosen) is not Observe here: it keeps the template, as the admin portal does. If the catalog has no Observe requirements to show (see the view's fallback), go on to case 2 / 3.
1. **Pack NOT active** (`Data.Active == false`; a never-applied known pack returns 200 with `Active: false`, not a 404 — a 404 from `state get` means the packId itself is not usable, so re-check it against `catalog list` and stop) — the pack is not applied, whatever the coverage numbers say. Offer the mode directly, never a plain "Apply" that asks the mode later: modes on → `'Enforce <packName>'` and `'Observe <packName>'`; modes off → `'Apply <packName>'`. A standard is applied as a whole ([SKILL.md Critical Rule 12](../../../SKILL.md#critical-rules)): never offer part of it (High impact only, one area, one product). If coverage already shows partial or full clause coverage, that is the tenant's own policies coinciding with the standard, NOT the pack — say so plainly ("some of these settings already match what the standard recommends; applying it will manage them going forward") and still offer to apply. Never suppress the apply offer because coverage looks good. Render the [If you apply](./apply-and-conflicts.md#if-you-apply--if-you-enforce) block with it. When `ConflictStatus == "unavailable"`, do NOT offer to apply in this run: show the `CONFLICTS NOT CHECKED` banner from [Conflicts with your existing policies](./apply-and-conflicts.md#conflicts-with-your-existing-policies).
2. **Pack active, everything covered** (`Data.Active == true` and `PartiallyDeployedCount == 0 && NotDeployedCount == 0`): render the [All settings applied](#all-settings-applied) block. Nothing to apply. If the pack is not enforced, add the [If you enforce](./apply-and-conflicts.md#if-you-apply--if-you-enforce) block and the enforce call-to-action from case 3.
3. **Pack active, gaps remain** (`Data.Active == true`, otherwise): do NOT suggest reapplying the standard or applying a subset. Point the user at the residual settings, checking the enforce and drift cases FIRST:
   - **3·0. If the pack is not enforced** (modes on, `Mode` is `"audit"`, null or absent): render the [If you enforce](./apply-and-conflicts.md#if-you-apply--if-you-enforce) block, and offer first: `'Enforce <packName>'`. On yes, hand off to [`../full-apply/impl.md` § Modes on](../full-apply/impl.md#modes-on) — it asks the mode and, for every conflict, keep or update. Every ✗ setting that is in `Conflicts[]` is covered by this offer. Do NOT route a conflict to restore or to the product UI.
   - **3a′. Modes on and the pack is Enforced, with conflicts** (`ConflictStatus == "evaluated"`, `ConflictCount > 0`): the conflicts are the drifted settings. Offer `'Correct the changed <packName> settings'` and hand off to [`../full-apply/impl.md` § Modes on](../full-apply/impl.md#modes-on) (Enforce again): for each one the admin chooses `pack` (put the standard's value back) or `keep` (accept the change). Settings kept on an earlier apply come back as conflicts too — say so. Use 3a for a Cannot-Be-Checked product.
   - **3a. If `Summary.DriftedControlCount > 0` OR any product is `unverifiable`** (and 3a′ does not cover it): `'Reset the changed <packName> settings back to the standard'` — the ⟳ items ARE that list, and restore also RECREATES the missing policy behind any Cannot-Be-Checked product (it resets every live pack policy to the bundle's suggested values and recreates deleted ones). Hand off to [`../restore/impl.md`](../restore/impl.md), which owns the confirmation gate — including the warning that restore also resets any ⚙ manual values an admin has already configured. Do NOT tell the user to hand-edit a ⟳ setting, and do NOT route ⟳ items into the AOps handoff below — that is the remedy for ⚙, not for drift.
   - If any ⚙ `manual` controls exist: `'Configure the manual <packName> settings'` — the ⚙ items with expected/actual (in DETAILS, shown on 'show full details' or when the admin accepts this offer) ARE the to-do list. When the user accepts, hand off to the AOps plugin to update the existing pack policy — see [Configuring manual settings (AOps handoff)](./posture-view.md#configuring-manual-settings--aops-handoff). When 3a also applies, sequence restore FIRST, then the manual values — restore would overwrite manual values configured before it.
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

## Where each part lives

This file is split so that each part fits in one read. Read this file, then the file for the case you are rendering:

| Part | File |
|---|---|
| Posture template (cases 1 and 3), its layout rules and the **Next action** pick list every view ends with; configuring manual settings | [posture-view.md](./posture-view.md) |
| Observe view (case 0) and Enforced view | [views.md](./views.md) |
| Enable view (the admin asked to apply, enable or enforce) | [enable-view.md](./enable-view.md) |
| What happens to your AOps policies (If you apply / If you enforce), Your deployed policies, Conflicts with your existing policies | [apply-and-conflicts.md](./apply-and-conflicts.md) |

Every view uses Your deployed policies and the conflict banner from apply-and-conflicts.md, so read it with any view.

## All settings applied

Next-action case 2 only: `state get` says `Data.Active == true` **AND** `Summary.ClauseSummary.PartiallyDeployedCount == 0 && NotDeployedCount == 0` (every clause fully deployed). Do NOT use `Summary.NewCount == 0` for this — with disjoint product counts a `needs-manual-config` product leaves `NewCount == 0` while settings still need manual setup:

```
All <packName> recommended settings are Applied on <tenantName>.
<fullyDeployedCount> / <totalClauses> clauses fully deployed  ·  all settings Applied ✓

To remove them: 'Remove <packName> settings'
```

Do NOT call `state enable` in this case.

**The `Active` half is not optional.** With full clause coverage but `Active == false`, the tenant's own policies happen to match the standard — the pack is not managing anything. Use case 1 instead: say the settings already line up, and still offer to apply. Never print "To remove them" for a pack that was never applied — there is nothing to remove.

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
- **Vague policy labels** — "this standard's policy", "a pack policy", "the policy". Every policy cell names a policy: its `PolicyName`, `P<i>`, or the catalog title (with the reuse note under the table).
- **Choosing for the admin** — picking Enforce or Observe, or keep or update for any conflict the admin's reply (directly, or through `all` / `rest` / a range) did not cover, because the user said "apply", or because the service treats a missing choice as pack. Ask; every conflict is covered by the admin's reply ([full-apply § Modes on](../full-apply/impl.md#modes-on)).
- **Compressing the layout** — "N other requirements", a requirement named only in the conflict list, or policies listed in a sentence. Every requirement and every policy gets its own line.
- **Printing raw formData keys or live policy names** — follow the line rules; card titles use the catalog `PolicyName`.

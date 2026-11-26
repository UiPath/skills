# Coverage — Posture view

Part of the posture check: read [impl.md](./impl.md) first (commands, parsing, which view to render). This file: the posture template (cases 1 and 3), the Next action pick list every view ends with, and configuring manual settings.

**Output:** print the template filled in, in one fenced code block, with every section, box line and table row it defines ([SKILL.md Critical Rule 11](../../../SKILL.md#critical-rules)).

**How to print it.** Output the template below as plain monospace text inside one fenced code block, filled in, in this section order — not a prose or bullet paraphrase of it. Never use HTML tags (`<details>`, `<summary>`, `<br>`, …): the CLI terminal shows them as raw text, and nothing collapses. Long sections are printed in full, never hidden. The conflict banner is always its own box on its own lines, never a bullet or a clause inside another sentence.

Render this template ONLY for cases 1 and 3 above (pack not applied, or applied with gaps). When the admin asked to apply, enable or enforce the standard (modes on, pack not Enforced), render the [Enable view](./enable-view.md#enable-view) instead — also over case 0. For case 0 (active in Observe) use the [Observe view](./views.md#observe-view). For case 2 (active and fully covered) use the [All settings applied](./impl.md#all-settings-applied) block instead — never reach this template with zero gaps. It follows the admin portal page: requirement counts, policy status, then the requirements under their headings.

```
<packName> — <tenantName>  ·  <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIREMENTS
┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐
│ Not applied - <NotDeployed…> │ Needs configuration - <Par…> │ Applied - <FullyDeployed…>   │
│ None of its settings in      │ Some settings in place, or   │ All its settings in place    │
│ place yet                    │ one needs your input         │                              │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
<pack not active: "Not applied on this tenant yet." · active: nothing>
(Counts are <NotDeployedCount>, <PartiallyDeployedCount>, <FullyDeployedCount>. The two legend lines in each cell are fixed text; pad every cell to 30 characters so the borders line up, e.g. `│ Not applied - 12             │ Needs configuration - 4      │ Applied - 0                  │`.)

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
  <ClauseId>  <clauseName>[ — waits on the conflicts above]
  … every requirement with this status

Not applied  (<NotDeployedCount> requirements)
Requirements not yet addressed by any UiPath settings.
  <ClauseId>  <clauseName>[ — waits on the conflicts above]

Applied  (<FullyDeployedCount> requirements)
Requirements fully addressed by UiPath recommended settings applied through this pack. No further action needed.
  <ClauseId>  <clauseName>

Outside platform scope  (<count> requirements)
These requirements cannot be addressed through platform configuration. Your auditor will need independent organizational evidence.
  • <ClauseId> — <ClauseName>: <Description>
  (first 3, then "and <N> more")

[DETAILS: only when the admin asked to 'show full details' (or for the settings of a named requirement);
 otherwise leave this whole section out and go straight to Next action]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILS  (every requirement, every setting)
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

  [repeat per clause: every requirement, Applied ones included]

  When any product is Cannot Be Checked (unverifiable), add ONE note after the last
  clause block (when DETAILS is left out: after the requirement lists), naming the affected ✗ settings without exposing product status values:
  "Note: the ✗ settings above (<their display names or products>) sit behind a policy
  that is missing from the tenant, so they can't currently be verified. Resetting the
  standard recreates that policy with the recommended values."

```

## Next action

The same for every view: this template, the [Observe view](./views.md#observe-view), the [Enforced view](./views.md#enforced-view), [All settings applied](./impl.md#all-settings-applied) and the report after an apply. It is not printed in the block. After the block, ask with a selectable prompt ([SKILL.md Critical Rule 13](../../../SKILL.md#critical-rules)): question `What would you like to do next?`, header `Next`, 2–4 options taken from this list in order (state-aware — see "Next-action suggestion"), each with a one-line description:

| State | Options |
|---|---|
| modes on, not applied | `Enforce <packName>` (`Block violations across the whole tenant; you then keep or update each of the <N> conflicts`) · `Observe <packName>` (`Monitor and report without blocking; nothing changes in your AOps policies`) |
| modes off, not applied | `Apply <packName>` |
| modes on, active, not enforced | `Enforce <packName>` (keep or update for every conflict) |
| modes on, Enforced, conflicts | `Correct the changed <packName> settings` (keep or update for each) |
| any ⟳ settings or Cannot-Be-Checked | `Reset the changed <packName> settings back to the standard` |
| active, ⚙ settings | `Configure the manual <packName> settings` |
| always, while DETAILS is not shown | `Show full details` (every setting in each requirement, with its recommendation and impact) |

`Show full details` is always one of the options, last, in every view while DETAILS is not on screen; when more than four rows apply, drop from the rows above it, never this one. Picking it prints this template's DETAILS section (every requirement: Setting · Recommendation · Impact, with the ⚙ and ⟳ sub-lines), then asks this question again without it. Never add a do-nothing option (`Leave as is`, `Stay in Observe`): the admin can close the question or type in Other. Picking `Enforce <packName>` or `Observe <packName>` chooses the mode: go to [full-apply § Modes on](../full-apply/impl.md#modes-on) without asking it again. Without a selectable prompt, print the same options as a numbered list under `Next action:` and END YOUR REPLY.

## Layout rules

- **Do not compress the layout.** Every non-empty section (Needs configuration, Not applied, Applied) lists **every** requirement in it on its own line. Never merge requirements into "N other requirements", and never mention a requirement only inside the conflict table. The number of lines in a section must equal its count in the REQUIREMENTS row; check this before printing. Omit a section with zero entries (its count still shows in the REQUIREMENTS row).
- Append `— waits on the conflicts above` to a requirement whose remaining gaps are all conflicts: it has no ⚙ setting, and every one of its ✗ settings is in its `Conflicts[]` (`Clauses[].ConflictCount` equals its count of `Status == "not-deployed"` controls). A requirement with conflicts *and* other ✗ settings does not get the note. Count these from the data; never estimate.
- **POLICY STATUS is one line per product**, never a sentence: the catalog `PolicyName` verbatim (no shortening, no live-name suffix such as "(12)"), then `<ProductDisplayName> Policy`, then the badge. Two products can share a policy name (Studio and Studio Web); the subtitle tells them apart. Stable = product `in-place` or `needs-manual-config` with `DriftedControlCount == 0`; drifted = `DriftedControlCount > 0`; Cannot Be Checked = `unverifiable`. Only when a product has several entries in `Policies[]`, list each under its line as `<LicenseTypes[].DisplayName joined by ", ">: <live PolicyName>`.
- Drift: a product with `DriftedControlCount > 0` gets its ⟳ settings listed under its POLICY STATUS line (`<ControlDisplayName>` + its `Lines[]` per the [line rules](./impl.md#line-rules) + `Requirement impacted by this drift: <clauseName> (<ImpactedClauseId>)`), as well as the ⟳ rows in DETAILS when DETAILS is shown.

## Configuring manual settings — AOps handoff

When the user accepts `'Configure the manual <packName> settings'` (offered ONLY in the already-applied / partial state), hand off to this skill's AOps policy mechanic to update the EXISTING deployed policy. Do NOT re-enable the pack (`state enable`) and do NOT create a new policy — the pack already deployed one policy per product; a `manual` setting is just an org-specific formData key on that policy that automation could not fill. This mutation happens on the **AOps branch** (Critical Rule 3: one branch per mutation).

Each ⚙ setting is a `Data.Clauses[].ManualConfigChecks[]` entry: `{ ProductIdentifier, Key, Expected, Actual }`. Group them by `ProductIdentifier`. A product can have several live policies, one per license-type group (`DeploymentPolicies[].Policies[]`): update each of them, once.

Per product:
1. **Resolve the pack's policy id for the product.** `uip gov aops-policy deployment tenant get <TENANT_ID> --output json` → the `TenantPolicies[]` entry whose `ProductIdentifier` matches → its `PolicyIdentifier`. Cross-check it belongs to the pack against `state get tenant <TENANT_ID> <packId>` `Policies[].ExternalPolicyId`.
2. **Collect the org-specific value(s).** `Expected` is a predicate (`{Eq}`/`{Gte}`/`{Lte}`/`{Contains}`); `manual` means the concrete value is org-specific (an allowlist, a package set, a threshold). Ask the user, and confirm the value satisfies `Expected`. For a `{Contains: [...]}` predicate, compare against the live policy's own formData from step 3's `aops-policy get` — the keys inside the predicate entry are CLI-PascalCased formData keys, not the real ones (see the `Expected` note above), so building an entry from them writes keys the policy does not have.
3. **Update via the AOps plugin.** Follow [`../../aops-policy/aops-policy-manage-guide.md`](../../aops-policy/aops-policy-manage-guide.md): `aops-policy get <PolicyIdentifier>` → set each `Key` in the returned formData to the collected value (build `--input` per [`../../aops-policy/configure-aops-policy-data-guide.md`](../../aops-policy/configure-aops-policy-data-guide.md)) → `aops-policy update` (**full replacement** — pass `--identifier <PolicyIdentifier>` plus every existing field back: `--name`, `--product-name`, `--description`, `--priority`, `--availability`, `--input` — omitting any clears it, per [`../../aops-policy/aops-policy-commands.md`](../../aops-policy/aops-policy-commands.md)). Never call `state enable`.
4. **Receipt + confirm.** Show a post-update receipt (Critical Rule 6), then re-run coverage; each fixed ⚙ setting should flip to ✓ (`Controls[].Status == "deployed"`).

Graceful degrade: if the AOps guides are unavailable, present the ⚙ list (setting, expected, current) and tell the user to set each value on the product's deployed policy in Automation Ops — never leave the manual settings as a dead-end suggestion.

## User-facing output (shape to follow)

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

Print the list, then ask the settings that have a recommended value with a selectable prompt (Critical Rule 13), one question each: options `Use the recommended value` (`<recommended>`) and `Keep the current value` (`<current>`); another value goes in the tool's Other field. A value only the admin can know (a package list, an allowlist) has nothing to pick from: ask it in text.

Review gate before applying:

```
Will change (3 existing policies — no re-apply of the standard):
  Studio Web — Publish Outside Personal Workspace       → Development only
  Workflow Analyzer — Required Packages                 → <user packages>
  Model Governance — Third-Party AI Providers Allowlist → <user providers>
```

Then ask with a selectable prompt (Critical Rule 13): `Update these <n> settings?`, options `Yes, update` / `Cancel`. Without the tool: `Proceed? (y/n)`.

Receipt + re-check after applying:

```
✅ 3 settings configured on <tenantName> · by you · <date>
Clauses fully covered: 9 / 15  (was 7)  ·  Suppliers 2/5 → 3/5
Remaining gaps: ask 'What does [clause] require?'
```

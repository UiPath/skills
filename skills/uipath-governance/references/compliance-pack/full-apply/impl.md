# Full Apply — Configure All Recommended Settings

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Applies the entire compliance standard in one command. Backend creates and deploys all recommended settings.

`<packId>` / `<packName>` below = the standard being applied — `Data.PackId` / `Data.PackName` from the session `catalog.json`, resolved via [`../catalog/impl.md` § Pack ID lookup](../catalog/impl.md#pack-id-lookup).

**Note:** This configures settings recommended by <packName>. Your organization's auditor determines compliance status — UiPath does not certify compliance.

## Pre-condition

Coverage (posture analysis) has been run and presented, and is run **again right before the confirmation** below. Enable checks the choices against the coverage they were made on (`CoverageVersion`), so a reading from earlier in the conversation is not enough. If coverage returned `ConflictStatus == "unavailable"`, do not apply: tell the user conflicts with deployed policies couldn't be checked and to retry.

This flow covers: a standard that is not applied; one that is applied but not enforced (switch to Enforce); and, with modes on, one already in Enforce whose coverage shows conflicts (enforce again to correct the changed settings).

```bash
SESSION_TEMP=$(cat "$HOME/.uipath-compliance-current-session")
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state settings --output json > "$SESSION_TEMP/settings.json"
uip gov compliance-packs state coverage tenant $TENANT_ID <packId> --output json > "$SESSION_TEMP/coverage.json"
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json > "$SESSION_TEMP/state.json"
```

`settings.json` `Data.ModeSelectionEnabled == true` → [Modes on](#modes-on). `false`, or a failed / 404 `state settings` → [Modes off](#modes-off).

## Modes on

Every decision below is the admin's. Ask, wait for the answer, and never fill one in — not the mode, and not a single conflict.

### Step 1 — Ask how the standard should run

The admin must have seen coverage's [YOUR DEPLOYED POLICIES](../coverage/impl.md#your-deployed-policies) and WHAT HAPPENS TO YOUR AOPS POLICIES blocks ([coverage § If you apply / If you enforce](../coverage/impl.md#if-you-apply--if-you-enforce)) before choosing. If coverage was just printed in this reply, ask right after it and don't repeat anything; otherwise show those two blocks unchanged first. The question itself stays short — the blocks already say what each mode does.

```
How should <packName> run on <tenantName>?

  1. Enforce — you then choose, for each conflict (C1–C<N>), current or standard
  2. Observe — nothing changes in your AOps policies; you can enforce later

Reply 1 or 2.
```

- Ask even when the user said "apply" or "enable": neither names a mode.
- Standard already applied (`state.json` `Data.Active == true`): say its current mode first ("<packName> is in Observe"). A reply naming the current mode changes nothing — say so; for Enforce → Enforce this is only useful to correct changed settings (step 2 onward).
- Enforce → Observe takes the standard's policies off the tenant: each slot gets back the admin's own policy it replaced, if it still exists, or no policy. Say this before the confirmation.
- Anything other than 1 or 2: ask again.

Observe → go to step 4 (no choices: Observe changes none of the conflicting values).

### Step 2 — Show the conflicts

The conflicts were shown with coverage (CONFLICTS — RESOLVE THEM TO ENFORCE). Don't print them again in the same reply; if they are no longer in view, render [coverage § Conflicts with your existing policies](../coverage/impl.md#conflicts-with-your-existing-policies) exactly. 0 conflicts → step 4.

### Step 3 — Ask, for every conflict: current or standard

One message, then wait. The admin answers with the words **current** and **standard**; `keep` / `pack` are only the values sent to the service, never shown.

```
For each conflict, choose what the setting holds after enforcing:
  current   — stays as your policy has it today. <packName> then counts that setting
              as not applied.
  standard  — set to the value <packName> recommends.

  #     Setting                                          Today              Standard
  C1    Agents: Enable Agents                            Disabled           Enabled
  C2    Coded Agents: Enable Coded Agents                Not set            Enabled
  C4    Trace Management: Trace Data TTL                 30d                7d
          ↳ TTL enforcement                              Disabled           Enabled
          ↳ in 2 policies: RPA Developer ("Robot Dev"), Automation Developer ("Robot AD")
  C7    Product Toggles: Enable Coded Agents             Disabled           Enabled
          ↳ ISO 42001 also requires today's value: standard changes it there too.
  C9    Product Toggles: Enable Apps AI Features         Disabled           Enabled
          ↳ today's value also meets <packName>: current keeps it applied.
  …     one row per conflict, C1 to C<N>

Reply in any of these ways:
  all standard                              all current
  C1 standard, C2 standard, rest current    C1–C9 current, C10–C15 standard
  all standard except C3, C5                C4 standard for RPA Developer, current for Automation Developer
```

- **Today / Standard** = the conflict's `Lines[]` `Current` / `Recommended`, per the [line rules](../coverage/impl.md#line-rules) (same rows and `↳` sub-rows as the conflict table). One or two short lines after the list may say what the choices turn on or off ("standard for C1–C9 turns on AI features that are off today"); never more.
- **Reading the reply.** `current`, `keep`, `mine`, `today` → keep · `standard`, `pack`, `recommended` → pack. `all <choice>` sets every conflict; `except C…` gives the listed ones the other choice; `rest` / `others` / `remaining` sets every conflict not named earlier in the same reply; ranges `C1–C9`, `C1-C9`, `C1 to C9`. A per-license-type answer applies only to the license types it names.
- **Nothing is filled in by the skill.** After reading the reply, every conflict (and, for a conflict in several policies, every license type of it) must have a choice the admin gave, directly or through `all` / `rest` / a range. Ask again only for what is still open, listing those conflicts. Ask too when a reply is contradictory (a conflict given both choices) or names a conflict that doesn't exist. Never use the service's "no entry means pack".
- A conflict whose `Policies[]` has several entries (license-type groups): show the `↳ in N policies` line. A plain choice for it applies to all its license types.
- A current value with `OwnerPackIds`: show the `↳` line naming those standards (catalog names) — standard writes this standard's value, and their setting then shows as changed.
- Mark `today's value also meets <packName>` only when every one of the conflict's `Lines[]` has `IsMet == true`; otherwise the `current` legend line holds.
- Correcting changed settings on a standard already in Enforce: `standard` puts its value back, `current` accepts the change. Settings left at current on an earlier apply come back as conflicts; say so, and ask again anyway.
- Never show a `ConflictId`, `PolicyId` or license identifier.

### Step 4 — Confirm

```
<Enforce | Apply in Observe> <packName> on <tenantName>?

CONFLICT CHECK
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ⚠  <N> CONFLICTS WITH YOUR DEPLOYED POLICIES                                                 ┃
┃    Your choices: <S> set to the standard · <K> stay as today                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Your choices                                              (Enforce, with conflicts)
  C1   Agents: Enable Agents                        standard → Enabled
  C2   Coded Agents: Enable Coded Agents            current  → Not set
  C4   Trace Management: Trace Data TTL             RPA Developer: standard → 7d · Automation Developer: current → 30d
  … every conflict, C1 to C<N>

WHAT HAPPENS TO YOUR AOPS POLICIES
  <only the chosen mode's part of coverage's block: the ENFORCE table, or the OBSERVE paragraph>

⚠ <N> settings will still need a value from you:          (Enforce only)
  • <controlDisplayName>  — <plain-English prompt for the value>

Proceed? (y/n)
```

- **CONFLICT CHECK is its own block, first in the confirmation, always shown** — the admin sees whether this apply changes any of their values before reading anything else. Pick it by what coverage reported and the mode:

  ```
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃ ⚠  <N> CONFLICTS WITH YOUR DEPLOYED POLICIES                                                 ┃
  ┃    Your choices: <S> set to the standard · <K> stay as today                                 ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃ ✓  0 CONFLICTS WITH YOUR DEPLOYED POLICIES                                                   ┃
  ┃    Enforcing changes none of the values your policies apply today.                           ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃ ⓘ  <N> CONFLICTS WITH YOUR DEPLOYED POLICIES                                                 ┃
  ┃    Observe changes none of them. You'll choose current or standard for each if you enforce.  ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  ```

  - Enforce with conflicts → ⚠, with `<S>` + `<K>` (+ `<M>`) = `<N>` = `Summary.ConflictCount`, counted from the choices file, not by eye. A conflict answered per license type is neither: add ` · <M> mixed (per license type)` to the line, and omit it when 0.
  - 0 conflicts (Enforce or Observe) → ✓; for Observe write "Observe writes nothing to your policies." as its second line.
  - Observe with conflicts → ⓘ.
  - Never fold this into a sentence or the "Your choices" list.
- "Your choices" lists every conflict with the value it will hold (`Recommended` for standard, `Current` for current). Its line count equals `Summary.ConflictCount`; check before printing.
- The ⚠ list is coverage `Clauses[].Controls[]` with `StatusAfterApply == "manual"`, with the `ManualConfigChecks[]` expectation as the prompt.
- "Your choices" always lists every conflict, also when the admin answered with `all` / `rest` / a range — this is where a shortcut is checked.
- Require `y`. Halt on anything else. A change of mind ("make C3 current") updates that conflict and shows this confirmation again.

### Step 5 — Enable

Write the choices (current → `keep`, standard → `pack`), one entry per conflict — `pack` ones too, so what is sent is exactly what the admin chose — or one per license type for a conflict answered per license type (`licenseTypeIdentifier` = that policy's `LicenseTypes[].Identifier`; a policy with several license types gets an entry for each):

```json
[
  { "conflictId": "<Conflicts[].ConflictId>", "choice": "pack" },
  { "conflictId": "<Conflicts[].ConflictId>", "choice": "keep", "licenseTypeIdentifier": "<LicenseTypes[].Identifier>" }
]
```

Check before sending: every `ConflictId` in coverage is covered, and none other appears.

```bash
# Enforce
uip gov compliance-packs state enable tenant $TENANT_ID <packId> --mode enforce \
  --coverage-version "$(jq -r '.Data.CoverageVersion' "$SESSION_TEMP/coverage.json")" \
  --conflict-resolutions "$(cat "$SESSION_TEMP/conflict-resolutions.json")" --output json
# Enforce with no conflicts: the same, without --conflict-resolutions
# Observe
uip gov compliance-packs state enable tenant $TENANT_ID <packId> --mode audit --output json
```

```powershell
$cov = (Get-Content "$tmpDir\coverage.json" -Raw | ConvertFrom-Json).Data.CoverageVersion
$res = (Get-Content "$tmpDir\conflict-resolutions.json" -Raw) -replace '\s+', ' '
# Windows PowerShell 5.1 drops the inner double quotes of a native argument; escape them there.
if ($PSVersionTable.PSVersion.Major -lt 7) { $res = $res.Replace('"', '\"') }
uip gov compliance-packs state enable tenant $tenantId <packId> --mode enforce --coverage-version $cov --conflict-resolutions $res --output json
```

### Errors (modes on)

The service's code is in the failure's `Message` (`HTTP 409: {"error":"coverage_stale"}`).

| Code | Action |
|---|---|
| `coverage_stale` (409) | The tenant's policies changed after coverage was read. Re-run coverage, show the conflicts again (step 2), and ask again for **every** conflict (step 3) — show the earlier answer next to a conflict that is unchanged, but get it confirmed. Never resend the old choices. |
| `another_pack_already_enabled` (409) | Another standard is active. Name it (`state list`, catalog name) and ask whether to replace it. Only on yes, run the same command with `--replace-active`. |
| `invalid_conflict_resolutions` (400) | A choice names a conflict coverage no longer lists. Re-run coverage and ask again for the conflicts that changed. |
| `coverage_version_required`, `conflict_resolutions_not_applicable`, `invalid_pack_mode` (400) | The command was built wrong — fix it from the CLI's `Instructions`; don't ask the admin again. |

## Modes off

Build this table from `catalog.clauses[].editorialPolicies[].controls[]` filtered to products where `coverage.deploymentPolicies[].status == "new"`. Group settings by impact. List the settings that will still need user-supplied values after apply — coverage `Clauses[].Controls[]` with `StatusAfterApply == "manual"`, with the `ManualConfigChecks[]` expectation as the plain-English prompt (fall back to `synthesize-formdata` notEmpty warnings only when `StatusAfterApply` is absent).

Always add the conflict banner to the confirmation (below the ⚠ section), so the admin sees the conflict count right before `y` — ✓ `0 CONFLICTS` when there are none. With modes off every conflicting setting is replaced with the standard's value. Render it exactly as [coverage § Conflicts with your existing policies](../coverage/impl.md#conflicts-with-your-existing-policies), with the modes-off footer.

```
Configure <packName> settings on <tenantName>?

┌──────────┬─────────────────────────────────────────────────────┐
│ Impact   │ Settings                                            │
├──────────┼─────────────────────────────────────────────────────┤
│ High     │ <comma-separated displayNames of High settings,     │
│ (<N>)    │ truncated to first 3 + "N more">                    │
├──────────┼─────────────────────────────────────────────────────┤
│ Medium   │ <comma-separated displayNames, first 3 + "N more">  │
│ (<N>)    │                                                     │
├──────────┼─────────────────────────────────────────────────────┤
│ Low (<N>)│ <comma-separated displayNames>                      │
└──────────┴─────────────────────────────────────────────────────┘

⚠ <N> settings need values from you:
  • <controlDisplayName>  — <plain-English prompt for the value>
  • ...
(omit the ⚠ section if no settings need user-supplied values)

<conflict banner from coverage — ⚠ <N> CONFLICTS with its per-policy blocks and footer, or ✓ 0 CONFLICTS — unchanged>

Proceed? (y/n)
```

Require `y`. Halt on anything else.

```bash
uip gov compliance-packs state enable tenant $TENANT_ID <packId> --output json
```

`state enable` is idempotent — safe to call even if partially applied. On `another_pack_already_enabled` (409), name the active standard and ask whether to replace it; only on yes, run it again with `--replace-active`.

## Verify

```bash
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Parse `Data.Active` (must be `true`), `Data.Mode` (modes on: the mode the admin chose) and `Data.Policies[]` (policy UUIDs). Then run coverage again: with Enforce, every conflict answered `pack` is gone, and every one answered `keep` still shows (as a ✗ setting).

## Report

```
<packName> settings configured on <tenantName> ✓

SUMMARY
┌───────────────────────────────────┬───────────┐
│ Settings before                   │ <N> / <T> │
│ Settings after                    │ <T> / <T> │
│ High impact settings configured   │ <N>       │
└───────────────────────────────────┴───────────┘

⚠ Manual configuration needed:
┌──────────────────────┬──────────────────────────────────────────────┐
│ Control              │ Where                                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ <controlDisplayName> │ <configLocation from catalog>                │
└──────────────────────┴──────────────────────────────────────────────┘
(omit the ⚠ table if no SKIPped controls)

Applied by: <UIPATH_USER from ~/.uipath/.auth>  ·  <tenantName>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
```

## Org-scope deployment (all tenants)

When the user says "apply to all tenants", "organization-wide", or "entire org", configure each tenant individually.

> **Note:** `state enable organization` is exposed by the CLI but is not implemented on the backend — calling it has no effect. The correct approach is to iterate over all tenants in the org and call `state enable tenant` for each one.

### Step 1 — Discover all tenants in the org

```bash
uip login tenant list --output json > "$SESSION_TEMP/tenants.json"
```

Parse `Data[].TenantName` and `Data[].TenantId` for the list of tenants.

### Step 2 — Run posture analysis per tenant

For each tenant, run coverage to understand current state:

```bash
uip gov compliance-packs state coverage tenant <tenantId> <packId> --output json
```

Aggregate results: note how many tenants have gaps vs are already fully Applied.

### Step 3 — Confirmation

```
Configure <packName> settings across all tenants in <UIPATH_ORGANIZATION_NAME>?

Tenants to configure:
  <tenantName1> — <N> settings Not Applied
  <tenantName2> — <N> settings Not Applied
  <tenantName3> — already fully Applied (will skip)

<totalTenantsToConfig> tenants will be configured. Your auditor determines compliance status.
Continue? (y/n)
```

Require `y`. Halt on anything else. Skip tenants where `NewCount == 0` (all settings already Applied).

### Step 4 — Enable per tenant

For each tenant with gaps, call enable individually:

```bash
for each tenant with NewCount > 0:
  uip gov compliance-packs state enable tenant <tenantId> <packId> --output json
```

### Step 5 — Verify

```bash
for each configured tenant:
  uip gov compliance-packs state get tenant <tenantId> <packId> --output json
```

### Report

```
<packName> settings configured across <N> tenants in <UIPATH_ORGANIZATION_NAME> ✓

┌──────────────────┬──────────────────┐
│ Tenant           │ Status           │
├──────────────────┼──────────────────┤
│ <tenantName1>    │ Applied ✓        │
│ <tenantName2>    │ Applied ✓        │
│ <tenantName3>    │ Already Applied  │
└──────────────────┴──────────────────┘

Applied by: <user>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
```

## Error handling

| Error | Action |
|---|---|
| Any compliance-packs call → **403 / Forbidden** | Org not enrolled in the Compliance Standards preview — stop, do not retry, run no further compliance commands. Show the opt-in message. See [preview-gate.md](../preview-gate.md). |
| `state enable` → **409** with `"Retry": "RetryAfter10Seconds"` | Another operation holds the per-pack lock (e.g. a concurrent enable/disable) — transient. Wait ~10 seconds and retry, up to 3 attempts. Halt and report only if it persists. |
| `state enable` → 4xx (non-403, non-409) | Halt. Report error verbatim. Do NOT retry. |
| `state enable` → 5xx AND `"Retry": "RetryWillNotFix"` | Halt. Report error verbatim. Do NOT retry — the server explicitly flagged retrying as futile. |
| `state enable` → 5xx (transient, no `RetryWillNotFix`) | Retry once after a short pause. If it fails again, halt and report. |
| `Data.active != true` after enable | Unexpected — ask user to run `state get` manually and report the output. |

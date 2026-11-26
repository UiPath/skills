# Coverage — Enable view

Part of the posture check: read [impl.md](./impl.md) first (commands, parsing, which view to render). This file: the view shown when the admin asks to apply, enable or enforce the standard.

**Output:** print the template filled in, in one fenced code block, with every section, box line and table row it defines ([SKILL.md Critical Rule 11](../../../SKILL.md#critical-rules)).

## Enable view

Rendered in place of the template above when the admin asked to **apply, enable or enforce** the standard, modes are on, and the pack is not Enforced (not applied, in Observe, or Mode not chosen). It follows the admin portal's enable page: the two modes with what each covers, the admin's deployed policies, what happens to their AOps policies, then the conflicts **by requirement**, and the count of requirements with none. There is no REQUIREMENTS box, impact summary or per-status requirement list here: those are posture, and they stay in the template for a posture question or "show full details". Modes off, or a catalog without `CheckerSummary` (older server): use the template above.

**Read the checker view of the catalog** — it adds the requirements covered only by runtime checker rules (the portal's total), each clause's `Source` and `CheckerSummary`. Keep it in its own file: `catalog.json` stays the default view the template counts from.

```bash
uip gov compliance-packs catalog get <packId> --include-checker-rules --output json > "$SESSION_TEMP/catalog-checker.json"
```
```powershell
uip gov compliance-packs catalog get <packId> --include-checker-rules --output json | Set-Content "$tmpDir\catalog-checker.json"
```

**Counts — compute them with a command, never by reading the JSON:**
- `T` = `CheckerSummary.ClauseCount` — every requirement UiPath settings or checker rules cover. Enforce covers all `T`.
- `O` = `CheckerSummary.CheckerClauseCount` minus the Observe requirements (`Source` `"CHECKER"` / `"BOTH"`) with at least one setting an existing policy already sets (the [Observe view](./views.md#observe-view)'s Enforced rule, read from `catalog-checker.json`), never below 0. When `O == 0`, add under Observe: `Your policies already set every setting Observe would watch.`
- `R` = coverage clauses with at least one `Conflicts[]` entry · `N` = `Summary.ConflictCount` · `U` = `catalog-checker.json` `UnsupportedClauses[]` count.

```bash
jq -n --slurpfile cat "$SESSION_TEMP/catalog-checker.json" --slurpfile cov "$SESSION_TEMP/coverage.json" '
($cat[0].Data) as $c | ($cov[0].Data) as $v
| ([$v.Clauses[] | {key: .ClauseId, value: (.Controls // [])}] | from_entries) as $ctlById
| [$v.Clauses[].Conflicts[]?] as $conf
| def same($p; $ctl): .ProductIdentifier == $p and (if ($ctl.ControlId and .ControlId) then .ControlId == $ctl.ControlId else .ControlDisplayName == $ctl.DisplayName end);
  [ $c.Clauses[] | select(.Source == "CHECKER" or .Source == "BOTH") | . as $cl
    | [.Rules[]?.ControlId | select(.)] as $ids
    | [ .EditorialPolicies[]? | .ProductIdentifier as $p | .Controls[]
        | select(.ControlId as $i | $i != null and ($ids | index($i)) != null) | . as $ctl
        | ([$conf[] | select(same($p; $ctl))] | length > 0)
          or ([($ctlById[$cl.ClauseId] // [])[] | select(same($p; $ctl)) | (.EnforcedBy // [])[]] | length > 0) ]
    | any ] as $enforced
| { T: $c.CheckerSummary.ClauseCount,
    O: ([0, ($c.CheckerSummary.CheckerClauseCount - ([$enforced[] | select(.)] | length))] | max),
    R: ([$v.Clauses[] | select((.Conflicts // []) | length > 0)] | length),
    N: $v.Summary.ConflictCount,
    U: (($c.UnsupportedClauses // []) | length) }'
```
```powershell
$c = (Get-Content "$tmpDir\catalog-checker.json" -Raw | ConvertFrom-Json).Data
$v = (Get-Content "$tmpDir\coverage.json" -Raw | ConvertFrom-Json).Data
$conf = @($v.Clauses | ForEach-Object { $_.Conflicts })
function Same($i, $p, $ctl) { $i.ProductIdentifier -eq $p -and $(if ($ctl.ControlId -and $i.ControlId) { $i.ControlId -eq $ctl.ControlId } else { $i.ControlDisplayName -eq $ctl.DisplayName }) }
$enforced = @($c.Clauses | Where-Object { $_.Source -in 'CHECKER', 'BOTH' } | Where-Object {
  $cl = $_; $ids = @($cl.Rules | ForEach-Object { $_.ControlId } | Where-Object { $_ })
  $ctls = @(($v.Clauses | Where-Object ClauseId -eq $cl.ClauseId).Controls)
  @($cl.EditorialPolicies | ForEach-Object { $p = $_.ProductIdentifier; $_.Controls | Where-Object { $_.ControlId -and $ids -contains $_.ControlId } | Where-Object {
    $ctl = $_; @($conf | Where-Object { Same $_ $p $ctl }).Count -gt 0 -or @($ctls | Where-Object { (Same $_ $p $ctl) -and @($_.EnforcedBy).Count -gt 0 }).Count -gt 0 } }).Count -gt 0 }).Count
[pscustomobject]@{ T = $c.CheckerSummary.ClauseCount
  O = [Math]::Max(0, $c.CheckerSummary.CheckerClauseCount - $enforced)
  R = @($v.Clauses | Where-Object { @($_.Conflicts).Count -gt 0 }).Count
  N = $v.Summary.ConflictCount; U = @($c.UnsupportedClauses).Count }
```

Print it as one fenced code block, filled in:

```
<PackLongName> — <tenantName>  ·  <date>
● <Not applied | Observe | Mode not chosen>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APPLICATION MODE
  1. Enforce   Block violations across the whole tenant. The complete standard.
               Covers everything you build and run in the tenant · <T> of <T> requirements
  2. Observe   Monitor and report without blocking anything. A subset of the standard.
     (preview) Covers all AI activities in the tenant · <O> of <T> requirements

<YOUR DEPLOYED POLICIES block — see "Your deployed policies">

<WHAT HAPPENS TO YOUR AOPS POLICIES block — see "If you apply / If you enforce">

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<conflict banner — see "Conflicts with your existing policies">

CONFLICTS TO RESOLVE                                            <R> requirements · <N> conflicts

<ClauseId>  <ClauseName>                                                                   ⚠ <n>
Your policy: P<i> "<live PolicyName>" · Included in policy: <catalog PolicyName>
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C<k>  <ControlDisplayName>[ (×<n>)]                  │ <Recommended>    │ <Current>          │
│       ↳ <sub-setting>                                │ <Recommended>    │ <Current>          │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘
… one block per requirement with conflicts, in catalog order

NO CONFLICTS                                                                <T − R> requirements
OUTSIDE PLATFORM SCOPE — your auditor needs separate evidence for these         <U> requirements
```

After the block, ask the mode with a selectable prompt: the question and options are in [full-apply § Step 1](../full-apply/impl.md#step-1--ask-how-the-standard-should-run) (Enforce, Observe, Show full details). Without the tool, end the block with `How should <packName> run on <tenantName>? Reply 1 (Enforce) or 2 (Observe).` When the admin already chose the mode (a posture next action, or a request that names it), print the view without the question and go on with full-apply.

Worked example — ISO 42001 on appsdevDefault (not applied; P1 is an AI Trust Layer policy with 9 conflicts):

```
UiPath ISO/IEC 42001:2023 — AI Management System — appsdevDefault  ·  2026-11-24
● Not applied
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APPLICATION MODE
  1. Enforce   Block violations across the whole tenant. The complete standard.
               Covers everything you build and run in the tenant · 23 of 23 requirements
  2. Observe   Monitor and report without blocking anything. A subset of the standard.
     (preview) Covers all AI activities in the tenant · 9 of 23 requirements

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ YOUR DEPLOYED POLICIES                                                                       ┃
┃ 2 policies are deployed on appsdevDefault in the products this standard covers.              ┃
┃                                                                                              ┃
┃ P1  "aitl-22-nov-2026"                                                        ⚠ 9 conflicts  ┃
┃     AI Trust Layer · No License                                                              ┃
┃ P2  "Assistant Governance and Experience (6)"                                ✓ no conflicts  ┃
┃     Assistant · No License                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

WHAT HAPPENS TO YOUR AOPS POLICIES

  OBSERVE
  No AOps policy is created, changed or deployed. P1 and P2 stay as they are. Agents that
  break a rule are reported, not blocked.

  ENFORCE
  ✓ 48 settings will be applied
  ⚙ 17 will still need a value only you can set (listed before you confirm)
┌───────────────────┬────────────────┬───────┬──────────────────────┬──────────────────────────┐
│ Product           │ License type   │ Today │ On enforce           │ AOps policy after        │
│                   │                │       │                      │ enforce                  │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ AI Trust Layer    │ No License     │ P1    │ Reuse with P1's      │ AI Capabilities And      │
│                   │                │       │ values and your      │ Safety Governance        │
│                   │                │       │ C1–C9 choices;       │                          │
│                   │                │       │ deploy in place of   │                          │
│                   │                │       │ P1 (P1 not edited)   │                          │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Assistant         │ Development    │ —     │ Reuse, update,       │ Assistant Governance and │
│                   │                │       │ deploy               │ Experience               │
│                   │ Studio Pro     │ —     │ Reuse, update,       │ Assistant Governance and │
│                   │                │       │ deploy               │ Experience               │
│                   │ No License     │ P2    │ Reuse with P2's      │ Assistant Governance and │
│                   │                │       │ values; deploy in    │ Experience               │
│                   │                │       │ place of P2 (P2 not  │                          │
│                   │                │       │ edited)              │                          │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Studio            │ Studio Pro     │ —     │ Reuse, update,       │ Secure Development &     │
│                   │                │       │ deploy               │ Code Quality Gates       │
│                   │ Development    │ —     │ Reuse, update,       │ Secure Development &     │
│                   │                │       │ deploy               │ Code Quality Gates       │
│                   │ No License     │ —     │ Reuse, update,       │ Secure Development &     │
│                   │                │       │ deploy               │ Code Quality Gates       │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Robot             │ Studio Pro     │ —     │ Reuse, update,       │ Runtime Access And       │
│                   │                │       │ deploy               │ Behavior Controls        │
│                   │ Development    │ —     │ Reuse, update,       │ Runtime Access And       │
│                   │                │       │ deploy               │ Behavior Controls        │
│                   │ No License     │ —     │ Reuse, update,       │ Runtime Access And       │
│                   │                │       │ deploy               │ Behavior Controls        │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Studio Web        │ No License     │ —     │ Reuse, update,       │ Secure Development &     │
│                   │                │       │ deploy               │ Code Quality Gates       │
└───────────────────┴────────────────┴───────┴──────────────────────┴──────────────────────────┘
  All 11 reuse a policy UiPath ISO 42001 created on its earlier apply and kept in Policy
  Library, one per product and license type; none is created new. Their names there may
  carry a suffix such as (6).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ⚠  9 CONFLICTS WITH YOUR DEPLOYED POLICIES — RESOLVE THEM TO ENFORCE                         ┃
┃    In 1 of your 2 deployed policies, these settings differ from the standard.                ┃
┃    To enforce, choose for each one: keep the current value or update to the standard's       ┃
┃    recommendation.                                                                           ┃
┃    Observe changes none of them.                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

CONFLICTS TO RESOLVE                                                5 requirements · 9 conflicts

6.1.4  AI system impact assessment                                                           ⚠ 2
Your policy: P1 "aitl-22-nov-2026" · Included in policy: AI Capabilities And Safety Governance
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C1  Agent Guardrail — Sensitive Data Exposure (×7)   │ Enabled          │ Disabled / Not set │
│ C2  Agent Guardrail — Prompt Injection Prev. (×6)    │ Enabled          │ Disabled / Not set │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘

A.3.3  Reporting of concerns                                                                 ⚠ 1
Your policy: P1 "aitl-22-nov-2026" · Included in policy: AI Capabilities And Safety Governance
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C3  Agent Guardrail — Sentiment Detection (×2)       │ Enabled          │ Disabled           │
│       ↳ Execution stage                              │ Pre              │ Both               │
│       ↳ Sentiment table                              │ Negative · 0.7 · │ Negative · 0.7 ·   │
│                                                      │ Enabled          │ Not set            │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘

A.6.2.8  AI system recording of event logs                                                   ⚠ 2
Your policy: P1 "aitl-22-nov-2026" · Included in policy: AI Capabilities And Safety Governance
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C4  Trace Management — Trace Data TTL                │ 7d               │ 30d                │
│       ↳ TTL enforcement                              │ Enabled          │ Disabled           │
│ C5  Trace Management — Input/Output Logging          │ Enabled          │ Disabled           │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘

A.9.2  Processes for responsible use of AI systems                                           ⚠ 3
Your policy: P1 "aitl-22-nov-2026" · Included in policy: AI Capabilities And Safety Governance
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C6  Product Toggles — Enable Agents                  │ Enabled          │ Disabled           │
│ C7  Product Toggles — Enable Coded Agents (×2)       │ Enabled          │ Not set / Disabled │
│ C8  Product Toggles — Enable Apps AI Features        │ Enabled          │ Disabled           │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘

A.9.3  Objectives for responsible use of AI system                                           ⚠ 1
Your policy: P1 "aitl-22-nov-2026" · Included in policy: AI Capabilities And Safety Governance
┌──────────────────────────────────────────────────────┬──────────────────┬────────────────────┐
│ Conflict                                             │ Pack recommended │ Policy applied     │
├──────────────────────────────────────────────────────┼──────────────────┼────────────────────┤
│ C9  Agent Guardrail — Output Content Filtering (×6)  │ Enabled          │ Disabled / Not set │
└──────────────────────────────────────────────────────┴──────────────────┴────────────────────┘

NO CONFLICTS                                                                     18 requirements
OUTSIDE PLATFORM SCOPE — your auditor needs separate evidence for these          15 requirements
```

- **Status line**: `Not applied` when `Active == false`; `Observe` / `Mode not chosen` for an active pack, and mark that mode `(current)` after its name in APPLICATION MODE.
- **Mode texts are fixed** (the portal's words); only `<T>` / `<O>` change.
- **Conflicts by requirement**: one block per coverage clause with `Conflicts[]`, in catalog order, headed by `ClauseId`, the catalog `ClauseName` and `⚠ <its conflict count>`. `Your policy:` names the `P<i>` and live name of each deployed policy in those conflicts' `Policies[]` (`Your policies:` and comma-separated when several, with `(C<k>, …)` after each); `Included in policy:` = the catalog `DeploymentPolicies[].PolicyName` of the product(s). The table, numbering (`C1`… once by `ConflictId`, in clause order), values and `↳` rows follow [Conflicts with your existing policies](./apply-and-conflicts.md#conflicts-with-your-existing-policies) rules 5–6; the per-policy `DEPLOYED POLICY P<i>` blocks are not printed in this view.
- **Count check**: blocks = `R`; distinct `C` numbers = `N`; `NO CONFLICTS` = `T − R`.
- The ⚙ settings that will still need a value are not named here; the Enforce confirmation lists them ([full-apply § Step 4](../full-apply/impl.md#step-4--confirm)). The ✓ / ⚙ line keeps only its two counts.
- `ConflictStatus` `"unavailable"`: the `CONFLICTS NOT CHECKED` banner, no conflict blocks, and no apply offer in this run. `"evaluated"` with 0 conflicts: the ✓ banner, no `CONFLICTS TO RESOLVE` heading, and `NO CONFLICTS  <T> requirements`.

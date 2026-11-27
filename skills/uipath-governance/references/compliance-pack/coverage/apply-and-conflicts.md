# Coverage — Apply plan and conflicts

Part of the posture check: read [impl.md](./impl.md) first (commands, parsing, which view to render). This file: what an apply does to the admin's AOps policies, their deployed policies, and the conflicts.

**Output:** print the template filled in, in one fenced code block, with every section, box line and table row it defines ([SKILL.md Critical Rule 11](../../../SKILL.md#critical-rules)).

## If you apply / If you enforce

Rendered for case 1 (pack not applied) and for an active pack that is not enforced, as the WHAT HAPPENS TO YOUR AOPS POLICIES block followed by the CONFLICTS section, separated by a rule line so the conflicts never read as part of Observe:

```
WHAT HAPPENS TO YOUR AOPS POLICIES

  OBSERVE                                  (modes on only)
  No AOps policy is created, changed or deployed. <P1, P2 …> stay as they are. Agents that
  break a rule are reported, not blocked.

  ENFORCE                                  (modes off: APPLY)
  ✓ <count of Controls[].StatusAfterApply == "deployed"> settings will be applied
  ⚙ <sum of Clauses[].ManualConfigControlCountAfterApply> will still need a value only you can set: <their ControlDisplayNames>
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
  ✓ 52 settings will be applied
  ⚙ 5 will still need a value only you can set: Connector Allowlist, App Allowlist,
    App Blocklist, URL Allowlist, URL Blocklist
┌───────────────────┬────────────────┬───────┬──────────────────────┬──────────────────────────┐
│ Product           │ License type   │ Today │ On enforce           │ AOps policy after        │
│                   │                │       │                      │ enforce                  │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Assistant         │ Development,   │ —     │ Reuse, update,       │ Assistant Governance and │
│                   │ Studio Pro     │       │ deploy               │ Experience               │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Integration       │ No License     │ —     │ Create, deploy       │ Connector And Provider   │
│ Service           │                │       │                      │ Restrictions (11)        │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ AI Trust Layer    │ No License     │ P1    │ Reuse with P1's      │ AI Capabilities And      │
│                   │                │       │ values and your      │ Safety Governance        │
│                   │                │       │ C1–C15 choices;      │                          │
│                   │                │       │ deploy in place of   │                          │
│                   │                │       │ P1 (P1 not edited)   │                          │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Robot             │ Development,   │ —     │ Reuse, update,       │ Runtime Access And       │
│                   │ Studio Pro     │       │ deploy               │ Behavior Controls        │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Studio Web        │ No License     │ P2    │ Update in place (P2  │ Secure Development &     │
│                   │                │       │ is an ISO 27001      │ Code Quality Gates (10)  │
│                   │                │       │ policy)              │                          │
├───────────────────┼────────────────┼───────┼──────────────────────┼──────────────────────────┤
│ Studio            │ Development,   │ —     │ Reuse, update,       │ Secure Development &     │
│                   │ Studio Pro     │       │ deploy               │ Code Quality Gates       │
└───────────────────┴────────────────┴───────┴──────────────────────┴──────────────────────────┘
```

**What happens to your AOps policies — rules**

1. **OBSERVE first, then ENFORCE**, both whenever modes are on and the pack is not applied or not enforced (the admin picks the mode from this). Modes off: only the ENFORCE part, titled APPLY.
2. **OBSERVE** is one fixed paragraph, never a table: Observe writes nothing to the tenant's AOps policies. Name the deployed policies by `P<i>`; with none, drop the "stay as they are" sentence.
3. **ENFORCE table, columns fixed:** Product · License type · Today · On enforce · AOps policy after enforce. One row per `ApplyPlan[]` entry, in `DeploymentPolicies[]` order; entries merge into one row only when they are the **same policy** (`update` entries with the same `PolicyId`), their license types joined with ", ". Never merge `new` entries or different `PolicyId`s, even when their names match: each license type usually has its own policy (ISO 42001 on appsdevDefault: 11 entries, 11 policies). Every entry is in exactly one row. Print the product only on its first row and draw a row line only between products, so a product's rows read as one group.
   - **Product** = catalog `ProductDisplayName`. **License type** = the `DisplayName` coverage gives that identifier anywhere (`Policies[]`, `Conflicts[].Policies[]`, `EnforcedBy[]` `LicenseTypes[]`); when none does, the identifier split into words (`StudioPro` → `Studio Pro`, `NoLicense` → `No License`). Never substitute another license name (`StudioPro` is not "Automation Developer" unless coverage says so).
   - **Today** = `P<i>` of the deployed policy in that product and license type (the `DeploymentPolicies[].Policies[]` entry whose `LicenseTypes[].Identifier` includes the entry's `LicenseTypeIdentifier`); none → `—`. The names are in [Your deployed policies](#your-deployed-policies); don't repeat them here.
   - **On enforce**: `update` of the Today policy → `Update in place (P<i> is a <packName> policy)` · `update` of another policy with a Today policy → `Reuse with P<i>'s values and your C…–C… choices; deploy in place of P<i> (P<i> not edited)` (name the conflict numbers only when P<i> has conflicts) · `update` with Today `—` → `Reuse, update, deploy` (an earlier apply of this standard left that policy in Policy Library, not deployed) · `new` from the Today policy (`SourcePolicyId`) → `Create from P<i> with your choices; deploy in place of P<i> (P<i> not edited)` · other `new` → `Create, deploy`. Modes off: the same, without "your choices".
   - **AOps policy after enforce** = the entry's `PolicyName` verbatim — the title the policy has in Policy Library after the apply. The server leaves `PolicyName` out for some `update` entries (a policy reused from an earlier apply). Then write the standard's own title for that product — `catalog.json` `Data.DeploymentPolicies[].PolicyName`, joined by `ProductIdentifier` — with no tag in the cell, on every row (each row is its own policy; never `(same as above)`). Say it once under the table: `All <n> reuse a policy <packName> created on its earlier apply and kept in Policy Library, one per product and license type; none is created new. Their names there may carry a suffix such as (6).` — or `<k> of the <n> …` when only some rows are `Reuse`. For a `new` entry without a name: `New <catalog PolicyName>`. Never write "this standard's policy", "a policy", or an id.
4. The ✓ / ⚙ lines: ✓ on its own line, ⚙ on the next, never joined with `·`. Compute both numbers with the command below and name the ⚙ settings here once — not again elsewhere in the reply. In the [Enable view](./enable-view.md#enable-view), give only the two counts and end with `(listed before you confirm)`; the Enforce confirmation names them. Creates in the table (`Create…` rows' entries) + updates must equal `ApplyPlan.length`.

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
- Modes on: the admin chooses keep or update for every conflict before an Enforce apply ([full-apply § Modes on](../full-apply/impl.md#modes-on)); Observe changes none of them. Modes off: applying takes the standard's value for every conflict — say so before any apply confirmation, and name the count.
- An `update` entry is a policy this standard created earlier; it is one of the tenant's deployed policies only when it is in `DeploymentPolicies[].Policies[]`.
- A ✗ setting that is a conflict is listed once, in the conflict list, not again with a separate explanation.

## Your deployed policies

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

## Conflicts with your existing policies

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
┃    <modes on: To enforce, choose for each one: keep the current value or update to the       ┃
┃    standard's recommendation.>                                                               ┃
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
┃    To enforce, choose for each one: keep the current value or update to the standard's       ┃
┃    recommendation.                                                                           ┃
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
6. **Values** from `Lines[]` per the [line rules](./impl.md#line-rules): lines with the same `Recommended` collapse into one row, with `(×<n>)` after the setting when `n > 1` and their distinct `Current` values joined with ` / `. Each other distinct change of the same conflict is a `↳` sub-row, labelled with the line's `Setting` when it has a label, else the key's last segment as plain words (`traces-ttl-enforcement` → `TTL enforcement`, `sentiment-execution-stage` → `Execution stage`). Wrap a long value onto the next line inside its cell; never truncate a value.
7. **Count check before printing**: distinct conflict numbers = `Summary.ConflictCount` (a conflict in several blocks counts once); every `Lines[]` entry is covered by exactly one row or sub-row; the number of blocks = `<C>`.
8. **Banner and footer are fixed text.** The count goes in the banner's first line, in capitals with the word CONFLICTS, and the box uses the heavy border (`┏━┓ ┃ ┗━┛`) so it stands out from the light-bordered tables, and is the same width as them. Pick the banner's third line and the footer by modes (on / off). Modes on: no footer (the banner says it). Modes off: keep the footer.

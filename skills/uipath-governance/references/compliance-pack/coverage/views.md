# Coverage — Observe and Enforced views

Part of the posture check: read [impl.md](./impl.md) first (commands, parsing, which view to render). This file: the views for a standard that is applied, in Observe (case 0) or in Enforce.

**Output:** print the template filled in, in one fenced code block, with every section, box line and table row it defines ([SKILL.md Critical Rule 11](../../../SKILL.md#critical-rules)).

## Observe view

Rendered for case 0 (modes on, pack active, `Mode == "audit"`). It is the admin portal's Compliance Standards page for a standard in Observe: four coverage counts, then one policy card listing what Observe watches, requirement by requirement. Observe watches the standard's runtime checker rules, so the view is built from `catalog.json` (the rules) and coverage (what existing policies already enforce).

**Which requirements Observe covers** — `catalog.json` `Data.Clauses[]` with `Source` `"CHECKER"` or `"BOTH"`, in catalog order (call them the Observe requirements). `"AOPS"` requirements take effect only on Enforce.

**A requirement's settings**, in this order:
1. Each `EditorialPolicies[].Controls[]` entry whose `ControlId` equals the `ControlId` of one of the clause's own `Rules[]` — shown by its `DisplayName`. A rule that names a `ControlId` is that setting: show it once, as the setting, never again as a rule.
2. Each `Rules[]` entry with no `ControlId` — shown by its `Name`.

**A setting's status** — **Enforced** when an existing policy already sets it, else **Observed**:
- Enforced: the coverage clause with the same `ClauseId` has a `Controls[]` entry for the same `ProductIdentifier` and setting (match on `ControlId` when both carry one, else `ControlDisplayName` = the setting's `DisplayName`) with a non-empty `EnforcedBy[]`; or any coverage `Clauses[].Conflicts[]` entry matches the same product and setting the same way.
- A rule from step 2 is always Observed: no policy can enforce a checker rule.

**Counts** — `T` = the number of `catalog.json` `Data.Clauses[]` (every requirement; Outside platform scope is not counted). `O` = the number of Observe requirements. `P` (**Partly observable**) = Observe requirements with at least one Enforced setting. `F` (**Fully observed**) = `O − P`. `N` (**Not covered**) = `max(0, T − O)`. **Requirements coverage** = `round(F / T × 100)`%, `0%` when `T == 0`. Worked example: 21 requirements, 9 of them Observe, none with an Enforced setting → `F` 9, `P` 0, `N` 12, `43%`.

**Fallback (older catalog):** when no `Data.Clauses[]` entry carries `Source` (a server or bundle without checker data), or no requirement has a setting from the steps above, Observe has nothing to show from the catalog. Skip this view and continue with case 2 / 3.

Print it as one fenced code block, filled in:

```
<PackLongName>   ● Observing
Monitoring enforcement coverage and policy health for this tenant.
<tenantName>  ·  <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COVERAGE
┌────────────────────────────────┬────────────────────────────────┐
│ Fully observed                 │ Partly observable              │
│ <F>                            │ <P>                            │
│ of <T> requirements            │ Some settings not observable   │
├────────────────────────────────┼────────────────────────────────┤
│ Not covered                    │ Requirements coverage          │
│ <N>                            │ <pct>%                         │
│ Take effect on Enforce         │ <F> of <T> fully covered       │
└────────────────────────────────┴────────────────────────────────┘

POLICIES
┌─────────────────────────────────────────────────────────────────┐
│ <PackName> policy                                               │
│ Covers  [<ClauseId>] [<ClauseId>] [<ClauseId>] …                │
├─────────────────────────────────────────────────────────────────┤
│ SETTINGS                                                        │
│ <ClauseId> <ClauseName>                                         │
│   <setting name>                                   ● Observed   │
│   <setting name>                                   ● Enforced   │
│ <ClauseId> <ClauseName>                                         │
│   <setting name>                                   ● Observed   │
│ … every listed requirement                                      │
└─────────────────────────────────────────────────────────────────┘
```

Rules:
- The card lists every Observe requirement that has at least one setting, in catalog order, each followed by all its settings; never merge or truncate. A requirement with no setting is left out of the card but still counted in `O`. `Covers` lists exactly the `ClauseId`s the card shows, in the same order, wrapping onto the next line inside the box when long.
- The title is `<PackName> policy` (e.g. `UiPath ISO 27001 policy`). The heading line is `PackLongName`, else `PackName`.
- Status words are only **Observed** and **Enforced**, right-aligned in one column. No Impact, no ✓/✗/⟳/⚙ markers, no recommendation column: the view shows what Observe watches, not gaps.
- The four counts must satisfy `F + P + N == T`; check before printing.
- After the block, continue with the next actions of case 3, asked as in [Next action](./posture-view.md#next-action): the [If you enforce](./apply-and-conflicts.md#if-you-apply--if-you-enforce) block, then the pick list with `Enforce <packName>` first, any drift or manual-setting offer that applies, and `Show full details` last.

## Enforced view

The admin portal's Compliance Standards page for a standard in Enforce: four coverage counts, the standard's policies grouped by state, then the checks recorded as evidence. [full-apply § Report](../full-apply/impl.md#report) prints it after an Enforce apply, from `catalog.json` and the coverage read again in Verify.

**Requirements** — every `catalog.json` `Data.Clauses[]` entry (`T` of them). A requirement's settings are its `EditorialPolicies[].Controls[]`, each under its `ProductIdentifier`.

**A setting's status**, first match wins:
1. **Not applied** — its product is `unverifiable` in coverage `Data.DeploymentPolicies[]` (the standard's policy was deleted).
2. **Drifted** — a coverage `Clauses[].Conflicts[]` entry (any clause) has the same `ProductIdentifier` and setting (match on `ControlId` when both carry one, else `ControlDisplayName` = the setting's `DisplayName`).
3. **Needs configuration** — the coverage clause with the same `ClauseId` has a `Controls[]` entry for it (same match) whose `StatusAfterApply`, else `Status`, is `"manual"`.
4. **Enforced** — otherwise.

**Counts**, one per requirement from its settings' statuses: **Drifted** (`D`) when any setting is Drifted; else **Needs manual setup** (`M`) when any is Needs configuration; else **Fully enforced** (`F`) unless one is Not applied. A requirement with no product setting (checker rules only) counts as Fully enforced. A requirement with a Not applied setting and no other state counts in none, so `F + D + M` can be less than `T`. **Requirements coverage** = `round(F / T × 100)`%, `0%` when `T == 0`.

**Policies** — one card per `catalog.json` `Data.DeploymentPolicies[]` entry: title `PolicyName`, subtitle `<ProductDisplayName> policy`, plus `· <n> setting needs setup` / `· <n> settings need setup` when it has Needs configuration settings and `· <n> setting differs from the standard` / `· <n> settings differ from the standard` when it has Drifted ones. The card lists every requirement with a setting of that product, in catalog order, with `Covers` naming exactly those `ClauseId`s. Each card's group: **Unverifiable** when its product is `unverifiable`; else **Drifted** when it has a Drifted setting; else **Needs configuration** when it has one; else **Stable**. Print the groups in that order, each with its heading, and leave out an empty group.

**Evidence** — every `Rules[]` entry with no `ControlId`, across all requirements. They are recorded in Observe and Enforce alike; nothing blocks on them.

**Fallback:** a coverage response without `Conflicts[]` (older server) has no Drifted settings; read every other status as above.

```
<PackLongName>   ● Enforced
Monitoring enforcement coverage and policy health for this tenant.
<tenantName>  ·  <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COVERAGE
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ Fully enforced                       │ Drifted                              │
│ <F>                                  │ <D>                                  │
│ of <T> requirements                  │ Policy edited elsewhere              │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ Needs manual setup                   │ Requirements coverage                │
│ <M>                                  │ <pct>%                               │
│ Settings awaiting setup              │ <F> of <T> fully covered             │
└──────────────────────────────────────┴──────────────────────────────────────┘

POLICIES

<group heading: ⟳ Drifted | ? Unverifiable | 🔧 Needs configuration | ✓ Stable>
┌─────────────────────────────────────────────────────────────────────────────┐
│ <PolicyName>                                                                │
│ <ProductDisplayName> policy[ · <n> settings need setup][ · <n> settings     │
│ differ from the standard]                                                   │
│ Covers  [<ClauseId>] [<ClauseId>] …                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ SETTINGS                                                                    │
│ <ClauseId> <ClauseName>                                                     │
│   <setting DisplayName>                              ● Enforced             │
│   <setting DisplayName>                              ● Needs configuration  │
│     <ConfigLocation>                                                        │
│   <setting DisplayName>                              ● Not applied          │
│ … every requirement of this policy                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ DRIFTED FROM THE STANDARD                    (only when it has Drifted ones)│
│   <ControlDisplayName>                                                      │
│     <Setting>: <Current> → <Recommended>                                    │
└─────────────────────────────────────────────────────────────────────────────┘
… one card per policy of the group, then the next group

ALSO RECORDED AS EVIDENCE
<n> checks are recorded as evidence, not as policies. Recorded in both Observe and Enforce. Nothing is blocked.
  <ClauseId>  <rule Name>
  … every evidence check
```

Rules:
- Print every card in full: the portal collapses cards, a terminal can't, so nothing is hidden or summarized. A card with one setting says `SETTING`.
- Drifted settings are not setting rows: they go in the card's DRIFTED FROM THE STANDARD panel, with their conflict's `Lines[]` per the [line rules](./impl.md#line-rules). After the block, offer `'Correct the changed <packName> settings'` (case 3a′).
- A Needs configuration row carries its `ConfigLocation` from `catalog.json` on the next line. After the block, offer `'Configure the manual <packName> settings'` for them; an Unverifiable card gets the restore offer (case 3a).
- Status words are only **Enforced**, **Needs configuration** and **Not applied** on rows. No Impact column and no ✗/⟳/⚙ markers inside the cards.
- The offers above are asked after the block as one pick list, as in [Next action](./posture-view.md#next-action), with `Show full details` last.
- Leave out ALSO RECORDED AS EVIDENCE when there are no evidence checks; write `1 check is recorded as evidence, not as a policy.` for one.

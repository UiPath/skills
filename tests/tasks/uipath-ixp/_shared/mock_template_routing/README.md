# `mock_template_routing` — group-level vs field-level rewrite

## Why

When extraction scores are low, the improvement guide's first routing decision
(2a) is WHERE the rewrite belongs: an entire group failing together points at
the group's instructions (`groups update-prompts`), a single bad field inside
an otherwise healthy group points at that field's instructions
(`fields update-prompts`). Getting this wrong wastes a retrain either way —
rewriting group instructions to fix one field disturbs its healthy siblings,
and rewriting three fields one by one misses their common cause.

This overlay serves a project where the two cases sit side by side and neither
level of the payload answers alone.

List it SECOND in `template_sources` so its `mocks/uip` wins over the base
`mock_template`, whose mock fails every invocation.

## Fixture

Project `parcel_docs-6e2b91c8-ixp`, `ValidatedDocuments` 10, target `F1` 0.7,
two non-repeatable groups. Every `Annotations` is 10, so each field's
regression threshold collapses to the flat 0.1 — no noise-floor interference
with the routing question.

| group | `FieldId` | field | `F1` | correct rewrite |
|---|---|---|---|---|
| Shipping Address | `dddd000000000001` | Street | 0.400 | **group** |
| Shipping Address | `dddd000000000002` | City | 0.500 | **group** |
| Shipping Address | `dddd000000000003` | Postal Code | 0.400 | **group** |
| Invoice Header | `dddd000000000004` | Reference Number | 0.200 | **field** |
| Invoice Header | `dddd000000000005` | Issue Date | 0.800 | — |
| Invoice Header | `dddd000000000006` | Carrier Name | 1.000 | — |

Group rows: Shipping Address `F1` 0.433, Invoice Header `F1` 0.667.

Rows derive from explicit confusion matrices (TP/FP/FN): 4/6/6, 5/5/5, 4/6/6,
2/8/8, 8/2/2, 10/0/0. Group rows aggregate them (TP13 FP17 FN17 → 0.433;
TP20 FP10 FN10 → 0.667); `ErrorRate` is the integer error count `max(FP, FN)`
over `Annotations`; `ProjectScore` is the unweighted mean of per-field `F1`
(0.550).

## What it discriminates

**Both group rows sit below the 0.7 target — that is the point.**

- An agent routing on **group-row `F1` alone** reads both groups as "entire
  group low" and rewrites Invoice Header's group instructions to fix what is
  one field's problem — disturbing two fields at 0.8 and 1.0.
- An agent routing on **per-field `F1` alone** emits four field rewrites and
  misses that the three Shipping fields fail *together* — the shared-cause
  case the guide routes to `--groups`.

The correct read is 2a's order: check `FieldGroups` first, then look *inside*
a low group — every field low means the group instructions, one field low
means that field.

`get-taxonomy` is served (field names and existing group instructions);
graded artifacts are keyed by group name and field id, which need no join.

## Call log

Same as the base mock: one flat `uip <args>` line per invocation in
`calls.log`, CR/LF folded to spaces, so anchored `^uip\s+ixp …` criteria keep
working. `calls.jsonl` is not written by this overlay.

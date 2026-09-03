# Occurrence-resolving mock (Critical Rule 18)

Overlay for `../../smoke/occurrence_renumber.yaml`. List it **second** in
`template_sources`, after `../mock_template`, so `mocks/uip` here wins the PATH
shadow while the base template's `mocks/curl` and seeded sinks remain.

## Why this one resolves instead of responding

Every other mock in this folder answers a read and records the call. That is
enough when the graded thing is the command's *shape*. It is not enough here.

Critical Rule 18: `Occurrence` is scoped to the read that produced it. The server
returns annotation-prediction matched pairs first, so confirming one row of a
repeatable group moves it to the front and renumbers the rest on the next read.
An index carried across a write lands on a **different row** than the agent
meant.

In the call log those two calls are byte-identical. `--occurrence 2` looks the
same whether the 2 came from a fresh read or a stale one — only the server knows
which row it resolves to. So no regex over `calls.log` can grade this rule.

This mock therefore keeps the ordering the way the server does, resolves each
requested index against the **current** ordering, and appends the row it landed
on to `mocks/resolved.log`:

```
confirm occurrence=3 -> Pallet wrap
confirm occurrence=2 -> Premium freight surcharge
```

The task's criteria read row **names**, so a stale index fails by naming the
wrong row rather than by looking wrong.

## Fixture

Project `freight_docs-df33115f-ixp`, document `doc-freight-7`, repeatable group
`Invoice > Line Items` — the FULL label path, which is what `--group` takes.

| Document order | Row | State |
|---|---|---|
| 0 | Premium freight surcharge | unannotated, **invented** — not on the page |
| 1 | Steel bolts | unannotated, correct → must be confirmed |
| 2 | Pallet wrap | unannotated, correct → must be confirmed |
| 3 | Copper wire | **already annotated** |

Annotated rows sort first, so the first `get-predictions` reports:

```
Occurrence 0 = Copper wire            (matched pair)
Occurrence 1 = Premium freight surcharge
Occurrence 2 = Steel bolts
Occurrence 3 = Pallet wrap
```

## The walk that makes the trap fire

Confirming occurrence 3 (Pallet wrap) moves it into the annotated block, so the
next read is:

```
0 = Copper wire, 1 = Pallet wrap, 2 = Premium freight surcharge, 3 = Steel bolts
```

An agent that now reuses **occurrence 2** for Steel bolts — the index it read
before the write — confirms the invented surcharge instead, and Steel bolts never
gets confirmed. Two criteria fire on one mistake.

**Reordering `ROWS` without re-deriving this walk turns the trap into a no-op.**
Indices only shift for rows that sat *before* the confirmed one in the unannotated
block, so the invented row has to sit immediately before a target, and the agent
has to confirm the later target first.

Only one of the two sequential orders bites: confirming Steel bolts first leaves
Pallet wrap's index unmoved, correct by luck. The batched `--updates` path — the
one the skill recommends — is correct by construction. So this mock never fails a
correct run. `../check_occurrence_reread.py` covers the lucky-order gap by
grading the method: two or more per-occurrence calls require a `get-predictions`
between them.

## Two sinks, and a third

`calls.log` and `calls.jsonl` are both written in the base mock's exact format,
so anchored `^uip\s+ixp …` criteria keep working. (The `/bin/sh` overlays in this
folder write only the flat log; this one writes both because it is Python
already and `check_occurrence_reread.py` needs `argv` as a list — a
`--updates` payload with spaces is ambiguous on the flat line.)

`resolved.log` is the mock's own resolution trace, not a call log. It exists only
here, and it is **seeded** with a comment line for the same reason the base
template seeds its two sinks: coder_eval's `file_matches_regex` scores a missing
file `0.0` whatever `must_match` says, so an unseeded sink makes the two negative
guards on this file FAIL rather than pass vacuously. Fail-safe, but it would fail
runs that did nothing wrong. The seed line starts with `#` and every criterion on
this file is `^`-anchored to `confirm`/`unconfirm`, so it matches nothing.

State lives in `.annotated.json`. It is dot-prefixed on purpose: CI's
`upload-artifact` skips hidden files, and unlike the two sinks this is
scratch state, not evidence.

Fixture values — project, document, group path, and all four row names — are
hard-coded into the task's criteria. Change one here and update the task.

# Process Resolution Guide — the resolved process description

Rules and procedure. **The first phase of deriving an entity set is resolving the
process description against the relational tables the R2RML mapping exposes.**
Everything downstream — which entities this solution owns, which constraints it
enforces and how, which folds are even candidates — reads the result.

Read whole at the start of a bundle run, before the inspector's output is used for
anything. Router: [data-model-guide.md](data-model-guide.md).

## Why this comes first

An ontology says what the business world contains. It does not say who owns a record,
whether a value is written whole or filled in over time, or which two tables are
always read together. Those are facts about the **process**, and without them the
derivation has to guess or defer:

| Without the resolved description | With it |
|---|---|
| `locus` is a declared default; a hand-written list of systems of record | derived — a table the process only reads is a replica; one it inserts into is ours |
| `level` is parked as `null`, "needs the write sites" | the write sites are right here |
| the envelope records only what is *impossible* | co-reads in one step are real consolidation candidates |
| hop count is prose written after the model exists | counted before it |

Deferring these was the original design's mistake. The inputs already answer them.

## The three descriptions

| | Written against | By | Read by |
|---|---|---|---|
| **raw** | the business's own words | the user, or the agent from a brief | a person |
| **resolved** | the R2RML logical tables and columns | **the agent, in this phase** | `resolve-process.py`, then the derivation |
| **final** | the derived entities and fields | the agent, after the model exists | the genome's Workflow section |

The raw description names "the order's total value". The resolved one names
`EKKO.RLWRT`. The final one names `PurchaseOrder.PoTotalAmount`. Same step, three
vocabularies, and only the middle one exists before the entity set does.

**The resolved description is an input to the model. The final one is an output of
it.** Conflating them is what put the process description after the derivation.

## Resolving a step

The R2RML mapping gives the table set. Every `rr:logicalTable` is a table the query
interface can reach, and every `rr:column` under a `rr:predicateObjectMap` is a
column of it, already tied to the ontology predicate it realizes. That is the whole
vocabulary — nothing else is addressable.

For each step of the raw description, write one `**Data:**` line in this grammar:

```markdown
2. **Raise the exception** (input: a failed match row; output: an exception reference):
   a. Mint the reference from the invoice number and the run date
   b. Record the invoice number, when it arrived, and the variance
   **Data:** creates `ZINVEXC`;
   writes `ZINVEXC.EXCREF`, `ZINVEXC.BELNR`, `ZINVEXC.CPUDT`, `ZINVEXC.DIFFWR`
```

| Clause | Means | What it decides |
|---|---|---|
| `creates <TABLE>` | the step inserts a row | this solution is a candidate system of record for it |
| `writes <TABLE>.<COLUMN>, …` | the step sets these columns | the write sites — `state` vs `transition` |
| `reads <TABLE>.<COLUMN>, …` | the step needs these values | which columns are hot |
| `deletes <TABLE>` | the step removes a row | retention |
| `… via <TABLE>.<COLUMN> -> <TABLE>.<COLUMN>` | the values were reached by a join | **one hop, one round trip** |
| `filters <TABLE> on <COLUMN>` | a query narrowing a set | index pressure, federated-view fit |
| `decides on <TABLE>.<COLUMN>` | a branch or gateway turns on this value | **a bad value changes behaviour, so the constraint must at least be surfaced** |

`decides on` is the clause that earns its keep. A column the process merely carries
can be trusted; one a gateway branches on cannot, even when someone else owns it.
That distinction is what separates `monitor` from `assumed`, and nothing but the
process can supply it.

### Rules

1. **Name only tables and columns the R2RML mapping exposes.** `resolve-process.py`
   fails on anything else — a step that needs a table the mapping does not carry is
   a gap in the mapping, not a licence to invent a name.
2. **A traversal is written as the join it is**, source column to target column, so
   the hop is countable and checkable against the mapping's `rr:joinCondition`.
   Chained traversals are several `via` clauses, one round trip each.
3. **`creates` and `writes` are different claims.** A step that creates a row and
   sets three of its ten columns writes three. The other seven are filled later, and
   that is precisely what makes a constraint on them `transition` rather than `state`.
4. **State the cadence where the business states it.** `**Runs:** per instance,
   ~800/day` on a step is evidence for a fold; absent, the step is assumed
   infrequent and no fold is argued from it.
5. **Do not resolve a step that touches no table.** An over-declared step inflates
   the hop count and argues for a fold nobody needs.

## Running the resolver

```bash
python3 "<SKILL_DIR>/scripts/resolve-process.py" \
  --process "<PROCESS_RESOLVED_MD>" \
  --inventory "<BUNDLE_SLUG>-inventory.json" \
  --out access-patterns.json
```

It parses the `**Data:**` lines, checks every table and column against the
inventory's `triplesMaps`, and emits one record per step plus a per-table summary.
Exit 1 naming any reference the mapping does not carry.

**The resolver reads the description; it does not write it.** Resolving the raw
description into the table vocabulary is the agent's work, and it is a judgement —
which table realizes "the order's total value" is read off the mapping, but which
columns a step genuinely touches is read off the business.

### access-patterns.json

```jsonc
{
  "steps": [
    { "n": 2, "name": "Raise the exception",
      "creates": ["ZINVEXC"],
      "writes": [{ "table": "ZINVEXC", "column": "EXCREF" }],
      "reads": [], "deletes": [], "filters": [],
      "decides": [],
      "traversals": [{ "from": "ZINVEXC.EBELN", "to": "EKKO.EBELN" }],
      "runs": "per instance, ~800/day",
      "hops": 1 }
  ],
  "tables": {
    "ZINVEXC": { "created": true, "written": true, "readOnly": false,
                 "createdIn": [2], "writtenIn": [2, 5, 6],
                 "columnsWritten": ["EXCREF", "STATUS"],
                 "columnsCreatedWith": ["EXCREF", "BELNR"],
                 "decidedOn": ["DIFFWR"], "readIn": [1] }
  },
  "coReads": [{ "tables": ["EKKO", "LFA1"], "steps": [3] }],
  "hotPaths": [{ "step": 3, "hops": 2, "runs": "per instance, ~800/day" }]
}
```

## What the derivation does with it

| Signal | Decides | Rule |
|---|---|---|
| `tables[t].readOnly` | **`locus`** | a table the process never writes is a replica — the system of record is elsewhere. One it creates or writes is ours |
| `columnsCreatedWith` vs `columnsWritten` | **`level`** | a column set at creation is `state`-able; one written only by a later step means the record exists incomplete first, so the constraint is `transition` |
| `decidedOn` | **`level` on a replica** | a column a gateway branches on gets `monitor` — a bad value changes behaviour. One only carried gets `assumed` |
| `coReads` | **consolidation candidates** | two tables read in one step are a candidate, with the step as evidence |
| `hotPaths` | **fold evidence** | hops × cadence. Recorded, never acted on in Author mode |

**None of this is a fold.** Author mode still emits the normalized form
([normalization-guide.md](normalization-guide.md)); the access patterns turn
deferred rows into decided ones and turn an empty candidate list into an evidenced
one. The decision to denormalize remains a later phase's.

## Degrading without it

A bundle with no process description still derives. Every signal above falls back:

| Signal | Fallback |
|---|---|
| `locus` | default D1 — every entity a replica unless named in `systemsOfRecord` |
| `level` | `null`, `resolution: deferred` |
| consolidation candidates | R2RML co-location only (the source's layout, not this process's reads) |
| hot paths | none |

The run says so: *"no process description was resolved, so `locus` is defaulted and
every `level` is deferred."* That is the honest report, not a silent downgrade.

## Anti-patterns

1. **Writing the resolved description against entity names.** Those do not exist
   yet. The whole point of the table vocabulary is that it is available before the
   derivation runs.
2. **Letting the SHACL declare the enforcement decision.** Whether a constraint is
   enforced, surfaced or trusted is **genome's call**, made from the locus and the
   access pattern ([constraint-register-guide.md](constraint-register-guide.md)
   § Deriving the verdict). A bundle that pre-states it has made the decision the
   pipeline exists to make.
3. **Inventing a table or column the mapping does not carry.** The resolver fails,
   and it should: the gap is in the mapping.
4. **Omitting `decides on`.** Without it every replica constraint falls to
   `assumed`, and a value a gateway turns on gets trusted when it should be surfaced.
5. **Declaring a cadence the business did not state.** Fold evidence invented is
   worse than fold evidence absent.

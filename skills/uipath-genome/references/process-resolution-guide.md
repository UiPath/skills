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
| **raw** | the business's own words | **the user — this is the input** | a person |
| **resolved** | the R2RML logical tables and columns | **genome, in this phase — an output, never asked for** | `resolve-process.py`, then the derivation |
| **final** | the derived entities and fields | genome, after the model exists | the genome's Workflow section |

**Only the raw description is an input.** A bundle arrives as three ontology
artifacts and a prose process description; asking the user for a resolved one asks
them to do the step this phase exists to perform. `process-resolved.md` is written
to the working folder and ships as a deliverable beside `entities.json` and
`target.r2rml`.

The raw description names "the order's total value". The resolved one names
`EKKO.RLWRT`. The final one names `PurchaseOrder.PoTotalAmount`. Same step, three
vocabularies, and only the middle one exists before the entity set does.

**The resolved description is this phase's output and the derivation's input. The
final one is an output of the model.** Conflating them is what put the process
description after the derivation.

## Reading the raw description

The raw text does not name tables. Turning it into the table vocabulary is the
judgement this phase makes, and these are the only rules it needs.

1. **One numbered step in, one numbered step out.** Keep the business's own step
   names and order. A step the business describes but that touches no data is kept
   and left without a `**Data:**` line.
2. **Match a noun to a table through the mapping, not through its name.** "The
   supplier" is whichever `rr:logicalTable` a triples map with `rr:class ap:Supplier`
   reads. Two classes on one table means two nouns resolve to the same table — that
   is normal and says nothing about identity.
3. **Match an attribute to a column through the predicate.** "The order's total
   value" is the `rr:column` of the `rr:predicateObjectMap` whose `rr:predicate` is
   the property the ontology uses for it.
4. **A verb chooses the clause.** *Register / create / raise / open* → `creates`;
   *record / set / capture / write back / mark* → `writes`; *look up / fetch / read
   / check* → `reads`; *compare / decide / route on / depends on* → `decides on`
   beside the `reads`; *for each X matching* → `filters`; *archive / purge* →
   `deletes`.
5. **A possessive across classes is a traversal.** "the supplier's country" with
   `Supplier` and `Address` on different tables is one `via` clause per
   `rr:joinCondition` the mapping crosses. Two possessives in a row are two.
6. **Carry a cadence only when the business stated one.** "About 800 a day" becomes
   `**Runs:**`; "regularly" becomes nothing.
7. **Resolve nothing the mapping does not carry.** A step that needs an absent table
   is a gap in the mapping — report it; do not invent a name. The resolver fails on
   one anyway.

A step whose resolution is a guess gets the guess written down and flagged in the
report, not quietly dropped: an omitted step understates the hop count and argues
for a fold nobody needs.

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

## Re-resolving after a revision

A `target.r2rml` revision changes the vocabulary — folding two classes onto one
subject removes the join the old description traversed, and moving a logical table
removes the table name it used. **The resolved description is written against
`target.r2rml`, so a revision invalidates it.**

The order, every time:

1. revise `target.r2rml`;
2. re-run the inspector against it;
3. **re-resolve the raw description** against the new inventory, rewriting the
   clauses the revision changed — a traversal that the fold absorbed disappears, and
   its columns become plain `reads` on the surviving table;
4. re-run `resolve-process.py`;
5. re-derive.

**Skipping step 3 is silent.** `resolve-process.py` fails loudly on a table the
mapping no longer carries, but `derive-entities.py` accepts a stale
`access-patterns.json` without complaint and quietly loses the rows whose tables
have gone — taking `locus`, `level` and the fold evidence with them. Re-resolve
before re-deriving, and check that the hop count moved the way the revision
predicted.

## Anti-patterns

1. **Writing the resolved description against entity names.** Those do not exist
   yet. The whole point of the table vocabulary is that it is available before the
   derivation runs.
2. **Asking the user for a resolved description.** It is this phase's output
   (§ The three descriptions).
3. **Re-deriving after a `target.r2rml` revision without re-resolving**
   (§ Re-resolving after a revision).
4. **Letting the SHACL declare the enforcement decision.** Whether a constraint is
   enforced, surfaced or trusted is **genome's call**, made from the locus and the
   access pattern ([constraint-register-guide.md](constraint-register-guide.md)
   § Deriving the verdict). A bundle that pre-states it has made the decision the
   pipeline exists to make.
5. **Inventing a table or column the mapping does not carry.** The resolver fails,
   and it should: the gap is in the mapping.
6. **Omitting `decides on`.** Without it every replica constraint falls to
   `assumed`, and a value a gateway turns on gets trusted when it should be surfaced.
7. **Declaring a cadence the business did not state.** Fold evidence invented is
   worse than fold evidence absent.

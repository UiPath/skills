# R2RML + USAGE POLICY guide — the physical and behavior layers

The R2RML is read twice: parsed to derive the entity allow-list
`(rr:tableName, uipath:folderPath)` and injected **verbatim into the SQL
prompt**, where `rr:tableName` / `rr:column` / `rr:joinCondition` are the
agent's source of exact SQL identifiers. It also hosts the USAGE POLICY block —
prompt guidance colocated in the file (it can later migrate to a system prompt).

## 1. Mapping correctness rules

1. **One TriplesMap per selected/provisioned entity — exactly.** The
   `(rr:tableName, uipath:folderPath)` set is the runtime allow-list: adding an
   unprovisioned table breaks resolution; removing one deletes the entity from
   the agent's world. In IMPROVE mode the set is immutable.
2. **`rr:column` values are bare physical column names.** No SQL expressions,
   no arithmetic, no aliases (`"EnrollmentK12 + EnrollmentAges517"` is invalid).
   Only columns that exist on the Data Fabric entity.
3. **A `rr:joinCondition` for EVERY foreign key.** The single highest-leverage
   fix measured: ontologies shipped with zero joins added nothing; wiring FKs
   was worth up to +10 points alone. Each join's `rr:predicate` must be an
   ObjectProperty declared in the OWL. Relationship targets resolve by
   UUID/Id-field, never by name; cross-folder targets carry the target's folder
   key (record it in a comment).
4. **Predicates mirror the OWL** — same namespace, same local names; rename in
   both files or neither (gate-enforced).
5. **Correct `rr:datatype`** per column (see entity-schema-guide for the
   FieldDataType→xsd table); choice-set columns are `xsd:integer` NumberIds.
6. **Document surprising physical naming** — e.g. reserved words prefixed
   (`colId` = id, `colName` = name, `colDate` = date). One policy line; saves
   endless wrong-identifier SQL.
7. **Keep the mapping body boring** — section titles and per-construct
   one-liners only; knowledge belongs in the OWL, behavior in the policy block.
8. **Surgical joins may be appended as separate statements** — turtle allows
   re-opening a subject:
   ```turtle
   map:TM_child rr:predicateObjectMap [
       rr:predicate onto:child__parent ;
       rr:objectMap [ rr:parentTriplesMap map:TM_parent ;
                      rr:joinCondition [ rr:child "ParentId" ; rr:parent "Id" ] ] ] .
   ```

## 2. The USAGE POLICY block

One leading `#` comment block, **≤30 non-empty lines**, delimited by `# ====`
rules. It is the behavior layer: imperative rules that teach the agent *how to
use* the constructs. Every line references constructs that exist; it states
rules, never facts.

Section order that worked (highest priority first — models weight early lines):

```
# ============================================================================
# USAGE POLICY  (how to use the constructs; facts live on the OWL properties)
# ============================================================================
# SQL DIALECT LIMITS - the query engine REJECTS: CAST(...), and column
#   arithmetic inside WHERE (filter on plain columns; simple division or
#   multiplication in SELECT is fine).            [verify per QE version]
# NEVER append a default LIMIT (no habitual LIMIT 100/10): list questions
#   return EVERY matching row; LIMIT 1 only for single-answer superlatives.
# JOIN GRAPH (join only what the question needs):
#   <child.col = parent.col, one line per FK>
# ROUTING (canonical columns):
#   <ambiguous phrase -> table.column, SIDED by question type where duplicated>
# GRAIN DISCIPLINE: <per-table dedup rules, e.g. time-series -> SELECT DISTINCT>
# OUTPUT DISCIPLINE:
#   answer with ONE final query - never submit exploration results or hard-coded
#   ids discovered by exploration; no DISTINCT unless uniqueness is asked;
#   for ranked/ordered asks return ONLY the requested column(s).
# SUPERLATIVE/COMPARATIVE asks -> ORDER BY the measure, LIMIT 1, deterministic
#   tie-break; IS NOT NULL only for ascending ranks on nullable measures.
# LITERALS are case- and format-sensitive - copy exactly as annotated.
# ============================================================================
```

Content rules, each traceable to measured failures:

- **Dialect limits first.** Engine-rejected constructs (CAST,
  arithmetic-in-WHERE) caused up to 40% of one model's failures; say what to do
  instead, not just what to avoid. These are platform truths — re-verify per
  query-engine version.
- **The default-LIMIT ban must name the habit** ("no habitual LIMIT 100") —
  generic "avoid LIMIT" gets ignored; agents' inner prompts push them toward it.
- **Routing must be sided:** when an attribute exists in two tables, give the
  canonical column *per question type* ("county for FRPM questions →
  Frpm.CountyName; directory questions → Schools.County"). A single global
  winner mis-routes half the cases.
- **Row-set discipline outranks column minimalism:** consumers tolerate extra
  columns far better than changed row sets — invented filters, DISTINCT, and
  LIMIT are the killers.
- **Anti-exploration:** agents that wander (`SELECT DISTINCT type LIMIT 10`)
  must be told the final answer is one query and ids from exploration may not be
  hard-coded.
- **Conditional rules carry their condition inline** ("IS NOT NULL only for
  ascending ranks") — see owl-authoring-guide §4.

## 3. Publishing mechanics

- `uip ontology files put <name> r2rml <file> --content-type text/turtle`
  (and `owl` for the .ofn); REST `PUT` is unreliable — use the CLI.
- Fetching for verification: force UTF-8 (`text/turtle` responses default to
  Latin-1 in many HTTP clients — non-ASCII mojibakes and byte-comparison lies).
  Prefer ASCII-only file content.
- After every publish: fetch and byte-compare.

## 4. Validation gates (before any publish)

1. Turtle parses (rdflib or equivalent).
2. `(rr:tableName, uipath:folderPath)` set matches the provisioned allow-list
   exactly.
3. Every `rr:column` exists on its Data Fabric entity.
4. Every `rr:predicate` and `rr:class` is declared in the OWL.
5. Policy block ≤30 non-empty lines; body comments bounded (no dumps).
6. Publish → fetch → byte-compare (UTF-8).

## 5. Failure taxonomy (IMPROVE mode)

Classify each wrong answer before fixing anything:

| Class | Signal | Fix location |
|---|---|---|
| Knowledge | wrong column/literal/scale/code chosen | OWL fact (verified) |
| Behavior | right knowledge, wrong conduct (extra filters, LIMIT, DISTINCT, concatenation, exploration output) | policy line |
| Mapping | missing join, wrong column binding, wrong datatype | R2RML |
| Engine limit / data quirk | valid SQL rejected, or the expected answer itself is eccentric | accept & note; do not distort the package |

Fix **rule expression before adding content** — most regressions come from how
an existing rule is phrased, not from missing facts. When re-measuring is
possible, keep the best-scoring package and roll back regressions.

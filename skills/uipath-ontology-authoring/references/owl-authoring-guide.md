# OWL authoring guide — the knowledge layer

The OWL (.ofn, OWL 2 QL) is read by the consuming agent as **text**. It works
exactly as well as its facts are (a) true, (b) placed on the construct they
describe, (c) phrased so a model can act on them. The profile must stay QL and
the file must parse, but the reader is a language model, not a reasoner.

**Division of labor:** facts live here; behavior (routing, join/output
discipline) lives in the USAGE POLICY block; physical correctness lives in the
R2RML. Never narrate behavior here; never bury facts in the policy.

## 1. Skeleton and rules of form

```
Prefix(:=<http://.../ontology/<name>#>)
Prefix(owl:=...) Prefix(rdf:=...) Prefix(rdfs:=...) Prefix(xsd:=...)

Ontology(<http://.../ontology/<name>>
  Annotation(rdfs:comment "<one-paragraph domain summary>")

  Declaration(Class(:Order))
  AnnotationAssertion(rdfs:label :Order "order")
  AnnotationAssertion(rdfs:comment :Order "<what one row is; the grain; the key>")

  Declaration(DataProperty(:order__Total))
  DataPropertyDomain(:order__Total :Order)
  DataPropertyRange(:order__Total xsd:decimal)
  AnnotationAssertion(rdfs:label :order__Total "order total")
  AnnotationAssertion(rdfs:comment :order__Total "<meaning / values / format>")

  Declaration(ObjectProperty(:order__customer))
  ObjectPropertyDomain(:order__customer :Order)
  ObjectPropertyRange(:order__customer :Customer)
  AnnotationAssertion(rdfs:comment :order__customer "Links an order to its customer. FK: Order.CustomerId -> Customer.Id.")
)
```

- One `Declaration` + `rdfs:label` + (where it earns its place) one
  `rdfs:comment` per construct. Never a second comment elsewhere about the same
  thing.
- `rdfs:label` = the natural business phrase a user would say ("number of test
  takers", "charter funding type"). Labels are the synonym channel — they drive
  NL→property resolution.
- Every FK gets an `ObjectProperty` with domain/range, even though the mapping
  layer operationalizes it.
- Property IRIs must match the R2RML `rr:predicate` IRIs exactly (gate-enforced).
- Booleans: note "compare true/false, never 1/0" where the store is boolean;
  choice sets: the stored value is an integer NumberId — record the
  NumberId↔label map in the comment.

## 2. OWL 2 QL profile — the hard fence

Annotations are profile-neutral. These constructs are **forbidden** (no reasoner
will catch you — `uip ontology verify` is syntactic-only — so treat this as a
blacklist to scan for):

`DataOneOf`, `ObjectOneOf`, `ObjectUnionOf`/`DataUnionOf`,
`ObjectAllValuesFrom`/`DataAllValuesFrom`, `ObjectHasValue`/`DataHasValue`,
`ObjectHasSelf`, all cardinality restrictions,
`FunctionalObjectProperty`/`FunctionalDataProperty`/`InverseFunctionalObjectProperty`,
`TransitiveObjectProperty`, `HasKey`, negative assertions.

Value domains therefore go in **annotation text**, never as `DataOneOf`
enumerations. QL-inexpressible constraints ("exactly one") are recorded as
comments.

## 3. The seven fact types that move accuracy

Each earned measured questions in the source campaign; each must be verified
against the actual data first (data-verification-guide.md).

1. **Grain of every class.** What one row is, and whether multiple rows exist
   per business entity. *"TIME SERIES: ~5 dated rows per team (1458 rows / 288
   teams)"* fixed whole failure families. State the consequence ("a per-team
   question returns duplicates unless DISTINCT").
2. **Value domains for low-cardinality columns** — exact, complete,
   case-sensitive literals: `'Directly funded' | 'Locally funded' | 'Not in CS
   funding model' (case-sensitive)`. Truncated or paraphrased literals produce
   SQL that filters on wrong values.
3. **Code lists** — cryptic codes with their documented meanings, on the
   property that carries them: `'A' = contract finished, no problems | 'B' =
   finished, not paid | 'C' = running, OK | 'D' = running, in debt`. Include the
   phrase-to-code bridge ("'running contract' means status IN ('C','D')").
4. **Formats and scales** — zero-padding (`'0040'`), stored fraction vs percent
   ("stored 0–1; a 'Percent (%)' answer expects count*100/enrollment"),
   date/timestamp shapes ("text 'YYYY-MM-DD HH:MM:SS'; year comparisons work
   lexically"), sign conventions ("longitude negative for all rows").
5. **Cryptic column semantics** — `A11` = average salary, `A13` = unemployment
   rate 1996. Source from the dataset's own documentation, never from example
   answers.
6. **Disambiguation between lookalikes** — `GSoffered` vs `GSserved`, League.name
   vs Country.name, mailing vs physical address. Say *which phrase maps to which
   property*.
7. **Domain semantics that phrases imply** — "'eligible for loans' means
   disposition type = 'OWNER' (a right, NOT the existence of a loan)". This is
   the ontology's real job: business meaning the schema alone cannot show.
   Source: the author interview.

NULL behavior belongs with a condition (§4): "NULL for ~600 rows; NULLs sort
last in DESC, so highest-X needs no filter; add IS NOT NULL only when ranking
ascending."

## 4. Rule expression — how correct facts go wrong

A correct fact stated as an unconditional-sounding rule **regresses** questions:

- ✗ "filter `sname IS NOT NULL` for satscores-only questions" → applied to
  joined queries, broke them.
- ✓ "school rows have sname populated; district rows have sname NULL; the
  cds→CDSCode join keeps school rows automatically — **when joining, add no
  rtype or sname filters**."

Pattern: **state the fact, state the condition, state the non-action
explicitly.** Expect *filter invention*: documenting a discriminator column
(rtype, StatusType) tempts the model to filter on it — pair every such fact with
its bounding non-action, and keep the global "no filters the question didn't ask
for" rule in the policy layer.

## 5. Provenance and updates

- Add "Maps <Entity>.<Field>" provenance in comments where it aids the mapping.
- When updating an existing ontology: **upsert** (replace the construct's
  existing comment or insert after its label) — never duplicate, and never drop
  a verified fact you can't attribute a removal reason to.

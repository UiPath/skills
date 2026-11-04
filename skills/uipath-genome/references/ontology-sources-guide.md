# Ontology Sources Guide — detecting and reading the bundle

Catalog and procedure. How the three inputs of an ontology bundle are recognised,
what each one contributes, and the inventory contract everything downstream reads
instead of re-reading them.

Router: [data-model-guide.md](data-model-guide.md).

## Detection

Run against every path the request gives, and against the folder holding the ontology
file. Never search the disk beyond the paths given.

| Signal | Artifact | Role |
|---|---|---|
| `.ofn`; or a file whose first non-comment line matches `Prefix(` / `Ontology(` | OWL, functional syntax | conceptual schema |
| `.owl`, `.ttl`, `.rdf` carrying `owl:Class` / `owl:ObjectProperty` declarations | OWL, other serialization | conceptual schema |
| `.r2rml`, `.r2rml.ttl`; or Turtle declaring `rr:TriplesMap`, `rr:logicalTable` | R2RML | source↔conceptual mapping |
| `.shacl`, `.shapes.ttl`; or Turtle declaring `sh:NodeShape` / `sh:property` | SHACL | constraints on the conceptual level |

One Turtle file can hold more than one of these. Classify by the vocabulary present,
not by the extension: a file declaring both `sh:NodeShape` and `rr:TriplesMap` is
read as both.

**A bundle is any one of the three.** All three is the designed case; fewer is
handled below.

## What each input contributes

| Contributes | OWL | R2RML | SHACL |
|---|---|---|---|
| which entities exist | ✔ classes | — | ○ node shapes, when no OWL |
| which fields exist | ✔ datatype properties | ✔ column mappings | ○ property shapes |
| relationships | ✔ object properties | ✔ join conditions | ○ `sh:class` |
| field **types** | ○ property ranges | ✔ column SQL types | ✔ `sh:datatype` |
| field **lengths and bounds** | — | ✔ column declarations | ✔ `sh:maxLength`, `sh:minInclusive` |
| functional dependencies | ✔ functional properties, `owl:hasKey` | ✔ logical tables, keys | ✔ `sh:maxCount 1` |
| closed value sets | ○ `owl:oneOf` | — | ✔ `sh:in` |
| required-ness *(as a domain claim)* | ○ cardinality restrictions | — | ✔ `sh:minCount` |
| human labels | ✔ `rdfs:label` | — | ✔ `sh:name` |
| source provenance | — | ✔ logical table and column | — |

✔ primary source · ○ fallback

## Missing inputs

Proceed and say what cannot be derived. Never substitute a guess for a missing input.

| Missing | Still derivable | Lost |
|---|---|---|
| SHACL | the entity set, relationships, types from ranges | every constraint row; the register holds only renames. Field options default to permissive — no `isRequired`, no `lengthLimit`, no bounds |
| R2RML | the entity set from OWL, constraints from SHACL | source provenance on every field; column-derived lengths and precisions; the FD evidence the source's own decomposition carries; **the `target.r2rml` baseline** — later phases have no diff anchor |
| OWL | entities from `sh:NodeShape`, fields from property shapes | class hierarchy, `owl:hasKey`, functional-property FDs, the n-ary reification signature (§ Reified relations) |

**No R2RML is the serious one.** Without it there is no baseline document, so the
later phases lose the mechanism that makes their decisions reviewable as a diff. Say
so explicitly, and offer to emit a `target.r2rml` synthesized from the ontology so a
baseline exists even though it was never executable against a source.

## Reified relations — read before synthesizing a junction

OWL supports only binary relations. An n-ary relation, or a binary relation that
carries its own attributes, is modelled by **reification**: a new class is introduced
whose instances link to the participants through accessor properties, and the
relation's attributes become datatype properties of that class. This is the W3C
best-practice pattern ([Defining N-ary Relations on the Semantic Web](https://www.w3.org/2001/sw/BestPractices/OEP/n-aryRelations-20060323)).

So an ontology can already contain its junctions, and they are not bare.

**Detection — a class is a reified relation when all of these hold:**

1. it has ≥2 functional object properties whose ranges are different classes;
2. those properties are the only object properties it has;
3. it has no `owl:hasKey` of its own over a datatype property.

**The rule that follows:**

| In the ontology | Emit | `derivation` |
|---|---|---|
| a reified relation class, with or without extra datatype properties | an entity, with a `RELATIONSHIP` per participant **and its attribute fields** | `direct` — the class is the junction |
| a bare many-to-many object property, no reifying class | a synthesized junction with exactly two `RELATIONSHIP` fields | `junction` |

Getting this wrong loses data in the common case: `Student ⟷ Course` reified as
`Enrollment` carries a grade and a date, and synthesizing a bare bridge beside it
silently drops both. The inspector reports every class matching the signature under
`reifiedRelations`; the derivation must consult it before synthesizing anything
([entity-derivation-guide.md § Junctions](entity-derivation-guide.md)).

When the signature matches but the class also carries an `owl:hasKey` or three or
more participants, report it and emit `direct` without synthesizing — a reviewer
decides.

## The inspector

One deterministic read of all three inputs into one JSON document.

```bash
python3 "<SKILL_DIR>/scripts/ontology-inspect.py" \
  --ontology "<ONTOLOGY_FILE>" \
  --r2rml "<R2RML_FILE>" \
  --shacl "<SHACL_FILE>" \
  --out "<BUNDLE_SLUG>-inventory.json"
```

Every flag is optional except `--out`; a bundle missing an input omits its flag and
the inventory records the omission under `inputs`. Exit 0 on a parse; exit 1 with one
line per failure.

**Read the inventory, not the sources.** The derivation, the register and every later
phase consume `<slug>-inventory.json` only. Three reasons: the parser limits below are
then stated once and visible rather than rediscovered; the derivation is reproducible
from an artifact a reviewer can read in full; and a bundle too large for one context
still yields a derivation, because the inventory is far smaller than its sources.

### Inventory contract

```jsonc
{
  "inputs": { "ontology": "<path|null>", "r2rml": "<path|null>", "shacl": "<path|null>" },
  "prefixes": { "<prefix>": "<iri>" },
  "classes": [
    { "iri": "<IRI>", "label": "<rdfs:label|null>", "comment": "<rdfs:comment|null>",
      "superClasses": ["<IRI>"], "hasKey": [["<IRI>"]] }
  ],
  "datatypeProperties": [
    { "iri": "<IRI>", "label": "<...>", "domain": ["<IRI>"], "range": "<XSD_IRI|null>",
      "functional": true }
  ],
  "objectProperties": [
    { "iri": "<IRI>", "label": "<...>", "domain": ["<IRI>"], "range": ["<IRI>"],
      "functional": false, "inverseFunctional": false }
  ],
  "reifiedRelations": [
    { "iri": "<IRI>", "participants": ["<OBJECT_PROPERTY_IRI>"], "attributes": ["<DATATYPE_PROPERTY_IRI>"] }
  ],
  "shapes": [
    { "iri": "<IRI>", "targetClass": "<IRI|null>",
      "properties": [
        { "path": "<IRI>", "datatype": "<XSD_IRI|null>", "minCount": 1, "maxCount": 1,
          "maxLength": null, "minLength": null, "pattern": null,
          "minInclusive": null, "maxInclusive": null, "in": ["<VALUE>"],
          "nodeKind": null, "class": null, "name": null,
          "unsupported": ["<SHACL_PREDICATE>"] }
      ] }
  ],
  "triplesMaps": [
    { "iri": "<IRI>", "logicalTable": "<TABLE|null>", "sqlQuery": "<SQL|null>",
      "subjectClass": "<IRI|null>",
      "predicateObjectMaps": [
        { "predicate": "<IRI>", "column": "<COLUMN|null>",
          "parentTriplesMap": "<IRI|null>",
          "joinConditions": [ { "child": "<COLUMN>", "parent": "<COLUMN>" } ] }
      ] }
  ],
  "parserNotes": ["<one line per construct seen but not understood>"]
}
```

`parserNotes` is load-bearing. Every construct the parser recognised as syntax but
could not interpret produces a line, and the derivation copies them into the
register's `notCovered`. Silence about an unparsed axiom is how a constraint
disappears.

## Parser limits

Stated once, here, so no downstream file has to rediscover them. The inspector uses
the Python standard library only — no `rdflib`, no reasoner — and reads a documented
subset.

**OWL functional syntax.** Recognised: `Prefix`, `Ontology`, `Declaration` of
`Class` / `ObjectProperty` / `DataProperty`, `SubClassOf` (named superclass only),
`ObjectPropertyDomain`, `ObjectPropertyRange`, `DataPropertyDomain`,
`DataPropertyRange`, `FunctionalObjectProperty`, `InverseFunctionalObjectProperty`,
`FunctionalDataProperty`, `HasKey`, `AnnotationAssertion` with `rdfs:label` and
`rdfs:comment`. Cardinality restrictions inside `SubClassOf` are read for
`ObjectMinCardinality` / `ObjectMaxCardinality` / `DataMinCardinality` /
`DataMaxCardinality` with a named property and an integer.

**Not recognised, and reported in `parserNotes`:** `EquivalentClasses`,
`DisjointClasses`, class expressions beyond a named class, `ObjectUnionOf`,
`ObjectIntersectionOf`, property chains, annotations other than label and comment,
and anything requiring reasoning. **No inference is performed** — asserted axioms
only, so a domain inherited through a superclass is not propagated.

**Turtle (R2RML and SHACL).** A constrained reader: prefixed names, IRIs in angle
brackets, string and integer literals, `;` and `,` continuations, and blank-node
property lists `[ … ]` nested one level. Collections (`( … )`) are read only as the
object of `sh:in` and `HasKey`. Not recognised: nested blank nodes beyond one level,
`@base`, long literals with embedded braces, reification, named graphs.

**When a parse limit bites**, the inspector exits 0, records the construct in
`parserNotes`, and continues. It never guesses a value. A bundle with many notes is a
bundle whose derivation is incomplete — report the count before anything else.

## Anti-patterns

1. **Re-reading the source files during derivation.** The inventory is the contract;
   a second reading diverges from it and the derivation stops being reproducible.
2. **Treating a `parserNotes` line as noise.** Each one is a construct the business
   wrote down and the model does not carry.
3. **Synthesizing a junction without checking `reifiedRelations`** (§ Reified
   relations). Drops the relationship's attributes.
4. **Inferring anything** — a superclass's domain, an equivalent class's members, a
   range from usage. The inspector asserts only what is written.
5. **Editing `source.r2rml`.** It is the baseline and the only artifact still
   checkable against the source database ([data-model-guide.md § Artifacts](data-model-guide.md)).

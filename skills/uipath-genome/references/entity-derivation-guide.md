# Entity Derivation Guide — inventory to entity set

Rules. How the inventory becomes entities, fields, relationships and junctions, and
how every emitted object records where it came from.

Read whole. Router: [data-model-guide.md](data-model-guide.md). Input contract:
[ontology-sources-guide.md § Inventory contract](ontology-sources-guide.md).

The tool that applies these rules is `scripts/derive-entities.py`. The rules are here
because a reviewer judges the output against them, and because the tool's defaults
are arguments the genome has to be able to state.

## The one-way doors

Three decisions in this file cannot be revisited cheaply once made
([data-model-guide.md § Commitment ladder](data-model-guide.md)):

1. **the naming convention** — fix it before the first name is emitted;
2. **entity identity** — what counts as one entity; every register row and component
   id keys on it;
3. **`numberId` per choice value** — immutable once deployed.

Everything else here is recomputed free on a re-run.

## Classes and properties

| Inventory | Emits | Notes |
|---|---|---|
| a class with ≥1 datatype property mapped to it | an entity | a class with none is a junction candidate, not an entity |
| a class in `reifiedRelations` | an entity with a `RELATIONSHIP` per participant plus its attribute fields | § Junctions — never also synthesize a bridge for it |
| a datatype property | a field on each class in its domain | a property with no domain and no shape targeting it goes to `notCovered` |
| an object property, functional or `sh:maxCount 1` | a `RELATIONSHIP` on the **many** side | lives on the child, points at the parent; no reverse field exists |
| an object property, many-to-many | a synthesized junction entity | § Junctions |
| `rdfs:label` / `sh:name` | `displayName`, and the `displayField` candidate | |
| `rdfs:comment` | `description`, truncated to 512 characters | a truncation is a register row |
| `owl:hasKey` or `owl:InverseFunctionalProperty` over **one** datatype property | `isUnique: true` on that field | a composite key cannot be expressed — § Composite keys |
| a class with no property of any kind | nothing; a `notCovered` row | |

**A property in several domains becomes a field on each.** That is duplication the
ontology asked for; it is not a consolidation decision. Record it on each field's
provenance so the coverage index shows the class→entities fan-out.

## Object properties and direction

`RELATIONSHIP` is single-valued, child→parent, with no reverse field. So direction is
forced by cardinality, not chosen:

| Cardinality | Field lives on | Points at |
|---|---|---|
| many-to-one (functional on the subject) | the subject's entity | the range class |
| one-to-many (inverse-functional) | the **range** class's entity | the subject's class |
| one-to-one (both) | the subject's entity | the range class; record the arbitrary choice |
| many-to-many | neither — a junction | § Junctions |

A one-to-one picks a side. The pick is arbitrary and must be a register row with
`resolution: default-applied`, so a reviewer can flip it.

## Junctions

**Consult `reifiedRelations` first.** OWL has no n-ary relations, so an ontology that
needs a relationship to carry attributes reifies it into a class, and that class is
already the junction ([ontology-sources-guide.md § Reified relations](ontology-sources-guide.md)).

```
reifiedRelations contains the class?  ──yes──▶  emit it as an entity, derivation: direct
          │                                      RELATIONSHIP per participant
          no                                     its datatype properties become fields
          ▼
many-to-many object property?  ──yes──▶  synthesize a junction, derivation: junction
          │                               exactly two RELATIONSHIP fields
          no                              from[] = both classes AND the property IRI
          ▼
      ordinary RELATIONSHIP
```

A synthesized junction is named `<Subject><Object>` in the convention of § Naming,
carries `because` stating which property forced it, and has **no other fields** — a
bare bridge is the faithful rendering of a relationship the ontology modelled without
attributes.

**What the junction cannot do.** `isUnique` is per field, so a junction cannot state
"at most one link per pair". That constraint is `expressible: no` and lands as
`transition` or `assumed` ([constraint-register-guide.md](constraint-register-guide.md)).
Emit the register row at the same time as the junction — a junction without that row
is a silent loss of a constraint the ontology stated.

## Composite keys

`owl:hasKey` over two or more properties has no Data Fabric counterpart. Emit no
field option, and write one register row with `expressible: no`, `candidate:
transition`, naming the properties. Do not approximate it with `isUnique` on one of
them — that enforces something the ontology did not say.

## Types

From `sh:datatype` when a shape gives one, else the property's `rdfs:range`, else the
R2RML column's SQL type, else `STRING` with a register row.

| XSD | Emit | Never emit |
|---|---|---|
| `xsd:string` ≤4000 | `STRING` + `lengthLimit` | |
| `xsd:string` >4000 | `MULTILINE_TEXT` | |
| `xsd:integer`, `xsd:int`, `xsd:long`, `xsd:short` | `DECIMAL` + `decimalPrecision: 0` | `INTEGER`, `BIG_INTEGER` |
| `xsd:decimal`, `xsd:float`, `xsd:double` | `DECIMAL` + `decimalPrecision` | `FLOAT`, `DOUBLE` |
| `xsd:boolean` | `BOOLEAN` | |
| `xsd:date` | `DATE` | |
| `xsd:dateTime`, `xsd:dateTimeStamp` | `DATETIME_WITH_TZ` | `DATETIME` |
| `xsd:anyURI`, opaque identifier | `STRING` | `UUID` |

The right column is accepted by the tenant API, refused by `--local`, and renders
broken in the Data Fabric UI. The authoritative type surface is
`uipath-platform` → `references/data-fabric/entity-schema.md`; this table is the
*mapping from XSD*, which that skill does not own.

`decimalPrecision` with no evidence defaults to `0` and is a register row. A money
field the ontology does not mark is the commonest miss — `sh:maxInclusive` with two
decimal places, or an R2RML column of `DECIMAL(n,2)`, is the evidence to look for.

`defaultValue` is **a string for every type** — `"0"`, never `0`.

## Naming

| Level | Rule |
|---|---|
| Entity project | letters, digits, `_`, `-` |
| Entity | `^[a-zA-Z][a-zA-Z0-9_]{2,99}$` — underscores legal, hyphens not |
| **Field** | `^[a-zA-Z][a-zA-Z0-9]{2,99}$` — **no underscores** |

Also: a field name cannot equal its entity name ignoring case; `Id`, `CreatedBy`,
`CreateTime`, `UpdatedBy`, `UpdateTime` and `RecordOwner` are reserved; names are
unique within a batch ignoring case; entity names are unique solution-wide; at most
10 `MULTILINE_MAX` fields per entity.

**The convention**, applied in order and fixed before the first name:

1. take the IRI's local name (after the last `#` or `/`);
2. strip a leading `has`, `is`, `had` when what remains is ≥3 characters;
3. split on `_`, `-`, space and camel-case boundaries;
4. PascalCase the parts and concatenate;
5. drop every character outside `[A-Za-z0-9]`;
6. if it now starts with a digit, prefix `N`; if shorter than 3 characters, suffix
   `Fld` (field) or `Ent` (entity);
7. if it equals the entity name ignoring case, suffix `Value`;
8. if it collides with a name already emitted in that scope, suffix `2`, `3`, … in
   emission order.

**Every rename is a register row** and every collision suffix is a register row with
both IRIs. The IRI is the identity; the Data Fabric name is a rendering of it. A
silent collision is how two ontology properties become one column.

## Cycles

Build the directed graph: entities as vertices, `RELATIONSHIP` fields as edges
child→parent.

1. **Discard self-references** — an edge from an entity to itself. They are legal
   (`Employee.manager → Employee`) and are emitted normally; they are simply removed
   before the cycle check.
2. **Any remaining cycle fails the run**, naming every member. A cycle means the
   ontology needs further normalization before it can be modelled.

This is not only modelling taste. `resource.dependencies` in the solution is a real
dependency graph, so an entity cycle is a cycle in the solution's own resource graph
([datafabric-emission-guide.md § Hand-authored resource shape](datafabric-emission-guide.md)).

A junction produces a diamond (`A → J ← B`), not a cycle, so many-to-many passes.

## Provenance

The ontology↔Data Fabric mapping is **many-to-many in both directions**: N classes can
fold into one entity, and two classes can expand into four. So `from` is a list,
never a scalar, and every emitted object records why it exists.

```jsonc
"provenance": {
  "from": ["<IRI>", "…"],
  "derivation": "junction",
  "because": "<one line>"
}
```

| `derivation` | `from[]` holds | Phase | Forced by |
|---|---|---|---|
| `direct` | one class, or one property | **Author** | 1:1 |
| `junction` | both endpoint classes **and** the object property | **Author** | many-to-many with a single-valued `RELATIONSHIP` — no alternative exists |
| `split-forced` | the class it was split from | **Author** | a platform cap with no option (>10 `MULTILINE_MAX`) |
| `decomposition` | the class it was split from | Phase 2 | lifecycle, scope or access |
| `consolidation` | every class folded in | Phase 2 | a denormalization judgement |
| `federated-view` | every class the view spans | Phase 2 | a query pattern recurring across surfaces |

Open vocabulary — a new mapping shape gets a new kind rather than being forced into
`direct`. **A non-`direct` derivation with an empty `because` is a defect.**

**Author mode emits only the first three.** The bottom three need a consumption
pattern, and no automation exists yet in the run that authors the genome
([data-model-guide.md § What Author mode decides](data-model-guide.md)).

## Coverage

Every class carrying at least one mapped property appears in some object's `from[]`,
or in a `notCovered` row with a reason. The index runs **both ways**:

- **entity → classes** — the `from[]` list, read directly;
- **class → entities** — the inverted index, which the tool emits as `coverage`.

A class legitimately appears in several entities: a property in two domains, or later
a federated view spanning classes that each keep their own `direct` entity. The
inverted index is what makes that visible rather than looking like duplication.

Same discipline as the genome's Source Map, where every source object is either a
step or a `Not covered` row ([extracted-genome-guide.md § Source Map](extracted-genome-guide.md)).

## Running it

```bash
python3 "<SKILL_DIR>/scripts/derive-entities.py" \
  --inventory "<BUNDLE_SLUG>-inventory.json" \
  --project "<ENTITY_PROJECT_NAME>" \
  --out entities.json
```

Optional: `--overrides <FILE>` for the named overrides of the four defaults
([constraint-register-guide.md § Defaults and overrides](constraint-register-guide.md)),
`--scope tenant|folder`.

Exit 0 on a derivation; exit 1 naming a cycle's members or a rule that cannot be
satisfied. Output keys are sorted and ordering is stable, so two runs on unchanged
input produce byte-identical files — the property every later phase's diff rests on.

## Anti-patterns

1. **Synthesizing a junction for a reified class.** Duplicates the entity and drops
   the relationship's attributes (§ Junctions).
2. **Approximating a composite key with `isUnique` on one field.** Enforces something
   the ontology did not state (§ Composite keys).
3. **Emitting `INTEGER`, `FLOAT`, `DOUBLE`, `UUID` or `DATETIME`.** Accepted by the
   tenant API, refused by `--local`, broken in the UI (§ Types).
4. **Renaming silently.** Every rename and every collision suffix is a register row;
   the IRI is the identity (§ Naming).
5. **Emitting `consolidation`, `decomposition` or `federated-view` in Author mode.**
   Those need a consumption pattern that does not exist yet (§ Provenance).
6. **Treating a self-reference as a cycle**, or a diamond as one (§ Cycles).
7. **Letting a Data Fabric limit edit the ontology.** The conceptual level is an
   input; a platform limit is a register row
   ([data-model-guide.md § Three schemas](data-model-guide.md)).

# Action Contract

Actions document what write operations are allowed on the ontology data. They give integrations and AI agents a governed, versioned vocabulary of mutations — any system that reads the ontology knows exactly what can be changed and how.

Each action targets one entity and one record (single-entity, single-record scope). Actions work on both native and federated entities. The skill extracts these semantic concepts from the PDD (structured table or prose) and generates a W3C FnO TTL artifact per action.

## What the skill needs to know

| Question | TTL construct | Notes |
|---|---|---|
| What's the mutation called? | `{ns}:{camelCaseVerb}` + file `{ontology}-{name}.ttl` | Must be a verb phrase describing what changes (e.g. `updateAccountDescription`, not `accountUpdate` or `action1`) |
| Which entity does it write to? | `{{Entity}}` template in SQL | Must match a `Declaration(Class(:...))` in schema.ofn |
| What SQL operation? | SQL verb in `ont:statements` | `UPDATE`, `INSERT INTO`, `DELETE FROM` |
| What does the SQL do to the data? | Operation-specific clause in `ont:statements` | UPDATE: `SET {{Entity.field}} = :param`; INSERT: `({{Entity.field}}, ...) VALUES (:param, ...)`; DELETE: no data clause |
| How is the target row identified? | `WHERE {{Entity.pk}} = :id` in SQL | Typically the entity's PK field |
| What inputs does the caller provide? | `fno:expects` list + `ont:param.*` blocks | Types derived from field's XSD type in schema.ofn |
| What does an AI agent need to know to pick this action? | `rdfs:comment` on the action node | What it changes, scope (one row or many), when to use it vs alternatives |

## PDD table format (when structured)

The PDD may use this table format. When it does, map fields to the semantic questions above. When the PDD uses prose instead, extract the same concepts from the description.

```
Action: {Human-readable title}
┌───────────────┬──────────────────────────────────────┐
│ Name          │ {camelCase action name}               │
│ Entity        │ {ontology class name}                 │
│ Operation     │ UPDATE | INSERT | DELETE              │
│ Description   │ {what it does — used by AI agents}    │
│ Target Fields │ {comma-separated field names}         │
│ Identifier    │ {PK field name}                       │
│ Inputs        │ {name (type, required), ...}          │
└───────────────┴──────────────────────────────────────┘
```

**Deterministic shortcut:** When the PDD uses the structured 7-row table, map fields directly — skip inference, the table gives exact values. The semantic questions above are for prose or non-standard formats.

| PDD Field | TTL construct | Notes |
|---|---|---|
| Name | `{ns}:{value}` + file `{ontology}-{value}.ttl` | Use value directly as action identity |
| Entity | `{{value}}` in SQL template | Must match class in schema.ofn, never real table names |
| Operation | SQL verb in `ont:statements` | `UPDATE`, `INSERT INTO`, `DELETE FROM` |
| Target Fields | `{{Entity.field}} = :param` in SET/VALUES | Must match DataProperty in schema.ofn, runtime resolves to physical columns via mapping |
| Identifier | `WHERE {{Entity.value}} = :id` | Typically the entity's primary key |
| Inputs | `fno:expects` list + `ont:param.*` blocks | Types derived from field's XSD type in schema.ofn |
| Description | `rdfs:comment` on action node | Use value directly, ensure it covers scope and when to use |

## Parameter type mapping

PDD uses business-friendly types. Map to XSD:

| PDD type | XSD type |
|---|---|
| PK | `xsd:string` (default) or match entity key type |
| Text | `xsd:string` |
| Number | `xsd:decimal` |
| Date | `xsd:date` |
| DateTime | `xsd:dateTime` |
| Boolean | `xsd:boolean` |

## Generated TTL structure

**Two prefixes required.** `ont:` = platform namespace (predicates: `kind`, `language`, `statements`, `paramName`, `paramType`, `required`). A separate prefix for the ontology's own namespace (entity-specific terms: action name, param/output resource IRIs). The parser resolves platform predicates by full URI — using the wrong namespace silently drops the action.

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix {ns}:  <https://ontology.uipath.com/{ontology-name}#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

{ns}:{name}
        a               fno:Function ;
        rdfs:label      "{Action title}" ;
        rdfs:comment    "{What it changes, scope, when to use it vs alternatives.}" ;
        ont:kind        "ACTION" ;
        ont:language    "SQL" ;
        ont:statements  ( "{generated SQL}" ) ;
        fno:expects     ( {ns}:param.{name}.{p1} ... ) ;
        fno:returns     ( {ns}:out.{name}.rowsAffected ) .

{one {ns}:param.{name}.{paramName} block per parameter, using ont: for paramName/paramType/required}

{ns}:out.{name}.rowsAffected
        a              fno:Output ;
        ont:paramName  "rowsAffected" ;
        ont:paramType  "xsd:integer" .
```

## Validation rules

1. Entity must match a `Declaration(Class(:...))` in schema.ofn
2. Every field reference must match a `Declaration(DataProperty(:Entity.field))` in schema.ofn
3. Identifier must match a declared DataProperty (typically the key)
4. Every input name must appear as `:paramName` in the generated SQL
5. Input types must match the field's XSD type from schema.ofn
6. `fno:returns` with `rowsAffected` output is mandatory
7. Output uses `ont:paramName` (not `ont:returnName`) — parser uses same method for both

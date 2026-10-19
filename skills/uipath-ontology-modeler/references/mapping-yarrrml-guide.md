# YARRRML Mapping Reference

Artifact type: `mapping` | Media type: `application/yaml` | File: `mapping.yarrrml.yml`

The mapping binds each class to a local entity **by name**. The ontology service resolves `table:` to the entity in the deployment folder at install; the mapping never carries IDs.

---

## File structure

```yaml
prefixes:
  ont: https://ontology.uipath.com/{name}#

mappings:
  {ClassName}:
    sources:
      - access: datafabric
        table: {EntityName}
        referenceFormulation: rr:SQL2008
    s: ont:{ClassName}/$(primaryKeyColumn)
    po:
      - - a
        - ont:{ClassName}
      - - ont:{ClassName}.{propName}
        - $({columnName})
      - p: ont:{objectProperty}
        o:
          mapping: {TargetClassName}
          condition:
            function: equal
            parameters:
              - - str1
                - $({foreignKeyColumn})
              - - str2
                - $({primaryKeyColumn})
```

---

## Rules

### Source block
- `access: datafabric` — always this literal string; tells the runtime to use Data Fabric as the FQS source
- `table:` — the local entity name from `entities/{EntityName}.json` (usually the class name). No entity IDs, folder IDs, or placeholders.
- `referenceFormulation: rr:SQL2008` — always this literal

### Subject template (`s:`)
- Pattern: `ont:{ClassName}/$(primaryKeyColumn)`
- `primaryKeyColumn` is `Id` (the system key) or a field name from the entity definition, case-sensitive
- Example: `ont:Doctor/$(doctorId)` where `doctorId` is the entity's primary key field name

### Property-object pairs (`po:`)

**rdf:type** (required for every mapping):
```yaml
- - a
  - ont:{ClassName}
```

**Data property** (scalar column → ontology data property):
```yaml
- - ont:{ClassName}.{propName}
  - $({columnName})
```
Column name must match the entity definition's field name exactly (case-sensitive).

**Object property** (join → ontology object property):

`ont:{objectProperty}` must exactly match an `ObjectProperty` IRI declared in `{name}.ofn` — look it up before writing the `p:` line.

`{TargetClassName}` must be the exact key of another mapping block in this file — if the block is absent or misspelled, YARRRML silently produces no join triples.

`str1` resolves from the **current mapping's** source rows; `str2` from the **target `mapping:`** source rows — they always reference different entity tables, even when `$(columnName)` is identical in both.

**Case A — FK and PK share the same column name** (most common):
```yaml
- p: ont:{objectProperty}
  o:
    mapping: {TargetClassName}
    condition:
      function: equal
      parameters:
        - - str1
          - $({sharedColumnName})
        - - str2
          - $({sharedColumnName})
```

**Case B — FK and PK have different names** (e.g. casing mismatch or renamed column):
```yaml
- p: ont:{objectProperty}
  o:
    mapping: {TargetClassName}
    condition:
      function: equal
      parameters:
        - - str1
          - $({foreignKeyColumn})
        - - str2
          - $({primaryKeyColumn})
```

---

## Full worked example

A complete worked 3-class mapping (Doctor, Patient, Prescription) is in [`mapping-yarrrml-example.md`](mapping-yarrrml-example.md). Read it only if a gate/consistency check fails and you need a concrete reference to self-correct, or you judge the rules above aren't enough to proceed confidently for this request.

---

## Junction class mapping (many-to-many)

A junction class maps to its own entity (the association table). It holds both FK columns, so both object property joins originate from the junction mapping block.

```yaml
{JunctionClass}:
  sources:
    - access: datafabric
      table: {JunctionEntityName}
      referenceFormulation: rr:SQL2008
  s: ont:{JunctionClass}/$(primaryKeyColumn)
  po:
    - - a
      - ont:{JunctionClass}
    - p: ont:{propToSideA}
      o:
        mapping: {SideA}
        condition:
          function: equal
          parameters:
            - - str1
              - $({sideAFKColumn})      # FK on the junction entity
            - - str2
              - $({sideAPKColumn})      # PK on the SideA entity
    - p: ont:{propToSideB}
      o:
        mapping: {SideB}
        condition:
          function: equal
          parameters:
            - - str1
              - $({sideBFKColumn})      # FK on the junction entity
            - - str2
              - $({sideBPKColumn})      # PK on the SideB entity
```

Both FK columns (`str1`) are on the junction entity. The `SideA` and `SideB` mapping blocks remain unchanged — they do not need to reference the junction. Verify FK and PK column casing separately for each side against the entity definitions — do not assume they match.

---

## USAGE POLICY block

Add a `# USAGE POLICY` comment block at the top of the `.yarrrml.yml` file, before the `prefixes:` key. This is the **rule** layer — imperative rules for any agent or tool that reads this file as text. It teaches *how* to use the constructs.

**Separation of Concerns**: the USAGE POLICY carries rules only. Facts (what status='A' means, grain, value domains) belong in `rdfs:comment` in `{name}.ofn`. Bindings (which FK column joins which PK column) belong in the `condition:` blocks below. Do not duplicate facts from `{name}.ofn` here — reference them ("LITERALS are case-sensitive — see `{name}.ofn`") instead of restating them.

Keep it ≤30 non-empty lines. Every rule must reference constructs that actually exist in the mapping or schema. State the non-action explicitly for conditional rules (see example below).

```yaml
# ============================================================================
# USAGE POLICY  (how to use the constructs; facts live in {name}.ofn)
# ============================================================================
# JOIN GRAPH (join only what the question needs):
#   Order → Customer via Order.customerId = Customer.Id
#   OrderLine → Order via OrderLine.orderId = Order.Id
# ROUTING (canonical property for ambiguous phrases):
#   "customer name" → Customer.customerName, not OrderLine.customerName
# GRAIN DISCIPLINE:
#   Order: ONE row per order — no dedup needed
#   OrderHistory: TIME SERIES — SELECT DISTINCT orderId for per-order questions
# OUTPUT DISCIPLINE:
#   Return ALL matching rows for list questions; LIMIT 1 only for single-answer superlatives.
#   No default LIMIT. No DISTINCT unless uniqueness was asked.
# LITERALS are case- and format-sensitive — copy exactly as annotated in {name}.ofn.
# ============================================================================

prefixes:
  ont: https://ontology.uipath.com/{name}#
...
```

Fill in only the sections relevant to the domain. Omit sections that don't apply rather than leaving them empty or generic. The join graph and routing sections have the most impact — always include them when there are object properties or ambiguous column names.

---

## Federated entities

Not supported in a local solution. A federated entity needs an Integration Service connection and cannot be authored locally; stop and tell the user.

---

## Common mistakes

- **Wrong column name** — column names in `$()` must match field names in `entities/{EntityName}.json` exactly (case-sensitive), or be `Id`.
- **Join column casing mismatch** — `str1` is the FK column on this entity; `str2` is the PK column on the target entity. The same logical key can have different casing on each side (e.g. `$(doctorId)` on Doctor but `$(doctorid)` on Prescription). Always verify both sides separately against the entity definitions — do not assume the casing matches.
- **Same-column-name join treated as a mistake** — when FK and PK share the same column name (e.g. both `supplierId`), `str1` and `str2` both use `$(supplierId)`. This is correct — YARRRML resolves each from its own source table. Do not invent different aliases.
- **Missing `a` triple** — every mapping block must have `- - a\n  - ont:{ClassName}` or the ontology class instances won't be typed.
- **Wrong object property direction** — check `ObjectPropertyDomain` and `ObjectPropertyRange` in `{name}.ofn`. The mapping entry goes on the entity that holds the foreign key.
- **Object property name not in schema** — `ont:{objectProperty}` in the `p:` line must exactly match an `ObjectProperty` declared in `{name}.ofn`. A mismatch causes validation rejection with a property-not-found error. Read `{name}.ofn` to find the correct IRI before writing the condition.
- **Missing `mapping:` block for target class** — `mapping: {TargetClassName}` must reference a top-level mapping key that exists in this file. A missing or misspelled block can silently produce no join triples for that property, so check every `mapping:` target against the top-level keys before running preflight.
- **Mapping out of sync with the schema** — every `ont:` property referenced in the mapping must exist in the schema. Generate the schema and constraints first, then the mapping, and let the preflight cross-file gate confirm they agree before attaching files to the solution.
- **Verbose YARRRML syntax** — Never use `subjects:`, `predicateobjects:`, `predicate:`, `object:`, or `[rdf:type, ont:Class~iri]`. Never add `~xsd:string` type annotations to data property values (`$(col)` not `$(col)~xsd:string`). Use only the compact `s:`/`po:`/`p:`/`o:` form with `table:` and `referenceFormulation: rr:SQL2008` in every source block; the verbose form can pass a syntax check yet fail to deploy. If `uip solution resources files list` returns warnings for the mapping, re-read this file and rewrite it.

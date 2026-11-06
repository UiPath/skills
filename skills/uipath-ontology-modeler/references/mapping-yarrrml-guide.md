# YARRRML Mapping Reference

Artifact type: `mapping` | Media type: `application/yaml` | File: `{name}-mapping.yarrrml.yml`

The mapping binds each class to a local entity **by name**. The ontology service resolves `table:` to the entity in the deployment folder at install. The mapping never carries an entity or folder identifier (rule `MAP-012`). It is an `application/yaml` artifact: check it with `uip ont artifacts check {name}-mapping.yarrrml.yml --content-type application/yaml --type mapping --file <path>`, and the CLI sends it to the service as YAML.

Write the mapping after every entity exists in the solution. It uses the entity and field names exactly as they were created.

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
    s: ont:{ClassName}/$(Id)
    po:
      - [a, ont:{ClassName}]
      - [ont:{ClassName}.{propName}, $({columnName})]
      - p: ont:{objectProperty}
        o:
          mapping: {TargetClassName}
          condition:
            function: equal
            parameters:
              - [str1, $({relationshipField})]
              - [str2, $(Id)]
```

---

## Rules

### Source block
- `access: datafabric`: always this literal string.
- `table: <EntityName>`: the local entity's name in the solution, case-sensitive. A federated entity is named the same way. No identifiers of any kind.
- `referenceFormulation: rr:SQL2008`: always this literal.

### Subject template (`s:`)
- Pattern: `ont:{ClassName}/$(Id)`. `$(Id)` is the subject key.
- Field names are case-sensitive.

### Property-object pairs (`po:`)

**Type** (required in every mapping block):
```yaml
- [a, ont:{ClassName}]
```

**Data property** (a column to an ontology data property):
```yaml
- [ont:{ClassName}.{propName}, $({columnName})]
```
The column is a field of the entity named in this block's `table:`, written exactly as it is spelled there.

**System fields.** `Id`, `CreateTime`, `UpdateTime`, `CreatedBy` and `UpdatedBy` exist on every entity. `Id` is the subject key and the join target. Never map the others as domain properties; they are not in the schema.

---

## Joins

An object property joins two mapped classes on plain columns. `ont:{objectProperty}` must exactly match an `ObjectProperty` declared in `{name}.ofn`, and `mapping: {TargetClassName}` must be the exact key of another mapping block in this file. A missing or misspelled target silently produces no join triples.

A `RELATIONSHIP` field on the referencing entity holds the target's key. The join reads the field on the current mapping's entity and the target's `Id`:

```
equal(str1=$(customer), str2=$(Id))
```

```yaml
- p: ont:placedBy
  o:
    mapping: Customer
    condition:
      function: equal
      parameters:
        - [str1, $(customer)]     # RELATIONSHIP field on SalesOrder
        - [str2, $(Id)]           # system key on Customer
```

- `str1` resolves from the **current mapping's** source rows, `str2` from the **target mapping's** rows.
- The join goes in the mapping of the entity that holds the field. The inverse property (`InverseObjectProperties` in the schema) gets no join; it is answered from this one. See [owl-patterns-guide.md](owl-patterns-guide.md#inverse-properties).
- A federated target is a plain-column join too: `str2` is the key column of the federated entity (usually `Id`).
- Every object property between two mapped classes needs its join (`XF-015`), and every join needs a declared object property (`XF-014`). See [relationships-guide.md](relationships-guide.md) for choosing the key.

### Junction class (many-to-many)

A junction class maps to its own entity. It holds one `RELATIONSHIP` field per side, so both joins live in the junction's block.

```yaml
OrderLine:
  sources:
    - access: datafabric
      table: OrderLine
      referenceFormulation: rr:SQL2008
  s: ont:OrderLine/$(Id)
  po:
    - [a, ont:OrderLine]
    - p: ont:lineOfOrder
      o:
        mapping: SalesOrder
        condition:
          function: equal
          parameters:
            - [str1, $(order)]       # RELATIONSHIP field on OrderLine
            - [str2, $(Id)]
    - p: ont:lineOfProduct
      o:
        mapping: Product
        condition:
          function: equal
          parameters:
            - [str1, $(product)]     # RELATIONSHIP field on OrderLine
            - [str2, $(Id)]
```

The `SalesOrder` and `Product` blocks stay unchanged. Check each side's column casing against its own entity.

---

## Choice-set columns

A choice-set field is mapped by its **value name**, as a literal `xsd:string`. Never map a value identifier.

```yaml
- [ont:SalesOrder.status, $(status), xsd:string]
```

- The value names in the column are the ones the constraints list with `sh:in` (see [shacl-patterns-guide.md](shacl-patterns-guide.md#value-list-from-a-choice-set)) and the schema comment lists.
- `CHOICE_SET_MULTIPLE` column: one triple per selected value; the service splits it. Write the same single line. Do not split or join values in the mapping.

---

## USAGE POLICY block

Add a `# USAGE POLICY` comment block at the top of the `.yarrrml.yml` file, before the `prefixes:` key. This is the **rule** layer: imperative rules for any agent or tool that reads this file as text. It teaches *how* to use the constructs.

**Separation of concerns.** The USAGE POLICY carries rules only. Facts (what a status value means, grain, value domains) belong in `rdfs:comment` in `{name}.ofn`. Bindings (which key column joins which) belong in the `condition:` blocks. Do not restate facts from `{name}.ofn` here; reference them instead.

Keep it to 30 non-empty lines or fewer. Every rule must reference constructs that exist in the mapping or schema. For a conditional rule, state what to leave undone when the condition is false.

```yaml
# ============================================================================
# USAGE POLICY  (how to use the constructs; facts live in {name}.ofn)
# ============================================================================
# JOIN GRAPH (join only what the question needs):
#   SalesOrder → Customer via SalesOrder.customer = Customer.Id
# ROUTING (canonical property for ambiguous phrases):
#   "customer name" → Customer.customerName
# GRAIN DISCIPLINE:
#   SalesOrder: ONE row per order, no dedup needed
# OUTPUT DISCIPLINE:
#   Return ALL matching rows for list questions; LIMIT 1 only for single-answer superlatives.
#   No default LIMIT. No DISTINCT unless uniqueness was asked.
# LITERALS are case- and format-sensitive. Copy status values exactly as annotated in {name}.ofn.
# ============================================================================

prefixes:
  ont: https://ontology.uipath.com/{name}#
...
```

Fill in only the sections that apply. The join graph and routing sections matter most: include them whenever there are object properties or ambiguous column names.

---

## Common mistakes

- **Wrong column name.** Names in `$()` must match field names in the entity exactly (case-sensitive), or be a system field.
- **Join casing mismatch.** `str1` is a field of this entity; `str2` is a field of the target entity. Check each side against its own entity.
- **Missing type triple.** Every block needs `[a, ont:{ClassName}]`, or the instances are untyped.
- **Wrong direction.** Check `ObjectPropertyDomain` and `ObjectPropertyRange` in `{name}.ofn`. The join goes in the mapping of the entity that holds the `RELATIONSHIP` field.
- **Object property not in the schema.** Read the IRI from `{name}.ofn` before writing the `p:` line.
- **Missing `mapping:` target.** Check every target against the top-level keys of this file.
- **Join on an inverse property.** Only the property whose entity holds the field gets a join.
- **Mapping out of sync with the schema.** Every `ont:` term must exist in the schema. Write schema and constraints first, then the mapping.
- **Identifiers in the mapping.** Never write `entityId` or `folderId`. `table: <EntityName>` is the only link.
- **Verbose YARRRML.** Never use `subjects:`, `predicateobjects:`, `predicate:`, `object:`, or inline `~iri` relationships. Use the compact `s:`/`po:`/`p:`/`o:` form with `table:` and `referenceFormulation: rr:SQL2008` in every source block.

---

## Full worked example

The Orders domain: `Customer` and `SalesOrder`. `SalesOrder.customer` is a `RELATIONSHIP` field, `SalesOrder.status` uses the choice set `OrderStatus`. It is a model to adapt, not a file to copy verbatim.

```yaml
prefixes:
  ont: https://ontology.uipath.com/SalesOps#

mappings:
  SalesOrder:
    sources:
      - access: datafabric
        table: SalesOrder
        referenceFormulation: rr:SQL2008
    s: ont:SalesOrder/$(Id)
    po:
      - [a, ont:SalesOrder]
      - [ont:SalesOrder.orderId, $(orderId)]
      - [ont:SalesOrder.status, $(status), xsd:string]
      - p: ont:placedBy
        o:
          mapping: Customer
          condition:
            function: equal
            parameters:
              - [str1, $(customer)]
              - [str2, $(Id)]
  Customer:
    sources:
      - access: datafabric
        table: Customer
        referenceFormulation: rr:SQL2008
    s: ont:Customer/$(Id)
    po:
      - [a, ont:Customer]
      - [ont:Customer.customerName, $(name)]
```

`places` (the inverse of `placedBy`) has no block entry: the schema declares it with `InverseObjectProperties`.

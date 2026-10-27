# Relationships Guide

**The ontology owns relationships.** Entities carry no relationship fields. A relationship between two classes has three parts, and all three must exist.

| Where | What |
|---|---|
| Schema (`{name}.ofn`) | an `ObjectProperty` with `ObjectPropertyDomain` (the class holding the key) and `ObjectPropertyRange` (the class it points to) |
| Constraints (`{name}-constraints*.ttl`) | `sh:class` on the object property path, where a shape constrains it |
| Mapping (`{name}-mapping.yarrrml.yml`) | a join in the domain class's mapping block, on plain columns |

## Worked example: Order to Customer

An order has one customer. `Order` holds the key, so the entity `Order` has a plain field `customerId` (`STRING`) and `Customer` is keyed by its system field `Id`.

Entity field (see [`entity-format-guide.md`](entity-format-guide.md)):

```json
{ "name": "customerId", "type": "STRING", "lengthLimit": 64 }
```

Schema:

```
Declaration(ObjectProperty(:placedBy))
AnnotationAssertion(rdfs:label :placedBy "placed by")
AnnotationAssertion(rdfs:comment :placedBy "Each Order is placed by one Customer. Join: Order.customerId = Customer.Id. 'Exactly one' is QL-inexpressible; recorded here.")
ObjectPropertyDomain(:placedBy :Order)
ObjectPropertyRange(:placedBy :Customer)
```

Mapping, on the `Order` block:

```yaml
- p: ont:placedBy
  o:
    mapping: Customer
    condition:
      function: equal
      parameters:
        - - str1
          - $(customerId)
        - - str2
          - $(Id)
```

`str1` is read from the current mapping's entity (`Order`), `str2` from the target mapping's entity (`Customer`). Both must be fields of those entities or system fields, case-sensitive.

Constraint, when the relationship is required:

```turtle
sh:property [ sh:path ont:placedBy ; sh:class ont:Customer ; sh:minCount 1 ] ;
```

## Rules the validator checks

- Every join in a mapping uses an object property declared in the schema.
- Every object property whose domain and range are both mapped classes has a join in the domain class's mapping.
- Every `$(column)` in a join is a field of its entity (or of the entity of the mapping it joins to), or a system field.
- Do not write an inline `~iri` relationship. Use the join form above.

## Choosing the key column

1. **The user named a key field.** Use it exactly as stated, for example `Order.customerId`. Do not rename it.
2. **The key field exists on a supplied entity.** Use that field. If it is not a plain column the join can use, ask.
3. **The user described the relationship but named no key.** Propose `{targetClass}Id` on the entity that holds the key (for example `customerId`), joined to the target's `Id`. **Ask before you invent it.** Do not add the field, or write the join, until the user confirms.
4. **Which side holds the key.** The many side holds it (`Order.customerId`, not a list on `Customer`). The object property's domain is the class that holds the key.
5. **The target key.** Join to the target's `Id` unless the user named a different unique field of the target (then use that).

A key column holds the same kind of value as the column it joins to. `Id` is a system field, so a foreign key to it is `STRING`.

If the key is missing from an entity you did not write (`ENTITY_SOURCE` is `supplied`), ask the user before adding it. Do not change a supplied body on your own.

## Many-to-many

Use a junction class backed by its own local entity. The entity has two plain key fields, and the junction's mapping block carries two joins, one per side. See the junction sections of [`owl-patterns-guide.md`](owl-patterns-guide.md) and [`mapping-yarrrml-guide.md`](mapping-yarrrml-guide.md).

## When entities carry relationship fields later

Today no entity has a relationship field, so every key is a plain field as above. When entities later define relationship fields, reuse that field as the join column instead of adding another key. The join check treats a relationship field like any other field. Nothing else in the three parts above changes.

## Do not

- Declare a foreign key as a `DataProperty` and stop there. Two matching columns are not a relationship until there is an `ObjectProperty` and a join.
- Use `RELATIONSHIP`, `CHOICE_SET_*` or any reference field in an entity.
- Write `entityId` or `folderId` in the mapping.

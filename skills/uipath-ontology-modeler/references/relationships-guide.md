# Relationships Guide

A relationship between two classes has three parts, and all three must exist.

| Where | What |
|---|---|
| Entity | one `RELATIONSHIP` field on the referencing entity, naming the target entity |
| Schema (`{name}.ofn`) | an `ObjectProperty` with `ObjectPropertyDomain` (the class holding the field) and `ObjectPropertyRange` (the class it points to) |
| Mapping (`{name}-mapping.yarrrml.yml`) | a join in the domain class's mapping block, on the field and the target's `Id` |

Where a shape constrains the relationship, the constraints file adds `sh:class` on the object property path.

## Worked example: SalesOrder to Customer

A sales order has one customer. `SalesOrder` holds the field, and `Customer` is keyed by its system field `Id`.

Entity field (see [entity-guide.md](entity-guide.md)):

```json
{ "name": "customer", "type": "RELATIONSHIP", "referenceEntityName": "Customer" }
```

`referenceFieldName` defaults to `Id`; add it only to reference a different unique field of the target.

Schema:

```
Declaration(ObjectProperty(:placedBy))
ObjectPropertyDomain(:placedBy :SalesOrder)
ObjectPropertyRange(:placedBy :Customer)
Declaration(ObjectProperty(:places))
InverseObjectProperties(:places :placedBy)
```

Mapping, on the `SalesOrder` block:

```yaml
- p: ont:placedBy
  o:
    mapping: Customer
    condition:
      function: equal
      parameters:
        - [str1, $(customer)]
        - [str2, $(Id)]
```

`str1` is read from the current mapping's entity, `str2` from the target mapping's entity. Both are fields of those entities or system fields, case-sensitive.

## One field, inverse in the schema only

The inverse lives only in the schema, as `InverseObjectProperties`. **Never add a second RELATIONSHIP field for the inverse.** Two fields pointing at each other form a cycle, which the validator reports as `XF-017`. The inverse gets no field, no join and no shape. `XF-017` also covers longer reference cycles (A to B to C to A): break the cycle by keeping only one field of the loop.

If `XF-017` is reported, remove the second field with `uip df entities update <E> --local` (`removeFields`), then validate again.

## Which side holds the field

1. **The user named a field.** Use it exactly as stated.
2. **The user described the relationship but named no field.** Propose a field named after the target (`customer`) on the many side and **ask before adding it**.
3. **The many side holds it.** `SalesOrder.customer`, not a list on `Customer`. The object property's domain is the class that holds the field.
4. **Create order.** The referenced entity is created before the entity that references it (see [entity-guide.md](entity-guide.md)).

For an entity you did not write (`ENTITY_SOURCE` is `supplied`), ask before adding the field.

## Federated target

A federated entity can't be a `RELATIONSHIP` target. Join on a plain column of the referencing entity to the federated entity's key column:

```yaml
- [str1, $(accountKey)]   # plain column on the referencing entity
- [str2, $(Id)]           # key column of the federated entity
```

## Many-to-many

Use a junction entity with two `RELATIONSHIP` fields, one per side (`OrderLine.order`, `OrderLine.product`). Its mapping block carries two joins. See [owl-patterns-guide.md](owl-patterns-guide.md) and [mapping-yarrrml-guide.md](mapping-yarrrml-guide.md).

## Self-reference

A `RELATIONSHIP` field may name its own entity (`"referenceEntityName": "<E>"`). Locally only the CLI authors it (`uip df entities create|update <E> --local`). Whether Data Fabric deploys it is not yet shown, so tell the user.

## Rules the validator checks

- Every join uses an object property declared in the schema (`XF-014`).
- Every object property between two mapped classes has a join in the domain class's mapping (`XF-015`). **Exception:** a property declared `InverseObjectProperties` of a joined property gets none. Sub-properties are not exempt.
- Every `$(column)` in a join is a field of its entity or a system field.
- Do not write an inline `~iri` relationship. Use the join form above.

## Do not

- Declare a key as a `DataProperty` and stop there. Two matching columns are not a relationship.
- Add a second `RELATIONSHIP` field for an inverse.
- Substitute a `STRING` column for a `RELATIONSHIP` field.
- Write an entity, field or folder id in the mapping.

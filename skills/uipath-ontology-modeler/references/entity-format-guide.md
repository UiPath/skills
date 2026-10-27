# Entity Format Guide

An ontology class is backed by a **local Data Fabric entity** in the same solution. Entities are authored with `uip df entities create <Name> --local` and `uip df entities update <Name> --local`, and referenced from the mapping by name (`table: <EntityName>`). Never read the tenant for entities and never write `entityId` or `folderId` anywhere.

---

## The entity body

`uip df entities create <Entity> --local --file <body.json>` takes this shape. Save each body as `input/entities/{EntityName}.json`.

```json
{
  "displayName": "Order",
  "description": "ONE row per customer order.",
  "fields": [
    { "name": "customerId", "type": "STRING", "displayName": "Customer Id", "isRequired": true, "lengthLimit": 64 },
    { "name": "orderDate", "type": "DATETIME_WITH_TZ", "displayName": "Order date" },
    { "name": "totalAmount", "type": "DECIMAL", "decimalPrecision": 2, "minValue": 0, "defaultValue": "0" },
    { "name": "quantity", "type": "DECIMAL", "decimalPrecision": 0 },
    { "name": "isPaid", "type": "BOOLEAN" }
  ]
}
```

Field keys you may use: `name`, `type`, `displayName`, `description`, `isRequired`, `isUnique`, `lengthLimit`, `decimalPrecision`, `minValue`, `maxValue`, `defaultValue`. Any other key is not authorable locally.

- `defaultValue` is text for every type: a `DECIMAL` default is `"0"`, not `0`.
- Entity names match `^[a-zA-Z][a-zA-Z0-9_]{2,99}$`.
- **Field names match `^[a-zA-Z][a-zA-Z0-9]{2,99}$` — no underscores.** Do not copy a snake_case column name; write `orderDate`, not `order_date`.
- **System fields are never declared:** `Id`, `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy`. Use `Id` as the primary key in the mapping subject template and in joins.

---

## The nine local types

`STRING`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME_WITH_TZ`, `MULTILINE_TEXT`, `MULTILINE_MAX`, `AUTO_NUMBER`, `FILE`.

Never use `INTEGER`, `FLOAT`, `UUID`, `DATETIME`, `RELATIONSHIP`, `CHOICE_SET_SINGLE` or `CHOICE_SET_MULTIPLE`. The CLI refuses them locally.

### xsd to local type

| Schema range | Local type | Note |
|---|---|---|
| `xsd:string` | `STRING` | `MULTILINE_TEXT` for long free text. `MULTILINE_MAX` for very large text (at most 10 per entity, not filterable) |
| `xsd:anyURI` | `STRING` | |
| `xsd:decimal`, `xsd:double`, `xsd:float` | `DECIMAL` | set `decimalPrecision` when known |
| `xsd:integer`, `xsd:int`, `xsd:long` | `DECIMAL` | `decimalPrecision: 0`. This is what the CLI itself advises for `INTEGER` |
| `xsd:boolean` | `BOOLEAN` | |
| `xsd:date` | `DATE` | |
| `xsd:dateTime` | `DATETIME_WITH_TZ` | never `DATETIME` |
| no schema range (generated key) | `AUTO_NUMBER` | only when the user asks for a running number |
| attachment | `FILE` | not mapped as a data property |

The data property's `DataPropertyRange` stays the xsd type (an integer column is `xsd:integer` in the schema and `DECIMAL` with `decimalPrecision: 0` in the entity).

**Value lists.** A fixed list of values is a `STRING` field. Put the values in the property's `rdfs:comment` and enforce them with `sh:in` in the constraints file. No choice-set field.

**Relationships.** No relationship field. A foreign key is a plain field (for example `customerId`, `STRING`); the ontology owns the relationship. See [`relationships-guide.md`](relationships-guide.md).

---

## Updating an entity

`uip df entities update <Name> --local --body '<json>'` takes `addFields`, `updateFields` and `removeFields`, plus `displayName` and `description`. `--body` is the key (not `--file`); each field in `addFields` uses the same keys as above.

```bash
uip df entities update Order --local --body '{
  "addFields": [
    { "name": "customerId", "type": "STRING", "lengthLimit": 64 },
    { "name": "shippedOn", "type": "DATE" }
  ],
  "updateFields": [ { "name": "totalAmount", "decimalPrecision": 2 } ],
  "removeFields": [ { "name": "legacyCode" } ]
}'
```

A changed field type is rejected when the entity is deployed into a folder that already holds it, so avoid changing the type of a field the user already has live.

After any create or update, run `uip df entities validate --local` and fix what it reports with `uip df entities update --local`.

---

## ENTITY_SOURCE

Record, per entity, where its definition came from.

| ENTITY_SOURCE | Meaning | What to do |
|---|---|---|
| `supplied` | The user gave a definition: a JSON body, a table, or a local entity already in the solution | Use it as the body, as is. Do not change names, types, required flags or display names. If a supplied type is not one of the nine, ask which local type to use. Never substitute silently |
| `described` | The user described fields in words | Keep every stated name, type and required flag. Fill gaps (display names, lengths) and show them for confirmation |
| `generated` | You proposed the entity from the domain | Generate it, show it, and get one confirmation |

In every case ask before changing anything the user stated. The schema and mapping follow the entity names and field names exactly (case-sensitive), not the other way round.

Every `$(column)` in the mapping must be a field of the entity named in that mapping's `table:`, or a system field such as `Id`.

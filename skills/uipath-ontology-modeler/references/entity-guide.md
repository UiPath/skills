# Entity Guide

An ontology class is backed by a **local Data Fabric entity** in the same solution. Entities, choice sets and federated entities are authored with `uip df … --local` and referenced by name: the mapping uses `table: <EntityName>`. Nothing is created on the tenant before deploy. Never look up, write or pass a Data Fabric id (`entityId`, `folderId`, a field, choice-set or connection id) or a GUID, not even inline.

Each local entity is an entity project (`<Name>/project.uiproj` and `<Name>.entity`) with its resource at `resources/solution_folder/entity/native/<Name>.json`. A federated entity's resource is `entity/federated/<Name>.json`. A choice set's is `choiceSet/<Name>.json`.

For field options beyond this table, delegate to `uipath-platform` (Data Fabric) by name. If that skill is absent, use the table and ask the user.

---

## xsd to Data Fabric type

| Schema range | Field type | Note |
|---|---|---|
| `xsd:string` | `STRING` | `MULTILINE_TEXT` for long free text |
| `xsd:anyURI` | `STRING` | |
| `xsd:decimal`, `xsd:double`, `xsd:float` | `DECIMAL` | set `decimalPrecision` when known |
| `xsd:integer`, `xsd:int`, `xsd:long` | `DECIMAL` | `decimalPrecision: 0` |
| `xsd:boolean` | `BOOLEAN` | |
| `xsd:date` | `DATE` | |
| `xsd:dateTime` | `DATETIME_WITH_TZ` | |
| object property | `RELATIONSHIP` | one field on the referencing entity. See [relationships-guide.md](relationships-guide.md) |
| value list, one value | `CHOICE_SET_SINGLE` | single-select: one value per row; names a local choice set |
| value list, several values | `CHOICE_SET_MULTIPLE` | multi-select: several values per row; names a local choice set |

Never use `UUID`, `INTEGER` or `DATETIME`: the Data Fabric UI renders them broken and `--local` refuses them. Never substitute `STRING` for a relationship or a choice set.

The data property's `DataPropertyRange` stays the xsd type: an integer column is `xsd:integer` in the schema and `DECIMAL` with `decimalPrecision: 0` in the entity.

- Entity names match `^[a-zA-Z][a-zA-Z0-9_]{2,99}$` and are unique in the solution.
- **Field names match `^[a-zA-Z][a-zA-Z0-9]{2,99}$`, with no underscores.** Write `orderDate`, not `order_date`.
- `defaultValue` is text for every type: a `DECIMAL` default is `"0"`, not `0`.
- **System fields are never declared:** `Id`, `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy`. Use `Id` as the key in the mapping subject template and in joins.

---

## How a definition is treated

Record an `ENTITY_SOURCE` per entity. What the user gives is authoritative.

| ENTITY_SOURCE | Meaning | What to do |
|---|---|---|
| `supplied` | The user gave a definition: a JSON body, a table, or a local entity already in the solution | Use it verbatim as the body. Never change names, types, required flags or display names. If a supplied type is not in the table above, ask which type to use |
| `described` | The user described fields in words | Keep every stated name, type and required flag. Fill gaps (display names, lengths) and show them |
| `generated` | You proposed the entity from the domain | Show it and get one confirmation |

A delegated handoff's `ENTITY_DEFINITIONS` are already confirmed: use them verbatim. In every other case ask before changing anything the user stated. The schema and mapping follow the entity and field names exactly (case-sensitive). Every `$(column)` in the mapping is a field of the entity named in that mapping's `table:`, or a system field.

Preview the full schema (entities, fields, choice sets and values) before every create.

---

## Duplicate check

Run before any create:

```bash
uip df choice-sets list --local --output json
uip df entities list --local --output json
uip df choice-sets list-values <C> --local --output json
```

Entity names are unique across the solution. A matching definition is reused. A different one is shown to the user as a diff, and the user is asked before `uip df entities update <E> --local` or `uip df choice-set-values create|delete <C> … --local`. Never update silently.

---

## Local create order

1. **Connections.** The connections of federated sources are already in the solution (the modeler's connection stage).
2. **Choice sets, with their values.**
3. **Entities with no `RELATIONSHIP` fields.**
4. **Entities in dependency order:** a referenced entity before any entity that references it.
5. **Federated entities,** after their connection and their native sources.
6. **The artifacts come after all of these.** The mapping uses the created entity and field names exactly, including a federated entity's external field names as `create --local` wrote them from the connector.

### Choice sets

`CHOICE_SETS` holds value names only. A value name is letters and digits and starts with a letter.

```bash
uip df choice-sets create OrderStatus --local --display-name "Order status" --output json
uip df choice-set-values create <C> <VALUE> --local --output json
```

Run `choice-set-values create` once per value, in order (`Open`, `Shipped`, `Cancelled`).

### Native entities

The body is a Data Fabric entity body with names in place of ids. Pass it as is. The CLI resolves each name inside the solution:

```bash
uip df entities create SalesOrder --local --body '<BODY>' --output json
```

```json
{
  "displayName": "Sales order",
  "description": "ONE row per customer order.",
  "fields": [
    { "name": "orderDate", "type": "DATETIME_WITH_TZ", "displayName": "Order date" },
    { "name": "totalAmount", "type": "DECIMAL", "decimalPrecision": 2, "minValue": 0, "defaultValue": "0" },
    { "name": "quantity", "type": "DECIMAL", "decimalPrecision": 0 },
    { "name": "customer", "type": "RELATIONSHIP", "displayName": "Customer", "referenceEntityName": "Customer" },
    { "name": "status", "type": "CHOICE_SET_SINGLE", "displayName": "Status", "choiceSetName": "OrderStatus" }
  ]
}
```

- A `RELATIONSHIP` field carries `"referenceEntityName": "<E>"`, a native local entity in the same solution, and optionally `"referenceFieldName"` (default `Id`).
- A choice-set field carries `"choiceSetName": "<C>"`, a local choice set in the same solution.
- Other field keys: `name`, `type`, `displayName`, `description`, `isRequired`, `isUnique`, `lengthLimit`, `decimalPrecision`, `minValue`, `maxValue`, `defaultValue`.
- If the CLI refuses a local `RELATIONSHIP` or choice-set field, or has no local choice sets or federated entities, the CLI build is too old: stop and tell the user.

Change an existing entity with `uip df entities update <E> --local --body '<CHANGE>' --output json`, where the body takes `addFields`, `updateFields` and `removeFields` plus `displayName` and `description`. A changed field type is rejected when the entity is deployed into a folder that already holds it. A federated entity cannot be updated: delete it and create it again. After any create or update, validate and fix what is reported with `uip df entities update <E> --local`.

### Federated entities

A federated entity reads from connector sources, local native entities, or both. Create it after its sources exist:

```bash
uip df entities create <F> --local --body '<FEDERATED_BODY>' --output json
```

The resource is written to `entity/federated/<F>.json`. With at least one connector source the command needs `uip login`, because the CLI reads the connection and each source object's fields from the tenant. With local native sources only it runs offline and takes the field types from those entities.

Build `<FEDERATED_BODY>` from the sources and joins the user confirmed. The sources become `externalFields`:

- A connector source keeps `connectionName` (already a connection resource in the solution), `object` and `fields`. The `connector` key is for finding the connection and is not passed.
- A native source keeps `entityName` (a local entity) and `fields`.
- `fields` entries are plain external field names, or override objects `{ "source": "<FIELD>", "name", "type", "direction", "searchable", "sortable", "requiredForRead" }` where only `source` is required. Field types come from the connector (connector source) or the local entity (native source).
- Each join in `joins` keeps `source`, `relatedSource`, `sourceField`, `relatedField`, `sourceConnectionName` and `relatedConnectionName`. For a connector source the connection name goes in `sourceConnectionName` / `relatedConnectionName`; for a native source, the entity name.

```json
{
  "displayName": "<DISPLAY_NAME>",
  "description": "<DESCRIPTION>",
  "externalFields": [
    {
      "connectionName": "<CONNECTION>",
      "object": "<OBJECT>",
      "fields": ["<FIELD>", { "source": "<FIELD>", "name": "<FIELD_ALIAS>", "type": "STRING" }]
    },
    { "entityName": "<NATIVE_ENTITY>", "fields": ["<FIELD>"] }
  ],
  "joins": [
    {
      "source": "<SOURCE>",
      "relatedSource": "<RELATED_SOURCE>",
      "sourceField": "<SOURCE_FIELD>",
      "relatedField": "<RELATED_FIELD>",
      "sourceConnectionName": "<CONNECTION>",
      "relatedConnectionName": "<NATIVE_ENTITY>"
    }
  ]
}
```

A federated entity is never a `RELATIONSHIP` target; see [relationships-guide.md](relationships-guide.md).

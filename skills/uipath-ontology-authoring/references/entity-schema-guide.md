# Data Fabric entity schema — reference

How to read what `uip df` returns, so the skill can scaffold its questions and
build the R2RML binding. The author never sees any of this — it is the skill's
working knowledge.

## Commands the skill calls

| Need | Command |
|---|---|
| Check login / active env | `uip login status --output json` |
| List folders (resolve keys) | `uip or folders list --all --output json` |
| List a folder's entities | `uip df entities list --native-only --folder-key <key> --output json` |
| One entity's schema | `uip df entities get <id> --folder-key <key> --output json` |
| Choice set values | `uip df choice-sets list-values <choice-set-id> --folder-key <key> --output json` |

**Folder-level entities only.** Always pass `--folder-key`. Never list
tenant-level entities — no bare `entities list`, no `--include-folders`.
`--native-only` excludes read-only federated entities (not valid
relationship/mapping targets). A returned row's `FolderId` is the folder's GUID.

## Shape of a list/get response

`Data` is an array of entities (list) or one entity (get). Key fields:

```json
{
  "Name": "Order",
  "DisplayName": "Order",
  "Description": "",
  "EntityType": "Entity",                 // "Entity" = native; federated entities are read-only
  "FolderId": "00000000-0000-0000-0000-000000000000",
  "Fields": [
    {
      "Id": "ab7358f4-...",               // field UUID — used for relationship targets
      "Name": "Id",
      "IsPrimaryKey": true,               // the subject-IRI key (a GUID)
      "IsForeignKey": false,
      "IsRequired": false,
      "IsUnique": false,
      "IsSystemField": false,             // CreatedBy/UpdatedTime/etc. — usually dropped
      "ReferenceType": "ManyToOne",       // set on relationship fields
      "FieldDataType": { "Name": "STRING", "LengthLimit": 200 }
    }
  ]
}
```

## Reading a field

- **Primary key** — `IsPrimaryKey: true` (the `Id`, a GUID). Drives the R2RML subject template and relationship joins.
- **Scalar attribute** — `FieldDataType.Name` is the type (see the type table in [owl-and-r2rml-guide.md](owl-and-r2rml-guide.md)). The column name for R2RML is the field `Name`.
- **Relationship / foreign key** — `IsForeignKey: true` and/or a `ReferenceType` (`ManyToOne`, `OneToMany`, `ManyToMany`). The schema names the target via the related field/entity; resolve the target entity's UUID and its `Id`-field UUID with `entities get`. Never reference by name. Cross-folder target → the binding needs the target's folder key.
- **Choice set field** — `FieldDataType.Name` is `CHOICE_SET_SINGLE` or `CHOICE_SET_MULTIPLE`. The stored value is an integer **NumberId** (single) or an integer array (multiple), not the label. Pull the value↔NumberId map with `choice-sets list-values`.
- **System field** — `IsSystemField: true` (`CreatedBy`, `CreatedTime`, `UpdatedBy`, `UpdatedTime`, …). Default: exclude from the ontology unless the author says a system field is business-meaningful.

## What scaffolds which question (business terms, never field terms)

| Schema signal | What the skill asks the author |
|---|---|
| Entity `DisplayName` | "In one sentence, what real-world thing is this?" |
| Set of non-system fields | "Which of these details matter for the business?" (described in plain words, not field names) |
| `FieldDataType` ambiguous (e.g. STRING that looks coded) | value meaning / units / format |
| `ReferenceType` + FK | the relationship's business cardinality, direction, and name |
| `CHOICE_SET_*` + real values | "These statuses exist: … — what does each mean?" |
| `FolderId` differs across two related entities | (internal) cross-folder binding — no author question, the skill wires it |

## Gaps to flag

- **Business concept with no field** — the author describes something the schema can't back. Flag it; do not invent a column.
- **Field never described** — a meaningful-looking field the author never mentioned. Ask in business words whether it matters; default to dropping it, not guessing.

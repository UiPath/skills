# Entity Schema Guide — `entities.json` from a data model

When a genome's input carries a checked data model, the genome's Data Fabric entities are defined in one file beside it: `<GENOME_SLUG>.entities.json`. The genome's Data Fabric table summarizes the file ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md)); the build creates the set from it.

A checked data model is an ontology that passed its check: `object-model.json` with `schema.ofn` and `constraints-shapes.ttl` (classes, properties with `sh:datatype`, `sh:maxLength`, `sh:minCount`, `sh:in`, links, source of record per class).

## Rules

1. **The file is a proposal until the Developer approves it.** Agent proposes which entities realize each class and which classes each entity carries (n:m); Developer approves (author-guide Step 8). Never present the n:m as decided.
2. **One native per class by default**, role `owner`, every property one field. Split a class across entities (`part`), add a `junction`, or carry another class's fields (`copy`) only when the process context or the sources show it; name the evidence in the review.
3. **A class with no source of record gets `"kind": "review"`.** Propose its fields anyway — they come out mostly the same whether it ends native or federated; the Developer settles the kind. The build refuses a `review` entity.
4. **Never invent a length, precision or required flag.** STRING length from `sh:maxLength`, required from `sh:minCount 1`, DECIMAL precision from the sources or the process context; missing → open question, not a default.
5. **Names the platform accepts.** Field names: letters, digits, `_`, starting with a letter; never a C# or VB keyword in any case (`event`, `virtual`, `date`, `string`) and never `Id`, `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy`, `RecordOwner` — rename and keep the property in `property`. Choice-set names: letters and digits. Choice value names: letters and digits starting with a letter; the code as written goes in `displayName`.
6. **A federated entity never selects one name from two sources** — rename one (`<source><Field>`); both sides select the join field.

## Mapping from the data model

| Data model | `entities.json` |
|---|---|
| `xsd:string` + `sh:maxLength n` | `"type": "STRING", "length": n` |
| `xsd:integer` | `"type": "DECIMAL", "precision": 0` |
| `xsd:decimal` | `"type": "DECIMAL", "precision": <from sources>` |
| `xsd:boolean` / `xsd:date` / `xsd:dateTime` | `BOOLEAN` / `DATE` / `DATETIME_WITH_TZ` |
| `sh:in (…)` | a choice set (values in order) + `"type": "CHOICE_SET_SINGLE", "choiceSet": "<Class><Property>"` |
| `sh:minCount 1` | `"required": true` |
| to-one link | `"type": "RELATIONSHIP", "target": "<native of the target class>"` |
| many-to-many link | a native with role `junction` and one RELATIONSHIP to each side |
| source of record UiPath | `"kind": "native"` |
| identical fields across natives, shown as one object | `"kind": "federated"` over those natives |
| no source of record | `"kind": "review"` |

## Format

```json
{
  "version": 1,
  "choiceSets": {
    "EventType": { "displayName": "Event type", "values": [{ "name": "Meeting", "displayName": "meeting" }] }
  },
  "entities": {
    "club_event": {
      "kind": "native",
      "realizes": [{ "class": "Event", "role": "owner" }],
      "fields": {
        "eventName": { "type": "STRING", "length": 80, "required": true, "property": "Event.name" },
        "type": { "type": "CHOICE_SET_SINGLE", "choiceSet": "EventType", "required": true, "property": "Event.type" }
      }
    },
    "club_event_detail": {
      "kind": "native",
      "realizes": [{ "class": "Event", "role": "part", "key": "eventName" }],
      "fields": { "eventName": { "type": "STRING", "length": 80, "required": true, "unique": true, "property": "Event.name" } }
    },
    "club_event_view": {
      "kind": "federated",
      "realizes": [{ "class": "Event", "role": "view" }],
      "primary": { "entity": "club_event", "fields": { "eventName": "eventName" } },
      "sources": [{ "entity": "club_event_detail", "join": "eventName", "fields": { "eventName": "detailEventName" } }]
    }
  }
}
```

| Key | Allowed |
|---|---|
| `kind` | `native`, `federated`, `review` |
| `realizes[].role` | `owner`, `part`, `copy`, `junction`, `view`; `key` names the key a part shares with its owner |
| field keys | `type`, `displayName`, `length`, `precision`, `required`, `unique`, `choiceSet`, `target`, `property` |
| field `type` | `STRING`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME_WITH_TZ`, `CHOICE_SET_SINGLE`, `RELATIONSHIP` |
| federated | `primary` and `sources[]` name natives of the file; `fields` maps source field → name in the view; each source has `join` |

Unknown keys are refused by the build.

## Review (author-guide Step 8)

Show the Developer, before offering edits:

1. **Trace:** one row per class → entity, role; one row per property → entity field.
2. **Every `review` kind** with the question "native (in UiPath) or federated (external system)?".
3. **Every split, junction or copy** with its evidence.

Wait for approval. Change the file on each answer; the genome's Data Fabric table follows the file.

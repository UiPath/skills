# Entity Schema Guide — `entities.json` from a data model

When a genome's input carries a checked data model, the genome's Data Fabric entities are defined in one file beside it: `<GENOME_SLUG>.entities.json`. The genome's Data Fabric table summarizes the file ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md)); the build creates the set from it.

A checked data model is an ontology that passed its check: `object-model.json` with `schema.ofn` and `constraints-shapes.ttl` (classes, properties with `sh:datatype`, `sh:maxLength`, `sh:minCount`, `sh:in`, links, source of record per class).

## Rules

1. **The file is a proposal until the Developer approves it.** Agent proposes which entities realize each class and which classes each entity carries (n:m); Developer approves (author-guide Step 8). Never present the n:m as decided.
2. **One native per class by default**, role `owner`, every property one field. Split a class across entities (`part`), add a `junction`, or carry another class's fields (`copy`) only when the process context or the sources show it; name the evidence in the review.
3. **A class with no source of record gets `"kind": "review"`.** Propose its fields anyway — they come out mostly the same whether it ends native or federated; the Developer settles the kind. The build refuses a `review` entity.
4. **Never invent a length or required flag.** STRING length from `sh:maxLength`, required from `sh:minCount 1`; missing → open question, not a default.
5. **DECIMAL precision is never asked.** Take it from the sources or the process context when they show it; otherwise `2`. List every defaulted precision in the review, where the Developer can change it.
6. **Names the platform accepts.** Entity names: letters and digits only, starting with a letter, 3–100 characters (`customerOrder`, never `customer_order`). Entity and field names are never a reserved SQL word in any case (`order`, `key`, `user`, `percent`, `select`, `table`) — name a link field after its target entity instead (`customerOrder`). Field names: letters, digits, `_`, starting with a letter; never a C# or VB keyword in any case (`event`, `virtual`, `date`, `string`) and never `Id`, `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy`, `RecordOwner` — rename and keep the property in `property`. Choice-set names: letters and digits. Choice value names: letters and digits starting with a letter; the code as written goes in `displayName`.
7. **A federated entity never selects one name from two sources** — rename one (`<source><Field>`); both sides select the join field.
8. **One relationship per link pair.** A link and its inverse (`inverse` in `object-model.json`, `InverseObjectProperties` in `schema.ofn`) are one relationship: one `RELATIONSHIP` field on the to-one side — the required side when both are to-one — and no field on the other side. Two fields pointing at each other are a cycle the build refuses. Every link of the model is either a field (its `property` is the link's name) or the inverse side of one; a link without an inverse is always a field.
9. **Every relationship shows a field the Developer chose.** `display` names the target entity field shown for a related record (`customerId`, `invoiceId`). It is a user-visible choice: propose one per target entity in the review, never default to `Id` silently.
10. **Creating the entities is never a Build With step.** The entities sit under Platform Dependencies; the build creates them from this file through its Data Fabric question. `uipath-platform` is operate-only and never appears in Build With.

## Mapping from the data model

| Data model | `entities.json` |
|---|---|
| `xsd:string` + `sh:maxLength n` | `"type": "STRING", "length": n` |
| `xsd:integer` | `"type": "DECIMAL", "precision": 0` |
| `xsd:decimal` | `"type": "DECIMAL", "precision": <from sources, else 2>` |
| `xsd:boolean` / `xsd:date` / `xsd:dateTime` | `BOOLEAN` / `DATE` / `DATETIME_WITH_TZ` |
| `sh:in (…)` | a choice set (values in order) + `"type": "CHOICE_SET_SINGLE", "choiceSet": "<Class><Property>"` |
| `sh:minCount 1` | `"required": true` |
| to-one link | `"type": "RELATIONSHIP", "target": "<native of the target class>", "display": "<target field>", "property": "<link name>"` |
| link with an inverse | one field, on the to-one side (the required one when both are to-one); the inverse side gets no field (rule 8) |
| many-to-many link, or a to-many link with no inverse | a native with role `junction` and one RELATIONSHIP to each side |
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
    "clubEvent": {
      "kind": "native",
      "realizes": [{ "class": "Event", "role": "owner" }],
      "fields": {
        "eventName": { "type": "STRING", "length": 80, "required": true, "property": "Event.name" },
        "type": { "type": "CHOICE_SET_SINGLE", "choiceSet": "EventType", "required": true, "property": "Event.type" }
      }
    },
    "clubEventDetail": {
      "kind": "native",
      "realizes": [{ "class": "Event", "role": "part", "key": "eventName" }],
      "fields": { "eventName": { "type": "STRING", "length": 80, "required": true, "unique": true, "property": "Event.name" } }
    },
    "clubEventView": {
      "kind": "federated",
      "realizes": [{ "class": "Event", "role": "view" }],
      "primary": { "entity": "clubEvent", "fields": { "eventName": "eventName" } },
      "sources": [{ "entity": "clubEventDetail", "join": "eventName", "fields": { "eventName": "detailEventName" } }]
    }
  }
}
```

| Key | Allowed |
|---|---|
| `kind` | `native`, `federated`, `review` |
| `realizes[].role` | `owner`, `part`, `copy`, `junction`, `view`; `key` names the key a part shares with its owner |
| field keys | `type`, `displayName`, `length`, `precision`, `required`, `unique`, `choiceSet`, `target`, `display`, `property` |
| field `type` | `STRING`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME_WITH_TZ`, `CHOICE_SET_SINGLE`, `RELATIONSHIP` |
| federated | `primary` and `sources[]` name natives of the file; `fields` maps source field → name in the view; each source has `join` |

Unknown keys are refused by the build.

## Review (author-guide Step 8)

Show the Developer, before offering edits:

1. **Trace:** one row per class → entity, role; one row per property → entity field.
2. **Every `review` kind** with the question "native (in UiPath) or federated (external system)?".
3. **Every split, junction or copy** with its evidence.
4. **Every defaulted precision** (rule 5), as one list.
5. **The display field per target entity** (rule 9), as one question per target.
6. **Link coverage:** every link of the model is a field or the inverse side of one (rule 8). Run the genome check with `--data-model` (author-guide Step 8); it reports a link carried by no field and a pair carried twice.

Wait for approval. Change the file on each answer; the genome's Data Fabric table follows the file.

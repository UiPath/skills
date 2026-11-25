# Federated Artifact Shapes Guide — the JSON shape of every pack artifact

The schema reference for the pack of [federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md): every field of every JSON artifact, its type, whether it is required, and a worked example from a real run. **The spine is the procedure a run follows; the shapes are schema reference consulted while writing an artifact** — and enforcement is migrating to CLI tooling, so when real schemas ship this file shrinks to a pointer and the spine is untouched.

Which artifact each phase hands off, the ids they are keyed by, the ledger's rules and every phase contract stay in the pipeline guide. **The guide declares; it does not enforce** ([federated-entity-pipeline-guide.md § Who enforces a shape](federated-entity-pipeline-guide.md)): this skill ships no schema file and no checker, and a run that wants the check writes its own throwaway script against this file.

Read it by section — the shape of the artifact being written, not the whole file.

Neither YARRRML file has a shape here. They are YARRRML, carry no `id` key and need none ([federated-source-mapping-guide.md § Block shape](federated-source-mapping-guide.md), [federated-mapping-guide.md § Block shape](federated-mapping-guide.md)).

**Every example below is from one real run** — a five-class `fieldservice` model over Salesforce, Snowflake and Database Hub, trimmed to what illustrates the shape. Connection names, connection ids and timestamps stand as placeholders in these examples; the artifacts themselves carry the real values.

**The casing of the examples is not arbitrary.** `fieldservice` is the ontology IRI's last segment taken verbatim, so it stems every file of the pack and names the ontology resource; `ServiceWorkOrder` and `PartReservation` are entity names derived from class local names and are PascalCase because the classes are ([federated-entity-pipeline-guide.md § Artifacts](federated-entity-pipeline-guide.md)).

## Shape — the pack manifest

`<MODEL_NAME>-pack.json`. Its rules — every phase rewrites it, it never lists itself and carries no hash of itself — are [federated-entity-pipeline-guide.md § The pack manifest](federated-entity-pipeline-guide.md).

| Field | Type | Required | Is |
|---|---|---|---|
| `model` | string | yes | `<MODEL_NAME>` |
| `ontology` | string | yes | `<ONTOLOGY_NAME>` |
| `run` | string | yes | `run:<MODEL_NAME>/<START_TIMESTAMP>`, minted once at the pipeline guide § Bootstrap and never re-derived. A resume keeps it; a rerun mints a new one |
| `startedAt` | string | yes | when the run started. ISO 8601 UTC, `YYYY-MM-DDTHH:MM:SSZ` |
| `writtenAt` | string | yes | when this manifest was last rewritten — so a pack handed over mid-run says how far it got |
| `supersedes` | string \| null | no | the `run` of the run this one reruns; `null` or absent on a first run |
| `cli` | string | yes | what `uip --version` printed. Every shape in this lane is read or written by that build |
| `inputs` | object[] | yes | the files the run ran against: the `.ofn` always, the constraints `.ttl` when one shipped (pipeline guide phase 1 § No constraints file). One or two entries |
| `artifacts` | object | yes | every artifact of the pack, **keyed by the phase that produced it** — `"1"`–`"7"`, `"bootstrap"`, or `"all"` for the ledger. Each value is a list, because phase 5 produces `entities.json` and one resource file per entity, and the bootstrap produces one connection resource file per connection plus the ontology resource file |

`inputs[]` and each `artifacts` entry: `path` (string, required, relative to the `.ofn`), `sha256` (string, required, `sha256:<LOWERCASE_HEX>` over the file's committed bytes — `shasum -a 256 <PATH>`), and on an artifact entry `format` (string, required, `json` or `yarrrml`).

```json
{"model":"fieldservice","ontology":"fieldservice",
 "run":"run:fieldservice/<START_TIMESTAMP>","startedAt":"<START_TIMESTAMP>","writtenAt":"<WRITE_TIMESTAMP>",
 "supersedes":null,"cli":"<CLI_VERSION>",
 "inputs":[{"path":"schema.ofn","sha256":"<SHA256>"},
           {"path":"constraints-shapes.ttl","sha256":"<SHA256>"}],
 "artifacts":{
   "bootstrap":[{"path":"resources/solution_folder/ontology/fieldservice.json","format":"json","sha256":"<SHA256>"}],
   "1":[{"path":"fieldservice-model.json","format":"json","sha256":"<SHA256>"}],
   "2":[{"path":"fieldservice-discovery.json","format":"json","sha256":"<SHA256>"}],
   "3":[{"path":"fieldservice-source.yarrrml","format":"yarrrml","sha256":"<SHA256>"}],
   "4":[{"path":"fieldservice-partition.json","format":"json","sha256":"<SHA256>"}],
   "5":[{"path":"entities.json","format":"json","sha256":"<SHA256>"},
        {"path":"resources/solution_folder/entity/federated/ServiceWorkOrder.json","format":"json","sha256":"<SHA256>"},
        {"path":"resources/solution_folder/entity/federated/PartReservation.json","format":"json","sha256":"<SHA256>"}],
   "6":[{"path":"fieldservice.yarrrml.yml","format":"yarrrml","sha256":"<SHA256>"}],
   "7":[{"path":"fieldservice-check.json","format":"json","sha256":"<SHA256>"}],
   "all":[{"path":"fieldservice-ledger.json","format":"json","sha256":"<SHA256>"}]}}
```

The run above shipped its model as `schema.ofn` beside a `constraints-shapes.ttl`, so `<MODEL_NAME>` is the ontology IRI's last segment and not the file's base name — `fieldservice`, verbatim and uncased, which is also why `ontology` carries the identical string ([federated-entity-pipeline-guide.md § Artifacts](federated-entity-pipeline-guide.md)).

## Shape — the typed model

`<MODEL_NAME>-model.json`, phase 1. The committed record of what the `.ofn` and the SHACL parse yielded, so every later walk reads the model without re-parsing OWL functional syntax.

| Field | Type | Required | Is |
|---|---|---|---|
| `model` | string | yes | `<MODEL_NAME>` |
| `ontologyIri` | string | yes | the model's IRI, which must sit under `https://ontology.uipath.com/` (pipeline guide phase 1 § Check the model's IRI) |
| `classes` | object[] | yes | one record per class |
| `dataProperties` | object[] | yes | one record per data property |
| `objectProperties` | object[] | yes | one record per object property |
| `skipped` | object[] | yes, may be empty | every axiom outside the accepted set, reported with its location and skipped (pipeline guide phase 1 § Stops) |

| Record | Field | Type | Required | Is |
|---|---|---|---|---|
| class | `id` | id | yes | `cls:<CLASS_LOCAL_NAME>` |
| | `iri` | string | yes | the class IRI |
| | `label` | string \| null | yes, may be null | `rdfs:label`; null feeds the XF-007 coverage count ([federated-check-guide.md § Coverage](federated-check-guide.md)) |
| | `comment` | string \| null | yes, may be null | `rdfs:comment`; same count |
| | `sourceOfRecord` | string \| null | yes, may be null | the `:sourceOfRecord` annotation — the lane gate. **Null is an exception at ingest, never a default** |
| | `annotations` | object | yes, may be empty | every other annotation, keyed by annotation property IRI |
| data property | `id` | id | yes | `dp:<PROPERTY_LOCAL_NAME>` |
| | `iri` | string | yes | the property IRI |
| | `domain` | id | yes | the `cls:` its `DataPropertyDomain` names |
| | `range` | string \| null | yes, may be null | the `DataPropertyRange` axiom's datatype as an `xsd:` name, where the `.ofn` carries one. **A model may declare both, and this lane authors neither** — the range is read, never written, and a disagreement with `datatype` is an exception at ingest, the same cross-check `shClass` gets against `range`. Null where the axiom is absent or the grammar skipped it (`xsd:date` and `xsd:boolean` inside an axiom, phase 1 § Stops) |
| | `datatype` | string \| null | yes, may be null | `sh:datatype` as an `xsd:` name. Null is the degraded case of the pipeline guide phase 1 § No constraints file, and the mapping then authors a two-element pair |
| | `minCount` | number \| null | yes, may be null | `sh:minCount`. No observation channel exists for it (pipeline guide phase 2) |
| | `maxCount` | number \| null | yes, may be null | `sh:maxCount` |
| | `maxLength` | number \| null | yes, may be null | `sh:maxLength`. No observation channel, and every string column is `NVARCHAR(200)` whatever it says |
| | `in` | string[] \| null | yes, may be null | `sh:in`, verbatim and in order |
| object property | `id` | id | yes | `op:<PROPERTY_LOCAL_NAME>` |
| | `iri` | string | yes | the property IRI |
| | `domain` | id | yes | the `cls:` its `ObjectPropertyDomain` names |
| | `range` | id \| null | yes, may be null | the `cls:` its `ObjectPropertyRange` names. **A range fixes a join's endpoints, never its validity** ([federated-entity-pipeline-guide.md § Principles](federated-entity-pipeline-guide.md) rule 5). Null blocks the join and any fold across it (pipeline guide phase 5 § Stops) |
| | `shClass` | id \| null | yes, may be null | the `cls:` of `sh:class`. A disagreement with `range` is an exception at ingest |
| | `minCount` | number \| null | yes, may be null | `sh:minCount` |
| | `maxCount` | number \| null | yes, may be null | `sh:maxCount` — **the only to-one signal that works** |
| skipped | `construct` | string | yes | the axiom's construct, e.g. `HasKey` |
| | `location` | string | yes | where in the `.ofn` it sat |
| | `reason` | string | yes | why it was skipped |

```json
{"model":"fieldservice","ontologyIri":"https://ontology.example.org/fieldservice#",
 "classes":[
   {"id":"cls:ServiceWorkOrder","iri":"https://ontology.example.org/fieldservice#ServiceWorkOrder",
    "label":"Service work order","comment":"One dispatched field job.","sourceOfRecord":null,"annotations":{}},
   {"id":"cls:InstalledAsset","iri":"https://ontology.example.org/fieldservice#InstalledAsset",
    "label":"Installed asset","comment":"A serialised unit in the field.","sourceOfRecord":null,"annotations":{}}],
 "dataProperties":[
   {"id":"dp:ServiceWorkOrder.grandTotal","iri":"https://ontology.example.org/fieldservice#ServiceWorkOrder.grandTotal",
    "domain":"cls:ServiceWorkOrder","range":"xsd:decimal","datatype":"xsd:decimal",
    "minCount":1,"maxCount":1,"maxLength":null,"in":null},
   {"id":"dp:InstalledAsset.serialNumber","iri":"https://ontology.example.org/fieldservice#InstalledAsset.serialNumber",
    "domain":"cls:InstalledAsset","range":"xsd:token","datatype":"xsd:token",
    "minCount":null,"maxCount":1,"maxLength":128,"in":null},
   {"id":"dp:InstalledAsset.isInternalAsset","iri":"https://ontology.example.org/fieldservice#InstalledAsset.isInternalAsset",
    "domain":"cls:InstalledAsset","range":null,"datatype":"xsd:boolean",
    "minCount":null,"maxCount":1,"maxLength":null,"in":null}],
 "objectProperties":[
   {"id":"op:concernsAsset","iri":"https://ontology.example.org/fieldservice#concernsAsset",
    "domain":"cls:ServiceWorkOrder","range":"cls:InstalledAsset","shClass":"cls:InstalledAsset",
    "minCount":null,"maxCount":1},
   {"id":"op:hasPartReservation","iri":"https://ontology.example.org/fieldservice#hasPartReservation",
    "domain":"cls:ServiceWorkOrder","range":"cls:PartReservation","shClass":"cls:PartReservation",
    "minCount":null,"maxCount":null}],
 "skipped":[{"construct":"DataPropertyRange","location":"<OFN_LOCATION>",
             "reason":"builtInDatatype refuses xsd:boolean inside an axiom; the range stays in SHACL"}]}
```

`isInternalAsset` carries `datatype` and no `range`: the grammar refuses `xsd:boolean` inside an axiom, so the axiom was skipped and SHACL is the only declaration left. `hasPartReservation` carries no `maxCount` — its absence is the to-many signal, and it is what forces `PartReservation` to stand alone at phase 4. `sourceOfRecord` is null on every class of this model, which is an exception at ingest and the reason its whole lane split rests on a decision.

## Shape — the discovery record

`<MODEL_NAME>-discovery.json`, phase 2. The rules on what goes in each field are the pipeline guide phase 2 § The discovery record.

| Field | Type | Required | Is |
|---|---|---|---|
| `model` | string | yes | `<MODEL_NAME>` |
| `allowListedConnectors` | string[] | yes | every connector key `uip df connectors list` returned, verbatim. It is what every `allowListed` below is read from, and the roster a class that needs a different source is re-sourced against. **An empty list means the `fqs-connectors-list` flag is unset**, not that nothing is supported |
| `connections` | object[] | yes | one record per connection |

| Record | Field | Type | Required | Is |
|---|---|---|---|---|
| connection | `id` | id | yes | `con:<CONNECTION_RESOURCE_NAME>` |
| | `resourceName` | string | yes | the connection resource's name — the tenant connection's own, which cannot be aliased (pipeline guide § Bootstrap) |
| | `connectorKey` | string | yes | e.g. `uipath-salesforce-sfdc`, never a display name |
| | `connectionId` | string | yes | the tenant connection id. It survives a tenant rename, so it is how a rerun tells a rename from a different connection |
| | `allowListed` | boolean | yes | whether `uip df connectors list` returned the connector. **False means no federated entity can ever be backed by it** |
| | `state` | string | yes | the connection state, verbatim. Independent of `allowListed` — require both |
| | `objects` | object[] | yes | one record per object described |
| object | `id` | id | yes | `obj:<CONNECTION_RESOURCE_NAME>/<OBJECT_NAME>` |
| | `of` | id | yes | the `con:` it was described on |
| | `object` | string | yes | the object name exactly as `uip is resources list` returns it |
| | `fieldsExposed` | number | yes | how many fields `describe` returned. Equal to `fields.length` unless `excluded` is non-empty, and the pair is the only thing that says a field list is a subset rather than the whole object |
| | `primaryKey` | id \| null | yes, may be null | the `fld:` of the declared primary key. **Null is a hard stop for every class that would bind here** (pipeline guide phase 2 § Stops) |
| | `stop` | id \| null | yes, may be null | the `E<n>` recorded against the object, so a rerun does not describe it again to learn the same thing |
| | `excluded` | object[] | yes, may be empty | the fields `describe` returned that this record deliberately does not carry: `field` (string, the name or the family) and `reason` (string). **Rule 1 of the pipeline guide phase 2 § The discovery record is one record per field returned**, so a non-empty list is a departure the record has to state rather than hide — a 120-field object cut to the model's own columns, a field family held back because it is personal data, and a **dotted compound name such as `BillingAddress.street`, which cannot be a flat federated column at all** |
| | `fields` | object[] | yes | one record per field `describe` returns, **including fields the model does not use** |
| field | `id` | id | yes | `fld:<CONNECTION_RESOURCE_NAME>/<OBJECT_NAME>/<FIELD_NAME>` |
| | `of` | id | yes | the `obj:` it belongs to |
| | `name` | string | yes | the field name as `describe` returns it, case-sensitive |
| | `displayName` | string \| null | yes, may be null | `displayName` as `describe` returns it. It is the one human-readable signal in the channel and phase 3 settles real bindings on it — `InstallDate` over `CreatedDate` on the strength of *"Install Date"* — so a correspondence decision citing it needs it recorded |
| | `declaredType` | string | yes | the connector's declared type. Never null — `declaredType` and `proseType` are never both absent |
| | `proseType` | string \| null | yes, may be null | the real column type transcribed from `description`, **only where the declared type was flattened** (pipeline guide phase 2 limit 3). Null means the declared type stands. A width inside it (`VARCHAR(32)`) is the only trace of a length there is, and it is read from here rather than given a key of its own |
| | `referenceTargetDeclared` | string \| null | yes, may be null | the `reference` projection verbatim. Null means *the connector declares no reference*, never *the source has none* |
| | `referenceTarget` | id \| null | yes, may be null | the `obj:` that string resolves to on the same connection, when it resolves |
| | `values` | string[] \| null | yes, may be null | `enum`, verbatim and in order. Null where the connector declares no picklist — which is everywhere outside Salesforce on the connectors run |

**Three keys the record does not have, on purpose.** No `nullable` and no `length` anywhere: neither is in the `describe` projection on any connector, so either key would be null on every field and would read as *observed and unconstrained* rather than *not observable*. And **no per-field key or uniqueness flag**: the object's one `primaryKey` is the whole of what the metadata declares, so a field has no key field in which to claim a uniqueness the metadata cannot support.

```json
{"model":"fieldservice",
 "allowListedConnectors":["uipath-salesforce-sfdc","uipath-snowflake-snowflake","uipath-servicenow-servicenow",
                          "uipath-uipath-jdbc","uipath-sap-c4cv2","uipath-workday-workdayrest",
                          "uipath-microsoft-azureactivedirectory","uipath-coupa-coupa","uipath-sap-odata"],
 "connections":[
  {"id":"con:<SF_CONNECTION>","resourceName":"<SF_CONNECTION>","connectorKey":"uipath-salesforce-sfdc",
   "connectionId":"<SF_CONNECTION_ID>","allowListed":true,"state":"Enabled",
   "objects":[
    {"id":"obj:<SF_CONNECTION>/Asset","of":"con:<SF_CONNECTION>","object":"Asset","fieldsExposed":110,
     "primaryKey":"fld:<SF_CONNECTION>/Asset/Id","stop":null,
     "excluded":[{"field":"<the 98 fields no class binds>","reason":"scenario-relevant subset recorded; E9"}],
     "fields":[
      {"id":"fld:<SF_CONNECTION>/Asset/Id","of":"obj:<SF_CONNECTION>/Asset","name":"Id","displayName":"Asset ID",
       "declaredType":"string","proseType":null,"referenceTargetDeclared":null,"referenceTarget":null,"values":null},
      {"id":"fld:<SF_CONNECTION>/Asset/InstallDate","of":"obj:<SF_CONNECTION>/Asset","name":"InstallDate",
       "displayName":"Install Date","declaredType":"string","proseType":null,
       "referenceTargetDeclared":null,"referenceTarget":null,"values":null},
      {"id":"fld:<SF_CONNECTION>/Asset/Status","of":"obj:<SF_CONNECTION>/Asset","name":"Status",
       "displayName":"Status","declaredType":"string","proseType":null,
       "referenceTargetDeclared":null,"referenceTarget":null,
       "values":["Shipped","Installed","Registered","Obsolete","Purchased"]},
      {"id":"fld:<SF_CONNECTION>/Asset/AccountId","of":"obj:<SF_CONNECTION>/Asset","name":"AccountId",
       "displayName":"Account ID","declaredType":"string","proseType":null,
       "referenceTargetDeclared":null,"referenceTarget":null,"values":null}]}]},
  {"id":"con:<SNOW_CONNECTION>","resourceName":"<SNOW_CONNECTION>","connectorKey":"uipath-snowflake-snowflake",
   "connectionId":"<SNOW_CONNECTION_ID>","allowListed":true,"state":"Enabled",
   "objects":[
    {"id":"obj:<SNOW_CONNECTION>/PARTS_RESERVATION","of":"con:<SNOW_CONNECTION>","object":"PARTS_RESERVATION",
     "fieldsExposed":11,"primaryKey":"fld:<SNOW_CONNECTION>/PARTS_RESERVATION/RESERVATION_ID","stop":null,
     "excluded":[],
     "fields":[
      {"id":"fld:<SNOW_CONNECTION>/PARTS_RESERVATION/RESERVATION_ID","of":"obj:<SNOW_CONNECTION>/PARTS_RESERVATION",
       "name":"RESERVATION_ID","displayName":"RESERVATION_ID","declaredType":"string","proseType":"VARCHAR(32)",
       "referenceTargetDeclared":null,"referenceTarget":null,"values":null},
      {"id":"fld:<SNOW_CONNECTION>/PARTS_RESERVATION/WO_ID","of":"obj:<SNOW_CONNECTION>/PARTS_RESERVATION",
       "name":"WO_ID","displayName":"WO_ID","declaredType":"string","proseType":"VARCHAR(64)",
       "referenceTargetDeclared":null,"referenceTarget":null,"values":null},
      {"id":"fld:<SNOW_CONNECTION>/PARTS_RESERVATION/WO_REFERENCE","of":"obj:<SNOW_CONNECTION>/PARTS_RESERVATION",
       "name":"WO_REFERENCE","displayName":"WO_REFERENCE","declaredType":"string","proseType":"VARCHAR(64)",
       "referenceTargetDeclared":null,"referenceTarget":null,"values":null},
      {"id":"fld:<SNOW_CONNECTION>/PARTS_RESERVATION/QTY_REQUESTED","of":"obj:<SNOW_CONNECTION>/PARTS_RESERVATION",
       "name":"QTY_REQUESTED","displayName":"QTY_REQUESTED","declaredType":"number","proseType":"NUMBER(12,3)",
       "referenceTargetDeclared":null,"referenceTarget":null,"values":null},
      {"id":"fld:<SNOW_CONNECTION>/PARTS_RESERVATION/CREATED_ON","of":"obj:<SNOW_CONNECTION>/PARTS_RESERVATION",
       "name":"CREATED_ON","displayName":"CREATED_ON","declaredType":"string","proseType":"TIMESTAMP_NTZ(9)",
       "referenceTargetDeclared":null,"referenceTarget":null,"values":null}]}]}]}
```

Two readings the example carries. `WO_ID` and `WO_REFERENCE` are both `VARCHAR(64)`, neither name matches a Salesforce column and `referenceTargetDeclared` is null on both — which is why the work-order reference is a phase 3 exception rather than a binding. And every Snowflake field carries a `proseType`: the connector flattens every column to `string` or `number`, so the real type survives in `description` alone and every agreement row over this object reads **unverifiable**.

## Shape — the partition manifest

`<MODEL_NAME>-partition.json`, phase 4. The rules on it are the pipeline guide phase 4 § The partition manifest, and the procedure that fills it is its § How to choose a partition.

| Field | Type | Required | Is |
|---|---|---|---|
| `model` | string | yes | `<MODEL_NAME>` |
| `toOneSubgraph` | id[] | yes, may be empty | the `op:` ids carrying `sh:maxCount 1` — the subgraph step 1 of the procedure built, and the input every later step ran on. An object property absent from it is to-many and forces its target to stand alone |
| `classification` | object[] | yes | one record per federated class: `class` (the `cls:`), `role` (`always-fact`, `always-dimension`, `isolated` or `hybrid` — **the whole vocabulary**) and `basis` (string, the edges it was classified on). **Only a hybrid was a choice**; the other three were decided by their edges, so a cover that cannot be re-derived from this table is not reproducible |
| `federated` | object[] | yes | one record per group. **Every federated class appears in exactly one group** — two records naming the same class are the two-entity cover of phase 3, and both carry a `forcingSignal` |
| `native` | object[] | yes, may be empty | the lane split's record. **Omitting it is how a class disappears** |

| Record | Field | Type | Required | Is |
|---|---|---|---|---|
| group | `id` | id | yes | `grp:<ENTITY_NAME>` |
| | `entityName` | string | yes | the name phase 4 derived and `create` adjudicates (pipeline guide phase 4 § Entity names) |
| | `classes` | id[] | yes | the `cls:` ids folded into this group |
| | `cells` | id[] | yes | the `cell:` ids the group covers |
| | `primaryCell` | id | yes | the cell whose object every join starts at. A single-source group repeats its only cell |
| | `pattern` | string | yes | `federated star` or `federated single-source` — the whole vocabulary |
| | `forcingSignal` | object \| null | yes, may be null | null when nothing forced the boundary, so a rerun can tell a forced cut from a chosen one. Otherwise `signal` (string, the pipeline guide phase 4 § Forced to stand alone signal) and `property` (the `op:` that forces it, or null) |
| | `tieBreak` | string \| null | yes, may be null | which tie-break of the pipeline guide phase 4 § How to choose a partition step 5 fired when two hubs could have absorbed the same spoke or two covers tied, and null when none did. **Without it the cover is reproducible and the reason it was taken is not** |
| | `expectedCollisions` | string[] | yes, may be empty | the external field names appearing on more than one of the group's sources, computed from the matrix. Phase 6 reads the real names back and **never predicts them** ([federated-mapping-guide.md § Column names](federated-mapping-guide.md)); this list only says where to look |
| native | `class` | id | yes | the `cls:` leaving the pipeline here |
| | `sourceOfRecord` | string | yes | the annotation that sent it to the native lane |

```json
{"model":"fieldservice",
 "toOneSubgraph":["op:servicedAccount","op:concernsAsset","op:installedAtAccount","op:drawsFromStock"],
 "classification":[
  {"class":"cls:ServiceWorkOrder","role":"always-fact","basis":"outgoing to-one only: servicedAccount, concernsAsset"},
  {"class":"cls:ServiceAccount","role":"always-dimension","basis":"incoming to-one only"},
  {"class":"cls:InstalledAsset","role":"hybrid","basis":"incoming concernsAsset, outgoing installedAtAccount"},
  {"class":"cls:PartReservation","role":"always-fact","basis":"outgoing drawsFromStock; its only incoming edge is to-many"},
  {"class":"cls:PartStockPosition","role":"always-dimension","basis":"incoming to-one only"}],
 "federated":[
  {"id":"grp:ServiceWorkOrder","entityName":"ServiceWorkOrder",
   "classes":["cls:ServiceWorkOrder","cls:ServiceAccount","cls:InstalledAsset"],
   "cells":["cell:ServiceWorkOrder__WorkOrder","cell:ServiceAccount__Account","cell:InstalledAsset__Asset"],
   "primaryCell":"cell:ServiceWorkOrder__WorkOrder","pattern":"federated star","forcingSignal":null,
   "tieBreak":null,
   "expectedCollisions":["Id","AccountId","Name","Status","CreatedDate"]},
  {"id":"grp:PartReservation","entityName":"PartReservation",
   "classes":["cls:PartReservation","cls:PartStockPosition"],
   "cells":["cell:PartReservation__PARTS_RESERVATION","cell:PartStockPosition__WarehouseInventory"],
   "primaryCell":"cell:PartReservation__PARTS_RESERVATION","pattern":"federated star",
   "forcingSignal":{"signal":"to-many target","property":"op:hasPartReservation"},
   "tieBreak":null,
   "expectedCollisions":[]}],
 "native":[]}
```

Two groups over five classes, which is the entity floor — a star cover — against a ceiling of five, one per class. `ServiceWorkOrder` holds 3 sources and 2 joins, `PartReservation` 2 and 1; both are inside `MAX_SOURCES` 6. `PartReservation` could not be absorbed into the work-order star at all: `hasPartReservation` carries no `sh:maxCount`, which is the forcing signal recorded against it. `native` is empty because no class carried `:sourceOfRecord` — the split itself rests on a ledger decision, which is a different thing from a class annotated `UiPath`.

## Shape — entities.json

Phase 5. The rules on `body` are the pipeline guide phase 5.

The file is one key, `entities` (object[], required): one entry per entity, each with the fields below and no others.

| Field | Type | Required | Is |
|---|---|---|---|
| `id` | id | yes | `ent:<ENTITY_NAME>` |
| `name` | string | yes | the entity name, as `create` takes it |
| `group` | id | yes | the `grp:` this entity was emitted for. **This is the link that used to be a name match** — a `group` that resolves to no record, or to a record whose `entityName` differs from `name`, is the naming fault the pack exists to catch |
| `body` | object | yes | exactly what `--body` takes |

The entity's cells and classes are not repeated here: they are one hop away through `group`. Its sources are not repeated either — `body.externalFields[].connectionName` and `.object` mint the `obj:` ids.

**The invariant that earns the envelope:** `body` passes through to `uip df entities create` **unchanged** — no enrichment, no reshaping, no keys of the pipeline's own, and no key substituted before the call. **Every pipeline key sits beside `body`, never inside it.** The moment the body itself diverges, the file stops recording what was called and becomes a format to maintain.

```json
{"entities":[
 {"id":"ent:ServiceWorkOrder","name":"ServiceWorkOrder","group":"grp:ServiceWorkOrder",
  "body":{
    "externalFields":[
      {"connectionName":"<SF_CONNECTION>","object":"WorkOrder",
       "fields":["Id","WorkOrderNumber","Subject","Status","StatusCategory","Priority","StartDate","EndDate",
                 "GrandTotal","LineItemCount","IsClosed","AccountId","AssetId"]},
      {"connectionName":"<SF_CONNECTION>","object":"Account",
       "fields":["Id","AccountNumber","Name","Industry","Type","NumberOfEmployees","AnnualRevenue","IsPartner",
                 "Website","Customer_Tier__c","CreatedDate"]},
      {"connectionName":"<SF_CONNECTION>","object":"Asset",
       "fields":["Id","SerialNumber","Name","StockKeepingUnit","ProductCode","Status","InstallDate","IsInternal","AccountId"]}],
    "joins":[
      {"source":"WorkOrder","relatedSource":"Account","sourceField":"AccountId","relatedField":"Id",
       "sourceConnectionName":"<SF_CONNECTION>","relatedConnectionName":"<SF_CONNECTION>"},
      {"source":"WorkOrder","relatedSource":"Asset","sourceField":"AssetId","relatedField":"Id",
       "sourceConnectionName":"<SF_CONNECTION>","relatedConnectionName":"<SF_CONNECTION>"}]}},
 {"id":"ent:PartReservation","name":"PartReservation","group":"grp:PartReservation",
  "body":{
    "externalFields":[
      {"connectionName":"<SNOW_CONNECTION>","object":"PARTS_RESERVATION",
       "fields":["RESERVATION_ID","WO_ID","WO_REFERENCE","MATERIAL_NO","PLANT_CODE","RESERVATION_STATUS",
                 "QTY_REQUESTED","QTY_CONFIRMED","CREATED_ON","PROMISED_DATE"]},
      {"connectionName":"<DB_CONNECTION>","object":"WarehouseInventory",
       "fields":["ProductSKU","TotalOnHand","TotalAvailable"]}],
    "joins":[
      {"source":"PARTS_RESERVATION","relatedSource":"WarehouseInventory",
       "sourceField":"MATERIAL_NO","relatedField":"ProductSKU",
       "sourceConnectionName":"<SNOW_CONNECTION>","relatedConnectionName":"<DB_CONNECTION>"}]}}]}
```

Every join gives `source` the same primary — `WorkOrder` twice, which is the star rule — and the primary itself is never declared. `WO_REFERENCE` and `Asset.AccountId` are selected although no data property maps either: fields are write-once, so selecting them now keeps a later resolution of the work-order reference and of the spoke-to-spoke edge from costing a delete and a recreate. `PartReservation` joins across two connectors, which is legal in a body and shows up later as the target mapping's `sourceSystems:` question.

## Shape — the check report

`<MODEL_NAME>-check.json`, phase 7. What each part means, the rejections to expect, the vocabulary bridge, the agreement rule and the reconciliation are [federated-check-guide.md](federated-check-guide.md).

| Field | Type | Required | Is |
|---|---|---|---|
| `model` | string | yes | `<MODEL_NAME>` |
| `run` | string | yes | the manifest's `run`, so a report is attributable to one run of the pack |
| `verdict` | object[] | yes | one row per artifact **and per input**: `artifact` (its `path` as the manifest lists it, under `inputs` or `artifacts` — the `.ofn` and the constraints `.ttl` take a row of their own, because a rule that refuses the input blocks every artifact derived from it), `state` (`clear` or `blocked` — **the whole vocabulary**), `blockedBy` (the `E<n>` ids, empty when clear), `expectedRejections` (number) |
| `expectedRejections` | object[] | yes, may be empty | `site` (string, the shipped rule or check that rejects a correct artifact — `XF-015`, `firstMappingByClass` and `SHC-002` are the ones seen so far, and the vocabulary is open because the next run meets the next one), `reached` (boolean, **whether the rule actually ran** — a prediction that never fired is not a prediction confirmed, and a run blocked before the cross-file rules reports every one of them `false`), `blocks` (the `blk:` ids it touches), `reason`, `decision` (the `D<n>` recording it). An expected rejection blocks nothing |
| `datatypeAgreement` | object[] | yes | one row per cell per property — the four readings and the three comparisons |
| `reconciliation` | object[] | yes | one row per declared fact |
| `coverage` | object | yes | the counts of [federated-check-guide.md § Coverage](federated-check-guide.md) |
| `openItems` | object[] | yes, may be empty | what goes to the target environment or the model's owner: `subject` (an id), `item` |
| `handChecks` | object[] | yes, may be empty | the blocks `firstMappingByClass` skipped and this run checked by hand: `block` (a `blk:`), `result`. **An unperformed check reported as a pass is worse than the rejection** |
| `notPerformed` | object[] | yes, may be empty | every check this run did not run, `check` (string) and `why` (string) — the cross-file rules when nothing attached, a hand check that was not needed, anything outside the lane. `handChecks` records what was performed; without this key a check that never ran is indistinguishable from one that passed, which is the failure the check guide § Stops rule 2 names |

A `datatypeAgreement` row: `cell` (a `cell:`), `property` (a `dp:`), `field` (an `fld:`), `declared` / `observed` / `created` / `authored` (the four readings, each a string or null — a missing reading is null, never a passing comparison), and `declaredVsAuthored` / `declaredVsObserved` / `declaredVsCreated`, each `agree`, `defect`, `reconciliation` or `unverifiable`.

A `reconciliation` row: `declared` (string \| null, the SHACL term — **null where the observation is the one with no declaration**, which is the inverse row a source that constrains what the model leaves open produces), `subject` (id[], the `dp:` or `op:` ids the row covers — **several, because one declaration contradicted the same way across six properties is one finding, not six**), `observed`, `created` (what the platform actually built, which is a third reading and not the same as `enforced`), `enforced` (whether the platform holds the line), `note`.

```json
{"model":"fieldservice","run":"run:fieldservice/<START_TIMESTAMP>",
 "verdict":[
  {"artifact":"schema.ofn","state":"blocked","blockedBy":["E8"],"expectedRejections":0},
  {"artifact":"constraints-shapes.ttl","state":"blocked","blockedBy":["E8"],"expectedRejections":1},
  {"artifact":"fieldservice-source.yarrrml","state":"blocked","blockedBy":["E2","E3"],"expectedRejections":0},
  {"artifact":"fieldservice.yarrrml.yml","state":"blocked","blockedBy":["E2","E4"],"expectedRejections":3},
  {"artifact":"resources/solution_folder/ontology/fieldservice.json","state":"clear","blockedBy":[],"expectedRejections":0}],
 "expectedRejections":[
  {"site":"XF-015","reached":false,"blocks":["blk:ServiceWorkOrder","blk:PartReservation"],
   "reason":"three condition-less same-row joins, which R2RML §8 permits; the cross-file rules never ran (E8)","decision":"D12"},
  {"site":"SHC-002","reached":true,"blocks":[],
   "reason":"the rule counts the string sh:targetClass inside a # comment as a sixth shape; all five shapes carry a sh:NodeShape","decision":"D11"}],
 "datatypeAgreement":[
  {"cell":"cell:ServiceWorkOrder__WorkOrder","property":"dp:ServiceWorkOrder.grandTotal",
   "field":"fld:<SF_CONNECTION>/WorkOrder/GrandTotal",
   "declared":"xsd:decimal","observed":"number","created":"DECIMAL","authored":"xsd:decimal",
   "declaredVsAuthored":"agree","declaredVsObserved":"reconciliation","declaredVsCreated":"reconciliation"},
  {"cell":"cell:PartReservation__PARTS_RESERVATION","property":"dp:PartReservation.quantityRequested",
   "field":"fld:<SNOW_CONNECTION>/PARTS_RESERVATION/QTY_REQUESTED",
   "declared":"xsd:decimal","observed":"NUMBER(12,3)","created":"DECIMAL","authored":"xsd:decimal",
   "declaredVsAuthored":"agree","declaredVsObserved":"unverifiable","declaredVsCreated":"reconciliation"}],
 "reconciliation":[
  {"declared":"sh:datatype xsd:dateTime",
   "subject":["dp:ServiceAccount.accountCreatedOn","dp:InstalledAsset.installedOn","dp:ServiceWorkOrder.scheduledStart",
              "dp:ServiceWorkOrder.scheduledEnd","dp:PartReservation.reservationCreatedOn","dp:PartReservation.promisedOn"],
   "observed":"string","created":"NVARCHAR(200)","enforced":"no",
   "note":"highest-signal row: the model asserts a timestamp and neither the source metadata nor the platform carries one. No connector of this model declares date, and the map keys off the connector's declaration"},
  {"declared":"sh:maxLength",
   "subject":["dp:InstalledAsset.serialNumber","dp:PartReservation.reservationNumber",
              "dp:PartReservation.plantCode","dp:PartReservation.materialNumber"],
   "observed":"prose width on Snowflake only","created":"NVARCHAR(200)","enforced":"no",
   "note":"128, 32, 8 and 64 declared; every one lands on 200. The length is hard-coded"},
  {"declared":null,
   "subject":["dp:ServiceAccount.industry","dp:ServiceAccount.accountType","dp:ServiceWorkOrder.workOrderStatus",
              "dp:ServiceWorkOrder.workOrderStatusCategory","dp:ServiceWorkOrder.workOrderPriority",
              "dp:InstalledAsset.assetStatus"],
   "observed":"Salesforce declares a picklist on all six","created":"NVARCHAR(200)","enforced":"no",
   "note":"the inverse row — the source constrains values the model leaves open. A report to the model's owner, never an edit"}],
 "coverage":{
  "terms":[{"kind":"class","count":5,"withLabel":5,"withComment":5},
           {"kind":"objectProperty","count":5,"withLabel":5,"withComment":5},
           {"kind":"dataProperty","count":38,"withLabel":38,"withComment":4}],
  "dataPropertiesWithoutDatatype":0,"objectPropertiesWithoutMaxCount":1,"classesWithoutSourceOfRecord":5},
 "openItems":[
  {"subject":"cls:ServiceWorkOrder","item":"the ontology IRI must be re-declared under https://ontology.uipath.com/ before any artifact attaches"},
  {"subject":"op:installedAtAccount","item":"an authored form for an object property between two spokes of one star"}],
 "handChecks":[],
 "notPerformed":[
  {"check":"every cross-file rule between the three artifacts","why":"uip ont files add attached nothing (E8)"},
  {"check":"the hand check of blocks firstMappingByClass skips","why":"no class in this model has a second block"},
  {"check":"whether a file under resources/ is a registered solution resource","why":"out of this lane; pack, publish and deploy were not run"}]}
```

Why `coverage.terms` is a list and not three numbers: XF-007 fails a model **whose properties carry labels and no comments**, which is the common shape and exactly what this run hit — 38 data properties labelled, 4 commented. Flat totals of 48 and 14 would report the same shortfall and say nothing about where it sits, and the shortfall is reported per kind or not usefully at all. The totals are the sum of the rows.

## Shape — a ledger row

`<MODEL_NAME>-ledger.json`. The three row kinds, when each is written, and the five rules on them — ids never reused, append-only with no state field, every decision naming what it chose between, every exception naming what it blocks, a touch point being a decision — are [federated-entity-pipeline-guide.md § The ledger](federated-entity-pipeline-guide.md). A flat `rows` array in write order.

| Field | Type | Required | Is |
|---|---|---|---|
| `id` | string | yes | `D<n>`, `E<n>` or `R<n>` |
| `kind` | string | yes | `decision`, `exception` or `resolution` |
| `phase` | string | yes | `bootstrap`, or `1`–`7` |
| `subject` | id[] | yes | the records the row is about. A row whose subject is a name not yet a record carries an empty array and says it in `why` |
| `chose` | string | `decision` only | what was taken — an id where the choice was between records, free text otherwise |
| `over` | string[] | `decision` only | what it was chosen over. Non-empty, except for a touch point (rule 3) |
| `why` | string | `decision`, `resolution` | the reason; for a touch point, the fallback |
| `blocks` | string[] | `exception` only | what does not get written: a record id, or an artifact's `path` as the pack manifest lists it |
| `needs` | string | `exception` only | what a person must resolve. Where the blocked thing is narrower than a whole record — one `po:` entry of a block — `blocks` names the record and `needs` names the entry |
| `recommends` | string | `exception` only | what the pipeline would take if the person said nothing, and **never what it did take**. Every stop in this lane computes before it asks ([federated-entity-pipeline-guide.md § Anti-patterns](federated-entity-pipeline-guide.md) 5), so an exception with no recommendation is a bare stop handed to someone who cannot answer it. Where the run proceeded on the recommendation rather than waiting, the `D<n>` that did so names this `E<n>` in `why` and the cost of a different answer belongs in `needs` |
| `closes` | string | `resolution` only | the `E<n>` this row closes |
| `decided` | string | `resolution` only | what the person decided — an id where the answer was a record |

```json
{"rows":[
 {"id":"D1","phase":"1","kind":"decision","subject":[],
  "chose":"every class federated","over":["every class native","stop the run"],
  "why":"no class carries :sourceOfRecord, and the three systems holding them are external. Proceeding on E1's recommendation; the rule is to stop"},
 {"id":"E1","phase":"1","kind":"exception",
  "subject":["cls:ServiceWorkOrder","cls:ServiceAccount","cls:InstalledAsset","cls:PartReservation","cls:PartStockPosition"],
  "blocks":["fieldservice-partition.json"],
  "needs":"which classes, if any, are UiPath system-of-record",
  "recommends":"all five federated"},
 {"id":"D2","phase":"3","kind":"decision",
  "subject":["cell:InstalledAsset__Asset","dp:InstalledAsset.installedOn"],
  "chose":"fld:<SF_CONNECTION>/Asset/InstallDate","over":["fld:<SF_CONNECTION>/Asset/CreatedDate"],
  "why":"the field's displayName is \"Install Date\"; CreatedDate is the record's own creation"},
 {"id":"E2","phase":"3","kind":"exception",
  "subject":["op:hasPartReservation"],
  "blocks":["cell:ServiceWorkOrder__WorkOrder","blk:ServiceWorkOrder"],
  "needs":"which pair carries the work-order reference: WorkOrder.Id to WO_ID, or WorkOrder.WorkOrderNumber to WO_REFERENCE, or the swap. Both child columns are VARCHAR(64) and no referential metadata exists. A different answer re-authors the po: entry in both YARRRML files",
  "recommends":"WorkOrder.Id to WO_ID"},
 {"id":"E3","phase":"3","kind":"exception",
  "subject":["op:drawsFromStock"],
  "blocks":["cell:PartReservation__PARTS_RESERVATION","ent:PartReservation"],
  "needs":"whether MATERIAL_NO or UNIT_SERIAL matches WarehouseInventory.ProductSKU. The entity was created on the recommendation, so a different answer costs a delete and a recreate",
  "recommends":"MATERIAL_NO"},
 {"id":"D9","phase":"5","kind":"decision","subject":["ent:ServiceWorkOrder","ent:PartReservation"],
  "chose":"LeftJoin","over":[],
  "why":"touch point — the join type is hard-coded, confirmed on the created entity as SourceJoinCriterias[].JoinType. A NULL key is expected to generate no term; no fallback exists in this lane"},
 {"id":"D13","phase":"4","kind":"decision","subject":["grp:ServiceWorkOrder"],
  "chose":"ServiceWorkOrder","over":["ServiceWorkOrderView"],
  "why":"the stem of the group's primary cell's class, taken without the folded-group suffix and accepted by create"}
]}
```

`D1` carries an empty `subject` and names its classes in the exception instead, because the lane itself is not a record. `D9` is the one row with an empty `over`: a touch point had no alternative to weigh, and its value is the fallback in `why`. `E3` is the dangerous shape — an exception the run proceeded past, where the answer now costs a delete and a recreate, which is why that cost sits in `needs`.

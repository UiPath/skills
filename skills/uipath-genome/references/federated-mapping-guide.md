# Federated Mapping Guide — the target YARRRML over created entities

Phase 6 of [federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md): rewrite the source YARRRML against the federated entities that phase 5 created. This guide is the syntax of that rewrite and nothing else — the phase contracts, stop conditions and the ledger stay in the pipeline guide.

**YARRRML** is what is authored here; **R2RML** names what it compiles to. Never "YAML", never bare "RML".

Read this when the entities exist and their column names can be read back, not before.

**One file.** An ontology carries exactly one `mapping` artifact, so the target YARRRML is a single file holding every block, named `<name>.yarrrml.yml` (`.yml` and `.yaml` also resolve). The source YARRRML of phase 3 is not an ontology artifact and cannot be attached beside it.

**It stays YARRRML.** Every other artifact of the pack is JSON because the pack is machine-read; this file is not an exception to that decision but a case of it. **This is the mapping artifact the platform itself consumes** — it takes the one `mapping` slot, `uip ont validate` runs the shipped cross-file rules over it, and the CLI's own YARRRML parser reads it, so it is already machine-parseable. Rewriting it as JSON leaves the ontology with no mapping ([federated-entity-pipeline-guide.md § Why the two YARRRML files stay YARRRML](federated-entity-pipeline-guide.md)).

## Conventions that carry over

The target YARRRML is the same language as the Data Fabric-side mappings already in use, and their spelling carries over as it stands. A new spelling is introduced only where an existing convention cannot say what this lane needs. Where a convention assumes one table per class, it is adopted for its spelling, not for its assumption.

1. **Compact form only.** `s:` / `po:` / `p:` / `o:`. Never `subjects:`, `predicateobjects:`, `predicate:`, `object:`, or an inline `~iri` relationship.
2. **The block key is the class name** for a class with one block, matching the `.ofn` exactly. A class with several blocks takes **`<Class>__<Entity>`** per block — the class name, double underscore, the entity name — mirroring the source YARRRML's `<Class>__<Object>`. The later keys have to be derivable because `mapping:` names a block key exactly, and a class with one block keeps the bare class name. `[a, ont:<Class>]` appears in **every** block of the class whatever its key. **The key is also the block's id** — `blk:<key>` — which is how this file joins the pack's graph without carrying an `id` of its own, and `table:` names the `ent:` the block sits over ([federated-entity-pipeline-guide.md § Ids](federated-entity-pipeline-guide.md)).
3. **`prefixes:` declares `ont:`** as the model's namespace IRI.
4. **`table:` is the only link to the entity.** Never write an entity id, a folder id or a connection id into a mapping.
5. **The `# USAGE POLICY` comment block** heads the file, before `prefixes:`, as it does in the mappings already in use (§ The USAGE POLICY block).

## Column names

**Read them back; never derive them.** The CLI derives an internal name per column at create (`deriveInternalName`, `data-fabric-tool`, `src/utils/federated-payload.ts`).

**The derivation is not camelCase.** The external name is split on runs of non-alphanumerics, the separators are dropped, the **first segment is kept exactly as it came**, and each later segment has only its **first character upper-cased with the remainder preserved**. A lowercase input happens to come out camelCased; nothing else does.

| Input | Segments | Result |
|---|---|---|
| `short_description` | `short`, `description` | `shortDescription` — camelCase only because the input was already lowercase |
| `RESERVATION_ID` | `RESERVATION`, `ID` | `RESERVATIONID` — not `reservationId` |
| `Customer_Tier__c` | `Customer`, `Tier`, `c` | `CustomerTierC` |

**Predict an all-caps column with the camelCase rule and every one is wrong.** Snowflake and most warehouse connectors expose all-caps columns, so that is the common case, not the exotic one.

Two more rules on the single name, applied in this order:

| Rule | Example |
|---|---|
| `f` prefixed when the result does not start with a letter | `2ndLine` → `f2ndLine` |
| `Field`, then `Col`, appended when the result is a reserved field name or fails the field-name format (letters and digits only, 3–100 characters) | `Id` → `IdField`; a name still invalid → `<name>Col` |

**Then the collision rules, over the entity's one flat namespace.** It spans **every** source, and no column may equal the entity name. Three mechanisms compose, and they escalate in this order — the numeric suffix is the last resort, not the second step:

| Step | Mechanism | Applies |
|---|---|---|
| 1 | the reserved/invalid suffix — `Field`, then `Col` | per name, before any collision is considered |
| 2 | the object-name prefix: the first source in `externalFields` order keeps the name; each later one is prefixed with its own object name, derived the same way, and the kept name capitalised | on a collision |
| 3 | a numeric suffix from `2` | only when the **prefixed** name also collides |

A three-source entity over `WorkOrder`, `Account` and `Asset`, as observed:

| External | Derived | Why |
|---|---|---|
| `WorkOrder.Id` | `IdField` | step 1 — `Id` is a system field name, so `validateName` rejects the bare name |
| `Account.Id` | `AccountIdField` | step 2 — `IdField` was taken; the prefix goes on the already-suffixed name |
| `Asset.Id` | `AssetIdField` | step 2 again |
| `Asset.Name` | `AssetName` | step 2 alone — `Name` is valid, so no step 1 |
| `Asset.Status` | `AssetStatus` | step 2 alone |

None of that is derivable from the model, and steps 2 and 3 depend on source order. Read the created entity:

```bash
uip df entities get <ENTITY_NAME> --local --output json
```

The derived names are `Fields[].Name`, under `Data` in the command's JSON envelope. Every `$(...)` in the file is one of them, case-sensitive, or a system field. A column the correspondence matrix expects and the entity does not carry is an exception, not a name to guess ([federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md) phase 6 § Stops).

**The entity also says which external field each derived name came from**, as `Fields[].ExternalFieldMappingDetail.ExternalFieldName` beside `.ExternalObjectId` — so the derived-to-external map is read off the entity rather than reconstructed from the correspondence matrix, and a column whose provenance surprises you is settled by the entity rather than argued.

**Five system fields come back on every entity** and belong to none of the sources: `Id` (`UNIQUEIDENTIFIER`, the primary key), `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy`. They are why `Id` is a reserved field name and why a source's own `Id` column is `IdField` on the first source that selects one.

## Block shape

One block per (class, entity) pair:

```yaml
prefixes:
  ont: https://ontology.uipath.com/<MODEL_NAME>#

mappings:
  <ClassName>:
    sources:
      - access: datafabric
        table: <ENTITY_NAME>
        referenceFormulation: rr:SQL2008
        system: <CONNECTOR_KEY>
    s: ont:<ClassName>/$(<KEY_COLUMN>)
    po:
      - [a, ont:<ClassName>]
      - [ont:<ClassName>.<propName>, $(<COLUMN>)]
      - [ont:<ClassName>.<numericProp>, $(<COLUMN>), xsd:decimal]
```

- `access: datafabric`, `referenceFormulation: rr:SQL2008` — both literal, in every source block.
- `table: <ENTITY_NAME>` — the local entity's name, case-sensitive. A federated entity is named the same way a native one is.
- `system: <CONNECTOR_KEY>` — the Integration Service connector key of the entity's source, never a connection name or id. It changes no data and no query; it tells the viewer which icon to draw, and a block without it is drawn as Data Fabric's own storage even when the entity is federated (§ Several connectors behind one entity).
- **`[a, ont:<ClassName>]` is required in every block.** Without it the instances are untyped.
- **A field selected only to carry a create-time join is not a data property.** It sits in the entity's columns and gets no `po:` row unless the model declares a property for it.

## Several connectors behind one entity

A federated entity may join sources on different connectors, so one block's `system:` cannot name all of them. The convention carried over from the mappings already in use keeps the **main** connector on `system:` and lists the departures in a `sourceSystems:` map on the same mapping, keyed by ontology property or source column:

```yaml
  PartReservation:
    sources:
      - access: datafabric
        table: PartReservation
        referenceFormulation: rr:SQL2008
        system: uipath-snowflake-snowflake
    sourceSystems:
      ont:PartStockPosition.partSku: uipath-uipath-jdbc
      ont:PartStockPosition.totalOnHand: uipath-uipath-jdbc
```

That is a real entity: `PARTS_RESERVATION` on Snowflake is the primary and `WarehouseInventory` on Database Hub is its one dimension, so the main connector covers the fact and the departures are the dimension's three columns.

**What is verified and what is not.** The shipped YARRRML rules read only `table:` off a source block — neither `system:` nor `sourceSystems:` is parsed, validated or rejected by `uip ont validate`, so writing either costs nothing and a wrong value is caught by nothing. Both are viewer-side spelling, and the effect of `sourceSystems:` was **not** observed on a run. Write it where the entity spans connectors, record it as a decision naming that it is unverified, and never report it as a checked fact. Where the main connector is the only thing a reader needs, `system:` alone is complete; the departures are presentation, not a binding.

## The USAGE POLICY block

The file's first lines, before `prefixes:`. It is the **rule** layer — imperative rules for whoever, agent or tool, reads the file as text. Facts (what a status value means, the grain, value domains) belong in `rdfs:comment` in the `.ofn`; bindings (which column joins which) belong in the `condition:` blocks. Reference them; never restate them.

```yaml
# ============================================================================
# USAGE POLICY  (how to use the constructs; facts live in <MODEL_NAME>.ofn)
# ============================================================================
# JOIN GRAPH (join only what the question needs):
#   <ClassName> → <TargetClassName> via <ClassName>.<prop> = <TargetClassName>.<KEY_COLUMN>
# ROUTING (canonical property for an ambiguous phrase):
#   "<phrase>" → <ClassName>.<propName>
# GRAIN DISCIPLINE:
#   <ClassName>: ONE row per <KEY_COLUMN>
# LITERALS are case- and format-sensitive. Copy values exactly as annotated in <MODEL_NAME>.ofn.
# ============================================================================
```

Three rules on it: 30 non-empty lines or fewer; every rule names a construct that exists in this file or in the `.ofn`; a conditional rule states what to leave undone when its condition is false. It is a comment block — nothing parses it, so it is never a place to put a fact the artifacts must agree on.

## Subject identity

1. **The subject key is the natural key column**, the same column the create-time join reads: `s: ont:<ClassName>/$(<KEY_COLUMN>)`. There is **no key rewrite** in this lane — source and target join on the same natural key. The `$(Id)` form belongs to a native source.
2. **Several blocks for one class mint an identical subject.** A class drawing on several source objects has several blocks; identical subjects are the only thing that makes them describe one object instead of several. Phase 3 settled which column that is — use it in every one of the class's blocks.
3. Field names in `$()` are case-sensitive.

## Datatypes

The third element of a `po:` pair is the property's range. **A two-element pair is read as `xsd:string`.** Every data property whose range is not `xsd:string` carries that range as the third element (`xsd:decimal`, `xsd:integer`, `xsd:dateTime`, `xsd:date`, `xsd:boolean`, `xsd:anyURI`), or the mapped range disagrees with `sh:datatype`, which is the only place this lane keeps a datatype.

**`xsd:date` and `xsd:boolean` are usable here like any other range.** Data Fabric carries both natively — `CONNECTOR_TYPE_MAP` maps a connector `date` to `DATE` and a connector `boolean` to `BOOLEAN` — and nothing in the shipped cross-file rules validates a mapping's third element at all. What the Ontop grammar refuses is either datatype inside an OWL axiom, a `DataPropertyRange` in the `.ofn`; this lane writes none, because every datatype stays in SHACL ([federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md) phase 1 § Stops).

## Object-property joins

An object property between two classes mapped over **different** entities is a join on plain columns:

```yaml
po:
  - p: ont:<objectProperty>
    o:
      mapping: <TargetClassName>
      condition:
        function: equal
        parameters:
          - [str1, $(<COLUMN_ON_THIS_ENTITY>)]
          - [str2, $(<KEY_COLUMN_ON_TARGET_ENTITY>)]
```

1. `str1` resolves from **this** block's rows, `str2` from the **target** block's rows. Check each side against its own entity.
2. `ont:<objectProperty>` matches an `ObjectProperty` declared in the `.ofn`, and `mapping:` matches another block's key in this file exactly. A missing or misspelled target silently produces no join triples.
3. `str2` is the column on the **target** entity that matches, and which column that is depends on the direction of the property. For a to-one reference it is the target's subject key column, the same one its `s:` template reads. For a **to-many** — a parent pointing at its children — it is the child's foreign-key column back to this class, which is *not* the child's subject key and usually not in its `s:` template at all. R2RML's join condition compares any child column to any parent column; nothing requires either side to be a key. Never assume `Id`, and never assume the target side must be the subject key.
4. The join goes in the block of the class whose entity holds the referencing column. The inverse property gets no join; it is answered from this one.
5. **A range axiom fixed this join's endpoints, not its validity** ([federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md) § Principles rule 5). Phase 3 settled whether the field pair can carry the join; do not re-derive it here from the axiom.

## An intra-entity join is not represented

A federated entity presents **one flat row**. The joins that built it were consumed at create time, so an object property between two classes inside the same entity gets no `condition:`. R2RML allows this directly: a logical table is a table, a view **or** a SQL query, so `table: <ENTITY_NAME>` over a federated entity is the same construct as over a native one.

**A folded class is a second block over the same table.** It still exists in the `.ofn`, and `DataPropertyDomain` forbids hanging its properties off the host's subject. Host block and folded block both sit over `table: <ENTITY_NAME>`, each minting its own subject from its own key column, and the object property between them is a `mapping:` reference with **no `condition:`** — *same row*, rather than *join these queries*, which R2RML §8 permits precisely because both queries are the same table:

```yaml
po:
  - p: ont:<objectProperty>
    o:
      mapping: <FoldedClassName>
```

**The shipped checker rejects this block, and the block is right.** XF-015 demands a `condition:` on every join, so `uip ont validate` errors on the omission. Expect it by name, record it as a ledger decision and leave the block as it is; the fix belongs in the CLI ([federated-check-guide.md § Three rejections to expect](federated-check-guide.md)). `firstMappingByClass` is the other two sites: it skips the join checks on every block after a class's first, and it misreports a join whose `mapping:` names a block of its range class that is not that class's first.

**Fallback.** If the ontology *service* refuses the omission at runtime — a different failure, found by running something rather than by validating — write an explicit self-join on the shared key, `str1` and `str2` both reading the folded class's key column on the same entity, and record the fallback as a ledger decision. Do not reach for it to quiet XF-015.

### Open case — an object property between two spokes of one star

**Observed, unresolved. Do not resolve it by choosing a form.**

An object property can run between two classes that are both *dimensions* of the same entity, neither of them the primary. Observed: `installedAtAccount` runs `Asset → Account`, and each of the two reached the primary on its own column — `WorkOrder.AssetId` and `WorkOrder.AccountId`.

Structurally the same-row form is **available**: both spokes' columns sit on the same flattened row, so a `mapping:` reference with no `condition:` parses and the entity is one table. But the two claims are not the same claim:

- the property asserts **this asset belongs to this account**;
- the row witnesses only that **both appear on the same work order**.

The second does not entail the first. One asset on two accounts' work orders produces both triples, and nothing in the row distinguishes a real relationship from a coincidence of co-occurrence. So the same-row form is structurally legal and semantically an over-claim, which is exactly the failure § Principles rule 5 of the pipeline guide names for a range axiom read as referential integrity.

The explicit-`condition:` form is no better here: anti-pattern 2 below forbids a `condition:` on an intra-entity join, because the join already ran at create and a condition re-joins a flat row against itself. **Neither form is clean.**

What is true: the relationship is faithfully representable only from an entity where **one of the two is the fact** — an `Asset` entity whose star reaches `Account`, or the reverse — because there the row witnesses the relationship rather than a shared parent. Whether that entity is worth creating is a partition question with process context behind it, not a mapping question.

**What the run does.** On meeting an object property whose domain and range are both non-primary cells of one entity, **raise a ledger exception** against that property, naming both spokes, the columns each reached the primary on, and both forms with the reason each is wrong. Do not emit either block. The exception blocks that `po:` entry and nothing else; every other block of both classes is written. Its `subject` names the `op:` and both `cls:` ids, its `blocks` names the `blk:` the entry would have sat in, and its `needs` names the entry — because what is blocked is narrower than the whole block ([federated-entity-pipeline-guide.md § The ledger](federated-entity-pipeline-guide.md)). Its `recommends` is **not** one of the two forms: it is an entity where one of the two spokes is the fact, so the row witnesses the relationship rather than a shared parent. Naming either form there would be recommending a block the run is forbidden to emit.

## Worked example

From a real run. Phase 4 folded `ServiceWorkOrder`, `ServiceAccount` and `InstalledAsset` onto one star and named the entity `ServiceWorkOrder`: primary source object `WorkOrder`, dimensions `Account` and `Asset`, joined `WorkOrder.AccountId = Account.Id` and `WorkOrder.AssetId = Asset.Id`. Five external field names appeared on more than one source — `Id`, `AccountId`, `Name`, `Status`, `CreatedDate` — and the columns read back off the created entity are what the three mechanisms made of them. Trimmed to what shows the shape.

```yaml
prefixes:
  ont: https://ontology.uipath.com/fieldservice#

mappings:
  ServiceWorkOrder:
    sources:
      - access: datafabric
        table: ServiceWorkOrder
        referenceFormulation: rr:SQL2008
        system: uipath-salesforce-sfdc
    s: ont:ServiceWorkOrder/$(IdField)
    po:
      - [a, ont:ServiceWorkOrder]
      - [ont:ServiceWorkOrder.workOrderNumber, $(WorkOrderNumber), xsd:token]
      - [ont:ServiceWorkOrder.workOrderStatus, $(Status)]
      - [ont:ServiceWorkOrder.grandTotal, $(GrandTotal), xsd:decimal]
      - [ont:ServiceWorkOrder.isClosed, $(IsClosed), xsd:boolean]
      # intra-entity: Account was joined onto WorkOrder.AccountId at create — same row
      - p: ont:servicedAccount
        o:
          mapping: ServiceAccount
      # intra-entity: Asset was joined onto WorkOrder.AssetId at create — same row
      - p: ont:concernsAsset
        o:
          mapping: InstalledAsset

  ServiceAccount:
    sources:
      - access: datafabric
        table: ServiceWorkOrder
        referenceFormulation: rr:SQL2008
        system: uipath-salesforce-sfdc
    s: ont:ServiceAccount/$(AccountIdField)
    po:
      - [a, ont:ServiceAccount]
      - [ont:ServiceAccount.accountNumber, $(AccountNumber), xsd:token]
      - [ont:ServiceAccount.accountName, $(Name), xsd:normalizedString]
      - [ont:ServiceAccount.customerTier, $(CustomerTierC)]
      - [ont:ServiceAccount.accountCreatedOn, $(CreatedDate), xsd:dateTime]

  InstalledAsset:
    sources:
      - access: datafabric
        table: ServiceWorkOrder
        referenceFormulation: rr:SQL2008
        system: uipath-salesforce-sfdc
    s: ont:InstalledAsset/$(AssetIdField)
    po:
      - [a, ont:InstalledAsset]
      - [ont:InstalledAsset.serialNumber, $(SerialNumber), xsd:token]
      - [ont:InstalledAsset.assetName, $(AssetName), xsd:normalizedString]
      - [ont:InstalledAsset.assetStatus, $(AssetStatus)]
      - [ont:InstalledAsset.installedOn, $(InstallDate), xsd:dateTime]
```

Every reading the example is here for:

- **Three blocks, one `table:`.** All three classes sit over `ServiceWorkOrder`, each minting its own subject from its own key column. `servicedAccount` and `concernsAsset` carry no `condition:` — both blocks are the same table and the joins ran at create. XF-015 rejects both omissions and both blocks are right.
- **`IdField`, `AccountIdField`, `AssetIdField`** are step 1 then step 2: `Id` is a system field name, so every copy is suffixed before any collision is considered, and the first source keeps the suffixed name while the later two take their object-name prefix on top of it.
- **`AccountId` and `AssetAccountId`** are step 2 alone, on a name step 1 leaves alone: `WorkOrder.AccountId` keeps the bare name, `Asset.AccountId` takes the prefix. `AssetAccountId` sits in the entity and gets no `po:` row — the model declares no property for it, and it was selected only to keep a later resolution from costing a delete and a recreate.
- **`AssetName` and `AssetStatus`** are step 2 as well. `Account.Name` and `WorkOrder.Status` came first in `externalFields` order and kept their names; **source order decides which copy is renamed**, which is why a recreate whose order changed renames columns that did not change.
- **`CustomerTierC`** is the derivation itself: `Customer_Tier__c` splits to `Customer`, `Tier`, `c`, the first segment is kept as it came and each later one has only its first character upper-cased.
- **`AccountIdField` and `AssetIdField` exist in the entity** because the folded classes mint their subjects from them — a folded class whose key column was not selected has nothing to mint from, which phase 3 checks as its fourth condition.
- **`installedAtAccount` has no block here.** It runs `InstalledAsset → ServiceAccount`, both of them spokes of this one star reaching the primary on different columns, which is § Open case: the run raised a ledger exception against that `po:` entry and emitted neither form, and every other block of both classes is written as above.

Over on the other entity, `PartReservation` over Snowflake's `PARTS_RESERVATION`, the all-caps case: `RESERVATION_ID` reads back as `RESERVATIONID`, `WO_ID` as `WOID`, `QTY_REQUESTED` as `QTYREQUESTED`. Not one of them is camelCase, and a mapping that predicted `reservationId` would be wrong in every character after the first.

## Anti-patterns

1. **Writing `$()` names from the source objects' field names.** Derived column names and the collision rename make a mapping written before the read-back wrong in exactly the places a collision occurred. Two ways a prediction goes wrong even when the rules are consulted (§ Column names):
   - **predicting the derived name as camelCase** — the first segment is kept as it came, so `RESERVATION_ID` is `RESERVATIONID`, and an all-caps warehouse column predicted as camelCase is wrong in every character after the first;
   - **reading the collision escalation as prefix-then-number** — the reserved/invalid suffix fires first, per name, before any collision, so `Id` is `IdField` on the first source and `AccountIdField` on the second; a numeric suffix appears only when the prefixed name also collides.
2. **Representing an intra-entity join with a `condition:`.** The join already ran at create; a condition re-joins a flat row against itself (§ An intra-entity join is not represented).
3. **`$(Id)` on a connector-backed entity.** `Id` is the native lane's subject key; this lane's is the natural key column (§ Subject identity).
4. **Several blocks of one class minting different subjects.** They then describe several objects, silently (§ Subject identity rule 2).
5. **Hanging a folded class's properties off the host's subject** instead of giving it its own block. `DataPropertyDomain` forbids it.
6. **A two-element pair on a typed property.** It is read as `xsd:string` and disagrees with `sh:datatype` (§ Datatypes).
7. **Verbose YARRRML**, or an entity, folder or connection identifier anywhere in the file (§ Conventions that carry over).
8. **Emitting either form for an object property between two spokes of one star.** The same-row form over-claims and the explicit `condition:` is anti-pattern 2; the run raises a ledger exception and emits neither (§ Open case).
9. **Reporting `system:` or `sourceSystems:` as checked.** Nothing in the shipped rules parses either, and `sourceSystems:`'s effect was never observed (§ Several connectors behind one entity).

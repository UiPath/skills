# Federated Source Mapping Guide — the source YARRRML over external objects

Phase 3 of [federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md): write the correspondence down. This guide is the syntax of that file and nothing else — the phase contracts, stop conditions and the ledger stay in the pipeline guide, and the target YARRRML written against created entities is [federated-mapping-guide.md](federated-mapping-guide.md).

**YARRRML** is what is authored here; **R2RML** names what it compiles to. Never "YAML", never bare "RML".

## What this file is, and what reads it

Nothing in the platform reads it. An ontology carries exactly one `mapping` artifact and the target YARRRML holds that slot, so the source YARRRML is never attached. Its shape is therefore a design choice, settled here, and its only hard requirements are that it parse as YARRRML and that it carry every binding fact exactly once.

**It stays YARRRML. It is not converted to JSON, now or later.** Every other artifact of the pack is JSON because the pack is machine-read; these two are not an exception to that decision but a case of it. The target is the mapping artifact the platform itself consumes, the CLI's own YARRRML parser reads both files, so both are **already machine-parseable** — which is the whole of what the pack requires. And the two files are then the same language over different sources, so a diff between them is an account of what changed when the model met the platform. Rewriting either as a table or as JSON breaks what it is for ([federated-entity-pipeline-guide.md § Why the two YARRRML files stay YARRRML](federated-entity-pipeline-guide.md)).

**What it is authoritative for.** The bindings, the subject keys, the field names and the discovered types — everything it carries. It carries no declared constraint and never restates one: `sh:minCount`, `sh:maxLength` and `sh:in` stay in SHACL, which phases 6 and 7 re-read. A hand edit to this file therefore changes a binding, never a declaration, the two files cannot drift, and a declaration changes only in the model, upstream.

**Never add it as an ontology artifact.** `uip ont files add` resolves artifact type from the file name, and the `mapping` type claims `.yarrrml.yml`, `.yml` and `.yaml`. Adding this file would either be rejected as a second mapping or displace the real one. Keep it in the solution as an ordinary file, named `<MODEL_NAME>-source.yarrrml` with no `.yml` extension, so no resolver can claim it.

## Block shape

One block per (class, object) pair — one cell of the correspondence matrix:

```yaml
prefixes:
  ont: https://ontology.uipath.com/<MODEL_NAME>#

mappings:
  <ClassName>__<ObjectName>:
    sources:
      - access: integrationservice
        object: <EXTERNAL_OBJECT>
        system: <CONNECTOR_KEY>
        connection: <CONNECTION_RESOURCE>
    s: ont:<ClassName>/$(<PRIMARY_KEY_FIELD>)
    po:
      - [a, ont:<ClassName>]
      - [ont:<ClassName>.<propName>, $(<FIELD>)]
      - [ont:<ClassName>.<numericProp>, $(<FIELD>), xsd:decimal]
```

1. **The block key is `<ClassName>__<ObjectName>`**, double underscore. A class with one object still carries the object in its key, so the key alone says which cell it is and two cells of one class never collide. **The key is also the cell's id** — `cell:<ClassName>__<ObjectName>` — which is how this file joins the pack's graph without carrying an `id` of its own. Where one class binds to same-named objects on two connections, the key takes the connection resource name as a third segment, `<ClassName>__<ObjectName>__<Connection>`, because a block key that repeats is a cell id that repeats ([federated-entity-pipeline-guide.md § Ids](federated-entity-pipeline-guide.md)).
2. **`access: integrationservice`** distinguishes these blocks from the target's `access: datafabric` at a glance. It is this file's own convention, not a platform value.
3. **`object:` is the external object name** exactly as `uip is resources list` returns it, and **`system:` is the connector key** — `uipath-salesforce-sfdc`, not "Salesforce". **`connection:` names a connection resource the solution already holds**, never a connection id: the bootstrap added it before phase 1 and phase 5 resolves the same name ([federated-entity-pipeline-guide.md § Bootstrap](federated-entity-pipeline-guide.md)). That name is the tenant connection's own and cannot be aliased, so whatever the tenant calls the connection is what this key carries.
4. **`$()` names are the external field names** as `describe` returns them, case-sensitive. The entity's internal column names do not exist yet and must not appear; they arrive at phase 6, after create.
5. **`[a, ont:<ClassName>]` in every block of a class.** A junction object is the exception: it carries no class, so its block has a subject and one `po:` entry and **no `[a, …]` row**.
6. **Every upstream id a block needs is already in the block.** `connection:` mints the `con:`, `connection:` plus `object:` the `obj:`, each `$(<FIELD>)` an `fld:`, each `ont:<ClassName>.<propName>` names a `dp:` and `[a, ont:<ClassName>]` a `cls:`. A walker mints them from what the block says; nothing is indexed and no name is matched.

## Subject identity

The subject template is the whole point of this file. It carries the key that `HasKey` cannot declare, and phase 7 checks it against the correspondence.

1. **The subject key is the object's declared primary key.** No other column may be used: uniqueness beyond the primary key is invisible to the connector metadata, and the payload builder throws without one.
2. **Every block of one class mints an identical subject.** A class drawing on three objects has three blocks, and all three read a column whose value is the same key for the same real-world thing. That is what makes them one object rather than three, and it is the same key the federated star will join on — one constraint seen from two sides.
3. A class whose objects cannot produce a common key is a phase 3 exception, not a subject to approximate.

## Data properties

The third element is the property's range, taken from `sh:datatype`. A two-element pair is read as `xsd:string`, so every non-string property carries its range explicitly or the file disagrees with the SHACL it was built from.

Where the connector flattened its types — every column reported as `string` or `number` — the range still comes from the model, not from the connector. Record in the ledger that the agreement is unverifiable for that cell rather than claiming the two agree.

## Object properties

An object property joins two blocks on discovered reference fields:

```yaml
po:
  - p: ont:<objectProperty>
    o:
      mapping: <TargetClassName>__<TargetObjectName>
      condition:
        function: equal
        parameters:
          - [str1, $(<FIELD_ON_THIS_OBJECT>)]
          - [str2, $(<FIELD_ON_TARGET_OBJECT>)]
```

1. **`mapping:` names a block key**, so it carries the target's object as well as its class. A property pointing at a class with several blocks names the one block whose object actually holds the matching column.
2. **Which column `str2` reads depends on direction.** For a to-one reference it is the target's primary key. For a **to-many** — a parent pointing at its children — it is the child's foreign-key column back to the parent, which is not the child's primary key and is not in its subject template. R2RML compares any column to any column; neither side has to be a key.
3. **No connector declares a foreign key.** Every join column here was chosen at phase 3, and a choice between two plausible columns is a ledger exception, not a guess. Record the resolution's `R<n>` id in a comment on the block.
4. The join sits in the block of the class whose object holds the referencing column. The inverse property gets no join.

## Worked example

From a real run. Five classes over three Salesforce objects, a Snowflake table and a Database Hub table, one block each — `ServiceWorkOrder` from `WorkOrder` (primary key `Id`), `ServiceAccount` from `Account` (`Id`), `InstalledAsset` from `Asset` (`Id`), `PartReservation` from `PARTS_RESERVATION` (`RESERVATION_ID`) and `PartStockPosition` from `WarehouseInventory` (`ProductSKU`). `hasPartReservation` is the one to-many property; the other four carry `sh:maxCount 1`. Trimmed to the properties and joins that carry the shape.

```yaml
prefixes:
  ont: https://ontology.uipath.com/fieldservice#

mappings:
  ServiceWorkOrder__WorkOrder:
    sources:
      - access: integrationservice
        object: WorkOrder
        system: uipath-salesforce-sfdc
        connection: <SF_CONNECTION>
    s: ont:ServiceWorkOrder/$(Id)
    po:
      - [a, ont:ServiceWorkOrder]
      - [ont:ServiceWorkOrder.workOrderNumber, $(WorkOrderNumber), xsd:token]
      - [ont:ServiceWorkOrder.workOrderStatus, $(Status)]
      - [ont:ServiceWorkOrder.grandTotal, $(GrandTotal), xsd:decimal]
      # xsd:nonNegativeInteger — correct here, uncompilable if ever installed
      - [ont:ServiceWorkOrder.lineItemCount, $(LineItemCount), xsd:nonNegativeInteger]
      - [ont:ServiceWorkOrder.isClosed, $(IsClosed), xsd:boolean]
      # join column chosen by D4 (AccountId over CaseId); no reference metadata
      - p: ont:servicedAccount
        o:
          mapping: ServiceAccount__Account
          condition:
            function: equal
            parameters:
              - [str1, $(AccountId)]
              - [str2, $(Id)]
      # UNRESOLVED — E2 open. WO_ID and WO_REFERENCE are both VARCHAR(64) on
      # PARTS_RESERVATION, neither name matches, no foreign key is declared. The
      # pair below is E2's recommendation, not a resolution.
      - p: ont:hasPartReservation
        o:
          mapping: PartReservation__PARTS_RESERVATION
          condition:
            function: equal
            parameters:
              - [str1, $(Id)]
              - [str2, $(WO_ID)]

  ServiceAccount__Account:
    sources:
      - access: integrationservice
        object: Account
        system: uipath-salesforce-sfdc
        connection: <SF_CONNECTION>
    s: ont:ServiceAccount/$(Id)
    po:
      - [a, ont:ServiceAccount]
      - [ont:ServiceAccount.accountNumber, $(AccountNumber), xsd:token]
      - [ont:ServiceAccount.customerTier, $(Customer_Tier__c)]
      - [ont:ServiceAccount.accountCreatedOn, $(CreatedDate), xsd:dateTime]

  InstalledAsset__Asset:
    sources:
      - access: integrationservice
        object: Asset
        system: uipath-salesforce-sfdc
        connection: <SF_CONNECTION>
    s: ont:InstalledAsset/$(Id)
    po:
      - [a, ont:InstalledAsset]
      - [ont:InstalledAsset.serialNumber, $(SerialNumber), xsd:token]
      # installedOn bound to InstallDate over CreatedDate — D2, on displayName
      - [ont:InstalledAsset.installedOn, $(InstallDate), xsd:dateTime]
      # join column chosen by D3 (AccountId over ParentId, Product2Id) from the
      # name alone — describe exposes no reference metadata on any Salesforce object
      - p: ont:installedAtAccount
        o:
          mapping: ServiceAccount__Account
          condition:
            function: equal
            parameters:
              - [str1, $(AccountId)]
              - [str2, $(Id)]

  PartReservation__PARTS_RESERVATION:
    sources:
      - access: integrationservice
        object: PARTS_RESERVATION
        system: uipath-snowflake-snowflake
        connection: <SNOW_CONNECTION>
    s: ont:PartReservation/$(RESERVATION_ID)
    po:
      - [a, ont:PartReservation]
      - [ont:PartReservation.reservationNumber, $(RESERVATION_ID), xsd:token]
      - [ont:PartReservation.reservationStatus, $(RESERVATION_STATUS)]
      - [ont:PartReservation.quantityRequested, $(QTY_REQUESTED), xsd:decimal]
      - [ont:PartReservation.promisedOn, $(PROMISED_DATE), xsd:dateTime]
      # UNRESOLVED — E3 open. MATERIAL_NO and UNIT_SERIAL are both plausible against
      # ProductSKU; MATERIAL_NO is E3's recommendation.
      - p: ont:drawsFromStock
        o:
          mapping: PartStockPosition__WarehouseInventory
          condition:
            function: equal
            parameters:
              - [str1, $(MATERIAL_NO)]
              - [str2, $(ProductSKU)]

  PartStockPosition__WarehouseInventory:
    sources:
      - access: integrationservice
        object: WarehouseInventory
        system: uipath-uipath-jdbc
        connection: <DB_CONNECTION>
    s: ont:PartStockPosition/$(ProductSKU)
    po:
      - [a, ont:PartStockPosition]
      - [ont:PartStockPosition.partSku, $(ProductSKU), xsd:token]
      - [ont:PartStockPosition.totalOnHand, $(TotalOnHand), xsd:integer]
```

What the example carries. `servicedAccount` and `installedAtAccount` are to-one, so `str2` is `Account`'s primary key both times. `hasPartReservation` is to-many, so `str2` is `WO_ID` — the child's reference back, not `RESERVATION_ID`, which is the child's own key and is also the subject this block mints from. Every join column here was chosen at phase 3 on the field name or its `displayName` alone, because `reference` came back empty on every field of all three connectors; two of them had a second candidate and are open exceptions carrying a recommendation rather than a binding. `lineItemCount` is the one range the ontology install cannot compile — it agrees with `sh:datatype` and with the `.ofn`, and the install rewrites it and then objects; that lane is not entered here, so the pair stands as written ([federated-entity-pipeline-guide.md § The ontology resource does not ship](federated-entity-pipeline-guide.md)). `promisedOn` is a calendar date written `xsd:dateTime`, because the grammar refuses `xsd:date` inside an axiom and the model widened it upstream. The `xsd:decimal` on `quantityRequested` rests on a prose `NUMBER(12,3)`: Snowflake declares the column `number`, so the agreement for this cell is unverifiable and the ledger says so rather than claiming the two agree.

## Anti-patterns

1. **Attaching this file as the ontology's mapping artifact.** The type resolver claims `.yml` and `.yaml`, the mapping slot allows exactly one, and the target owns it (§ What this file is).
2. **Writing internal column names.** They are derived at create and do not exist yet; a source block that carries them was written backwards from the target (§ Block shape rule 4).
3. **A subject template on anything but the declared primary key.** Undeclared uniqueness is invisible to the metadata and unusable by the payload builder (§ Subject identity rule 1).
4. **Two blocks of one class minting different subjects.** They then describe different objects, and the star they imply cannot join (§ Subject identity rule 2).
5. **`str2` on the target's primary key for a to-many property.** The child's key identifies the child; the parent reference is a different column (§ Object properties rule 2).
6. **Guessing a join column because only one candidate looks right.** No connector declares a foreign key, so every such choice is phase 3's and belongs in the ledger with what it was chosen over (§ Object properties rule 3).
7. **`access: datafabric` or a `table:` key anywhere in this file.** Those belong to the target mapping, over entities that exist.

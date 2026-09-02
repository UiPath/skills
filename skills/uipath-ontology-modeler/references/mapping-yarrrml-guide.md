# YARRRML Mapping Reference

Artifact type: `mapping` | Media type: `application/yaml` | File: `mapping.yarrrml.yml`

Uploading a valid mapping artifact **deploys the ontology** (DRAFT → DEPLOYED). In standalone modeler mode, the modeler may upload the mapping last, after schema and constraints. In delegated modeler mode, the modeler must return or hold the mapping; authoring uploads it last after backend validation and the preceding tiers.

---

## File structure

```yaml
prefixes:
  ont: https://ontology.uipath.com/{name}#

mappings:
  {ClassName}:
    sources:
      - access: datafabric
        table: {EntityNameInDataFabric}
        entityId: {entity-uuid-from-uip-df-entities-list}
        folderId: {folder-key-guid}
        referenceFormulation: rr:SQL2008
    s: ont:{ClassName}/$(primaryKeyColumn)
    po:
      - - a
        - ont:{ClassName}
      - - ont:{ClassName}.{propName}
        - $({columnName})
      - p: ont:{objectProperty}
        o:
          mapping: {TargetClassName}
          condition:
            function: equal
            parameters:
              - - str1
                - $({foreignKeyColumn})
              - - str2
                - $({primaryKeyColumn})
```

---

## Rules

### Source block
- `access: datafabric` — always this literal string; tells the runtime to use Data Fabric as the FQS source
- `table:` — the **entity name** in Data Fabric (not a SQL table name; usually matches the class name)
- `entityId:` — UUID from `uip df entities list --output json` → `Data[].ID`
- `folderId:` — folder key GUID from `uip df entities list --output json` → `Data[].FolderKey`
- `referenceFormulation: rr:SQL2008` — always this literal

### Subject template (`s:`)
- Pattern: `ont:{ClassName}/$(primaryKeyColumn)`
- `primaryKeyColumn` is the column name **as it appears in the Data Fabric entity** (case-sensitive)
- Example: `ont:Doctor/$(doctorId)` where `doctorId` is the entity's primary key field name

### Property-object pairs (`po:`)

**rdf:type** (required for every mapping):
```yaml
- - a
  - ont:{ClassName}
```

**Data property** (scalar column → ontology data property):
```yaml
- - ont:{ClassName}.{propName}
  - $({columnName})
```
Column name must match the Data Fabric entity field name exactly (case-sensitive).

**Object property** (join → ontology object property):

`ont:{objectProperty}` must exactly match an `ObjectProperty` IRI declared in `schema.ofn` — look it up before writing the `p:` line.

`{TargetClassName}` must be the exact key of another mapping block in this file — if the block is absent or misspelled, YARRRML silently produces no join triples.

`str1` resolves from the **current mapping's** source rows; `str2` from the **target `mapping:`** source rows — they always reference different entity tables, even when `$(columnName)` is identical in both.

**Case A — FK and PK share the same column name** (most common):
```yaml
- p: ont:{objectProperty}
  o:
    mapping: {TargetClassName}
    condition:
      function: equal
      parameters:
        - - str1
          - $({sharedColumnName})
        - - str2
          - $({sharedColumnName})
```

**Case B — FK and PK have different names** (e.g. casing mismatch or renamed column):
```yaml
- p: ont:{objectProperty}
  o:
    mapping: {TargetClassName}
    condition:
      function: equal
      parameters:
        - - str1
          - $({foreignKeyColumn})
        - - str2
          - $({primaryKeyColumn})
```

---

## Getting entityId and folderId

```bash
uip df entities list --native-only --output json
```

From the JSON output, for each class find the matching entity:
- `entityId` = `Data[].ID`
- `folderId` = `Data[].FolderKey`

If the entity doesn't exist yet, create it with the `data-fabric` skill first.

---

## Full worked example

A complete worked 3-class mapping (Doctor, Patient, Prescription) is in [`mapping-yarrrml-example.md`](mapping-yarrrml-example.md). Read it only if a gate/consistency check fails and you need a concrete reference to self-correct, or you judge the rules above aren't enough to proceed confidently for this request.

---

## Junction class mapping (many-to-many)

A junction class maps to its own entity (the association table). It holds both FK columns, so both object property joins originate from the junction mapping block.

```yaml
{JunctionClass}:
  sources:
    - access: datafabric
      table: {JunctionEntityName}
      entityId: {junction-entity-uuid}
      folderId: {folder-key-guid}
      referenceFormulation: rr:SQL2008
  s: ont:{JunctionClass}/$(primaryKeyColumn)
  po:
    - - a
      - ont:{JunctionClass}
    - p: ont:{propToSideA}
      o:
        mapping: {SideA}
        condition:
          function: equal
          parameters:
            - - str1
              - $({sideAFKColumn})      # FK on the junction entity
            - - str2
              - $({sideAPKColumn})      # PK on the SideA entity
    - p: ont:{propToSideB}
      o:
        mapping: {SideB}
        condition:
          function: equal
          parameters:
            - - str1
              - $({sideBFKColumn})      # FK on the junction entity
            - - str2
              - $({sideBPKColumn})      # PK on the SideB entity
```

Both FK columns (`str1`) are on the junction entity. The `SideA` and `SideB` mapping blocks remain unchanged — they do not need to reference the junction. Verify FK and PK column casing separately for each side with `uip df entities get` — do not assume they match.

---

## USAGE POLICY block

Add a `# USAGE POLICY` comment block at the top of the `.yarrrml.yml` file, before the `prefixes:` key. This is the **rule** layer — imperative rules for any agent or tool that reads this file as text. It teaches *how* to use the constructs.

**Separation of Concerns**: the USAGE POLICY carries rules only. Facts (what status='A' means, grain, value domains) belong in `rdfs:comment` in `schema.ofn`. Bindings (which FK column joins which PK column) belong in the `condition:` blocks below. Do not duplicate facts from `schema.ofn` here — reference them ("LITERALS are case-sensitive — see schema.ofn") instead of restating them.

Keep it ≤30 non-empty lines. Every rule must reference constructs that actually exist in the mapping or schema. State the non-action explicitly for conditional rules (see example below).

```yaml
# ============================================================================
# USAGE POLICY  (how to use the constructs; facts live in schema.ofn)
# ============================================================================
# JOIN GRAPH (join only what the question needs):
#   Order → Customer via Order.customerId = Customer.Id
#   OrderLine → Order via OrderLine.orderId = Order.Id
# ROUTING (canonical property for ambiguous phrases):
#   "customer name" → Customer.customerName, not OrderLine.customerName
# GRAIN DISCIPLINE:
#   Order: ONE row per order — no dedup needed
#   OrderHistory: TIME SERIES — SELECT DISTINCT orderId for per-order questions
# OUTPUT DISCIPLINE:
#   Return ALL matching rows for list questions; LIMIT 1 only for single-answer superlatives.
#   No default LIMIT. No DISTINCT unless uniqueness was asked.
# LITERALS are case- and format-sensitive — copy exactly as annotated in schema.ofn.
# ============================================================================

prefixes:
  ont: https://ontology.uipath.com/{name}#
...
```

Fill in only the sections relevant to the domain. Omit sections that don't apply rather than leaving them empty or generic. The join graph and routing sections have the most impact — always include them when there are object properties or ambiguous column names.

---

## Federated entities in the mapping

A federated entity maps exactly like a native entity — same `access: datafabric`, `entityId`, `folderId`, and `referenceFormulation` fields. The FQS runtime resolves the external connection transparently.

```yaml
{FederatedClass}:
  sources:
    - access: datafabric
      table: {ExternalTableOrObject}
      entityId: {federated-entity-uuid}
      folderId: {folder-key-guid}
      referenceFormulation: rr:SQL2008
  s: ont:{FederatedClass}/$(primaryKeyColumn)
  po:
    - - a
      - ont:{FederatedClass}
    - - ont:{FederatedClass}.{propName}
      - $({columnName})
```

**What changes when a mapping includes federated classes:**
- Note the federation in the USAGE POLICY so a reader knows where the data lives: `# {FederatedClass}: FEDERATED — backed by an external system through Integration Service`
- SQL write actions (`ont:statements`) and coded actions may both reference `{{FederatedClass}}` entity tables. The DML is routed to the source system through its connector, which remains the authority on whether the write succeeds; a rejection surfaces as an upstream error. Add the `READONLY` note only for a source the author says rejects writes
- SPARQL read functions work normally — FQS queries federated and native entities in the same traversal

---

## Common mistakes

- **Wrong column name** — column names in `$()` must match Data Fabric field names exactly (case-sensitive). Run `uip df entities get {entityId} --output json` and read `Fields[].Name` to verify.
- **Join column casing mismatch** — `str1` is the FK column on this entity; `str2` is the PK column on the target entity. The same logical key can have different casing on each side (e.g. `$(doctorId)` on Doctor but `$(doctorid)` on Prescription). Always verify both sides separately with `entities get` — do not assume the casing matches.
- **Same-column-name join treated as a mistake** — when FK and PK share the same column name (e.g. both `supplierId`), `str1` and `str2` both use `$(supplierId)`. This is correct — YARRRML resolves each from its own source table. Do not invent different aliases.
- **Missing `a` triple** — every mapping block must have `- - a\n  - ont:{ClassName}` or the ontology class instances won't be typed.
- **Wrong object property direction** — check `ObjectPropertyDomain` and `ObjectPropertyRange` in `schema.ofn`. The mapping entry goes on the entity that holds the foreign key.
- **Object property name not in schema** — `ont:{objectProperty}` in the `p:` line must exactly match an `ObjectProperty` declared in `schema.ofn`. A mismatch causes upload rejection with a property-not-found error. Read `schema.ofn` to find the correct IRI before writing the condition.
- **Missing `mapping:` block for target class** — `mapping: {TargetClassName}` must reference a top-level mapping key that exists in this file. A missing or misspelled block causes YARRRML to silently produce no join triples for that property — no upload error, no runtime error, just absent relationships.
- **folderId vs folderKey** — Data Fabric uses `FolderKey` in the API response; this maps to `folderId` in the YARRRML source block.
- **Uploading mapping before schema/constraints** — the server validates that every `ont:` property referenced in the mapping exists in the schema. In standalone modeler mode, upload schema and constraints first, then the modeler may upload the mapping last. In delegated modeler mode, return or hold the mapping and let authoring upload it last after backend validation and the preceding tiers.
- **Verbose YARRRML syntax causes DRAFT stuck** — Never use `subjects:`, `predicateobjects:`, `predicate:`, `object:`, or `[rdf:type, ont:Class~iri]`. Never add `~xsd:string` type annotations to data property values (`$(col)` not `$(col)~xsd:string`). The backend `validate` command accepts the verbose form and returns `Valid: true` — this is a false green. Only the compact `s:`/`po:`/`p:`/`o:` form with `table:` and `referenceFormulation: rr:SQL2008` in every source block triggers DRAFT→DEPLOYED. If state stays DRAFT after mapping upload, the format is wrong — re-read this file and rewrite.

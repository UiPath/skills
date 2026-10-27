# YARRRML Mapping Reference

Artifact type: `mapping` | Media type: `application/yaml` | File: `{name}-mapping.yarrrml.yml`

The mapping binds each class to a local entity **by name**. The ontology service resolves `table:` to the entity in the deployment folder at install. The mapping never carries `entityId` or `folderId`. It is an `application/yaml` artifact: check it with `uip ont artifacts check {name}-mapping.yarrrml.yml --content-type application/yaml --type mapping --file <path>`, and the CLI sends it to the service as YAML.

---

## File structure

```yaml
prefixes:
  ont: https://ontology.uipath.com/{name}#

mappings:
  {ClassName}:
    sources:
      - access: datafabric
        table: {EntityName}
        referenceFormulation: rr:SQL2008
    s: ont:{ClassName}/$(Id)
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
- `table:` — the local entity name (the `input/entities/{EntityName}.json` body you created; usually the class name). It must be an entity listed in the ontology's `--entity` set. No entity IDs, folder IDs, or placeholders.
- `referenceFormulation: rr:SQL2008` — always this literal

### Subject template (`s:`)
- Pattern: `ont:{ClassName}/$(Id)`
- `primaryKeyColumn` is `Id` (the system key) unless the user named another unique field; field names are case-sensitive
- Example: `ont:Doctor/$(Id)`

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
Column name must be a field in the local entity body, exactly as written (case-sensitive), or a system field such as `Id`.

**Object property** (join → ontology object property):

`ont:{objectProperty}` must exactly match an `ObjectProperty` IRI declared in `{name}.ofn` — look it up before writing the `p:` line.

`{TargetClassName}` must be the exact key of another mapping block in this file — if the block is absent or misspelled, YARRRML silently produces no join triples.

**The join is on plain columns on both sides.** `str1` is the key field of the current mapping's entity (for example `Order.customerId`); `str2` is the target entity's key (usually `Id`). Both are ordinary fields (or system fields), never an entity or folder id. `str1` resolves from the **current mapping's** source rows; `str2` from the **target `mapping:`** source rows. See [`relationships-guide.md`](relationships-guide.md) for how to choose the key column.

```yaml
- p: ont:{objectProperty}
  o:
    mapping: {TargetClassName}
    condition:
      function: equal
      parameters:
        - - str1
          - $({foreignKeyColumn})     # e.g. customerId on the current entity
        - - str2
          - $({primaryKeyColumn})     # e.g. Id on the target entity
```

When the key column happens to have the same name on both sides, `str1` and `str2` both use that name. That is correct.

---

## Full worked example

A complete worked 3-class mapping (Doctor, Patient, Prescription) is in [`mapping-yarrrml-example.md`](mapping-yarrrml-example.md). Read it only if `uip ont validate --local` reports a mapping problem and you need a concrete reference to self-correct, or you judge the rules above aren't enough to proceed confidently for this request.

---

## Junction class mapping (many-to-many)

A junction class maps to its own entity (the association table). It holds both key columns, so both object property joins originate from the junction mapping block.

```yaml
{JunctionClass}:
  sources:
    - access: datafabric
      table: {JunctionEntityName}
      referenceFormulation: rr:SQL2008
  s: ont:{JunctionClass}/$(Id)
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
              - $({sideAKeyColumn})      # key field on the junction entity
            - - str2
              - $({sideAPKColumn})      # key on the SideA entity (usually Id)
    - p: ont:{propToSideB}
      o:
        mapping: {SideB}
        condition:
          function: equal
          parameters:
            - - str1
              - $({sideBKeyColumn})      # key field on the junction entity
            - - str2
              - $({sideBPKColumn})      # key on the SideB entity (usually Id)
```

Both key columns (`str1`) are on the junction entity. The `SideA` and `SideB` mapping blocks remain unchanged — they do not need to reference the junction. Verify column casing separately for each side against the entity bodies.

---

## USAGE POLICY block

Add a `# USAGE POLICY` comment block at the top of the `.yarrrml.yml` file, before the `prefixes:` key. This is the **rule** layer — imperative rules for any agent or tool that reads this file as text. It teaches *how* to use the constructs.

**Separation of Concerns**: the USAGE POLICY carries rules only. Facts (what status='A' means, grain, value domains) belong in `rdfs:comment` in `{name}.ofn`. Bindings (which key column joins which) belong in the `condition:` blocks below. Do not duplicate facts from `{name}.ofn` here — reference them ("LITERALS are case-sensitive — see `{name}.ofn`") instead of restating them.

Keep it ≤30 non-empty lines. Every rule must reference constructs that actually exist in the mapping or schema. State the non-action explicitly for conditional rules (see example below).

```yaml
# ============================================================================
# USAGE POLICY  (how to use the constructs; facts live in {name}.ofn)
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
# LITERALS are case- and format-sensitive — copy exactly as annotated in {name}.ofn.
# ============================================================================

prefixes:
  ont: https://ontology.uipath.com/{name}#
...
```

Fill in only the sections relevant to the domain. Omit sections that don't apply rather than leaving them empty or generic. The join graph and routing sections have the most impact — always include them when there are object properties or ambiguous column names.

---

## Federated entities

Not supported in a local solution. A federated entity needs an Integration Service connection and cannot be authored locally; stop and tell the user.

---

## Common mistakes

- **Wrong column name** — column names in `$()` must match field names in the local entity body exactly (case-sensitive), or be `Id`.
- **Join column casing mismatch** — `str1` is a field of this entity; `str2` is a field of the target entity. Check each side separately against its entity body.
- **Missing `a` triple** — every mapping block must have `- - a\n  - ont:{ClassName}` or the class instances won't be typed.
- **Wrong object property direction** — check `ObjectPropertyDomain` and `ObjectPropertyRange` in `{name}.ofn`. The join goes in the mapping of the entity that holds the key.
- **Object property name not in schema** — `ont:{objectProperty}` in the `p:` line must exactly match an `ObjectProperty` declared in `{name}.ofn`. Read `{name}.ofn` for the IRI before writing the join.
- **Missing `mapping:` target** — `mapping: {TargetClassName}` must be a top-level key of this file. Check every target.
- **Object property with no join** — an object property between two mapped classes needs a join in the domain class's mapping.
- **Mapping out of sync with the schema** — every `ont:` term in the mapping must exist in the schema. Write the schema and constraints first, then the mapping, and let `uip ont validate --local` confirm they agree.
- **Entity or folder ids** — never write `entityId` or `folderId`. `table: <EntityName>` is the only link.
- **Verbose YARRRML syntax** — never use `subjects:`, `predicateobjects:`, `predicate:`, `object:`, or `[rdf:type, ont:Class~iri]`, and no inline `~iri` relationships. Use only the compact `s:`/`po:`/`p:`/`o:` form with `table:` and `referenceFormulation: rr:SQL2008` in every source block. If `uip ont artifacts check` warns about the mapping, re-read this file and rewrite it.

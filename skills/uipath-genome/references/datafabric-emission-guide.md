# Data Fabric Emission Guide — entities.json to solution resources

Rules and procedure. How the derived entity set becomes files inside the solution,
what the on-disk shape is, and which gates must pass before edits are offered.

Read whole before writing any solution resource. Router:
[data-model-guide.md](data-model-guide.md).

Everything about field types, choice-set mechanics, relationship bindings and
federated rules belongs to `uipath-platform` → `references/data-fabric/`. This file
states only what is specific to emitting a derived model: the local-authoring route,
the resource shape the CLI cannot write, and the gates.

## Everything stays local

`uip df entities create --local` authors into the solution on disk — no login, no
tenant, and the entity becomes a real table at deploy. That is the only route Author
mode uses; nothing is written to a tenant
([data-model-guide.md § Boundaries](data-model-guide.md)).

**The CLI refuses `RELATIONSHIP`, `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE` on
the local path. The resource file accepts them.** Only the CLI refuses. So the
applier scaffolds each entity with its scalar fields through the CLI, then appends
the complex fields to the resource file it wrote.

This is the one place the skill deliberately breaks the standing "drive it through
the commands, never hand-edit the resource files" rule, and it is bounded: the CLI
still creates both halves of the file pair and establishes the envelope; the applier
only appends field objects and dependency rows. **Never author a `.entity` stub or a
whole resource file from scratch.**

When `--local` gains the two field types, delete the append step and call the CLI
throughout. Nothing else in this guide changes.

## entities.json

Genome's own format, derived from `target.r2rml` and the inventory. **Not** the
`uip df` input shape — the applier translates.

```jsonc
{
  "version": 1,
  "project": "<ENTITY_PROJECT_NAME>",
  "scope": "tenant",
  "choiceSets": [
    { "name": "<ChoiceSetName>", "displayName": "<LABEL>",
      "values": [ { "name": "<VALUE_1>", "displayName": "<LABEL>", "numberId": 0 },
                  { "name": "<VALUE_2>", "displayName": "<LABEL>", "numberId": 1 } ],
      "nextNumberId": 2,
      "provenance": { "from": ["<IRI>"], "derivation": "direct" } }
  ],
  "entities": [
    { "name": "<EntityName>", "displayName": "<LABEL>", "description": "<rdfs:comment>",
      "component": "<COMPONENT_ID>",
      "displayField": "<FieldName>",
      "provenance": { "from": ["<IRI>"], "derivation": "direct" },
      "fields": [
        { "name": "<FieldName>", "type": "STRING", "isRequired": true,
          "isUnique": false, "lengthLimit": 200,
          "provenance": { "from": ["<IRI>"], "derivation": "direct" },
          "r2rml": { "logicalTable": "<TABLE>", "column": "<COLUMN>" } }
      ],
      "relationships": [
        { "name": "<FieldName>", "target": "<EntityName>", "cardinality": "many-to-one",
          "provenance": { "from": ["<IRI>"], "derivation": "direct" } }
      ],
      "choiceSetFields": [
        { "name": "<FieldName>", "choiceSet": "<ChoiceSetName>", "multiple": false }
      ] }
  ],
  "register": [ /* constraint-register-guide.md § The register row */ ],
  "coverage": { "<CLASS_IRI>": ["<EntityName>"] },
  "envelope": [ /* normalization-guide.md § What Author mode may not decide */ ],
  "notCovered": [ { "from": "<IRI>", "why": "<what no construct holds>" } ]
}
```

`relationships` and `choiceSetFields` are separate from `fields` because they are
applied in a later pass and they are the fields the CLI cannot write.

## Choice sets

`numberId` is **author-assigned** on the local path — the server assigns it only for
tenant choice sets, where the "create one value at a time, then re-read
`list-values`" rule applies. Locally there is no round trip.

**Pinned, sequential, never recomputed.** `entities.json` stores each value's
`numberId` and the set's `nextNumberId`. A re-run keeps every existing value's
number and gives a newly appeared value `nextNumberId`, even when the ontology
inserted it in the middle of the list. A value the ontology drops **keeps its number
reserved** — never reuse it.

The platform's only rule is uniqueness within the set. The pinning is ours, and it is
what stops a later run silently remapping records that are already deployed: the
stored record value is the integer, so renumbering changes what every existing row
means. This is a one-way door ([data-model-guide.md § Commitment ladder](data-model-guide.md)).

## Hand-authored resource shape

Two files per entity that must agree: a `<Name>.entity` stub in the Entity project,
and the definition resource. The schema lives **JSON-escaped inside
`spec.resourceJson`**.

`resources/solution_folder/entity/native/<Name>.json`:

```jsonc
{ "docVersion": "1.0.0",
  "resource": {
    "key": "<ENTITY_GUID>",
    "name": "<EntityName>", "kind": "entity", "type": "native",
    "apiVersion": "dataservice.uipath.com/v2",
    "dependencies": [
      { "kind": "Entity",    "name": "<OtherEntity>" },
      { "kind": "ChoiceSet", "name": "<ChoiceSetName>" } ],
    "isOverridable": true, "runtimeDependencies": [],
    "folders": [ { "fullyQualifiedName": "solution_folder" } ],
    "spec": { "resourceJson": "<escaped>", "name": "<EntityName>",
              "displayName": "<LABEL>", "description": "" } } }
```

Unescaped `resourceJson`:

```jsonc
{ "Id": "<ENTITY_GUID>", "Name": "<EntityName>", "DisplayName": "<LABEL>",
  "EntityType": "Entity",
  "FolderId": "99999999-9999-9999-9999-999999999999",
  "Fields": [
    { "Name": "<FieldName>", "DisplayName": "<LABEL>",
      "SqlType": { "Name": "NVARCHAR", "LengthLimit": 300 },
      "IsSystemField": false, "IsRequired": true },

    { "Name": "<FieldName>", "DisplayName": "<LABEL>",
      "SqlType": { "Name": "INT" }, "IsSystemField": false, "IsRequired": false,
      "FieldDisplayType": "ChoiceSetSingle",
      "ReferenceChoiceSet": { "Name": "<ChoiceSetName>" } },

    { "Name": "<FieldName>", "DisplayName": "<LABEL>",
      "SqlType": { "Name": "UNIQUEIDENTIFIER" }, "IsSystemField": false,
      "FieldDisplayType": "Relationship",
      "ReferenceEntity": { "Name": "<OtherEntity>", "Id": "<OTHER_ENTITY_GUID>",
                           "FolderId": "99999999-9999-9999-9999-999999999999" } } ] }
```

`resources/solution_folder/choiceSet/<Name>.json` — `kind: "choiceSet"`, **no `type`
key**, `dependencies: []`:

```jsonc
{ "Name": "<ChoiceSetName>", "DisplayName": "<LABEL>",
  "Data": [ { "Name": "<VALUE_1>", "DisplayName": "<LABEL>", "NumberId": 0 },
            { "Name": "<VALUE_2>", "DisplayName": "<LABEL>", "NumberId": 1 } ] }
```

### Four rules the shape dictates

1. **`SqlType.Name` is the SQL type, not the CLI enum.** A third vocabulary beside
   the CLI write shape (`"type": "STRING"`) and the API read shape
   (`FieldDataType.Name`): `STRING`→`NVARCHAR`, `MULTILINE_TEXT`/`MULTILINE_MAX`→
   `NVARCHAR`, `DECIMAL`/`AUTO_NUMBER`→`DECIMAL`, `BOOLEAN`→`BIT`, `DATE`→`DATE`,
   `DATETIME_WITH_TZ`→`DATETIMEOFFSET`, `CHOICE_SET_SINGLE`→`INT`,
   `CHOICE_SET_MULTIPLE`→`NVARCHAR`, `RELATIONSHIP`/`FILE`→`UNIQUEIDENTIFIER`.
2. **`resource.key` must equal `resourceJson.Id`.** Both are the GUID the applier
   mints for that entity.
3. **`resource.dependencies` is separate from the in-field `Reference*` pointer.**
   Emit both. A reference with no matching dependency row packs cleanly and fails at
   deploy, because the solution's dependency graph never learned the ordering.
4. **`ReferenceEntity` carries `Name`, `Id` and `FolderId`.** Local entities have a
   stable minted `Id`, so all three are available; emit all three.
   `ReferenceChoiceSet` takes `Name` alone.

The sentinel `99999999-9999-9999-9999-999999999999` is the unassigned-folder marker
that identifies a locally authored entity; deploy and debug replace it. It appears at
entity level in `resourceJson` and inside every `ReferenceEntity`.

## The applier

```bash
python3 "<SKILL_DIR>/scripts/apply-entities.py" \
  --entities entities.json \
  --solution "<SOLUTION_DIR>" \
  [--dry-run]
```

Five passes. All local — no login, no tenant, no UUID round trip, so ordering is
about emission only.

| # | Pass | Does |
|---|---|---|
| 0 | validate graph | discard self-references; compute components; topologically sort within each; **fail hard** on any remaining cycle, naming its members |
| 1 | mint ids | one GUID per entity, reused as `resource.key` and `resourceJson.Id`; derived from the entity name so a re-run mints the same id |
| 2 | choice sets | write `resources/solution_folder/choiceSet/<Name>.json` |
| 3 | entities | `uip df entities create <Name> --local --project-name <P>` with **scalar fields only** — the CLI writes both halves of the pair |
| 4 | complex fields | re-open the entity resource, append the `Relationship` / `ChoiceSet` field objects into `spec.resourceJson`, add the matching `resource.dependencies` rows |

Rules:

- **Re-read and re-escape.** `spec.resourceJson` is an escaped JSON string: parse it,
  append to `Fields`, re-serialize, re-escape. Never string-patch it.
- **Idempotent.** Pass 3 skips an entity whose resource file exists; pass 4 appends
  only fields whose `Name` is absent. Re-running changes nothing.
- **`--dry-run`** prints every command and every file write without performing them.
  Use it before the first real run on a solution that already holds entities.
- Mint ids deterministically from the entity name, so two runs produce identical
  files and the determinism gate holds.

## Validation gates

All must pass before edits are offered.

| Gate | Command | Catches |
|---|---|---|
| Schema | `uip df entities validate --local` | `ENTITY_NAME_INVALID`, `ENTITY_NAME_NOT_UNIQUE`, `FIELD_NAME_INVALID`, `DUPLICATE_FIELD_NAME`, `FIELD_TYPE_NOT_ALLOWED`, `NAME_RESERVED`, `SYSTEM_FIELD_MISSING`, `SYSTEM_FIELD_MODIFIED`, `FIELDS_MALFORMED`, `TOO_MANY_MULTILINE_MAX`, and the stub↔resource pairing |
| Pack | `uip solution pack "<SOLUTION>" --dry-run` | the same rules at the shipping boundary |
| Determinism | two applier runs → identical files | a non-stable id or ordering |

`entities validate --local` needs no login and runs the same checks `solution pack`
runs. Run it after **every** edit — it is the only check between an authored
document and a deploy.

> **S19 — de-risk before relying on this route.** `FIELD_TYPE_NOT_ALLOWED` is in that
> diagnostic set, and the hand-authored fields are exactly the types the CLI refuses.
> A fixture in this repository proves the shape is *writable*
> (`tests/tasks/uipath-platform/integration-service/_setup/df_local_solution/`), but
> that fixture is a test's `_setup` input and is never packed — so it does not prove
> `validate --local` and `pack` accept it. One run of both gates against a
> two-entity hand-authored solution settles it. **If it rejects, complex fields move
> to the tenant lane**: entities holding a relationship or choice-set field become
> open items created by the engineer with `uip df entities create "<Entity>" --file`,
> and the local tier keeps only the scalar entities
> ([open-items-guide.md § Data Fabric](open-items-guide.md) already carries that
> instruction).

## What reaches the genome

| From | Genome section |
|---|---|
| each entity | one **Platform Dependencies** row — `<EntityName>` / Data Fabric entity / what the automation does with it |
| the model as a whole | the **`## Data Model`** section — counts, components, the four defaults as applied, the deferred set |
| register rows that are `locus: uipath, level: transition` by rule | a **Business Rule** under the writing step, plus one **acceptance criterion** |
| entities the target environment must receive | nothing here — the open items are written at execution, from Platform Dependencies, as for every other resource |

The entity *definitions* do not go into the genome body. The genome names resources
and states behaviour; `entities.json` and the solution resources are the artifacts.
Writing a field list into the genome duplicates a contract that is already machine-
checked, and it would drift ([genome-format-guide.md § Provenance](genome-format-guide.md)).

## Anti-patterns

1. **Creating anything on a tenant.** Author mode is local-only; the target
   environment's setup is an open item.
2. **Authoring a resource file or a `.entity` stub from scratch.** The CLI creates
   the pair; the applier appends (§ Everything stays local).
3. **String-patching `spec.resourceJson`** instead of parsing and re-serializing.
4. **Recomputing `numberId`.** A one-way door; renumbering remaps deployed records
   (§ Choice sets).
5. **Emitting a `Reference*` pointer with no `resource.dependencies` row.** Packs
   clean, fails at deploy.
6. **Skipping `validate --local` because the files "look right".** It is the only
   gate between the document and a deploy.
7. **Copying the Data Fabric type table, operator matrix or command flags into this
   skill.** They belong to `uipath-platform` and will drift.

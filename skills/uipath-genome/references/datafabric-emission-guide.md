# Data Fabric Emission Guide — entities.json to solution resources

Rules and procedure. How the derived entity set becomes files inside the solution,
what the on-disk shape is, and which gates must pass before edits are offered.

Read whole before writing any solution resource. Router:
[data-model-guide.md](data-model-guide.md).

Everything about field types, choice-set mechanics, relationship bindings and
federated rules belongs to `uipath-platform` → `references/data-fabric/`. This file
states only what is specific to emitting a derived model: the local-authoring route,
the resource shape the CLI cannot write, and the gates.

## The two tiers

`uip df entities create --local` authors into the solution on disk — no login, no
tenant, and the entity becomes a real table at deploy. Author mode writes nothing to
a tenant ([data-model-guide.md § Boundaries](data-model-guide.md)).

**The local path carries scalar fields only.** `RELATIONSHIP`, `CHOICE_SET_SINGLE`
and `CHOICE_SET_MULTIPLE` cannot be authored into a solution at all — not through the
CLI, and not by hand-editing the resource file either.

| Tier | Holds | Route |
|---|---|---|
| **Local** | every entity, with its scalar fields and their options | `uip df entities create <Name> --local`; ships in the solution, becomes a table at deploy |
| **Open item** | every relationship field, every choice-set field, every choice set | the engineer runs `uip df entities update` / `choice-sets create` against the target tenant after deploy |

> **Measured, not assumed.** Hand-authoring the field objects into
> `resources/solution_folder/entity/native/<Name>.json` and running
> `uip df entities validate --local` fails:
>
> ```
> FIELD_TYPE_NOT_ALLOWED  Field 'Supplier' uses an unsupported type combination
>                         (Relationship / UNIQUEIDENTIFIER).
> FIELD_TYPE_NOT_ALLOWED  Field 'Tier' uses an unsupported type combination
>                         (ChoiceSetSingle / INT).
> ```
>
> `uip df choice-sets` has no `--local` flag, so a choice set has no solution-side
> representation to point at even if the field validated. The fixture at
> `tests/tasks/uipath-platform/integration-service/_setup/df_local_solution/` carries
> a hand-written `ReferenceChoiceSet` and looks like a counter-example; it is a test's
> `_setup` input and is never validated or packed.

**Writing one by hand does not merely fail a gate — it bricks the entity.** The
validator checks the *stored document*, not the create body, so the field is rejected
however it got there. Three verbs then refuse it: `validate --local`, `solution pack`
(same check), and `entities update --local`, which declines **even an unrelated
edit** rather than leave the entity invalid. `get` and `list` still read it, so the
damage is quiet until pack.

**So the applier never edits a resource file.** The CLI owns both halves of the pair
and nothing else writes them — the standing rule holds with no exception. The complex
tier leaves the solution as open items instead.

**One consequence the genome must carry:** a workflow that traverses a relationship
cannot be built until that field exists, because the generated entity types come from
the schema. Any Workflow step whose `**Data:**` line has a `via` clause is flagged in
the completion report as blocked on its open item
([data-model-consumption-guide.md](data-model-consumption-guide.md)).

The restriction is a hard allowlist, not a flag to find: a type map in the authoring
path, a second membership check against an external package's pair list, and a
tenant-only classification of the reference keys. There is no environment variable
and no preview mode that lifts it. When local support lands, the open-item tier
collapses into the local one — `entities.json` already carries the fields with
symbolic targets, so the change here is to emit them in pass 1's body and delete
pass 3.

## entities.json

Genome's own format, derived from the inventory. **Not** the
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

A choice set has no local form, so it is created on the tenant by the open items
(§ The two tiers). **The server assigns `NumberId`, 0-based by creation order**, and
the number is immutable once records exist — the stored record value is the integer,
so renumbering silently changes what every existing row means. That is the one-way
door ([data-model-guide.md § Commitment ladder](data-model-guide.md)), and it closes
at the open-item run, not at derivation.

What `entities.json` carries is therefore a **proposal**: the value order the bundle
implies, with the numbers it would produce. `--previous` carries that proposal
forward so a re-derivation does not reshuffle it, and a value the ontology drops
keeps its slot rather than letting a later value inherit it.

The proposal is not authority. `uip df choice-set-values create` can be rejected
without the server reserving the slot, so a later success takes the number the failed
one was meant to occupy. The open items therefore say: create one value at a time,
**fail loud on each** — never silence a rejection — then re-read with
`uip df choice-sets list-values` and check every number against the proposal before
any record is written. `uipath-platform` → `references/data-fabric/choice-sets.md`
owns that rule.

## The resource shape the CLI writes

Read-only knowledge: the applier never writes these files, but a reviewer and a
diagnosis need to know what the CLI produced. Two files per entity that must agree —
a `<Name>.entity` stub in the Entity project, and the definition resource whose
schema lives **JSON-escaped inside `spec.resourceJson`**.

Measured from a real `uip df entities create --local`, not from a fixture:

- the envelope carries `docVersion`, then `resource` with `name`, `kind`, `type`,
  `apiVersion`, `isOverridable`, `dependencies`, `runtimeDependencies`, `folders`,
  `spec`, `locks`, `key`, `files`;
- `resource.key` equals `resourceJson.Id`, a random GUID the CLI mints;
- `resourceJson` carries `EntityTypeId`, `Description`, `Data`, `ExternalFields`,
  `SourceJoinCriterias`, `RecordCount`, `StorageSizeInMB`, `UsedStorageSizeInMB`,
  `AttachmentSizeInByte`, `IsRbacEnabled`, `InvalidIdentifiers`, `IsModelReserved`
  and `CategoryId` beside the obvious keys, and is serialized **compactly, in
  insertion order** — not sorted, not indented;
- the five system fields (`Id`, `CreateTime`, `CreatedBy`, `UpdateTime`,
  `UpdatedBy`) are materialized with `IsSystemField: true`;
- every field object carries eighteen keys, and a non-system field five more
  (`DefaultValue`, `ReferenceChoiceSet`, `ReferenceEntity`, `ReferenceField`,
  `ReferenceName`), all present and mostly null;
- `FolderId` sits at entity level inside `resourceJson`, holding the unassigned-folder
  sentinel `99999999-9999-9999-9999-999999999999`;
- `dependencies` is written empty and is not populated by the CLI.

The practical reading: **the shape is the CLI's to own, and it is wider and more
particular than it looks.** That is the second reason the applier does not edit it —
even setting aside the validator, a partial field object written by hand diverges
from what the CLI and the deploy expect.

### For reference: the shape a hand-authored field would need

Kept because the open-item instructions have to name the equivalent values, and
because this is what changes when the CLI gains local support.

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

1. **`SqlType.Name` is the SQL type, not the CLI enum** — a third vocabulary beside
   the CLI write shape (`"type": "STRING"`) and the API read shape
   (`FieldDataType.Name`). The mapping is the SQL column of `uipath-platform` →
   `references/data-fabric/entity-schema.md` § Supported Field Types; do not copy it
   here, it drifts.
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
  --open-items "<HANDOFF_DIR>/open-items/data-fabric.md" \
  [--dry-run]
```

Four passes. All local — no login, no tenant, no UUID round trip.

| # | Pass | Does |
|---|---|---|
| 0 | validate graph | discard self-references; **fail hard** on any remaining cycle, naming its members; check every relationship target exists |
| 1 | entities | `uip df entities create <Name> --local --project-name <P>` with **scalar fields only** — the CLI writes both halves of the pair and mints the ids |
| 2 | gate | `uip df entities validate --local`; a failure stops the run with the diagnostics |
| 3 | open items | write the complex tier — every choice set, every relationship field, every choice-set field — as an ordered checklist with the exact commands |

Rules:

- **Never write into `resources/solution_folder/`.** The CLI owns those files
  (§ The two tiers). The applier reads them only to resolve a minted id for the
  open-items text.
- **Idempotent.** Pass 1 skips an entity whose resource file exists; pass 3 rewrites
  the open-items file wholesale from `entities.json`, so it is always current.
- **Ordered open items.** Choice sets first, then entity updates that reference them,
  then relationship fields in dependency order — the engineer runs the file top to
  bottom.
- **`--dry-run`** prints every command and every file write without performing them.

## Open items for the complex tier

One section per kind, each row naming the entity, the field, the target and the exact
command. Ids are not knowable before deploy, so every command resolves its own:

```markdown
## Data Fabric — complex fields

These could not ship in the solution: the local authoring path carries scalar fields
only. Run them against the target tenant after the solution deploys.

- [ ] Create the choice set `<ChoiceSetName>` with its values, in this order —
      the position fixes each value's immutable NumberId:
      `uip df choice-sets create "<ChoiceSetName>" --output json`
      `uip df choice-set-values create <choice-set-id> "<VALUE_1>" --output json`
      …then re-read with `choice-sets list-values <choice-set-id>` and check the
      numbers against the table below before any record is written.
- [ ] Add `<EntityName>.<FieldName>` as a choice-set field:
      `uip df entities update <entity-id> --body '{"addFields":[{"name":"<FieldName>",
      "type":"CHOICE_SET_SINGLE","choiceSetId":"<choice-set-id>"}]}' --output json`
- [ ] Add `<EntityName>.<FieldName>` as a relationship to `<TargetEntity>`,
      displaying `<TargetDisplayField>`:
      `uip df entities update <entity-id> --body '{"addFields":[{"name":"<FieldName>",
      "type":"RELATIONSHIP","referenceEntityId":"<target-entity-id>",
      "referenceFieldId":"<target-display-field-id>"}]}' --output json`
```

Three things the text must carry, because they are decisions rather than mechanics:

1. **Value order fixes `NumberId`.** It is assigned 0-based by creation order and is
   immutable, so the table of intended numbers travels with the checklist and is
   checked against `list-values` before records exist.
2. **`referenceFieldId` is the target's display field**, not its `Id` — it decides
   what renders in pickers. `entities.json` carries `displayField` as a **proposal**;
   `uipath-platform` requires the choice to be confirmed rather than defaulted, and
   never silently defaulted to the target's `Id`. An entity with no proposal asks.
3. **Which workflows are blocked** until each field exists (§ The two tiers).

## Validation gates

All must pass before edits are offered.

| Gate | Command | Catches |
|---|---|---|
| Schema | `uip df entities validate --local` | `ENTITY_NAME_INVALID`, `ENTITY_NAME_NOT_UNIQUE`, `FIELD_NAME_INVALID`, `DUPLICATE_FIELD_NAME`, `FIELD_TYPE_NOT_ALLOWED`, `NAME_RESERVED`, `SYSTEM_FIELD_MISSING`, `SYSTEM_FIELD_MODIFIED`, `FIELDS_MALFORMED`, `TOO_MANY_MULTILINE_MAX`, and the stub↔resource pairing |
| Pack | `uip solution pack "<SOLUTION>" --dry-run` | the same rules at the shipping boundary |
| Completeness | every complex field in `entities.json` has an open-item row | a field silently dropped rather than deferred |

`entities validate --local` needs no login and runs the same checks `solution pack`
runs. Run it after **every** edit — it is the only check between an authored
document and a deploy. It is also the gate that settled the two tiers: it rejects a
hand-authored relationship or choice-set field, which is why the applier does not
write one (§ The two tiers).

Two environment notes for a probe: `uip solution init` and `uip df entities create
--local` need no login, but the CLI's daily tool-update check does reach the network
and fails without an npm token — set `UIPATH_CLI_DISABLE_VERSION_SYNC=1` to skip it.

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
2. **Writing into `resources/solution_folder/` at all.** The CLI owns both halves of
   the pair (§ The two tiers).
3. **String-patching `spec.resourceJson`** instead of parsing and re-serializing.
4. **Recomputing `numberId`.** A one-way door; renumbering remaps deployed records
   (§ Choice sets).
5. **Emitting a `Reference*` pointer with no `resource.dependencies` row.** Packs
   clean, fails at deploy.
6. **Skipping `validate --local` because the files "look right".** It is the only
   gate between the document and a deploy.
7. **Copying the Data Fabric type table, operator matrix or command flags into this
   skill.** They belong to `uipath-platform` and will drift.

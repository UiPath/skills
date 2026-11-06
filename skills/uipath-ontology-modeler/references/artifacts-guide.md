# Ontology Artifacts Guide

The modeler writes the ontology's artifact files into `WORKDIR` and attaches them to the Ontology resource with `uip ont files add`. The CLI packages them into the deployable zip. This guide lists the files, their types and how many of each the ontology takes.

| File | Artifact type | Media type | Count |
|---|---|---|---|
| `{name}.ofn` | `schema` | `text/owl-functional` | exactly 1 |
| `{name}-constraints[-{area}].ttl` | `constraints` | `text/turtle` | 1+ |
| `{name}-mapping.yarrrml.yml` | `mapping` | `application/yaml` | exactly 1 |
| `{name}-summary.json` | `summary` | `application/json` | 0..1 |
| `{name}-context.json` | `context` | `application/json` | 0..1 |

`{name}` is the Ontology resource name, verbatim, in every file name and every IRI.

Per-file format rules:

| Artifact | Guide |
|---|---|
| `schema` | [owl-patterns-guide.md](owl-patterns-guide.md) |
| `constraints` | [shacl-patterns-guide.md](shacl-patterns-guide.md) |
| `mapping` | [mapping-yarrrml-guide.md](mapping-yarrrml-guide.md) |
| `summary`, `context` | [summary-context-guide.md](summary-context-guide.md) |

Check one file at a time with `uip ont artifacts check <FILE_NAME> --content-type <MEDIA_TYPE> --type <ARTIFACT_TYPE> --file <PATH>`. That check is offline. Whole-ontology validation (`uip ont validate --local`) calls the ontology service and needs `uip login`.

## Write order

1. Schema (`{name}.ofn`): classes, properties, labels and comments.
2. Constraints (`{name}-constraints.ttl`): one shape per rule, over terms the schema declares.
3. Mapping (`{name}-mapping.yarrrml.yml`): one block per class over the local entity, using the entity and field names exactly as created.
4. Summary and context, only when they add value.

Every term in a later file must exist in the schema.

## Files the skill does not own

- `operations/` is reserved and empty. Put nothing in it.
- The CLI writes `ontology.json` and the zip. The skill never builds, reads or edits either one.

## Entity-backed facts

- The mapping links a class to its entity by name only (`table: <EntityName>`). The service resolves the name in the deployment folder at install.
- System fields are `Id`, `CreateTime`, `UpdateTime`, `CreatedBy` and `UpdatedBy`. Never model them as domain properties. `$(Id)` is the subject key.
- A relationship is one `RELATIONSHIP` field on the referencing entity. The mapping joins it with `equal(str1=$(customer), str2=$(Id))`.
- A choice-set field is mapped by value name (`xsd:string`) and listed in the constraints with `sh:in`.

## Do not

- Write business rules, functions or actions into any artifact. The ontology describes data only: classes, properties, constraints and mappings.
- Write a Data Fabric identifier of any kind into an artifact. Reference entities, fields and choice sets by name.
- Put a `.txt` or manifest file in the artifact set. The summary is JSON.

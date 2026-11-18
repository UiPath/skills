# Errors Guide

Act on each violation's `rule`, `file` and `suggestion` (`Rule`, `File`, `Suggestion` in a success envelope; lower case in a failure's `Data`); never re-implement a check. Per-file rules come from `artifacts check`, `files add` and `validate`; cross-file rules from `validate`. Error codes come in the `Code` of a failure envelope; `NAME_RESERVED` and the field-name rules of `uip df` come in its `Instructions`.

## Recovery table

| Signal | Source | Action |
|---|---|---|
| `OFN-001`, `OFN-002`, `OFN-004`, `OFN-005`, `OFN-009` | local | Fix `{name}.ofn` per [owl-patterns-guide.md](owl-patterns-guide.md); `artifacts check`, `files add`, validate |
| `SHC-002`, `SHC-003`, `SHC-004`, `SHC-006`, `SHC-007`, `SHC-008`, `SHC-009`, `SHC-010` | local | Fix the constraints file per [shacl-patterns-guide.md](shacl-patterns-guide.md); same loop |
| `SHC-011` | local | WARNING: the `.ttl` declares no SHACL shape, so it is probably another artifact type under the wrong extension. Rename it to its real type's extension, or drop it with `uip ont files remove` (constraints are optional) |
| `MAP-002`, `MAP-004`, `MAP-005`, `MAP-006` | local | Fix the mapping per [mapping-yarrrml-guide.md](mapping-yarrrml-guide.md); same loop |
| `SUM-003` | local | The summary has a root `@context`, so it is the context file: rename it `{name}-context.json` (or `--type context`), or remove `@context` from the summary; same loop |
| `CTX-001`, `CTX-002`, `CTX-003`, `CTX-005`, `CTX-006`, `CTX-007`, `SUM-001`, `SUM-002` | local | Fix the context or summary per [summary-context-guide.md](summary-context-guide.md), or drop it with `uip ont files remove`; same loop |
| `MAP-012` | local | Remove every Data Fabric id from the mapping; keep `table: <Entity>` |
| `XF-001` | local | Exactly one schema, one mapping, any number of constraints (optional), at most one summary and one context; `files add` / `files remove` |
| `XF-002` | local | WARNING: re-run `uip ont files add` to rebuild the zip. ERROR: rebuild it with `files add` for every artifact |
| `XF-003`, `XF-004` | local | Use `https://ontology.uipath.com/<name>#` and `https://ontology.uipath.com/shapes#` for `shape:` |
| `XF-005` | local | Remove the construct outside OWL 2 QL; record the rule in `rdfs:comment` or SHACL |
| `XF-006`, `XF-008` | local | Declare the term in the schema, or fix the name in the mapping or constraints |
| `XF-007` | local | Add `rdfs:label` and `rdfs:comment` to every class and property |
| `XF-009` | local | Give the class a property and a mapping block over a local entity, or fold it into a comment |
| `XF-010` | local | Map every property; give every class a `sh:targetClass` shape |
| `XF-012`, `XF-013` | local | The entity is missing from the solution or the column isn't a field. Add the local entity (`cd "<SOLUTION_DIR>" && uip df entities create <E> --local --body '<BODY>' --output json`) and link it (`uip ont update <Name> --local --add-entity <E> --solution-folder "<SOLUTION_DIR>" --output json`), or fix the name; when the field is genuinely missing, after confirmation `cd "<SOLUTION_DIR>" && uip df entities update <E> --local --body '<CHANGE>' --output json` adding it, then validate |
| `XF-014`, `XF-015` | local | Declare the object property or add the join per [mapping-yarrrml-guide.md](mapping-yarrrml-guide.md#joins) |
| `XF-017` | local | A relationship cycle among the ontology's entities. After confirmation, remove one RELATIONSHIP field of the loop locally (`cd "<SOLUTION_DIR>" && uip df entities update <E> --local --body '<CHANGE>' --output json` with `removeFields`), keep the inverse in the schema ([owl-patterns-guide.md](owl-patterns-guide.md#inverse-properties)), then validate |
| `XF-019` | local | Copy the choice-set value names exactly into `sh:in`; add a missing value with `cd "<SOLUTION_DIR>" && uip df choice-set-values create <C> <VALUE> --local --output json`, or author a missing choice set with `cd "<SOLUTION_DIR>" && uip df choice-sets create <C> --local --output json` and its values, then validate |
| `ZIP-001` | local | The zip exceeds the service limits. Split large constraint files or trim summary and context, then `uip ont files add` again |
| `SVC-001` | service | Every service finding is `SVC-001` on the named file. Fix the syntax it names; same loop |
| `ENTITY_ID_IGNORED` | service | An `SVC-001` WARNING naming it; same fix as `MAP-012` |
| `ValidationFailed` | CLI | The ERRORs are in `Data`; fix each per the rows above, then validate |
| `ServiceValidationUnavailable` | CLI | Service validation needs `uip login`; ask for it, then validate again; stop if the service stays unreachable |
| `ServiceValidationFailed` | CLI | The service could not validate; `Instructions` carries its answer (`Not Found` when the tenant has no validate endpoint) and `Data` the local results. Stop and tell the user; never pack as validated |
| `ArtifactCheckFailed` | CLI | The ERRORs are in `Data.violations`; nothing was attached. Fix them, then `files add` again |
| `ArtifactTypeUnresolved`, `InvalidArtifactFileName` | CLI | Rename the file to the `{name}-…` convention (`{name}-summary.json`, `{name}-context.json`) or pass `--type`; never name a file `ontology.json` |
| `ArtifactTypeAlreadyPresent` | CLI | Re-add under the existing file name, or `files remove` the old one first |
| `ArtifactTypeNotSupported` | CLI | Drop the file; only the five artifact types are supported |
| `ArtifactNotFound` | CLI | Check `uip ont files list <Name> --local` and use the listed name |
| `NoParentSolution` | CLI | `--solution-folder` holds no `.uipx`; fix `SOLUTION_DIR` or init the solution (Stage 3) |
| `OntologyNotFound` | CLI | Create the resource (Stage 6), or fix the name from `uip ont list --local` |
| `OntologyNameTaken` | CLI | The name is used in the solution: ask for another, or update the existing resource |
| `InvalidOntologyName` | CLI | Use a name matching the `ONTOLOGY_NAME` pattern |
| `EntityNotFound` | CLI | Author it locally with `uip df entities create <E> --local --body '<BODY>'` (Stage 4), or fix the name |
| `LocalFlagRequired` | CLI | Add `--local` |
| `LocalAndFolderConflict`, `FolderKeyAndPathConflict`, `InvalidArguments` | CLI | Drop the flag that doesn't belong to the local flow (`files list` takes `--local` or `--package`, never both) |
| `InvalidFolderKey`, `InvalidFolderPath` | CLI | The local flow passes no folder key or path; drop it |
| `ConfirmationRequired` | CLI | `uip ont delete` needs `--yes`; ask the user first |
| `ResourceFileMissing`, `InvalidResourceArchive` | CLI | Rebuild the zip with `uip ont files add` for every artifact |
| `InvalidAttachedFile`, `FileAttachNotSupported`, `ResourceNotFound` | CLI | The attach was refused; read `Instructions`, fix the solution state, then `files add` again |
| `PackageNotFound`, `OntologyNotInPackage` | CLI | Pass the `PACKAGE_PATH` pack reported; if the ontology is missing, validate and pack again |
| `OntologyManifestNotWritten` | CLI | Re-run `uip ont files add`; if it repeats, stop and report the CLI version |
| `Ambiguous match`, `No remote resource found with key` | connection import | Pass `--folder-path "<CONNECTION_FOLDER>"` to the `--kind Connection` import, or `--cloud-key` from the listed candidates |
| `CONNECTION_NOT_FOUND`, or a federated connection missing from the solution | `uip df` | Import the connection (Stage 3), then create the federated entity again |
| `Not logged in` on a federated `uip df entities create … --local` | `uip df` | A connector source makes that create read the connection and the source object's fields from the tenant; ask for `uip login`, then retry. A federated entity over local native sources only never needs it |
| `unknown command 'ont'` | `uip` | The installed `uip` predates the ontology tool. Stop and ask the user to update `uip`, then re-run from the saved model. Never pack, refresh or import resources instead: a package without the ontology is not the result |
| `NAME_RESERVED` (in `Instructions`) | `uip df` | The entity is named `Order` or `Group`. Propose a domain name (`SalesOrder`), confirm it, use it in the class map, every body and the mapping, then create it |
| `REFERENCE_TARGET_NOT_FOUND`, `CHOICE_SET_NOT_FOUND` | `uip df` | The create order is wrong or a name is misspelled: create the target entity or choice set first, then retry |
| `RELATIONSHIP_CYCLE` | `uip df` | The field would close a reference cycle. Keep the relationship on one side and express the inverse with `InverseObjectProperties` ([relationships-guide.md](relationships-guide.md)) |
| `RELATIONSHIP_TARGET_FEDERATED` | `uip df` | A federated entity can't be a `RELATIONSHIP` target: use a plain column joined to its key column |
| `FEDERATED_UPDATE_NOT_SUPPORTED` | `uip df` | After confirmation, `uip df entities delete <F> --local --yes`, then create it again with the changed body |
| `ENTITY_IN_USE`, `CHOICE_SET_IN_USE` | `uip df` | Another entity's field still references it: after confirmation, change that field first (`uip df entities update <E> --local`) |
| `CHOICE_SET_NAME_TAKEN`, `CHOICE_SET_VALUE_NAME_TAKEN`, `ENTITY_NAME_TAKEN`, "Entity '<E>' already exists" | `uip df` | The duplicate check was skipped: reuse the existing choice set, value or entity (names are unique regardless of case) |
| `INVALID_NAME` | `uip df` | The choice-set name breaks the naming rules or is a reserved keyword: pick a domain name per [entity-guide.md](entity-guide.md) |
| `INVALID_FEDERATED_SOURCE`, `INVALID_JOIN`, `UNSUPPORTED_SOURCE_COLUMN` | `uip df` | Fix the federated body: each source names an `entityName` or a `connectionName` + `object`, each join side names a source of this entity, no join relates the primary source to itself, and every native source column it maps or joins on is a plain column. A relationship, choice-set, file or auto-number column, or an imported type such as `INT`, is refused even with a `type` override: leave it out of `fields` and joins ([entity-guide.md](entity-guide.md#federated-entities)) |
| `referenceEntityName` or `choiceSetName` unknown, or local choice sets or federated create unknown | `uip df` | The `uip` build cannot author these locally. Stop and ask for a newer CLI; never substitute `STRING` |
| `InstallError` "Missing in the target folder" | deploy, via `uipath-solution` | The entity, column or choice set is not in the solution. Add it locally (`cd "<SOLUTION_DIR>" && uip df entities create <E> --local --output json`, or `entities update`), validate, pack, and redeploy through `uipath-solution` |
| Packed listing differs from the validated set | `files list --package` | `files add` again, validate, pack |
| `BLOCKED_AMBIGUITY` | skill | A class-to-entity, join or identifier has no unique answer: stop and ask |

Deploy-stage rejections other than "Missing in the target folder" (`TypeIncompatible`, `EntityConflict`, an ontology rename onto a taken name) belong to `uipath-solution`.

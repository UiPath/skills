# Federated Rerun Guide — a second run over a model already generated

Read this **before phase 1** of [federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md) whenever a `<MODEL_NAME>-ledger.json` already sits beside the `.ofn`. It also covers resuming a run that failed partway. The phase contracts, the artifact shapes and the hard constraints stay in the pipeline guide.

A rerun is the dangerous half of this lane. Field types and entity topology are write-once, so every change to a federated entity is a **delete and a recreate**, and nothing about the recreated entity is guaranteed to match the one that was deleted — its column names included. The committed artifacts are the only thing that survives.

**A rerun is not a fresh run in a cleaned tree.** Deleting the artifacts loses the identity map and the ledger, and with the ledger goes every record of what was chosen over what — so the run re-asks every question a person already answered, and silently re-proposes the binding they overruled.

## The identity map

A federated entity cannot be updated: `uip df entities update --local` is refused with **`FEDERATED_UPDATE_NOT_SUPPORTED`**. So nothing on the platform side carries identity across a change. Everything that does is on disk:

| Identity | Held by | Why it must survive |
|---|---|---|
| what the previous pack was | `<MODEL_NAME>-pack.json` | its `run`, its input hashes and every artifact's hash. It is how a rerun tells *the `.ofn` changed* from *the tenant changed* before it reads a single record, and the new run's `supersedes` names its `run` |
| class → group | the partition manifest's group records, by `grp:` id | a regenerated partition that cuts differently silently moves properties between entities |
| group → entity name | the group record's `entityName` | `table:` in the target mapping names it, and so does the genome's Data Fabric dependency row |
| class → cells | the source YARRRML block keys, `<Class>__<Object>`, which are the `cell:` ids | the key is the cell, so a block that keeps its key keeps its bindings and its hand edits |
| entity → body | `entities.json`, keyed by `ent:` id, each entry naming the `grp:` it came from | it is the record of what was asked for, against which the resource file is diffed — after parsing the resource's stringified document, never as raw text (pipeline guide phase 5 § What the CLI adds). **The `group` field is what used to be a name match**: an entry whose `group` resolves to no record, or to a group whose `entityName` differs from the entry's `name`, is the naming fault rather than a silent re-link |
| decision, exception and resolution ids | the ledger | `D<n>` / `E<n>` / `R<n>` are never reused or renumbered, across runs included |

Those six are the identity map. Keep all six or the rerun is a first run.

**Every id in the pack is content-derived** (pipeline guide § Ids), so a rerun that finds the same thing mints the same id with no coordination between the runs, and a diff is a comparison of id sets rather than of file positions. Two ids do change when the subject looks the same, and both are real changes this guide already handles: a connection renamed on the tenant re-keys its `con:` and every `obj:` and `fld:` under it (§ The procedure step 1), and an entity renamed re-keys its `grp:` and `ent:`, so the diff reads a rename as a removal plus an addition (§ The three diff classes).

## The three diff classes

Compute the diff per entity — the new bodies against the committed `entities.json`, matched on `ent:` id — and classify every change before applying any. In this lane the *how* is the same for all three (delete, then create), so the classification exists to say **what else has to change** and what to tell the user:

| Class | What changed | What it costs |
|---|---|---|
| **additive** | a new entity, a new block, a field added to an existing entity's `fields` list | the entity is still deleted and recreated, because `update --local` is refused. Downstream, only the target mapping's new `po:` rows and the ontology declaration change |
| **type change** | a property's `sh:datatype` changed, or the connector now declares a different type for a bound field | the field type is write-once, so the entity is recreated and **every `po:` pair over that column is re-authored**. A reconciliation row becomes an agreement row, or the reverse — rerun the agreement rule for that cell ([federated-check-guide.md § The agreement rule](federated-check-guide.md)) |
| **removal** | a class, a cell, a field or a whole entity gone from the new partition | the resource file, the `entities.json` entry, the source and target blocks, and the ontology declaration all go. **The declaration goes first** — `uip ont update <ONTOLOGY_NAME> --local --remove-entity <ENTITY_NAME>`, then the delete: the name resolves only while the entity resource exists (§ The procedure, the recreate loop) |

**An entity renamed reads as a removal plus an addition.** `grp:` and `ent:` both carry the entity name, so a new name is a new id on both, and the diff reports the old id gone and a new one arrived rather than one entity changed. That is the correct reading — the rename changes `table:` in the target mapping and the genome's Data Fabric dependency row — and phase 4's decision carrying the old name in `over` is what ties the two ids together.

**A removal nobody asked for is an exception, not a removal.** Discovery failure looks exactly like a dropped class: a connector outside the allow-list, a connection that stopped returning an object, a field renamed upstream. Before deleting anything, check the removal against the model — a class still in the `.ofn` whose cells vanished is a discovery finding, and the exception names which.

## The procedure

1. **Read the pack manifest, then the ledger, then re-check the bootstrap.** The manifest says what the previous run was and which inputs it ran against; re-hash the `.ofn` and the constraints `.ttl` against its `inputs` before anything else, because an unchanged input means every difference found later came from the tenant. Then mint this run's `run` id with `supersedes` naming the previous one. Open exceptions from the previous run are still open — an exception is open while no `R<n>` closes it, computed from the ledger, and a rerun does not clear them; a question a person did not answer is not answered by asking the tenant again. The bootstrap is re-checked, never re-run: the solution, the ontology resource and every connection resource the source YARRRML's `connection:` keys name must still be there (pipeline guide § Bootstrap). A connection **renamed on the tenant** since the first run is the case to watch — the resource keeps the old name, so re-add the resource under the new name and re-key every `connection:` that named the old one, as a decision carrying both names. The rename also re-keys that connection's `con:` id and every `obj:` and `fld:` under it, and the connection record's unchanged `connectionId` is what proves it is the same connection.
2. **Re-run phases 1 and 2 in full.** Never reuse a discovery record from an earlier run: the tenant is the one input that changes with nobody editing a file. Write the new record to the same path — the old one is in git.
3. **Diff the new discovery record against the committed one** before touching correspondence. Fields gone, types changed, a primary key that disappeared: each is a finding, and a disappeared key is a hard stop for every class bound to that object, the same as on a first run.
4. **Re-propose correspondence only for the cells the diff touched.** A cell whose object, key and fields are unchanged keeps its block, its hand edits and its `R<n>` resolution comments (§ The merge rule).
5. **Re-run phase 4 and compare the new partition against the manifest.** A group whose boundary moved is a decision with the old boundary in `Over`. A group whose `Forcing signal` is filled did not move by choice — if the new partition moves it, the forcing signal changed, and that is the finding to report rather than the cut to take.
6. **Classify every entity change** (§ The three diff classes), then apply per entity: delete and recreate the changed ones, leave the unchanged ones alone.
7. **Read the column names back for every recreated entity** ([federated-mapping-guide.md § Column names](federated-mapping-guide.md)). The collision rename depends on `externalFields` order, so a recreate whose source order changed **renames columns that did not change** — and a target mapping carried over unchanged is then wrong in exactly those places.
8. **Re-run phase 7 over the whole set**, not only the changed entities. The cross-file rules are over the file, so one changed block is a new result for the file.
9. **Append to the ledger, and rewrite the pack manifest.** Never renumber and **never rewrite any row** — close an exception by appending its `R<n>`; there is no state cell to flip (pipeline guide § The ledger rule 2). The manifest is the one artifact a phase rewrites: refresh every hash it touched, including the ledger's, which changes under every phase.

The recreate loop for one changed entity, in order:

```bash
uip ont update <ONTOLOGY_NAME> --local --remove-entity <ENTITY_NAME>
uip df entities delete <ENTITY_NAME> --local --yes
uip df entities create <ENTITY_NAME> --local --body '<BODY>'
uip ont update <ONTOLOGY_NAME> --local --add-entity <ENTITY_NAME>
uip df entities validate <ENTITY_NAME> --local --output json
uip df entities get <ENTITY_NAME> --local --output json
```

**`--remove-entity` comes before the delete.** `resolveEntityKeys` (`packager-tool-ontology/src/inline/ontology-service.ts:172`) resolves a name only through an entity resource that still exists, so removing the declaration after the delete throws `EntityNotFound`. Pass the stale key instead of the name if the entity is already gone.

`--yes` is required; the CLI never prompts on an irreversible delete.

**Both `uip ont update` calls are needed on every recreate, rename or not.** The ontology stores entity **keys**, not names: `createEntitySkeleton` mints `Id: randomUUID()`, `wrapEntityJson` sets `resource.key = entity.Id`, and `entityNamesOf` resolves the stored keys back to names. A same-name recreate therefore carries a **new key**, `declaredEntities` loses the entity, and XF-012 fires at phase 7 against every block whose `table:` names it. The re-declaration is not optional — dropping it is exactly the failure phase 5's precondition 3 warns about (pipeline guide phase 5).

## The merge rule

The source YARRRML is committed, hand-editable and regenerated by a rerun. Three cases:

| The new run | The committed file | Rule |
|---|---|---|
| proposes the same binding | unchanged | rewrite freely |
| proposes a different binding | carries a hand edit, or an `R<n>` resolution comment on that block | **the committed file wins.** Keep the block, and write a decision naming what the run would have proposed and why it was not taken. A resolution comment is a person's answer to an exception; regenerating over it asks the same question twice |
| proposes nothing for the block | the block exists | the removal case of § The three diff classes — check it against the model before deleting |

A hand edit is recognised by the `R<n>` comment a resolution wrote, or by a diff against the previous generated file in git. The manifest's phase-3 hash settles the cheaper half of that question first: a committed file whose `sha256` still matches what the previous run recorded was not edited at all. Nothing else marks one, so **a run that cannot diff the previous generation treats every block as hand-edited** and proposes rather than rewrites.

What the file is authoritative for does not change on a rerun: bindings, subject keys, field names and discovered types are its, and the declared constraints stay in SHACL and are read from the typed model, which phases 6 and 7 read rather than re-parsing the `.ttl` ([federated-source-mapping-guide.md § What this file is, and what reads it](federated-source-mapping-guide.md)).

## Resuming a failed run

Phase 5 writes N entities in N calls and nothing rolls back (pipeline guide phase 5 § Stops). Recover from the tree rather than from memory:

1. **List what exists.** The resource files under `resources/solution_folder/entity/federated/` are the entities created; `entities.json` is the full set that was asked for; the difference, by `ent:` id, is what is left to create. The manifest's phase-5 list says which resource files this run wrote and with what hash, so a file the manifest does not carry was left by an earlier run.
2. **Validate each existing resource before trusting it** — `uip df entities validate <ENTITY_NAME> --local --output json`. A create that failed partway may still have written a file.
3. **Create only the missing entities**, and declare each on the ontology as phase 5 does.
4. **Do not delete the entities that succeeded.** Deleting costs the column names phase 6 already read back, and the recreate may rename them (§ The procedure step 7).
5. **Close the exception** the failed create wrote, with an `R<n>` row naming what the resume created.

## Registration and packaging — open

Whether dropping a file under `resources/` registers it with the solution manifest is **unverified**, and nothing in this lane covers `pack`, `publish` or `deploy`. That is the gap between *the pipeline ran* and *the entities exist*. The solution lifecycle is `uipath-solution`'s: route the question there, and carry whatever is unresolved as an open item for the target environment ([open-items-guide.md](open-items-guide.md)). **Never assert that a file under `resources/` is a registered resource** — the only registration this lane performs and re-checks is the connection resource and the `uip ont update --add-entity` declaration.

**What packs is settled, even though packing is not this lane's.** The solution carries **entity and connection resources only**: the ontology resource is created and validated locally and removed before `solution pack`, deliberately rather than left to fail install ([federated-entity-pipeline-guide.md § The ontology resource does not ship](federated-entity-pipeline-guide.md)). A rerun re-checks that removal the same way it re-checks the bootstrap — a previous run's ontology resource still sitting in the solution is a finding, and the `--add-entity` declarations of a recreate are made against the local resource before it goes.

## Anti-patterns

1. **Deleting the artifacts to get a clean run.** The committed artifacts and the pack manifest are the identity map; without them every resolved question is asked again (§ The identity map).
2. **Reusing the previous discovery record.** The tenant changes with no file edit, so a rerun that skips phase 2 is checking last week's schema (§ The procedure step 2).
3. **Taking a removal at face value.** A vanished cell is a discovery finding until the model says otherwise (§ The three diff classes).
4. **Regenerating over a resolution comment.** It re-asks a question a person already answered, and the second answer is the pipeline's guess (§ The merge rule).
5. **Carrying the target mapping over a recreate unchanged.** Source order decides the collision rename, so unchanged columns can come back renamed (§ The procedure step 7).
6. **Renumbering ledger ids** so the new run reads cleanly, or editing a written row — including reintroducing a state cell so an exception can be closed in place. The ids are the only cross-run identity a person can cite, and a resolution is its own row (pipeline guide § The ledger).
7. **Deleting the entities that succeeded** in order to restart phase 5 from zero (§ Resuming a failed run).
8. **Claiming the entities exist because the files are under `resources/`** (§ Registration and packaging).
9. **Starting a rerun without re-hashing the inputs** against the previous manifest. An unchanged `.ofn` means every difference the run finds came from the tenant, which is the single most useful thing to know before reading a record (§ The procedure step 1).

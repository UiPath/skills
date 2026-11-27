# Federated Entity Pipeline Guide — a logical data model to Data Fabric federated entities

A genome whose Platform Dependencies name Data Fabric entities and that ships with a logical data model — an `.ofn` in OWL 2 QL functional syntax plus its SHACL constraints file — realizes that model as **federated** entities over Integration Service connections, then rewrites the mapping against them. Seven phases: ingest the model, discover what the external systems hold, establish the correspondence between the two, name and partition, emit the entity definitions, write the target mapping, check the set. Each phase owns one responsibility, hands off one artifact, and that artifact's shape is all the next phase may rely on. No phase starts before the phase it reads from has handed off. § Bootstrap runs before phase 1 and creates what every phase runs inside: the solution, the ontology resource and the connection resources.

The mapping language is **YARRRML**. **R2RML** names the data model it compiles to — `rr:class`, `rr:refObjectMap`, `rr:joinCondition`, logical tables: R2RML for what a construct *means*, YARRRML for what is *authored*. Never "YAML", never bare "RML", for either.

This is not `uipath-ontology`'s flow. That one starts from entities that already exist and writes an ontology over them, one logical object per physical table. Here the model comes first and the physical layer is discovered, and the one-table-one-entity assumption is false. The two flows share no step; do not mix them.

Six reads, each opened by the phase or condition that needs it:

| Read | When |
|---|---|
| this guide, whole | before the entity group is planned |
| [federated-artifact-shapes-guide.md](federated-artifact-shapes-guide.md) | by section, as each JSON artifact of the pack is written — the shape being written, not the whole file |
| [federated-source-mapping-guide.md](federated-source-mapping-guide.md) | phase 3 writes the source YARRRML |
| [federated-mapping-guide.md](federated-mapping-guide.md) | phase 6 — the entities exist and their columns can be read back |
| [federated-check-guide.md](federated-check-guide.md) | phase 7 — the target YARRRML is written; its § Four ERROR rules the run must clear, at phase 1 |
| [federated-rerun-guide.md](federated-rerun-guide.md) | **before phase 1**, when a `<MODEL_NAME>-ledger.json` already sits beside the `.ofn` |

The native lane is § The native lane — out of scope, and never mixed into the federated text above it.

## Principles

1. **The physical layer is discovered, never derived.** The `.ofn` and SHACL are the inputs. Which columns, keys and reference fields an external object has are facts about that system, not consequences of the model. Nothing downstream of phase 2 may be settled before phase 2 ran.
2. **Scope is artifact consistency, not runtime.** Three obligations: each artifact internally consistent; the artifacts consistent with each other; each consistent with the constraints its own syntax imposes. Runtime behaviour of the ontology service and of the Federated Query Engine is out of scope — flag a touch point in the ledger, do not design around it.
3. **Declared, observed and enforced are three different things.** The model declares, discovery observes, the platform enforces some subset. Record each separately and never collapse them: a declaration the source contradicts is a ledger exception, not a correction. The reconciliation of the three is a primary output of this lane, not a side effect ([federated-check-guide.md § Declared, observed, enforced](federated-check-guide.md)).
4. **Structural and enforcement facts, not OWL and SHACL.** Three SHACL facts are structural and none of them can move into the `.ofn`: `sh:datatype`, because a field must have a type and without one every field is `STRING` — **a different entity, not a weaker one**; `sh:maxCount` on an object property, the only thing separating a foldable spoke from a to-many target; `sh:in`, which in other lanes is a separate resource rather than a validation on a string. Everything else in SHACL tightens an existing field and is genuinely optional.
5. **An object-property axiom is not a join constraint.** `ObjectPropertyDomain` / `ObjectPropertyRange` are OWL entailment rules — they add types and are never violated. `sh:class` is a validation. Referential integrity is a closed-world guarantee of the source system, which a connector-backed object may not have at all, and a federated join is an execution instruction with a platform-imposed shape. **A range axiom fixes a join's endpoints, never its validity.** Reading one as a referential guarantee emits joins that are structurally legal and semantically wrong.
6. **Ambiguity is flagged, never guessed** (phase 3 § Stops). A wrong binding is invisible downstream: the mapping is syntactically valid, the entity is created, and the mistake surfaces as wrong data much later.
7. **Field types and entity topology are write-once.** Changing either means deleting the entity and creating it again, package deltas included. Both are settled before the first create call in phase 5; there is no in-place correction.
8. **The model is never edited here.** A contradicted datatype, an ignored value list, a missing `rdfs:comment`, a class too wide to fit the source budget: each is a report to the model's owner, never an edit to the `.ofn` or its SHACL file.
9. **Scope discipline.** Add no capability nobody asked for, and tighten no success condition beyond what the artifact contract requires.

## Artifacts

Every phase leaves one deliverable on disk, so which step lost which information is visible rather than argued. Together they are **the pack**, and the pack is machine-read: **no artifact here is surfaced to a person as it stands.** An agent or a deterministic parser walks it to find where a fault entered, and a user reporting an issue hands over the whole pack for the same walk. Human rendering is a separate concern and out of scope — no format in this set is kept because it reads nicely. Everything sits beside the `.ofn` except the solution resources, and everything is committed.

**The two names every artifact is keyed by.** Both are fixed at § Bootstrap and never re-derived by a later phase — a phase that recomputes either renames the artifact set mid-run.

| Name | Is | Derived from |
|---|---|---|
| `<MODEL_NAME>` | the artifact stem: every file of the set is `<MODEL_NAME>-*`, and the target mapping is `<MODEL_NAME>.yarrrml.yml` | the **last segment of the ontology IRI** (`https://ontology.uipath.com/<segment>#`) **verbatim, with no case transformation** — the same segment `prefixes: ont:` carries in both YARRRML files. A segment `fieldservice` stems every artifact on `fieldservice`, never `FieldService`. Never the `.ofn`'s file name: a model delivered as `schema.ofn` would stem every artifact on `schema`, and the file name is incidental to the model while the IRI is intrinsic to it |
| `<ONTOLOGY_NAME>` | the ontology resource's name in the solution — the argument `ont create`, `ont update` and `ont validate` all take | **the same segment, character for character.** XF-003 compares the schema IRI against `https://ontology.uipath.com/<ONTOLOGY_NAME>` as strings, so a name differing in one character — a PascalCased stem over a lowercase segment — fails the ontology and every artifact under it ([federated-check-guide.md § Four ERROR rules the run must clear](federated-check-guide.md)). It is not a choice, and a solution that already holds that name is an exception: renaming the ontology would require re-declaring the IRI, which is a model edit (§ Principles rule 8) |

| Artifact | File | Format | Phase | Carries uniquely | Cannot carry |
|---|---|---|---|---|---|
| pack manifest | `<MODEL_NAME>-pack.json` | JSON | rewritten by every phase | what the pack is: the run, the inputs it ran against, every artifact and its hash | its own hash |
| typed model | `<MODEL_NAME>-model.json` | JSON | 1 | classes, edges, cardinality, declared types, `:sourceOfRecord` | keys; to-one declared in OWL |
| discovery record | `<MODEL_NAME>-discovery.json` | JSON | 2 | real field types, declared primary keys, reference fields, the `enum` channel | uniqueness beyond the primary key; liveness; any nullable or length reading |
| source YARRRML | `<MODEL_NAME>-source.yarrrml` | YARRRML | 3 | class↔object and property↔field bindings, the subject key each block mints from | a class with no counterpart object; sources forming a chain; more than `MAX_SOURCES` objects for one class; a table with no declared key |
| partition manifest | `<MODEL_NAME>-partition.json` | JSON | 4 | the entity groups, their patterns and the entity names, and the to-one subgraph and class classification the cover was derived from | a name over 100 characters, or a reserved one such as `Order` or `Group` |
| entity bodies | `entities.json`, then `resources/solution_folder/entity/federated/<ENTITY_NAME>.json` | JSON | 5 | what was asked for, then what the platform built | the platform's own enrichment, until the two are diffed |
| target YARRRML | `<MODEL_NAME>.yarrrml.yml` | YARRRML | 6 | class → entity binding, and the collapse of several source blocks into one | — |
| check report | `<MODEL_NAME>-check.json` | JSON | 7 | every declared-versus-observed disagreement | — |
| ledger | `<MODEL_NAME>-ledger.json` | JSON | all | every decision taken alone, every exception a person must resolve, and every resolution | — |

**Every JSON artifact's field list is [federated-artifact-shapes-guide.md](federated-artifact-shapes-guide.md)**, by section, with a worked example from a real run; this table is what each one uniquely carries and what it cannot.

Two readings the set exists for: the **two YARRRML files are the same language over different sources**, so a diff between them is what changed when the model met the platform; and the gap between `entities.json` and the written resource file is what the platform added on its own (phase 5 § What the CLI adds).

**No pack file can be mis-attached as an ontology artifact.** `uip ont files add` resolves artifact type from the extension: `.ofn` is `schema`, `.ttl` is `constraints`, `.yarrrml.yml` / `.yml` / `.yaml` is `mapping`, and `.json` is ambiguous between `summary` and `context`, which the resolver refuses unless the name ends `-summary.json` or `-context.json` or `--type` is passed. So no `.json` of this pack resolves by accident — **and no pack file may ever take a `-summary` or `-context` suffix before its extension.** The source YARRRML is the one that needs care: it carries no `.yml` extension precisely so no resolver can claim it as the mapping ([federated-source-mapping-guide.md § What this file is, and what reads it](federated-source-mapping-guide.md)).

### Why the two YARRRML files stay YARRRML

**They are not converted to JSON, now or later.** The target is the mapping artifact **the platform itself consumes** — it takes the ontology's one `mapping` slot, `uip ont validate` runs the shipped cross-file rules over it, and the CLI's own YARRRML parser reads both files. They are therefore already machine-parseable, which is the whole of what the pack requires; rewriting either as JSON would break the thing it is for and leave the platform with no mapping. The source file stays in the same language for the reading § Artifacts names: the two are then one language over different sources, and the diff between them is the account of what changed when the model met the platform.

Neither file carries an `id` key and neither needs one (§ Ids).

### Ids

**Every record carries an id, and every record names the upstream ids it was derived from.** Linking by name breaks exactly when naming goes wrong, which is one of the faults the pack exists to find: a mis-derived entity name used to sever `entities.json` from the partition manifest silently. With ids, the same mistake is a wrong field on one record and a dangling reference the walk reports. **The walk is a graph traversal, never a string match on a name.**

An id is `<prefix>:<segment>[/<segment>…]`. It is **opaque**: nothing parses an id back into its parts, because every record also carries those parts as its own fields. Equality is the only operation.

| Record | Id | Minted at |
|---|---|---|
| class | `cls:<CLASS_LOCAL_NAME>` | 1 |
| data property | `dp:<PROPERTY_LOCAL_NAME>` — the local name as the predicate writes it, `<Class>.<prop>` | 1 |
| object property | `op:<PROPERTY_LOCAL_NAME>` | 1 |
| connection | `con:<CONNECTION_RESOURCE_NAME>` | 2 |
| source object | `obj:<CONNECTION_RESOURCE_NAME>/<OBJECT_NAME>` | 2 |
| discovered field | `fld:<CONNECTION_RESOURCE_NAME>/<OBJECT_NAME>/<FIELD_NAME>` | 2 |
| correspondence cell | `cell:<SOURCE_BLOCK_KEY>` — the source YARRRML block key, `<Class>__<Object>` | 3 |
| partition group | `grp:<ENTITY_NAME>` | 4 |
| entity | `ent:<ENTITY_NAME>` | 5 |
| mapping block | `blk:<TARGET_BLOCK_KEY>` — `<Class>`, or `<Class>__<Entity>` for a class with several blocks | 6 |
| ledger row | `D<n>` decision, `E<n>` exception, `R<n>` resolution | all |

Five rules on them:

1. **Derived from content, never from position.** No segment comes from a row number, an array index or the order a phase wrote. Reordering any file changes no id.
2. **Each segment is the thing's own identity in the layer that owns it**, verbatim and case-sensitive: the model's local names, which this lane never invents; the connector's object and field names, which discovery never invents; the entity name phase 4 derived and `create` adjudicated. A rerun that finds the same field in the same object on the same connection mints the same `fld:`, with no coordination between the runs.
3. **No hashes.** An id is emitted directly by the phase that mints it, with no library and no digest. The pack's only digests are the content hashes in the manifest, which hash files, not identities.
4. **An id changes only when the thing changed.** Two cases where it changes and the subject looks the same, both of which the lane already treats as a real change: a **connection renamed on the tenant** — the solution resource is re-added under the new name, so its `con:`, every `obj:` and every `fld:` under it take new ids and the rerun re-keys every reference as a decision ([federated-rerun-guide.md § The procedure](federated-rerun-guide.md) step 1); and an **entity renamed** — `grp:` and `ent:` both carry the entity name, so a rename reads as a removal plus an addition, which is what phase 4's "never silently rename" requires.
5. **Block keys are unique per file, so cell and mapping-block ids are too.** Where one class binds to same-named objects on two connections, the source block key — and with it the cell id — takes the connection resource name as a third segment, `<Class>__<Object>__<Connection>`.

**How the YARRRML files join the graph.** A block's key *is* its id — a source block keyed `ServiceWorkOrder__WorkOrder` is `cell:ServiceWorkOrder__WorkOrder`. And because every id is derived from content, a block that carries the content carries the ids: its `connection:` and `object:` mint the `con:` and `obj:`, each `$(<FIELD>)` mints an `fld:`, each `ont:<Class>.<prop>` predicate names a `dp:`, `[a, ont:<Class>]` names a `cls:`, and the target block's `table:` names an `ent:`. A walker resolves a block to its upstream records by minting the ids from what the block already says — no index, no lookup table and no name match.

### Who enforces a shape

**The guide declares; it does not enforce.** [federated-artifact-shapes-guide.md](federated-artifact-shapes-guide.md) is the contract: every field of every JSON artifact, its type, whether it is required. **This skill ships no schema file and no checker** — enforcement belongs to the `ont` tooling, which will own the schemas, and nothing shipped today reads a pack (§ Proposed tooling, not shipped). Do not propose a command surface for it, and do not add one to this skill. A run that wants the check writes its own throwaway script against that file, as any other check in this lane does. The division does not need re-litigating: **the guide is the contract, the `ont` tooling is the enforcer.**

**The shapes sit in their own file because this one is the procedure a run follows and they are schema reference consulted while writing an artifact** — and because enforcement is migrating to the `ont` command, so when real schemas ship that file shrinks to a pointer and this spine is untouched.

### The pack manifest

`<MODEL_NAME>-pack.json`. Without it the pack is a pile of files with no statement of what they are files of. **Every phase rewrites it** after writing its own artifact — it is the one artifact that is rewritten rather than appended, because the ledger's hash changes under every phase. It is not self-describing: it never lists itself and carries no hash of itself. Shape: [federated-artifact-shapes-guide.md § Shape — the pack manifest](federated-artifact-shapes-guide.md).

## The ledger

`<MODEL_NAME>-ledger.json`, beside the `.ofn` it belongs to. One append-only file, written by every phase: a flat `rows` array in write order. Three row kinds:

| `kind` | Written when | Carries |
|---|---|---|
| `decision` | the pipeline settled something on its own — a class bound to an object, a property bound to a field, a partition cut, a name derived | what it chose **and what it chose between** |
| `exception` | it cannot settle something — a declared type the source contradicts, a value list the source does not honour, a class with no counterpart object, a table with no unique column, sources forming a chain, a property whose field is ambiguous | what it blocks, and what a person must resolve |
| `resolution` | a person settled an exception | the `E<n>` it closes and what was decided |

Decisions accumulate. **An exception blocks what it feeds** until a person resolves it: the run writes the exception and stops short of that artifact, and continues on the classes the exception does not touch. A rerun appends; it never rewrites. Phase 7's reconciliation is a view over this file, not a second document.

**What a row is.** Shape: [federated-artifact-shapes-guide.md § Shape — a ledger row](federated-artifact-shapes-guide.md).

Six rules on it:

1. **Ids are never reused or renumbered**, across runs included. `D<n>` for a decision, `E<n>` for an exception, `R<n>` for a resolution.
2. **Append-only, with no exception. No row is ever edited or deleted, and no field of a written row ever changes.** An exception is closed by appending a `resolution` row whose `closes` names it. **There is no state field, and none may be added**: an exception is open while no resolution closes it and closed by the `R<n>` that does, computed from the file. A mutable cell in a machine-read log gives one cell two writers, and it erases the log's own history — which is what the pack is walked for.
3. **Every decision names what it chose between.** A decision with an empty `over` is not a decision, it is the only option — do not log it. The value of the ledger is the alternatives, because that is what a person needs to overrule it. **One exception, and it is rule 6's:** a touch point carries `over: []`, because there was no alternative for the pipeline to weigh. Its value is the fallback in `why`, not the alternatives. No other row may carry an empty `over`.
4. **An exception names what it blocks, not just the problem.** `blocks` is what does not get written, which is what makes the stop checkable.
5. **Every exception carries a recommendation.** Every stop in this lane computes before it asks (§ Anti-patterns 5), so `recommends` is what the pipeline would take if the person said nothing — and never what it did take. Where the run proceeded on the recommendation rather than waiting, the `D<n>` that did so names the `E<n>` in `why`, and the cost of a different answer — a delete and a recreate, a `po:` entry re-authored in both YARRRML files — belongs in `needs`.
6. **A touch point is a decision, not an exception, and it is rule 3's one exception.** Runtime behaviour this lane does not own — the `LeftJoin`, whether the service reads a `condition:`-less join as same-row — is recorded as a decision whose `why` carries the fallback and whose `over` is empty, and blocks nothing. So is a shipped check that rejects a correct artifact ([federated-check-guide.md § Three rejections to expect](federated-check-guide.md)).

## Bootstrap — the solution, the ontology, the connection resources

**Not a phase.** It reads nothing from the model and writes no artifact of § Artifacts but one: it **mints the `run` id and writes the first `<MODEL_NAME>-pack.json`**, carrying the run, the CLI version and the input hashes, so a run that dies at phase 1 still hands over a pack that says what it ran against. It exists because every phase below runs *inside* a solution that holds an ontology resource, and a run that starts from a bare `.ofn` has neither. Run it first. Its ledger rows carry `bootstrap` in `phase`, and only where there was an alternative to weigh — which of several connections a system's classes bind to, a connection renamed on the tenant since the last run. A name with one candidate is not a decision (§ The ledger rule 3); it lives in the artifact that uses it. Neither name of § Artifacts is a decision: both are the IRI segment verbatim.

1. **The solution.** Every `--local` command below resolves a solution root by walking upward for a `.uipx`; outside one they all fail with *"Not inside a solution"*. Create it, and run everything after this from inside it:

   ```bash
   uip solution init "<SOLUTION_NAME>"
   ```

2. **The ontology resource — local only.** `ont create` takes a name unique in the solution and creates the resource with no artifacts; `--entity` is repeatable but names entities that do not exist yet, so pass none here — phase 5 declares each entity as it is created:

   ```bash
   uip ont create <ONTOLOGY_NAME> --local
   ```

   The `.ofn` and the constraints `.ttl` are attached to it with `uip ont files add`, and the target mapping of phase 6 takes the one `mapping` slot (phase 1 § What an ontology may carry).

   **The resource exists for phase 7 and does not ship.** `ont create --local`, `ont files add` and `ont validate --local` are the whole of what it is for: they are the cross-file consistency check over the three artifacts, and without the ontology existing locally nothing in phase 7 runs. **The packed and deployed solution carries entity and connection resources only** — remove the ontology resource before `solution pack` (`uip ont delete <ONTOLOGY_NAME> --local --yes`), and record the removal as a decision taken over packing it and letting the install fail. The exclusion is deliberate, never a failure left to happen (§ The ontology resource does not ship).

3. **One connection resource per connection the run binds to.** This is what phase 3's `connection:` names and what phase 5's `connectionName` resolves against — [federated-source-mapping-guide.md § Block shape](federated-source-mapping-guide.md), phase 5 precondition 2. Add one per connection the genome's Platform Dependencies or the user names:

   ```bash
   uip solution resources add --source remote --kind Connection --name <CONNECTION_NAME>
   ```

   A connection phase 2 discovers that the bootstrap did not add is added at phase 2, before phase 3 writes a block naming it. Either way the resource exists before phase 3, and phase 3 names what already exists rather than announcing work for a later phase.

**`<CONNECTION_NAME>` is the tenant connection's own name, and cannot be aliased.** A remote add resolves the resource by searching the tenant for that kind and name, and records the name it matched; the create body matches `connectionName` against the connection resource's `resource.name`, and `uip solution resources edit --patch` merges into the resource's **spec**, which does not reach `resource.name`. So whatever the tenant calls the connection — an email address, a person's name, an environment string — lands verbatim in the connection resource's file name, in every entity resource file's `dependencies` list (phase 5 § What the CLI adds), in the packed zip, in the pack's `con:`, `obj:` and `fld:` ids (§ Ids), and in the deployed entity's `ExternalConnectionDetail.ConnectionName`. That is the platform's behaviour and the run neither strips it nor works around it.

## Phase 1 — Ingest

**Responsibility.** Parse the `.ofn` and the SHACL file into one typed model. **No shipped command parses either file** — there is no `.ofn` reader and no SHACL reader in the CLI (§ Proposed tooling, not shipped) — so the run parses both itself.

**Handoff.** The typed model, `<MODEL_NAME>-model.json` — committed, because every later walk reads the model from it rather than re-parsing OWL functional syntax. Shape: [federated-artifact-shapes-guide.md § Shape — the typed model](federated-artifact-shapes-guide.md). **Where the typed model and the `.ttl` disagree — which a hand edit to either can cause — the typed model wins**, and the disagreement is recorded as a decision. The committed artifact is complete, so no later phase re-parses the `.ttl` to settle it.

**Shape.**

| Level | Fields |
|---|---|
| per class | IRI, label, comment, every annotation, and **`:sourceOfRecord`** — the lane gate |
| per data property | IRI, domain class, the `DataPropertyRange` datatype where the `.ofn` carries one; from SHACL `sh:datatype`, `sh:minCount`, `sh:maxCount`, `sh:maxLength`, `sh:in` |
| per object property | IRI, domain, range; from SHACL `sh:minCount`, `sh:maxCount`, `sh:class` |

SHACL binds to classes through `sh:targetClass`.

**The four constructs the pipeline runs on.** An `.ofn` carrying these and nothing else is a sufficient input; every relational fact comes from phase 2, never from here.

| Construct | Role |
|---|---|
| `Declaration` | the vocabulary — read from the signature, not an axiom |
| `ObjectPropertyDomain` / `ObjectPropertyRange` | the edge graph: every reference and every junction |
| `DataPropertyDomain` | which class each field belongs to |
| `AnnotationAssertion` | labels, comments, `:sourceOfRecord` |

**`:sourceOfRecord` is the lane gate, per class.** A class whose `:sourceOfRecord` names UiPath belongs to the native lane and is not built here. A model whose classes name a mix of systems is **split by that annotation at phase 4, never forced into one lane**. A class carrying no `:sourceOfRecord` cannot be assigned a lane: write the exception, never a default. **An annotation naming a connection, an external object or a field is an input defect** — reported to the model's owner and not worked around, because the model may name a system and nothing narrower.

**Cross-check `DataPropertyRange` against `sh:datatype`.** A model may declare a datatype in both places, and a supplied model usually does. This lane **authors** no `DataPropertyRange` — every datatype it writes stays in SHACL — but it reads every one the `.ofn` carries into the typed model's `range`, and a disagreement with `datatype` is an exception at ingest, exactly as `sh:class` against `ObjectPropertyRange` is. A range the grammar skipped (`xsd:date` or `xsd:boolean` inside an axiom, § Stops) leaves `range` null and SHACL as the only declaration.

**Cross-check `sh:class` against `ObjectPropertyRange`.** They should name the same class for every object property, and the check is cheap. A disagreement is an exception at ingest — the two declare the same edge's far end and the correspondence phase reads the range to choose the object to join to.

**What an ontology may carry.** Exactly one `schema` artifact (`.ofn`) and exactly one `mapping` artifact (`.yarrrml.yml`, `.yml` or `.yaml`). Two consequences. The source YARRRML of phase 3 **cannot be attached as an ontology artifact** — the one mapping slot belongs to the target — so it lives in the solution as an ordinary file. And `constraints` is optional and inert: the ontology service retired SHACL, still accepts and stores a `.ttl`, and never parses or uses it. So this pipeline is the only consumer of SHACL, which is why every constraint has to be spent at generation time; nothing downstream will enforce one.

**Check the model's IRI before anything else.** The ontology IRI must sit under `https://ontology.uipath.com/`. A model declaring any other namespace is rejected at attach time by `OFN-001` (ERROR, `file-rules.ts`), and one failed rule attaches nothing — so the pipeline cannot lodge its own input and the run dies at phase 7 having done every other thing correctly. Check it at ingest, where the fix is cheap.

**Check the last segment and the declaration prefix with it.** Three more ERROR rules turn on what the `.ofn` says and are all decidable here: the IRI's last segment must equal `<ONTOLOGY_NAME>` character for character (XF-003), every term must be declared with the bare `:` prefix or nothing in the model parses as declared (XF-006, XF-014), and every data property's local name must be `<Class>.<property>` (OFN-002). Each is an input defect with the same remedy as the IRI — a report to the model's owner, never an edit ([federated-check-guide.md § Four ERROR rules the run must clear](federated-check-guide.md)).

This is an **input defect, not something to repair**: § Principles forbids editing the model, and rewriting an IRI silently rebases every term in it. Write the exception against the model, name the required namespace, and stop. The same holds for a `.ttl` whose shapes IRI sits elsewhere.

**Stops.** An ontology IRI outside `https://ontology.uipath.com/` stops the run, per above. Otherwise none — an axiom outside the accepted set is reported with its location and skipped, into the typed model's `skipped` list ([federated-artifact-shapes-guide.md § Shape — the typed model](federated-artifact-shapes-guide.md)), matching the behaviour of the `ont` tooling itself. The accepted set is the grammar that tooling reads, `owl2ql-ontop.ebnf` — **supplied with the model, not checked into either the skills or the CLI repository** — and it is **not** the W3C OWL 2 QL profile; read the grammar rather than assuming the profile. Four consequences bite later:

- **`HasKey` is rejected** — warned about and skipped. No key is declared in the `.ofn`, so every key in this lane comes from a source YARRRML subject template (phase 3 § Where the keys come from).
- **`FunctionalObjectProperty` and `InverseFunctionalObjectProperty` load but are inert.** `sh:maxCount` is the only to-one signal that works.
- **`xsd:date` and `xsd:boolean` are rejected only inside an OWL axiom.** The grammar's `builtInDatatype` production refuses them, so an `.ofn` `DataPropertyRange` naming either is skipped — and this lane authors no `DataPropertyRange`, because every datatype stays in SHACL. A data property carrying `sh:datatype xsd:date` or `xsd:boolean` is **not** an exception: the mapping carries the range as its third element like any other, and `DATE` and `BOOLEAN` are field types the create body can hold. Which one a column actually gets is the **connector's** declaration, never the model's (`CONNECTOR_TYPE_MAP` in `data-fabric-tool`, `src/utils/federated-payload.ts`, keys off the connector's declared field type) — and a connector that declares its date columns as `string` gets `STRING`, which is what happened on all three connectors run ([federated-check-guide.md § The vocabulary bridge](federated-check-guide.md)).
- **Never author either EXT rule.** `ObjectMinCardinality(1 P)` and nested existential fillers are accepted only behind hard-coded flags the tooling's own source marks temporary. One consequence is worth stating in full: nested existentials, which the W3C profile forbids, are **accepted** here, so nothing in the accepted set bounds graph depth. A partition rule that assumes depth ≤ 1 is leaning on the W3C profile rather than on what this tooling reads — the depth bound this lane actually has is `MAX_SOURCES` and the star rule, both checked at phases 3 and 4.

`ObjectSomeValuesFrom` in superclass position is legal and says *every Loan has an Account*, but it duplicates `sh:minCount 1`. One home per fact: leave it in SHACL. The highest-value future addition to the accepted set is `SubClassOf(C D)` with both classes named — the one addition that would change the relational decomposition — and it is the model owner's to request, not this lane's to author.

**No constraints file, or constraints written as prose.** `uipath-ontology` treats a constraints file as optional and routes required, range and value-list rules into `rdfs:comment` prose instead. That flow confirms a model with a person table by table; this one consumes SHACL at generation time. **Do not stop the run.** Degrade it, and record every degradation as a decision:

| Missing | What has no declared side | What the run does |
|---|---|---|
| `sh:datatype` | the mapping's third element, and the agreement rule | author every data property as a two-element pair, which R2RML reads as `xsd:string`, and log one decision per property. Where `rdfs:comment` names a range, put it to the model's owner as an `sh:datatype` to add — **never transcribe a prose range into a third element**: a range nobody declared is not a declaration |
| `sh:maxCount` on an object property | to-one, so nothing may fold | treat every object property as to-many. The partition degenerates to one entity per class, which is the conservative cover and always legal (phase 4) |
| `sh:in` | nothing | nothing — this lane emits no choice set either way (§ Out of scope, decided) |

Phase 7 then reports coverage rather than agreement, and says so in the verdict.

## Phase 2 — Source discovery

**Responsibility.** Find out what the external systems actually hold. Pure observation: it asks the model nothing.

**Handoff.** The discovery record, one entry per connection.

**Shape.** Per connection: connector key, connection id, the objects it exposes. Per object: its fields with their declared types, its **declared primary-key field**, the reference fields that point at other objects, and the one observation channel.

**One observation channel, not three.** `describe` projects a field as `name`, `type`, `displayName`, and, only where the connector declares them, `description`, `reference`, `enum`, `primaryKey`, `searchable`, `searchableOperators`, `searchableNames` — rendered with PascalCase keys (`Name`, `Type`, `PrimaryKey`, `SearchableOperators`, `Enum`), so match either casing. That list is the whole channel budget: **there is no nullable flag and no length anywhere in it**, on any connector, so `sh:minCount` and `sh:maxLength` have no observation channel at all and phase 7 reports both as coverage rather than agreement.

| Channel | Observes | Caveat |
|---|---|---|
| `enum` on the field | `sh:in` | present only where the connector declares a picklist. Observed on Salesforce; empty on Snowflake and Database Hub |
| `reference` on the field | the reference target, not a declared constraint | a projection key, not a guarantee: it was empty on every field of Salesforce, Snowflake and Database Hub, so treat an empty `Reference target` cell as *no connector declaration*, never as *no reference in the source* |

**Length survives only as description prose**, where a connector writes the real column type into `description` (limit 3 below) — never as a field of its own. A declared `sh:maxLength` checked against prose is a weaker reading than one checked against a channel, and the report says which it was.

**What discovery can and cannot see.** Three limits, all verified against the tooling rather than assumed.

1. **The metadata is catalog-served.** Discovery observes the connector's *declaration* of an object, not the live object: a field appearing in `describe` does not prove the live system has it, and a declared type is a second declaration rather than an observation. Treat a disagreement between it and the model as two declarations in conflict. **A `Failed` connection still answers, and answers partially** — observed: a `Failed` Salesforce connection listed 40 resources carrying neither `WorkOrder` nor `Asset`, where the `Enabled` connection on the same connector listed 1808. A partial schema is worse than none: it reads as success, and a class whose object is simply absent looks like a model that names an object the system does not have. Check the state before reading a resource list, and never diagnose a missing object before the connection is `Enabled`.
2. **Uniqueness beyond the primary key is invisible.** The resource summary carries no uniqueness flag, the payload builder throws on a missing primary key, and no field spec lets a column be nominated as the key. A table with no declared primary key therefore cannot be used, whatever uniqueness its columns really have.
3. **Type fidelity varies by connector, and some flatten it.** A connector may report every column as `string` or `number` while the real SQL type — `TIMESTAMP_NTZ`, `DATE`, `NUMBER(12,3)` — survives only in the field's description prose. Where that happens, transcribe the prose type beside the declared one and record which of the two the model was built on, because a declared model resting on prose is a weaker claim than one resting on a type.

Nothing here is reason to doubt a connector's field *names*; the limits are on types, keys and liveness.

**How.** Four commands, in order. The first is a gate, not a convenience:

```bash
uip df connectors list --output json
uip is connections list --all-folders --refresh --output json
uip is resources list <CONNECTOR_KEY> --connection-id <CONNECTION_ID> --output json
uip is resources describe <CONNECTOR_KEY> <OBJECT> --connection-id <CONNECTION_ID> --operation List --output json
```

`df connectors list` returns the tenant's allow-list of connectors usable as federated sources, backed by the `fqs-connectors-list` feature flag — an empty list means the flag is unset, not that nothing is supported. **A connector outside that list can never back a federated entity**, so describing its objects is wasted work and every class bound to it is dead before phase 5. Allow-list membership and connection state are independent: a connector can be allow-listed with every connection `Failed`, or `Enabled` with no allow-list entry at all. Require both.

Connection resolution, folder scope and connector keys are `uipath-platform`'s. All four commands only read — no artifact and no tenant object is written in this phase — but they authenticate against a tenant, so a run with no login fails here rather than later.

**`:sourceOfRecord` scopes which connections to describe.** The annotation is not only phase 4's lane gate: it is this phase's input. A tenant carries more connections than a model has systems — on an alpha tenant, over a hundred — so describing every allow-listed connection is both slow and a worse starting point for phase 3, which then proposes a correspondence across objects no class could plausibly bind to. Match each class's `:sourceOfRecord` against the connector behind each connection, describe the objects of the matching connections, and record the ones you skipped and why. Two consequences to write down rather than infer: a class whose `:sourceOfRecord` names a system with **no allow-listed connection** is dead before phase 5, so raise it here rather than at emission; and a class whose system has several connections is an ambiguity for phase 3 to resolve, not a reason to pick the first.

**The discovery record.** `<MODEL_NAME>-discovery.json`, beside the `.ofn`. Shape: [federated-artifact-shapes-guide.md § Shape — the discovery record](federated-artifact-shapes-guide.md). Ten rules on what goes in it:

1. **One field record per field** `describe` returns, including fields the model does not use. Phase 3 proposes a correspondence from the discovered names and cannot propose from a filtered list.
2. **The object's `primaryKey` is the whole of the key claim.** There is no per-field key or uniqueness flag anywhere in the record — uniqueness beyond the primary key is invisible (limit 2), so a field has nowhere to claim what the metadata does not support.
3. **`proseType` is filled only where the declared type was flattened** (limit 3). Null means the declared type stands, and `declaredType` and `proseType` are never both absent.
4. **`referenceTargetDeclared` is the object the field points at, as discovery reports it** — the object, never the class; `referenceTarget` is that string resolved to an `obj:` id. No connector declares a foreign key, and `reference` came back empty on every field of all three connectors run, so null means the connector exposes no reference, not that the source has none.
5. **`values` carries `enum`, verbatim and in order**, and is null everywhere the connector declares no picklist — which is everywhere outside Salesforce on the connectors run. It is the only declared-constraint channel there is.
6. **No `nullable` key and no `length` key.** Neither is in the `describe` projection, on any connector, so either would be null on every field and would read as *observed and unconstrained* rather than *not observable*. A declared `sh:minCount` or `sh:maxLength` is carried to phase 7 as a declaration with no observation, never as a disagreement. A width inside a `proseType` — `VARCHAR(32)` — is read from there, and is the only trace of a length there is.
7. **An object with no declared primary key is still written into the record**, with `primaryKey: null` and `stop` naming its exception, so a rerun does not describe it again to learn the same thing.
8. **`displayName` is recorded per field.** It is the one human-readable signal in the channel, and phase 3 settles real bindings on it — `InstallDate` over `CreatedDate` on the strength of *"Install Date"* — so a correspondence decision that cites it needs it in the record.
9. **A field list that is a subset says so.** Rule 1 is one record per field returned; a 120-field object cut to the model's own columns, a field family held back because it is personal data, and a dotted compound name such as `BillingAddress.street` — **which cannot be a flat federated column at all** — each go in the object's `excluded` list with its reason, against a `fieldsExposed` count of what `describe` returned. A filtered list with no such statement is indistinguishable from a thin object.
10. **The allow-list is recorded as the roster, not as a verdict.** `allowListedConnectors` carries every connector key `uip df connectors list` returned, so each connection's `allowListed` is checkable rather than asserted and a class that needs a different source is re-sourced against a list the run already has.

**Stops.** An object with **no declared primary key** is a hard stop for every class that would bind to it, not a warning: phase 3 cannot bind a class to it and phase 5 cannot emit it. Write the exception against the object and the classes that wanted it. A table whose uniqueness is real but undeclared stops the same way, because nothing in the metadata exposes it and nothing in the body accepts a nominated key. **Composite uniqueness is out of scope** either way.

## Phase 3 — Correspondence

**Responsibility.** Decide which class draws which properties from which discovered object. Nothing in the model names an external object and nothing in discovery names a class, so this is the one phase that cannot be made deterministic: propose from the discovered names, confirm with the user, then map property to field.

**Handoff.** The **source YARRRML** — the correspondence written down, one block per (class, object) pair where the class draws at least one property from that object. The matrix and the file are one artifact: a cell is a block. It is the only place the bindings, the subject keys and the reference fields exist, so nothing downstream reconstructs them. Syntax: [federated-source-mapping-guide.md](federated-source-mapping-guide.md).

**How many blocks.** `max(M, N) ≤ blocks ≤ M × min(N, MAX_SOURCES)`, for M classes and N distinct source objects. The floor holds because every class needs at least one block or it has no manifestation at all, and every object needs at least one or it is not part of the model. Once N exceeds `MAX_SOURCES` the ceiling becomes `M × MAX_SOURCES` and a class can no longer reach every object: the complete case stops being merely wide and becomes unrepresentable. The 1:1 diagonal other tooling assumes is the floor with M = N. A **sparse** matrix is what keeps the entity count tractable: as it fills, every entity becomes a wider join and the `MAX_SOURCES` budget is spent before any folding can happen.

**Shape.** Per cell: the class, connector key, connection id, source object name, and the property-to-field pairs with each field's **discovered** type, so phase 7 can check it against `sh:datatype`. Per class: which cell is the **primary** — the object every join starts at — and the key each cell reads to mint that class's subject.

**Four conditions, all checkable here.** Check all four before writing any cell:

1. At most `MAX_SOURCES` cells for one class (§ A class that needs more sources than fit).
2. Every non-primary cell joinable **directly** off the primary. A chain — a join off a spoke — is refused by the star check with *"Joins must form a star — every join's `source` must be the same primary source"*, a plain error carrying no code. `INVALID_JOIN` is a narrower thing and not this: it covers a join side naming an object that is not one of the entity's sources, and a join of a source to itself.
3. Every cell of a class yields the **same subject key**. Identical subjects are the only thing that makes several blocks describe one object instead of several. Which candidate objects can satisfy that is a decidable test, not a judgement — see § A class over several objects below.
4. The key column of every class folded into another class's entity appears among that entity's selected fields. A folded class still mints its own subject in the target mapping and has nothing to mint from otherwise.

**No key, no individual.** Every external table a class binds to carries a declared primary key. OWL 2 QL names an individual only by IRI, the subject IRI is minted from that column, and a relational row offers nothing else. That column does triple duty: it mints the subject, it is what the class's other cells must mint an identical subject from, and it is what the federated star joins on.

**Fields spanning several objects is the ordinary shape, not an edge case.** A federated entity takes one primary object and joins the rest, so a class may bind to several objects and carry one block per cell — all minting an identical subject. Two conditions bound it, and they are conditions 1 and 2 above. A class whose sources form a chain rather than a star is the case that does not fit.

### A class over several objects

Condition 3 says every cell mints the same subject key. **Which objects can be a cell follows from that, and the test is decidable.** The class has no declared key — `HasKey` is rejected, so nothing in the `.ofn` says what identifies an instance. Its key is the **primary cell's declared primary key**, fixed here, flowing upward from the physical layer.

A further object qualifies as a cell of the same class **only if its own declared primary key carries that same value**. It must be a 1:1 extension of the class, which makes the join primary-key to primary-key by construction. Three candidates that look workable and are not:

| Candidate | Why it fails |
|---|---|
| the shared column is **not** that object's primary key | the object permits many rows per key, so the cell mints one subject repeatedly and the entity stops having one row per key |
| a **parent** reached from the primary | its primary key identifies the parent, never the class, so no column in it can mint the class's subject at all |
| an object keyed on a different value space | the cells cannot agree on a subject, and reaching it needs a chain the star check refuses |

**The column names differ and that is expected.** `emp_details.id` and `emp_compensation.emp_id` are the same value under two spellings; each block's subject template reads **its own object's** primary-key column, and condition 3 is about the value, never the name. Do not look for one spelling across the cells.

**What no channel can verify.** That two primary-key columns share a value space is unobservable — no connector declares a foreign key, and the metadata carries nothing that relates one object's key to another's. Two GUID primary keys in one database is the strongest evidence available and it is still inference. So a multi-cell class is a **decision**, recorded with the evidence it rests on and what it was chosen over, never a fact the discovery record asserts. A class whose extension cannot be justified that way stands alone.

**The contrary direction needs none of this.** Several classes reading **one** object — different column subsets of the same table — requires no shared key at all, because each class mints from that object's primary key and they are different classes with different subjects. That case is unconstrained and is where most of a sparse matrix's second dimension comes from.

**An object property carries a second question.** A data property asks only which field holds the value. An object property asks that **and** whether the pair of fields can carry the join: a usable field on both sides, the related side's field being the key the related object is bound on, and the related object reachable directly off the primary. Usually yes — which is why the check gets skipped. When it is no, the axiom is still sound and the binding is still wrong, and that is a **different** exception from "which field is it".

### A class that needs more sources than fit

More than `MAX_SOURCES` objects for one class is an exception whose `Needs` cell names three options and what each costs. **Compute first, then ask** — a stop condition is not a procedure, and a user handed "this class is too wide" cannot answer it.

1. **Rank the cells** by how many of the class's properties each supplies, and name the cheapest — the cells whose removal costs the fewest properties, with the properties listed, not counted.
2. **Test a two-entity cover.** Partition the cells into two groups where each group is at most `MAX_SOURCES` cells, is a star off its own primary, and carries the class's subject key column. Report whether such a cover exists and what it is. A class legitimately has one block per entity, so two entities for one class is a supported shape rather than a workaround: the target mapping gives the class two blocks minting an identical subject.
3. **Put all three options**, each with its concrete consequence:

| Option | What it gives up | Who acts |
|---|---|---|
| drop the cheapest cells until the class fits | the properties those cells supplied, by name | the pipeline, on the answer |
| accept two entities for the class | nothing structural — one more entity, two blocks for the class, a second star inside the same budget | the pipeline, on the answer, when step 2 found a cover |
| split the class in the model | nothing here: the `.ofn` changes and the run re-ingests | the model's owner. This pipeline never edits the model (§ Principles rule 8) |

4. **Write the exception and stop short of the class's blocks.** The pipeline does not resolve it by taking the cheapest option.

**What wins on a hand edit.** The source YARRRML is committed and hand-editable. What it is authoritative for, and what it never carries, is [federated-source-mapping-guide.md § What this file is, and what reads it](federated-source-mapping-guide.md).

**Stops.** Write a ledger exception and stop short of the mapping that would rest on the guess when: two fields of the right type and neither name matches; a field that might be the reference and might be a label; a class two objects could serve; an object property whose field pair cannot carry the join. The exception names the property, the candidates weighed, and why none won. Never pick the better-looking candidate.

**Where the keys come from.** `HasKey` is rejected at ingest, so the key is not in the `.ofn`. Each source YARRRML block's subject template carries it, and this phase's per-cell subject key is what that template must say. Phase 7 checks the two against each other.

## Phase 4 — Naming and partition

**Responsibility.** Split the classes by lane, partition the federated side into entity groups, assign each group a pattern, and name every entity.

**Handoff.** The partition manifest.

**The lane split comes first.** Every class whose `:sourceOfRecord` names UiPath leaves the pipeline here, recorded in the manifest's native table so nothing downstream silently loses it. A mixed model is split, never forced. A class with no `:sourceOfRecord` was already an exception at ingest.

**The partition is a decision, not the identity.** One source object is not one entity, and one class is not one entity. Several classes fold into one entity when they draw on the same star; one class spreads across several blocks over one entity, or over two entities when phase 3's § A class that needs more sources than fit landed there. The bounds:

| Count | Floor | Ceiling |
|---|---|---|
| Entities | a star cover of the matrix | M, one per class |

M = classes. The block bound is phase 3's, where the blocks are authored.

### How to choose a partition

**Absent process context, fold maximally: emit the fewest entities the constraints allow, using Data Fabric's expressivity in full.** An external object gets its own entity only when something forces it, never because the model happened to name two classes. The procedure below is the method that chooses **within** § Forced to stand alone and the entity bound above, never around them.

**Why folding is the default and not a preference.** Every join this lane emits is an equality between two columns, which is exactly what a federated entity expresses natively. So where a relationship is expressible as a join, a separate entity buys nothing and costs a second query at read time. **Splitting is the thing that needs a reason; folding does not.**

Five of the seven dimensions are computable from the artifacts. The two that are not are process context, and they override the default where they are supplied rather than being asked for before it runs:

| Dimension | Discriminates | From |
|---|---|---|
| where the data lives | native vs federated | `:sourceOfRecord` |
| fan-out | a to-many edge can never be a baked spoke | `sh:maxCount` |
| envelope fit | at most `MAX_SOURCES` sources, a star off one primary | the correspondence matrix |
| closure | a group with an edge crossing its boundary is not closed — **does not bind here**: a crossing edge becomes a target-mapping join. Computed anyway, because it is what the composite decision later runs on | the matrix |
| relationship cycles | a cycle cannot be plain native relationships — **does not bind here**: no reference becomes a `RELATIONSHIP` field in this lane | the matrix |
| read vs write | federated is read-only | **process — override** |
| query shape | which objects are traversed together | **process — override** |

In order:

1. **Build the to-one subgraph**: every object property carrying `sh:maxCount 1`. To-many edges are excluded — they cannot fold, because a row would multiply, and they are a forcing condition at step 3.
2. **Classify every class on that subgraph** — **always-fact** (outgoing to-one edges only), **always-dimension** (incoming only), **isolated** (neither), **hybrid** (both). **Only hybrids are a real choice**; the other three are decided by their edges. Record the classification and its basis in the manifest, or the cover cannot be re-derived.
3. **Remove what is forced to stand alone**, each with its ledger reason: the target of a to-many object property; a class in a chain position, since a join off a spoke is refused by the star check; any class whose own cells already exhaust `MAX_SOURCES`.
4. **Cover the rest with stars, greedily, widest first.** A spoke may be absorbed into a hub's entity only when **all** of these hold:
   - the join is an equality on a usable field pair;
   - the related side's field is the key that object is bound on;
   - the related object is reachable **directly** off the primary, not through a third;
   - the resulting entity stays within `MAX_SOURCES` sources, counting the fact.
5. **Tie-break, so the result is reproducible.** When two hubs could absorb the same spoke, or two covers have equal cardinality: prefer the hub with more absorbable spokes; then the hub supplying more data properties; then the lexicographically smaller class IRI local name. **State which tie-break fired**, in the group's `tieBreak`.
6. **Record the cover in the ledger** as a decision per group, with the alternatives it was chosen over. A chain cut is one of them: a chain cannot collapse into one entity, so every path longer than one hop is cut somewhere, and where the model sees a path the platform sees a hub with spokes.
7. **Name each group** (§ Entity names).

**The procedure is greedy, not provably minimum** — a minimum star cover is set cover, and an exponential search is not worth the certainty. Greedy plus a stated tie-break is **deterministic**, which is the property that matters: the same input yields the same partition, so a difference in output means the pipeline changed rather than the agent's mind. **Do not describe the result as "minimum".**

**What process context overrides.** Where process context *is* supplied, it decides the hybrids and can override a fold: *read versus write* — a federated entity is virtual and read-only, so a class the process writes cannot be one, and when its `:sourceOfRecord` names an external system **and** the process writes it, neither lane serves it, so write the exception and name the conflict rather than picking a lane; and *query shape* — which objects the process traverses together. **A supplied context that splits a foldable star is a decision with its reason in the ledger, not an exception.**

**What reverse multiplicity cannot tell you.** `sh:maxCount` gives outbound to-one only and `InverseFunctionalObjectProperty` is inert, so **one-to-one and many-to-one are indistinguishable** from the artifacts, and nothing upstream supplies the missing half. Step 2 therefore classifies on edge *direction*, not on parent-side uniqueness: a class that reads as a dimension of two facts may be a fact in its own right. That is why a hybrid is the one real choice — and absent process context it is folded, not inferred into a role the artifacts cannot support.

**Forced to stand alone.** A group cannot absorb a class when any of these holds:

| Signal | Why |
|---|---|
| a to-many target — no `sh:maxCount` on the object property | the row would multiply, and the entity stops having one row per key |
| a chain position — the only join available is off a spoke | refused by the star check: every join's `source` must be the one primary |
| its own cells already exhaust `MAX_SOURCES` | nothing is left in the budget to join it into |
| independent consumption | **not derivable from the artifacts** — it is process context, so it fires only where that context was supplied; never infer it from the model |

Fan-out itself is not an R2RML problem: duplicated host rows repeat the same subject and the same triples, which is idempotent in RDF. The to-many exclusion rests on the Data Fabric constraint alone. Do not argue it from the mapping — that makes the rule look stronger than it is.

### Entity names

Derive, check, and never silently rename.

1. **Derive the stem from the group's primary cell's class** IRI local name: drop non-alphanumerics, keep the rest in PascalCase. The stem alone is the entity name only for a **one-class group** — there the entity *is* the class. Two cases take a suffix on the stem, because the name has to distinguish the entity from the class it was named after:

   | Group | Name | Why |
   |---|---|---|
   | one class | the stem — `PartReservation` | entity and class are the same thing |
   | several classes folded onto one star | the stem, unsuffixed — `Invoice` + `Vendor` → `Invoice` | folding is the default, so a suffix marking it would be on almost every entity; and the name must not move when the partition does |
   | one class over two entities (the two-entity cover of phase 3) | stem + a suffix naming what distinguishes each group | two groups cannot both take the stem, and the suffix is a decision carrying the other candidate in `Over` |

   The suffix is part of the derived name and goes through rule 2 with it.
2. **Check both command-imposed constraints**: 3–100 letters and digits starting with a letter (`INVALID_NAME`), and not reserved. **The reserved set is the command's own and is not reproducible here** — `Order` and `Group` are reserved SQL keywords (`NAME_RESERVED`), and the entire C# and VB keyword set is refused as well (`RESERVED_LANGUAGE_KEYWORDS`). Do not maintain a copy of the list: derive the name, let `create` adjudicate, and treat its rejection as the authority. A class named `Event` passes any naive check and still fails at create.
3. **A name failing either is an exception**, carrying the derived name, the constraint it broke and one proposed alternative for the user to confirm. Never rename silently: the entity name is what `table:` carries in the target mapping and what the genome's Data Fabric dependency row names, so a rename nobody saw is a rename nothing else follows.
4. **Naming owners split by layer.** Relational identifiers — object and field names — belong to discovery and are never invented. UiPath identifiers belong to this phase, and in this lane that is the **entity name only**: a federated entity's column names are derived by the CLI at create and read back at phase 6 ([federated-mapping-guide.md § Column names](federated-mapping-guide.md)), never chosen here. Table name and entity name stop being the same string the moment a group folds several objects into one entity.

### The partition manifest

`<MODEL_NAME>-partition.json`, beside the `.ofn`. Shape: [federated-artifact-shapes-guide.md § Shape — the partition manifest](federated-artifact-shapes-guide.md). Seven rules on it:

1. One record per group, and **every federated class appears in exactly one group**. A class in two groups is the two-entity cover of phase 3, written as two records naming the same class and flagged in `forcingSignal`.
2. `primaryCell` is the cell whose object every join starts at; a single-source group repeats its only cell there.
3. `forcingSignal` is null when nothing forced the boundary, and names the § Forced to stand alone signal otherwise, with the `op:` that forces it — so a rerun can tell a cut that was forced from a cut that was chosen.
4. `native` is the lane split's record. Omitting it is how a class disappears.
5. **`toOneSubgraph` and `classification` are the procedure's own inputs, written down.** Step 1 built the subgraph and step 2 classified every class on it; without both recorded the cover cannot be re-derived, and a deterministic partition nobody can re-derive is indistinguishable from a guess.
6. `tieBreak` names which tie-break of § How to choose a partition step 5 fired, and is null when none did. It is the reason the cover was taken, which reproducibility alone does not supply.
7. `expectedCollisions` lists the external field names appearing on more than one of the group's sources. It says where phase 6 will find a rename; **it never predicts the renamed column**, which is read back off the created entity ([federated-mapping-guide.md § Column names](federated-mapping-guide.md)).

### Stops

A group that exceeds `MAX_SOURCES`, or whose cells do not form a star off one primary, is an exception against the group and runs the procedure of phase 3 § A class that needs more sources than fit — never a group to split silently.

## Phase 5 — Entity emission

**Responsibility.** Create the Data Fabric entity definitions as **solution resources**. Nothing reaches a tenant.

**These resources and the connection resources of § Bootstrap are the whole of what the solution packs and deploys.** The ontology resource is removed before `solution pack`, so no artifact of phases 1, 3, 6 or 7 ships either (§ The ontology resource does not ship).

**Handoff.** `entities.json` — a collection of create-call bodies and nothing else — plus the entity resource files the CLI writes from it at `resources/solution_folder/entity/federated/<ENTITY_NAME>.json`. Never hand-write either resource file; drive them through the CLI.

**`entities.json`, and the invariant that earns it.** One entry per entity, carrying `id`, `name`, the `grp:` it was emitted for, and `body` exactly what `--body` takes. Shape: [federated-artifact-shapes-guide.md § Shape — entities.json](federated-artifact-shapes-guide.md). `body` passes through to `uip df entities create` **unchanged** — no enrichment, no reshaping, no keys of the pipeline's own, and no substitution of any key before the call; every pipeline key sits beside `body`, never inside it. `connectionName` carries the tenant connection's own name, whatever that name is (§ Bootstrap).

Rules on the body:

1. **Local bodies name connections; tenant bodies name ids.** Local: `connectionName`, `sourceConnectionName`, `relatedConnectionName`. Tenant: `connectionId`, `sourceConnectionId`, `relatedConnectionId`. The tenant lane, its allow-list gate and everything else `uip df entities` accepts are `uipath-platform`'s.
2. **A native source is `entityName` + `fields`** locally (`entityId` on a tenant), and a native side's connection name is its entity name.
3. **The primary is never declared.** It is derived as the source every join starts from. A single-source entity carries no `joins`; a multi-source entity gives **every** join the same `source`.
4. **The join type is hard-coded `LeftJoin`.** A NULL key generates no term, so the triple is skipped rather than minting a bogus IRI — spec-level, unverified against the service, so record it as a touch point rather than relying on it.
5. **Sources and joins are fixed at create, in this lane.** `update --local` is refused outright for a federated entity, so changing either means deleting the resource and creating it again ([federated-rerun-guide.md](federated-rerun-guide.md)). The tenant path is weaker — it accepts adding, removing and replacing sources, fields and joins — but this lane emits local resources, so treat topology as settled before the first create call, alongside the field types of § Principles rule 7. Do not state the local refusal as a platform-wide rule.
6. **No `RELATIONSHIP` fields.** A federated entity cannot be the target of one, so every reference stays a plain column for the mapping to join on.

**How.** Each entity is one create call, then one declaration, then validation:

```bash
uip df entities create <ENTITY_NAME> --local --body '<BODY>'
uip ont update <ONTOLOGY_NAME> --local --add-entity <ENTITY_NAME>
uip df entities validate <ENTITY_NAME> --local --output json
```

Three preconditions, each of which fails the create if unmet:

1. **A connector source requires a login.** The connector's field metadata comes from the tenant even though the resource is local, so `--local` does not mean offline here. **Field types are not the pipeline's to set** — the command reads them from the connection, and SHACL's types feed the reconciliation instead.
2. **Every `connectionName` must already be a connection resource of the solution.** § Bootstrap step 3 produces it and phase 3 names it; the create resolves the body's `connectionName` against the resource's own name, case-insensitively, and validate re-checks it. A name the solution does not hold fails with `CONNECTION_NOT_FOUND`, which lists the connections the solution does hold.
3. **The entity must be declared on the ontology.** `uip ont validate` fails any `table:` that is not one of the ontology's declared entities, so without `--add-entity` the cross-file check of phase 7 rejects every block the target mapping writes.

Validation is narrower than it looks: on a federated entity `uip df entities validate` checks that **each of its sources is a resource of the solution**. A federated entity has no project and nothing for `solution pack` to validate, so this is not the stub-and-resource pairing a native entity gets — do not claim more of it than that.

### What the CLI adds, and why the diff is the point

The resource file is not `entities.json`'s entry. The CLI fills in four things the body does not carry:

| Added | Read from | Recorded as |
|---|---|---|
| each field's type, as a SQL type | the connection, through the create body's `EntityFieldDataType` | `Fields[].SqlType.{Name,LengthLimit,DecimalPrecision}` ([federated-check-guide.md § The vocabulary bridge](federated-check-guide.md)) |
| each field's derived internal column name | the external field name ([federated-mapping-guide.md § Column names](federated-mapping-guide.md)) | `Fields[].Name` |
| the connection's local resource key, per source | the solution | each source's `ExternalConnectionDetail.ConnectionId` |
| `type: "federated"` | the command | the resource wrapper |
| the dependencies list | the sources | **`[{"kind":"Connection","name":"<CONNECTION_NAME>"}]` — by name, not by key.** A native source is `{"kind":"Entity","name":...}`. This is the second place the tenant connection's name lands verbatim (§ Bootstrap) |

**Diff the entry against the resource file, per entity, and record the delta as a decision** — but know what the diff can and cannot show. The resource file stores the entity as a **stringified single-line document** under `resource.spec.resourceJson`, so the two are not comparable by eye and a diff tool reports one changed line. Parse the string before comparing, and compare field by field; an unparsed diff shows that something changed and nothing about what.

Two losses to look for, both now confirmed on a live tenant rather than reported:

- **Every string column comes back `NVARCHAR(200)`, whatever `sh:maxLength` declared.** The length is hard-coded, not read from the connection or from the model — a `STRING` field is written with `LengthLimit: 200` and every other type with `LengthLimit: null`. A declared 40 and a declared 4000 land on the same column.
- **Decimal scale is reduced to the connector's declared type, not the column's.** A Snowflake `NUMBER(12,3)` whose connector declares the field as `number` lands on `DECIMAL` with `DecimalPrecision: 2`; a connector `integer` lands on precision 0. The real scale survives nowhere in the entity. Record the loss per column, with the prose type beside it where discovery captured one (phase 2, limit 3).

**Stops.**

- **A validate failure blocks the target mapping for every class in that entity.** Phase 6 reads column names off the created entity, and an entity that did not create has none.
- **Partial failure is not rolled back.** N entities are N calls: a failure on the k-th leaves the first k−1 resource files in the tree and their decisions in the ledger. Do not delete them and do not restart from zero — the resource files plus `entities.json` are what a resume reads ([federated-rerun-guide.md § Resuming a failed run](federated-rerun-guide.md)). Record the failed entity as an exception naming the create that failed.
- **Three structural-fact failures the model admits are possible.** Each blocks a different artifact, each is detected before phase 5, and none is a reason to emit a partial entity:

| Failure | Detected | Blocks |
|---|---|---|
| a data property with no `sh:datatype` | phase 1 | the third element of its `po:` pair, and the agreement rule for its cell |
| a class with no derivable key | phase 2 or 3 | every block and every entity of that class — fatal in this lane |
| an object property with a domain and no range | phase 1 | the join's far endpoint, so the join and any fold across it |

## Phase 6 — Target mapping

**Responsibility.** Rewrite the source YARRRML against the entities that now exist, as the target YARRRML.

**Handoff.** The target YARRRML — **one** file, because an ontology carries exactly one mapping artifact. Its syntax — block shape, subject identity, folded classes, join form, datatypes, column names — is [federated-mapping-guide.md](federated-mapping-guide.md).

**It cannot run beside phase 5.** The target mapping cannot use the source objects' field names: the CLI derives an internal column name at create, and a federated entity has one flat column namespace across every source, so a collision renames the later source's column. None of that is derivable from the model. **Read the column names back off the created entity** before writing a single block.

**Stops.** A column the matrix expects and the created entity does not carry is an exception against that entity, not a column to guess at.

## Phase 7 — Check

**Responsibility.** Validate the whole set and report every declared-versus-observed disagreement.

**Handoff.** `<MODEL_NAME>-check.json` (shape: [federated-artifact-shapes-guide.md § Shape — the check report](federated-artifact-shapes-guide.md)), and the final rewrite of `<MODEL_NAME>-pack.json`. The report's parts, the three shipped-checker rejections it must expect by name, the `xsd`-to-Data Fabric bridge, the agreement rule the run has to write and the reconciliation table are [federated-check-guide.md](federated-check-guide.md).

**Stops.** An exception still open in the ledger fails the report for the artifact it blocks. The report states which artifacts are clear and which are blocked, by exception.

## Hard constraints

Every row is statically checkable. Check them at the phase that can, not at emission.

| Constraint | Value / rule | Source of truth |
|---|---|---|
| `MAX_SOURCES` | 6 — counts the fact table **and** its dimensions | `MAX_FEDERATED_SOURCES` in `data-fabric-tool`, `src/utils/federated-payload.ts`, checked against `sources.length` |
| `MAX_DIMENSIONS` | `MAX_SOURCES - 1` = 5 — the join count | a star with N sources needs exactly N−1 joins |
| Topology | every join's `source` is the primary; every other source joined directly to it; one field pair per source pair | `validateFederatedTopology` |
| Source identity | each `(object, connection)` pair appears once, for connector sources; a native source carries no `object` and is skipped by the check | `validateFederatedTopology` |
| Blocks in the source YARRRML | `max(M, N) ≤ blocks ≤ M × min(N, MAX_SOURCES)` | M = classes, N = distinct source objects |
| Entities | floor a star cover; ceiling M, one per class | — |
| Key | a declared primary key per bound table; undeclared uniqueness and composite uniqueness both out of scope | OWL 2 QL names individuals only by IRI; `expandSource` throws on a missing primary key |
| Entity name | 3–100 letters and digits, starting with a letter | `INVALID_NAME` |
| Reserved names | the command's own set, not reproducible here: `Order` and `Group` plus every C# and VB keyword — let `create` adjudicate | `NAME_RESERVED`, `RESERVED_LANGUAGE_KEYWORDS` |
| Field types | write-once; a type change is a delete and recreate, package deltas included | confirmed by the domain owner |
| Entity topology | fixed at create **in this lane**: `update --local` is refused for a federated entity. The tenant path accepts source, field and join edits | `entities-inline.ts`; `expandFederatedUpdate` for the tenant path |
| Join type | hard-coded `LeftJoin` | `buildJoinConditions` |

## Out of scope, decided

Do not reintroduce these; each was ruled out on the merits.

1. **A choice set on a federated field.** Values arrive from the source and nothing enforces a list on a virtual column. `sh:in` stays in the declared model and feeds the ledger; no choice-set resource is emitted.
2. **`sh:minCount` enforcement.** A required flag on a column the platform never writes cannot be enforced. Recorded as declared, never pushed.
3. **Composite and case entities.** A composite is a **closed** star of relational tables — one isolated logical unit carrying no dependency or constraint against any table outside itself — and case is its only templatized exposure today, so the two are one pattern. It is out because the grouping decision needs process context no ontology artifact carries: whether a group of tables is better as one merged unit or several entities depends on how the process queries them. **This pipeline is its substrate, not a throwaway first step** — every composite is a merge of 1:1 units. One note for whoever opens the path: the closure rule is stated and enforced nowhere in the skills or CLI repos, where only the analogous `RELATIONSHIP_TARGET_FEDERATED` exists, so it has to come from the platform team rather than from the code.
4. **Composite uniqueness as a key** (phase 2 § Stops).
5. **The native lane** (§ The native lane).
6. **Packing or deploying the ontology resource.** It is created and validated locally and excluded from the pack (§ The ontology resource does not ship).

## The ontology resource does not ship

**Decided by the domain owner, on a live tenant.** The entity half of the solution packs, deploys and activates cleanly. The ontology resource fails install on rules that cannot all be satisfied at once, so it is **excluded from the pack deliberately**, never packed and left to fail. Five deploy attempts; the one that activated was the one with the ontology resource removed.

What that leaves, in each direction:

| Still done | Never done |
|---|---|
| `uip ont create --local`, `ont files add`, `ont validate --local` — phase 7's cross-file consistency check, and nothing in phase 7 runs without the ontology existing locally | packing or deploying the ontology resource. Remove it before `solution pack` (§ Bootstrap step 2) |
| authoring the target YARRRML (phase 6) — the class-to-entity record, the second half of the two-file diff, and what `ont validate` reads | shipping it. The one `mapping` slot is still the reason there is exactly one target file |
| the entity and connection resources | every artifact of the pack: the pack is committed beside the `.ofn`, not deployed |

**The install rules are a note about a lane this pipeline does not enter.** They are not constraints to satisfy, and no artifact here is shaped to clear them. They are recorded only so a run that meets them knows why, and knows the dead end is upstream. Four rules, the first three binding jointly:

1. every declared data property must be mapped;
2. the mapped datatype must equal the declared `DataPropertyRange`;
3. the compiler rewrites `xsd:nonNegativeInteger` to `xsd:integer`, then objects that the two differ;
4. the installer **refuses a relationship with no join keys** — `Relationship '<property>' has no join keys` — which makes the condition-less same-row form undeployable. It binds with nothing; it bites **only if that lane is ever entered**. Phase 7 keeps the condition-less block and does not reach for the self-join fallback precisely because this pipeline never enters it ([federated-check-guide.md § Three rejections to expect](federated-check-guide.md)). The two passages are one position, not two: should the ontology resource ever ship, this rule is what reopens that choice.

Worked example, from the run: a data property declaring `DataPropertyRange xsd:nonNegativeInteger`. Rule 1 forbids dropping it from the mapping; rule 2 forbids mapping it as anything but `xsd:nonNegativeInteger`; rule 3 rewrites that to `xsd:integer` and fails rule 2 against the declaration it just rewrote. No authored form clears all three, and the only remedy is a different declaration in the `.ofn` — a model edit, which this lane never makes (§ Principles rule 8). The same property stands in [federated-source-mapping-guide.md § Worked example](federated-source-mapping-guide.md), flagged there for what it is.

## Proposed tooling, not shipped

`uip ont` ships `artifacts check`, `create`, `delete`, `files add|list|remove`, `get`, `list`, `update` and `validate`. **`uip ont model plan` and `uip ont model emit` do not exist** — they are proposals. Do not invoke them and do not write a step that depends on them. Propose no new command surface either: this lane's tooling stays in the `ont` family, and what sits in this skill is the agentic layer that drives it.

## The native lane

**Out of scope here.** Native entity generation is a parallel effort over the same inputs — the same parse, the same classes, the same edges, and these same seven phases. Nothing in this section applies to a federated entity, and nothing above it applies to a native one. A phase's responsibility *widens* there rather than disappearing; four differences decide the rest:

1. **The physical layer is derived, not discovered.** There is no external system to observe, so phase 2 becomes a derivation from the model — junction tables and foreign-key columns included — and phase 3 stops being non-deterministic.
2. **A reference becomes a `RELATIONSHIP` field**, joined as `str1` in the mapping. A federated entity cannot be the target of one at all, so the same edge stays a plain column here and the join does the work.
3. **Keylessness is survivable.** A native entity mints its own `Id`, so phase 2's hard stop does not arise and the subject template is the `$(Id)` form. The same keyless class is fatal here and an annotation question there.
4. **SHACL configures fields there and reconciles declarations here.** The enforcement work is redirected, not reduced.

## Anti-patterns

1. **Guessing an ambiguous binding.** Picking the better-looking of two candidate fields, or the more plausible of two candidate objects, instead of writing the exception. The mapping validates, the entity creates, and the error surfaces as wrong data much later (§ Principles rule 6, phase 3 § Stops).
2. **Deriving the physical layer from the model.** Assuming an object has the fields, the key or the reference the ontology implies, and skipping or short-cutting phase 2. Column names, key columns and reference fields are facts about the source system, read from discovery and — after create — read back off the entity (§ Principles rule 1, phase 6).
3. **Treating a range axiom as referential integrity.** `ObjectPropertyRange` says what type the join's far end has, not that a matching row exists, and a connector-backed object may have no referential guarantee at all. A join emitted on the strength of a range axiom is structurally legal and semantically wrong (§ Principles rule 5).
4. **Conflating `MAX_SOURCES` with the dimension count.** `MAX_SOURCES` is 6 **including** the fact table, so a star holds at most 5 dimensions and 5 joins. Reading 6 as six dimensions emits a seven-source entity that `validateFederatedTopology` refuses.
5. **Raising a bare stop where a procedure exists.** "This class needs too many sources", "this group is over budget", "this name is reserved" are not answerable by a user on their own: each has a procedure that computes the options first (phase 3 § A class that needs more sources than fit, phase 4 § Entity names).
6. **Defaulting a class with no `:sourceOfRecord` into this lane**, or building a mixed model as if every class were federated (phase 1).
7. **Bounding graph depth on the W3C profile.** Nested existentials are accepted by the grammar this tooling reads, so the only depth bound is `MAX_SOURCES` and the star rule (phase 1 § Stops).
8. **Writing the target mapping from the source objects' field names.** The created entity's column names are derived and may be renamed on collision; a mapping written before they are read back is wrong in exactly the places a collision occurred ([federated-mapping-guide.md § Column names](federated-mapping-guide.md)).
9. **Correcting the model to match the source.** A contradicted datatype, an ignored value list, an unenforceable `sh:minCount`, an absent `rdfs:comment` are reconciliation rows and reports to the model's owner, not edits (§ Principles rules 3 and 8).
10. **Splitting an over-wide group silently**, or dropping a to-many class into a group to stay under `MAX_SOURCES` (phase 4 § Stops).
11. **Stopping the run because no constraints file shipped.** The run degrades and logs the degradation; it does not refuse to generate (phase 1 § No constraints file).
12. **Rerunning by deleting the artifacts and starting over.** The ledger, the pack manifest and the committed artifacts are the identity map; a cleaned tree is a first run that silently re-asks every resolved question ([federated-rerun-guide.md](federated-rerun-guide.md)).
13. **Converting either YARRRML file to JSON** to "finish the job". The target is the artifact the platform consumes and both are read by the shipped YARRRML parser, so both are already machine-parseable — which is all the pack requires (§ Why the two YARRRML files stay YARRRML).
14. **Mutating a ledger row**, or adding back a state field so an exception can be flipped to closed in place. A resolution is its own row naming the `E<n>` it closes (§ The ledger rule 2).
15. **Linking a record to an upstream one by name.** An entity whose only tie to its group is a matching entity name breaks exactly when naming goes wrong, which is one of the faults the pack exists to find (§ Ids).
16. **Handing over a pack whose manifest is stale**, or leaving the manifest unwritten because the run did not finish. Every phase rewrites it; a pack with no current manifest is a pile of files with no statement of what they are files of ([federated-artifact-shapes-guide.md § Shape — the pack manifest](federated-artifact-shapes-guide.md)).
17. **Shipping a schema file or a checker from this skill.** The guide is the contract and the `ont` tooling is the enforcer (§ Who enforces a shape).
18. **Splitting a foldable star for want of process context**, or putting the partition to the user before the default has run. Folding needs no reason and splitting does; absent that context the cover is computed, and a hybrid is folded rather than asked about (phase 4 § How to choose a partition).
19. **Calling the cover minimum.** It is greedy with a stated tie-break, which buys determinism and not optimality — and a run that claims optimality invites someone to go looking for the exponential search (phase 4 § How to choose a partition).

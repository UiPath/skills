# Data Model Guide — ontology bundle to Data Fabric entities

Router for the data-model extension of Author mode. An **ontology bundle** — an OWL
ontology, an R2RML mapping and SHACL shapes — describes the business world as data.
This extension turns it into a Data Fabric entity set that ships inside the
solution, plus a record of every decision taken and every one deferred.

This file routes. Each subject is stated in full in exactly one guide below.

## When this engages

Author mode, when the request supplies an ontology bundle alongside (or instead of)
a prose description. Detection: [ontology-sources-guide.md § Detection](ontology-sources-guide.md).

Without a bundle, the genome's `## Data Model` section carries its stub line and
nothing here is read.

A bundle **never replaces the process description**. It says what the data is; the
genome still says what the automation does. A bundle with no described process
produces a data model and a genome whose Workflow is `*[Inferred]*` — say so.

## Discovery — which guide, when

**[SKILL.md § Read Plans](../SKILL.md) is the one routing table**, for this extension
as for every other. It names each guide below with the condition that opens it. Do
not keep a second copy here; the two drift, and the plan is what an agent reads.

One standing boundary it cannot express: **any Data Fabric field type, choice-set
mechanic, federated rule or relationship binding belongs to `uipath-platform` →
`references/data-fabric/`** — named here, never restated. When that skill is not
installed the deterministic tools still run, because they encode the field-shape
rules they need; the run then says which guidance it could not consult.

## Artifacts

```
  INPUT                                          DELIVERABLES
  ontology (.ofn) ─┐
  SHACL shapes ────┼──▶ inventory ──┐
  source.r2rml ────┘                ├──▶ entities.json
        │                           │
        └──▶ target.r2rml ──────────┘    target.r2rml
                   ▲                     process-resolved.md
  process.md ──▶ process-resolved.md ─┘        │
    (raw)                                      ▼
                                   a coding agent authors the
                                   local entities and packs the
                                   solution from entities.json
```

**Four inputs, three deliverables.** The user supplies the three ontology artifacts
and a **raw** prose process description. Everything else is written by this
extension.

| Artifact | Written by | Mutable | Means |
|---|---|---|---|
| `<name>.ofn` | the user | no | the business world |
| SHACL shapes | the user | no | what is true of the business world |
| `source.r2rml` | the user | **no** | how the source realizes the ontology — executable against the source |
| `process.md` | the user | no | the process in the business's own words |
| `<bundle>-inventory.json` | `ontology-inspect.py` | derived | the parsed, normalized reading of the three inputs |
| **`process-resolved.md`** | **this extension** | yes — must stay resolvable against `target.r2rml` | the process named against the mapping's tables ([process-resolution-guide.md](process-resolution-guide.md)) |
| `access-patterns.json` | `resolve-process.py` | derived | who writes what, what a branch turns on, what is read together |
| **`target.r2rml`** | this extension | yes, from Phase 2 on | the relational design **and the entity identities** the entity set derives from |
| **`entities.json`** | `derive-entities.py` | derived | the entity set, register and provenance |

Solution resources are **not** part of this flow. `entities.json` is the final
deliverable: its entity and field objects are shaped to be handed to `uip df` by a
downstream coding agent ([datafabric-emission-guide.md](datafabric-emission-guide.md)).

**Copy `source.r2rml` to `target.r2rml` before any derivation, and do not write
`target.r2rml` again in Author mode.** The two files are byte-identical when Author
mode ends. Everything downstream derives from `target.r2rml`, so later phases revise
one file and the diff against `source.r2rml` is the whole normalization decision
record — machine-readable, replayable, and reviewable as a diff rather than as a
model someone must re-derive.

Keeping `source.r2rml` immutable preserves the one artifact that can still be checked
against reality: it is the only document that remains executable against the source
database. A single mutable mapping drifts from "how the source realizes the ontology"
to "the relational design for Data Fabric" with no marker saying when it crossed over.

## The inventory is the contract

Run the inspector once; derive everything from its output. Do not re-read the `.ofn`,
the R2RML or the SHACL files during derivation.

```bash
python3 "<SKILL_DIR>/scripts/ontology-inspect.py" \
  --ontology "<ONTOLOGY_FILE>" --r2rml "<R2RML_FILE>" --shacl "<SHACL_FILE>" \
  --out "<BUNDLE_SLUG>-inventory.json"
```

Why the inventory rather than the sources, and what it contains:
[ontology-sources-guide.md § The inspector](ontology-sources-guide.md).

## Three schemas, three completeness assumptions

Two pieces of standing theory decide most of the junctures below. Both are worth
knowing before writing anything.

### The three-schema architecture

The pipeline is the ANSI/SPARC three-level architecture, and the artifacts line up
one-to-one:

| ANSI/SPARC level | Here | Locked |
|---|---|---|
| Conceptual — the community view: entities, attributes, relationships | the ontology | **input; never written by us** |
| Internal — how data is actually stored | the Data Fabric entity set | derived, revisable until first binding |
| External — the views each user of the data needs | the automation's access patterns | discovered last, in Phase 2 |

The architecture's claim is that **explicit mappings between levels are what deliver
independence** — conceptual↔internal changes do not ripple outward. That is exactly
why `source.r2rml` and `target.r2rml` are two documents. Collapsing them into one
mutable file destroys the only mapping that still ties the internal level back to
something checkable.

Practical consequence: **never let an internal-level concern edit the conceptual
level.** A Data Fabric limit is not a reason to change the ontology. It is a reason
for a register row.

### Three completeness assumptions in a row

OWL makes the **open-world assumption**: what is not stated is unknown, not false.
SHACL validates under the **closed-world assumption**: it treats the graph as
complete, which is why `sh:minCount 1` can fail at all. Those are different worlds,
and the mismatch is a known, actively researched problem.

Our pipeline adds a **third**: a Data Fabric entity at a point in time, which during
incremental ingestion is *not* complete — a record may legitimately exist with a
field the domain considers mandatory still unfilled.

So a constraint crosses two gaps before it can become `isRequired`:

```
OWL cardinality  ──OWA→CWA──▶  SHACL sh:minCount  ──CWA→store──▶  isRequired
   "unknown is                  "complete graph                     "complete at
    not false"                   must satisfy"                       write time"
```

`sh:minCount 1` already encodes the first crossing. **The second is ours, and nothing
in the inputs carries it** — it depends on whether this store is a system of record
or a staging buffer, and on whether records are written whole or completed over time.
That is the formal statement of "mandatory in the business world ≠ must be enforced
here", and it is why the register separates `expressible`, `locus` and `level`
([constraint-register-guide.md](constraint-register-guide.md)).

Sources: [SHACL validation in the presence of ontologies](https://arxiv.org/abs/2507.12286) ·
[Open world / closed world](https://ontologist.substack.com/p/the-open-worldclosed-world-conundrum) ·
[ANSI-SPARC three-level architecture](https://www.geeksforgeeks.org/dbms/the-three-level-ansi-sparc-architecture/)

## Authoring order

Strictly sequential. Each step's output is the next step's input, and several steps
lock a decision that later steps cannot revisit cheaply (§ Commitment ladder).

| # | Step | Produces | Locks |
|---|---|---|---|
| 1 | Detect the bundle; copy `source.r2rml` → `target.r2rml` | the baseline | the diff baseline for every later phase |
| 2 | Run `ontology-inspect.py` | `<slug>-inventory.json` | the reading of the three inputs |
| 2a | **Resolve the raw process description into the mapping's table vocabulary; run `resolve-process.py`** | `process-resolved.md`, `access-patterns.json` | **which entities this solution owns, and where each constraint is enforced** ([process-resolution-guide.md](process-resolution-guide.md)) |
| 3 | Declare the four defaults for whatever 2a left open; take named overrides | the override list | the remaining category-3 answers |
| 4 | Fix the naming convention | — | **every entity and field name** |
| 5 | Run `derive-entities.py` | `entities.json` | entity identity, junctions, components, `numberId`s |
| 6 | Classify every SHACL shape | the register | `expressible`; `locus` by default |
| 7 | Run the gates on the three deliverables | pass/fail | — |
| 8 | Write `## Data Model`, Platform Dependencies rows, transition-level Business Rules and their criteria | the genome | the contract |
| 9 | Work the checklist; report | — | — |

**Do not reorder 4 before 3** — an override can rename an entity. **Do not reorder 6
before 5** — a register row's `subject` names an entity and field that step 5 mints.

A Phase 2 revision re-enters at step 1: edit `target.r2rml`, then re-run 2, 2a and 5
in that order. Skipping the re-resolution at 2a loses access-pattern rows silently
([process-resolution-guide.md § Re-resolving after a revision](process-resolution-guide.md)).

## Commitment ladder

What locks when, and what it costs to revisit. This is the table to consult before
deferring anything "until we know more".

| Decision | Locked at | Why there | Cost of revisiting later |
|---|---|---|---|
| The ontology itself | never by us | conceptual level; it is the input | out of scope — a change to the business model |
| Naming convention | step 4, before the first name | every name, register row and binding keys on it | rename cascade through every workflow binding |
| Entity identity — what is one entity | step 5 (Author) | provenance, component ids and every register row key on it | full re-derivation |
| Junction vs reified class | step 5 (Author) | forced by the ontology's own shape, not by consumption | changes the entity set |
| Component partition | step 5 (Author) | a deterministic function of the relationship graph | recomputed free, but island decisions made inside one move |
| `numberId` per choice value | step 5, first emission | **immutable once deployed** | silently remaps deployed records — unrecoverable |
| Tenant vs folder scope | step 5, before `entities.json` is written | every consumer reads it off the deliverable | regenerate `entities.json` |
| `locus` — who enforces | step 6 by default; Phase 2 on evidence | **multi-phase by design** | a register edit; cheap |
| `level` — state / transition / monitor / assumed | Phase 2 | needs the write sites | may add or remove field options; moderate |
| Normalization degree | Phase 2a, refined 2b | **multi-phase by design** | free until the first binding, then a rework of bindings |
| Federated views | Phase 2b | needs a cost model over access patterns | additive; cheap |

**Three of these are one-way doors**: the naming convention, entity identity, and
`numberId`. Everything else is revisable, and two are *designed* to be revisited
across phases rather than settled early. Say which is which when reporting
(§ Closing the run) — a reader who cannot tell a locked decision from a parked one
will either re-litigate the first or trust the second.

## Determinism

**The entity set is a deterministic function of `(inventory, overrides, previous, project, scope)`.**
Same inputs, same `entities.json`, byte for byte. The tools enforce it: sorted keys,
stable ordering, no timestamps, no generated ids that vary between runs.

This is the property that makes everything later reviewable as a diff. Protect it:
anything that would make a second run differ belongs outside the tools.

Check it:

```bash
python3 "<SKILL_DIR>/scripts/derive-entities.py" --inventory "<INV>" \
  --project "<P>" --overrides "<OVR>" --previous "<PRIOR>" --out /tmp/a.json
python3 "<SKILL_DIR>/scripts/derive-entities.py" --inventory "<INV>" \
  --project "<P>" --overrides "<OVR>" --previous "<PRIOR>" --out /tmp/b.json
diff /tmp/a.json /tmp/b.json
```

## What Author mode decides, and what it does not

Author mode emits **only what the inputs and the platform force**. Anything a
consumption pattern would justify is deferred, because Author mode has no consumption
pattern — the genome's Workflow is being written in the same run, and no automation
exists yet.

| Emitted in Author mode | Deferred |
|---|---|
| `direct` entities and fields | `consolidation` — several classes folded into one entity |
| `junction` entities for many-to-many | `decomposition` — one class split for lifecycle or access |
| — | `federated-view` — a read entity over native entities |
| field options for `expressible: yes` constraints | the `level` axis of every register row |
| `locus` by declared default | `locus` where the default was overridden on evidence |

The deferred set is not a gap; it is the contract with the later phases. Every
deferred item is a register row with `resolution: deferred`, so the next phase has a
worklist rather than a re-derivation.

## Boundaries

1. **Nothing is written to a tenant.** No `uip df` command without `--local`, no
   `choice-sets create`, no records. Everything the target environment needs goes to
   the open items, as every other platform resource does
   ([open-items-guide.md](open-items-guide.md)).
2. **The genome stays the contract.** The `## Data Model` section is written once by
   Author mode and is read-only afterwards, like every other section
   (the genome is read-only during execution — [execution-guide.md](execution-guide.md)).
3. **The Data Fabric surface is `uipath-platform`'s.** Name capabilities; route for
   detail. A field type, a choice-set mechanic or a relationship binding rule that is
   restated here will drift.
4. **No reasoning over the ontology.** No classification, no inference closure, no
   materialising of `owl:equivalentClass`. The inspector reads asserted axioms only,
   and says so.

## Validation gates

The gates this flow runs are over the three deliverables, not over a solution:
inventory parsed, graph sound (no cycle, every relationship target present),
determinism (two derivations byte-identical), `process-resolved.md` resolvable
against `target.r2rml`, and the genome checks. Every one blocks offering edits.

The schema and pack gates belong to the downstream run that authors the local
entities, and are stated with it
([datafabric-emission-guide.md § Validation gates](datafabric-emission-guide.md)).

## Closing the run

Before offering edits ([genome-format-guide.md § Write, Then Offer Edits](genome-format-guide.md)),
work § Closing checks, then tell the user, in this order:

1. what was emitted — entities, fields, junctions, choice sets, by count and by
   component;
2. the four defaults that were applied, and how to override each — and whether the
   bundle declared any enforcement of its own
   ([constraint-register-guide.md](constraint-register-guide.md));
3. the deferred set, by category, with what would resolve it;
4. the complex tier a downstream run has to create on the tenant — relationship and choice-set fields;
5. anything in `notCovered` and every `parserNotes` line, with why;
6. the gates that passed.

A run that emitted a model and listed no deferred decisions has almost certainly
guessed at something. Check the register before reporting it.

## Closing checks

Work these before offering edits. Each names the guide that states its rule.

| # | Check | Rule |
|---|---|---|
| 1 | `source.r2rml` was copied to `target.r2rml` and never written again | § Artifacts |
| 2 | the inventory was the only reading of the three inputs | § The inventory is the contract |
| 3 | every class is in a `from[]` or in `notCovered`, and the index runs both ways | [entity-derivation-guide.md § Coverage](entity-derivation-guide.md) |
| 4 | no `consolidation`, `decomposition` or `federated-view` was emitted | § What Author mode decides |
| 5 | every non-`direct` derivation carries a `because` | [entity-derivation-guide.md § Provenance](entity-derivation-guide.md) |
| 6 | every rename and every applied default has a register row | [constraint-register-guide.md § The register row](constraint-register-guide.md) |
| 7 | no `source: process` row carries a `level` | [constraint-register-guide.md § What Author mode may not decide](constraint-register-guide.md) |
| 8 | `isRequired` was never set from `sh:minCount` alone | [constraint-register-guide.md § The isRequired trap](constraint-register-guide.md) |
| 9 | two derivation runs are byte-identical | § Determinism |
| 10 | `process-resolved.md` still resolves against `target.r2rml` | [process-resolution-guide.md § Re-resolving after a revision](process-resolution-guide.md) |
| 11 | every relationship and choice-set field in `entities.json` is marked for the downstream run, and every `via` step is flagged blocked | [datafabric-emission-guide.md § The two tiers](datafabric-emission-guide.md) |
| 12 | nothing was written to a tenant | § Boundaries |

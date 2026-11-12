# Normalization Guide — how far to decompose, and when to decide

Rules. What Author mode emits (the normalized form the dependencies dictate), what
it may not decide, and the protocol by which later phases revise it.

Read whole when the inventory reports ≥2 classes with an object property between
them. Router: [data-model-guide.md](data-model-guide.md).

## The decision splits in two

**Normalization toward BCNF is deterministic**, not a judgement. Decomposition is an
algorithm over a functional-dependency set, and a real part of that set is already in
the inputs:

| Signal | Gives |
|---|---|
| `owl:FunctionalProperty`, `sh:maxCount 1` | X determines Y |
| `owl:hasKey`, `owl:InverseFunctionalProperty` | candidate keys |
| R2RML logical tables and join conditions | the source designer's own FD understanding |

**The stopping point is the judgement.** Denormalization is the non-deterministic
half, and it is what the phases are about.

Independent support for starting normalized: the mapping literature observes that a
normalized relational schema is structurally closer to the ontology, which is what
makes the correspondence direct and auditable
([Generating relational databases from ontologies — review](https://www.researchgate.net/publication/326088759_Generating_Relational_Database_using_Ontology_Review_Issues_Challenges_and_trends)).

## Conservative means normalized

**Author mode emits the FD-dictated normalized form. Nothing is denormalized without
evidence, and Author mode has no evidence.**

The asymmetry is informational, not operational: a denormalized view is always
derivable from a normalized model, but a normalized model is not reliably recoverable
from a denormalized one — recovering it means re-deriving FDs from data that may
already have lost them. Starting normalized keeps every later option open; starting
folded closes some permanently.

It also gives the iteration a property worth having: Author mode's deterministic
output **is** the baseline, so every later change is a diff against a reproducible
starting point. A reviewer reads "these three merges, with this evidence" instead of
re-deriving the model to check it.

## The unit of work is a component

Entities as vertices, `RELATIONSHIP` fields as edges: the **weakly connected
components** of that graph are independent normalization problems.

Two entities in different components have **no join path**, so they share no hop cost
and cannot be folded into each other. There is no interaction term to miss — a hard
separation, not a heuristic. Weakly connected rather than strongly, because a fold
can go either way along an edge regardless of which side holds the foreign key.

Inside a component, merges happen only **along an edge**, so a merge perturbs its
neighbourhood rather than the whole component.

Consequences:

1. The derivation assigns every entity a `component` id, stable across runs.
2. A later phase may revise one component without reopening any other.
3. A component is the unit the binding deadline applies to (§ Revision has a
   deadline).
4. Report counts per component, not only in total — a 60-entity model in 18
   components is a very different review from one in 2.

## Platform limits prune first

Data Fabric carries a standing bias against normalization that exists before anyone
mentions a domain or a workflow. These are **hard constraints, not preferences**, and
they narrow the space before any judgement is applied.

1. **No query-time join between native entities.** To filter a child by a parent's
   attribute, resolve the parent's UUID first, then filter the child — two round
   trips, per hop, per query.
2. **The only join mechanism is a federated entity**, which is read-only, an
   **undirected** star (N sources → N−1 joins, every non-primary joined directly to
   the primary, no chaining, one field pair per source pair, matching types), and
   silently ignores `aggregates` / `groupBy`. The primary is a free choice, and a
   join is symmetric, so which side holds the foreign key does not matter — see
   § The feasibility envelope for what this does and does not forbid.
3. **No composite uniqueness** — `isUnique` is per field. A junction therefore cannot
   enforce pair-uniqueness: the decomposition is paid for and the constraint that
   motivated it is still lost ([entity-derivation-guide.md § Junctions](entity-derivation-guide.md)).
4. **`RELATIONSHIP` is single-valued child→parent with no reverse field**, so
   traversal is one-directional.

Detail on all four belongs to `uipath-platform` → `references/data-fabric/`; what is
stated here is only their consequence for how far to decompose.

Limit 1 is stated by the platform, not inferred: a `RELATIONSHIP` field's stored,
returned and filterable value is the target's UUID, and filtering a child by a
parent's attribute is documented as resolve-the-parent-first then filter-the-child
(`uipath-platform` → `references/data-fabric/records-query.md`). So the two
directions cost differently, and the difference decides which argument applies:

| Direction | Example | Cost over a chain of N hops |
|---|---|---|
| **traversal** — hold a record, want an ancestor's value | an invoice, want its supplier's country | N reads |
| **filter** — want the records whose ancestor matches | every invoice from a DE supplier | N queries, each materializing a UUID set the next one passes as an `in` list |

The filter direction is the expensive one, and it is the one a reporting surface
needs — which is exactly why a federated entity is wanted there, and why what the
envelope says about feasibility matters.

### Materialize or virtualize

Native entity = materialization. Federated entity = virtualization. This is the
standing trade in ontology-based data access, and the literature's finding is that
neither wins outright — practical systems hybridize, using a cost model over the
actual query load to decide which views to materialize
([OBDA: query rewriting or materialization? In practice, both!](https://link.springer.com/chapter/10.1007/978-3-319-11964-9_34)).

The axis is **sync cost versus query coverage**: virtualization avoids duplication and
staleness but cannot serve every query; materialization serves everything and owes
synchronization.

The operative consequence for us: **a cost model needs a query load, and Author mode
has none.** That is the whole reason federated views are a Phase 2 decision rather
than something the ontology could imply.

## Priority

The three contexts are not peers.

```
platform  ──prunes──▶  domain  ──shapes──▶  process  ──tunes──▶  the model
 (hard; no appeal)    (what IS an entity)   (how far to collapse)
```

- A **process** convenience never overrides a **platform** constraint.
- A **process** convenience never silently overrides a **domain** boundary; it may
  override it with a recorded reason.
- A **platform** limit never edits the **ontology** — the conceptual level is an
  input ([data-model-guide.md § Three schemas](data-model-guide.md)).

## What Author mode may not decide

| Not decided here | Needs |
|---|---|
| **to fold** several classes into one entity | a read pattern showing they are always fetched together, and no write that separates them |
| **to split** one class across entities | a lifecycle, scope or access difference |
| a `federated-view` | a query pattern recurring across surfaces, and every member read-only |

The distinction that matters: Author mode may not **decide** a fold or a split, but
it does **apply** one the mapping already states. A shared subject template in
`target.r2rml` is a decision someone took and wrote down, and the derivation reads
it like any other fact
([entity-derivation-guide.md § Identity is the subject](entity-derivation-guide.md)).
What it never does is invent one from co-location or from a hunch.

## The feasibility envelope

Author mode writes the envelope: which compositions are *structurally available* and
which are *impossible*, so Phase 2 proposes neither a view that cannot exist nor
one it wrongly believes is barred.

```jsonc
"envelope": [
  { "kind": "federated-view", "members": ["A", "B", "C"], "primary": "B",
    "verdict": "possible",
    "why": "every other member joins directly to B" },
  { "kind": "federated-view", "members": ["A", "D"],
    "verdict": "impossible", "evidence": { "hops": 3 },
    "why": "A and D are 3 joins apart, so no member is adjacent to both" },
  { "kind": "consolidation", "members": ["X", "Y"],
    "verdict": "candidate",
    "evidence": { "sharedLogicalTable": "<TABLE>" } }
]
```

**The feasibility test, exactly.** A set of entities is federatable **iff some member
is adjacent to every other member** in the undirected relationship graph. Three
consequences follow, and the middle one is the easy mistake:

1. The **maximal** federatable sets are exactly the closed neighbourhoods — one per
   entity with two or more neighbours. The envelope reports those, dropping any star
   wholly contained in a larger one.
2. **A directed two-hop chain `A→B→C` is not impossible.** It is a star centred on
   `B`: the primary is a free choice and a join is symmetric, so `A` and `C` both
   join directly to `B`. Reading "depth-2 chain" as a bar is wrong, and it bars
   views that are available.
3. The minimal genuinely impossible shape is a **pair three or more joins apart** —
   nothing is adjacent to both, whatever else the view includes. Those pairs are
   what the `impossible` rows name, and they appear first at a four-entity path.

`candidate` is **evidence recorded, not a proposal**. R2RML co-location says the
source keeps two classes in one table; it says nothing about whether this automation
reads them together, and co-location is not identity. Phase 2 decides; Author mode
only makes sure Phase 2 does not have to rediscover the fact.

## Revision has a deadline

Before any workflow binds to an entity, revision is nearly free — no records exist on
the local path, so the emitter regenerates and nothing downstream has to change.

**The first build group that binds to an entity closes that component.** After it, a
fold or a split is a rework of every binding. The deadline is **per component**, so
one component stays open while others have closed.

This is not theoretical: genome's execution creates entities before the workflows
that read them, because the generated types require it
([execution-guide.md § 1.3](execution-guide.md), the Data Fabric question).

| Phase | Reads | May revise |
|---|---|---|
| Author | the inventory | nothing — emits the baseline |
| 2a — solution fidelity | Components, Process Map, Handoffs | `locus`; component isolation; which entities are written at all |
| 2b — step fidelity | Workflow substeps and their `(input: …; output: …)` | hop counts, hot paths, the denormalization itself |

**2a cannot settle hop cost.** Handoffs rows name which component touches which store
and in which direction — enough for `locus` and for island isolation, not for "this
query costs three round trips on a path that runs every 90 seconds". That is a
step-level fact, so the latency argument for folding belongs to 2b, and 2b only
touches components whose workflows exist.

## How a revision is recorded

The genome is read-only during execution, so a revision never edits it
(the genome is read-only during execution — [execution-guide.md](execution-guide.md)).

| Artifact | Holds | Mutable |
|---|---|---|
| genome `## Data Model` | the contract — entity set, register, verdicts | no |
| `target.r2rml` | the evolving relational design **and the entity identities** | **yes, from Phase 2** |
| `process-resolved.md` | the process in the table vocabulary `target.r2rml` exposes | **yes — it must stay resolvable against it** |
| the working folder | evidence gathered, per component | yes |
| README § Differences from the genome | any revision contradicting the contract | written at the end |

`target.r2rml` is byte-identical to `source.r2rml` when Author mode ends, and every
later revision edits it — so the diff between them is the normalization decision
record ([data-model-guide.md § Artifacts](data-model-guide.md)).

**A revision is three edits, not one.** Changing a subject template changes which
tables and columns the mapping exposes, so the resolved process description written
against the old vocabulary stops resolving. Re-resolve it against the revised
mapping and re-derive from both
([process-resolution-guide.md § Re-resolving after a revision](process-resolution-guide.md)).
The resolver fails loudly on a stale reference; the derivation does not, so the
order matters.

The last row closes the loop: genome's completion report already surfaces a
divergence and offers it as a genome edit, so an iteration that outgrows the contract
corrects the contract instead of drifting from it.

## Anti-patterns

1. **Deciding to denormalize in Author mode.** There is no evidence yet; the
   baseline is the deliverable (§ Conservative means normalized). Applying a fold the
   mapping already states is not this.
2. **Treating R2RML co-location as a proposal, or as identity.** One table can carry
   two records; only one subject mints one record (§ What Author mode may not
   decide).
3. **Calling a two-hop chain an impossible federated view** (§ The feasibility
   envelope). It is a star centred on the middle entity.
4. **Deciding a whole model at once** when it decomposes into components (§ The unit
   of work).
5. **Using 2a evidence for a hop-cost argument** (§ Revision has a deadline).
6. **Editing `source.r2rml`**, or editing `target.r2rml` during Author mode. The
   baseline is the only thing that makes a later diff meaningful.
7. **Revising `target.r2rml` without re-resolving the process description against
   it** (§ How a revision is recorded). The derivation accepts a stale resolution
   without complaint.
8. **Letting a platform limit change the ontology** (§ Priority).

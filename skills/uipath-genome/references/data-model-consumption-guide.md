# Data Model Consumption Guide — entities in the process description

Rules. How a genome's Workflow, Handoffs and Interface refer to a derived entity set,
and how the owning build skills bind to it.

Read whole before writing the Workflow of a genome that has a data model, and in
Edit or Execute when the genome carries a `## Data Model` section. Router:
[data-model-guide.md](data-model-guide.md).

This guide exists for one reason beyond readability: **the access pattern Phase 2
needs is declared here, not inferred later.** A step that says which entities and
fields it touches, and which traversals it makes, turns the denormalization question
from a global inference into a pile of local declarations
([normalization-guide.md § Revision has a deadline](normalization-guide.md)).

## The Data line

A Workflow step that reads or writes the model carries one `**Data:**` line after its
substeps. Steps that touch nothing carry none.

```markdown
4. **Record the assessment** (input: assessor decision; output: updated claim):
   a. Set the claim's status to the decision
   b. Stamp the assessment date and the assessor
   **Data:** writes `Claim.status`, `Claim.assessedOn`, `Claim.assessedBy`;
   reads `Policy.coverageLimit` via `Claim.policy`
```

Grammar — one line, clauses separated by `;`, each clause `<verb> <items>`:

| Clause | Means | Phase 2 reads it for |
|---|---|---|
| `reads <Entity>.<Field>, …` | the step needs these values | which fields are hot |
| `writes <Entity>.<Field>, …` | the step sets these values | write sites, atomicity, `level` |
| `creates <Entity>` | a new record | required-ness at insert time |
| `deletes <Entity>` | a record is removed | retention, cascade |
| `… via <Entity>.<Relationship>` | the values were reached by traversing | **hop count** — each `via` is a round trip |
| `filters <Entity> on <Field>` | a query narrowing a set | index pressure, whether a federated view would help |

Rules:

1. **Name entities and fields exactly as the model names them**, not as the ontology
   names them. The genome is written against the Data Fabric model; the IRI lives in
   the register.
2. **Every `via` is a hop**, on the documented resolve-then-filter access pattern —
   a claim that still needs confirming against a tenant
   ([normalization-guide.md § Platform limits](normalization-guide.md)). Count them
   regardless: the count is evidence whether or not the cost is what we think.
   Chained traversals are written as several `via` clauses and cost one round trip
   each — that is exactly the evidence a later fold is argued from.
3. **A step that writes a field a constraint governs cites nothing extra** — the
   constraint's register row already names the subject, and the Business Rule for a
   `transition`-level constraint sits under this step anyway.
4. **Keep it behavioural.** No activity names, no query syntax, no entity ids. The
   `**Data:**` line names business objects and their fields, like every other line of
   a genome ([genome-format-guide.md § Provenance](genome-format-guide.md)).

**Do not write a `**Data:**` line the step does not need.** An over-declared step
inflates the hop count and argues for a fold nobody needs.

## Handoffs and the model

An entity that one component writes and another reads is a **shared store**, and
genome already has a row shape for it: Handoffs names the mechanism "a shared store
one component writes and another reads — a Data Fabric entity"
([genome-format-guide.md § Handoffs](genome-format-guide.md)).

| Situation | Handoffs row |
|---|---|
| component A writes `Claim`, component B reads it | one row, mechanism `Data Fabric entity Claim`, data schema the fields passed, failure behaviour on the reading side |
| both components write the same entity | one row per direction; say which fields each owns |
| a component reads an entity nothing in the genome writes | **no row** — it is an input system; the entity is a Platform Dependency and the ontology says where it comes from |

Solution-fidelity Phase 2 reads exactly these rows for `locus` and for island
isolation; it does not need the `**Data:**` lines
([normalization-guide.md § Revision has a deadline](normalization-guide.md)).

## Interface

A component whose contract carries a record names the entity and the fields crossing
the boundary, never a record id alone:

```markdown
- **Inputs:** `ClaimReference` (text) — the business key of the `Claim` record to assess
- **Outputs:** `AssessmentOutcome` (text) — written to `Claim.status`
```

A record **id** is not a contract: it is a UUID the platform mints, meaningless
outside the tenant that holds it. Cross a business key instead and let the receiving
component resolve it. Where a component genuinely must pass an id, say so and record
why — it couples the two components to one tenant.

## Platform Dependencies

One row per entity, whatever the component count:

| Resource | Type | Purpose |
|---|---|---|
| `Claim` | Data Fabric entity | the claim under assessment, created at intake and updated through the lifecycle |

The entity's **fields are not listed here.** `entities.json` and the solution
resources are the schema; duplicating a field list into the genome creates a second
contract that drifts and is not machine-checked
([datafabric-emission-guide.md § What reaches the genome](datafabric-emission-guide.md)).

## What the build skills need

Naming only — each skill owns its own binding mechanics.

| Target | Needs | Owned by |
|---|---|---|
| **Maestro Flow** `core.datafabric.*` nodes | the entity's resource key **and** the unassigned-folder sentinel; without both the node is tenant-scoped and fails at run time | `uipath-maestro-flow`; the keys and the `node configure` step are described in `uipath-platform` → `references/data-fabric/local-entities.md` § Using a local entity from a flow |
| **Maestro BPMN** | Data Service connector activities for record operations | `uipath-maestro-bpmn` → its registry reference |
| **Maestro Case** | the entity picker on case data | `uipath-maestro-case` |
| **RPA** | the Data Service activity package and the generated entity types | `uipath-rpa` |
| **Coded agents / functions** | the SDK's entity surface | `uipath-agents`, `uipath-functions` |

Two facts the genome must carry for any of them to work, because they are decisions
rather than mechanics:

1. **A locally authored entity is provisioned into the deployment's folder, not at
   tenant level.** Anything binding to it needs the folder sentinel at design time.
   A binding that omits it resolves to a tenant entity that does not exist, and the
   failure message names the entity — so it reads as "the entity was not created"
   when the entity exists and the binding is missing.
2. **The entity must exist before the workflows that read it are built**, because the
   generated types come from it. That is why the Data Fabric scaffolding question is
   asked once per run, before the build groups
   ([execution-guide.md § 1.3](execution-guide.md)).

## Build order

Strict, and it follows from fact 2 above.

```
1  entity set emitted and applied        apply-entities.py, gates green
2  Platform Dependencies rows written    one per entity
3  Workflow authored with Data lines     the access pattern is declared here
4  Handoffs rows written                 entity edges between components
5  build groups run                      the first group that binds closes
                                         that entity's component for revision
```

Step 5's first binding is the deadline: after it, a fold or split in that component
is a rework of every binding, not a regeneration
([data-model-guide.md § Commitment ladder](data-model-guide.md)).

## Anti-patterns

1. **Omitting the `**Data:**` line on a step that touches the model.** Phase 2 then
   has to infer the access pattern, which is the thing this design exists to avoid.
2. **Listing entity fields in Platform Dependencies.** A second schema that drifts.
3. **Passing a record id across a component boundary** without saying why.
4. **Writing a `via` chain the step does not make**, or omitting one it does. Hop
   count is evidence; a wrong count argues for the wrong fold.
5. **Naming ontology IRIs in the Workflow.** The genome is written against the model;
   the IRI is in the register.
6. **Binding a Flow or BPMN node to a local entity without the folder sentinel.**
   Fails at run time with a message that blames the entity.

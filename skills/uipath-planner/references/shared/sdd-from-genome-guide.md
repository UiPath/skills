# SDD From Genome Guide — the SDD written from a genome

An SDD is written from a genome once the genome passes its strict check: by `extract` for a documentation request, by `extract` or `edit` when the user or a caller asks for it ("Write the SDD"), and by `edit` again after every edit of a genome that has one. It is the people's rendering of the genome: it opens with every open question ([open-questions-guide.md](open-questions-guide.md)), followed by the design in the template people know. Whoever answers the questions reads it, without the genome. A genome with no SDD keeps its open questions in its Open Decisions, which the interview asks ([interview-guide.md](../interview/interview-guide.md)).

**The genome is the source.** An answer, a change or a correction goes into the genome first, and the SDD is written again from it.

A genome designed from an SDD (one with a `Designed in:` line) keeps that SDD as its source. There this guide writes only the SDD's Action Required section (item 6).

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| the genome passed its strict check | — | this guide whole; [open-questions-guide.md](open-questions-guide.md) whole; [sdd-writing-guide.md](../design/sdd-writing-guide.md) § Gap Markers |
| the genome passed its strict check | an SDD is written whole, or one of its body sections again | the template of each SDD item 1 names, in `assets/templates/`; [sdd-writing-guide.md](../design/sdd-writing-guide.md) Step 2 items 2, 5 and 8 |
| the genome passed its strict check | a process genome | [scope-recommendation-guide.md](../design/scope-recommendation-guide.md) § Solution scope (Level 1 = Solution or user picked Solution (customize)) and § Solution overview SDD structure |

## Write the SDD

1. **One SDD per buildable project, laid out as `design` lays them out.**
   - **A component genome:** one SDD, `<slug>-sdd.md` beside the genome, from the template of its Build With skill:

     | Build With skill | Template |
     |---|---|
     | `uipath-rpa` | `rpa-sdd-template.md` |
     | `uipath-maestro-flow` | `flow-sdd-template.md` |
     | `uipath-maestro-bpmn` | `bpmn-sdd-template.md` |
     | `uipath-maestro-case` | `case-sdd-template.md` |
     | `uipath-agents` | `agent-sdd-template.md` |
     | `uipath-api-workflow` | `api-workflow-sdd-template.md` |
     | `uipath-coded-apps` | `coded-app-sdd-template.md` |

     A Case component designed in an SDD already has one: its Interface names it, and nothing is written for it.
   - **A process genome:**
     - a solution overview, `<slug>-solution-sdd.md`, beside the process genome;
     - one SDD per project, `<component-slug>-sdd.md` beside its component genome in `<slug>-genome/`, linked from the overview's Per-Project SDD Index; the RPA components of one flow share one RPA SDD, named after the first of them.

     The open questions of every component are in the overview's Action Required ([open-questions-guide.md](open-questions-guide.md) § Items).

     A component built by a skill with no template (a function, an IXP model, a connector) gets no SDD of its own. Its contract goes in the table its consumer's template holds for it.
   - **A large extraction** writes its SDDs once the whole genome passes its strict check: the lead agent writes the solution overview, and may give each per-project SDD to a subagent that reads this guide, its template and that component genome, run as the parts are ([extraction-parts-guide.md § Running in Parts](extraction-parts-guide.md) item 7).
2. **Front matter, in the template's order and where the template places it** (the Maestro BPMN template holds Decisions Made and Recommended Scope in §10 and Action Required last):
   - **Document History:** one row per write, naming the verb.
   - **Planner Handoff:**
     - `Status: ready`: the genome exists, and its open entries are Action Required items, not a gate;
     - `Execution autonomy`: `interactive` when someone answers the run's questions, otherwise `autonomous`;
     - `Delivery model`: `unspecified` unless the request, or the run's own delivery-model answer, names it, since a genome names no platform;
     - `SDD scope`, and the solution rows for a process genome;
     - `Template validation`, as the template check sets it;
     - last, `| **Genome** | <relative path to the genome> · genome-sha256 <fingerprint> |` (item 4). This row tells every reader that the genome is the source.
   - **Decisions Made**, whatever the `Execution autonomy` (the template's condition and its fixed rows are `design`'s): what the genome decides, one row each, the reason taken from the genome's own words:
     - each component's skill;
     - each `Decided:` split;
     - an implementation mode or package pin the Build With rationale states;
     - each decided Open Decisions entry.
   - **Recommended Scope:** the genome's Components (or its one Build With product) as the recommendation.
   - **Action Required — SME Review Items:** [open-questions-guide.md](open-questions-guide.md).
3. **The body: each template section written from the genome section that owns its subject**, in the template's words for people. The genome's ids stay: steps by number and bold name, criteria and Configuration Questions by number, entries as `D<n>`.

   | RPA template section | Written from |
   |---|---|
   | 1 Process Overview | Overview, and Actors and Systems. In Scope: the steps built. Out of Scope: the Source Map's `Not covered` and `Unused` rows and retired targets. Assumptions: each open reading, marked `[SME REVIEW]` |
   | 2 Process Map | the Process Map diagram, or the Workflow's steps for a component; the As-is process map when the genome holds one |
   | 3 Detailed Process Steps | Workflow, step by step, with its substeps |
   | 4 Business Rules; 6 Value Mappings | Business Rules: the rules that map one value to another go to § 6 |
   | 5 Data Definitions | Interface, the queues' item fields, the Data Fabric entities |
   | 7 Exception Handling; 8 Error Handling | Error Handling, business exceptions to § 7 and system errors to § 8; the Transactional Shape's outcomes |
   | 9 Application Inventory | Target Applications or Actors and Systems, Connections, Credentials |
   | 10 Master Project Architecture; 11 Project Structure; 12 Queue Architecture | Components or Build With; the Transactional Shape; Queues |
   | 13 Implementation Mode; 14 Packages | the Build With rationale, where it decides them |
   | 15 Credentials & Assets | Assets, Credentials, and the Configuration Questions by number |
   | 16 Deployment Environment | Deployment, Interface and the Triggers table; the environments themselves as decided when the build is prepared |
   | 17 Testing Strategy | Acceptance Criteria, by number |
   | 18 Next Steps | preparing the build (optional) and building with `uipath-genome` |

   The other templates take the same subjects into their own sections.

   **What the genome leaves to the build** is written as its options, never as a pick of the SDD's own: a split with no `Decided:` line, the libraries' layout, the implementation mode, the packages, the template. Each option comes with what it requires and changes, and the line "Decided when the build is prepared". A section whose subject the genome does not have says so in one line. A template instruction to add an Action Required item for a fact the source leaves out is met by the genome's own entry for that fact. The SDD adds no question the genome lacks: a missing one is a genome edit first.

   Length follows content, and the template-superset check passes ([sdd-writing-guide.md](../design/sdd-writing-guide.md) Step 2 items 5 and 8).

   An extracted genome's provenance stays in its Source Map. The SDD names the source once, in § 1, and nothing more of it.
4. **Fingerprint.** `node "<SKILL_DIR>/scripts/sdd-fingerprint.mjs" --genome "<GENOME_MD>"` prints the genome's fingerprint: the process genome and every component genome it links. It goes in the root SDD's `Genome` row once the genome is final; a per-project SDD's row names its component genome, `| **Genome** | <relative path to its component genome> |`, with no fingerprint. The strict check fails an SDD whose row no longer matches its genome.
5. **Written again on every write.**
   - `edit` writes again the sections the edit changed, and Action Required, keeping its answers ([open-questions-guide.md](open-questions-guide.md) Writing Rule 1), then the fingerprint.
   - A person's edit to any other section is a change request: `edit` "The SDD was edited: update the genome" ([edit-guide.md](../edit/edit-guide.md)). The genome takes the change, and the SDD is written from it again.
6. **A designed genome's SDD** keeps its body as `design` wrote it. After the genome is written and after every edit, its Action Required section is written again from the genome, holding:
   - the SDD's own items carried as entries, under the ids the genome gives them, each naming the id the SDD's body marks it with where the two differ (`was D3`);
   - the SDD's items that touch no genome section, as the SDD wrote them, under their SDD ids;
   - the genome's Configuration Questions;
   - every entry the genome added.

   The SDD's fingerprint leaves this section out, so the genome's `Designed in:` line stays current. A Case Management SDD keeps its own review-item table, and nothing is written into it.
7. **A client Word document** is made on request, as `design` makes one ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Client Word Document). It is for reading and sign-off: answers come back through the markdown, an interview or a reply.

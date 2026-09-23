# Extraction Guide — genome from an existing automation

Read source, then write a genome that reads as authored: behavioural, generalized, replication-grade, provenance confined to the Source Map. Content rules: [genome-format-guide.md](genome-format-guide.md). Framework specifics: source guide. Never ask the user what the automation does; artifacts tell you.

## Source Guides

A UiPath source is read with [uipath-source-guide.md](uipath-source-guide.md). Any other source is read through the framework migration pack: resolve it, select the framework row, run its script and read its source guide in full before Step 1, exactly as [SKILL.md § Source Frameworks](../SKILL.md) states. No pack, or no row matches → stop as that section says. Do not improvise an extraction from an unknown framework.

## Pipeline

### Step 1 — Detect

Run source guide's Detection table against the given path. Decide:
- **Framework** (which source guide).
- **Deployment unit:** solution or multi-project bundle → process genome; single project → component genome ([genome-format-guide.md § Two Levels](genome-format-guide.md)).
- **Missing manifest:** proceed from artifact files; every value that would have come from the manifest is `*[Inferred]*`.

### Step 2 — Inventory

List every file per project, classify with source guide's Inventory table, drop everything in its Exclusions. Record artifact types present; read only those Signals sections of the source guide.

### Step 3 — Extract signals

Per artifact, in inventory order, using source guide's signal tables. Collect into working notes (not the genome) grouped by component:

| Signal class | Feeds |
|---|---|
| Steps and actions, with `DisplayName` or node labels | Workflow |
| Conditions, switches, loops, gateways, expressions | Business Rules, Workflow substeps |
| Try/catch, retry, error ports, boundary events, SLAs, escalations | Error Handling |
| Arguments, schemas, variables, data objects | Interface, Workflow data annotations |
| Applications, connectors, URLs, connection references | Target Applications |
| Invocation edges inside a component | Call graph → step order |
| Invocation edges across components, queues, tasks, events | Handoffs (process genome) |
| Triggers, schedules, entry points | Workflow step 1, Deployment |
| Queues, assets, credentials, buckets, connections, folders | Platform Dependencies |
| Per-item iteration with per-item outcomes: queue item fetch and status updates, a loop over rows or files with a per-item catch, a work-list read; framework state machines and their configuration workbook | **Transactional Shape** — unit of work and its alternatives, the As-is (produced by, consumed by, item store, coordination, item kinds, step groups), the outcomes, the split options derived with rule 8's table and the evidence ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)); never a verdict; the framework's plumbing is not steps (source guide's framework section) |
| Hardcoded literals: paths, URLs, addresses, names, thresholds, columns | Configuration Questions |
| Test cases, eval sets, assertions | Acceptance Criteria evidence |
| Prompts and instructions (agents) | Business Rules (paraphrased) |
| UI control recognition data (object maps, selectors, XPaths) | **Not written** ([genome-format-guide.md § Source Map](genome-format-guide.md)). Read source guide's target inventory (scratch folder) for each control's type and the actions applied to it — they decide substep wording; record counts in the Source Map |
| Composite UI actions (type-ahead picks, menu paths, option lists, find-row-then-act, keystrokes to the focused element) | Workflow substeps carrying the full interaction contract ([genome-format-guide.md § Workflow](genome-format-guide.md)); wording per source guide's § Composite actions |
| Data-driving rows (recordsets, data sheets) | **Not written.** Literals feed Configuration Questions; row schemas feed Interface and test components' row tables; rows stay in the export |
| Login accounts used per scenario | Platform Dependencies: one credential asset per account ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md)) |
| Blanket screenshot or capture steps | **Evidence policy**, not steps (below) |
| Where everything came from | **Source Map** — the migration contract ([genome-format-guide.md § Source Map](genome-format-guide.md)) |

Read every relevant file. No sampling, no "the helpers are similar".

**Values are read, not inferred from their rendering.** A framework's inventory output is a rendering of the source, and the genome inherits every gap in it. Run the source guide's renderer self-test first when it has one, and treat an empty value in a rendering as "not shown", never as "not set". Every fact a rule or a step depends on is written as the source states it: comparison literals verbatim (spacing and punctuation included) with the source's operator and case rule — "contains `Wollen Sie wirklich`, case-insensitive" — and, where the framework normalises whitespace or searches with a pattern, that too ("reads exactly `Order placed!`, spacing aside", "matches `software|automation` anywhere, ignoring case"); counts and loop bounds with whether the test comes before or after the body; lengths, positions and occurrences of text operations; waits and pauses in their unit, and a check's budget — its own timeout, or the framework default the source guide names when it has none; whether a field is set (replaced) or typed into (appended, key by key); flags that decide control flow. A fact the rendering does not show is read from the source object before it is written; a fact that cannot be read is flagged `*[Inferred]*` and named in the Source Map, never filled with a plausible number.

**Three readings a rendering gets wrong silently.** A value bound to a built-in (the run date, the user's folder) is computed at run time — write it as such, never as the stored default a same-named project variable carries. The format a date or number is typed or compared in (a mask, a pattern, one part of a date per segment) is part of the value. A step's own result handling is behaviour: a check whose failure the source logs as a pass or ignores is a decision or an optional wait, not a hard check, and a check that passes when its target is absent asserts absence. A parameter's unit, its default, and which of two filled parameters overrides the other are read from the source's own documentation of that parameter (a framework export often carries it) before they are called unknown.

**Wrappers are not components.** A library that exists only to drive a technology through an identity passed to it — find the element by id, then click, type, read — is the source's substitute for a driver. Its calls are UI steps of the component that makes them, on the element the identity names; the identities are that component's UI targets (recorded in the Source Map's inventory with the recorder's captures), and the library's logon, session and certificate workflows are what remains of it as a component. The source guide's § Component Detection names such wrappers per framework.

**Evidence policy.** A source whose steps are dense with screen captures (settle-wait, full-desktop capture, next interaction) is recording its audit trail, not choosing verification points. Treat it as a policy: count captures per process; never write one as a workflow step; never emit one activity per capture. State the policy once per component, in Error Handling (in Error Handling and Recovery for a process genome, with the test-execution facts under Deployment): the source's density, and what the rebuilt automation does instead (screenshot attached to the test result at each verification point and on every failure — what a reviewer comparing a source run to a UiPath run needs). Give it an acceptance criterion: evidence not asserted is evidence nobody notices is missing. Read where the captures sit to say who owns the evidence (inside reusable sub-processes and none in the roots → library produces it, test cases collect it; in the roots → the opposite). Platform mapping: `uipath-test` owns execution evidence (screenshots and attachments per test case in Test Manager); the robot's own screenshot-on-failure covers the failure half; both belong under Platform Dependencies / Deployment, never in Build With. Which step kinds count as checkpoints for the Source Map: source guide's § Evidence.

### Step 4 — Build graphs

- **Call graph per component** with source guide's Call Graph Rules → ordered workflow steps. An invocation made from a result or error route (run this process when the step fails) is an edge too, a conditional one; objects named alike are separate nodes — every edge names its callee by id, a step is described from the copy its caller runs, and two live copies are both carried. Dead code goes to the Source Map — but a branch is dead only when the conditions on every path to it contradict it for every value; prove that from the condition text before writing "dead" (an inner `contains X` under an outer `is empty OR contains X` is reachable for every value the outer condition admits). A wrong dead-code row drops behaviour from the build, and execution never edits the genome to restore it.
- **Handoff graph across components** from cross-component edges → Components order and Handoffs table. Each edge records mechanism, data passed, and failure behaviour visible in the source (error port, retry, boundary event, dead-letter queue). Every edge — or intra-component phase boundary — that hands items one by one (a queue, a file drop, a work table, a mailbox, a work-list file) is a **candidate flow** of the Transactional Shape: it starts a flow of its own only when its items are independent of the upstream item and the phases are separated; a store the same job fills and empties with each upstream item's own children (a mail's attachments, a report's work list and its rows) is a level of one unit of work, not a second flow; a component that takes items of one flow and creates independent items of the next is a chain ([genome-format-guide.md § Transactional Shape](genome-format-guide.md) rules 11–13).

### Step 4b — Verify every suspected source defect

A finding that the source misbehaves is a **suspected defect** until this step settles it. Examples: a flag set but never tested, an exit that cannot fire, a result checked but never captured, a retry an exception bypasses, a notice prepared but never sent, a branch whose test contradicts its own comment, one copy of a template doing what its sibling does not. The inventory output is a rendering the pack's script produced, and extraction has read it, not the source. So the finding may belong to the source, or to the rendering. Settle each one before anything is written about it, in two passes.

1. **The rendering, in full.** Re-read every object the finding rests on in the uncompressed rendering, never a compact or folded one. That includes:
   - the call's argument and result bindings, in both directions;
   - the callee's error and final blocks;
   - the disabled code (a superseded flow often explains a value the live flow only carries);
   - the sibling copies.
   Then follow the effect through the bindings to where it lands: what the caller does next, and what a later or resumed run does with what was, or was not, written.
2. **The framework's source, directly.** Open the source objects the finding rests on in the export itself, located by the identity the source guide uses (object id, editor line, node path). Read them the way the source guide states next to its command block: the pack's direct-read lookup for a structured export, which prints every key and masks secrets as the renderings do, or the cited lines of the file for code. Only when a pack offers no direct read, use a generic reader, and print no secret with it:
   - For a structured export (JSON, XML, a database dump): parse the file, select the object, and print every key. Drop only empty values and binary blobs.
   - For code: read the lines themselves.
   Compare field by field with what the rendering showed for exactly the facts the finding rests on: operators and every operand of a condition chain, bindings, flags, defaults, the presence or absence of a command. Never check through a projection that names the fields it keeps. It hides every key it did not name, such as a chained condition kept under its own key or a result binding held on the node rather than in its attributes. A reader that misses such a key produces a "discrepancy" that is the reader's own. Read the objects targeted, not whole files. The source guide's warnings against reading raw exports are about bulk reading, and this is a lookup.

Classify each finding by what the two passes show, and write it accordingly:

| Finding | When | Genome | Also |
|---|---|---|---|
| **Rendering artefact** | the source differs from the rendering | write the behaviour from the source; no defect | report the renderer defect for the pack, with the object and the field |
| **Source defect** | rendering and source agree, and the behaviour contradicts the evident intent — the source's own comment or log text, a sibling copy, the step's purpose | marked **Source defect** per [genome-format-guide.md § Source Defects](genome-format-guide.md); evidence in the Source Map | the consequence traced through the source; the parts that depend on data, configuration, platform or package behaviour flagged `*[Inferred]*` |
| **Source rule** | rendering and source agree, and the source's comment or design shows the behaviour is intended | the rule, unmarked | nothing |
| **Unresolved** | the structure is certain, but the behaviour turns on a setting or platform or package semantics that neither the export nor the pack documents | both readings stated, the one the rebuild follows marked `*[Inferred]*` | report the undocumented semantics for the pack |

Each finding gets its own Source Map row, with the object ids, the line numbers and the classification. Each component also gets one Verification row saying that both passes were made and whether the rendering matched the source. A finding nobody verified is not written as a defect. When time does not allow both passes, it is written as the behaviour the rendering shows, flagged `*[Inferred]*`, with its Source Map row saying which pass is missing.

### Step 5 — Infer complexity (component)

| Signal | Simple | Medium | Complex |
|---|---|---|---|
| Workflow files or nodes carrying logic | 1-3 | 4-8 | 9+ |
| Distinct target applications or connectors | 1-2 | 3-4 | 5+ |
| Entry points or triggers | 1 | 1-2 | 3+ |
| Conditional branches (if / switch / gateway / decision) | 0-3 | 4-10 | 11+ |
| Error-handling constructs | 0-1 | 2-3 | 4+ |
| Composite UI interactions carrying a contract (type-ahead pick, custom option list, segmented or picker date, menu path, row-by-content, dialog answer) | 0-1 | 2-4 | 5+ |
| Test cases of a test component, or checkpoints they assert (take the higher) | 1-3 cases / ≤6 checkpoints | 4-8 / 7-20 | 9+ / 21+ |

A **test component**'s Workflow has one numbered step per test case (`N. **Test case: <title>**` with lettered substeps), so the population matrix's step minimums do not apply to it — its depth is the cases and their checkpoints; a **library** component's rows 1 and 3 count its public workflows and one entry point.
| Platform resources (queues, assets, buckets, connections) | 0 | 1-2 | 3+ |
| Human-in-the-loop waits | 0 | 0 | 1+ |

Take the level the majority of rows land on; ties go lower. Process genomes: [genome-format-guide.md § Complexity](genome-format-guide.md).

### Step 6 — Map signals to sections

Write the **process genome first** (when applicable), then each **component genome**.

| Section | From |
|---|---|
| Overview | Purpose synthesised from names, targets, data flow. Author's voice. Inferred intent gets `*[Inferred]*`. |
| Target Applications / Actors and Systems | Resolved applications (source guide § Target Resolution). Human lanes, escalation recipients, task assignees become actors. |
| Build With / Components | Source guide § Component Detection → skill per component; [skill-mapping-guide.md](skill-mapping-guide.md) decision tree for steps inside a hybrid component. Test components: one test project, typed and laid out per [genome-format-guide.md § Build With / Components](genome-format-guide.md). |
| Platform Dependencies | Source guide § Platform Resources. Keep source resource name. Credential asset per login account ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md)). |
| Interface | Arguments, schemas, entry points. Must agree with the Handoffs rows touching this component. |
| Configuration Questions | Every hardcoded literal and every application choice: `N. {Question}? (default: {source value})`. |
| Workflow / Process Map | Ordered from call graph; substeps for every multi-field, conditional, or transforming step; `(input: …; output: …)` annotations. |
| Business Rules | Conditions translated per format guide, attached to their step. Agent prompts paraphrased into rules. |
| Error Handling | Constructs translated to behaviour, attached to their step; `### Global` for global handlers. The business/system classification of per-item outcomes goes to the Transactional Shape. |
| Transactional Shape | Source guide's transactional signals, written per [genome-format-guide.md § Transactional Shape](genome-format-guide.md) rules 8, 10 and 11: the As-is exactly as the source has it (its queues, statuses, tags, locks, ledgers, parent and child levels, robot count), the split options derived from the signals for the unit of work and for each alternative unit, with what each requires and changes, the evidence as facts; candidates carry `*[Inferred]*`; no unit of work → the stub; no verdict, no role word in Components; framework files go to the Source Map as a `Framework files` row. |
| Handoffs | One row per cross-component edge from Step 4. |
| Acceptance Criteria | One per step, per transformation, per rule, per handler, plus edge cases. Existing test cases and eval sets become criteria directly (behavioural wording). |
| Deployment | Solution vs independent packages, triggers, folders from manifest and bindings. Count buildable projects: non-test components plus exactly one test project when test components exist. |
| Complexity, Tags | Step 5; applications + domain + platform features. |
| Source Map | Step → file / workflow / node label; component → project. Dead code, unresolved references, inferred steps, every Step 4b finding with its classification and one Verification row per component. Plus migration-contract rows of Step 6b. |

### Step 6b — Complete the Source Map as the migration contract

Fill every row [genome-format-guide.md § Source Map](genome-format-guide.md) lists: framework, export root path and identity, per-step source objects as `` `Name` (id) `` with the data sets that drive each step, checkpoints per step of a test component (source guide's § Evidence says which step kinds count), inventory counts. Nothing is written beside the genome.

Check the contract resolves before offering edits: run the source guide's inventory into a scratch folder **outside the genome's folder** (a temp directory, or one deleted after the check), then `scripts/genome-step-map.py <genome.md> --processes <process inventory> --recordsets <recordset list> --out <scratch>` reads the written genomes' Source Map tables plus that inventory and prints one entry per component workflow step (`component`, `project`, `step`, `name`, `sourceProcesses` `{name, id}`, `recordsets`). Pass the process genome (it follows the Components table to every component genome) or a standalone component genome. It reads as a step every Source Map row keyed by a step number or a step name; every other row (framework, export, checkpoints, inventory, excluded, inferred, data files, row schema, …) is contract and is skipped whatever it is called. Fix every warning it prints — each is a step row whose reference does not resolve against the export, and execution will hit the same gap.

Generalization checklist before writing Configuration Questions: file and folder paths, URLs and hosts, email addresses, server and database names, credential and asset names, queue and bucket names, folder paths, thresholds and limits, column and field names, document types, prompts' tunable parameters (model, thresholds), the application choice itself.

### Step 7 — Write and offer edits

Write all files, then ask "Want to adjust anything?" ([genome-format-guide.md § Write, Then Offer Edits](genome-format-guide.md)). Common follow-ups:

| Request | Update |
|---|---|
| "This step is wrong / missing" | Workflow, then Build With, Acceptance Criteria, Source Map |
| "Complexity should be higher/lower" | Complexity, then depth per population matrix |
| "Remove the inferred flags" | Delete every `*[Inferred]*` — user confirmed the content |
| "Drop the Source Map" | Remove section from every file — genome is being shared as a blueprint; say target and data migration will no longer be possible from it |
| "Re-extract, the source changed" | Rerun from Step 1; preserve user edits the source does not contradict and say which were kept |
| "Merge these two components" / "split this one" | Adjust Components, Handoffs, component files; re-check Interface agreement |
| "Split the dispatcher" / "use one queue" / "apply the REFramework" / "drop the ledger" | Not a genome edit: the split, the store, the template and the fate of the source's coordination stores are execution's configuration answers ([execution-guide.md § 1.3](execution-guide.md)). Edit the Transactional Shape only when its As-is or Evidence is wrong or incomplete |
| "Rename / reorder / remove steps" | Workflow and Source Map together, so every step still names its source objects |
| "Is this really a defect?" / "check it against the source" | Rerun Step 4b for that finding, both passes, and re-mark it in the body and its Source Map row by what the passes show |

## Anti-patterns

1. **Asking what the automation does.** Read it.
2. **Transcribing instead of generalizing.** Queue name or path in the body instead of a Configuration Question with that value as default.
3. **Code in the body:** activity names, node types, variable names, file names, selectors, expressions. Translate; provenance goes to the Source Map.
4. **Integration Service as an application.** Resolve the connector to the vendor system.
5. **Flattening a solution into one component genome**, losing handoffs between projects, or emitting one test project per business area ([genome-format-guide.md § Two Levels](genome-format-guide.md)).
6. **Treating designer metadata, generated files, or test projects as workflow logic.**
7. **Sampling files.** Every non-generated artifact is read.
8. **Leaving a section empty because the source is ambiguous.** Write the best interpretation, flag it, note it in the Source Map.
9. **Extracting the behaviour and losing the provenance** — Source Map without the export's location or without per-step source objects — or its mirror, copies of the export's catalogs beside the genome (Step 6b; [genome-format-guide.md § Source Map](genome-format-guide.md)).
10. **Flattening a composite action to its data** — "Enter Voluntary into Primary Reason" for a type-ahead pick, "choose Terminate Employee" for a two-level menu path, "select row 2" for a row found by content ([genome-format-guide.md § Workflow](genome-format-guide.md)).
11. **Transcribing blanket screen captures as steps or dropping them entirely.** They are the evidence policy (Step 3). A genome that mentions screenshots only in an unhandled-exception handler has dropped the suite's whole audit trail.
12. **Transcribing framework plumbing as steps** — state transitions, retry counters, status updates, screenshots on exception — or dropping the framework's configuration workbook instead of turning its rows into Configuration Questions and Platform Dependencies ([genome-format-guide.md § Transactional Shape](genome-format-guide.md) rule 10).
13. **Asserting a split, a store or a verdict in the Transactional Shape** — a `Recommendation` line, a role word in the Components Type cell, a Consumer row that names a mode, or a split option presented as the design — instead of the As-is, the options and the evidence ([genome-format-guide.md § Transactional Shape](genome-format-guide.md) rules 2, 3, 8).
14. **Writing a value from its rendering** — a count read as "once" because the rendering showed nothing, a case-insensitive test written as case-sensitive, a status text paraphrased or retyped with different spacing, a parsing rule worded from the command's name instead of from its use (Step 3).
15. **Making a scripting wrapper a library of verbs** — "Click by id", "Type by id" as public workflows — instead of the calling steps' UI actions on the elements its identities name (Step 3).
16. **Writing a suspected defect from a rendering.** A defect is marked only after Step 4b's two passes, the full rendering and then the framework's source itself. The mirror failure is just as bad: calling a rendering artefact, or a reader's own blind spot, a defect of the source. Other forms: a defect labelled "suspected" and left for the reader to check, a consequence asserted without tracing it through the bindings, and platform semantics nobody documented presented as fact.

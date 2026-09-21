# Extraction Guide — genome from an existing automation

Read source, then write a genome that reads as authored: behavioural, generalized, replication-grade, provenance confined to the Source Map. Content rules: [genome-format-guide.md](genome-format-guide.md). Framework specifics: source guide. Never ask the user what the automation does; artifacts tell you.

## Source Guides

Frameworks with a source guide, their detection signals, selectors guides and scripts: [SKILL.md § Source Frameworks](../SKILL.md). Select the row whose detection matches, run its script if it has one, read its source guide in full before Step 1. No row matches → tell the user which framework the files appear to be from, that no source guide exists yet, and point to [sources/source-framework-contract.md](sources/source-framework-contract.md). Do not improvise an extraction from an unknown framework.

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

**Evidence policy.** A source whose steps are dense with screen captures (settle-wait, full-desktop capture, next interaction) is recording its audit trail, not choosing verification points. Treat it as a policy: count captures per process; never write one as a workflow step; never emit one activity per capture. State the policy once per component, in Error Handling (Deployment for a process genome): the source's density, and what the rebuilt automation does instead (screenshot attached to the test result at each verification point and on every failure — what a reviewer comparing a source run to a UiPath run needs). Give it an acceptance criterion: evidence not asserted is evidence nobody notices is missing. Read where the captures sit to say who owns the evidence (inside reusable sub-processes and none in the roots → library produces it, test cases collect it; in the roots → the opposite). Platform mapping: `uipath-test` owns execution evidence (screenshots and attachments per test case in Test Manager); the robot's own screenshot-on-failure covers the failure half; both belong under Platform Dependencies / Deployment, never in Build With. Which step kinds count as checkpoints for the Source Map: source guide's § Evidence.

### Step 4 — Build graphs

- **Call graph per component** with source guide's Call Graph Rules → ordered workflow steps. Dead code goes to the Source Map — but a branch is dead only when the conditions on every path to it contradict it for every value; prove that from the condition text before writing "dead" (an inner `contains X` under an outer `is empty OR contains X` is reachable, and the reference migration lost the source's "already completed" handling to exactly that misreading). A wrong dead-code row drops behaviour from the build, and execution never edits the genome to restore it.
- **Handoff graph across components** from cross-component edges → Components order and Handoffs table. Each edge records mechanism, data passed, and failure behaviour visible in the source (error port, retry, boundary event, dead-letter queue).

### Step 5 — Infer complexity (component)

| Signal | Simple | Medium | Complex |
|---|---|---|---|
| Workflow files or nodes carrying logic | 1-3 | 4-8 | 9+ |
| Distinct target applications or connectors | 1-2 | 3-4 | 5+ |
| Entry points or triggers | 1 | 1-2 | 3+ |
| Conditional branches (if / switch / gateway / decision) | 0-3 | 4-10 | 11+ |
| Error-handling constructs | 0-1 | 2-3 | 4+ |
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
| Error Handling | Constructs translated to behaviour, attached to their step; `### Global` for global handlers and REFramework-style classification. |
| Handoffs | One row per cross-component edge from Step 4. |
| Acceptance Criteria | One per step, per transformation, per rule, per handler, plus edge cases. Existing test cases and eval sets become criteria directly (behavioural wording). |
| Deployment | Solution vs independent packages, triggers, folders from manifest and bindings. Count buildable projects: non-test components plus exactly one test project when test components exist. |
| Complexity, Tags | Step 5; applications + domain + platform features. |
| Source Map | Step → file / workflow / node label; component → project. Dead code, unresolved references, inferred steps. Plus migration-contract rows of Step 6b. |

### Step 6b — Complete the Source Map as the migration contract

Fill every row [genome-format-guide.md § Source Map](genome-format-guide.md) lists: framework, export root path and identity, per-step source objects as `` `Name` (id) `` with the data sets that drive each step, checkpoints per step of a test component (source guide's § Evidence says which step kinds count), inventory counts. Nothing is written beside the genome.

Check the contract resolves before offering edits: run the source guide's inventory into a scratch folder, then `scripts/genome-step-map.py <genome.md> --processes <process inventory> --recordsets <recordset list> --out <scratch>` reads the written genomes' Source Map tables plus that inventory and prints one entry per component workflow step (`component`, `project`, `step`, `name`, `sourceProcesses` `{name, id}`, `recordsets`). Fix every warning it prints — each is a Source Map row whose reference does not resolve against the export, and execution will hit the same gap.

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
| "Rename / reorder / remove steps" | Workflow and Source Map together, so every step still names its source objects |

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

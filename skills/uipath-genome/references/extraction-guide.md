# Extraction Guide — genome from an existing automation

Read the source, then write a genome that reads as if authored: behavioural, generalized, replication-grade, with provenance confined to the Source Map. Content rules: [genome-format-guide.md](genome-format-guide.md). Framework specifics come from a source guide.

## Source Guides

The frameworks with a source guide, their detection signals, selectors guides and scripts are listed once, in [SKILL.md § Source Frameworks](../SKILL.md). Select the row whose detection matches, run its script if it has one, and read its source guide in full before Step 1. No row matches → tell the user which framework the files appear to be from, that no source guide exists yet, and point to [sources/source-framework-contract.md](sources/source-framework-contract.md). Do not improvise an extraction from an unknown framework.

## Pipeline

### Step 1 — Detect

Run the source guide's Detection table against the given path. Decide:
- **Framework** (which source guide).
- **Deployment unit:** solution or multi-project bundle → process genome; single project → component genome.
- **Missing manifest:** proceed from the artifact files; every value that would have come from the manifest is `*[Inferred]*`.

### Step 2 — Inventory

List every file per project, classify with the source guide's Inventory table, drop everything in its Exclusions. Record the artifact types present; read only those Signals sections of the source guide.

### Step 3 — Extract signals

Per artifact, in inventory order, using the source guide's signal tables. Collect into working notes (not the genome) grouped by component:

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
| UI control recognition data (object maps, selectors, XPaths) | **Not written.** Read it (the source guide's `targets` inventory) to know each control's type and the actions applied to it — that decides the substep wording — but the locators stay in the export; execution derives the catalog from the export the Source Map names ([source-migration-guide.md § Migration preflight](source-migration-guide.md)) |
| Composite UI actions (type-ahead picks, menu paths, option lists, find-row-then-act, keystrokes to the focused element) | Workflow substeps carrying the **full interaction contract** in behavioural words: typed value, match rule, confirm key, path levels, row rule (source guide § Composite actions) |
| Data-driving rows (recordsets, data sheets) | **Not written.** Literals feed Configuration Questions; row schemas feed the Interface and the test components' row tables; the rows themselves stay in the export and are migrated at execution from the data catalog derived there |
| Login accounts used per scenario | Platform Dependencies: one credential asset per account; the account identity stays in the test data, the secret never |
| Where everything came from | **Source Map** — framework, export path and identity, per-step source objects with ids, inventory counts ([genome-format-guide.md § Source Map](genome-format-guide.md)) |

Read every relevant file. No sampling, no "the helpers are similar". The genome files are the only output; the Source Map is what lets execution find the export's locators and rows again.

### Step 4 — Build graphs

- **Call graph per component** with the source guide's Call Graph Rules → ordered workflow steps. Dead code goes to the Source Map.
- **Handoff graph across components** from the cross-component edges → the Components order and the Handoffs table. Each edge records mechanism, data passed, and failure behaviour visible in the source (error port, retry, boundary event, dead-letter queue).

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

Take the level the majority of rows land on; ties go lower. Process genomes: `medium` with 2-3 components and no human lanes, else `complex`.

### Step 6 — Map signals to sections

Write the **process genome first** (when applicable), then each **component genome**.

| Section | From |
|---|---|
| Overview | Purpose synthesised from names, targets, and data flow. Author's voice. Inferred intent gets `*[Inferred]*`. |
| Target Applications / Actors and Systems | Resolved applications (source guide § Target Resolution). Human lanes, escalation recipients, task assignees become actors. |
| Build With / Components | Source guide § Component Detection → skill per component; [skill-mapping-guide.md](skill-mapping-guide.md) decision tree for steps inside a hybrid component. Test components (test-case groups) all belong to one test project `<ProcessName>.Tests`: type them as "Test-case group in project …" and add the Project layout table ([genome-format-guide.md § Build With / Components](genome-format-guide.md)). |
| Platform Dependencies | Source guide § Platform Resources. Keep the source resource name. One credential asset per login account the scenarios use, named after the account. |
| Interface | Arguments, schemas, entry points. Must agree with the Handoffs rows that touch this component. |
| Configuration Questions | Every hardcoded literal and every application choice: `N. {Question}? (default: {source value})`. |
| Workflow / Process Map | Ordered from the call graph; substeps for every multi-field, conditional, or transforming step; `(input: …; output: …)` annotations. |
| Business Rules | Conditions translated per the format guide, attached to their step. Agent prompts paraphrased into rules. |
| Error Handling | Constructs translated to behaviour, attached to their step; `### Global` for global handlers and REFramework-style classification. |
| Handoffs | One row per cross-component edge from Step 4. |
| Acceptance Criteria | One per step, per transformation, per rule, per handler, plus edge cases. Existing test cases and eval sets become criteria directly (behavioural wording). |
| Deployment | Solution vs independent packages, triggers, folders from the manifest and bindings. Count the buildable projects: non-test components plus exactly one test project when test components exist. |
| Complexity, Tags | Step 5; applications + domain + platform features. |
| Source Map | Step → file / workflow / node label; component → project. Dead code, unresolved references, inferred steps. Framework, export path and identity, per-step source objects with ids, inventory counts — the migration contract of Step 6b. |

### Step 6b — Complete the Source Map as the migration contract

Execution regenerates the target catalog, the data catalog and the step map from the export, so the Source Map must let it: the framework name, the export's root path and identity, one row per workflow step naming the source objects it was built from as `` `Name` (id) `` (names repeat across folders; the id identifies the copy), the data sets that drive each step, and the inventory counts (processes, windows, controls and how many lack a locator, recordsets, rows, credential accounts). Nothing is written beside the genome: no catalog copy, no decoded rows.

Check the contract resolves before offering edits: run the source guide's inventory into a scratch folder (for Certify, `certify-export-inventory.py data`), then `scripts/genome-step-map.py <genome.md> --processes <process inventory> --recordsets <recordset list> --out <scratch>` reads the written genomes' Source Map tables plus that inventory and prints one entry per component workflow step (`component`, `project`, `step`, `name`, `sourceProcesses` `{name, id}`, `recordsets`). Fix every warning it prints — each one is a Source Map row whose reference does not resolve against the export, and execution will hit the same gap.

Generalization checklist before writing Configuration Questions: file and folder paths, URLs and hosts, email addresses, server and database names, credential and asset names, queue and bucket names, folder paths, thresholds and limits, column and field names, document types, prompts' tunable parameters (model, thresholds), the application choice itself.

### Step 7 — Write and offer edits

Write all files, then ask "Want to adjust anything?". Common follow-ups:

| Request | Update |
|---|---|
| "This step is wrong / missing" | Workflow, then Build With, Acceptance Criteria, Source Map |
| "Complexity should be higher/lower" | Complexity, then depth per the population matrix |
| "Remove the inferred flags" | Delete every `*[Inferred]*` — user confirmed the content |
| "Drop the Source Map" | Remove the section from every file — the genome is being shared as a blueprint |
| "Re-extract, the source changed" | Rerun from Step 1; preserve user edits that the source does not contradict and say which ones were kept |
| "Merge these two components" / "split this one" | Adjust Components, Handoffs, and the component files; re-check Interface agreement |

## Anti-patterns

1. **Asking what the automation does.** Read it.
2. **Transcribing instead of generalizing.** A queue name or path in the body instead of a Configuration Question with that value as default.
3. **Code in the body:** activity names, node types, variable names, file names, selectors, expressions. Translate; provenance goes to the Source Map.
4. **Integration Service as an application.** Resolve the connector to the vendor system.
5. **Flattening a solution into one component genome**, or losing the handoffs between projects.
5b. **One test project per business area.** Test-case groups are separate components but one project; the process genome must say so.
6. **Treating designer metadata, generated files, or test projects as workflow logic.**
7. **Sampling files.** Every non-generated artifact is read.
8. **Leaving a section empty because the source is ambiguous.** Write the best interpretation, flag it, note it in the Source Map.
9. **Extracting the behaviour and losing the provenance.** A Source Map without the export's location or without per-step source objects leaves execution unable to find the locators and rows the export carried, and it ships placeholders and invented data. Writing copies of the export's catalogs beside the genome is the opposite mistake: they duplicate the export, go stale, and are not the genome's to keep.
10. **Copying credentials, or dropping the account identity with them.** Passwords stay out; which account each scenario signs in as is part of the data.
11. **Flattening a composite action to its data.** "Enter Voluntary into Primary Reason" for a type-ahead pick, "choose Terminate Employee" for a two-level menu path, "select row 2" for a row found by content: the builder cannot recover the interaction from that wording. Write the contract the source guide's composite-actions table demands.

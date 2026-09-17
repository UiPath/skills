# Extraction Guide — genome from an existing automation

Read the source, then write a genome that reads as if authored: behavioural, generalized, replication-grade, with provenance confined to the Source Map. Content rules: [genome-format-guide.md](genome-format-guide.md). Framework specifics come from a source guide.

## Source Guides

| Framework | Guide | Detection summary |
|---|---|---|
| UiPath (Studio, Studio Web, Maestro, Agents, API workflows, Coded apps, Functions, Solutions) | [sources/uipath-source-guide.md](sources/uipath-source-guide.md) | `.uipx`, `project.json`, `project.uiproj`, `.xaml`, `.cs`, `.flow`, `.bpmn`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json` |

No guide matches → tell the user which framework the files appear to be from, that no source guide exists yet, and point to [sources/source-framework-contract.md](sources/source-framework-contract.md). Do not improvise an extraction from an unknown framework.

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

Read every relevant file. No sampling, no "the helpers are similar".

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
| Build With / Components | Source guide § Component Detection → skill per component; [skill-mapping-guide.md](skill-mapping-guide.md) decision tree for steps inside a hybrid component. |
| Platform Dependencies | Source guide § Platform Resources. Keep the source resource name. |
| Interface | Arguments, schemas, entry points. Must agree with the Handoffs rows that touch this component. |
| Configuration Questions | Every hardcoded literal and every application choice: `N. {Question}? (default: {source value})`. |
| Workflow / Process Map | Ordered from the call graph; substeps for every multi-field, conditional, or transforming step; `(input: …; output: …)` annotations. |
| Business Rules | Conditions translated per the format guide, attached to their step. Agent prompts paraphrased into rules. |
| Error Handling | Constructs translated to behaviour, attached to their step; `### Global` for global handlers and REFramework-style classification. |
| Handoffs | One row per cross-component edge from Step 4. |
| Acceptance Criteria | One per step, per transformation, per rule, per handler, plus edge cases. Existing test cases and eval sets become criteria directly (behavioural wording). |
| Deployment | Solution vs independent packages, triggers, folders from the manifest and bindings. |
| Complexity, Tags | Step 5; applications + domain + platform features. |
| Source Map | Step → file / workflow / node label; component → project. Dead code, unresolved references, inferred steps. |

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
6. **Treating designer metadata, generated files, or test projects as workflow logic.**
7. **Sampling files.** Every non-generated artifact is read.
8. **Leaving a section empty because the source is ambiguous.** Write the best interpretation, flag it, note it in the Source Map.

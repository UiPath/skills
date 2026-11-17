# Configuration Answers Guide — read from the genome, never asked

Step 1.3 of [execution-guide.md](execution-guide.md): after preflight discovery (1.2), before the target project is resolved (1.4). Bare step and section numbers below are that guide's.

The build asks the user nothing. A genome is build-complete: `uipath-planner` answers every choice the build makes before the genome reaches the build — its Build Decisions section, every Configuration Question's default, every flow's `Decided:` line. This step reads those answers into the `Configuration Answers` list, adds the machine facts discovery found, and applies a fixed fallback wherever the machine contradicts the genome.

## The readiness gate

Read first, before any project, package or file is created:

1. **The `Build:` line** of the Build Decisions section — a process genome's own; a component genome inside a process reads `As the process genome.`.
2. **`Build: ready`** → continue with § Reading the answers.
3. **`Build: open`, no Build Decisions section (a genome written before the section existed), or a flow of the Transactional Shape with no `Decided:` line** → the genome is not build-complete. Build nothing. Tell the user, in one message: the open rows by the role each names, each with its question and default, and the flows with no `Decided:` line; then that `uipath-planner` answers them — "interview `<genome>`" to answer them, or "use the defaults for `<genome>`" to take every default. Stop.
4. **A request that already waives the choices** ("take the defaults", "run unattended") on a genome that is not ready: invoke `uipath-planner` with "use the defaults for `<genome>`", then read the genome again from item 1. Without `uipath-planner` installed, stop as item 3 says. The build never takes a default the genome does not record.

## Reading the answers

Record every answer as the `Configuration Answers` list, with a `Scaffolding` group, in the hand-off's README as soon as it exists ([completion-report-guide.md](completion-report-guide.md)). Each answer carries the label of its genome source: `(from the genome: <From>)` for a Build Decisions row, its From cell (`SDD`, `request`, `interview`, `refactor answers`, `source`, `default`); `(from the genome)` for a Configuration Question's default; the `Decided:` line's source for a split. The project-creation step in 1.4 receives the scaffolding answers, and every later build step receives the answers relevant to it. A choice the request makes that nothing in the genome holds — a semantic step on migrated targets ([selector-translation-guide.md](selector-translation-guide.md) rule 12) — is recorded in the same list, as the request words it; a request that contradicts the genome is a `uipath-planner` edit, named in the report, and the build follows the genome.

| Answer | Read from | What it builds |
|---|---|---|
| Genome values | Configuration Questions: each question's default is its answer | each value where the Settings store answer puts it; a setting per environment is the build's value, set per environment at deployment; "not in the export" builds an empty setting, guarded (rule 2) |
| Refactor answers | Source Map's `Requested change` row; Build Decisions' Run modes, Run record and Connections rows; each step's `User ruling` and the defect index's Rebuild follows cell | [refactor-guide.md § Refactor answers](refactor-guide.md) |
| Split | each flow's `Decided:` line and its `Split details — Flow N` row | [transactional-execution-guide.md § Split answers](transactional-execution-guide.md) |
| Location | Build Decisions' Project location | the folder next to the genome, or the existing project to build into (§ 1.4) |
| Library layout | Library layout | each library as a package, or its workflows as a folder of the one project that consumes it ([execution-parts-guide.md § What a Build Adds](execution-parts-guide.md) item 1) |
| Library location | Library location | where each library kept a package is created, or the existing project of it updated in place (§ 1.4) |
| Target framework, expression language, workflow type (RPA projects) | the three rows | the owning skill's init flags; a workflow type whose API an activity package or connection lacks is a contradiction (§ When the machine contradicts the genome) |
| Package versions | Package versions | the versions installed in 1.2 step 3 when the row reads "the latest stable", each pinned version otherwise; one version of each package serves the whole run (§ 1.4) |
| Runtime (non-RPA projects) | Runtime | the owning skill's scaffold choices |
| Settings store | Settings store | settings as Orchestrator assets read once per job and constants where the project keeps its configuration, every value an asset, or a configuration workbook in a storage bucket ([genome-reading-guide.md § Configuration Questions](genome-reading-guide.md)); under every answer the assets Platform Dependencies names stay assets |
| Log target | Log target | a plain Log Message at each log point to Orchestrator's job log, plus the source's run log in its shape or the named target when the row says so |
| Data Fabric | Data Fabric | the entities created at tenant level and the records the build holds loaded, or created only, or neither — what is not done is an open item, and the workflows that use an entity wait for it |
<!--skill-flavor:test-project-template-row:start-->
| Test project template | Test project template | the Test Automation Framework template: configuration loaded, setup and teardown hooks, a timeout around every case and an exception recorded as a failed assertion with its screenshot, so cases carry no failure wrapper; a blank project — each case carries its own failure capture and cleanup ([test-execution-guide.md § Result parity](test-execution-guide.md) rule 3) |
<!--skill-flavor:test-project-template-row:end-->
| Test case status | Test case status | Publishable cases the test package carries and Test Manager runs, or in progress, marked before the pack in the open items |
| Source export | Source export, checked in 1.2 step 5 | the export UI targets and test data migrate from; none — live capture or placeholders, said in the report |
| Framework migration guide | Migration guide | the pack [source-frameworks-guide.md](source-frameworks-guide.md) resolves |
| Source fidelity | Source fidelity | how closely the rebuild follows the source's steps, workflows and folder tree ([source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md)) |
| Live application | Live application, probed (below) | none — every target `offline-unverified` in a migration, a placeholder in an authored genome, its live checks handed to the engineer; an instance — explored and checked as [live-application-guide.md](live-application-guide.md) states, never closing what the row names |
| Healing pass | Healing pass | read-only checks only, or runs of the workflows and tests on the data the row names ([live-application-guide.md § Live healing pass](live-application-guide.md)) |
| Subagents | Subagents, when the host runs subagents | [execution-parts-guide.md § Running in Parts](execution-parts-guide.md) item 7 |

## Machine facts

Discovered in 1.2, recorded in the list with the label `(discovered)`, never asked:

- **Installed packages** where the automation will be built and run (Studio, Robot, tenant feed), by name and version.
- **The export** at the path the Source Map records, its identity checked against the manifest.
- **The live application**: whether the instance the Live application row names answers. The user signs in when the row names an account that signs in; the build waits for the sign-in once and continues offline when it does not come.
- **Templates** the owning skill's discovery finds (the REFramework, the Test Automation Framework).

## When the machine contradicts the genome

Never a question: the build follows the fallback, records it with the label `(fallback)`, and lists it in the report as a deviation and, where named, a `uipath-planner` edit.

| Contradiction | The build |
|---|---|
| a pinned version is not on the feed | takes the nearest higher stable version of the same major; none → that project stops, an edit for `uipath-planner` (Package versions) |
| the host cannot build the target framework, runtime or workflow type, or a decided workflow type cannot use a package or connection the genome needs | that project stops, an edit for `uipath-planner` naming the row; the other projects build on |
| the export is missing at the recorded path | built as Source export "none" |
| the named instance does not answer, or the sign-in does not come | built as Live application "none"; the healing pass does not run |
| a template the decisions name is not found | the plain project with the behaviour authored from the genome ([transactional-execution-guide.md § Split answers](transactional-execution-guide.md) rule 1) |

## Rules

1. **Nothing is asked.** A default in the genome is an answer someone gave or chose; the build takes it as written. Absence of an answer is the readiness gate's stop, never a default the build picks.
2. **An empty or malformed setting that would change the flow, or fail only after business work has begun, is guarded, not defaulted.** A configuration value marked as a setting and left empty — "not in the export", or by the user's instruction — is built as a setting with an empty value. Where the empty value would silently change what the automation does instead of failing (an end-of-day time that compares as reached, a mode switch that falls to its else branch, a name list matched by containment that matches everything, a folder name that resolves to the drive root), and where a value of a fixed format would fail only where it is first used, after items have been worked (an end time that does not parse as `HH:mm`), the build checks it where the settings load and stops the run naming the setting and its source reference. The guards are listed in the report.
3. **Names in the report.** Every component, project and step the answers mention goes by the name the genome gives it — a component by its Component cell, a step by its number and bold name (`step 4, Submit requisition`) — never by its position (`component 2`) or a role several could share (`the consumer`).
4. **Nothing reaches a tenant that no answer allowed**: the Data Fabric answer allows its entities; publishing, deploying, queues, assets and triggers stay open items ([build-guide.md](build-guide.md) rule 12).

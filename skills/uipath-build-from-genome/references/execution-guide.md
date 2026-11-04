# Execution Guide — build an automation from a genome

Genome says *what* to build; build skills know *how*. Execution reads genome, collects configuration answers, builds skill group by skill group through owning skills, wires pieces, checks result against acceptance criteria. Genome is read-only throughout: spec fixes are a `uipath-planner` edit, then a new build. Companion guides open only when their condition holds, and the build's only once the configuration answers exist ([build-guide.md § Read Plan](build-guide.md)).

**Done when** — execution is finished only when all of these hold; a passing build alone is not the end:

1. Every configuration question is answered — by the user, or by its default in an autonomous run ([configuration-questions-guide.md](configuration-questions-guide.md)) — and applied: each setting lives where the Settings store answer puts it ([configuration-questions-guide.md](configuration-questions-guide.md)).
2. Every project validates and builds through its owning skill (§ 2.2).
3. Every acceptance criterion carries a verdict (§ 3.1).
4. The completion report is written as the hand-off's README, and its status is given to the user ([completion-report-guide.md](completion-report-guide.md)).
5. When the target environment needs any setup — a package to deploy, an asset, a queue, a trigger, a connection, a machine prerequisite — [open-items-guide.md](open-items-guide.md) is read and the open-items files are written in the hand-off folder (§ 3.4).
6. A migration with UI targets has its live checks written, and, where the Live application answer names a reachable application, its live healing pass done (§ 2.2b).
7. A refactor also meets [refactor-guide.md § Done](refactor-guide.md).

## Phase 1 — Parse and configure

### 1.1 Read the genome

Read whole file. Identify level from preamble comment (`component` or `process`). For a process genome, read every component genome linked in the Components table before anything else. A missing linked component file: [build-guide.md § Start](build-guide.md) (ask for its path; none supplied → a `uipath-planner` edit, and stop).

Required sections — component: Overview, Target Applications, Build With, Workflow, Acceptance Criteria, Complexity; process: Overview, Actors and Systems, Components, Process Map, Handoffs, Acceptance Criteria, Deployment, Complexity. Optional (may be stubs) — component: Platform Dependencies, Interface, Configuration Questions, Business Rules, Error Handling, Transactional Shape, Tags, Source Map; process: Platform Dependencies, Configuration Questions, Business Rules, Error Handling and Recovery, Transactional Shape, Tags, Source Map. Genome missing a required section is malformed: report which section and stop. Every other missing section is a report item, and the build continues.

The genome is checked before anything is asked, by the `context` call [SKILL.md § Setup](../SKILL.md) already ran: reuse that JSON (level, build mode, the `Designed in:` link, the strict check) and never run the checker again for it. A `FAIL` the build cannot work around ([build-guide.md § Start](build-guide.md) names which) stops execution like a missing section; the report names it as an edit for `uipath-planner`, then a new build.

When the genome carries a design link ([genome-reading-guide.md § Design Links](genome-reading-guide.md)):

- **`Designed in:`** — read the SDD at `designed_in`: its Planner Handoff and project list. The SDD's delivery model is a constraint on every build step, and its project list is the project list of § 1.4 — in a refactor its products and projects are the targets, recorded `(from the SDD)`, and the Target question is asked only for a component the SDD leaves unplaced ([refactor-guide.md § Choosing the target](refactor-guide.md) rule 7). What the SDD decided — the split and queue design, the implementation mode, the package pins, the refactor answers — is answered: [configuration-questions-guide.md](configuration-questions-guide.md) states it in the Configuration Answers as `(from the SDD)` and does not ask it again; the scaffolding and environment questions the SDD leaves open are asked as usual; its `Execution autonomy` row governs the design only and never waives them ([configuration-questions-guide.md](configuration-questions-guide.md), autonomous runs). The build never reads the SDD's PDD.
  - **The SDD changed since the genome** (`designed_in_current` is `false`): the genome is stale. Hand it to `uipath-planner`'s `edit` with the request "The SDD was revised: update the genome" and the genome path, then run the `context` call again on the updated genome and continue with its JSON; the completion report lists what the edit changed. When `uipath-planner` is not available, stop before any question and report the genome as stale, naming the SDD. A genome without a fingerprint (`designed_in_current` is `null`) is read as it is.
  - **The SDD is missing on disk:** say so — the path the line links and that it was not found — and ask the questions the SDD would have decided as usual, Target question included; nothing is recorded `(from the SDD)`.

### 1.2 Preflight discovery

Gather facts the 1.3 scaffolding questions are built from before asking anything. Discovery is silent; it never replaces the questions.

1. Run the platform login status check (`uip login status --output json`); record what an expired session blocks (resource refresh, publish, deploy, Test Manager attachments — local init, validate, build, pack and run still work).
2. Confirm runtime host and edit surface; record which target frameworks and expression languages they support.
3. For every skill named in Build With / Components, run that skill's discovery commands for installed packages; record activity packages and versions available to the authoring host. When a project already exists in the build location, also record its declared dependencies and versions from its manifest.
4. Determine candidate build location: the folder containing the genome file, never the current working directory when that is a different repository.
5. **Export check.** When the Source Map names a framework other than UiPath, read the export path and identity it records and check the export is where it says (manifest matches recorded identity). Record the outcome for the 1.3 scaffolding questions; derive nothing yet — that is [source-migration-guide.md § Migration preflight](source-migration-guide.md), after the questions. The framework migration pack is asked for in 1.3, not searched for here ([source-frameworks-guide.md](source-frameworks-guide.md)).
6. **Template check.** When the genome's Transactional Shape is not the stub ([transactional-execution-guide.md § Shape Rules](transactional-execution-guide.md)), run the owning skill's template discovery for the REFramework (`uipath-rpa` searches the template feed) and record whether an official template is available to this host. The result informs 1.4; it never removes the 1.3 scaffolding question — the owning skill's template-selection rules decide what happens at creation when no official template is found.

### 1.3 Configuration questions — never skipped

[configuration-questions-guide.md](configuration-questions-guide.md), read whole before anything is asked.

### 1.4 Resolve the target project

Every project is created with the `Scaffolding` answers from 1.3: location, target framework, expression language, package set and versions. Pass them to the owning skill's project-creation step as its init flags and dependency list; when the answer was "pin to installed versions", install exactly those versions and never let the init command's defaults override them. When the Source fidelity answer keeps the source's names, each project is named as [source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md) names it.

**Component genome:**
1. When the Location answer is "reuse the existing project" (`project.json`, `project.uiproj`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.case`, `caseplan.json`, `uipath.json` matching the genome's primary skill), use it.
2. Otherwise create the project through the owning skill's project-creation step (that skill knows the init command and its mandatory flags) at the chosen location. Name it after the genome. A `uipath-maestro-case` genome whose Interface names a case SDD creates no project here: `uipath-maestro-case` creates its own solution and case project when 2.2 invokes it.
3. Record `PROJECT_DIR`. Every build step targets it. One project for the whole component genome; XAML and coded files coexist in one RPA project.

**Process genome:**
<!--skill-flavor:process-genome-solution:start-->
1. Create or reuse a solution named after the process, without a dot in the name (`uip solution init` reads the text after a dot as an extension): `uip solution init "<NAME>" --output json` when none exists. Record `SOLUTION_DIR`.
2. Each non-test component becomes one project inside the solution folder: create it through its owning skill with that component's scaffolding answers. A **process** created inside the solution folder is registered by its creation; a project created elsewhere is added to the solution per `uipath-solution`.
<!--skill-flavor:process-genome-solution:end-->
   A **library** is never a solution project (`uipath-solution` states the refusal and how a published library joins the solution as a resource): create it where § 1.5 item 2 places libraries and consume it as a package. A library the Library layout answer folds gets no project: its workflows are authored in its consumer, at their source paths when the run keeps the source's shape ([source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md)) and in a folder named after the library otherwise, the consumer invokes each public one as a workflow file with the arguments of the library genome's Interface, its targets join the consumer's Object Repository and its packages the consumer's manifest, and § 1.5 does not apply to it.
<!--skill-flavor:process-genome-test-project:start-->
3. **All test components share one test project** ([genome-reading-guide.md § Two Levels](genome-reading-guide.md) rule 1). Create `<ProcessName>.Tests` once through `uipath-rpa`'s test-project creation step, with the Test project template answer, register it once, and give every test component the same `PROJECT_DIR`: its test cases and data files in a folder named after it (`<ComponentSlug>/`), or at their source objects' paths when the run keeps the source's shape ([source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md)), plus, without the template, a shared `Config/` folder for the configuration workflow.
<!--skill-flavor:process-genome-test-project:end-->
4. Verify with `uip solution projects list --output json` after all components exist (libraries do not appear in it).

If the genome's Deployment section says "independent packages", skip the solution and treat each component as a standalone project.

**Split answers** (the split questions, one per flow): resolve them before creating anything, and create each consumer project chosen for the REFramework from its template — [transactional-execution-guide.md § Projects from the split answers](transactional-execution-guide.md).

### 1.5 Library components and their consumers

A component of type library is consumed by the other components as a package dependency, so it gates them (a library the Library layout answer folds is a folder of its consumer instead, § 1.4):

1. The library is built, validated and packed first with the owning skill's pack command, clearing the analyzer errors that skill lists. Where a fix touches what the genome settles, the genome's rule decides it: a credential, or an identifier read from an asset, follows § 2.2, credentials; more than 20 arguments become the options object of [genome-reading-guide.md § Interface](genome-reading-guide.md), an Interface deviation when the genome lacks it; a literal `idx` above 2 is replaced per [selector-translation-guide.md](selector-translation-guide.md) rule 7, and an index none of its replacements removes is a rule that cannot be satisfied. A rule that cannot be satisfied is decided with the user and recorded. The public Interface is read against these rules and the owning skill's library rules before the library's first workflow is written, so a rename they force is an Interface deviation the consumers are written against, not one found at pack.
2. **Library placement follows the Library location answer.** The local feed the packs write to and the one `NuGet.config` that names it serve every process and library of the build. Consumers install the dependency from that feed through the owning skill's sources file for install and build; the solution pack takes `uipath-solution`'s sources file.
3. Each library packs under a version the package cache does not hold yet, per the owning skill's same-version rule.
4. **Consumers call a library's activities directly**, in the steps that use them. A workflow wrapping one library activity adds a file and an invoke to every call and nothing else, so none is written. A consumer workflow that calls a library activity is written once the package is installed in the consumer, with the activity names and namespace item 6 returns and the arguments of the library genome's Interface ([genome-reading-guide.md § Interface](genome-reading-guide.md)); the consumer's other workflows need not wait for the pack. Do not build an interface-only stand-in package unless the user asks for one, and delete it afterwards.
5. **What the library keeps private is a contract with its consumers, not tidiness.** A workflow marked private does not surface as an activity in the consuming project, and a consumer cannot reach into the package to invoke a workflow file by path — the only way in is a public workflow's activity. The genome settles which is which before the library is packed: a workflow is public when a consumer's steps, handoffs or error handling invoke it, private otherwise. Internals built for the library's own use (the composite-pattern helpers) are private, unless a consumer's own steps repeat the pattern on the library's application: that helper is public and the consumer invokes it, since a copy drifts (item 7). A helper a consumer calls stays public however internal it looks — a clean-up a test case's exception handler calls is the common case.
6. **Read the consuming project's activity names from the installed package, never from the library's folder layout.** A public workflow surfaces under a class name the package derives from the project name and the workflow's folder, and the consumer's XAML needs that name and its namespace declaration. Take the names, the namespace and the argument types from the owning skill's library-consumption steps, run in the *consumer* project once the package is installed. The packed surface also lists the library's private helpers (marked not browsable) — a consumer never invokes those.
7. **A library that calls another library's public workflow depends on that library's package.** It installs the package like any consumer (items 2 and 6) and is packed after it. A private copy of the workflow inside the calling library drifts from the original on the first change to either.
8. **A common library, whether the Shared steps answer creates it or the genome's shared-behaviour component names it, is named `<Solution>.Common`.** Before a process drops its own helpers, a run shows the library gives the same results on the same inputs. The processes and the library pin one version of a shared activities package.

## Phase 2 — Build

### 2.1 Plan skill groups

Component genome: read Build With top to bottom; merge consecutive rows with the same skill into one group. Process genome: one group per component in Components order, unless a Handoffs row requires a consumer to exist before its producer (queue definitions, entry points) — then reorder only as far as needed and say so. Test components remain separate groups but all target the single test project; without the Test Automation Framework template, the shared `Config/` workflow is built with the first test group. A split that materialises projects plans its groups per project, each step on the surface it lands on ([transactional-execution-guide.md § Groups and surfaces](transactional-execution-guide.md)).

Plan large groups in parts per [execution-parts-guide.md § What a Build Adds](execution-parts-guide.md) item 1a.

Report plan before building:

```
Genome build plan:
  Group 1: Steps 1, 3, 4 → uipath-rpa (3 steps)
    Parts (large group, sized by context): A — skeleton and stubs, steps 1 and 3 → B — step 4, verification, gate, exits and criteria; link and build after each
  Group 2: Step 2 → uipath-agents (1 step)
  Split: option A (as-is) — Group 1 on the REFramework (direct): once per run: 1; per item: 3, 4; at the end: none
  Total: 2 groups, 4 steps
```

### 2.2 Build each group

For each group, in order:

1. **Assemble context:** Workflow steps (with substeps) for this group, Business Rules and Error Handling entries under those steps plus General/Global, Platform Dependencies touched, Interface, Configuration Answers, Overview, and for process genomes the Handoffs rows where this component is From or To.
2. **Invoke the owning skill** named in the Build With / Components row and follow its workflow end to end. Pass `PROJECT_DIR` so it reuses the project from 1.4 instead of creating one. When the skill is not installed, build from the genome text using the CLI directly, mark the group "built without <skill>", and continue.
   - **The owning skill's contract is mandatory.** Perform its mandatory reads — its authoring rules, the installed activity package's core guide and per-activity docs — and its own validation loop: validate per file and build per project exactly as the skill prescribes. The contract is not optional because the group is large or delegated: a subagent that builds a group receives the same instruction and reports which reads it performed.
   - **Workflows are authored as files through the owning skill's journey, not generated.** Scripts in the working folder may loop over CLI commands, write data files no CLI owns, and run checks; no script or shell command writes or edits a `.xaml` or `.cs` in a project, a one-line replace included.
   - **Activity XML comes from the skill's discovery commands and the installed package's per-activity docs, never from memory.** A per-activity doc that [package-doc-errata-guide.md](package-doc-errata-guide.md) corrects is read together with its row there, which decides while the installed text is uncorrected.
   - **The two sources answer different questions, and a build needs both for every activity kind it uses.** The default-XAML command settles the **shape**: the class the designer actually drops, its namespace prefix, which properties are attributes and which are child elements, the version attribute, whether the activity is generic or not. The package's per-activity doc settles the **values**: which property to set when several look alike, and how the value is encoded. A fragment can be shaped correctly and still be inert because a property's value is encoded the way a *different* activity encodes it — two activities that both take keystrokes can require two different encodings of the same key, and the one that is wrong fails at run time, not at `validate`. Neither source substitutes for the other, and two things are weaker than both: a snippet in any skill's card, since cards go stale and the installed package does not, and another file of the build, since an inert value validates as cleanly as a working one.
   - **Do this once per activity kind, before the first file using it is written.** A wrong shape repeats in every file using the activity, and each copy validates, builds and packs cleanly. List the activity kinds the group will use, fetch the default XAML and read the per-activity doc for each, and record the list in the group report — an activity kind that appears in the output but not in that list was written from memory.
   - **Names and texts in a project are written for the developer who maintains it, who has no working folder.** Messages and log texts the source gives keep its wording ([source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md); a refactor: [refactor-guide.md § The contract](refactor-guide.md)), and so does a step name the source's author wrote where the run keeps the source's names. What the build writes itself — the display names it gives, annotations, verify titles and message formats — says in the business's words what a step does and, where its name does not show it, why. It cites no record of the run — a brief ruling, a finding, a defect-index row, a deviation, plan or part number — and no source object id, line or step number: an engineer reading the workflow cannot follow them. A step that exists because of a ruling, a source defect or a platform limit carries an annotation stating that reason itself (`Stops instead of posting again: the source posted a second time after a timeout and duplicated the invoice.`), never the citation. The links back stay outside every project — the correspondence and parity tables and the checkpoint maps in the hand-off folder ([completion-report-guide.md](completion-report-guide.md)), the ledgers in the working folder (`migration/` in a migration) — for whoever needs them. One text names its source by design: an Object Repository element's description, for whoever heals the target ([ui-target-migration-guide.md](ui-target-migration-guide.md) rule 2), still with no record of the run.
   - **UI checks and failure handling — every build, not only migrations:** [ui-verification-guide.md](ui-verification-guide.md).
   - **Credentials.** Each credential asset (one per account) and Secret asset the genome names is declared as a solution resource. The build reads each one inside the scope that consumes it — the application card whose sign-in form the value is typed into, or the request that sends it — as the owning skill's analyzer rules for secrets require, and a local run, which has no Orchestrator folder to read the asset from, gives the read its folder from a configuration value left empty in the published package. Identifiers that are not secrets are Text assets ([genome-reading-guide.md § Platform Dependencies](genome-reading-guide.md)); in a migration the asset names come from the source's accounts ([source-migration-guide.md § Credentials](source-migration-guide.md)).
   - **Migration groups.** When the run is a migration (an export was resolved in 1.3), the group's UI activities are built without targets and receive Object Repository targets in 2.2b; the placeholder-selector stub pattern applies only when no export and no live application exist. Before authoring, classify every UI step of an extracted genome against [composite-interactions-guide.md](composite-interactions-guide.md) (substep wording plus the per-control `actions` in the derived catalog), build each pattern of several activities once as a shared helper workflow per [ui-target-migration-guide.md § Object Repository identity](ui-target-migration-guide.md), read the owning skill's control-interaction guidance for the controls involved as that skill mandates, and list the classified steps, their patterns and the helpers in the group plan. Verification is built per [ui-verification-guide.md](ui-verification-guide.md).
   - **A `uipath-maestro-case` component whose Interface names a Case Management SDD as its build input** is built by invoking `uipath-maestro-case` with the SDD's file path — its basename contains `sdd`, so that skill builds from it instead of handing off to design. Inside a process genome it runs from the component's own working folder (`<SOLUTION_DIR>/<COMPONENT_FOLDER>/`, one per case component, so its `./sdd.md` copy and `tasks/` never collide with another case's) with the solution directory, stating that the solution already exists: the case project is created inside it, and solution registration stays with the lead agent (execution-parts-guide.md § What a Build Adds item 5). The case is never redesigned from the genome's steps. A component genome runs it from the genome's folder, and it creates the solution itself.
   - **Test components:** [test-execution-guide.md](test-execution-guide.md).
   - **REFramework chosen for a consumer project:** build it on the template's surfaces, and re-derive an alternative unit of work, per [transactional-execution-guide.md § REFramework at build](transactional-execution-guide.md).
3. **Verify the group:** every file the group needed exists, the owning skill's validate command passed, no unresolved errors remain. When the group produced Object Repository targets, read their definitions back and write their live checks per [ui-target-migration-guide.md § Verifying targets](ui-target-migration-guide.md) before reporting the group complete; the live healing pass follows once all UI groups are linked (§ 2.2b). A consumer project on the REFramework also reports its customisation checklist and the exits it exercised ([transactional-execution-guide.md § REFramework at build](transactional-execution-guide.md)).
4. **Report and advance without pausing.** The group report goes into the project's report in the hand-off folder ([completion-report-guide.md](completion-report-guide.md)); the message is:

```
Group 1/2 complete — uipath-rpa
  Files: Main.xaml, ProcessInvoice.xaml
  Validation: passed
Advancing to group 2/2…
```

Never stop between groups to ask whether to continue.

### 2.2a Parts, ledgers and resuming

A group built in parts, a build run through subagents, and a pause or a compaction mid-build follow [execution-parts-guide.md](execution-parts-guide.md): one owner per project, the ledger and its skeleton, read plans, progress written through, the run brief and its rulings, and the part report checked against the disk.

### 2.2b Migrate UI targets (extracted genomes)

The UI targets follow the three phases of [ui-target-migration-guide.md](ui-target-migration-guide.md) rule 4. Before the first UI group, run [source-migration-guide.md § Migration preflight](source-migration-guide.md) with the export resolved in 1.3: the catalogs into the build's working folder, the genome's step tables checked against the export, and the target spec, with exploration and the contract probe on a reachable application (its step 3a). The UI groups are the offline migration: each registers and links its files' targets from the target spec with the run's target tool, per [ui-target-migration-guide.md](ui-target-migration-guide.md) § UI targets and § Object Repository identity and [composite-interactions-guide.md](composite-interactions-guide.md), and writes their live checks per its § Verifying targets. Once every UI group is linked, a reachable application gets the live healing pass ([live-application-guide.md § Live healing pass](live-application-guide.md)). Report screens, elements, confidence counts, labels, fragile targets (positional indexes, tag-only) and the live checks left open. Placeholder stubs remain only for activities the catalog cannot cover, and the report lists them.

### 2.2c Migrate test data (extracted genomes)

After the test project exists, migrate each data set from the derived data catalog where the source kept it — its records in the project's test-data entity, or its test case's variation file — per [test-execution-guide.md § Test data](test-execution-guide.md) and rules 1–2 there (scripted mapping, frozen argument set of a variation file) and the credential asset per account ([source-migration-guide.md § Credentials](source-migration-guide.md)), and report as that section states.

### 2.3 Wire handoffs

Component genome: after all groups, connect steps built by different skills (a coded workflow invoking a XAML workflow, a shared state file, a main entry point calling the others). Edit, then re-validate touched files.

Process genome: implement every Handoffs row with the named mechanism: queue item (queue declared as a solution resource), start job, Flow or BPMN invoke of a sibling component, Action Center task, file drop. Confirm each component's Interface matches the data the Handoffs row passes.

<!--skill-flavor:process-genome-pack:start-->
Then refresh the solution's resources and pack it per the `uipath-solution` skill; on failure follow that skill's diagnosis. Without a tenant login, resource refresh, publish and deploy are out of reach; that skill's pack dry run, resolving packages from the local feed when libraries come from it, still proves the solution packs and is the last local gate, and a failure there takes the same diagnosis as pack.
<!--skill-flavor:process-genome-pack:end-->

A build binds a queue, asset or bucket only where an activity names it literally, so one whose name a workflow reads from configuration or an argument, as the REFramework template reads its queue's, can be missing from the solution's resources once they are synced: compare the solution's resource list with Platform Dependencies and the store answers, and declare each missing resource through the `uipath-solution` skill.

## Phase 3 — Validate

### 3.1 Acceptance criteria

For every criterion (component criteria first, then process criteria), cited by its number in its genome:

| Verdict | Meaning |
|---|---|
| Met | Code directly implements behaviour and a local run confirmed it; cite file and location |
| Met (static) | Code directly implements behaviour and validates, but the run needs a system not reachable in this session (live tenant, credentials); cite file and location and name the blocker once, in the report header |
| Partial | Implemented with a gap; name the gap |
| Not Met | Nothing addresses it |
| Not Verifiable | Nothing the build contains can address it before a run (a manual act, the target environment's own setup); never given to a criterion the code implements |

A verdict judges the build against the criterion. A criterion that states behaviour (something is created, typed, moved, written) is Met (static) when the code builds it. A criterion that states a confirmed outcome ("is checked", "equals", "shows", "is found") needs an assertion that fails on a mismatch; without one it is Partial, naming the missing assertion. A criterion built as the source does it, which the source's own data or defect fails on a live run, is Met (static), and the completion report lists it among the live failures to expect, with the reason.

Where the owning skill offers a local run (`uip rpa run`, `uip maestro flow debug`, `uip codedagent run`, …) and the criterion is testable locally, run it and record the result instead of a static verdict. A run against the application the Live application answer names goes only as far as the Healing pass answer allows ([live-application-guide.md § Runs](live-application-guide.md)); a criterion it leaves unrun keeps its static verdict, with that answer as its blocker.

### 3.2 Report

```
Acceptance Criteria
  ✓ 1. Given an invoice PDF, extracts vendor_name, … — Met (ProcessInvoice.xaml)
  ⚠ 2. When confidence < 70%, creates a validation task — Partial: task created, priority not set
  ✗ 3. Duplicate invoice is skipped — Not Met
  ○ 4. Sends notification on failure — Not Verifiable (SMTP)
Result: 5/8 met, 1 partial, 1 not met, 1 not verifiable
```

For each Partial or Not Met: state what is missing and the concrete change. Fix them when the user asks, or immediately in autonomous runs, then re-validate the touched files and re-run every local run and test that exercises them: a fix to a shared workflow can break a criterion already Met. A fix that turns a Met criterion into Partial or Not Met is undone before another fix is tried, and the report gives the final build's verdicts.

### 3.3 Completion report — the hand-off

The hand-off folder and its README: [completion-report-guide.md](completion-report-guide.md).

### 3.4 Open items for the engineer

Execution ends by writing, in the hand-off folder ([completion-report-guide.md](completion-report-guide.md)), what the target environment needs before the automation runs there — one file per project plus the solution's — whenever it needs at least one setup step: [open-items-guide.md](open-items-guide.md).

### 3.5 Integration review

After every project of a process genome is built, and before the report, a reviewer who built none of them reads the projects against each other, read-only: each Handoffs row's mechanism and names, queue names, the argument contract at every invoke (names, directions, types) and the configuration keys and assets the projects share. It writes `integration-check.md` in the hand-off folder ([completion-report-guide.md](completion-report-guide.md)): each finding with the projects and files it spans, its severity, and what became of it. A finding is fixed by the project's owner and the touched files re-validated, or recorded unresolved in `integration-check.md` and the README's Expected failures; none is dropped. The README counts the findings and links the file.

## Anti-patterns

1. **Building before the configuration questions are answered.** Produces placeholder values the user must hunt down later. Variants: skipping 1.3 because the genome's section is a stub (scaffolding questions are asked regardless); taking a "(Recommended)" or discovered value without asking outside an autonomous run; declaring the run autonomous because nobody replied yet, or because it runs in a subagent; letting the init command pick target framework and package versions the user was never asked about.
2. **Pausing between skill groups.** "Shall I continue with the RPA part?" is wrong. Advance.
3. **One project per skill group.** Component genome is one project. Process genome is one solution with one project per non-test component, a library the Library layout answer folds excepted, and exactly one test project holding every test component — never one test project per business area.
4. **Reordering Build With or Components** except for the handoff-dependency case in 2.1.
5. **Adding features the genome does not name, or dropping steps it does.** Gaps go to the user, not into improvised code. A refactor adds only what its answers ask for and drops only what they retire or fold ([refactor-guide.md](refactor-guide.md)).
6. **Editing the genome during execution.** It is read-only.
7. **Skipping acceptance validation** because "everything compiled". Criteria are the definition of done.
8. **Building past the owning skill.** Activity XML written from memory, or a subagent dispatched without the skill's mandatory reads and authoring journey (2.2 step 2).
9. **Skipping the export question, or deriving nothing because no catalog sat beside the genome**, and so shipping placeholder targets or generated test rows for a reachable export (1.3, 2.2b, 2.2c). Every other migration mistake — naive composite translation, per-step Object Repository entries, Check activities instead of `VerifyOptions`, copied credentials — is prohibited in the anti-patterns of [source-migration-guide.md](source-migration-guide.md), [ui-target-migration-guide.md](ui-target-migration-guide.md), [ui-verification-guide.md](ui-verification-guide.md) and [test-execution-guide.md](test-execution-guide.md).
10. **Writing to a tenant the user did not ask for** — publishing or deploying a package, creating a queue, asset or trigger, or an entity the Data Fabric answer did not allow. The build is local; what the target environment needs goes into the open-items files (§ 3.4).
11. **Generating workflows by script.** Every fix goes into the generator and regenerates the project; regeneration after linking drops Object Repository links; template shapes bypass the discovery commands; reviewers must read the generator to judge the build (2.2 step 2).
12. **Ending with the report in the conversation only, or with the engineer's files spread across the working folder.** The genome and the build then travel without the answers, the decisions and what is left to check on the live application ([completion-report-guide.md](completion-report-guide.md)).

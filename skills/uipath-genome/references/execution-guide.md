# Execution Guide — build an automation from a genome

Genome says *what* to build; build skills know *how*. Execution reads genome, collects configuration answers, builds skill group by skill group through owning skills, wires pieces, checks result against acceptance criteria. Genome is read-only throughout: spec fixes are a separate authoring or extraction edit, then re-execution.

## Phase 1 — Parse and configure

### 1.1 Read the genome

Read whole file. Identify level from preamble comment (`component` or `process`). For a process genome, read every component genome linked in the Components table before anything else. A missing linked component file stops execution: report the missing path and ask the user to supply it — the one question about the source an executor asks.

Required sections (component): Overview, Target Applications, Build With, Workflow, Acceptance Criteria, Complexity. Optional (may be stubs): Platform Dependencies, Interface, Configuration Questions, Business Rules, Error Handling, Source Map. Genome missing a required section is malformed: report which section and stop.

### 1.2 Preflight discovery

Gather facts the 1.3 scaffolding questions are built from before asking anything. Discovery is silent; it never replaces the questions.

1. Run platform login status check; record what an expired session blocks (resource refresh, publish, deploy — local init, validate, build and pack still work).
2. Confirm runtime host and edit surface; record which target frameworks and expression languages they support.
3. For every skill named in Build With / Components, run that skill's discovery commands for installed packages; record activity packages and versions available to the authoring host. When a project already exists in the build location, also record its declared dependencies and versions from its manifest.
4. Determine candidate build location: the folder containing the genome file, never the current working directory when that is a different repository.
5. **Export check.** When the Source Map names a framework listed in [SKILL.md § Source Frameworks](../SKILL.md), read the export path and identity it records and check the export is where it says (manifest matches recorded identity). Record the outcome for the scaffolding question below; derive nothing yet — that is [source-migration-guide.md § Migration preflight](source-migration-guide.md), after the questions.

### 1.3 Configuration questions — never skipped

Ask before writing any code, creating any project, or installing any package. This step runs in every execution, including when the genome's Configuration Questions section is the stub line, because the scaffolding questions below do not come from the genome.

Two sources of questions, asked in this order:

**A. Genome questions** — every numbered question in the genome's Configuration Questions section. Absent only when that section is the stub line.

**B. Scaffolding questions** — always asked, once per project the genome will create (per component for a process genome, once for the single test project):

| Topic | Question | Options (first = Recommended) |
|---|---|---|
| Location | Where to create the project? | Folder next to genome (1.2 step 4); reuse existing project found there (only when one exists and matches the primary skill); another path |
| Target framework (RPA projects) | Which target framework? | The one the host supports and an existing project uses; alternatives the host supports |
| Expression language (RPA projects) | Which expression language? | C#; VB |
| Installed packages | Which activity packages and versions are installed where this automation will run (Studio / Robot / tenant feed)? | Set discovered in 1.2 step 3, listed by name and version; versions declared by the existing project; user provides the list (free text) |
| Package pinning | Pin the new project to those versions, or take the latest stable from the feed? | Pin to installed versions; latest stable |
| Runtime (non-RPA projects) | Owning skill's scaffold choices — runtime version, framework, template (Python version and agent framework, Node and SDK version, Flow or BPMN template) | Value the owning skill's init defaults to; alternatives it lists |
| Source export (extracted genomes only) | Where is the source export the Source Map names, for migrating UI targets and test data? | Recorded path when 1.2 step 5 found it there; another path (free text); no export available — build with live capture or placeholders and say so in the report |

Rules:

1. Group questions by topic (notifications, data sources, behaviour, environment, scaffolding).
2. For each question generate three concrete options. When the genome carries a default, or discovery produced a value, it is option one with "(Recommended)". Labels 1-5 words; header ≤ 12 characters.
3. Present with `AskUserQuestion`, at most four per batch; collect a batch before showing the next.
4. Record answers as a `Configuration Answers` list with a `Scaffolding` group; the project-creation step in 1.4 receives the scaffolding answers, and every later build step receives the answers relevant to it.
5. A default in the genome, a value found by discovery, a stub section, a "(Recommended)" option or a silent user never licenses skipping the question. Only the user answers it.
6. Process genomes: ask the process-level genome questions first, then each component's genome questions in Components order, then the scaffolding questions per project.

Autonomous runs — only when the user's current request explicitly says not to ask (for example "take the defaults", "run unattended"): take the default for every question, record "(default)" next to each answer, and list them in the completion report. Absence of a reply, a long-running session, or a subagent context is not authorisation to run autonomously; the executor asks and waits.

### 1.4 Resolve the target project

Every project is created with the `Scaffolding` answers from 1.3: location, target framework, expression language, package set and versions. Pass them to the owning skill's project-creation step as its init flags and dependency list; when the answer was "pin to installed versions", install exactly those versions and never let the init command's defaults override them.

**Component genome:**
1. When the Location answer is "reuse the existing project" (`project.json`, `project.uiproj`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.json`, `uipath.json` matching the genome's primary skill), use it.
2. Otherwise create the project through the owning skill's project-creation step (that skill knows the init command and its mandatory flags) at the chosen location. Name it after the genome.
3. Record `PROJECT_DIR`. Every build step targets it. One project for the whole component genome; XAML and coded files coexist in one RPA project.

**Process genome:**
1. Create or reuse a solution named after the process (`uip solution init "<NAME>" --output json` when none exists). Record `SOLUTION_DIR`.
2. Each non-test component becomes one project inside the solution folder: create it through its owning skill with that component's scaffolding answers. A **process** created inside the solution folder is registered in the `.uipx` by `init` itself (`solutionRegistration.Status: Registered`); a project created elsewhere is registered with `uip solution projects add <PROJECT_PATH> --output json`. A **library** is never a solution project — the CLI refuses it (`Status: Skipped`, "A library cannot be a project inside a solution — it is a reusable .nupkg"): create it in the solution folder anyway, consume it as a package (§ 1.5), and attach it to the solution only as a resource once it is published to the tenant (`uip solution resources add --source remote --kind Library --name <library>`, which needs a login).
3. **All test components share one test project** ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1). Create `<ProcessName>.Tests` once through `uipath-rpa`'s test-project creation step, register it once, and give every test component the same `PROJECT_DIR` with its own subfolder (`<ComponentSlug>/`) for test cases and data files, plus a shared `Config/` folder for the configuration workflow. The process genome's Project layout table names the folders; when an older genome lacks it, derive the folder names from the component names and say so.
4. Verify with `uip solution projects list --output json` after all components exist (libraries do not appear in it).

If the genome's Deployment section says "independent packages", skip the solution and treat each component as a standalone project.

### 1.5 Library components and their consumers

A component of type library is consumed by the other components as a package dependency, so it gates them:

1. The library is built, validated and packed first with the owning skill's pack command. Analyzer rules configured as Error fail `build` and `pack` but not per-file `validate`, so a project whose every file validates clean can still fail `build`; fix the workflow first and, only when a rule cannot be satisfied, decide with the user between lowering it and packing with the analyzer skipped, and record the decision. Rules met as Errors under the default configuration, with the fix that satisfied each: `ST-SEC-008` — a SecureString variable used outside the scope that declares it → declare it on the Sequence that directly contains the activity creating it and every activity consuming it; `ST-SEC-009` — a SecureString converted to text (`NetworkCredential(…).Password`) to feed a plain-string property → the value was an identifier, not a secret (an OAuth client or tenant id) and is read from a Text asset instead ([source-migration-guide.md](source-migration-guide.md) rule 4); `UI-REL-001` — a literal `idx` above 2 in a strict selector → the index is carried as a selector variable bound to an annotated workflow constant ([selector-translation-guide.md](selector-translation-guide.md) rule 7).
2. Consumers install the dependency from a local feed: a sources file listing the folder that holds the package, passed to install and build with the owning skill's sources flag. The feed folder lives outside every project. Two formats exist: `uip rpa packages install` / `uip rpa build --nuget-sources-config-path` take a JSON list `[{"Url": "C:/feed"}]` whose path must use forward slashes (a backslash path is rejected as an invalid JSON escape), while `uip solution pack --nuget-sources-config-path` takes an XML `NuGet.config`.
3. Repacking under the same version is ignored by the package cache: bump the library version, or clear the cached copy and reinstall, before rebuilding consumers.
4. Consumers can be authored before the library packs when the library genome's Interface carries the per-workflow argument tables ([genome-format-guide.md § Interface](genome-format-guide.md)); they are validated once the package exists. Isolate every library activity in one thin wrapper workflow per activity (its arguments mirror the library's Interface) and invoke the wrappers from the business workflows: until the package is installed only the wrappers fail validation (`Cannot create unknown type '{clr-namespace:<Namespace>;assembly=<Library>}<Activity>'`) and every other file validates; once it is installed, only the wrappers are touched — they take the activity names and namespace item 6 returns, and the business workflows never change. Do not build an interface-only stand-in package unless the user asks for one, and delete it afterwards.
5. **What the library keeps private is a contract with its consumers, not tidiness.** A workflow marked private does not surface as an activity in the consuming project, and a consumer cannot reach into the package to invoke a workflow file by path — the only way in is a public workflow's activity. The genome settles which is which before the library is packed: a workflow is public when a consumer's steps, handoffs or error handling invoke it, private otherwise. Internals built for the library's own use (the composite-pattern helpers) are private; a helper a consumer calls stays public however internal it looks — the evidence/screenshot workflow a test case's exception handler uses is the common case.
6. **Read the consuming project's activity names from the installed package, never from the library's folder layout.** A public workflow surfaces under a class name the package derives from the project name and the workflow's folder, and the consumer's XAML needs that name and its namespace declaration. Ask the owning skill's activity-discovery command in the *consumer* project for the real names once the package is installed, and build the invocations from what it returns. The packed surface itself — public workflows and their arguments — is listed by `uip rpa packages inspect`; check it before trusting a wrapper's argument list.

## Phase 2 — Build

### 2.1 Plan skill groups

Component genome: read Build With top to bottom; merge consecutive rows with the same skill into one group. Process genome: one group per component in Components order, unless a Handoffs row requires a consumer to exist before its producer (queue definitions, entry points) — then reorder only as far as needed and say so. Test components remain separate groups (one folder each) but all target the single test project; the shared `Config/` workflow is built with the first test group.

Report plan before building:

```
Genome build plan:
  Group 1: Steps 1, 3, 4 → uipath-rpa (3 steps)
  Group 2: Step 2 → uipath-agents (1 step)
  Total: 2 groups, 4 steps
```

### 2.2 Build each group

For each group, in order:

1. **Assemble context:** Workflow steps (with substeps) for this group, Business Rules and Error Handling entries under those steps plus General/Global, Platform Dependencies touched, Interface, Configuration Answers, Overview, and for process genomes the Handoffs rows where this component is From or To.
2. **Invoke the owning skill** named in the Build With / Components row and follow its workflow end to end. Pass `PROJECT_DIR` so it reuses the project from 1.4 instead of creating one. When the skill is not installed, build from the genome text using the CLI directly, mark the group "built without <skill>", and continue.
   - **The owning skill's contract is mandatory.** Perform its mandatory reads — its authoring rules, the installed activity package's core guide and per-activity docs — and its own validation loop: validate per file and build per project exactly as the skill prescribes. The contract is not optional because the group is large or delegated: a subagent that builds a group receives the same instruction and reports which reads it performed.
   - **Activity XML comes from the skill's discovery commands and the installed package's per-activity docs, never from memory** and never from a bespoke template generator whose templates were not derived from those commands. A code generator may repeat fragments that were obtained that way; it may not invent them.
   - **Migration groups.** When the run is a migration (an export was resolved in 1.3), the group's UI activities are built without targets and receive Object Repository targets in 2.2b; the placeholder-selector stub pattern applies only when no export and no live application exist. Before authoring, classify every UI step of an extracted genome against [source-migration-guide.md § Composite interactions](source-migration-guide.md) (substep wording plus the per-control `actions` in the derived catalog), build each pattern once as a shared helper workflow per § Object Repository identity there, read the owning skill's control-interaction guidance for the controls involved as that skill mandates, and list the classified steps, their patterns and the helpers in the group plan. Verification is built per [source-migration-guide.md § Verification](source-migration-guide.md): `VerifyOptions` on the acting activity, a Check activity only for a genuine branch.
   - **Test components** follow the owning skill's testing guidance for shape and registration (Given-When-Then, data variations, test-case registration in the project manifest). Genome-specific rules on top: a source loop over data rows becomes runner-level data variations with an execute-flag skip gate inside the case; the row carries only the fields that vary per scenario and constants live in the shared configuration workflow or argument defaults ([genome-format-guide.md § Interface](genome-format-guide.md) states the argument cap); every case ends with a verification of the source's success criterion, records a one-line result the business consumer can read, and captures a screenshot in its exception handler through the library's screenshot workflow when the genome has one.
3. **Verify the group:** every file the group needed exists, the owning skill's validate command passed, no unresolved errors remain. When the group produced Object Repository targets, verify them per [source-migration-guide.md § Verifying targets](source-migration-guide.md) before reporting the group complete — one element per interaction family against the live driver when the application is reachable, the offline read-back and `offline-unverified` label otherwise.
4. **Report and advance without pausing:**

```
Group 1/2 complete — uipath-rpa
  Files: Main.xaml, ProcessInvoice.xaml
  Validation: passed
Advancing to group 2/2…
```

Never stop between groups to ask whether to continue.

### 2.2a Delegating groups to subagents

Groups may be built by parallel subagents, one project per agent (test-component groups share one project and therefore one agent, or run sequentially), under these rules:

1. Every agent receives the owning skill's contract (2.2 step 2) and reports the reads it performed.
2. One authoring host serves all agents: every CLI call carries the project directory; a busy or locked host is retried once after a pause; per-file mutations (validate, link, register) of one project run sequentially — never two agents on one project. An agent that is stopped mid-way is replaced by one briefed with the state on disk (registered Object Repository entries, authored helpers) so it continues rather than restarts.
3. Object Repository linking follows the owning skill's target-attachment guidance (screen first, then elements; never two link commands on one file at once) and the ordering and verification rules in [source-migration-guide.md § UI targets](source-migration-guide.md) — link last, size batches by payload, check the file. The executor only orders the work.
4. Agents write each artifact as soon as it is complete (one workflow, one mapping file, one report) so an interrupted run loses one item, not a group; the orchestrator inventories the disk before relaunching and relaunches only what is missing.
5. Solution-level mutations (project registration, resources) are done by the orchestrator alone, after the agents finish.
6. Before packing, remove designer recovery copies (`~<Workflow>.xaml`) that the host leaves in a project after rewrites and linking; they would ship as workflows.

### 2.2b Migrate UI targets (extracted genomes)

Before the first UI group, run [source-migration-guide.md § Migration preflight](source-migration-guide.md) with the export resolved in 1.3 (catalogs and step map into the build's working folder). After the UI groups exist, build their Object Repository targets per that guide's § UI targets, § Object Repository identity and § Composite interactions, and verify them per § Verifying targets. Report screens, elements, confidence counts, fragile targets (positional indexes, semantic-only) and derived elements as the first healing-pass targets. Placeholder stubs remain only for activities the catalog cannot cover, and the report lists them.

### 2.2c Migrate test data (extracted genomes)

After the test project exists, fill the data files of each of its folders from the derived data catalog per [source-migration-guide.md § Test data](source-migration-guide.md) (rules 3–5 there: scripted mapping per folder, frozen argument set, credential asset per account) and report as that section states.

### 2.3 Wire handoffs

Component genome: after all groups, connect steps built by different skills (a coded workflow invoking a XAML workflow, a shared state file, a main entry point calling the others). Edit, then re-validate touched files.

Process genome: implement every Handoffs row with the named mechanism: queue item (queue declared as a solution resource), start job, Flow or BPMN invoke of a sibling component, Action Center task, file drop. Confirm each component's Interface matches the data the Handoffs row passes. Then `uip solution resources refresh --output json` and `uip solution pack --output json` per the `uipath-solution` skill; on failure follow that skill's diagnosis. Without a tenant login `resources refresh`, `publish` and `deploy` are out of reach; `uip solution pack --dry-run` (with `--nuget-sources-config-path` naming the local feed's `NuGet.config` when libraries come from it) still proves the solution packs and is the last local gate.

## Phase 3 — Validate

### 3.1 Acceptance criteria

For every criterion (component criteria first, then process criteria):

| Verdict | Meaning |
|---|---|
| Met | Code directly implements behaviour and a local run confirmed it; cite file and location |
| Met (static) | Code directly implements behaviour and validates, but the run needs a system not reachable in this session (live tenant, credentials); cite file and location and name the blocker once, in the report header |
| Partial | Implemented with a gap; name the gap |
| Not Met | Nothing addresses it |
| Not Verifiable | Needs live systems or runtime data |

Where the owning skill offers a local run (`uip rpa run`, `uip maestro flow debug`, `uip codedagent run`, …) and the criterion is testable locally, run it and record the result instead of a static verdict.

### 3.2 Report

```
Acceptance Criteria
  ✓ Given an invoice PDF, extracts vendor_name, … — Met (ProcessInvoice.xaml)
  ⚠ When confidence < 70%, creates a validation task — Partial: task created, priority not set
  ✗ Duplicate invoice is skipped — Not Met
  ○ Sends notification on failure — Not Verifiable (SMTP)
Result: 5/8 met, 1 partial, 1 not met, 1 not verifiable
```

For each Partial or Not Met: state what is missing and the concrete change. Fix them when the user asks, or immediately in autonomous runs, then re-validate.

### 3.3 Completion report

```
Genome execution complete.
Genome: <file>   Level: component | process
Project/Solution: <name> at <path>
Skills used: … (mandatory reads performed per skill)
Files created: <count>
Source export: <path> (<identity>) | none — live capture / placeholders
UI targets: <screens>/<elements> from the derived catalog (high/medium/low); <created>/<reused>/<parametrised>; <n> placeholders left
Test data: <files> filled from source rows, <n> credential assets declared (values to enter in Orchestrator)
Acceptance criteria: N/total met
Configuration answers: … (defaults marked)
Scaffolding: <target framework>, <expression language>, <package@version, …> (pinned | latest) per project
Gate: validate + build per project (errors / warnings), libraries packed to <feed>, solution pack --dry-run <verdict>; runs performed or "compile only — no reachable application"
Run: <the owning skill's run command for the entry point>
```

Extracted genomes add the healing-pass note: inferred targets are verified on the first run against the live application, and fixes go into the Object Repository element. Migrated test components add the checkpoint line per test case — `Checkpoints: <source> / <asserted> / <not asserted: reasons> / <added>` — and the path of the generated mapping tables ([source-migration-guide.md § Result parity](source-migration-guide.md)). The report does not claim results match the source; the tables make that comparison possible for whoever holds a source result.

## Anti-patterns

1. **Building before the configuration questions are answered.** Produces placeholder values the user must hunt down later. Variants: skipping 1.3 because the genome's section is a stub (scaffolding questions are asked regardless); taking a "(Recommended)" or discovered value without asking; declaring the run autonomous because nobody replied yet; letting the init command pick target framework and package versions the user was never asked about.
2. **Pausing between skill groups.** "Shall I continue with the RPA part?" is wrong. Advance.
3. **One project per skill group.** Component genome is one project. Process genome is one solution with one project per non-test component and exactly one test project holding every test component as a folder — never one test project per business area.
4. **Reordering Build With or Components** except for the handoff-dependency case in 2.1.
5. **Adding features the genome does not name, or dropping steps it does.** Gaps go to the user, not into improvised code.
6. **Editing the genome during execution.** It is read-only.
7. **Skipping acceptance validation** because "everything compiled". Criteria are the definition of done.
8. **Building past the owning skill.** Emitting activity XML from memory or from templates nobody derived from the skill's discovery commands and package docs, or dispatching subagents without the skill's mandatory reads (2.2 step 2).
9. **Skipping the export question, or deriving nothing because no catalog sat beside the genome**, and so shipping placeholder targets or generated test rows for a reachable export (1.3, 2.2b, 2.2c). Every other migration mistake — naive composite translation, per-step Object Repository entries, Check activities instead of `VerifyOptions`, copied credentials — is prohibited in [source-migration-guide.md § Anti-patterns](source-migration-guide.md).

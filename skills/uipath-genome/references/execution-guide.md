# Execution Guide — build an automation from a genome

The genome says *what* to build; the build skills know *how*. Execution reads the genome, collects configuration answers, builds skill group by skill group through the owning skills, wires the pieces, and checks the result against the acceptance criteria.

## Phase 1 — Parse and configure

### 1.1 Read the genome

Read the whole file. Identify the level from the preamble comment (`component` or `process`). For a process genome, read every component genome linked in the Components table before doing anything else. A linked component file that is missing stops execution: report the missing path and ask the user to supply it.

Required sections (component): Overview, Target Applications, Build With, Workflow, Acceptance Criteria, Complexity. Optional (may be stubs): Platform Dependencies, Interface, Configuration Questions, Business Rules, Error Handling, Source Map. A genome missing a required section is malformed: report which section and stop.

### 1.2 Preflight discovery

Before asking anything, gather the facts the scaffolding questions in 1.3 are built from. Discovery is silent; it never replaces the questions.

1. Run the platform login status check and record what an expired session blocks (resource refresh, publish, deploy — local init, validate, build and pack still work).
2. Confirm the runtime host and edit surface, and record which target frameworks and expression languages they support.
3. For every skill named in Build With / Components, run that skill's discovery commands for installed packages and record the activity packages and versions available to the authoring host. When a project already exists in the build location, also record its declared dependencies and versions from its manifest.
4. Determine the candidate build location: the folder that contains the genome file, never the current working directory when that is a different repository.
5. **Migration preflight.** When the Source Map names a framework listed in [SKILL.md § Source Frameworks](../SKILL.md), read the export path and identity it records and check the export is where it says (its manifest matches the recorded identity). Record the outcome for the scaffolding question below; do not derive anything yet.

### 1.3 Configuration questions — never skipped

Ask before writing any code, creating any project, or installing any package. This step runs in every execution, including when the genome's Configuration Questions section is the stub line, because the scaffolding questions below do not come from the genome.

Two sources of questions, asked in this order:

**A. Genome questions** — every numbered question in the genome's Configuration Questions section. Absent only when that section is the stub line.

**B. Scaffolding questions** — always asked, once per project the genome will create (per component for a process genome, once for the single test project):

| Topic | Question | Options (first = Recommended) |
|---|---|---|
| Location | Where to create the project? | Folder next to the genome (1.2 step 4); reuse the existing project found there (only when one exists and matches the primary skill); another path |
| Target framework (RPA projects) | Which target framework? | The one the host supports and an existing project uses; the alternatives the host supports |
| Expression language (RPA projects) | Which expression language? | C#; VB |
| Installed packages | Which activity packages and versions are installed where this automation will run (Studio / Robot / tenant feed)? | The set discovered in 1.2 step 3, listed by name and version; the versions declared by the existing project; user provides the list (free text) |
| Package pinning | Pin the new project to those versions, or take the latest stable from the feed? | Pin to the installed versions; latest stable |
| Runtime (non-RPA projects) | The owning skill's scaffold choices — runtime version, framework, template (Python version and agent framework, Node and SDK version, Flow or BPMN template) | The value the owning skill's init defaults to; the alternatives it lists |
| Source export (extracted genomes only) | Where is the source export the Source Map names, for migrating UI targets and test data? | The recorded path when 1.2 step 5 found it there; another path (free text); no export available — build with live capture or placeholders and say so in the report |

Rules:

1. Group questions by topic (notifications, data sources, behaviour, environment, scaffolding).
2. For each question generate three concrete options. When the genome carries a default, or discovery produced a value, it is option one with "(Recommended)". Labels 1-5 words; header ≤ 12 characters.
3. Present with `AskUserQuestion`, at most four per batch; collect a batch before showing the next.
4. Record answers as a `Configuration Answers` list with a `Scaffolding` group; the project-creation step in 1.4 receives the scaffolding answers, and every later build step receives the answers relevant to it.
5. A default in the genome, a value found by discovery, or a "(Recommended)" option never licenses skipping the question. Only the user answers it.
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
2. Each non-test component becomes one project inside the solution: create it through its owning skill with that component's scaffolding answers, then register it with `uip solution projects add <PROJECT_PATH> --output json`.
3. **All test components share one test project.** Create `<ProcessName>.Tests` once through `uipath-rpa`'s test-project creation step, register it once, and give every test component the same `PROJECT_DIR` with its own subfolder (`<ComponentSlug>/`) for test cases and data files, plus a shared `Config/` folder for the configuration workflow. The process genome's Project layout table names the folders; when an older genome lacks it, derive the folder names from the component names and say so. Never create one test project per component.
4. Verify with `uip solution projects list --output json` after all components exist.

If the genome's Deployment section says "independent packages", skip the solution and treat each component as a standalone project.

### 1.5 Library components and their consumers

A component of type library is consumed by the other components as a package dependency, so it gates them:

1. The library is built, validated and packed first (the owning skill's pack command; when analyzer rules configured as Error block the pack, decide with the user between lowering them and packing with the analyzer skipped, and record the decision).
2. Consumers install the dependency from a local feed: a sources file listing the folder that holds the package, passed to install and build with the owning skill's sources flag. The feed folder lives outside every project.
3. Repacking under the same version is ignored by the package cache: bump the library version, or clear the cached copy and reinstall, before rebuilding consumers.
4. Consumers can be authored before the library packs when the library genome's Interface carries the per-workflow argument tables ([genome-format-guide.md § Interface](genome-format-guide.md)); they are validated once the package exists. Do not build an interface-only stand-in package unless the user asks for one, and delete it afterwards.

## Phase 2 — Build

### 2.1 Plan skill groups

Component genome: read Build With top to bottom; merge consecutive rows with the same skill into one group. Process genome: one group per component in Components order, unless a Handoffs row requires a consumer to exist before its producer (queue definitions, entry points) — then reorder only as far as needed and say so. Test components remain separate groups (one folder each) but all target the single test project; the shared `Config/` workflow is built with the first test group.

Report the plan before building:

```
Genome build plan:
  Group 1: Steps 1, 3, 4 → uipath-rpa (3 steps)
  Group 2: Step 2 → uipath-agents (1 step)
  Total: 2 groups, 4 steps
```

### 2.2 Build each group

For each group, in order:

1. **Assemble context:** the Workflow steps (with substeps) for this group, Business Rules and Error Handling entries under those steps plus General/Global, Platform Dependencies touched, Interface, Configuration Answers, the Overview, and for process genomes the Handoffs rows where this component is From or To.
2. **Invoke the owning skill** named in the Build With / Components row and follow its workflow end to end, including its mandatory reads and its own validation loop. Pass `PROJECT_DIR` so it reuses the project from 1.4 instead of creating one. When the skill is not installed, build from the genome text using the CLI directly, mark the group "built without <skill>", and continue.
   - The skill's contract is not optional because the group is large or delegated: a subagent that builds a group receives the same instruction to invoke the skill and read what it mandates, and reports which reads it performed.
   - Activity XML comes from the skill's discovery commands and the installed package's per-activity docs, never from memory. A code generator may repeat fragments that were obtained that way; it may not invent them.
   - When the run is a migration (an export was resolved in 1.3), the group's UI activities are built without targets and receive Object Repository targets in 2.2b; the placeholder-selector stub pattern applies only when no export and no live application exist.
   - **Composite source steps expand before authoring, into shared helpers.** For an extracted genome, classify every UI step against [source-migration-guide.md § Composite interactions](source-migration-guide.md) using the substep wording and the per-control `actions` in the derived catalog: type-ahead picks, option lists, menu paths, table-row-by-content, keystrokes, coordinate clicks. Each pattern is built **once** as a reusable helper workflow parametrised by field label and value, and every step invokes it — never the nearest single activity, and never the pattern's activities copied per step ([source-migration-guide.md § Object Repository identity](source-migration-guide.md)). Read the owning skill's control-interaction guidance for the controls involved (option lists, tables, date inputs) as that skill mandates before writing them. List the classified steps, their patterns and the helpers in the group plan.
   - **Test components** follow the owning skill's testing guidance for shape and registration (Given-When-Then, data variations, test-case registration in the project manifest). Genome-specific rules on top: a source loop over data rows becomes runner-level data variations with an execute-flag skip gate inside the case; the row carries only fields that vary per scenario (workflows are capped by an analyzer rule at about 20 arguments; constants live in a shared configuration workflow or argument defaults); every case ends with a verification of the source's success criterion, records a one-line result the business consumer can read, and captures a screenshot in its exception handler through the library's screenshot workflow when the genome has one.
   - **Verification is a property of the acting activity.** A pattern's verify sub-step is built as `VerifyOptions` on the Click / Type Into / Hover / Keyboard Shortcuts that performs the step — a separate Check Element / Check App State activity is only for a genuine branch, and costs a guessed target every time it is not ([source-migration-guide.md § Verification](source-migration-guide.md)). A UI group that emits Check activities and no `VerifyOptions` has taken the wrong route.
3. **Verify the group:** every file the group needed exists, the owning skill's validate command passed, no unresolved errors remain.
   - **When the group produced Object Repository targets, verify them before reporting the group complete.** Application reachable: one representative element per interaction family goes through the owning skill's live selector tools per [source-migration-guide.md § Verifying targets](source-migration-guide.md) — the driver's own default shape, the node's real attribute list, uniqueness — and the derivation rule that produced the family is corrected before the rest of the family is written back. Application not reachable: read the definitions back against [selector-translation-guide.md § Checking a definition](selector-translation-guide.md) (a throwaway script for the run is fine when there are hundreds), fix what fails, and label every element `offline-unverified`. A structural pass is a floor, not a proof — only the live driver knows whether a selector matches the screen.
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

1. Every agent receives the owning skill's contract (invoke it, perform its mandatory reads) and reports the reads it performed.
2. One authoring host serves all agents: every CLI call carries the project directory; a busy or locked host is retried once after a pause; per-file mutations (validate, link, register) of one project run sequentially — never two agents on one project.
3. Object Repository linking follows the owning skill's target-attachment guidance (screen first, then elements; never two link commands on one file at once; batch large element lists); the executor only orders the work.
4. Agents write each artifact as soon as it is complete (one workflow, one mapping file, one report) so an interrupted run loses one item, not a group; the orchestrator inventories the disk before relaunching and relaunches only what is missing.
5. Solution-level mutations (project registration, resources) are done by the orchestrator alone, after the agents finish.
6. Before packing, remove designer recovery copies (`~<Workflow>.xaml`) that the host leaves in a project after rewrites; they would ship as workflows.

### 2.2b Migrate UI targets (extracted genomes)

Before the first UI group, derive the catalogs from the export resolved in 1.3 into the build's working folder (`<solution or project>/migration/source/`) with the source guide's script — target catalog, data catalog, process inventory — and the step map with `scripts/genome-step-map.py <genome.md> --processes <the derived process inventory> --recordsets <the derived recordset list> --out <that folder>` ([source-migration-guide.md § Migration preflight](source-migration-guide.md)). After the UI groups exist, build their Object Repository targets from the target catalog per [source-migration-guide.md § UI targets](source-migration-guide.md): map every UI activity to a source control, derive the selector with the source guide's translation table, find or create screens and elements through the owning skill's Object Repository CLI — one element per node, never per step, window or activity type (§ Object Repository identity) — link, validate. Every element is labelled `INFERRED (<confidence>)`, and when the application is reachable one element per interaction family is verified against the live driver before the family is written back ([source-migration-guide.md § Verifying targets](source-migration-guide.md)). Composite steps also receive their derived elements (suggestion entries, menu levels, option rows, matched cells) built from the anchor control and the matched text — never with an identifier borrowed from another catalog control — labelled `derived from <control> — <pattern>`. Report screens, elements, confidence counts, the fragile targets (positional indexes, semantic-only) and the derived elements as the first healing-pass targets. Placeholder stubs remain only for activities the catalog cannot cover, and the report lists them.

### 2.2c Migrate test data (extracted genomes)

After the test project exists, fill the data files of each of its folders from the derived data catalog per [source-migration-guide.md § Test data](source-migration-guide.md): one mapping file per folder (test component), coverage check, migration, one rebuild of the project. Account user names become credential asset names plus environment URLs per row; one credential asset per account is declared as a solution resource; secrets are never written. Report coverage, kept defaults, unmapped source values, and the quirks and stale values carried over.

### 2.3 Wire handoffs

Component genome: after all groups, connect steps built by different skills (a coded workflow invoking a XAML workflow, a shared state file, a main entry point calling the others). Edit, then re-validate the touched files.

Process genome: implement every Handoffs row with the named mechanism: queue item (queue declared as a solution resource), start job, Flow or BPMN invoke of a sibling component, Action Center task, file drop. Confirm each component's Interface matches the data the Handoffs row passes. Then `uip solution resources refresh --output json` and `uip solution pack --output json` per the `uipath-solution` skill; on failure follow that skill's diagnosis.

## Phase 3 — Validate

### 3.1 Acceptance criteria

For every criterion (component criteria first, then process criteria):

| Verdict | Meaning |
|---|---|
| Met | Code directly implements the behaviour and a local run confirmed it; cite file and location |
| Met (static) | Code directly implements the behaviour and validates, but the run needs a system that is not reachable in this session (live tenant, credentials); cite file and location and name the blocker once, in the report header |
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
Run: <the owning skill's run command for the entry point>
```

Extracted genomes add the healing-pass note: inferred targets are verified on the first run against the live application, and fixes go into the Object Repository element.

## Anti-patterns

1. **Building before the configuration questions are answered.** Produces placeholder values the user has to hunt down later. Variants: skipping 1.3 because the genome's section is a stub (the scaffolding questions are asked regardless); taking a "(Recommended)" or discovered value without asking; declaring the run autonomous because nobody replied yet; letting the init command pick target framework and package versions the user was never asked about.
2. **Pausing between skill groups.** "Shall I continue with the RPA part?" is wrong. Advance.
3. **One project per skill group.** A component genome is one project. A process genome is one solution with one project per non-test component and exactly one test project holding every test component as a folder — never one test project per business area.
4. **Reordering Build With or Components** except for the handoff-dependency case in 2.1.
5. **Adding features the genome does not name, or dropping steps it does.** Gaps go to the user, not into improvised code.
6. **Editing the genome during execution.** It is read-only. Fixes to the spec are a separate authoring/extraction edit followed by re-execution.
7. **Skipping acceptance validation** because "everything compiled". The criteria are the definition of done.
8. **Shipping placeholder targets or generated test rows when the Source Map names an export that is reachable.** Both are migrated by default (2.2b, 2.2c) from catalogs derived at execution; skipping the export question, or deriving nothing because no catalog sat beside the genome, is the failure.
12. **Registering Object Repository entries per step, per source window or per activity type**, or copying a composite pattern's activities into every step instead of one helper workflow. Find before create; one element per node (§ Object Repository identity in the migration guide).
9. **Building past the owning skill.** Emitting activity XML from memory or from templates nobody derived from the skill's discovery commands and package docs, or dispatching subagents without the skill's mandatory reads.
10. **Copying credentials into data files, or flattening every scenario onto one login.** The asset name and environment per row are data; the secret is not.
11. **Translating a composite source step into the nearest single activity.** A type-ahead pick is not type-then-click-the-first-entry, a custom list is not a native select, a menu path is not one click, a found row is not a stored integer. Expand per the migration guide's pattern table, with the verify sub-step.

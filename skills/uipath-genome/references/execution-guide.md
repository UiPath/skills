# Execution Guide — build an automation from a genome

The genome says *what* to build; the build skills know *how*. Execution reads the genome, collects configuration answers, builds skill group by skill group through the owning skills, wires the pieces, and checks the result against the acceptance criteria.

## Phase 1 — Parse and configure

### 1.1 Read the genome

Read the whole file. Identify the level from the preamble comment (`component` or `process`). For a process genome, read every component genome linked in the Components table before doing anything else. A linked component file that is missing stops execution: report the missing path and ask the user to supply it.

Required sections (component): Overview, Target Applications, Build With, Workflow, Acceptance Criteria, Complexity. Optional (may be stubs): Platform Dependencies, Interface, Configuration Questions, Business Rules, Error Handling, Source Map. A genome missing a required section is malformed: report which section and stop.

### 1.2 Configuration questions

Skip when the section is the stub line. Otherwise ask every question before writing any code:

1. Group questions by topic (notifications, data sources, behaviour, environment).
2. For each question generate three concrete options. When the genome carries a default, it is option one with "(Recommended)". Labels 1-5 words; header ≤ 12 characters.
3. Present with `AskUserQuestion`, at most four per batch; collect a batch before showing the next.
4. Record answers as a `Configuration Answers` list; every later build step receives the answers relevant to it.

Autonomous runs (user said not to ask, or no user available): take the default for every question, record "(default)" next to each answer, and list them in the completion report.

Process genomes: ask the process-level questions first, then each component's questions in Components order.

### 1.2b Preflight

Before creating anything: run the platform login status check and record what an expired session blocks (resource refresh, publish, deploy — local init, validate, build and pack still work); confirm the runtime host and edit surface to fix the target framework and expression language for every project; choose the build location. The build location defaults to the folder that contains the genome file, never to the current working directory when that is a different repository; say where you are building.

### 1.3 Resolve the target project

**Component genome:**
1. Look for an existing project in the working directory (`project.json`, `project.uiproj`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.json`, `uipath.json`). If one matches the genome's primary skill, confirm reuse with the user (autonomous: reuse).
2. Otherwise create the project through the owning skill's project-creation step (that skill knows the init command and its mandatory flags). Name it after the genome.
3. Record `PROJECT_DIR`. Every build step targets it. One project for the whole component genome; XAML and coded files coexist in one RPA project.

**Process genome:**
1. Create or reuse a solution named after the process (`uip solution init "<NAME>" --output json` when none exists). Record `SOLUTION_DIR`.
2. Each non-test component becomes one project inside the solution: create it through its owning skill, then register it with `uip solution projects add <PROJECT_PATH> --output json`.
3. **All test components share one test project.** Create `<ProcessName>.Tests` once through `uipath-rpa`'s test-project creation step, register it once, and give every test component the same `PROJECT_DIR` with its own subfolder (`<ComponentSlug>/`) for test cases and data files, plus a shared `Config/` folder for the configuration workflow. The process genome's Project layout table names the folders; when an older genome lacks it, derive the folder names from the component names and say so. Never create one test project per component.
4. Verify with `uip solution projects list --output json` after all components exist.

If the genome's Deployment section says "independent packages", skip the solution and treat each component as a standalone project.

### 1.4 Library components and their consumers

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
2. **Invoke the owning skill** named in the Build With / Components row and follow its workflow end to end, including its mandatory reads and its own validation loop. Pass `PROJECT_DIR` so it reuses the project from 1.3 instead of creating one. When the skill is not installed, build from the genome text using the CLI directly, mark the group "built without <skill>", and continue.
   - The skill's contract is not optional because the group is large or delegated: a subagent that builds a group receives the same instruction to invoke the skill and read what it mandates, and reports which reads it performed.
   - Activity XML comes from the skill's discovery commands and the installed package's per-activity docs, never from memory. A code generator may repeat fragments that were obtained that way; it may not invent them.
   - When a source target catalog exists (`source/targets.json`), the group's UI activities are built without targets and receive Object Repository targets in 2.2b; the placeholder-selector stub pattern applies only when no catalog and no live application exist.
   - **Composite source steps expand before authoring.** For an extracted genome, classify every UI step against [source-migration-guide.md § Composite interactions](source-migration-guide.md) using the substep wording and the per-control `actions` in the catalog: type-ahead picks, option lists, menu paths, table-row-by-content, keystrokes, coordinate clicks. Each becomes the pattern's activity sequence including its verify sub-step — never the nearest single activity. Read the owning skill's control-interaction guidance for the controls involved (option lists, tables, date inputs) as that skill mandates before writing them. List the classified steps and their patterns in the group plan.
   - **Test components** follow the owning skill's testing guidance for shape and registration (Given-When-Then, data variations, test-case registration in the project manifest). Genome-specific rules on top: a source loop over data rows becomes runner-level data variations with an execute-flag skip gate inside the case; the row carries only fields that vary per scenario (workflows are capped by an analyzer rule at about 20 arguments; constants live in a shared configuration workflow or argument defaults); every case ends with a verification of the source's success criterion, records a one-line result the business consumer can read, and captures a screenshot in its exception handler through the library's screenshot workflow when the genome has one.
3. **Verify the group:** every file the group needed exists, the owning skill's validate command passed, no unresolved errors remain.
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

After the UI groups exist, build their Object Repository targets from `source/targets.json` per [source-migration-guide.md § UI targets](source-migration-guide.md): map every UI activity to a source control, derive the selector with the source guide's translation table, create screens and elements through the owning skill's Object Repository CLI, link, validate. Every element is labelled `INFERRED (<confidence>)`. Composite steps also receive their derived elements (suggestion entries, menu levels, option rows, matched cells) built from the anchor control and the matched text, labelled `derived from <control> — <pattern>`. Report screens, elements, confidence counts, the fragile targets (positional indexes, semantic-only) and the derived elements as the first healing-pass targets. Placeholder stubs remain only for activities the catalog cannot cover, and the report lists them.

### 2.2c Migrate test data (extracted genomes)

After the test project exists, fill the data files of each of its folders from `source/test-data.json` per [source-migration-guide.md § Test data](source-migration-guide.md): one mapping file per folder (test component), coverage check, migration, one rebuild of the project. Account user names become credential asset names plus environment URLs per row; one credential asset per account is declared as a solution resource; secrets are never written. Report coverage, kept defaults, unmapped source values, and the quirks and stale values carried over.

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
UI targets: <screens>/<elements> from source catalog (high/medium/low), <n> placeholders left
Test data: <files> filled from source rows, <n> credential assets declared (values to enter in Orchestrator)
Acceptance criteria: N/total met
Configuration answers: … (defaults marked)
Run: <the owning skill's run command for the entry point>
```

Extracted genomes add the healing-pass note: inferred targets are verified on the first run against the live application, and fixes go into the Object Repository element.

## Anti-patterns

1. **Building before the configuration questions are answered.** Produces placeholder values the user has to hunt down later.
2. **Pausing between skill groups.** "Shall I continue with the RPA part?" is wrong. Advance.
3. **One project per skill group.** A component genome is one project. A process genome is one solution with one project per non-test component and exactly one test project holding every test component as a folder — never one test project per business area.
4. **Reordering Build With or Components** except for the handoff-dependency case in 2.1.
5. **Adding features the genome does not name, or dropping steps it does.** Gaps go to the user, not into improvised code.
6. **Editing the genome during execution.** It is read-only. Fixes to the spec are a separate authoring/extraction edit followed by re-execution.
7. **Skipping acceptance validation** because "everything compiled". The criteria are the definition of done.
8. **Shipping placeholder targets when the extraction produced a target catalog**, or generated test rows when it produced test data. Both are migrated by default (2.2b, 2.2c).
9. **Building past the owning skill.** Emitting activity XML from memory or from templates nobody derived from the skill's discovery commands and package docs, or dispatching subagents without the skill's mandatory reads.
10. **Copying credentials into data files, or flattening every scenario onto one login.** The asset name and environment per row are data; the secret is not.
11. **Translating a composite source step into the nearest single activity.** A type-ahead pick is not type-then-click-the-first-entry, a custom list is not a native select, a menu path is not one click, a found row is not a stored integer. Expand per the migration guide's pattern table, with the verify sub-step.

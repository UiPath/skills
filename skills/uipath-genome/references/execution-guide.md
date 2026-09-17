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

### 1.3 Resolve the target project

**Component genome:**
1. Look for an existing project in the working directory (`project.json`, `project.uiproj`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.json`, `uipath.json`). If one matches the genome's primary skill, confirm reuse with the user (autonomous: reuse).
2. Otherwise create the project through the owning skill's project-creation step (that skill knows the init command and its mandatory flags). Name it after the genome.
3. Record `PROJECT_DIR`. Every build step targets it. One project for the whole component genome; XAML and coded files coexist in one RPA project.

**Process genome:**
1. Create or reuse a solution named after the process (`uip solution init "<NAME>" --output json` when none exists). Record `SOLUTION_DIR`.
2. Each component becomes one project inside the solution: create it through its owning skill, then register it with `uip solution projects add <PROJECT_PATH> --output json`.
3. Verify with `uip solution projects list --output json` after all components exist.

If the genome's Deployment section says "independent packages", skip the solution and treat each component as a standalone project.

## Phase 2 — Build

### 2.1 Plan skill groups

Component genome: read Build With top to bottom; merge consecutive rows with the same skill into one group. Process genome: one group per component in Components order, unless a Handoffs row requires a consumer to exist before its producer (queue definitions, entry points) — then reorder only as far as needed and say so.

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
2. **Invoke the owning skill** named in the Build With / Components row and follow its workflow end to end, including its own validation loop. Pass `PROJECT_DIR` so it reuses the project from 1.3 instead of creating one. When the skill is not installed, build from the genome text using the CLI directly, mark the group "built without <skill>", and continue.
3. **Verify the group:** every file the group needed exists, the owning skill's validate command passed, no unresolved errors remain.
4. **Report and advance without pausing:**

```
Group 1/2 complete — uipath-rpa
  Files: Main.xaml, ProcessInvoice.xaml
  Validation: passed
Advancing to group 2/2…
```

Never stop between groups to ask whether to continue.

### 2.3 Wire handoffs

Component genome: after all groups, connect steps built by different skills (a coded workflow invoking a XAML workflow, a shared state file, a main entry point calling the others). Edit, then re-validate the touched files.

Process genome: implement every Handoffs row with the named mechanism: queue item (queue declared as a solution resource), start job, Flow or BPMN invoke of a sibling component, Action Center task, file drop. Confirm each component's Interface matches the data the Handoffs row passes. Then `uip solution resources refresh --output json` and `uip solution pack --output json` per the `uipath-solution` skill; on failure follow that skill's diagnosis.

## Phase 3 — Validate

### 3.1 Acceptance criteria

For every criterion (component criteria first, then process criteria):

| Verdict | Meaning |
|---|---|
| Met | Code directly implements the behaviour; cite file and location |
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
Skills used: …
Files created: <count>
Acceptance criteria: N/total met
Configuration answers: … (defaults marked)
Run: <the owning skill's run command for the entry point>
```

## Anti-patterns

1. **Building before the configuration questions are answered.** Produces placeholder values the user has to hunt down later.
2. **Pausing between skill groups.** "Shall I continue with the RPA part?" is wrong. Advance.
3. **One project per skill group.** A component genome is one project. A process genome is one solution with one project per component.
4. **Reordering Build With or Components** except for the handoff-dependency case in 2.1.
5. **Adding features the genome does not name, or dropping steps it does.** Gaps go to the user, not into improvised code.
6. **Editing the genome during execution.** It is read-only. Fixes to the spec are a separate authoring/extraction edit followed by re-execution.
7. **Skipping acceptance validation** because "everything compiled". The criteria are the definition of done.

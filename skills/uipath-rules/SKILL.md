---
name: uipath-rules
description: "UiPath Business Rules — `.dmn` decision tables (DMN 1.5, FEEL) in a BusinessRules project (`project.uiproj`), built with `uip rules` (`init`, `refresh`, `validate`, `debug`). Author, edit, review, validate, and debug a rule's decision table from a spreadsheet or description; extract rules from a source document (policy, PDF, scan, text, amendments, supporting documents) in checkpointed phases with page and quote citations and uipdm source refs; list and describe deployed rules. For .bpmn business rule tasks→uipath-maestro-bpmn. For EvaluateBusinessRule in .xaml→uipath-rpa. For caseplan.case/caseplan.json business rule tasks→uipath-maestro-case. For field extraction from invoices or forms→uipath-ixp. For solution pack/publish/deploy→uipath-solution."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Skill
---

# UiPath Business Rules

A Business Rules project holds one DMN decision table. DMN and FEEL follow the OMG standard; this skill covers only what UiPath accepts on top of it.

`<SKILL_DIR>` is the folder that contains this SKILL.md.

## When to Use This Skill

- Create a business rule (decision table) from a spreadsheet or description
- Generate rules from a policy, guideline, or other document, section by section, with a citation per row; build one from a base policy plus amendments or supporting documents; draft one from a single policy with IXP rules extraction (Quick draft)
- Edit the rows, columns, or hit policy of a `.dmn` in a BusinessRules project
- Validate or debug a rule that returns the wrong output
- List deployed rules or read a deployed rule's inputs and outputs

## Critical Rules

1. **Write DMN 1.5.** Use the MODEL and DMNDI namespaces `https://www.omg.org/spec/DMN/20230324/...` and DC/DI `http://www.omg.org/spec/DMN/20180521/...`. When editing a file on an older DMN version, rewrite it to these namespaces.
2. **One `.dmn` per project.** `rules debug` evaluates only the project's first `.dmn`.
3. **One decision per file, and its logic is a decision table.** When the user asks for chained decisions, a decision requirements diagram, business knowledge models, or a literal expression, say authoring them is not supported yet, then offer to flatten the logic into one table or to create one rules project per decision and let the calling process chain them. Never write the unsupported element.
4. **No DOCTYPE, XML comments, or processing instructions.** Put notes in the annotation column or a `<description>` element.
5. **Use the designer's types.** `string`, `number`, `boolean`, `Any`, `date`, `time`, `date and time`, `days and time duration`, `years and months duration`, for both columns and input arguments.
<!--skill-flavor:lifecycle-rules:start-->
6. **Scaffold a new project with `init`; after every edit, or each batch of edits written together, `refresh` then `validate`, as one command (Quick Start, step 4).** An existing project needs no `init`: edit its `.dmn` and run `refresh`. Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; keep the scaffolded `.dmn` file and its root element.
7. **A rule is done when `validate` passes and `debug` returns what the reviewed table expects.** On a wrong output, read the trace with `uip traces spans get <Data.traceId>`. Stop after 3 fix rounds and show the user the table and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
8. **Stop on a tenant without Business Rules, and publish through `uip solution`.** When `rules debug` fails with `Business Rules is not available on tenant '<TENANT>'` or `Business Rules is a preview feature and is not enabled for your organization.`, stop and relay the CLI's instruction. Pack, publish, and deploy belong to the uipath-solution skill.
9. **Name every rule.** Declare one `<annotation name="Annotation" />` after the table's last `<output>`, then give each `<rule>` one `<annotationEntry>` with a short name for the case it covers; the review table's Annotation column is what goes there. Never write an `<annotationEntry>` without that column.
10. **Write a numeric range in one cell as one interval.** `(25..60]`, never `> 25, <= 60`: a comma in a cell means "or", so the comma form matches every number.
11. **Check the uipdm elements a `.dmn` carries.** `validate` does not read `uipdm:` elements. After `validate`, run `node "<SKILL_DIR>/scripts/check-uipdm.mjs" <DMN_FILE>` ([uipdm guide](references/uipdm-guide.md)) and fix what it reports. Editing a rule that carries them keeps each row's `sourceRefs` unless the edit changes what the row cites. Never write `review`, `ruleState`, `parkedRule`, `scoreBand`, `conditionState` or `agentAssessment`; a policy gives no source for them.
12. **A rule built from a source document follows the extraction guides.** When the request gives a policy, PDF, scan, text, amendments, or supporting documents to extract rules from, read [extraction/start-guide.md](references/extraction/start-guide.md) before any other step, then only the guide it names for the path taken. It adds the "extraction rules" (cited as `extraction rule N`) on top of rules 1-11.
13. **Look for an existing project before creating one, and never replace a rule's rows without asking.** Quick Start step 1 says which project to use: a project that still holds the scaffold's placeholder is used as it is, and one with rules of its own is changed only when the request says so or the user answers `Update`.

## Quick Start

### 1. Find or create the project

Look for a BusinessRules project before creating one: a folder that holds `project.uiproj` and one `.dmn`, in the working folder or its solution.

| Found | Do |
|---|---|
| None | Create one (below). |
| One that still holds the scaffold's placeholder (input `input1`, output `output1`, one rule that returns `null`) | Use it; do not create another. Keep its `.dmn` file name and decision `id`, and set the decision's `name` and `label` to the rule's name. |
| One with rules of its own, and the request names it or asks to change it | Edit it ([Editing an Existing Rule](#editing-an-existing-rule)). |
| One with rules of its own, and the request does not say | Ask once with AskUserQuestion: `Update <PROJECT_NAME>` (replace its table, keeping the file name and decision `id`) or `Create a new project`. Never replace a rule's rows without that answer. |
| Several, and exactly one still holds the placeholder | Use that one; do not ask. |
| Several, otherwise | Ask which one, with `Create a new project` as the last option. |

When told not to pause, or in a headless run, do not ask: use a placeholder project when there is one, and otherwise create a new project. Leave every other project as it is; do not copy it or check it afterwards.

<!--skill-flavor:scaffold:start-->
To create one:

```bash
uip rules init <RULE_NAME> --output json
```

Run `init` from the solution folder when one exists; outside a solution it creates `<RULE_NAME>Solution/<RULE_NAME>/`. `Data.RuleStatus: "Preserved"` means the project already held a `.dmn` and `init` left it untouched. The rule is the one `.dmn` file in the project folder. Treat whatever table the scaffolded `.dmn` holds as a placeholder; step 3 replaces it.
<!--skill-flavor:scaffold:end-->

### 2. Design and review

Show the table as Markdown before authoring and after each change. Ask only what the request leaves open, in one question; ask nothing when told not to pause.

```markdown
**Hit policy:** FIRST

| # | creditScore (number) | income (number) | riskBand (string) | Annotation |
|---|---|---|---|---|
| 1 | < 580 | - | "High" | Subprime |
| 2 | [580..700) | >= 50000 | "Medium" | Near-prime, sufficient income |
| 3 | - | - | "Low" | Default |
```

### 3. Author the table

Replace the scaffolded table with the reviewed design. A rule built from a document also carries its uipdm elements ([uipdm guide](references/uipdm-guide.md)).

### 4. Refresh and validate

```bash
uip rules refresh <PROJECT_DIR> --output json && uip rules validate <PROJECT_DIR> --output json
```

Run them as this one command, not as two steps. Fix every error in `Data.Diagnostics`, then run it again. A file with `uipdm:` elements also gets the check in rule 11.

### 5. Verify

<!--skill-flavor:verify:start-->
```bash
uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --output json
```

`--inputs` takes one JSON object keyed by input-argument name, or `@<FILE>`. Compare `Data.result.decisions[].outputs` with the expected values. The run failed when `debug` exits 1 (`Result: Failure`); the decision and input errors are in `Data.result`, the summary code in `Data.error`. On a mismatch, read the trace:

```bash
uip traces spans get <TRACE_ID> --output json
```

`<TRACE_ID>` is `Data.traceId`. The trace shows which rules fired. `Data.traceId` is present only when tracing is on for the tenant (the default); without it, compare the inputs against each row by hand. `rules debug` needs the project directly inside its solution folder, as `init` creates it, and a logged-in user (`uip login`). `debug` uploads the solution's own files (`.uipignore` applied) and overwrites its Studio Web solution; pull Studio Web edits first.
<!--skill-flavor:verify:end-->

## Rules from a Source Document

The extraction guides turn a base policy document, plus any amendments or supporting documents, into a `.dmn` draft (Framing, Intake, Understanding, Inputs and structure, Extraction, Finish). Rule 12 routes to the start guide, which names the one guide to read for the path the user chose. They reuse everything above: the table, the lifecycle, and `validate`.

## Editing an Existing Rule

- Keep the decision's `id` and `name` and the `.dmn` file name. Consumers bind to the entry point `/<file>.dmn#<decisionId>`, and renaming either points them at an entry point that no longer exists.
- Change only what the request names; every other row keeps its entries, annotation, and position.

## Deployed Rules (Preview)

<!--skill-flavor:deployed-rules:start-->
```bash
uip rules list --folder-path <FOLDER_PATH> --output json
uip rules list --all-folders --output json
uip rules get <RULE_NAME> --folder-path <FOLDER_PATH> --output json
uip rules versions <RULE_NAME> --folder-path <FOLDER_PATH> --output json
uip rules describe <RULE_NAME> --folder-path <FOLDER_PATH> --output json
```

Each command takes `--folder-path` or `--folder-key`, never both. Exception: `list --all-folders` spans every folder you can see (mutually exclusive with the folder flags) — use it to locate a rule when its folder is unknown. `describe` returns the active version's entry points, with `InputArguments` and `OutputArguments` as JSON Schema strings. `OutputArguments` carrying `"x-uipath-decision-keyed": true` nests each output under its decision's name.
<!--skill-flavor:deployed-rules:end-->

Binding a rule into a process, workflow, or case belongs to that artifact's skill.

## Reference Navigation

| Reference | When to read |
|---|---|
| [Failure Modes Guide](references/failure-modes-guide.md) | A `uip rules` command reports an error |
| [Extraction start guide](references/extraction/start-guide.md) | The rule is built from a source document; read first. It names which of the guides below to read |
| [Guided path](references/extraction/guided-guide.md) | The user chose a guided review level |
| [Every section](references/extraction/every-section-guide.md) | The user chose `Every section` |
| [More than one document](references/extraction/multi-document-guide.md) | The request gives an amendment or a supporting document |
| [Citation guide](references/extraction/citation-guide.md) | A `dom.json` with page positions exists |
| [One-shot guide](references/extraction/one-shot-guide.md) | Only when the user picked `Quick draft (IXP)` |
| [uipdm guide](references/uipdm-guide.md) | The rule is built from a document, or a `.dmn` already carries `uipdm:` elements |
| [uipdm.xsd](references/uipdm.xsd) | Read by `scripts/check-uipdm.mjs`; not read directly |
| `scripts/check-uipdm.mjs` | After `validate`, when the `.dmn` carries `uipdm:` elements |
| `scripts/extraction/` | `resolve-refs.mjs` at Finish and `one-shot.mjs` for Quick draft, run as the extraction guides say |

## Anti-patterns

- Writing a range as a comma list (`> 25, <= 60`) instead of an interval
- Editing a row of a rule that carries `uipdm:` elements and dropping that row's `sourceRefs`
- Creating a second project when one that still holds the placeholder is already there, or replacing an existing rule's rows without the user's answer
- Guessing an input value's JSON shape instead of reading the input argument's `typeRef`
- Naming an output with spaces or a leading digit; `validate` rejects it

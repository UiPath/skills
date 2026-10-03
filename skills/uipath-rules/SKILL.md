---
name: uipath-rules
description: "UiPath Business Rules — `.dmn` decision tables (DMN 1.5, FEEL) in a BusinessRules project (`project.uiproj`), built with `uip rules` (`init`, `refresh`, `validate`, `debug`). Author, edit, review, validate, and debug a rule's decision table from a policy, spreadsheet, or description; list and describe deployed rules. For .bpmn business rule tasks->uipath-maestro-bpmn. For EvaluateBusinessRule in .xaml->uipath-rpa. For caseplan.json business rule tasks->uipath-maestro-case. For solution pack/publish/deploy->uipath-solution."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Business Rules

A Business Rules project holds one DMN decision table. DMN and FEEL follow the OMG standard; this skill covers only what UiPath accepts on top of it.

## When to Use This Skill

- Create a business rule (decision table) from a policy, spreadsheet, or description
- Edit the rows, columns, or hit policy of a `.dmn` in a BusinessRules project
- Validate or debug a rule that returns the wrong output
- List deployed rules or read a deployed rule's inputs and outputs

## Critical Rules

1. **Write DMN 1.5.** Use the MODEL and DMNDI namespaces `https://www.omg.org/spec/DMN/20230324/...` and DC/DI `http://www.omg.org/spec/DMN/20180521/...`. When editing a file on an older DMN version, rewrite it to these namespaces.
2. **One `.dmn` per project.** `rules debug` evaluates only the project's first `.dmn`.
3. **One decision per file, and its logic is a decision table.** When the user asks for chained decisions, a decision requirements diagram, business knowledge models, or a literal expression, say authoring them is not supported yet, then offer to flatten the logic into one table or to create one rules project per decision and let the calling process chain them. Never write the unsupported element.
4. **No DOCTYPE, XML comments, or processing instructions.** Put notes in the annotation column or a `<description>` element.
5. **Use the designer's types.** `string`, `number`, `boolean`, `Any`, `date`, `time`, `date and time`, `dayTimeDuration`, `yearMonthDuration`, for both columns and input arguments.
<!--skill-flavor:lifecycle-rules:start-->
6. **Scaffold with `init`; after every edit, `refresh` then `validate`.** Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; edit the scaffolded `.dmn` in place, keeping its root element.
7. **A rule is done when `validate` passes and `debug` returns what the reviewed table expects.** On a wrong output, re-run it with `--explain` and read the trace. Stop after 3 fix rounds and show the user the table and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
8. **Stop on a tenant without Business Rules, and publish through `uip solution`.** When `rules debug` fails with `Business Rules is not enabled on tenant '<TENANT>'.`, stop and relay the CLI's instruction. Pack, publish, and deploy belong to the uipath-solution skill.

## Quick Start

### 1. Scaffold

<!--skill-flavor:scaffold:start-->
```bash
uip rules init <RULE_NAME> --output json
```

Run `init` from the solution folder when one exists; outside a solution it creates `<RULE_NAME>Solution/<RULE_NAME>/`. `Data.RuleStatus: "Preserved"` means the project already held a `.dmn` and `init` left it untouched. The rule is the one `.dmn` file in the project folder.
<!--skill-flavor:scaffold:end-->

### 2. Design and review

Show the table as Markdown before authoring and after each change. Ask only what the request leaves open, in one question; ask nothing when told not to pause.

```markdown
**Hit policy:** FIRST

| # | creditScore (number) | income (number) | riskBand (string) | Annotation |
|---|---|---|---|---|
| 1 | < 580 | - | "High" | Subprime |
| 2 | [580..700) | >= 50000 | "Medium" | |
| 3 | - | - | "Low" | Default |
```

### 3. Author the table

Replace the scaffolded table with the reviewed design.

### 4. Refresh and validate

```bash
uip rules refresh <PROJECT_DIR> --output json
uip rules validate <PROJECT_DIR> --output json
```

Fix every error in `Data.Diagnostics`, then run both again.

### 5. Verify

<!--skill-flavor:verify:start-->
```bash
uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --output json
```

`--inputs` takes one JSON object keyed by input-argument name, or `@<FILE>`. Compare `Data.results[0].decisions[].outputs` with the expected values. On a mismatch:

```bash
uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --explain --output json
uip traces spans get <TRACE_ID> --output json
```

`<TRACE_ID>` is `Data.traceId`. The trace shows which rules fired. `rules debug` needs the project directly inside its solution folder, as `init` creates it, and a logged-in user (`uip login`). `debug` uploads the whole solution folder and overwrites its Studio Web solution; pull Studio Web edits first.
<!--skill-flavor:verify:end-->

## Editing an Existing Rule

- Keep the decision's `id` and `name` and the `.dmn` file name. Consumers bind to the entry point `/<file>.dmn#<decisionId>`, and renaming either points them at an entry point that no longer exists.
- Change only what the request names; every other row keeps its entries, annotation, and position.

## Deployed Rules (Preview)

<!--skill-flavor:deployed-rules:start-->
```bash
uip rules list --folder-path <FOLDER_PATH> --output json
uip rules get <RULE_NAME> --folder-path <FOLDER_PATH> --output json
uip rules versions <RULE_NAME> --folder-path <FOLDER_PATH> --output json
uip rules describe <RULE_NAME> --folder-path <FOLDER_PATH> --output json
```

Each command takes `--folder-path` or `--folder-key`, never both. `describe` returns the active version's entry points, with `InputArguments` and `OutputArguments` as JSON Schema strings. `OutputArguments` carrying `"x-uipath-decision-keyed": true` nests each output under its decision's name. Binding a rule into a process, workflow, or case belongs to that artifact's skill.
<!--skill-flavor:deployed-rules:end-->

## Reference Navigation

| Reference | When to read |
|---|---|
| [Failure Modes Guide](references/failure-modes-guide.md) | A `uip rules` command reports an error |

## Anti-patterns

- Guessing an input value's JSON shape instead of reading the input argument's `typeRef`
- Naming an output with spaces or a leading digit; `validate` rejects it

---
name: uipath-rules
description: "UiPath Business Rules — a `.dmn` rule (DMN 1.5, FEEL) in a BusinessRules project (`project.uiproj`), built with `uip rules` (`init`, `refresh`, `format`, `validate`, `debug`). Author, edit, review, validate, and debug a rule from a policy, spreadsheet, or description — one decision table, or a decision graph of several decisions linked by requirements, with literal expressions, business knowledge models and text annotations; list and describe deployed rules. For .bpmn business rule tasks→uipath-maestro-bpmn. For EvaluateBusinessRule in .xaml→uipath-rpa. For caseplan.case/caseplan.json business rule tasks→uipath-maestro-case. For solution pack/publish/deploy→uipath-solution."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Business Rules

A Business Rules project holds one `.dmn` rule of one or more decisions. DMN and FEEL follow the OMG standard; this skill covers only what UiPath accepts on top of it.

## When to Use This Skill

- Create a business rule from a policy, spreadsheet, or description — one decision, or a graph of several
- Edit the rows, columns, or hit policy of a `.dmn` in a BusinessRules project
- Validate or debug a rule that returns the wrong output
- List deployed rules or read a deployed rule's inputs and outputs

## Critical Rules

1. **Write DMN 1.5.** Use the MODEL and DMNDI namespaces `https://www.omg.org/spec/DMN/20230324/...` and DC/DI `http://www.omg.org/spec/DMN/20180521/...`. When editing a file on an older DMN version, rewrite it to these namespaces.
2. **One `.dmn` per project.** `rules debug` evaluates only the project's first `.dmn`.
3. **A decision's logic is a decision table or a literal expression.** The file's `<uipath:authoring surface="…" />` says which editor opens it: `decision-table` for a rule that is one decision table and nothing else — which is what `uip rules init` scaffolds, so **leave it as it is** — and `decision-graph` only once the file holds a second decision, a knowledge model, or a text annotation. `decision-graph` on a single table opens it on the canvas instead of the table editor, and `validate` reports nothing either way. A rule may hold several decisions linked by `informationRequirement`, business knowledge models they call, and text annotations; read the [Decision Graphs Guide](references/drd-guide.md) before authoring or editing one, and remember how a decision reads an upstream one turns on how many outputs that one's table has: its own name when there is one output, `name.column` only when there are several. Never a column name on its own. When the user asks for a knowledge source, a decision service, a group, an import, or any other expression kind — context, invocation, relation, list, conditional — say authoring it is not supported yet, then offer to express the logic as decision tables. Never write the unsupported element.
4. **No DOCTYPE, XML comments, or processing instructions.** Put notes in the annotation column, a `<description>` element, or a `<textAnnotation>` tied to the element it is about.
5. **Use the designer's types.** `string`, `number`, `boolean`, `Any`, `date`, `time`, `date and time`, `days and time duration`, `years and months duration`, for both columns and input arguments.
<!--skill-flavor:lifecycle-rules:start-->
6. **Scaffold a new project with `init`; after every edit, `format`, `refresh` then `validate`.** An existing project needs no `init`: edit its `.dmn` and run `refresh`. Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; keep the scaffolded `.dmn` file and its root element.
7. **A rule is done when `validate` passes and `debug` returns what the reviewed design expects, from every decision and not only the last.** On a wrong output, read the trace with `uip traces spans get <Data.traceId>`. Stop after 3 fix rounds and show the user the tables and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
8. **Stop on a tenant without Business Rules, and publish through `uip solution`.** When `rules debug` fails with `Business Rules is not available on tenant '<TENANT>'` or `Business Rules is a preview feature and is not enabled for your organization.`, stop and relay the CLI's instruction. Pack, publish, and deploy belong to the uipath-solution skill.
9. **Name every rule.** Declare one `<annotation name="Annotation" />` after each table's last `<output>`, then give each `<rule>` one `<annotationEntry>` with a short name for the case it covers; the review table's Annotation column is what goes there. Never write an `<annotationEntry>` without that column. A decision whose logic is a literal expression has no rules, so it has neither.
10. **Never place diagram shapes by hand; `format` draws them.** Leave DMNDI out of a new `.dmn`, and run `uip rules format <PROJECT_DIR>` after adding or removing any element the canvas draws — an input, a decision, a knowledge model or a text annotation. It adds a shape for each new element, leaves placed shapes where the user left them, and drops the shapes of deleted ones. `validate` never looks at the diagram, so a shape you place yourself is reported by nothing; it just lands on top of another card in the designer. When you edit a `.dmn` that already has one, **keep its `dmndi:DMNDI` element as it is**: rewriting the file without it throws away the layout the user arranged, and `format` then lays the whole graph out afresh.

## Quick Start

### 1. Scaffold (new projects only)

<!--skill-flavor:scaffold:start-->
```bash
uip rules init <RULE_NAME> --output json
```

Run `init` from the solution folder when one exists; outside a solution it creates `<RULE_NAME>Solution/<RULE_NAME>/`. `Data.RuleStatus: "Preserved"` means the project already held a `.dmn` and `init` left it untouched. The rule is the one `.dmn` file in the project folder. Treat whatever table the scaffolded `.dmn` holds as a placeholder; step 3 replaces it. The **table** is the placeholder — not the root element, and not its `extensionElements`, which already carry the right authoring surface.
<!--skill-flavor:scaffold:end-->

### 2. Design and review

Show the table as Markdown before authoring and after each change — one table per decision when the rule is a graph, upstream first, each naming the decision it belongs to. Ask only what the request leaves open, in one question; ask nothing when told not to pause.

```markdown
**Hit policy:** FIRST

| # | creditScore (number) | income (number) | riskBand (string) | Annotation |
|---|---|---|---|---|
| 1 | < 580 | - | "High" | Subprime |
| 2 | [580..700) | >= 50000 | "Medium" | Near-prime, sufficient income |
| 3 | - | - | "Low" | Default |
```

### 3. Author the rule

Replace the scaffolded table with the reviewed design, and add the other decisions a graph needs.

### 4. Format, refresh and validate

```bash
uip rules format <PROJECT_DIR> --output json
uip rules refresh <PROJECT_DIR> --output json
uip rules validate <PROJECT_DIR> --output json
```

Run `format` whenever the edit added or removed a drawn element; it writes only the files whose diagram changed. Fix every error in `Data.Diagnostics`, then run all three again.

### 5. Verify

<!--skill-flavor:verify:start-->
```bash
uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --output json
```

`--inputs` takes one JSON object keyed by input-argument name, or `@<FILE>`. Compare `Data.result.decisions[].outputs` with the expected values, for every decision the rule holds. The run failed when `debug` exits 1 (`Result: Failure`); the decision and input errors are in `Data.result`, the summary code in `Data.error`. On a mismatch, read the trace:

```bash
uip traces spans get <TRACE_ID> --output json
```

`<TRACE_ID>` is `Data.traceId`. The trace shows which rules fired. `Data.traceId` is present only when tracing is on for the tenant (the default); without it, compare the inputs against each row by hand. `rules debug` needs the project directly inside its solution folder, as `init` creates it, and a logged-in user (`uip login`). `debug` uploads the solution's own files (`.uipignore` applied) and overwrites its Studio Web solution; pull Studio Web edits first.
<!--skill-flavor:verify:end-->

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

A deployed rule is held by the Business Rules service, or still by Orchestrator when it was deployed before rules moved there; each row's `Source` (`BusinessRules` or `Orchestrator`) says which. `get`, `versions`, `describe` and `list --all-folders` find a rule in either. `list` on one folder shows the service's rules there, or Orchestrator's when the service holds none in that folder. When it leaves Orchestrator's rules out, it says so on stderr: read those by name with `get`, or find them with `list --all-folders`.
<!--skill-flavor:deployed-rules:end-->

Binding a rule into a process, workflow, or case belongs to that artifact's skill.

## Reference Navigation

| Reference | When to read |
|---|---|
| [Decision Graphs Guide](references/drd-guide.md) | The rule holds, or needs, more than one decision |
| [Failure Modes Guide](references/failure-modes-guide.md) | A `uip rules` command reports an error |

## Anti-patterns

- Guessing an input value's JSON shape instead of reading the input argument's `typeRef`
- Naming an output with spaces or a leading digit; `validate` rejects it
- Writing `dmndi:` shapes by hand instead of running `uip rules format`

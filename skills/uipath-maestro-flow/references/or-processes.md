# Orchestrator Processes

Orchestrator has several process types:

- Agent - see [Agent](agent.md)
- Api - see [API Workflow](api-workflow.md)
- CaseManagement
- Flow
- Function
- Process
- ProcessOrchestration - see [Agentic Process](agentic-process.md)
- TestAutomationProcess
- WebApp

## Finding a process

List the available processes with the process type using either of the following commands, depending on if you know the folder:

```shell
uip or processes list --all-folders --process-type !!ProcessType!! --limit 200 --output json
uip or processes list --folder-path '<folder>' --process-type !!ProcessType!! --limit 200 --output json
```

Replace `!!ProcessType!!` with the process type, e.g. `Agent` or `ProcessOrchestration`.

The `list` command is paginated.
If the output field *Pagination.HasMore* flag is true, there are more results available.
Use `--offset` to move to the next set of results.

The resulting list will have *Name*, *ProcessKey*, and sometimes *Description* fields that may help identify the process you need.
Note that there is a flag *IsLatestVersion* in case there are multiple published versions with the same process key.
The *Key* field (GUID) is the unique id for the process.

## Getting the inputs and outputs

Do not copy the key or the argument schema by hand.
Write the step with `name` and `folderPath` only, and leave `key` and `returns` out.

Needs `@uipath/maestro-builder-sdk` 6.109.0 or later: `prepare --kind Process` then prints `Type`, `Inputs` and `Outputs` lines.
An older SDK records only the catalogue row (no `Type` line), and its `compile` refuses a step with no `key` (`*_NO_KEY`).
<!--skill-flavor:or-processes-prepare-sdk:start-->
Upgrade the copy in use: `npm install @uipath/maestro-builder-sdk@latest` in a workspace that has its own `node_modules` copy, else `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:or-processes-prepare-sdk:end-->

```ts
.step('intake',
  agenticProcess({
    name: 'ProcurementProcess',
    folderPath: '<FOLDER_PATH>',
    inputs: { productId: 1 },
  }))
```

`check` reports the missing key with the factory's `*_NO_KEY` code (`RPA_NO_KEY`, `APIWF_NO_KEY`, `FUNCTION_NO_KEY`, `AGENTIC_NO_KEY`, `AGENT_NO_KEY`) and prints the command that records the process.
Run it:

```shell
uip maestro registry prepare --kind Process --name ProcurementProcess --folder-path '<FOLDER_PATH>'
```

If `uip` answers `unknown option '--kind'`, the `uip` in use predates key-less `prepare`: run the same command as `npx flow-sdk registry prepare --kind Process …`.

`prepare` prints the process's inputs and outputs:

```text
Type      ProcessOrchestration
Inputs    productId: integer
Outputs   status: boolean
```

Re-run `check` and fix what it reports:

- `PROCESS_INPUT_UNKNOWN`: an input the process does not declare (it names the nearest real one);
- `PROCESS_INPUT_MISSING`: a required input left out;
- `PROCESS_INPUT_TYPE`: a literal of the wrong type;
- `PROCESS_RETURNS_UNKNOWN`: a `returns` field the process does not return;
- `PROCESS_TYPE_MISMATCH`: the wrong factory for the process type.

Then `compile` writes the key and the output schema (`returns`) from that record.
Read `out('<step>', '<field>')` with the names `prepare` printed.

Orchestrator often leaves a process's contract blank (common for API workflows and some RPA processes).
`prepare` then prints `(not recorded …)` for that side, or `Arguments not recorded`.
`check` does not validate that side, and `compile` still writes the key.
Keep your `inputs`, and declare `returns` for the fields you read; to see the contract, use `uip maestro flow registry get <node type>` (`inputDefinition`, `outputDefinition`).

A record more than 24 hours old still compiles; `check` warns `PROCESS_RECORD_STALE` and prints the `prepare` that refreshes it.

## Notes

Sometimes you need to search across multiple process types.
For example, the **ProcessOrchestration**, **CaseManagement**, and **Flow** process types could all be considered "Agentic Processes".
The `--process-type` filter does not accept multiple entries.
When performing a `list` command, the default fields returned do not include *ProcessType* so you will need either to use the `--all-fields` option or run multiple `list` commands with each process type.

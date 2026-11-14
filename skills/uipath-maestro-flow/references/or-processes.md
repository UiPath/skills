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
Write the step with `name` and `folderPath` only, and leave `key` and `returns` out:

```ts
.step('intake',
  agenticProcess({
    name: 'ProcurementProcess',
    folderPath: 'Shared/uipath-agents/ProcurementProcess',
    inputs: { productId: 1 },
  }))
```

`check` reports the missing key (`AGENTIC_NO_KEY`, `RPA_NO_KEY`, ...) and prints the command that records the process.
Run it:

```shell
uip maestro registry prepare --kind Process --name ProcurementProcess --folder-path Shared/uipath-agents/ProcurementProcess
```

It prints the process's inputs and outputs:

```text
Type      ProcessOrchestration
Inputs    productId: integer
Outputs   status: boolean
```

Then `compile` writes the key and the output schema (`returns`) from that record.
`check` validates the step against it: an unknown input (`PROCESS_INPUT_UNKNOWN`), a required input left out (`PROCESS_INPUT_MISSING`), a literal of the wrong type (`PROCESS_INPUT_TYPE`), a `returns` field the process does not return (`PROCESS_RETURNS_UNKNOWN`), and the wrong factory for the process type (`PROCESS_TYPE_MISMATCH`).
Fix what it reports; read `out('<step>', '<field>')` with the names `prepare` printed.

## Notes

Sometimes you need to search across multiple process types.
For example, the **ProcessOrchestration**, **CaseManagement**, and **Flow** process types could all be considered "Agentic Processes".
The `--process-type` filter does not accept multiple entries.
When performing a `list` command, the default fields returned do not include *ProcessType* so you will need either to use the `--all-fields` option or run multiple `list` commands with each process type.

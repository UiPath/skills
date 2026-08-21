# Orchestrator Processes

Orchestrator has several process types:

- Agent - see [Agent](agent.md)
- Api - see [API Workflow](agent.md)
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

Once you find the process, you must use the `get` command with the *Key* to retrieve more details.
The inputs and outputs of a published process are buried in the *ArgumentsV2* field that is only exposed when using the `--all-fields` option.
The *Input* and *Output* parameters inside *ArgumentsV2* are escaped JSON strings.
The following CLI command can be used to extract inputs and outputs as JSON text:

```shell
uip or processes get BAADF00D-BAAD-F00D-BAAD-F00DBAADF00D --all-fields --output json 2>/dev/null \
  | jq '.Data.ArgumentsV2 | {Input, Output} | map_values(if (. // "") == "" then null else fromjson end)'
```

Here is an example output of this command:

```json
{
  "Input": {
    "type": "object",
    "properties": {
      "productId": {
        "type": "integer",
        "title": "productId"
      }
    },
    "required": []
  },
  "Output": {
    "type": "object",
    "properties": {
      "status": {
        "type": "boolean",
        "title": "status"
      }
    },
    "required": []
  }
}
```

The defined inputs and outputs would be represented in an action similar to the following:

```ts
.step('intake',
  agenticProcess({
    key: 'BAADF00D-BAAD-F00D-BAAD-F00DBAADF00D',
    name: 'ProcurementProcess',
    folderPath: 'Shared',
    inputs: { productId: 1 }, // input object
    returns: { status: 'boolean' } // output object
  }))
```

## Notes

Sometimes you need to search across multiple process types.
For example, the **ProcessOrchestration**, **CaseManagement**, and **Flow** process types could all be considered "Agentic Processes".
The `--process-type` filter does not accept multiple entries.
When performing a `list` command, the default fields returned do not include *ProcessType* so you will need either to use the `--all-fields` option or run multiple `list` commands with each process type.

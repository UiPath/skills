# Orchestrator Processes

Process types: Agent ([Agent](agent.md)); Api ([API Workflow](api-workflow.md)); CaseManagement; Flow; Function; Process; ProcessOrchestration ([Agentic Process](agentic-process.md)); TestAutomationProcess; WebApp.

## Finding a process

List processes by type in all folders or a known folder:

```shell
uip or processes list --all-folders --process-type !!ProcessType!! --limit 200 --output json
uip or processes list --folder-path '<folder>' --process-type !!ProcessType!! --limit 200 --output json
```

Replace `!!ProcessType!!` with a type such as `Agent` or `ProcessOrchestration`. `--process-type` accepts one entry, so search each needed process type separately. If *Pagination.HasMore* is true, run the next paginated request with `--offset`. The resulting list will have *Name*, *ProcessKey*, and sometimes *Description* fields that may help identify the process you need. Use *IsLatestVersion* to distinguish published versions sharing a process key. *Key* (GUID) is the unique process ID. Since the default `list` response omits *ProcessType*, use `--all-fields` or run a separate `list` command for each process type.

**ProcessOrchestration**, **CaseManagement**, and **Flow** are "Agentic Processes".

## Getting the inputs and outputs
Once you find the process, you must use the `get` command with the *Key* to retrieve more details.

After finding a process, run `get` with its *Key*. Published-process inputs and outputs are in *ArgumentsV2*, exposed only with `--all-fields`; *Input* and *Output* are escaped JSON strings. Extract them as JSON text:

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
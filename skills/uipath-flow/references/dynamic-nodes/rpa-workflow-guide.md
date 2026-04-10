# RPA Workflow Nodes

RPA workflow nodes invoke UiPath processes (attended or unattended) via Orchestrator. They map to `Orchestrator.StartJob` service calls and appear in the flow designer with the `rpa` icon. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

For shared structure (handle configuration, definition/instance templates, bindings pattern), see [resource-node-guide.md](resource-node-guide.md).

## When to Use

| Situation | Use RPA? |
|---|---|
| Desktop/browser automation via a published RPA process | Yes |
| Target system has a REST API | No -- use a connector or HTTP node |
| RPA process not yet published | No -- use `core.logic.mock` placeholder, tell user to create with `uipath-rpa` |
| Need AI reasoning, not desktop automation | No -- use an agent node |

## Type Parameters

| Field | Value |
|---|---|
| `model.serviceType` | `Orchestrator.StartJob` |
| `model.bindings.resourceSubType` | `Process` |
| `model.bindings.orchestratorType` | `process` |
| `category` | `rpa-workflow` |
| `display.icon` | `rpa` |
| `display.iconBackground` | `linear-gradient(225deg, #DDFBF1 0%, #DAF3FF 100%)` |
| `display.iconBackgroundDark` | `linear-gradient(225deg, rgba(131, 255, 214, 0.30) 0%, rgba(109, 122, 128, 0.30) 100%)` |
| Node type pattern | `uipath.core.rpa-workflow.<KEY>` |

The `<KEY>` is a UUID that uniquely identifies the process in the registry. Obtain it from `uip flow registry search` or `uip flow registry get`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.rpa-workflow" --output json
```

Requires `uip login`. Only published processes from your tenant appear.

## Complete Example -- AO_HRO_HITLWrapper (hr-onboarding)

This example is taken verbatim from the `hr-onboarding` reference flow. The `AO_HRO_HITLWrapper` process accepts agent recommendations as input and produces formatted email content and structured recommendations as output via a human-in-the-loop review step.

### Node Instance

This is the entry in the top-level `nodes` array:

```json
{
  "id": "aoHroHitlwrapper1",
  "type": "uipath.core.rpa-workflow.1fd0e004-7744-46b9-90ba-23fab201a6ba",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 2944, "y": 48 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "AO_HRO_HITLWrapper",
    "subLabel": "",
    "iconBackground": "linear-gradient(225deg, #DDFBF1 0%, #DAF3FF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, rgba(131, 255, 214, 0.30) 0%, rgba(109, 122, 128, 0.30) 100%)",
    "icon": "rpa"
  },
  "inputs": {
    "in_AgentMessage": "{{ $vars.trainingrecommendationagent1.message }}",
    "in_Recommendations": null,
    "in_HTMLRecs": "{{ $vars.trainingrecommendationagent1.customHTMLrecs }}"
  },
  "outputs": {
    "out_EmailContent": {
      "type": "string",
      "source": "=out_EmailContent",
      "var": "out_EmailContent"
    },
    "out_Recommendations": {
      "type": "array",
      "source": "=out_Recommendations",
      "var": "out_Recommendations"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["code", "message", "detail", "category", "status"],
        "properties": {
          "code": { "type": "string", "description": "Error code as a string" },
          "message": { "type": "string", "description": "High-level error message" },
          "detail": { "type": "string", "description": "Detailed error description" },
          "category": { "type": "string", "description": "Error category" },
          "status": { "type": "integer", "description": "HTTP status code" }
        },
        "additionalProperties": false
      },
      "source": "=Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartJob",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Process",
      "resourceKey": "1fd0e004-7744-46b9-90ba-23fab201a6ba",
      "orchestratorType": "process",
      "values": {
        "name": "AO_HRO_HITLWrapper",
        "folderPath": ""
      }
    },
    "projectId": "ebf43d6a-d89d-4352-a4f4-05ebeb84263f",
    "context": [
      {
        "name": "name",
        "type": "string",
        "value": "=bindings.bsjxIdfuk",
        "default": "AO_HRO_HITLWrapper"
      },
      {
        "name": "folderPath",
        "type": "string",
        "value": "=bindings.bqygS23tH",
        "default": "folderPath"
      },
      {
        "name": "_label",
        "type": "string",
        "value": "AO_HRO_HITLWrapper"
      }
    ]
  }
}
```

### Definition

This is the entry in the top-level `definitions` array:

```json
{
  "nodeType": "uipath.core.rpa-workflow.1fd0e004-7744-46b9-90ba-23fab201a6ba",
  "version": "1.0.0",
  "category": "rpa-workflow",
  "description": "",
  "tags": [],
  "sortOrder": 5,
  "supportsErrorHandling": true,
  "display": {
    "label": "AO_HRO_HITLWrapper",
    "icon": "rpa",
    "iconBackground": "linear-gradient(225deg, #DDFBF1 0%, #DAF3FF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, rgba(131, 255, 214, 0.30) 0%, rgba(109, 122, 128, 0.30) 100%)"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        { "id": "input", "type": "target", "handleType": "input" }
      ]
    },
    {
      "position": "right",
      "handles": [
        { "id": "output", "type": "source", "handleType": "output" },
        {
          "id": "error",
          "label": "Error",
          "type": "source",
          "handleType": "output",
          "visible": "{inputs.errorHandlingEnabled}",
          "constraints": { "maxConnections": 1 }
        }
      ]
    }
  ],
  "toolbarExtensions": {
    "design": {
      "actions": [
        { "id": "open-workflow", "icon": "external-link", "label": "Open" }
      ]
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartJob",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Process",
      "resourceKey": "1fd0e004-7744-46b9-90ba-23fab201a6ba",
      "orchestratorType": "process",
      "values": {
        "name": "AO_HRO_HITLWrapper",
        "folderPath": ""
      }
    },
    "projectId": "ebf43d6a-d89d-4352-a4f4-05ebeb84263f",
    "context": [
      { "name": "name", "type": "string", "value": "<bindings.name>" },
      { "name": "folderPath", "type": "string", "value": "<bindings.folderPath>" },
      { "name": "_label", "type": "string", "value": "AO_HRO_HITLWrapper" }
    ]
  },
  "form": {
    "id": "activity-properties",
    "title": "RPA workflow",
    "sections": [
      {
        "id": "inputs",
        "title": "Inputs",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          { "name": "inputs.in_AgentMessage", "type": "text", "label": "in_AgentMessage" },
          {
            "name": "inputs.in_Recommendations",
            "type": "custom",
            "component": "object-editor",
            "label": "in_Recommendations",
            "componentProps": {
              "schema": {
                "type": "array",
                "x-default-expression": "new Newtonsoft.Json.Linq.JArray From {  }"
              }
            }
          },
          { "name": "inputs.in_HTMLRecs", "type": "text", "label": "in_HTMLRecs" }
        ]
      }
    ]
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "in_AgentMessage": { "type": "string" },
      "in_Recommendations": {
        "type": "array",
        "x-default-expression": "new Newtonsoft.Json.Linq.JArray From {  }"
      },
      "in_HTMLRecs": { "type": "string" }
    }
  },
  "inputDefaults": {
    "in_AgentMessage": "",
    "in_Recommendations": null,
    "in_HTMLRecs": ""
  },
  "outputDefinition": {
    "out_EmailContent": {
      "type": "string",
      "source": "=out_EmailContent",
      "var": "out_EmailContent"
    },
    "out_Recommendations": {
      "type": "array",
      "source": "=out_Recommendations",
      "var": "out_Recommendations"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["code", "message", "detail", "category", "status"],
        "properties": {
          "code": { "type": "string", "description": "Error code as a string" },
          "message": { "type": "string", "description": "High-level error message" },
          "detail": { "type": "string", "description": "Detailed error description" },
          "category": { "type": "string", "description": "Error category" },
          "status": { "type": "integer", "description": "HTTP status code" }
        },
        "additionalProperties": false
      }
    }
  },
  "debug": { "runtime": "bpmnEngine" }
}
```

### Bindings (2 entries)

These are the entries in the top-level `bindings` array that correspond to this node. They are matched by `resourceKey: "1fd0e004-7744-46b9-90ba-23fab201a6ba"`. Every RPA workflow node requires exactly 2 binding entries: one for `name` and one for `folderPath`.

```json
[
  {
    "id": "bsjxIdfuk",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "1fd0e004-7744-46b9-90ba-23fab201a6ba",
    "default": "AO_HRO_HITLWrapper",
    "propertyAttribute": "name",
    "resourceSubType": "Process"
  },
  {
    "id": "bqygS23tH",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "1fd0e004-7744-46b9-90ba-23fab201a6ba",
    "default": "",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Process"
  }
]
```

The `model.context` entries in the node instance reference these bindings by ID: `"value": "=bindings.bsjxIdfuk"` resolves to the `name` binding, and `"value": "=bindings.bqygS23tH"` resolves to the `folderPath` binding.

## Input/Output Patterns

RPA workflow arguments follow .NET naming conventions inherited from UiPath Studio:

- Input arguments: `in_<ArgumentName>` (e.g., `in_AgentMessage`, `in_HTMLRecs`)
- Output arguments: `out_<ArgumentName>` (e.g., `out_EmailContent`, `out_Recommendations`)

### .NET to JSON Type Mapping

| .NET Type | JSON Schema Type |
|---|---|
| `System.String` | `string` |
| `System.Int32` / `System.Int64` | `number` |
| `System.Boolean` | `boolean` |
| `JArray` / `List<T>` | `array` |
| `JObject` / `Dictionary<string,object>` | `object` |

### Input Wiring

Inputs are set in the node instance `inputs` object. Values can be:

1. **Expression references** to upstream node outputs: `"{{ $vars.trainingrecommendationagent1.message }}"`
2. **Literal values**: `"some string"` or `42`
3. **Null**: `null` (uses the process default)

### Output Wiring

Each output in the node instance `outputs` object has three fields:

- `type` -- the JSON schema type (`string`, `array`, `object`, etc.)
- `source` -- the expression mapping from the process output argument (e.g., `=out_EmailContent`)
- `var` -- the variable name used to reference this output downstream (e.g., `$vars.aoHroHitlwrapper1.out_EmailContent`)

The `error` output is always present and follows a fixed schema with `code`, `message`, `detail`, `category`, and `status` fields.

### Output Variables

- `$vars.<NODE_ID>.output` -- the RPA process return value (structure depends on the process)
- `$vars.<NODE_ID>.error` -- error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Adding via CLI

```bash
uip flow node add <PROJECT_NAME>.flow "uipath.core.rpa-workflow.<KEY>" --output json \
  --input '{"<ARG_NAME>": "<VALUE>"}' \
  --label "<PROCESS_NAME>" \
  --position <X>,<Y>
```

## Common Mistakes

1. **Using `Orchestrator.StartAgentJob` instead of `Orchestrator.StartJob`.** RPA workflow nodes use `Orchestrator.StartJob`. The `StartAgentJob` service type is for agent nodes, not RPA workflows.

2. **Forgetting to add the 2 binding entries to `workflow.bindings`.** Every RPA workflow node requires a `name` binding and a `folderPath` binding in the top-level `bindings` array. Without them, the node cannot resolve its process reference at runtime.

3. **Not running `uip flow registry pull --force` before searching.** The local registry cache may be stale. Always pull before searching to ensure you get current results.

4. **Hand-writing `inputDefinition` instead of copying from `registry get`.** Argument names and types must exactly match the process definition in Orchestrator. Use `uip flow registry get "<NODE_TYPE>" --output json` and copy the `inputDefinition` and `outputDefinition` verbatim. Hand-written argument types will be wrong.

5. **Forgetting to regenerate `variables.nodes` after adding the node.** The `variables.nodes` section must include entries for the new node's outputs. Run the variable regeneration step or manually add the output variable entries.

6. **Mismatching the `resourceKey` between the node instance, definition, and bindings.** All three locations must use the same UUID. The node `type` suffix, `model.bindings.resourceKey`, definition `nodeType` suffix, and binding `resourceKey` fields must all contain the same key.

7. **Setting `resourceSubType` to `Agent` instead of `Process`.** RPA workflow nodes always use `"resourceSubType": "Process"`. The `Agent` subtype is reserved for agent nodes.

## Debug

| Error | Cause | Fix |
|---|---|---|
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.<NODE_ID>.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow in [resource-node-guide.md](resource-node-guide.md) |

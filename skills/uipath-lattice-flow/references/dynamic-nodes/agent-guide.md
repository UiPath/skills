# Agent Nodes

Agent resource nodes run AI agents published to UiPath Orchestrator. They use the `Orchestrator.StartAgentJob` service type and require registry data pulled via `uip registry pull`.

## Type Parameters

| Field | Value |
|---|---|
| `model.serviceType` | `Orchestrator.StartAgentJob` |
| `model.bindings.resourceSubType` | `Agent` |
| `model.bindings.orchestratorType` | `agent` |
| `category` | `agent` |
| `display.icon` | `autonomous-agent` |
| `display.iconBackground` | `linear-gradient(225deg, rgba(225, 246, 253, 0.60) 0%, rgba(193, 160, 255, 0.20) 100%)` |
| `display.iconBackgroundDark` | `linear-gradient(225deg, rgba(236, 211, 255, 0.40) 0%, rgba(211, 229, 255, 0.40) 100%)` |
| Node type pattern | `uipath.core.agent.<KEY>` |

The `<KEY>` is typically a UUID (e.g., `93f09b44-e635-40f9-8cab-44ca29e748ed`) matching the `resourceKey` in bindings. For personal workspace agents, the key is a path string instead (see Section 3).

## Complete Example (hr-onboarding)

This example uses the `JobOfferAcceptanceDeciderAgent` from the hr-onboarding reference flow. An agent node requires three pieces: a node instance in `workflow.nodes`, a definition in `workflow.definitions`, and two binding entries in `workflow.bindings`.

### Node Instance

```json
{
  "id": "jobofferacceptancedecideragent1",
  "type": "uipath.core.agent.93f09b44-e635-40f9-8cab-44ca29e748ed",
  "typeVersion": "1.0.0",
  "ui": {
    "position": {
      "x": 608,
      "y": 240
    },
    "size": {
      "width": 96,
      "height": 96
    },
    "collapsed": false
  },
  "display": {
    "label": "JobOfferAcceptanceDeciderAgent",
    "subLabel": "",
    "iconBackground": "linear-gradient(225deg, rgba(225, 246, 253, 0.60) 0%, rgba(193, 160, 255, 0.20) 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, rgba(236, 211, 255, 0.40) 0%, rgba(211, 229, 255, 0.40) 100%)",
    "icon": "autonomous-agent",
    "description": ""
  },
  "inputs": {
    "in_emailContent": "{{ $vars.aoHroMonitorandrecievemailfromuser1.out_EmailContent }}",
    "in_SlackHiringMangerEmail": "{{ $vars.manualTrigger1.output.prehireemail }}"
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "version": "v2",
    "section": "In this solution",
    "debug": {
      "runtime": "bpmnEngine"
    },
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "93f09b44-e635-40f9-8cab-44ca29e748ed",
      "orchestratorType": "agent",
      "values": {
        "name": "JobOfferAcceptanceDeciderAgent",
        "folderPath": ""
      }
    },
    "projectId": "c2b3ce9d-bc31-467d-a91b-f5eed7f379d9",
    "context": [
      {
        "name": "name",
        "type": "string",
        "value": "=bindings.bbW6wyXDV",
        "default": "JobOfferAcceptanceDeciderAgent"
      },
      {
        "name": "folderPath",
        "type": "string",
        "value": "=bindings.bRos6xbQF",
        "default": "folderPath"
      },
      {
        "name": "_label",
        "type": "string",
        "value": "JobOfferAcceptanceDeciderAgent"
      }
    ]
  }
}
```

### Definition

```json
{
  "nodeType": "uipath.core.agent.93f09b44-e635-40f9-8cab-44ca29e748ed",
  "version": "1.0.0",
  "category": "agent",
  "description": "",
  "tags": [],
  "sortOrder": 5,
  "supportsErrorHandling": true,
  "display": {
    "label": "JobOfferAcceptanceDeciderAgent",
    "description": "",
    "icon": "autonomous-agent",
    "iconBackground": "linear-gradient(225deg, rgba(225, 246, 253, 0.60) 0%, rgba(193, 160, 255, 0.20) 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, rgba(236, 211, 255, 0.40) 0%, rgba(211, 229, 255, 0.40) 100%)"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ]
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "output",
          "type": "source",
          "handleType": "output"
        },
        {
          "id": "error",
          "label": "Error",
          "type": "source",
          "handleType": "output",
          "visible": "{inputs.errorHandlingEnabled}",
          "constraints": {
            "maxConnections": 1
          }
        }
      ]
    }
  ],
  "toolbarExtensions": {
    "design": {
      "actions": [
        {
          "id": "open-workflow",
          "icon": "external-link",
          "label": "Open"
        }
      ]
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "version": "v2",
    "section": "In this solution",
    "debug": {
      "runtime": "bpmnEngine"
    },
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "93f09b44-e635-40f9-8cab-44ca29e748ed",
      "orchestratorType": "agent",
      "values": {
        "name": "JobOfferAcceptanceDeciderAgent",
        "folderPath": ""
      }
    },
    "projectId": "c2b3ce9d-bc31-467d-a91b-f5eed7f379d9",
    "context": [
      {
        "name": "name",
        "type": "string",
        "value": "<bindings.name>"
      },
      {
        "name": "folderPath",
        "type": "string",
        "value": "<bindings.folderPath>"
      },
      {
        "name": "_label",
        "type": "string",
        "value": "JobOfferAcceptanceDeciderAgent"
      }
    ]
  },
  "form": {
    "id": "activity-properties",
    "title": "autonomous agent",
    "sections": [
      {
        "id": "inputs",
        "title": "Inputs",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.in_emailContent",
            "type": "text",
            "label": "in_emailContent"
          },
          {
            "name": "inputs.in_SlackHiringMangerEmail",
            "type": "text",
            "label": "in_SlackHiringMangerEmail"
          }
        ]
      }
    ]
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "in_emailContent": {
        "type": "string"
      },
      "in_SlackHiringMangerEmail": {
        "type": "string"
      }
    }
  },
  "inputDefaults": {
    "in_emailContent": "",
    "in_SlackHiringMangerEmail": ""
  },
  "outputDefinition": {
    "out_isAccepted": {
      "type": "boolean",
      "source": "=out_isAccepted",
      "var": "out_isAccepted"
    },
    "out_explanation": {
      "type": "string",
      "source": "=out_explanation",
      "var": "out_explanation"
    },
    "out_confidence": {
      "type": "string",
      "source": "=out_confidence",
      "var": "out_confidence"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
          "code",
          "message",
          "detail",
          "category",
          "status"
        ],
        "properties": {
          "code": {
            "type": "string",
            "description": "Error code as a string"
          },
          "message": {
            "type": "string",
            "description": "High-level error message"
          },
          "detail": {
            "type": "string",
            "description": "Detailed error description"
          },
          "category": {
            "type": "string",
            "description": "Error category"
          },
          "status": {
            "type": "integer",
            "description": "HTTP status code"
          }
        },
        "additionalProperties": false
      }
    }
  },
  "debug": {
    "runtime": "bpmnEngine"
  }
}
```

### Bindings (2 entries)

Every agent node requires exactly two entries in the top-level `workflow.bindings` array -- one for `name` and one for `folderPath`. The `id` values must match the binding references used in the node instance's `model.context` entries.

```json
[
  {
    "id": "bbW6wyXDV",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "93f09b44-e635-40f9-8cab-44ca29e748ed",
    "default": "JobOfferAcceptanceDeciderAgent",
    "propertyAttribute": "name",
    "resourceSubType": "Agent"
  },
  {
    "id": "bRos6xbQF",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "93f09b44-e635-40f9-8cab-44ca29e748ed",
    "default": "",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Agent"
  }
]
```

Key relationships:

1. The node instance `model.context[0].value` is `"=bindings.bbW6wyXDV"` -- this references the `name` binding entry by its `id`.
2. The node instance `model.context[1].value` is `"=bindings.bRos6xbQF"` -- this references the `folderPath` binding entry by its `id`.
3. Both binding entries share the same `resourceKey` as the node's `model.bindings.resourceKey`.
4. Both binding entries have `"resourceSubType": "Agent"` (not `"Process"`).

## Personal Workspace Agents

When an agent is published from a personal workspace rather than an Orchestrator folder, the `resourceKey` is a path string instead of a UUID. The node type still embeds a UUID (generated locally), but all `resourceKey` fields use the workspace path format.

### Differences from Orchestrator Folder Agents

| Field | Orchestrator Folder Agent | Personal Workspace Agent |
|---|---|---|
| `model.bindings.resourceKey` | UUID (`93f09b44-...`) | Path (`user@domain's workspace/Project.AgentName`) |
| `model.bindings.values.folderPath` | `""` (empty) | `"user@domain's workspace/ProjectName"` |
| `model.projectId` | Present (UUID) | Absent |
| `model.section` | `"In this solution"` | `"Published"` |
| Binding `default` for `folderPath` | `""` (empty) | Full workspace path |

### Example from devconnect-email

Node instance `model` section (abbreviated to show key differences):

```json
{
  "type": "bpmn:ServiceTask",
  "serviceType": "Orchestrator.StartAgentJob",
  "version": "v2",
  "section": "Published",
  "bindings": {
    "resource": "process",
    "resourceSubType": "Agent",
    "resourceKey": "guy.vanwert@uipath.com's workspace/Debug_DevConnect.EmailAgent",
    "orchestratorType": "agent",
    "values": {
      "name": "EmailAgent",
      "folderPath": "guy.vanwert@uipath.com's workspace/Debug_DevConnect"
    }
  },
  "context": [
    {
      "name": "name",
      "type": "string",
      "value": "=bindings.bLjPZz5av",
      "default": "EmailAgent"
    },
    {
      "name": "folderPath",
      "type": "string",
      "value": "=bindings.bx1RWLtLM",
      "default": "guy.vanwert@uipath.com's workspace/Debug_DevConnect"
    },
    {
      "name": "_label",
      "type": "string",
      "value": "EmailAgent"
    }
  ]
}
```

Corresponding bindings:

```json
[
  {
    "id": "bLjPZz5av",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "guy.vanwert@uipath.com's workspace/Debug_DevConnect.EmailAgent",
    "default": "EmailAgent",
    "propertyAttribute": "name",
    "resourceSubType": "Agent"
  },
  {
    "id": "bx1RWLtLM",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "guy.vanwert@uipath.com's workspace/Debug_DevConnect.EmailAgent",
    "default": "guy.vanwert@uipath.com's workspace/Debug_DevConnect",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Agent"
  }
]
```

The `resourceKey` format for personal workspace agents is: `<email>'s workspace/<ProjectName>.<AgentName>`

The `folderPath` is the workspace prefix without the agent name: `<email>'s workspace/<ProjectName>`

## Agent Nodes vs HITL Nodes

Do not confuse agent resource nodes with the out-of-the-box `uipath.human-in-the-loop` node. They serve different purposes and have different structures.

| Property | Agent Nodes | HITL Node |
|---|---|---|
| Type pattern | `uipath.core.agent.<KEY>` | `uipath.human-in-the-loop` |
| Purpose | Run AI agents in Orchestrator | Create human review tasks |
| `model.serviceType` | `Orchestrator.StartAgentJob` | N/A (OOTB bundled node) |
| Registry data required | Yes (`uip registry pull`) | No (bundled in skill) |
| Requires `uip login` | Yes | No |
| Definition source | Pulled from Orchestrator registry | Bundled with the flow runtime |
| Binding entries | 2 per agent (`name` + `folderPath`) | None (OOTB) |

## Common Mistakes

1. **Using `Orchestrator.StartJob` instead of `Orchestrator.StartAgentJob`.** Process nodes use `StartJob`; agent nodes use `StartAgentJob`. Using the wrong service type causes the agent to be treated as an RPA process.

2. **Forgetting to add 2 binding entries to `workflow.bindings`.** Every agent node requires both a `name` binding and a `folderPath` binding in the top-level bindings array. Missing either one causes runtime binding resolution failures.

3. **Confusing agent nodes with the OOTB HITL node.** Agent nodes (`uipath.core.agent.*`) run autonomous AI agents. The HITL node (`uipath.human-in-the-loop`) creates human review tasks. They are unrelated despite both involving "people in the loop."

4. **Using UUID format for personal workspace agents.** When the agent is published from a personal workspace, the `resourceKey` is a path string (e.g., `"guy.vanwert@uipath.com's workspace/Debug_DevConnect.EmailAgent"`), not a UUID. Using a UUID here causes the agent to not be found.

5. **Not running `registry pull` before searching for agents.** Agent definitions come from the Orchestrator registry. Run `uip registry pull --output json` before searching for available agents, or the registry cache will be empty.

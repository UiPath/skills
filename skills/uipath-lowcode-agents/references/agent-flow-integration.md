# Agent Flow Integration Guide

Three distinct patterns for using low-code agents inside UiPath Flow projects.
Validated against `ValidSolutions/ExamplifyingThreeWaysOfUsingAgentsInFlow`.

---

## The Five Patterns

| Pattern | Node type | Agent lives in | `model.section` |
|---------|-----------|----------------|-----------------|
| **1. Inline** | `uipath.agent.autonomous` | The `.flow` file | *(not a service task)* |
| **2. Solution agent** | `uipath.core.agent.<process-key>` | Agent project in same solution | `"In this solution"` |
| **3. External agent** | `uipath.core.agent.<process-key>` | Orchestrator, outside this solution | `"Published"` |
| **4. External agent tool** | `uipath.agent.resource.tool.agent.<process-key>` | Orchestrator, outside this solution | `"Published"` |
| **5. Solution agent tool** | `uipath.agent.resource.tool.agent.<process-key>` | Agent project in same solution | `"In this solution"` |

Patterns 2 and 3 share the node type format `uipath.core.agent.<guid>`. Patterns 4 and 5 share the node type format `uipath.agent.resource.tool.agent.<guid>` — they mirror Patterns 3 and 2 respectively, but are wired to an inline agent's `tool` handle instead of the main flow sequence.

---

## Pattern 1: Inline Agent Node

### When to use

- Agent is tightly coupled to this specific flow
- No need for separate versioning, evaluation, or reuse across flows
- Fastest to set up — no separate agent project required

### Node types

| Node type | Description |
|-----------|-------------|
| `uipath.agent.autonomous` | Autonomous reasoning agent |

### `.flow` node structure

```jsonc
{
  "id": "myAgent",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0.0",
  "inputs": {
    "systemPrompt": "You are a helpful assistant.",
    "userPrompt": "=js: $vars.userInput",   // Flow variable reference
    "model": "gpt-4o-2024-11-20",
    "temperature": 0,
    "maxTokenPerResponse": 16384,
    "maxIterations": 25,
    "guardrails": []
  },
  "model": {
    "agentProjectId": "<stable-uuid>"
    // NOT a bpmn:ServiceTask — only agentProjectId
    // This UUID is assigned at node creation and must never change.
    // It becomes the projectId in the extracted agent.json at pack time.
  }
}
```

### Handles

| Handle | Position | Allowed connections |
|--------|----------|---------------------|
| `escalation` | top | `uipath.agent.resource.escalation` |
| `context` | bottom | `uipath.agent.resource.context.*` |
| `tool` | bottom | `uipath.agent.resource.tool.*` |
| `input` | left | Previous flow node |
| `success` | right | Next flow node |
| `error` | right | Error handler (when enabled) |

### Resource nodes (tools, contexts, escalations)

Resources are separate canvas nodes wired to the agent via artifact handle edges:

```jsonc
// Agent-as-tool for an inline agent (Pattern 1 + Pattern 3 combined)
{
  "id": "agentTool1",
  "type": "uipath.agent.resource.tool.agent.65eca26d-b9e6-43ae-9aab-5d2ff38ffa0c",
  //       ^ format: uipath.agent.resource.tool.agent.<process-key>
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "Shared/DateAgent.Agent",
      "values": { "name": "Agent", "folderPath": "Shared/DateAgent" }
    }
  }
}

// Edge connecting tool to agent:
// sourceNodeId: "myAgent", sourcePort: "tool"
// targetNodeId: "agentTool1", targetPort: "input"
```

| Resource type | Node type pattern |
|--------------|-------------------|
| RPA process | `uipath.agent.resource.tool.rpa` |
| Agent-as-tool (external) | `uipath.agent.resource.tool.agent.<process-key>` |
| IS connector | `uipath.agent.resource.tool.connector` |
| Semantic index | `uipath.agent.resource.context.index` |
| Escalation | `uipath.agent.resource.escalation` |
| MCP server | `uipath.agent.resource.mcp.*` |
| Memory space | `uipath.agent.resource.memory.*` |

### What happens at pack time

`flow-workbench` extracts inline agents during `uip solution bundle` / `uip solution pack`:

1. Scans for `uipath.agent.*` nodes (not `uipath.agent.resource.*`)
2. Collects connected resource nodes via artifact handles
3. Converts to `AgentDefinition` (`version: "1.1.0"`, `storageVersion: "48.0.0"`)
4. Writes into package:

```
content/
├── process.bpmn
├── operate.json            # contentType: "Flow"
├── entry-points.json       # type: "processorchestration"
├── bindings_v2.json
└── agents/
    └── <agentProjectId>/
        ├── agent.json      # Extracted AgentDefinition
        └── .agent-builder/
            ├── agent.json  # Execution model
            └── bindings.json
```

### Variable references in prompts

```jsonc
// Reference previous node output
"userPrompt": "=js: $vars.fetchData.response"

// String interpolation
"userPrompt": "=js: `Order for ${$vars.customerName}, ID: ${$vars.orderId}`"

// Literal text (no expression)
"userPrompt": "What is the current date?"
```

---

## Pattern 2: Solution Agent

### When to use

- Agent needs its own configuration, evaluation, or independent updates
- Multiple flows in the same solution call the same agent
- Agent needs to be opened and edited in the agent designer (Studio Web)

### Prerequisites

1. An agent project exists in the same solution (created via `uip low-code-agent init` + `uip solution project add`)
2. The solution has been uploaded to Studio Web at least once so the agent process resource key is assigned

### Node type format

```
uipath.core.agent.<process-resource-key>
```

The `<process-resource-key>` = the `key` field in `resources/solution_folder/process/agent/<AgentName>.json`.

### `.flow` node structure

```jsonc
{
  "id": "solutionAgentNode",
  "type": "uipath.core.agent.e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",
  "typeVersion": "1.0.0",
  "display": { "label": "AgentFromTheCurrentSolution" },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "version": "v2",
    "section": "In this solution",          // ← REQUIRED: distinguishes from external
    "skipBindingsReference": true,           // ← Does NOT use name+folder lookup
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",  // ← process key UUID
      "orchestratorType": "agent",
      "values": {
        "name": "Agent 1",
        "folderPath": ""              // ← Empty: resolved to solution folder at deploy time
      }
    },
    "projectId": "ce1da495-f9c2-4e62-871d-b18b4ef6e2c8",   // ← SolutionStorage ProjectId
    "projectName": "Agent 1"
  }
}
```

### Flow-level bindings (root `bindings` array)

```jsonc
{
  "id": "blzrLJIVV",
  "name": "name",
  "resource": "process",
  "resourceKey": "e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",  // ← UUID (process key)
  "default": "Agent 1",
  "propertyAttribute": "name",
  "resourceSubType": "Agent"
},
{
  "id": "bOWen1SOq",
  "name": "folderPath",
  "resource": "process",
  "resourceKey": "e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",
  "default": "",          // ← Empty = resolved at deploy time
  "propertyAttribute": "folderPath",
  "resourceSubType": "Agent"
}
```

### Resource files required

**`resources/solution_folder/package/Agent_1.json`:**
```jsonc
{
  "resource": {
    "name": "Agent 1",
    "kind": "package",
    "projectKey": "<uipx-project-Id>",  // From .uipx Projects[].Id
    "spec": { "name": "Agent 1", "fileName": null, "fileReference": null },
    "key": "<package-resource-uuid>"
  }
}
```

**`resources/solution_folder/process/agent/Agent_1.json`:**
```jsonc
{
  "resource": {
    "name": "Agent 1",
    "kind": "process",
    "type": "agent",
    "projectKey": "<uipx-project-Id>",  // Same as package
    "dependencies": [{ "name": "Agent 1", "kind": "package" }],
    "spec": {
      "type": "Agent",
      "packageName": "<SolutionName>.agent.<AgentName>",  // spaces → dots
      "package": { "key": "<package-resource-uuid>" }
    },
    "key": "<process-resource-key>"  // ← This UUID goes in the node type
  }
}
```

### UUID cross-reference

Three separate IDs for an agent project — do not confuse them:

```
(A) agent.json.projectId = SolutionStorage.json.ProjectId = flow node.model.projectId
(B) .uipx.Projects[].Id = resources/.../package/Agent_1.json.resource.projectKey
(C) resources/.../process/agent/Agent_1.json.resource.key = flow node.type GUID
                                                           = flow bindings.resourceKey
```

Studio Web assigns these IDs. Do not set them manually — they are assigned when the solution is created/uploaded.

---

## Pattern 3: External Agent

### When to use

- Agent is deployed in Orchestrator from a **different** solution
- Agent is shared across multiple solutions
- Agent has its own independent lifecycle (versioning, deployment)

### Node type format

Same format as Pattern 2:
```
uipath.core.agent.<process-resource-key>
```

But the GUID is from `resources/solution_folder/process/agent/<AgentName>.json` where the process references the external package.

### `.flow` node structure

```jsonc
{
  "id": "externalAgentNode",
  "type": "uipath.core.agent.65eca26d-b9e6-43ae-9aab-5d2ff38ffa0c",
  "typeVersion": "1.0.0",
  "display": { "label": "AgentExternalToThisSolution" },
  "outputs": {
    "output": {
      "type": "object",
      "source": "=this",
      "schema": { "type": "object", "properties": { "content": { "type": "string" } } }
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "version": "v2",
    "section": "Published",               // ← REQUIRED: distinguishes from solution agent
    // NO skipBindingsReference            // ← Uses name+folder bindings
    // NO projectId                        // ← Not a project in this solution
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "Shared/DateAgent.Agent",   // ← "FolderPath/PackageName.AgentName"
      "orchestratorType": "agent",
      "values": {
        "name": "Agent",
        "folderPath": "Shared/DateAgent"          // ← Actual Orchestrator folder
      }
    }
  }
}
```

### Flow-level bindings (root `bindings` array)

```jsonc
{
  "id": "bAJbQElpP",
  "name": "name",
  "resource": "process",
  "resourceKey": "Shared/DateAgent.Agent",   // ← "Folder/PackageName.AgentName" format
  "default": "Agent",
  "propertyAttribute": "name",
  "resourceSubType": "Agent"
},
{
  "id": "ba77VTCCJ",
  "name": "folderPath",
  "resource": "process",
  "resourceKey": "Shared/DateAgent.Agent",
  "default": "Shared/DateAgent",             // ← Actual Orchestrator folder path
  "propertyAttribute": "folderPath",
  "resourceSubType": "Agent"
}
```

### Resource files for external agent

The solution bundles the external agent's **published NuGet package** so it can be reproduced at deployment time.

**`resources/solution_folder/package/DateAgent.agent.Agent.json`:**
```jsonc
{
  "resource": {
    "name": "DateAgent.agent.Agent",
    "kind": "package",
    // No projectKey — external agent
    "files": [
      {
        "name": "DateAgent.agent.Agent.1.0.0.nupkg",
        "kind": "Package",
        "version": "1.0.0",
        "url": "https://{org}.uipath.com/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.DownloadPackage(key='DateAgent.agent.Agent:1.0.0')?feedId=...",
        "key": "DateAgent.agent.Agent_1.0.0"
      }
    ],
    "spec": {
      "fileName": "DateAgent.agent.Agent.1.0.0.nupkg",
      "fileReference": "DateAgent.agent.Agent_1.0.0",
      "name": "DateAgent.agent.Agent"
    },
    "key": "DateAgent.agent.Agent:1.0.0"
  }
}
```

**`resources/solution_folder/process/agent/Agent.json`:**
```jsonc
{
  "resource": {
    "name": "Agent",
    "kind": "process",
    "type": "agent",
    // No projectKey — external agent
    "dependencies": [
      { "name": "DateAgent.agent.Agent", "kind": "Package" }  // ← capital P for external
    ],
    "spec": {
      "type": "Agent",
      "packageName": "DateAgent.agent.Agent",
      "packageVersion": "1.0.0",     // ← explicitly pinned for external
      "package": {
        "name": "DateAgent.agent.Agent",
        "key": "DateAgent.agent.Agent:1.0.0"
      },
      "entryPointUniqueId": "...",    // ← known at bundle time for external
      "entryPointName": "content/agent.json"
    },
    "key": "65eca26d-b9e6-43ae-9aab-5d2ff38ffa0c"  // ← This GUID → node type
  }
}
```

**Key differences between Pattern 2 and Pattern 3 resource files:**

| Field | Pattern 2 (Solution) | Pattern 3 (External) |
|-------|----------------------|----------------------|
| `resource.projectKey` | present (`.uipx` Id) | absent |
| `dependencies[].kind` | `"package"` (lowercase) | `"Package"` (capital) |
| `files[]` in package | empty (`[]`) | populated with NuGet URL |
| `spec.packageVersion` | `null` (set at pack time) | explicit version string |
| `spec.entryPointUniqueId` | `null` | populated |

---

## Pattern 4: External Agent Tool Node

### What it is

An **external** agent (Pattern 3) used as a **tool** for an inline agent (Pattern 1). The tool node connects to the inline agent's `tool` handle. The inline agent calls it during reasoning; results return to the inline agent, not to the main flow sequence.

Pattern 4 is NOT a standalone flow node — it only exists attached to a Pattern 1 inline agent.

### Node type format

```
uipath.agent.resource.tool.agent.<process-key>
```

Same `<process-key>` as the corresponding Pattern 3 node. The `model` is **identical** to Pattern 3.

### `.flow` node structure

```jsonc
{
  "id": "agentTool",
  "type": "uipath.agent.resource.tool.agent.65eca26d-b9e6-43ae-9aab-5d2ff38ffa0c",
  "display": { "label": "Agent Tool", "shape": "circle" },
  "inputs": { "guardrails": [] },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "section": "Published",           // ← identical to Pattern 3
    // NO skipBindingsReference, NO projectId
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "Shared/DateAgent.Agent",
      "values": { "name": "Agent", "folderPath": "Shared/DateAgent" }
    }
  }
}
```

### Edge

```jsonc
{
  "sourceNodeId": "<inline-agent-id>",
  "sourcePort": "tool",
  "targetNodeId": "<tool-node-id>",
  "targetPort": "input"
}
```

### Resource files

Pattern 4 reuses the **same resource definition files** as Pattern 3. No additional files needed.

---

## Pattern 5: Solution Agent Tool Node

### What it is

A **solution** agent (Pattern 2) used as a **tool** for an inline agent (Pattern 1). Structurally identical to Pattern 4, but the backing agent is a project in the same solution.

### Node type format

```
uipath.agent.resource.tool.agent.<process-key>
```

Same `<process-key>` as the corresponding Pattern 2 node. The `model` is **identical** to Pattern 2.

### `.flow` node structure

```jsonc
{
  "id": "solutionAgentTool",
  "type": "uipath.agent.resource.tool.agent.e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",
  "display": { "label": "Agent 1 (tool)", "shape": "circle" },
  "inputs": { "guardrails": [] },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "section": "In this solution",   // ← identical to Pattern 2
    "skipBindingsReference": true,
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",  // process key UUID
      "values": { "name": "Agent 1", "folderPath": "" }
    },
    "projectId": "ce1da495-f9c2-4e62-871d-b18b4ef6e2c8",
    "projectName": "Agent 1"
  }
}
```

### Edge

```jsonc
{
  "sourceNodeId": "<inline-agent-id>",
  "sourcePort": "tool",
  "targetNodeId": "solutionAgentTool",
  "targetPort": "input"
}
```

### Resource files

Pattern 5 reuses the **same resource definition files** as Pattern 2. No additional files needed.

---

## Key Differences Summary

| | P1: Inline | P2: Solution | P3: External | P4: Ext. Tool | P5: Sol. Tool |
|--|------------|-------------|-------------|--------------|--------------|
| Node type | `uipath.agent.autonomous` | `uipath.core.agent.<guid>` | `uipath.core.agent.<guid>` | `uipath.agent.resource .tool.agent.<guid>` | `uipath.agent.resource .tool.agent.<guid>` |
| `model.section` | — | `"In this solution"` | `"Published"` | `"Published"` | `"In this solution"` |
| `model.skipBindingsReference` | — | `true` | absent | absent | `true` |
| `model.projectId` | — | present | absent | absent | present |
| `resourceKey` format | — | UUID | `"Folder/Pkg.Agent"` | `"Folder/Pkg.Agent"` | UUID |
| `folderPath` | — | `""` | actual folder | actual folder | `""` |
| Sits in flow sequence | ✓ | ✓ | ✓ | ✗ | ✗ |
| Resource files | none | package + process | package (with files) + process | shares P3 | shares P2 |
| Handles for tools/contexts | ✓ | ✗ | ✗ | ✗ | ✗ |
| Edit prompts | In flow canvas | In `agent.json` | In source solution | In source solution | In `agent.json` |
| Separate evals | ✗ | ✓ | ✓ | ✓ (same agent) | ✓ (same agent) |

---

## Pattern Selection Guide

| Requirement | Use pattern |
|-------------|-------------|
| Prototype or one-off agent for this flow only | 1 (Inline) |
| Agent + flow in same solution, agent needs its own evals | 2 (Solution) |
| Multiple flows in same solution call the same agent | 2 (Solution) |
| Agent deployed in Orchestrator from another solution | 3 (External) |
| Agent shared across many solutions/flows | 3 (External) |
| Inline agent needs to call an external agent as a tool | 1 + 4 |
| Inline agent needs to call a solution agent as a tool | 1 + 5 |

---

## Solution Node Type Quick Reference

```
uipath.agent.autonomous                               ← Pattern 1: Inline agent

uipath.agent.resource.tool.rpa                        ← Tool: RPA process
uipath.agent.resource.tool.agent.<process-key>        ← Pattern 4 (section: Published) or Pattern 5 (section: In this solution)
uipath.agent.resource.tool.connector                  ← Tool: IS connector
uipath.agent.resource.tool.api                        ← Tool: API
uipath.agent.resource.tool.builtin                    ← Tool: built-in
uipath.agent.resource.context.index                   ← Context: semantic index
uipath.agent.resource.escalation                      ← Escalation: HITL
uipath.agent.resource.mcp.*                           ← MCP server
uipath.agent.resource.memory.*                        ← Memory space

uipath.core.agent.<process-key>                       ← Solution OR external agent node
  └─ model.section = "In this solution"               ← Pattern 2: solution agent
  └─ model.section = "Published"                      ← Pattern 3: external agent
```

---

## Debug Overwrites

Override resource resolution for debug runs without full reprovisioning:

**`userProfile/{userId}/debug_overwrites.json`:**
```jsonc
{
  "docVersion": "1.0.0",
  "tenants": [
    {
      "tenantKey": "<tenant-uuid>",
      "resources": [
        {
          "solutionResourceKey": "<process-resource-key>",
          // ^^^ matches resources/solution_folder/process/agent/*.json → resource.key
          "reprovisioningIndex": 0,
          "overwrite": {
            "resourceKey": "<orchestrator-resource-uuid>",
            "resourceName": "Agent",
            "folderKey": "<orchestrator-folder-uuid>",
            "folderFullyQualifiedName": "Shared/DateAgent",
            "folderPath": "<orchestrator-folder-uuid>",
            "type": "Reference",   // "Reference" = reuse existing; "New" = provision new
            "kind": "process"
          }
        }
      ]
    }
  ]
}
```

---

## BPMN Execution Engine Notes

- **Inline agents (Pattern 1)**: At pack time, compiled to BPMN `ServiceTask` with `ExtensionType: "UiPath.AgentTask"`. Engine calls `OverwatchRunAgentActivityAsync`.
- **Solution/external agents (Patterns 2 & 3)**: `ServiceTask` with `serviceType: "Orchestrator.StartAgentJob"`. Engine calls Orchestrator to start the agent job.

Both execution paths are asynchronous (Temporal-based). The flow pauses at the agent node and resumes when the agent job completes.

For more detail see `docs/agents-in-flow-guide.md`.

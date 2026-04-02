---
name: uipath-low-code-agents
description: "This skill should be used when the user wants to 'create a low-code agent project', 'scaffold a new agent', 'add an agent to a solution', 'init an agent with uip low-code-agent', 'create a solution with agent projects', 'link an agent to a solution', 'add an agent node to a flow', 'configure agent tools or contexts', 'set up RAG for an agent', 'wire agent-to-agent calls', 'add escalations to an agent', 'publish or deploy a low-code agent solution', 'evaluate an agent', 'pack or bundle an agent solution', 'upload an agent solution to Studio Web', 'configure agent bindings', or 'manage agent.json'. TRIGGER when: user mentions low-code agent, agent.json, uip low-code-agent init/build, uip solution pack/publish/deploy, or wants to create/manage an agent project inside a solution or flow. DO NOT TRIGGER when: user is writing Python coded agents (use uipath-coded-agents), building a flow without an agent (use uipath-flow), or doing pure solution/Orchestrator management unrelated to agent projects (use uipath-platform)."
metadata:
  allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Low-Code Agents

## When to Use This Skill

- Scaffold a new low-code agent project (`uip low-code-agent init`)
- Create a solution that contains one or more agent projects
- Add an agent project to an existing solution
- Configure agent.json: system/user prompts, model settings, input/output schema
- Add tools to an agent: RPA processes, other agents, Integration Service connections
- Add RAG contexts (semantic index) to an agent
- Add escalations (human-in-the-loop) to an agent
- Wire agent-to-agent invocations within a solution
- Pack, bundle, publish, and deploy agent solutions (`uip solution` commands)
- Upload solutions to Studio Web for visual development
- Run evaluations on an agent
- Add an inline agent node to a flow (use alongside `uipath-flow` skill)
- Reference an already-deployed agent from a flow node

## Critical Rules

1. **NEVER hand-write agent.json from scratch.** Always use `uip low-code-agent init` to generate the scaffold, then edit the result. The format has many auto-generated fields (`storageVersion`, `contentTokens`, UUIDs) that must be consistent.

2. **NEVER edit `.agent-builder/` files manually.** These are generated build artifacts. Edit `agent.json` at the project root, then regenerate with `uip low-code-agent build`.

3. **Run `uip low-code-agent build` after every `agent.json` edit** (add/remove tools, contexts, resources) before packing or uploading the solution.

4. **`uip low-code-agent init` creates ONLY the agent project.** It does NOT create solution files. Create solutions separately with `uip solution new`, then link with `uip solution project add`.

5. **All solution lifecycle operations go through `uip solution`.** Pack, bundle, upload, publish, deploy, activate, uninstall — all via `uip solution` commands. Never use raw REST API calls for these.

6. **Use `"folderPath": "solution_folder"` for resources internal to the solution.** This is the magic placeholder that resolves to the actual deployment folder. External resources (not part of the solution) use their real folder path (e.g., `"Shared"`, `"Shared/TestRPA"`).

7. **Agents that call other solution agents must use `"location": "solution"` in the resource definition.** External agent processes use `"location": "external"`.

8. **Always run `uip login status` before any `uip solution` command.** If not logged in, run `uip login` first.

9. **Use `--output json` on all `uip` commands when parsing output programmatically.**

10. **The `projectId` in `agent.json` must match the `ProjectId` in `SolutionStorage.json`.** This link is established by `uip low-code-agent init` and maintained by `uip solution project add`. Never change it manually.

11. **For agent-in-flow scenarios, follow the `uipath-flow` skill** for all flow operations. Use this skill only for the agent-specific configuration (agent node inputs, resource wiring).

12. **Do NOT run `uip solution publish` or `uip solution deploy` without explicit user consent.** These modify shared Orchestrator state.

13. **The `storageVersion` field in agent.json should never be manually edited.** It is managed by Studio Web and the packager. The current version is 50.0.0 (cloud designer).

14. **There are 5 agent-in-flow patterns.** `uipath.agent.autonomous` = inline (P1). `uipath.core.agent.<guid>` with `section: "In this solution"` = solution agent (P2). `uipath.core.agent.<guid>` with `section: "Published"` = external agent (P3). `uipath.agent.resource.tool.agent.<guid>` with `section: "Published"` = external agent tool (P4). `uipath.agent.resource.tool.agent.<guid>` with `section: "In this solution"` = solution agent tool (P5). P4 and P5 only connect to an inline agent's `tool` handle — never to the main flow sequence.

15. **Never invoke other skills automatically.** If the user needs flow operations, tell them to use the `uipath-flow` skill.

---

## Quick Start: Scenario 1 — New Solution with New Agent Projects

Use this when nothing exists yet. Create the solution first, then create agent projects and link them.

```bash
# 1. Verify login
uip login status --output json

# 2. Create the solution (creates MySolution.uipx + SolutionStorage.json)
uip solution new "MySolution" --output json

# 3. Scaffold agent projects inside the solution directory
#    init creates ONLY the agent project files — no solution files
uip low-code-agent init ./MySolution/Agent --model gpt-4o-2024-11-20 --output json
uip low-code-agent init ./MySolution/Agent2 --model gpt-4o-2024-11-20 --output json

# 4. Link each agent project to the solution
uip solution project add ./MySolution/Agent ./MySolution/MySolution.uipx --output json
uip solution project add ./MySolution/Agent2 ./MySolution/MySolution.uipx --output json

# 5. Edit agent.json files to configure prompts, model, tools (see References)

# 6. Rebuild .agent-builder artifacts after editing
uip low-code-agent build ./MySolution/Agent --output json
uip low-code-agent build ./MySolution/Agent2 --output json

# 7. Upload solution to Studio Web for visual development
uip solution upload ./MySolution --output json

# 8. For deployment: pack → publish → deploy
uip solution pack ./MySolution ./output -v "1.0.0" --output json
uip solution publish ./output/MySolution.1.0.0.zip --output json
uip solution deploy run \
  --name "MySolution-v1" \
  --package-name "MySolution" \
  --package-version "1.0.0" \
  --folder-name "MySolution" \
  --folder-path "Shared" \
  --output json
```

---

## Quick Start: Scenario 2 — Add Agent Project to Existing Solution

Use this when a solution already exists on disk.

```bash
# 1. Scaffold a new agent project inside the existing solution directory
uip low-code-agent init ./ExistingSolution/NewAgent --model gpt-4o-2024-11-20 --output json

# 2. Link to the solution
uip solution project add ./ExistingSolution/NewAgent ./ExistingSolution/ExistingSolution.uipx --output json

# 3. Edit agent.json as needed (see agent-file-format.md)

# 4. Rebuild .agent-builder artifacts
uip low-code-agent build ./ExistingSolution/NewAgent --output json

# 5. Upload updated solution to Studio Web
uip solution upload ./ExistingSolution --output json
```

---

## Quick Start: Scenario 3 — Five Patterns for Agents in Flows

There are five distinct patterns. Use `references/agent-flow-integration.md` for full detail.

### Pattern 1: Inline agent (defined in the flow canvas)

The agent lives entirely inside the `.flow` file. No separate agent project required.

```jsonc
// In the .flow file — inline agent node
{
  "id": "myAgent",
  "type": "uipath.agent.autonomous",   // only autonomous is in scope for this skill
  "typeVersion": "1.0.0",
  "inputs": {
    "systemPrompt": "You are a helpful assistant.",
    "userPrompt": "=js: $vars.userInput",
    "model": "gpt-4o-2024-11-20",
    "temperature": 0,
    "maxTokenPerResponse": 16384,
    "maxIterations": 25,
    "guardrails": []
  },
  "model": {
    "agentProjectId": "<stable-uuid>"
    // NOT a bpmn:ServiceTask — agentProjectId only
    // Assigned once at node creation; never change it
  }
}
```

Tools are separate resource nodes wired via the `tool` handle:

| Resource | Node type |
|----------|-----------|
| Agent-as-tool | `uipath.agent.resource.tool.agent.<process-key>` |
| RPA process | `uipath.agent.resource.tool.rpa` |
| IS connector | `uipath.agent.resource.tool.connector` |
| Semantic index | `uipath.agent.resource.context.index` |
| Escalation | `uipath.agent.resource.escalation` |

### Pattern 2: Solution agent (agent project in same solution)

The agent is a separate project in the same solution. It appears as a `uipath.core.agent.<guid>` node with `section: "In this solution"`.

**Prerequisites:**
1. Create the agent project: `uip low-code-agent init ./MySolution/MyAgent`
2. Link to solution: `uip solution project add ./MySolution/MyAgent ./MySolution/MySolution.uipx`
3. Upload to Studio Web: `uip solution upload ./MySolution`
4. In Studio Web, add the agent to the flow — Studio Web assigns the process resource key

**Key node fields:**
```jsonc
{
  "type": "uipath.core.agent.<process-resource-key>",
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "section": "In this solution",    // ← identifies as solution agent
    "skipBindingsReference": true,    // ← folder resolved at deploy time
    "projectId": "<SolutionStorage-ProjectId>",
    "bindings": {
      "resourceKey": "<process-resource-key>",  // UUID
      "values": { "name": "MyAgent", "folderPath": "" }
    }
  }
}
```

### Pattern 3: External agent (deployed in Orchestrator from outside)

The agent is deployed from a **different** solution. It also uses `uipath.core.agent.<guid>` but with `section: "Published"` and explicit name+folderPath.

**Prerequisites:** The agent solution must be deployed to Orchestrator first.

**Key node fields:**
```jsonc
{
  "type": "uipath.core.agent.<process-resource-key>",
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "section": "Published",           // ← identifies as external agent
    // NO skipBindingsReference
    // NO projectId
    "bindings": {
      "resourceKey": "Shared/MyAgent.Agent",    // "FolderPath/PackageName.AgentName"
      "values": { "name": "Agent", "folderPath": "Shared/MyAgent" }
    }
  }
}
```

### Pattern 4: External agent tool node

An **external** agent wired to an inline agent's `tool` handle. `model` is identical to Pattern 3.

**Node type:** `uipath.agent.resource.tool.agent.<process-key>`

```jsonc
{
  "type": "uipath.agent.resource.tool.agent.65eca26d-b9e6-43ae-9aab-5d2ff38ffa0c",
  "display": { "label": "External Tool Agent", "shape": "circle" },
  "inputs": { "guardrails": [] },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "section": "Published",           // identical to Pattern 3
    "bindings": {
      "resource": "process", "resourceSubType": "Agent",
      "resourceKey": "Shared/DateAgent.Agent",
      "values": { "name": "Agent", "folderPath": "Shared/DateAgent" }
    }
  }
}
```

Edge: `sourcePort: "tool"` on the inline agent → `targetPort: "input"` on this node.
Reuses the same `resources/solution_folder/` files as Pattern 3.

### Pattern 5: Solution agent tool node

A **solution** agent wired to an inline agent's `tool` handle. `model` is identical to Pattern 2.

**Node type:** `uipath.agent.resource.tool.agent.<process-key>`

```jsonc
{
  "type": "uipath.agent.resource.tool.agent.e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",
  "display": { "label": "Solution Tool Agent", "shape": "circle" },
  "inputs": { "guardrails": [] },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "section": "In this solution",   // identical to Pattern 2
    "skipBindingsReference": true,
    "bindings": {
      "resource": "process", "resourceSubType": "Agent",
      "resourceKey": "e10758d6-a4e6-4b29-89cf-1ecc5d456e1f",
      "values": { "name": "Agent 1", "folderPath": "" }
    },
    "projectId": "ce1da495-f9c2-4e62-871d-b18b4ef6e2c8",
    "projectName": "Agent 1"
  }
}
```

Edge: `sourcePort: "tool"` on the inline agent → `targetPort: "input"` on this node.
Reuses the same `resources/solution_folder/` files as Pattern 2.

---

## Quick Start: Scenario 4 — Deploying a Solution for Use as External Agent (Pattern 3)

Use this when you want to publish an agent solution so it can be referenced as Pattern 3 (external agent) from a different flow/solution.

```bash
# Step 1: Deploy the agent solution so it is available in Orchestrator
uip solution pack ./MyAgentSolution ./output -v "1.0.0" --output json
uip solution publish ./output/MyAgentSolution.1.0.0.zip --output json
uip solution deploy run \
  --name "MyAgentSolution-v1" \
  --package-name "MyAgentSolution" \
  --package-version "1.0.0" \
  --folder-name "MyAgentSolution" \
  --folder-path "Shared" \
  --output json

# Step 2: In the flow, add a resource node referencing the deployed agent
# First discover the node type
uip flow registry search agent --output json

# Add the agent resource node to the flow
uip flow node add MyFlow.flow "uipath.core.agent.<key>" --output json

# Step 3: The flow binding for this node in bindings_v2.json:
# {
#   "resource": "process",
#   "key": "<node-binding-key>",
#   "value": {
#     "name": { "defaultValue": "MyAgent", "isExpression": false },
#     "folderPath": { "defaultValue": "Shared/MyAgentSolution", "isExpression": false }
#   },
#   "metadata": { "subType": "Agent", "SolutionsSupport": "true" }
# }
```

---

## Solution Publish & Deploy Flow

Once the agent project is ready, all lifecycle operations use `uip solution`:

```bash
# 1. Rebuild .agent-builder artifacts (always do this after editing agent.json)
uip low-code-agent build ./MySolution/Agent --output json

# 2. Upload to Studio Web (for visual development / review)
uip solution upload ./MySolution --output json

# 3. Pack for Orchestrator deployment
uip solution pack ./MySolution ./output -v "1.0.0" --output json
# → ./output/MySolution.1.0.0.zip

# 4. Publish the package to Orchestrator
uip solution publish ./output/MySolution.1.0.0.zip --output json
# → { PackageVersionKey, PackageName, PackageVersion }

# 5. Deploy (installs and auto-activates)
uip solution deploy run \
  --name "MySolution-Production" \
  --package-name "MySolution" \
  --package-version "1.0.0" \
  --folder-name "MySolution" \
  --folder-path "Shared" \
  --output json
# → polls until DeploymentSucceeded
# → { Status, DeploymentKey, PipelineDeploymentId, InstanceId }

# 6. To activate an existing (previously installed) deployment
uip solution deploy activate "MySolution-Production" --output json
```

---

## Configuring agent.json

### Minimal agent.json template

See `references/agent-file-format.md` for the full format.

```jsonc
{
  "version": "1.1.0",
  "type": "lowCode",
  "projectId": "<uuid-from-SolutionStorage.json>",
  "settings": {
    "model": "gpt-4o-2024-11-20",
    "maxTokens": 16384,
    "temperature": 0,
    "engine": "basic-v2",
    "maxIterations": 25,
    "mode": "standard"
  },
  "metadata": {
    "storageVersion": "50.0.0",
    "isConversational": false,            // always false for low-code agents
    "targetRuntime": "pythonAgent",
    "showProjectCreationExperience": false
  },
  "messages": [
    { "role": "system", "content": "You are a helpful assistant.", "contentTokens": [] },
    { "role": "user", "content": "{{userInput}}", "contentTokens": [] }
  ],
  "inputSchema": {
    "type": "object",
    "title": "Agent Inputs",
    "properties": {
      "userInput": { "type": "string", "title": "User Input" }
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "content": { "type": "string", "description": "Agent response" }
    }
  },
  "resources": []
}
```

### Adding an RPA process tool

```jsonc
// In agent.json "resources" array:
{
  "$resourceType": "tool",
  "id": "<new-uuid>",
  "referenceKey": "<new-uuid>",
  "name": "MyProcess",
  "type": "process",
  "location": "external",   // "external" = in Orchestrator, not in this solution
  "description": "Runs the MyProcess RPA workflow",
  "inputSchema": {
    "type": "object",
    "properties": {
      "inputParam": { "type": "string" }
    },
    "required": ["inputParam"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "result": { "type": "string" }
    }
  },
  "isEnabled": true,
  "properties": {
    "processName": "MyProcess",
    "folderPath": "Shared"   // actual folder, not solution_folder (external)
  }
}
```

### Adding another solution agent as a tool

```jsonc
{
  "$resourceType": "tool",
  "id": "<new-uuid>",
  "referenceKey": "<new-uuid>",
  "name": "Agent2",
  "type": "agent",
  "location": "solution",   // "solution" = internal to this solution
  "description": "Calls Agent2 for specialized processing",
  "inputSchema": {
    "type": "object",
    "properties": {
      "agent2Input": { "type": "string" }
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "content2": { "type": "string" }
    }
  },
  "isEnabled": true,
  "properties": {
    "processName": "Agent2",
    "folderPath": "solution_folder"  // always "solution_folder" for solution-internal resources
  }
}
```

### Adding a RAG context (semantic index)

```jsonc
{
  "$resourceType": "context",
  "contextType": "index",
  "indexName": "MyIndex",
  "folderPath": "solution_folder",
  "settings": {
    "query": { "variant": "dynamic" },
    "retrievalMode": "semantic",
    "resultCount": 3,
    "threshold": 0,
    "fileExtension": "All"
  }
}
```

---

## Anti-Patterns

- **Do NOT** create a separate solution for each agent when they need to call each other — put them in the same solution.
- **Do NOT** use `folderPath: "solution_folder"` for truly external resources (existing Orchestrator processes not part of this solution) — use the actual folder path.
- **Do NOT** manually bump `storageVersion` — this breaks compatibility with the packager.
- **Do NOT** copy-paste UUIDs from one resource to another — every resource needs a unique UUID.
- **Do NOT** edit `contentTokens` arrays — they are auto-generated by Studio Web from the prompt content.
- **Do NOT** use `uip solution deploy` without explicit user consent — this modifies shared Orchestrator state.
- **Do NOT** leave `"isEnabled": false` on tools unless intentionally disabling them — disabled tools are not available to the agent.
- **Do NOT** call raw Automation.Solutions REST APIs for deploy/activate/uninstall — always use `uip solution deploy` commands instead.
- **Do NOT** forget to run `uip low-code-agent build` after editing `agent.json` — the `.agent-builder/` artifacts become stale and the pack/upload will use outdated bindings.

---

## References

- `references/agent-file-format.md` — Complete agent.json, entry-points.json, bindings.json formats
- `references/agent-commands.md` — All `uip low-code-agent` and `uip solution` CLI commands with flags and examples
- `references/agent-solution-guide.md` — Solution integration: resource definitions, bindings, package/process files
- `references/agent-flow-integration.md` — All 5 patterns: inline agent, solution agent, external agent, external agent tool node, solution agent tool node; node types, bindings, resource files

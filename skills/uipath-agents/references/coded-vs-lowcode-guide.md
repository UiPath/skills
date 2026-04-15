# Coded vs Low-Code Agent Selection Guide

Reference for comparing **coded** (Python) and **low-code** (agent.json) agents. Use this when the user needs help deciding which mode to choose.

## Capability Matrix

| Capability | Low-code | Coded |
|---|:---:|:---:|
| Build without writing Python | ✅ | ❌ |
| Call UiPath processes / API workflows as tools | ✅ | ✅ |
| Use Integration Service connectors | ✅ | ✅ |
| RAG over Context Grounding index | ✅ | ✅ |
| Use third-party Python libraries | ❌ | ✅ |
| Custom LLM state machine (LangGraph StateGraph) | ❌ | ✅ |
| Human-in-the-loop | ✅ escalation | ✅ `interrupt()` |
| Complex conditional HITL resume logic | ❌ | ✅ |
| Studio Web Agent Builder canvas | ✅ | Optional |
| `@mockable()` for evaluation isolation | ❌ | ✅ |
| Full runtime control over LLM prompts | ❌ | ✅ |
| Multi-model / multi-framework strategies | ❌ | ✅ |
| Fastest path to first working agent | ✅ | ❌ |
| Embed inline in a flow project | ✅ | ❌ |
| Embed as sibling project in same solution | ✅ | ✅ |
| Invoke as published agent node in a flow | ✅ | ✅ |
| Use as tool resource for another agent in a flow | ✅ | ✅ |
| Solution-level deployment with resource provisioning | ✅ | ❌ |

## Key Differences

| Aspect | Coded | Low-code |
|--------|-------|----------|
| Language | Python | Declarative JSON (`agent.json`) |
| CLI | `uip codedagent` | `uip agent` + `uip solution` |
| Project marker | `pyproject.toml` + `.py` files | `agent.json` + `project.uiproj` |
| Frameworks | LangGraph, LlamaIndex, OpenAI Agents, Simple Function | None (prompt + tools config) |
| Deployment | `uip codedagent deploy` | `uip solution pack/publish/deploy` |
| Local testing | `uip codedagent run` | Studio Web only |
| Evaluations | `uip codedagent eval` (13 evaluator types) | Not available |
| Flow integration | Inline, published node, tool resource (3 patterns) | Inline, published, solution, external, tool resource (5 patterns) |
| Solution support | Standalone projects | Full solution lifecycle |
| Custom code | Full Python | None |
| Sync | `uip codedagent push/pull` | `uip solution upload` |

## Solution-Level Mixing

A UiPath solution can contain **both** coded and low-code agent projects. Each project is independently one mode or the other — there is no hybrid within a single project.

### Pattern 1: Low-code orchestrator calling coded agent as tool

The low-code agent adds the coded agent as an **external tool** in its `resources[]` array:

```jsonc
{
  "$resourceType": "tool",
  "type": "agent",
  "location": "external",
  "properties": {
    "processName": "MyCodedAgent",
    "folderPath": "Shared/CodedAgents"
  }
}
```

The coded agent must be deployed to Orchestrator first via `uip codedagent deploy`.

### Pattern 2: Coded agent invoking low-code agent via SDK

The coded agent calls the deployed low-code agent as an Orchestrator process:

```python
sdk = UiPath()
result = await sdk.processes.invoke(
    name="MySolution.agent.MyLowCodeAgent",
    folder_path="Shared/MySolution",
    input_arguments={"userInput": "Hello"}
)
```

The low-code agent must be deployed via `uip solution deploy` first.

### Pattern 3: Mixed solution

A solution contains both project types, deployed together:

```
MySolution/
├── LowCodeAgent/      ← agent.json (low-code)
├── CodedAgent/        ← pyproject.toml + .py (coded)
├── resources/
└── MySolution.uipx
```

Each agent type uses its own CLI and lifecycle. The solution's `uip solution deploy` handles both.

## Interop Mechanisms

| From | To | Mechanism |
|------|----|-----------|
| Low-code | Coded (deployed) | Agent tool resource with `location: "external"` in `agent.json` |
| Coded | Low-code (deployed) | `sdk.processes.invoke()` targeting the deployed agent process |
| Low-code | Low-code (same solution) | Agent tool resource with `location: "solution"` in `agent.json` |
| Low-code | Low-code (different solution) | Agent tool resource with `location: "external"` in `agent.json` |
| Coded | Coded | `workflows.*` or `sdk.processes.invoke()` |
| Flow | Coded (deployed) | Published agent node (`uipath.core.agent.{key}`) in the flow |
| Flow | Low-code (deployed) | Published agent node (`uipath.core.agent.{key}`) in the flow |
| Flow (inline low-code agent) | Coded (deployed) | Tool resource (`uipath.agent.resource.tool.agent`) wired to the agent |

### Flow Integration Details

- **Low-code agents** support 5 Flow patterns: inline embedding, published node, solution-level, external, and tool resource
- **Coded agents** support 3 Flow patterns: in-solution sibling project (`uipath.core.agent.<resourceKey>` with `section: "In this solution"`), published node (`uipath.core.agent.<resourceKey>` via `uip codedagent deploy`), and tool resource
- **Low-code inline embedding**: `uip agent init --inline-in-flow` creates a `<projectId-uuid>` subdirectory inside the flow project
- **Coded solution-level embedding**: The coded agent lives as a sibling folder to the flow project; `uip solution project add` mints the `resource.key` that the flow's `uipath.core.agent.<resourceKey>` node references, discoverable via `uip maestro flow registry list --local` (see [coded/embedding-in-flows.md](coded/embedding-in-flows.md))
- Node types differ by pattern: inline low-code uses `uipath.agent.autonomous`; every other case (published low-code, in-solution coded, published coded) uses `uipath.core.agent.{key}`
- For coded agent Flow integration details, see [coded/flow-integration.md](coded/flow-integration.md)

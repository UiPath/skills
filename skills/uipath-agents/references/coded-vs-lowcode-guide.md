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
| Embed agent inline in a flow | ✅ | ❌ |
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
| Flow integration | Not supported | 5 patterns (inline, solution, external, tool variants) |
| Solution support | Standalone projects | Full solution lifecycle |
| Custom code | Full Python | None |
| Sync | `uip codedagent push/pull` | `uip solution bundle/upload` |

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

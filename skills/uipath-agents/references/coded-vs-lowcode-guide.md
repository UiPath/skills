# Coded vs Low-Code Agent Selection Guide

Use this reference to choose between **coded** (Python) and **low-code** (`agent.json`) agents.

## Capability matrix

| Capability | Low-code | Coded |
|---|:---:|:---:|
| Build without Python | ✅ | ❌ |
| Call UiPath processes/API workflows as tools | ✅ | ✅ |
| Integration Service connectors | ✅ | ✅ |
| RAG over Context Grounding index | ✅ | ✅ |
| Third-party Python libraries | ❌ | ✅ |
| Custom LLM state machine (`LangGraph StateGraph`) | ❌ | ✅ |
| Human-in-the-loop | ✅ escalation | ✅ `interrupt()` |
| Complex conditional HITL resume logic | ❌ | ✅ |
| Studio Web Agent Builder canvas | ✅ | Optional |
| `@mockable` evaluation isolation | ❌ | ✅ |
| Full LLM prompt runtime control | ❌ | ✅ |
| Multi-model/framework strategies | ❌ | ✅ |
| Fastest path to a working agent | ✅ | ❌ |
| Conversational, multi-turn use cases | ✅ | Currently not recommended for production; use low-code |
| Inline flow embedding | ✅ | ❌ |
| Sibling project in the same solution | ✅ | ✅ |
| Published agent node in a flow | ✅ | ✅ |
| Tool resource for another flow agent | ✅ | ✅ |
| Solution-level deployment and resource provisioning | ✅ | ❌ |

## Key differences

| Aspect | Coded | Low-code |
|---|---|---|
| Language | Python | Declarative JSON (`agent.json`) |
| CLI | `uip codedagent` | `uip agent` + `uip solution` |
| Project marker | `pyproject.toml` + `.py` files | `agent.json` + `project.uiproj` |
| Frameworks | LangGraph, LlamaIndex, OpenAI Agents, Coded Function | None; prompt + tools configuration |
| Deployment | `uip codedagent deploy` | `uip solution pack/publish/deploy` |
| Local testing | `uip codedagent run` | Studio Web only |
| Evaluations | `uip codedagent eval` (13 evaluator types) | Not available |
| Flow integration | Inline, published node, tool resource (3 patterns) | Inline, published, solution, external, tool resource (5 patterns) |
| Solution support | Standalone projects | Full solution lifecycle |
| Custom code | Full Python | None |
| Sync | `uip codedagent push/pull` | `uip solution upload` |

## Solution-level mixing

A solution may contain both agent types, but each project is exclusively coded or low-code; no hybrid project exists.

### Low-code orchestrator calling a coded agent

Add the deployed coded agent as an external tool in `resources[]`:

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

Run `uip codedagent deploy` before using the coded agent.

### Coded agent invoking a low-code agent

Invoke the deployed low-code agent as an Orchestrator process:

```python
sdk = UiPath()
result = await sdk.processes.invoke(
    name="MySolution.agent.MyLowCodeAgent",
    folder_path="Shared/MySolution",
    input_arguments={"userInput": "Hello"}
)
```

Run `uip solution deploy` before invoking the low-code agent.

### Mixed solution deployment

A mixed solution can contain:

```
MySolution/
├── LowCodeAgent/      ← agent.json (low-code)
├── CodedAgent/        ← pyproject.toml + .py (coded)
├── resources/
└── MySolution.uipx
```

Each project retains its own CLI and lifecycle. Run `uip solution deploy` to deploy both through the solution.

## Interop mechanisms

| From | To | Mechanism |
|---|---|---|
| Low-code | Coded (deployed) | Agent tool resource with `location: "external"` in `agent.json` |
| Coded | Low-code (deployed) | `sdk.processes.invoke()` targeting the deployed agent process |
| Low-code | Low-code (same solution) | Agent tool resource with `location: "solution"` in `agent.json` |
| Low-code | Low-code (different solution) | Agent tool resource with `location: "external"` in `agent.json` |
| Coded | Coded | `workflows.*` or `sdk.processes.invoke()` |
| Flow | Coded (deployed) | Published agent node (`uipath.core.agent.{key}`) |
| Flow | Low-code (deployed) | Published agent node (`uipath.core.agent.{key}`) |
| Flow (inline low-code agent) | Coded (deployed) | Tool resource (`uipath.agent.resource.tool.agent`) wired to the agent |

## Flow integration

- Low-code supports five patterns: inline embedding, published node, solution-level, external, and tool resource.
- Coded supports three patterns: in-solution sibling project (`uipath.core.agent.<resourceKey>` with `section: "In this solution"`), published node (`uipath.core.agent.<resourceKey>` via `uip codedagent deploy`), and tool resource.
- Run `uip agent init --inline-in-flow` to create a `<projectId-uuid>` subdirectory inside the flow project for inline low-code embedding.
- For coded solution-level embedding, place the coded agent in a sibling folder to the flow project. Run `uip solution projects add` to mint the `resource.key` referenced by the flow's `uipath.core.agent.<resourceKey>` node. Discover it with `uip maestro flow registry list --local` (see [coded/embedding-in-flows.md](coded/embedding-in-flows.md)).
- Inline low-code uses `uipath.agent.autonomous`; published low-code, in-solution coded, and published coded use `uipath.core.agent.{key}`.
- For coded Flow integration, see [coded/flow-integration.md](coded/flow-integration.md).

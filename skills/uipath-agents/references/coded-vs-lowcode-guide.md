# Coded vs Low-Code Agent Selection Guide

Use this guide to determine whether to build a **coded** (Python) or **low-code** (agent.json) agent.

## Decision Flowchart

Follow these steps in priority order. Stop at the first match.

| Priority | Check | Result |
|----------|-------|--------|
| 0 | User explicitly specified a mode? | **Use their choice** — never override |
| 1 | Existing project detected? (`pyproject.toml` = coded, `agent.json` with `"type": "lowCode"` = low-code) | **Match the project's mode** |
| 2 | Needs to be embedded in a `.flow` file? | **Low-code** — only low-code agents support inline flow integration |
| 3 | Needs custom Python logic, external libraries, or programmatic control? | **Coded** |
| 4 | Needs a specific framework (LangGraph, LlamaIndex, OpenAI Agents)? | **Coded** |
| 5 | Needs agent evaluations with evaluator configs? | **Coded** — eval framework is coded-only |
| 6 | Simple prompt + tools agent, no custom code needed? | **Low-code** |
| 7 | Part of a solution with flows? | **Low-code** |
| 8 | Default / ambiguous | **Ask the user** |

## Mode Selection Table

| Scenario | Mode | Reason |
|----------|------|--------|
| Simple prompt-based agent with tools (RPA, IS connectors) | **Low-code** | Declarative JSON config, no code needed |
| Agent embedded inline in a flow | **Low-code** | Only low-code supports `uipath.agent.autonomous` nodes |
| Multi-agent solution (parent orchestrates tool agents) | **Low-code** | Solution-level resource wiring, `uip solution` deployment |
| Complex multi-step reasoning with conditional routing | **Coded** | LangGraph StateGraph with conditional edges |
| RAG / knowledge retrieval with custom chunking | **Coded** | LlamaIndex or LangGraph with ContextGroundingVectorStore |
| Agent needs external Python libraries (pandas, requests, etc.) | **Coded** | Low-code has no custom code execution |
| Agent needs human-in-the-loop with LangGraph interrupts | **Coded** | `interrupt()` pattern is Python-only |
| Agent needs automated evaluation suite | **Coded** | `uip codedagent eval` is coded-only |
| Agent with custom data transforms or HTTP calls | **Coded** | Python is more natural than JSON config |
| Lightweight LLM agent with tools and handoffs | **Coded** | OpenAI Agents framework |
| Deterministic logic, no LLM | **Coded** | Simple Function agent |
| User explicitly requests a mode | **User's choice** | Never second-guess |

## Key Differences

| Aspect | Coded | Low-code |
|--------|-------|----------|
| Language | Python | Declarative JSON (`agent.json`) |
| CLI | `uip codedagent` | `uip low-code-agent` + `uip solution` |
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

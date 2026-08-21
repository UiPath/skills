# Classification Details — uipath-agents

**Classification: Partial**

---

## What the Skill Teaches

End-to-end authoring, deployment, and operation of UiPath Coded Agents (LangGraph, LlamaIndex, OpenAI Agents) and Low-Code Agents, including project-type detection, bindings derivation, framework selection, lifecycle commands, and capability integration.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Project type detection (function vs coded vs low-code)** | **Yes — DETECT** | Rule-based check on file signatures (`uipath.json` functions map, `pyproject.toml` + framework dep, `agent.json` + type field) |
| 2 | Framework selection (LangGraph vs LlamaIndex vs OpenAI Agents) | No | Judgment; depends on capability requirements, latency needs, and conversational vs task-agent use case |
| 3 | **Bindings derivation scan (scan code → regenerate `bindings.json`)** | **Yes — TRANSFORM-PIPELINE** | Fixed sequence: scan SDK resource calls, regenerate bindings — no AI judgment required |
| 4 | Authentication / login status check | Marginal | Two-command check (`login status` → `login`); too small for standalone script |
| 5 | Coded agent lifecycle (scaffold → init → pack → deploy) | No | Routes to `coded/quickstart.md`; each sub-step requires reading reference guides and applying judgment |
| 6 | Low-code agent authoring (`agent.json`, capabilities, tools) | No | Judgment; tool selection, prompt engineering, capability configuration |
| 7 | Evaluation and debugging | No | Judgment; interpreting eval results, diagnosing runtime failures |
| 8 | Capability integration (memory, guardrails, HITL, RAG, MCP) | No | Judgment; capability design, configuration decisions |

---

## Codifiable Procedures (not yet scripted)

### 1. Project Type Detection — DETECT

**Source:** `skills/uipath-agents/SKILL.md` §Project Type Detection

**What it does:** Inspects files in the working directory to classify the project as one of: Python Coded Function (has `functions` map in `uipath.json`), Coded Agent (has `pyproject.toml` + Python framework dependency), Low-Code Agent (has `agent.json` with `"type": "lowCode"` + no `pyproject.toml`), or no existing project. Applies rules in a fixed priority order (check for Coded Function first, then Coded, then Low-Code, else ask). Line 23: `"First — confirm this is an agent, not a Coded Function. If uipath.json declares a functions map (e.g. "functions": {"main": "main.py:main"}), the project is a Python Coded Function, not an agent."`

**Why it's mechanical:** All three positive cases test for specific file names and field values with no ambiguity; negative case (ask the user) is triggered only when none of the file-signature rules match.

**Turn savings:** Currently the agent reads multiple files (pyproject.toml, agent.json, uipath.json) across multiple turns to determine project type before routing to a quickstart; a detection script collapses this to one call.

---

### 2. Bindings Derivation Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-agents/SKILL.md` §Hard Rules

**What it does:** Scans the agent's Python source for UiPath SDK resource calls (`assets`, `queues`, `processes`, `buckets`, `indexes`, `connections`, `apps`, `MCP servers`, `InvokeProcess`, `CreateTask`, `CreateEscalation`), then regenerates `bindings.json` from the discovered resources. Inputs: agent source directory. Output: updated `bindings.json`. Line 17: `"always run the sync workflow in [coded/lifecycle/bindings-reference.md] — scan code, regenerate bindings.json. Without this, resources cannot be overridden per execution environment and will always default to the hardcoded values in the SDK calls."`

**Why it's mechanical:** The scan is deterministic (grep for SDK call patterns), and the regeneration follows a fixed mapping from call type to binding entry shape — no judgment about what resources to include.

**Turn savings:** Without a script, the agent reads source files and then manually constructs `bindings.json` entries across several turns; a scan-and-regenerate script does it in one.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The vast majority of what the skill teaches is judgment: which framework to use, how to design agent capabilities, how to wire tools and context, how to interpret evaluation results, and how to debug runtime failures. The two codifiable procedures (project detection, bindings derivation) are important but represent a small fraction of the skill's total surface area — most agent work requires reading multiple reference guides and applying domain judgment.

**Why not None:** The project type detection algorithm is a rule-based DETECT procedure with explicit file-signature checks, and the bindings derivation follows a documented fixed-sequence scan-and-regenerate pipeline — both are mechanically scriptable without AI judgment.

**Evidence locations:**
- Project type detection rules: `skills/uipath-agents/SKILL.md` §Project Type Detection (lines 19–30)
- Bindings derivation mandate: `skills/uipath-agents/SKILL.md` §Hard Rules (line 17)
- Framework judgment: `skills/uipath-agents/SKILL.md` §Task Navigation — "Select coded framework" routes to a reference guide requiring capability comparison

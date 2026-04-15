# Agent Common Issues

Catalog of frequently found issues in UiPath agent projects, with detection methods and recommended fixes.

## Coded Agent Issues

### Module-Level LLM Instantiation

**Symptom:** LLM client (e.g., `UiPathAzureChatOpenAI()`, `ChatOpenAI()`, `UiPathChat()`) created at module scope, outside any function.

```python
# BAD — fails during uip codedagent init
from uipath_langchain.chat_models import UiPathAzureChatOpenAI
llm = UiPathAzureChatOpenAI()  # Module-level instantiation

def main(input: Input) -> Output:
    result = llm.invoke(...)
```

**Impact:** `uip codedagent init` executes the module to discover input/output schemas. Module-level LLM instantiation triggers authentication, which fails during init, breaking the entire setup.

**Detection:** Check `main.py` top-level scope for LLM client creation. Look for assignments like `llm = ...` or `client = ...` outside functions.

**Fix:**
```python
# GOOD — lazy initialization inside function
def main(input: Input) -> Output:
    llm = UiPathAzureChatOpenAI()
    result = llm.invoke(...)
```

### Wrong Import Paths

**Symptom:** Using outdated or incorrect import paths for UiPath SDK.

**Common mistakes:**
```python
# BAD
from uipath import UiPath          # Wrong module path
from uipath.platform import CreateAction, WaitAction  # Renamed classes

# GOOD
from uipath import UiPath          # Correct (if package supports it)
from uipath.platform.common import CreateTask, WaitTask  # Correct HITL imports
```

**Detection:** Grep for `import` statements, verify against current SDK documentation.

**Fix:** Update imports to match the current `uipath` package API.

### Missing [build-system] Guard

**Symptom:** `pyproject.toml` contains a `[build-system]` section.

**Impact:** Causes packaging errors with `uip codedagent` commands. The UiPath toolchain manages the build system.

**Detection:** Read `pyproject.toml`, check for `[build-system]` section.

**Fix:** Remove the entire `[build-system]` section from `pyproject.toml`.

### No @traced() Decorator

**Symptom:** Entry point and key helper functions lack the `@traced()` decorator.

**Impact:** Agent executions don't appear in UiPath's tracing dashboard. No visibility into execution flow, timing, or errors in production.

**Detection:** Grep for `def main` and key function definitions, check for `@traced()`.

**Fix:** Add `@traced()` to the main entry point and significant helper functions. Note: LangGraph graph nodes get automatic tracing — only add `@traced()` to functions outside the graph.

### No @mockable() Decorator

**Symptom:** Functions calling external services (APIs, databases, UiPath processes) lack `@mockable()`.

**Impact:** Evaluations cannot mock external dependencies. Tests become flaky, slow, and require live services.

**Detection:** Identify functions that call external services, check for `@mockable()`.

**Fix:** Add `@mockable()` to any function that calls an external service. This enables evaluation mocking via `mockito` type mocking strategy.

### Infinite Graph Cycles

**Symptom:** LangGraph `StateGraph` has cycles with no exit condition (e.g., always routes back to the same node).

**Impact:** Agent runs indefinitely, consuming tokens until `maxIterations` limit is hit (if configured).

**Detection:** Trace the graph edges manually. Check conditional edges for reachable exit conditions.

**Fix:** Ensure every cycle has a conditional exit. Add `maxIterations` as a safety net.

## Low-Code Agent Issues

### Overpermissioned Tools

**Symptom:** Agent has access to tools that are not needed for its stated purpose.

**Example:** A customer support agent with tools for deleting database records, modifying system configuration, or accessing internal admin APIs.

**Impact:** Increased risk of unintended actions. If the agent misinterprets a request, it can take destructive actions. Larger attack surface for prompt injection.

**Detection:** Compare agent's described purpose (system prompt) against the list of available tools. Flag any tool that is not mentioned or implied by the agent's role.

**Fix:** Remove unnecessary tools. Follow principle of least privilege — agent should only have tools it needs for its specific task.

### Missing Escalation Paths

**Symptom:** Agent makes irreversible decisions (approvals, deletions, financial transactions) without any human escalation path.

**Impact:** Agent errors have no safety net. Incorrect decisions cannot be caught before execution.

**Detection:** Review the agent's tools for high-impact operations. Check if escalation resources are defined for these operations.

**Fix:** Add escalation resources for high-risk decisions. Configure system prompt to escalate when confidence is low or stakes are high.

### Missing Guardrails

**Symptom:** User-facing agent with no input validation, PII detection, or prompt injection defense.

**Impact:** Agent vulnerable to manipulation, data leakage, and unintended behavior.

**Detection:** Check `guardrails` array in agent.json. For user-facing agents, expect at minimum prompt injection and PII detection guardrails.

**Fix:** Enable out-of-the-box guardrails (PII detection, prompt injection). Add custom tool guardrails for destructive operations.

### Poor System Prompt Design

**Symptom:** System prompt is vague, overly broad, or missing key elements.

**Common deficiencies:**
- No explicit role definition ("You are a helpful assistant" — too generic)
- No scope boundaries (agent doesn't know what it should refuse)
- No tool usage guidance (agent guesses when to use tools)
- No escalation criteria (agent never escalates)
- No output format specification (agent produces inconsistent formats)

**Detection:** Read the system prompt and check for the five elements above.

**Fix:** Restructure the system prompt with explicit sections: role/persona, scope/boundaries, tool guidelines, escalation criteria, output format.

### Framework Mismatch

**Symptom:** Simple function agent built with LangGraph, or complex multi-step agent built as a simple function.

**Examples of mismatches:**
- LangGraph with a single node and no conditional edges → should be a simple function agent
- Simple function agent trying to implement multi-step reasoning with manual state management → should be LangGraph
- LlamaIndex used without any retrieval/RAG component → wrong framework choice

**Detection:** Check the framework config file against the agent's actual complexity. A LangGraph agent with 1-2 nodes and no cycles is likely overengineered.

**Fix:** Recommend the appropriate framework based on complexity. Simple → `uipath.json` with functions. Multi-step → `langgraph.json`. RAG-heavy → `llama_index.json`.

## Evaluation Issues

### No Evaluation Sets

**Symptom:** Agent has no evaluation sets at all. No `evaluations/` directory or empty eval sets.

**Impact:** No way to verify agent quality. No regression testing. No confidence in deployment.

**Detection:** Check for `evaluations/eval-sets/` directory and files.

**Fix:** Create at minimum a smoke evaluation set with 2-3 basic test cases covering the happy path. Target 30+ cases for production readiness.

### Single Evaluator Type

**Symptom:** All evaluations use only `ExactMatchEvaluator` for a natural-language agent, or only `LLMJudgeOutputEvaluator` for a deterministic agent.

**Impact:** ExactMatch is too strict for natural language (high false-negative rate). LLMJudge is overkill for deterministic outputs (unnecessary cost and non-determinism in tests).

**Detection:** Read evaluator configurations. Check if evaluator type matches agent behavior.

**Fix:** Use multiple evaluator types. Combine trajectory + output evaluators for multi-step agents. Use ExactMatch for deterministic outputs, LLMJudge for natural language.

### Missing Edge Case Tests

**Symptom:** Eval sets only cover the happy path. No tests for empty input, malformed input, missing data, or error scenarios.

**Impact:** Agent may fail unpredictably in production when encountering real-world data variability.

**Detection:** Review eval set test cases. Check for diversity of input patterns.

**Fix:** Add test cases for: empty/null inputs, extra-long inputs, special characters, missing required fields, service unavailability, ambiguous requests.

### Stale Mock Data

**Symptom:** Mock responses in eval sets don't match current tool output schemas or real-world response patterns.

**Impact:** Evaluations pass but agent fails in production because real responses differ from mocks.

**Detection:** Compare mock response schemas to actual tool output schemas.

**Fix:** Update mock data to match current API responses. Include realistic error responses in mocks.

## Multi-Agent System Issues

### Context Loss in Handoffs

**Symptom:** Information is lost when tasks are passed between agents. The receiving agent starts reasoning from a partial snapshot.

**Impact:** Downstream agents make incorrect decisions based on incomplete context. Per UC Berkeley's MAST taxonomy, inter-agent misalignment accounts for 36.9% of all multi-agent failures.

**Detection:** Review handoff points between agents. Check if structured schemas are used vs free-text handoffs.

**Fix:** Use JSON Schema-based structured outputs for inter-agent communication instead of natural language. Implement context summarization at handoff points. Pass only essential information with explicit schemas.

### Infinite Delegation Loops

**Symptom:** Agents with slightly conflicting instructions bounce tasks back and forth without resolution (Agent A → Agent B → Agent A → ...).

**Impact:** Consumes tokens indefinitely, stalls workflows. No task completion.

**Detection:** Check for circular handoff conditions. Look for missing termination criteria in agent routing logic.

**Fix:** Add explicit guard conditions preventing circular delegation. Implement a maximum handoff count (circuit breaker). Ensure every agent knows when a task is complete.

### Reasoning-Action Mismatch

**Symptom:** Agent's stated reasoning doesn't match its actual actions. The agent says it will do X but does Y. Per MAST taxonomy, this is the second most common failure (13.2% of all failures).

**Impact:** Unpredictable behavior. Debug logs show correct reasoning but wrong tool calls.

**Detection:** Compare agent trace reasoning steps to actual tool invocations. Use trajectory evaluators to detect mismatches.

**Fix:** Use structured output for action planning. Add output validation that checks action matches stated intent. Use trajectory-based evaluation to catch this pattern.

## Cross-Cutting Issues

### Agent Not Versioned

**Symptom:** No versioning strategy — agent deployed by overwriting previous version.

**Impact:** Cannot roll back to a known-good version. Cannot A/B test changes. No audit trail of changes.

**Detection:** Check for version field in agent config. Check git history for tagging/branching strategy.

**Fix:** Use semantic versioning. Tag releases in git. Maintain changelog.

### No Observability

**Symptom:** Agent deployed without tracing, logging, or monitoring.

**Impact:** No visibility into production behavior. Cannot diagnose failures or performance issues. Cannot identify drift.

**Detection:** Check for `@traced()` decorators (coded), check if tracing is enabled (low-code), check for monitoring dashboards.

**Fix:** Enable agent traces. Set up monitoring dashboards for key metrics (success rate, latency, token usage, tool call patterns). Review traces regularly.

## Tool and Guardrail Antipatterns

### Agent Deployed Without Tool Guardrails

**Symptom:** Agent deployed to production with write/delete/send tools but no guardrails configured.

**Impact:** Agent can invoke any tool with any arguments — no validation. Misinterpreted prompts trigger unintended destructive actions. UiPath docs recommend Block-type guardrails for sensitive data in production.

**Detection:** Check `guardrails` section in agent config. If absent or empty when the agent has destructive tools, flag.

**Fix:** Configure tool-level guardrails for destructive operations. Use Block-type for sensitive data. Add confirmation/escalation via Action Center for high-impact actions.

**Severity:** Critical (for agents with destructive tool capabilities)

### Vague Tool Descriptions

**Symptom:** Tool descriptions are generic ("Process invoice", "Update record") without specifying side effects, destructiveness, input/output format, or repeat-call behavior.

**Impact:** Agents select tools based on description matching. Vague = wrong-tool selection or wrong argument format.

**Detection:** Review tool descriptions. Flag descriptions under 50 characters or missing action-effect keywords ("creates", "deletes", "modifies", "sends", "permanent", "irreversible").

**Fix:** Rewrite descriptions to cover: what the tool does, what it affects, side effects, destructiveness, idempotency, when to use, when NOT to use.

**Severity:** Warning

### Destructive Tools Without Explicit Flags

**Symptom:** Tools performing irreversible operations (delete, send email, approve, modify config) without explicit `destructive`/`write`/`irreversible` markers in the description.

**Impact:** Agent has no basis to add confirmation or escalate. May execute destructively on ambiguous input.

**Detection:** Tool descriptions containing "delete", "remove", "send", "approve", "update", "create" without explicit destructive markers.

**Fix:** Add explicit markers. Consider mandatory human-in-the-loop confirmation via Action Center for destructive tools.

**Severity:** Warning

### Context Grounding Missing for Domain-Specific Agents

**Symptom:** Agent handles domain-specific tasks (company procedures, product catalogs, policy documents) without Context Grounding / RAG configured.

**Impact:** Agent hallucinates — plausible but incorrect answers about company-specific processes. Context Grounding, when properly configured, returns "An answer could not be found" instead of hallucinating.

**Detection:** Check tenant for configured Context Grounding indexes. Compare system prompt against available knowledge sources. If the prompt references company-specific content not backed by a grounding source, flag.

**Fix:** Configure Context Grounding with relevant company documents. Reference the index in the system prompt. Tune retrieval threshold.

**Severity:** Warning

### Missing Output Interpretation Examples

**Symptom:** Agent has tools configured but system prompt has no examples showing how to interpret tool output (success/failure states, partial results, edge cases).

**Impact:** Agent misinterprets results. Example: API returns `{"status": "pending"}` → agent treats as success. UiPath docs state examples "significantly improve tool accuracy."

**Detection:** Count tools vs examples in system prompt. Each tool should have at least one usage example covering input format, expected output, edge-case interpretation.

**Fix:** Add per-tool examples in the system prompt with sample input, expected output shape, and edge-case interpretation guidance.

**Severity:** Info

## Trust and Output Validation Antipatterns

### Agent Output Missing Reasoning / Explanation Fields

**Symptom:** Agent JSON output schema includes only the decision/result (e.g., `{"classification": "X"}`) with no `reasoning` / `explanation` / `why` field.

**Impact:** Production debugging becomes impossible. When the agent classifies wrong, there's no trace of what it considered. Audit reviewers cannot assess whether the agent's logic was sound. Hallucinations are invisible until they cause downstream damage.

**Detection:** Inspect agent output schema / response shape. Flag schemas that contain only terminal values (labels, booleans, IDs) without accompanying reasoning fields.

**Fix:** Add a `reasoning` / `explanation` / `citations` field to the output schema. Prompt the agent to explain its decision. Log the reasoning alongside the decision.

**Severity:** Warning

### Agent with Both Read and Write Side-Effects (Should Be Separated)

**Symptom:** Single agent has tools spanning both read/query operations and write/delete/send/modify operations. Design coupling: a misclassification can cause both wrong reads AND unintended writes.

**Impact:** Blast radius is the full tool set. Harder to audit, harder to sandbox. Read-only evaluations cannot exercise write paths; write-safe evaluations require mock infrastructure.

**Detection:** Review agent tool list. Categorize each tool as read or write. If both categories are present, flag unless the agent's explicit purpose requires coupled read-then-write behavior (and even then, consider whether an orchestrator should call read-agent first, then write-agent).

**Fix:** Split into two agents: a read/query/classifier agent that returns decisions, and a write/execute agent invoked by an orchestrator based on the first agent's output. Use Maestro or a Flow to sequence them.

**Severity:** Warning

### No Trust Score Threshold for Autonomous Actions

**Symptom:** Agent output is consumed directly by downstream actions without a confidence / trust score check.

**Impact:** Low-confidence outputs trigger autonomous actions. Examples: "80% confidence this is fraud" → account automatically suspended. "60% confidence this invoice is approved" → auto-paid.

**Detection:** Check consuming workflow. After the agent returns, is there an `If confidence < threshold` branch that routes to human review?

**Fix:** Define a per-use-case confidence threshold. Below threshold → Action Center / human review / fallback logic. Above threshold → autonomous action.

**Severity:** Warning (Critical for financial / regulated / irreversible actions)

### No Escalation Path for UNCLEAR / Low-Confidence Results

**Symptom:** Agent returns `"status": "UNCLEAR"` or low-confidence output, but the consuming workflow has no branch for this — falls through to error handling or default path.

**Impact:** Ambiguous cases get lost or silently mishandled. No human review for the cases that most need it.

**Detection:** Inspect consuming workflow's handling of agent output. Check for explicit branches on UNCLEAR / low-confidence / null results.

**Fix:** Add explicit branch: on UNCLEAR/low-confidence → Create Action Center task → wait for human decision → resume. Do not default to "process as Yes" or "process as No."

**Severity:** Warning

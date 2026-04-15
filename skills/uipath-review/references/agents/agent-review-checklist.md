# Agent Review Checklist

Comprehensive quality checklist for UiPath AI agent projects — both low-code (agent.json) and coded (Python) agents.

> **Unit of Work:** Before running the technical checks below, complete Step 3a (Unit of Work Discovery) from SKILL.md. For low-code agents the declared unit is `agent.json` → `inputSchema`. For coded agents it's the `Input` Pydantic class in `main.py`. The actual unit is what the agent produces per invocation — if one input triggers iteration over an array of entities and produces N tool invocations or state changes that should have been separate agent calls, that is a Granularity Mismatch (see [rpa-common-issues.md](../rpa/rpa-common-issues.md) for the generic pattern).

## 1. Agent Type Appropriateness

Before reviewing implementation details, verify the right agent type was chosen:

| Criterion | Should Be Low-Code | Should Be Coded |
|---|---|---|
| Behavior expressible through prompts + pre-built tools | Yes | Overkill |
| Needs custom LLM reasoning or state machines | Wrong choice | Yes |
| Requires third-party Python libraries | Wrong choice | Yes |
| Standard UiPath capabilities only | Yes | Unnecessary complexity |
| Complex conditional HITL resume logic | Cannot do | Yes |
| Multi-agent routing in code | Cannot do | Yes |
| Speed of iteration is priority | Yes | Slower |
| Team is Python-proficient | Either works | Natural fit |

**Severity:** Flag agent type mismatch as **Warning** with recommendation.

## 2. Low-Code Agent Quality (agent.json)

### Schema Validation

| Check | Severity | How to Verify |
|---|---|---|
| `agent.json` passes schema validation | Critical | `uip agent validate ./path --output json` |
| `version` field is set (e.g., `"1.1.0"`) | Critical | Read agent.json |
| `name` field is set and descriptive | Warning | Read agent.json |
| Exactly 2 messages (system + user) | Critical | Read agent.json → `messages` array |
| `inputSchema` and `outputSchema` defined | Warning | Read agent.json |
| `settings.model` is set | Critical | Read agent.json |
| `settings.maxIterations` is configured (default 25) | Info | Read agent.json |
| `settings.temperature` is appropriate for task | Info | Read agent.json |

### System Prompt Quality

| Check | Severity | How to Verify |
|---|---|---|
| System prompt defines explicit role/persona | Warning | Read first message content |
| System prompt defines scope and boundaries | Warning | Check for "you should NOT" or boundary statements |
| System prompt includes tool usage guidelines | Warning | Check for tool-specific instructions |
| System prompt includes escalation criteria | Warning | Check for "escalate when" conditions |
| System prompt specifies output format | Info | Check for format instructions |
| System prompt is in English (best performance) | Info | Check language |
| No hardcoded examples that should be in eval sets | Info | Check for inline examples |
| Prompt length appropriate (not excessively long) | Info | Check token count |
| Prompts over ~2000 tokens have clear structural headers (Role / Task / Constraints / Output Format / Examples) | Warning | Long prompts without structure degrade LLM attention. Flag >2000-token prompts that read as unstructured prose |
| NO hardcoded customer-specific logic in the system prompt (names, rules, identifiers specific to one tenant/customer) | Warning | Customer-specific content should live in Context Grounding / knowledge base / config — not in the prompt. Makes the agent reusable across customers |

### Temperature Guidance

| Task Type | Recommended Range | Flag If |
|---|---|---|
| Factual extraction, classification | 0.0-0.3 | >0.5 |
| Conversational, general-purpose | 0.4-0.7 | >0.8 for production |
| Creative generation | 0.8-1.2 | >1.5 |

### Tool Configuration

| Check | Severity | How to Verify |
|---|---|---|
| All tools have descriptive names (lowercase, alphanumeric, no special chars) | Warning | Read resources array |
| All tools have clear descriptions (purpose, effects, risks) | Warning | Read tool descriptions |
| No overpermissioned tools (agent has access to tools it doesn't need) | Warning | Review tool list against agent's purpose |
| Process/API workflow tools reference correct published resource names | Critical | Verify referenced processes exist |
| Connector tools have valid connection configurations | Critical | Check connection references |
| Tool descriptions explain when to use AND when NOT to use each tool | Info | Read descriptions |
| Tool count is bounded — agents with >3 tools risk tool-selection overload; >7 is a strong smell | Warning | Count tools per agent. If >3, verify each is essential and non-overlapping; if >7, consider splitting into multiple specialized agents |
| Read-only agents do NOT have write-capable tools | Warning | If agent purpose is classification/triage/lookup (read-only), no write/delete/send/modify tools should be present |
| Output-consuming workflows validate agent output against expected schema before use | Warning | Check calling workflow: agent output should be validated (schema check, type check) before downstream activities consume it |

### Context Grounding Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Retrieval mode appropriate (JIT/DeepRAG for runtime docs, index for stable corpora) | Info | Read context grounding config |
| Index names are descriptive and versioned | Info | Check naming patterns |
| Chunk count balanced (not too few = missed context, not too many = token waste) | Info | Check retrieval config |
| Threshold configured appropriately (0 is default — higher risks excluding relevant passages) | Info | Check threshold value |

### Escalation Coverage

| Check | Severity | How to Verify |
|---|---|---|
| Escalation resources defined for high-risk decisions | Warning | Check resources for escalation type |
| Escalation criteria specified in system prompt | Warning | Read system prompt for escalation guidance |
| Escalation assignee configured | Critical | Check escalation resource config |
| Agent does not make irreversible decisions without escalation path | Warning | Review decision scope |

### Guardrails

| Check | Severity | How to Verify |
|---|---|---|
| PII detection configured (if handling personal data) | Warning | Check guardrails array |
| Prompt injection guardrails enabled (if user-facing) | Warning | Check guardrails config |
| Custom tool guardrails for destructive operations | Info | Check tool guardrail rules |
| Guardrail actions appropriate (Log/Block/Escalate) | Info | Review action types |

### Memory Management

| Check | Severity | How to Verify |
|---|---|---|
| Memory key length under 80-character limit | Warning | Check memory key definitions |
| Memory TTL appropriate for use case (default 3-month expiry) | Info | Check memory retention configuration |
| Sensitive data (PII, credentials) not stored in agent memory | Warning | Review memory key-value content and patterns |

## 3. Coded Agent Quality (Python)

### Project Structure

| Check | Severity | How to Verify |
|---|---|---|
| `main.py` exists with entry point function | Critical | `ls main.py` |
| Framework config file exists (`langgraph.json`, `llama_index.json`, `openai_agents.json`, or `uipath.json`) | Critical | Check for config file |
| `pyproject.toml` exists with valid config | Critical | Read pyproject.toml |
| `pyproject.toml` does NOT have `[build-system]` section | Critical | Read pyproject.toml |
| `.env` file not committed to source control | Critical | Check .gitignore and git status |
| `entry-points.json` present | Warning | `ls entry-points.json` |

### Dependencies (pyproject.toml)

| Check | Severity | How to Verify |
|---|---|---|
| `uipath` package in dependencies | Critical | Read pyproject.toml |
| `uipath-langchain` present if using LangGraph | Critical | Check for LangGraph usage |
| No unnecessary dependencies | Info | Review dependency list |
| Dependencies pinned or version-constrained | Warning | Check version specifiers |
| No `[build-system]` section | Critical | Read pyproject.toml |

### Code Quality

| Check | Severity | How to Verify |
|---|---|---|
| No module-level LLM instantiation | Critical | Check top-level code in main.py for LLM client creation |
| LLM clients created inside functions/nodes (lazy initialization) | Critical | Verify initialization is inside functions |
| Pydantic `BaseModel` used for Input and Output | Warning | Check for Input/Output class definitions |
| `@traced()` decorator on main function and key helpers | Warning | Grep for `@traced` |
| `@mockable()` decorator on functions calling external services | Warning | Grep for `@mockable` |
| Correct import: `from uipath import UiPath` | Critical | Check import statements |
| HITL imports correct: `CreateTask`/`WaitTask` (not `CreateAction`/`WaitAction`) | Critical | Check HITL-related imports |
| Structured output via `with_structured_output(MyModel)` | Info | Check LLM output patterns |
| No hardcoded API keys or secrets | Critical | Grep for `api_key=`, `secret=` in string literals |
| Async patterns used correctly (if async) | Warning | Check async/await usage |

### Framework-Specific Checks

#### LangGraph

| Check | Severity | How to Verify |
|---|---|---|
| `graph` variable is a compiled `CompiledStateGraph` | Critical | Check main.py for graph compilation |
| State class properly defined with all required fields | Warning | Check StateGraph definition |
| Conditional edges use proper routing logic | Warning | Review edge conditions |
| No infinite loops in graph (cycles must have exit conditions) | Critical | Review graph topology |
| Checkpointing configured for long-running graphs | Info | Check for checkpoint config |

#### LlamaIndex

| Check | Severity | How to Verify |
|---|---|---|
| Agent workflow properly defined | Warning | Check agent setup |
| Retry mechanisms present for retrieval failures | Warning | Check error handling |
| Index management follows best practices | Info | Check index usage |

#### OpenAI Agents SDK

| Check | Severity | How to Verify |
|---|---|---|
| Agent role explicitly defined | Warning | Check agent configuration |
| Structured tool use with examples | Info | Check tool definitions |
| Guardrails configured (input/output validation) | Warning | Check guardrail setup |

### Error Handling

| Check | Severity | How to Verify |
|---|---|---|
| Try-except blocks around external service calls | Warning | Check error handling |
| Graceful degradation when tools fail | Warning | Check tool error paths |
| Timeout configuration for LLM calls | Info | Check timeout settings |
| No bare `except:` blocks (catch specific exceptions) | Warning | Grep for `except:` without exception type |

## 4. Evaluation Quality (Both Types)

### Evaluation Set Existence

| Check | Severity | How to Verify |
|---|---|---|
| At least one smoke evaluation set exists | Warning | `ls evaluations/eval-sets/smoke-test.json` or similar |
| Eval set covers happy path (basic successful scenarios) | Warning | Read eval set |
| Eval set covers edge cases (missing data, unusual inputs) | Info | Read eval set |
| Eval set covers error scenarios (invalid inputs, service failures) | Info | Read eval set |
| Minimum 30 test cases for production readiness | Info | Count evaluations in eval sets |
| Eval set tiering aligned with FDE Architecture Review guidance: ~10-20 dev evals, ~50 benchmark cases, 200-400 UAT cases for production-critical agents | Warning | Check for tiered eval sets (smoke/dev/benchmark/UAT). Customer-critical agents with <50 benchmark cases are under-tested |
| Eval sets include **corrected failures** (cases that initially failed, were fixed, and are retained as regression tests) — NOT only happy-path / successful trajectories | Warning | Review eval dataset sourcing. Datasets built only from successful runs suffer selection bias — the agent passes evaluations that don't reflect real-world failure modes |
| Eval sets include adversarial / malicious inputs (prompt injection attempts, malformed data, boundary conditions) | Warning | Check for negative test cases |
| Trust score / confidence thresholds defined for probabilistic outputs (classification, extraction) | Warning | For agents producing labeled outputs, a minimum confidence threshold should gate autonomous action; below threshold → escalate |
| Low-confidence / UNCLEAR results have a defined escalation path (Action Center, human review, human-in-the-loop fallback) | Warning | Check consuming workflow for "what happens when confidence < threshold" branch |

### Evaluator Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Multiple evaluator types configured (not just one) | Warning | Check evaluatorRefs |
| Trajectory evaluator present for multi-step agents | Warning | Check for LLMJudgeTrajectoryEvaluator |
| Output-based evaluator present | Warning | Check for LLMJudgeOutputEvaluator or ExactMatchEvaluator |
| Evaluator selection matches agent type (see table below) | Warning | Compare agent type to evaluators |

### Evaluator Selection Guide

| Agent Type | Primary Evaluator | Secondary | Notes |
|---|---|---|---|
| Deterministic (calculator, lookup) | ExactMatchEvaluator | — | Pass/fail on exact output |
| Text generation (summarizer, writer) | LLMJudgeOutputEvaluator | ContainsEvaluator | Semantic + keyword |
| Multi-step orchestrator | LLMJudgeTrajectoryEvaluator | JsonSimilarityEvaluator | Path + output |
| API/data integration | JsonSimilarityEvaluator | ExactMatchEvaluator | Structural + exact |
| Classification/triage | BinaryClassificationEvaluator | LLMJudgeOutputEvaluator | Label + reasoning |

### Mocking Strategy

| Check | Severity | How to Verify |
|---|---|---|
| External dependencies mocked in eval sets | Warning | Check mockingStrategy in eval sets |
| Mock responses are realistic (not placeholder data) | Info | Review mock data |
| Mocking consistent across eval sets | Info | Compare mocking strategies |

## 5. Agent Type Decision Review

Before reviewing implementation details, verify the automation spectrum choice is appropriate:

### Deterministic vs Non-Deterministic Assessment

| Criterion | Deterministic (RPA) | Rules-Based (RPA + Business Rules) | Non-Deterministic (Agent) | Hybrid (Agentic Workflow) |
|---|---|---|---|---|
| Input type | Structured, predictable | Structured with conditional logic | Unstructured, ambiguous | Mix of both |
| Decision logic | Fixed if-then-else | Enumerable rules (DMN, decision tables) | Probabilistic, LLM reasoning | Agent reasons, RPA executes |
| Output consistency | Same input → same output | Same input → same output | Variable outputs | Controlled variability |
| Cost predictability | High | High | Medium-low (token variance) | Medium |
| Testing approach | Full regression, deterministic | Rule coverage testing | Evaluation sets, LLM-as-judge | Both approaches |
| Best for | Data entry, file processing, form filling | Loan approval, classification, routing | Support triage, research, content generation | Complex processes with ambiguous steps |

**Flag as Warning:** Agent used for a fully deterministic task (should be RPA). RPA used for a task requiring reasoning over unstructured input (should be agent or hybrid).

### UiPath Agent Deployment Pre-Flight (Official Best Practices)

| Check | Severity | How to Verify |
|---|---|---|
| System prompt includes role, constraints, and 3-5 input-mapped examples | Warning | Read system prompt |
| All tools have name, description, and input/output schema | Warning | Check tool definitions |
| Tool call logging enabled for audit and debugging | Info | Check logging config |
| At least one knowledge base grounded | Info | Check context grounding |
| Minimum 30 manual tests covering typical, edge, and malformed inputs | Warning | Check test records |
| 30+ curated test cases in evaluation sets | Warning | Count eval set cases |
| 70%+ score on evaluation sets with no regressions | Warning | Run evaluations |
| English used as default language for prompts and schemas | Info | Check language |

### Agent Limitations Awareness

Review whether the agent design accounts for known UiPath limitations:

| Limitation | Impact | Check |
|---|---|---|
| Conversational agents cannot run automations on user's local desktop | Critical if desktop execution expected | Verify architecture doesn't assume local execution |
| Only shared Integration Service connections work (not individual) | Warning | Check connection types |
| Agent does NOT ask for user confirmation before executing tools | Critical for destructive operations | Verify guardrails exist |
| File uploads limited to 5MB | Warning if processing large documents | Check file handling |
| Non-English characters may impact tool calls | Warning for multilingual agents | Check language handling |
| Memory key has 80-character limit; key-value pairs have 3-month TTL | Info | Check memory usage |
| Teams/Slack: only direct messages supported (no channels, no @mentions) | Info | Check deployment channel |

## 6. Deployment Readiness

| Check | Severity | How to Verify |
|---|---|---|
| `entry-points.json` present and correct | Warning | Read entry-points.json |
| `bindings.json` present (if using external resources) | Warning | Read bindings.json |
| Agent validates without errors | Critical | Run validation command |
| Smoke evaluation passes (70%+ score) | Warning | Run evaluations |
| No `.env` file or secrets in committed code | Critical | Check git status |
| No module-level side effects that fail during `uip codedagent init` | Critical | Run init |
| Version management in place | Info | Check versioning |

## 6. Agent Security Review

### Tool Permissions

| Check | Severity | How to Verify |
|---|---|---|
| Agent has only necessary tools (principle of least privilege) | Warning | Review tool list |
| Destructive tools (delete, modify) have guardrails or escalation | Warning | Check tool guardrails |
| No tools that expose internal systems unnecessarily | Warning | Review tool descriptions |
| File-access tools restricted to appropriate paths | Info | Check tool configurations |

### Data Protection

| Check | Severity | How to Verify |
|---|---|---|
| No PII in agent traces or logs (unless required) | Warning | Review trace content |
| Sensitive inputs/outputs masked appropriately | Warning | Check data handling |
| Context grounding indexes don't contain sensitive data in public-facing agents | Critical | Review index content |
| Memory TTL configured (default 3-month, 80-char key limit) | Info | Check memory config |

### Prompt Injection Defense

| Check | Severity | How to Verify |
|---|---|---|
| System prompt includes boundary instructions | Warning | Review system prompt |
| External data treated as untrusted (clear delimiters) | Warning | Check data handling patterns |
| Output validation present (schema-based) | Info | Check output handling |
| Rate limiting configured for user-facing agents | Info | Check rate limit config |

## 7. AI Trust Layer Audit

Verify that the organization's AI Trust Layer is properly configured for the agent's use case.

### Product Toggle Review

| Toggle | Default | Review Action |
|---|---|---|
| Enable calls to third-party AI models | Enabled | Verify this is intentional — disable if agent should only use UiPath-hosted models |
| Enable Agents | Yes | Required for agent operation |
| Enable Coded Agents | Yes | Disable if only low-code agents are used |
| Enable Document Understanding features | Yes | Disable if not using DU with AI |
| Enable UiPath GenAI activities | Yes | Verify scope — disable unused capabilities |

**Review principle:** Apply least-privilege — disable any toggle the agent does not need.

### Trace and Audit Settings

| Check | Severity | How to Verify |
|---|---|---|
| Trace TTL configured per compliance requirements (1, 7, or 30 days) | Warning | Check AI Trust Layer settings |
| Input/output audit saving enabled for production agents | Warning | Verify prompt/completion storage is active |
| PII protection configured (pseudonymization before reaching models) | Warning | Check PII masking settings |

## 8. Context Engineering Quality

For agents using context grounding (RAG):

| Check | Severity | How to Verify |
|---|---|---|
| Index names are versioned and descriptive (e.g., `HR-Policies-2025-Q3`) | Info | Check context grounding index names |
| Ingestion mode matches document type (Basic for text, Advanced for mixed text/image) | Warning | Check ingestion configuration |
| Regular sync cadence established for knowledge freshness | Warning | Check sync schedule — stale indexes produce outdated answers |
| Results count balanced (more chunks = more recall but more tokens) | Info | Check retrieval configuration |
| Threshold score tuned (default 0 — raising improves precision but risks missing content) | Info | Check threshold value |
| Context descriptions are informative for multi-source retrieval | Info | Review context source descriptions |

## 9. Agent Governance Policies (2025.10+)

If the organization uses Automation Ops agent governance:

| Check | Severity | How to Verify |
|---|---|---|
| Minimum reliability score enforced before production deployment | Warning | Check governance policy for score threshold |
| Maximum token count configured (controls response cost) | Info | Check token limit policy |
| Temperature threshold enforced (0=Precise, 1=Creative) | Info | Check temperature policy |
| Agentic guardrails catalog reviewed and applicable guardrails enabled | Warning | Check guardrail configuration |
| Human review required for Autopilot-generated suggestions | Info | Check approval workflow |

# Agents — Coded Judgment Rule Catalog

Judgment rules for **coded** agents (Python — `main.py` + framework config). Each rule requires reading source and reasoning; regex/AST-emulation/file-walk cannot reliably decide it. Same row schema as elsewhere — see [`../rule-format.md`](../rule-format.md).

> **This catalog is judgment-only.** Run `uip codedagent review "<PROJECT_DIR>" --output json` **first** (SKILL.md Step 2.5). It returns deterministic coded findings (pyproject/dependency/python-version gates, import & secret regex, framework symbol existence, bare-except, eval-run analysis, `.venv` packaging, git-tracked secrets) in the same rule format. Then apply these rules, which the CLI cannot do.

Read [`../rule-format.md`](../rule-format.md) and [`../rule-catalog-workflow.md`](../rule-catalog-workflow.md) first.

## Framework detection

Detect once and reuse:

| Signal | Framework |
|---|---|
| `langgraph.json` at project root | `LANGGRAPH` |
| `llama_index.json` | `LLAMAINDEX` |
| `openai_agents.json` | `OPENAI_AGENTS` |
| `google_adk.json` | `GOOGLE_ADK` |
| `pydantic_ai.json` | `PYDANTIC_AI` |
| `agent_framework.json` | `AGENT_FRAMEWORK` |
| `uipath.json` with `.functions` and no framework config above | `FUNCTION` |

Rules marked `(<FRAMEWORK> only)` in `trigger` skip on other frameworks.

## Agent shapes

- **Workflow**: one agent, one system prompt (zero for Simple Function), one tool surface, one entry point.
- **Coded workflow**: multiple agents in one project; an orchestrator chooses the handler. Detect when `create_react_agent(...)` is called ≥2 times, a `StateGraph` supervisor covers multiple agents, or OpenAI Agents `handoffs=[...]` covers multiple `Agent` instances.

Rules in `## GeneralChecker` tagged `(coded_workflow only)` skip on single-agent projects.

## How to apply rules

Each H2 is a checker class. Every `detection_method` is a judgment instruction: read the named source, reason, and emit when criteria hold; record reasoning in the finding `description`. The final row of each section is a category bucket and may be used only when no specific rule fits.

## EvalsChecker

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `CODED_EVAL_TRAJECTORY_SPECIFICITY` | warning | evals | Agent with 3+ tool calls has trajectory evaluators with generic `expectedAgentBehavior`. Read AST-detected tools and eval sets. For a typical 3+ tool-call flow, assess whether descriptions name tools, ordering, and decisions; emit per generic description. `"Agent should process the input and return a response"` is too generic. | Rewrite `expectedAgentBehavior` to name the specific tool sequence and decisions. |
| `CODED_EVAL_ARCHETYPE_FIT` | warning | evals | Read source and evaluators. Classify the agent as calculator/deterministic, text generator, multi-step orchestrator, API integration, or classifier; compare with [Archetype quick reference](#archetype-quick-reference), emitting each mismatch. | Choose evaluators per the archetype reference: deterministic → exact-match/JSON-similarity; orchestrator → trajectory; classifier → multiclass. |
| `CODED_EVAL_SET_ORGANISATION` | info | evals | Read eval sets. Emit only for mixed scenario concerns (happy-path and intentional-failure datapoints) or unrelated agents sharing a set; do not flag naming such as `set-1.json`. | Split sets by scenario type or agent and document intent in filename or metadata. |
| `CODED_EVAL_BEHAVIOR_DESCRIPTION` | warning | evals | Read every `expectedAgentBehavior`. Emit per datapoint when it does not name specific tools, steps, or decisions; generic text such as `"Agent should handle the request appropriately"` fails. | Name the specific tools, steps, or decisions. |
| `CODED_EVAL_FORMAT_MISMATCH` | warning | evals | Read `expectedOutput` and runtime output type (Pydantic/dataclass/JSON). Emit only for inspectable serialization mismatches: Python single-quoted dict such as `"{'temperature': 25.0}"` versus JSON, trailing-comma JSON, bytes versus string, or regex anchors on a non-regex evaluator. | Match `expectedOutput` to actual serialization. |
| `CODED_EVAL_COVERAGE_GAP` | warning | evals | Read evaluator configs and eval-set `evaluationCriterias` keys; emit when a configured evaluator is referenced by no eval entry. Read source; emit when a declared branch (platform-vs-local, error handler, rejection route) is exercised by no datapoint. Emit per concrete gap. | Add entries referencing the evaluator/exercising the path, or remove unused config. |
| `CODED_EVAL_GROUND_TRUTH_MISLABELED` | warning | evals | Read `.inputs` and `.expectedOutput`/`.expectedClass`. Emit only when input semantics clearly contradict the expected class; skip borderline labels. | Correct the label or split the datapoint into scenarios. |
| `CODED_EVAL_DATASET_SINGLE_CLASS` | warning | evals | Read evaluator type and labels. Emit when a multiclass shape (`uipath-multiclass-classification`, or custom balanced-accuracy with `classCounts: {…}`) has ≥3 datapoints with one label. Skip `<3` datapoints and single-class-by-design `uipath-binary-classification`. | Add other classes or use `uipath-binary-classification` for one-class detection. |
| `CODED_EXTERNAL_CALL_NOT_MOCKABLE` | warning | evals | For external boundaries (UiPath SDK, HTTP, database, queue, process invocation), read each function and emit when evaluations exist but it lacks `@mockable()`. Skip pure-Python helpers and projects without evaluations. | Decorate each boundary function with `@mockable()`. |
| `CODED_EVAL_MOCK_CONTRACT_DRIFT` | warning | evals | Read eval mock definitions (`mockito` type mocks and response fixtures) and mocked signatures, return annotations, Pydantic models, or `TypedDict`. Emit when fields, types, or required fields contradict the declared return contract. `CODED_EVAL_FORMAT_MISMATCH` owns `expectedOutput`; this rule owns mocks. Skip functions without declared return types. | Match the mock payload to the declared return shape, or add the return annotation it implies. |
| `CODED_EVAL_ISSUE` | warning | evals | Use only after all specific Evals rules, for an eval-infrastructure observation that fits none; include concrete description and suggested fix. | Defined per finding. |

### Archetype quick reference

| Agent archetype | Primary evaluator | Secondary | Mismatch to flag |
|---|---|---|---|
| Calculator / deterministic | `uipath-exact-match` or `file://` | — | LLM judge on deterministic output with no deterministic evaluator |
| Text generator / summariser | `uipath-llm-judge-output-semantic-similarity` | `uipath-contains` | `exact-match` on free-form text |
| Multi-step orchestrator | `uipath-llm-judge-trajectory-similarity` | `uipath-tool-call-order` | No trajectory evaluator |
| API integration | `uipath-json-similarity` or `file://` | `uipath-exact-match` | No structured comparison |
| Classifier | `uipath-binary-classification` / `uipath-multiclass-classification` or `file://` | — | `exact-match` on classification output |

LLM-judge-only is acceptable only for agents with no tools, no classification output, and free-form text; otherwise prefer a deterministic baseline.

## SchemaChecker

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `SCHEMA_NO_DESCRIPTIONS` | judgment | schema | Read authored input/output models separately. Emit when properties lack informative semantic descriptions; mere presence is insufficient. | Add a useful description to every field. |
| `CODED_SCHEMA_COMPLETENESS` | warning | schema | Read `StateGraph(input=..., output=...)` or `_schema=` variants and actual behavior. Emit when declared fields are insufficient for the contract, such as needed `customer_history` + `recent_invoices` omitted in favor of only `query: str`. | Expand the schema for required context and returned data. |
| `CODED_SCHEMA_FIELD_NO_VALIDATION` | warning | schema | For each constrained-value field suggested by `category`, `status`, `severity`, `role`, `intent`, `classification`, or `priority`, emit when logic maps to a small set but the field is bare `str` without `Literal`, `Enum`, or validator. | Use `Literal["a", "b", "c"]`, `Enum`, or `Field(..., pattern="...")`. |
| `CODED_OUTPUT_ENUM_MISSING_ON_CLASSIFIER` | warning | schema | Read output schemas (Pydantic, `StateGraph`, dataclass). For `class`, `classification`, `label`, `category`, `intent`, `severity`, `priority`, or `status` fields typed `str`, emit without `Literal[...]`, `Enum`, or pattern. May co-fire with `CODED_SCHEMA_FIELD_NO_VALIDATION`. | Add `Literal[...]`, `Enum`, or pattern constraint. |
| `CODED_OUTPUT_CONSUMER_DRIFT` | warning | schema | Only when Step 1 lists an in-scope consumer (sibling flow, RPA project, API workflow, or invoking agent). Read consumer use and output model; emit when fields, types, or states differ. `CODED_MULTI_AGENT_CROSS_SCHEMA` owns input direction of `sdk.processes.invoke(...)`; this owns output direction. Out-of-scope callers are not evidence; no consumer means an empty subject set, not a skipped rule. | Add the omitted output field or read the declared field/type/state. |
| `CODED_SCHEMA_ISSUE` | warning | schema | Use only after specific Schema rules, for another concrete schema observation. | Defined per finding. |

## ToolsChecker

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `CODED_TOOL_DOCSTRING_QUALITY` | warning | tools | Read each tool function passed to `bind_tools`, decorated `@tool`, or registered via `Tool(...)`. Emit when docstring is missing, generic, <20 chars, fails to name every parameter, or omits return shape and a usage cue. Do not emit when it names every parameter and describes the return shape or gives a usage cue (preconditions, side effects, example). | Name every parameter, return shape, and a usage cue. |
| `CODED_PROMPT_TOOL_COVERAGE` | warning | tools | Read system prompt passed to `UiPathChat`, `UiPathAzureChatOpenAI`, or `Agent(instructions=...)`, and registrations. Emit when fewer than half of registered tools are named or described by purpose. | Reference each tool by name and explain when to use it. |
| `CODED_PROMPT_REFERENCES_NONEXISTENT_TOOL` | warning | tools | Extract specific tool identifiers from the prompt (backticks, quotes, or “the X tool”) and compare with `@tool`, `Tool(...)`, and `bind_tools` registrations. Emit per missing name; skip generic prose such as “use a search tool”. | Rename, register, or remove the cited tool. |
| `CODED_TOOLS_ISSUE` | warning | tools | Use only after specific Tools rules, for another concrete tools observation. | Defined per finding. |

## GuardrailsChecker

> **Validator-name authority.** Do not name a platform-documented validator (`harmful_content` / `intellectual_property` / `user_prompt_attacks`) unless already present in code; phrase it generically. `pii_detection` / `prompt_injection` are SDK-confirmed and may be named.

> **Apply these via the structured workflow.** Apply `guardrails/coded-guardrails-review.md`: Step 0 must fetch the live `uip agent guardrails catalog` + `list` (30-min cache) **plus** public Python SDK docs mapping `validator_id` to Python class / scope / entity enums; then run **Audit Mode** (effectiveness/relevance/wiring) and **Recommend Mode** (missing guardrails), modeled on `uipath-agents` coded guardrail recommend/validate capability and the same live catalog. `uip codedagent review` (Step 2.5a) owns deterministic coded guardrail checks and emits `CODED_GUARDRAIL_WRONG_IMPORT` / `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS` / `CODED_GUARDRAIL_INVALID_CONTRACT`; never re-emit those. If catalog unavailable, defer Audit-Mode rows (Rules Skipped) per workflow Step 0.

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `CODED_GUARDRAIL_RECOMMENDED` | info | guardrails | In Recommend Mode, read entry `.py` (system prompt, Pydantic input/output schemas, `@tool` docstrings). For each live catalog entry whose `when_to_use` / `use_cases` / `security_risk_addressed` matches and is not wired by matching middleware / `@guardrail`, emit one finding, de-duplicated by `security_category`. Name guardrail/category, matched use case, recommended scope, and action: **block/escalate** when protection is needed (PII that must not enter, injection, harmful content), or **log** for audit only. Do not name platform validators unless already present. file = entry `.py`. | Wire the named guardrail at catalog-recommended scope/action (middleware or `@guardrail`; cite `examples[].config`) — see the `uipath-agents` coded guardrails-recommend capability. |
| `CODED_GUARDRAIL_ACTION_INEFFECTIVE` | judgment | guardrails | In Audit Mode → Actionability, compare validator, scope (`GuardrailScope.*` or decorator target), and action (`BlockAction` / `LogAction` / `EscalateAction` / custom) with catalog `when_not_to_use` / `examples[].config` for that scope. Emit counterproductive actions, including security-critical `LogAction` where the example blocks, PII `Block`/filter at Tool scope on a tool needing the data, or PII `Log` at Agent/Llm. Name recommended action. | Use the catalog action or move the guardrail to an effective scope. |
| `CODED_GUARDRAIL_MISAPPLIED` | judgment | guardrails | In Audit Mode → Relevance + Wiring, read agent context and catalog `when_not_to_use` / `NOT_recommended_for`; emit when a disqualifying condition matches, or when an LLM/Agent-scope `@guardrail` decorates a function that does not return `UiPathChat(...)` / `create_agent(...)` or a non-factory and therefore silently no-ops. Do not re-flag CLI wrong-import, Tool-scope-without-`tools=`, or contract violations. Cite clause or wiring defect. | Remove the guardrail or move the decorator to the correct factory / `@tool`. |
| `CODED_GUARDRAILS_ISSUE` | warning | guardrails | Use only after the three specific rules, Security rules `CODED_PROMPT_USER_INPUT_UNSANITIZED` and `CODED_PII_IN_TRACES`, and deterministic CLI guardrail/secret checks; emit only another concrete guardrail/policy observation. | Defined per finding. |

## CodeChecker

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `PYPROJECT_PLACEHOLDER` | warning | code | Read `[project]` `name` / `description` / `authors` in `pyproject.toml`; emit scaffold defaults such as `my-agent`, `app`, `Add your description here`, or `Your Name <you@example.com>`. | Replace with project-specific metadata. |
| `LANGGRAPH_GRAPH_NOT_COMPILED` | error | code | (`LANGGRAPH` only.) Read the module named by `langgraph.json`; reason through aliases/helpers. Emit when exported `StateGraph(...)` is never `.compile()`d directly or later. | Chain `.compile()` or compile before export. |
| `STATEGRAPH_MISSING_INPUT_OUTPUT` | warning | code | (`LANGGRAPH` only.) Read construction and emit without explicit `input=`/`input_schema=` and `output=`/`output_schema=` schemas. | Pass `input_schema=` and `output_schema=`. |
| `LLAMAINDEX_SYNC_STEP` | error | code | (`LLAMAINDEX` only.) Read workflow and emit for every `@step` method not declared `async def`. | Add `async`. |
| `OPENAI_AGENTS_UNSUPPORTED_FEATURE` | error | code | (`OPENAI_AGENTS` only.) Resolve aliases and emit LangGraph-only `interrupt`, `MemorySaver`, or `InvokeProcess`. | Remove the unsupported call. |
| `CODED_HELPER_TRACING` | info | code | (`LANGGRAPH` only.) Read functions called outside graph nodes (post-processing/formatting); emit untraced helpers lacking `@traced()`. | Add `@traced()`. |
| `CODED_DEAD_CODE` | info | code | Read logic and emit genuinely unreachable conditional branches; skip merely redundant but reachable defensive checks. | Remove the branch or fix its condition. |
| `CODED_LLM_OUTPUT_UNVALIDATED` | warning | code | Read uses of `response.content`, `chat_async(...).strip()`, and `client.invoke(...)`. Emit when output is expected to be constrained (`Literal`, `Enum`, fixed string set, JSON schema) but is not validated before use. Skip `Output.model_validate(...)` and `Enum` checks. | Validate against the expected schema/Enum. |
| `CODED_ERROR_HANDLING` | warning | code | Read external boundaries (LLM `ainvoke`, retriever `ainvoke`, attachment / queues / entities / processes API, HITL `interrupt`, HTTP/DB). Emit each call lacking try/except, fallback, retry, or error-state surfacing; skip pure-Python helpers. Multi-agent supervisors use `CODED_MULTI_AGENT_ERROR_HANDLING`. | Add try/except with fallback or surface the error in output state. |
| `CODED_INVOKEPROCESS_NO_FALLBACK` | warning | code | Only when source imports/calls `InvokeProcess` / `InvokeProcessEvent`. Read `interrupt(InvokeProcess(...))`; emit without branching on `status` via `if`, `match` on `.status`, or `result.get('status')`. General LLM/HTTP/SDK handling belongs to `CODED_ERROR_HANDLING`. | Branch on `result.status` and distinguish `"success"` / `"failed"` / `"faulted"`. |
| `LANGGRAPH_CYCLE_NO_EXIT` | error | code | (`LANGGRAPH` only.) Build topology from `add_node`, `add_edge`, and `add_conditional_edges`; for each cycle, emit when no conditional exit reaches `END` or a non-cycle node, or its router cannot return the exit because required state is never written. | Add a reachable conditional exit based on state nodes write. |
| `CODED_LLM_CLIENT_IMPORT_TIME_INIT` | warning | code | Read module-level statements in the entry module and imports. Emit authenticating/expensive clients (`UiPathChat`, `UiPathAzureChatOpenAI`, `ChatOpenAI`, SDK / HTTP / database client) constructed before function execution, directly, via module-level factory, or default argument. Follow indirection; do not re-flag CLI findings. `uip codedagent init` executes the module to discover schemas. | Construct inside the using function/node or a lazily-called accessor. |
| `CODED_CODE_ISSUE` | warning | code | Use only after specific Code rules for another concrete code observation. | Defined per finding. |

## GeneralChecker

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `CODED_FRAMEWORK_FIT` | info | general | Read source/config and emit only for genuine mismatch: LangGraph for deterministic no-branch pipeline; Simple Function for multi-step persistent-state orchestrator; LlamaIndex for agent with no retrieval. | Switch to a matching framework. |
| `CODED_UIPATH_JSON_FIELD_DRIFT` | warning | general | Read `uipath.json` and source. Emit demonstrably wrong runtime-contract fields, such as `entryPoint: main.py:classify` when function is `main`, `isConversational: true` on stateless agent, or `packOptions.includeUvLock: false`; skip stylistic preferences. | Correct the field to match code reality. |
| `CODED_DOC_CODE_DRIFT` | info | general | Read README and main docstrings. Emit documented integrations/evaluators/behaviors absent from source; skip outdated inline comments and “Future work”/“Roadmap”. | Update docs or implement the feature. |
| `CODED_PROMPT_QUALITY` | warning | general | Read prompts in `UiPathChat`/`UiPathAzureChatOpenAI`, `Agent(instructions=...)`, or `ChatPromptTemplate`. Emit internal contradictions, circular logic, or ambiguity that makes literal readings inconsistent; do not flag length alone. | Reconcile, uncouple circular references, or disambiguate. |
| `CODED_MULTI_AGENT_HUMANMESSAGE_NAME` | info | general | (coded_workflow only.) Read worker returns; emit `HumanMessage(...)` lacking `name="<worker_name>"`. | Add `name="<worker_name>"`. |
| `CODED_MULTI_AGENT_ROUTING_COHERENCE` | warning | general | (coded_workflow only.) Compare supervisor routing prompt with each worker prompt; emit when stated capabilities differ from actual capabilities. | Reconcile routing and worker responsibilities. |
| `CODED_MULTI_AGENT_ERROR_HANDLING` | warning | general | (coded_workflow only.) For ≥2 workers/handoffs, emit when supervisor lacks fallback edges, try/except, or error states in routing. Single-agent handling uses `CODED_ERROR_HANDLING`. | Add supervisor fallback edges or try-except. |
| `CODED_MULTI_AGENT_CROSS_SCHEMA` | warning | general | (coded_workflow only.) For each `sdk.processes.invoke(...)` to a sibling agent, compare `input_arguments` keys/types with target input schema. | Reconcile `input_arguments` with target schema. |
| `CODED_SUB_AGENT_PROMPT_DUPLICATION` | warning | general | (coded_workflow only.) Read worker prompts and emit pairwise paraphrase-equivalent prompts, not merely byte-identical, because indistinguishable workers make routing unreliable. | Give each worker distinct scoped responsibility. |
| `CODED_HANDOFF_NO_TERMINATION` | warning | general | (coded_workflow only.) Read handoff topology (`handoffs=[...]`, supervisor routing, agent graph) and instructions. Emit reachable mutual handoff with no completion criteria, handoff counter, or terminal agent. `LANGGRAPH_CYCLE_NO_EXIT` owns `StateGraph` cycles; this owns delegation. | State completion criteria or enforce a handoff bound. |
| `CODED_GENERAL_ISSUE` | warning | general | Use only when no other category fits, for another concrete repository-hygiene, documentation-drift, or project-structure observation. | Defined per finding. |

## SecurityChecker

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `CODED_PROMPT_USER_INPUT_UNSANITIZED` | warning | security | Read user-controlled fields from `input.X`, request bodies, attachments, or conversational history. Emit each field interpolated into a prompt by concatenation/f-string when neither a `prompt_injection` guardrail nor sanitization (allowlist, length cap, `html.escape`, regex-strip) intervenes. | Sanitize before interpolation or register a `prompt_injection` guardrail. |
| `CODED_PII_IN_TRACES` | warning | security | Read `@traced()` signatures. Emit PII-suggesting params (`email_body`, `customer_email`, `personal_*`, `*_ssn`, `customer_name`) without `hide_input=True` / `input_processor=...`; skip non-PII data such as item IDs and timestamps. | Pass `hide_input=True` or `input_processor=<redaction_fn>` to `@traced(...)`. |

## RuntimeQuirksChecker

| rule_id | severity | category | trigger / detection_method | suggested_fix |
|---|---|---|---|---|
| `LIST_ACCUMULATOR_NOT_FORWARDED` | warning | runtime | (`LANGGRAPH` only; advisory, not gating.) Read state and every node return. For each `Annotated[list[...], operator.add]` reducer key, emit when a node returns only new items rather than prior items. | Forward the accumulator: `{"items": [*state.get("items", []), "new"]}` instead of `{"items": ["new"]}`. |

## What this catalog cannot do

Apply rules to source checked into the repo. It cannot:

- Verify runtime behavior, including whether the LLM follows prompts, chooses the right tool, or routes correctly.
- Verify multi-agent correctness at runtime when structure appears sound but behavior is wrong.
- Verify external dependencies (process schemas, connection IDs, index names).
- Catch deep code logic bugs (field-name mismatches, arithmetic errors); use linters and human code review.

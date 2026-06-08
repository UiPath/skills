# Agents — Coded Judgment Rule Catalog

Judgment rules for **coded** agents (Python — `main.py` + framework config). Each rule requires the agent to read source and reason — what a regex/AST-emulation/file-walk cannot decide reliably. Same row schema as elsewhere — see [`../rule-format.md`](../rule-format.md).

> **This catalog is judgment-only.** Run `uip codedagent review --project-dir "<PROJECT_DIR>" --output json` **first** (SKILL.md Step 2.5) — it returns the deterministic coded findings (pyproject/dependency/python-version gates, import & secret regex, framework symbol existence, bare-except, eval-run analysis, `.venv` packaging, git-tracked secrets) in the same rule format. Then apply the rules below, which the CLI cannot do.

Read [`../rule-format.md`](../rule-format.md) and [`../rule-catalog-workflow.md`](../rule-catalog-workflow.md) first.

Companion files:

- [`agents-common-rules.md`](agents-common-rules.md) — judgment rule shared with low-code agents (schema-description informativeness)
- [`agents-lowcode-rules.md`](agents-lowcode-rules.md) — low-code judgment rules (for the agent-builder coded layout that ships both `agent.json` and `main.py`)

## Framework detection

Many rules below gate on framework. Detect once and reuse:

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

- **Workflow** — one agent, one system prompt (zero for Simple Function), one tool surface, one entry point.
- **Coded workflow** — multiple agents in one project; an orchestrator decides which agent handles which input. Detected when `create_react_agent(...)` is called ≥2 times, or there's a `StateGraph` supervisor over multiple agents, or OpenAI Agents `handoffs=[...]` over multiple `Agent` instances.

Rules in the `## GeneralChecker` section tagged `(coded_workflow only)` skip on single-agent projects.

## How to read this file

One H2 section per checker class groups related rules for navigation. Every row's `detection_method` is the **judgment form**: read the named source, reason about it, emit when the criteria hold. Log the reasoning in the finding's `description`. Each section's last row is a `CODED_*_ISSUE` category bucket — use **only** when no specific rule fits the observation; do not bend specific rules to use a bucket.

---

## EvalsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `CODED_EVAL_TRAJECTORY_SPECIFICITY` | warning | evals | Agent with 3+ tool calls has trajectory evaluators with generic `expectedAgentBehavior` | Read tools (AST-detected) + eval set. Assess: for agents with 3+ tool calls in a typical flow, do trajectory evaluators have `expectedAgentBehavior` specific enough to catch wrong tool sequences? `"Agent should process the input and return a response"` is too generic. Good: names tools, ordering, decisions. Emit per generic description. file = eval set JSON, element = evaluator id. | Rewrite `expectedAgentBehavior` to name the specific tool sequence and decisions. |
| `CODED_EVAL_ARCHETYPE_FIT` | warning | evals | Chosen evaluators don't match the agent's archetype (LLM-only on tool agent, exact-match on free-form text, etc.) | Read agent source + eval evaluators. Classify the agent archetype: calculator/deterministic, text generator, multi-step orchestrator, API integration, classifier. Compare against [Archetype quick reference](#archetype-quick-reference) below. Emit per mismatch. file = eval set JSON. | Pick evaluators per the archetype reference: deterministic agents → exact-match/JSON-similarity; orchestrators → trajectory; classifiers → multiclass. |
| `CODED_EVAL_SET_ORGANISATION` | info | evals | Mixed scenario concerns within one eval set, or unrelated agents share one set | Read eval sets. Assess: does one set mix happy-path + intentional-failure datapoints that distort the pass rate, or exercise unrelated agents in the same project? DO NOT fire on file-naming conventions (e.g. `set-1.json` is fine). Emit on content or ownership problems only. file = eval set JSON. | Split mixed sets by scenario type or agent; document the intent of each set in its filename or metadata. |
| `CODED_EVAL_BEHAVIOR_DESCRIPTION` | warning | evals | `expectedAgentBehavior` is generic, not specific | Read each eval entry's `expectedAgentBehavior`. Assess: does it name the specific tools, steps, or decisions the agent should take? Strings like `"Agent should handle the request appropriately"` fail. file = eval set JSON, element = datapoint id. | Name the specific tools, steps, or decisions in the description. |
| `CODED_EVAL_FORMAT_MISMATCH` | warning | evals | Expected-output string format doesn't match the agent's runtime serialization | Read eval `expectedOutput` strings + agent's output type (Pydantic / dataclass / JSON). Assess concrete mismatches: Python single-quoted dict (`"{'temperature': 25.0}"`) when runtime emits JSON; trailing-comma JSON; bytes-vs-string; regex anchors on a non-regex evaluator. Don't speculate — fire only on inspectable inconsistencies. file = eval set JSON, element = datapoint id. | Reformat `expectedOutput` to match the agent's actual serialization. |
| `CODED_EVAL_COVERAGE_GAP` | warning | evals | Registered evaluator never referenced by an eval set, OR a code path never exercised by any datapoint | Read evaluator configs + eval-set `evaluationCriterias` keys. Assess: is each evaluator config referenced by ≥1 eval entry? Symmetrically, read agent source — does each declared code branch (platform-vs-local, error handler, rejection route) get exercised by ≥1 eval input? Emit per concrete gap. file = evaluator config or source file. | Either add eval entries that reference the evaluator / exercise the path, or remove the unused config. |
| `CODED_EVAL_GROUND_TRUTH_MISLABELED` | warning | evals | Datapoint's expected class demonstrably contradicts input content | Read each datapoint's `.inputs` + `.expectedOutput` / `.expectedClass`. Assess: does the label unambiguously contradict input semantics (e.g., email body "I want to refund" labeled `expectedClass: "spam"`)? Borderline labels are eval-author judgment — skip. Emit on clear contradictions only. file = eval set JSON, element = datapoint id. | Correct the label, or split the datapoint into separate scenarios. |
| `CODED_EVAL_DATASET_SINGLE_CLASS` | warning | evals | Multiclass evaluator paired with ≥3-datapoint dataset where all labels are identical | Read evaluator types + eval set labels. Assess: is the evaluator multi-class shape (`uipath-multiclass-classification`, custom balanced-accuracy with `classCounts: {…}`)? AND does the dataset have ≥3 datapoints all sharing the same label? Skip when evaluator is single-class by design (`uipath-binary-classification` for one-class detection) or when dataset has <3 datapoints. file = eval set JSON. | Add datapoints with the other classes, or switch to `uipath-binary-classification` for one-class detection. |
| `CODED_EVAL_ISSUE` | warning | evals | Eval-infrastructure observation that no specific rule above fits | Use ONLY when no specific Evals rule fits. Walk all rules in this section first. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

### Archetype quick reference

| Agent archetype | Primary evaluator | Secondary | Mismatch to flag |
|---|---|---|---|
| Calculator / deterministic | `uipath-exact-match` or `file://` | — | LLM judge on deterministic output with no deterministic evaluator |
| Text generator / summariser | `uipath-llm-judge-output-semantic-similarity` | `uipath-contains` | `exact-match` on free-form text |
| Multi-step orchestrator | `uipath-llm-judge-trajectory-similarity` | `uipath-tool-call-order` | No trajectory evaluator |
| API integration | `uipath-json-similarity` or `file://` | `uipath-exact-match` | No structured comparison |
| Classifier | `uipath-binary-classification` / `uipath-multiclass-classification` or `file://` | — | `exact-match` on classification output |

LLM-judge-only is acceptable when the agent has no tools, no classification output, and emits free-form text. Otherwise prefer pairing with a deterministic baseline.

---

## SchemaChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `CODED_SCHEMA_COMPLETENESS` | warning | schema | `StateGraph` input/output schema is technically present but the fields are insufficient for the agent's contract | Read `StateGraph(input=..., output=...)` (or `_schema=` variants). Read the agent's actual behavior. Assess: are declared input/output fields meaningful and sufficient? An agent that needs `customer_history` + `recent_invoices` but only declares `query: str` is incomplete. file = source file. | Expand the schema to carry the context the agent actually needs / returns. |
| `CODED_SCHEMA_FIELD_NO_VALIDATION` | warning | schema | Constrained-value field declared as bare `str` (no `Literal`/`Enum`/regex pattern) | Read Pydantic / dataclass models. Assess per field: does the name suggest a constrained set (`category`, `status`, `severity`, `role`, `intent`, `classification`, `priority`)? AND is the type bare `str` (no `Literal`, no `Enum`, no validator)? AND does the agent's logic visibly map to a small enumerated set? Emit per concrete case. file = source file, element = `<Model>.<field>`. | Type the field as `Literal["a", "b", "c"]` or `Enum`, or add `Field(..., pattern="...")`. |
| `CODED_OUTPUT_ENUM_MISSING_ON_CLASSIFIER` | warning | schema | Classifier-shaped output field declared without enum | Read output schema (Pydantic field, `StateGraph` output annotation, dataclass). Identify classifier-shape fields by name (`class`, `classification`, `label`, `category`, `intent`, `severity`, `priority`, `status`) with `type: str`. Assess: is there a `Literal[...]` / `Enum` / pattern constraint? Both this rule and `CODED_SCHEMA_FIELD_NO_VALIDATION` can fire on the same field — the more-specific firing clarifies the issue. file = source file, element = field name. | Add `Literal[...]` / `Enum` / pattern constraint to the classifier output field. |
| `CODED_SCHEMA_ISSUE` | warning | schema | Schema observation that no specific rule above fits | Use ONLY when no specific Schema rule fits. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

---

## ToolsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `CODED_TOOL_DOCSTRING_QUALITY` | warning | tools | Tool docstring missing, generic, or missing parameter mention | Read each tool-surface function (passed to `bind_tools`, `@tool`-decorated, registered via `Tool(...)`). Assess docstring: is it missing or <20 chars? Does it state what the tool does in plain language? Does it mention every declared parameter? Is it generic boilerplate? Fire when **at least one** of these holds. Don't fire when the docstring names every param and either describes the return shape or gives a usage cue. file = source file, element = function name. | Write a docstring that names every parameter, describes the return shape, and gives a usage cue (preconditions, side effects, example). |
| `CODED_PROMPT_TOOL_COVERAGE` | warning | tools | Fewer than half the registered tools are mentioned in the system prompt | Read system prompt (passed to `UiPathChat`/`UiPathAzureChatOpenAI`/`Agent(instructions=...)`). Read tool registrations. Assess: is each tool mentioned by name or described by purpose? Emit when `<50%` are referenced. file = source file. | Reference each tool by name in the system prompt with guidance on when to use it. |
| `CODED_PROMPT_REFERENCES_NONEXISTENT_TOOL` | warning | tools | System prompt names a tool that's not registered | Read system prompt. Extract tool names cited (backticked, quoted, "the X tool"). Build registered tool set (`@tool`-decorated, `Tool(...)` registered, `bind_tools` entries). Emit per cited name not in registered set. Skip prose references like "use a search tool" without specific identifiers. file = source file, element = missing tool name. | Either rename the tool, register the cited tool, or remove the prompt reference. |
| `CODED_TOOLS_ISSUE` | warning | tools | Tools observation that no specific rule above fits | Use ONLY when no specific Tools rule fits. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

---

## GuardrailsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `CODED_GUARDRAILS_ISSUE` | warning | guardrails | Guardrails / safety / PII observation that no specific rule fits | Use ONLY when no specific rule fits. Coded agents have most safety concerns covered under `## SecurityChecker` (`CODED_PROMPT_USER_INPUT_UNSANITIZED`, `CODED_PII_IN_TRACES`) and the deterministic secret/`.env` checks in the review CLI. Reach here only for guardrail / policy observations none of those cover. | (Defined per finding.) |

---

## CodeChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `PYPROJECT_PLACEHOLDER` | warning | code | `name`, `description`, or `authors` are leftover scaffold defaults, not real metadata | Read `pyproject.toml` `[project]` `name` / `description` / `authors`. Assess: are these real project metadata or scaffold defaults left unchanged (`my-agent`, `app`, `Add your description here`, `Your Name <you@example.com>`)? Code cannot reliably tell a real value from a leftover placeholder — this is a semantic read. file = `pyproject.toml`, element = field name. | Replace placeholder values with project-specific metadata. |
| `LANGGRAPH_GRAPH_NOT_COMPILED` | error | code | Exported graph symbol is a `StateGraph(...)` never `.compile()`d (`LANGGRAPH` only) | Read the module `langgraph.json` points to. Assess: is the exported graph symbol the result of a `.compile()` call? A top-level `graph = StateGraph(...)` with no trailing `.compile()` (on the same or a later line, directly or via a helper) ships an uncompiled graph the runtime can't execute. Reason about aliasing/indirection a regex would miss. file = source file, element = graph symbol. | Chain `.compile()` onto the `StateGraph(...)` (or compile it before export). |
| `STATEGRAPH_MISSING_INPUT_OUTPUT` | warning | code | `StateGraph(...)` built without explicit input/output schemas (`LANGGRAPH` only) | Read the `StateGraph(...)` construction. Assess: are explicit `input=`/`input_schema=` and `output=`/`output_schema=` schemas passed? Without them the graph's external contract is the full internal state, leaking intermediate fields. file = source file. | Pass `input_schema=` and `output_schema=` to `StateGraph(...)`. |
| `LLAMAINDEX_SYNC_STEP` | error | code | `@step`-decorated method is not `async def` (`LLAMAINDEX` only) | Read the workflow source. Assess: is every `@step`-decorated method declared `async def`? A synchronous `@step` breaks the LlamaIndex workflow runtime. file = source file, element = method name. | Add `async` to the step method. |
| `OPENAI_AGENTS_UNSUPPORTED_FEATURE` | error | code | LangGraph-only feature called in an OpenAI Agents project (`OPENAI_AGENTS` only) | Read source. Assess: does it call `interrupt`, `MemorySaver`, or `InvokeProcess` — LangGraph-specific features unsupported under OpenAI Agents? Resolve import aliasing (`from x import interrupt as y`) the way a regex cannot. file = source file, element = unsupported call. | Remove the unsupported call — these are LangGraph-specific. |
| `CODED_HELPER_TRACING` | info | code | LangGraph helpers outside the graph lack `@traced()` (`LANGGRAPH` only) | Read source. Identify functions called outside graph nodes (post-processing, formatting). Assess: do they have `@traced()`? Without it, helper execution won't appear in traces. Emit per untraced helper. file = source file, element = function name. | Decorate helper functions outside the graph with `@traced()`. |
| `CODED_DEAD_CODE` | info | code | Unreachable conditional branch in agent logic | Read source. Assess: are there conditionals where one branch can never execute (`if x > y: do_a; if x > 0: do_b` — second branch unreachable when `x > y > 0`)? Skip merely-redundant-but-reachable defensive checks. Emit per concrete unreachable branch. file = source file, element = `<function>:<line>`. | Remove the unreachable branch, or fix the condition that makes it unreachable. |
| `CODED_LLM_OUTPUT_UNVALIDATED` | warning | code | LLM completion used downstream without value-space validation | Read code paths that consume LLM responses (`response.content`, `chat_async(...).strip()`, `client.invoke(...)`). Assess per use site: (a) is the output constrained (`Literal`, `Enum`, fixed string set, JSON schema)? AND (b) is there no validation between the LLM call and the use site? Skip when consumed via `Output.model_validate(...)` or `Enum`-checked. Emit per concrete case. file = source file. | Validate the LLM response against the expected schema/Enum before downstream use. |
| `CODED_ERROR_HANDLING` | warning | code | Risky external-call site without try/except, fallback, retry, or error surfacing | Read source. Identify external boundaries that can fail in production (LLM `ainvoke`, retriever `ainvoke`, attachment / queues / entities / processes API, HITL `interrupt`, HTTP/DB). Assess per call site: is there a `try/except`, fallback, retry, or error-state surfacing? Skip pure-Python helpers. The multi-agent supervisor variant is `CODED_MULTI_AGENT_ERROR_HANDLING`. Emit per concrete case. file = source file. | Wrap the call in try/except with a fallback path or surface the error in the agent's output state. |
| `CODED_INVOKEPROCESS_NO_FALLBACK` | warning | code | `interrupt(InvokeProcess(...))` call without branching on `result.status` | Read source. Fire only when source actually imports or calls `InvokeProcess` / `InvokeProcessEvent`. Assess: does the code branch on `status` (`if status ==`, `match` on `.status`, `result.get('status')`)? Without it, `failed`/`faulted` returns malformed data. For general LLM / HTTP / SDK retry use `CODED_ERROR_HANDLING` instead. file = source file. | Branch on `result.status`: handle `"success"` / `"failed"` / `"faulted"` distinctly. |
| `CODED_CODE_ISSUE` | warning | code | Code observation that no specific rule above fits | Use ONLY when no specific Code rule fits. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

---

## GeneralChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `CODED_FRAMEWORK_FIT` | info | general | Framework chosen is a genuine mismatch for the task | Read source + framework config. Assess: is the framework appropriate? Real mismatches: LangGraph used for a deterministic pipeline with no branching; Simple Function used for a multi-step orchestrator that needs persistent state; LlamaIndex used for an agent with no retrieval. **Fire ONLY on real mismatch** — never as a commentary slot when the framework genuinely fits. file = framework config. | Switch to the framework that matches the task pattern. |
| `CODED_UIPATH_JSON_FIELD_DRIFT` | warning | general | `uipath.json` field demonstrably wrong (`entryPoint` mismatch, `isConversational` wrong, `includeUvLock: false`, …) | Read `uipath.json` + source. Assess per field: does the declared value contradict the actual code shape or break the runtime contract? `entryPoint: main.py:classify` when the function is `main`; `isConversational: true` on a stateless agent; `packOptions.includeUvLock: false` (deployment-blocker). Skip stylistic preferences. file = `uipath.json`, element = field name. | Correct the field to match the code reality. |
| `CODED_DOC_CODE_DRIFT` | info | general | README / docstring describes a feature the code doesn't implement | Read README + main docstrings. Assess: do they mention integrations, evaluators, or behaviors absent from source? Trust hazard for future contributors. Skip outdated inline comments inside functions (different concern) and "Future work" / "Roadmap" sections. file = README or docstring source. | Update the doc to match what the code actually does, or implement the documented feature. |
| `CODED_PROMPT_QUALITY` | warning | general | System prompt has internal contradictions, circular logic, or ambiguous instructions | Read any system prompt embedded in coded source (`UiPathChat`/`UiPathAzureChatOpenAI`, `Agent(instructions=...)`, `ChatPromptTemplate` strings). Assess: (a) internal contradictions ("Always respond in JSON" + "Write as a friendly paragraph"); (b) circular logic (rule X says "see Y", Y says "see X"); (c) ambiguous instructions two readers would interpret differently. DO NOT fire merely because the prompt is long. Bar: literal reading produces inconsistent behaviour. file = source file. | Reconcile contradictions, break circular references, or disambiguate. |
| `CODED_MULTI_AGENT_HUMANMESSAGE_NAME` | info | general | (coded_workflow only) Worker `HumanMessage(...)` returns lack `name="<worker_name>"` | Read worker functions in a multi-agent / supervisor setup. Assess: do they return `HumanMessage(content=..., name="<worker_name>")`? Without `name`, the supervisor cannot attribute responses. file = source file, element = worker name. | Add `name="<worker_name>"` to each worker's `HumanMessage(...)`. |
| `CODED_MULTI_AGENT_ROUTING_COHERENCE` | warning | general | (coded_workflow only) Supervisor routing description doesn't match each worker's actual capability | Read supervisor routing prompt + each worker's system prompt. Assess: does the routing description match what each worker actually does? "Researcher handles fact-finding" + worker actually generates code → routing will be unreliable. file = supervisor source. | Reconcile routing description with worker capabilities; or rename / repurpose workers. |
| `CODED_MULTI_AGENT_ERROR_HANDLING` | warning | general | (coded_workflow only) Multi-agent project lacks supervisor-level error handling | Read supervisor. Assess: project has ≥2 sub-agents (workers / handoffs) AND supervisor lacks fallback edges, try/except, or error states in routing logic. An unhandled worker exception terminates the entire graph. For single-agent error handling use `CODED_ERROR_HANDLING`. file = supervisor source. | Add fallback edges / try-except at the supervisor level. |
| `CODED_MULTI_AGENT_CROSS_SCHEMA` | warning | general | (coded_workflow only) `sdk.processes.invoke(...)` targeting a sibling agent has cross-schema mismatch | Read source. For each `sdk.processes.invoke()` targeting another agent in the same repo, read both the call's `input_arguments` and the target agent's declared input schema. Assess: are keys + types consistent? Emit per concrete mismatch. file = source file. | Reconcile `input_arguments` with the target agent's input schema. |
| `CODED_SUB_AGENT_PROMPT_DUPLICATION` | warning | general | (coded_workflow only) Two or more sub-agent prompts are substantively the same (paraphrase-equivalent) | Read each sub-agent's system prompt (`create_react_agent` workers, `Agent[Ctx]` instances). Assess pairwise: are any two prompts paraphrase-equivalent (not literal byte-match)? Routing becomes unreliable when worker capabilities are indistinguishable. file = source file, element = `<agent_a>,<agent_b>`. | Differentiate prompts so each worker has a distinct, scoped responsibility. |
| `CODED_GENERAL_ISSUE` | warning | general | General-category observation that no specific rule above fits | Use ONLY when no other category fits — repository hygiene, documentation drift, project structure. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

---

## SecurityChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `CODED_PROMPT_USER_INPUT_UNSANITIZED` | warning | security | User-controlled input interpolated into LLM prompt without sanitization | Read source. Identify user-controlled fields (function params from `input.X`, request body, attachment content, conversational history). Assess per use: (a) does the field reach a prompt template via concatenation / f-string (`f"Classify this email: {input.email_body}"`)? AND (b) is no `prompt_injection` guardrail registered? AND (c) is no sanitization helper (allowlist match, length cap, `html.escape`, regex-strip) between input and prompt? file = source file. | Sanitize the input before interpolation, or register a `prompt_injection` guardrail. |
| `CODED_PII_IN_TRACES` | warning | security | `@traced()` on a function receiving PII-suggesting fields without redaction | Read `@traced`-decorated function signatures. Assess: do params have names suggesting PII (`email_body`, `customer_email`, `personal_*`, `*_ssn`, `customer_name`)? AND does the decorator lack `hide_input=True` / `input_processor=...`? Skip when the function only handles non-PII data (item IDs, timestamps). Emit per concrete case. file = source file, element = function name. | Pass `hide_input=True` or `input_processor=<redaction_fn>` to `@traced(...)`. |

---

## RuntimeQuirksChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `LIST_ACCUMULATOR_NOT_FORWARDED` | warning | runtime | LangGraph reducer-typed state key returned by a node without forwarding prior items (`LANGGRAPH` only) | Read the LangGraph state class + every node return. Assess: for each state key typed `Annotated[list[...], operator.add]` (a reducer), does any node return that key with only its new items instead of forwarding prior state? This is a whole-program dataflow read with no reliable regex — reason about it. **Advisory, not gating.** file = source file, element = state key. | Forward the accumulator: return `{"items": [*state.get("items", []), "new"]}` instead of `{"items": ["new"]}`. |

---

## What this catalog cannot do

The agent applies these rules from the project source as it is *checked into the repo*. It cannot:

- Verify runtime behavior (whether the LLM follows the prompt, picks the right tool, routes correctly).
- Verify multi-agent correctness at runtime — routing logic can look structurally sound and still produce wrong results.
- Verify external dependencies (process schemas, connection IDs, index names).
- Catch deep code logic bugs (field-name mismatches, arithmetic errors) — those are for linters and human code review.

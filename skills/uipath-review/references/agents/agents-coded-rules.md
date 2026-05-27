# Agents — Coded Rule Catalog

Unified catalog for **coded** agents (Python — `main.py` + framework config). Mixes mechanical rules (resolved via `Read` / `Grep` / `Glob` / `Bash` / `uip agent review`) and judgment rules (the agent reads source and reasons). Same row schema for both — see [`../rule-format.md`](../rule-format.md).

Read [`../rule-format.md`](../rule-format.md) and [`../rule-catalog-workflow.md`](../rule-catalog-workflow.md) first.

Companion files:

- [`agents-common-rules.md`](agents-common-rules.md) — rules shared with low-code agents (eval counts, schema descriptions, tool count)
- [`agents-lowcode-rules.md`](agents-lowcode-rules.md) — low-code agent rules (for the agent-builder coded layout that ships both `agent.json` and `main.py`)

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

- One H2 section per POC checker class. Names match the `uip agent review --checks <name>` vocabulary (lowercased): `evals`, `schema`, `tools`, `guardrails`, `code`, `general`, `security`, `runtime`, `eval-results`.
- Inside each section, rules sit in one table. The `detection_method` column tells you which form to use: inline (Glob/Read+JSON/Grep/Bash), CLI (`uip agent review`), or judgment (read + reason).
- The optional `status: deferred` flag means "documented but do not apply" — record in the report's "Rules Skipped" section.
- Each section's last row is a `CODED_*_ISSUE` category bucket — use **only** when no specific rule fits the observation; do not bend specific rules to use a bucket.

---

## EvalsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `MISSING_EVAL_DIR` | error | evals | No eval-sets directory found | `Glob 'eval-sets/'`, `'evals/eval-sets/'`, `'evaluations/eval-sets/'` at project root. Emit when none match. file = project root. | Create `evaluations/eval-sets/` and add at least one eval set JSON before deploying. |
| `EVAL_LLM_JUDGE_ONLY` | error | evals | All evaluators are LLM-judge; zero deterministic evaluators (including `file://` custom) | Walk `evaluations/evaluators/*.json`. Build set of `.type` values. Treat any `file://<path>` evaluator as deterministic coverage. Emit when set is non-empty AND every type is in `LLM_JUDGE_TYPES`. file = `evaluations/evaluators/`. | Add at least one deterministic evaluator (exact-match, contains, JSON similarity, tool-call, or `file://` custom) so failures are reproducible. |
| `EVAL_NO_LLM_JUDGE` | info | evals | All evaluators deterministic, zero LLM judge, >1 total | Same scan. Emit when total > 1 AND no type in `LLM_JUDGE_TYPES` (excluding `file://` custom). file = `evaluations/evaluators/`. | Consider adding one LLM judge for semantic similarity — deterministic evaluators alone miss paraphrased correct outputs. |
| `EVAL_JUDGE_HIGH_TEMPERATURE` | warning | evals | Any LLM judge has `temperature > 0.3` | Walk LLM-judge evaluators. Emit one finding per evaluator with `.config.temperature > 0.3` (or `.parameters.temperature`). file = evaluator JSON, element = evaluator id. | Lower judge temperature to ≤ 0.3 — high temperature makes judge scores non-reproducible. |
| `EVAL_JUDGE_WEAK_MODEL` | warning | evals | LLM judge uses weak model | Walk LLM-judge evaluators. Emit when `.config.model` (or `.model`) matches any of: `gpt-3.5*`, `gpt-4o-mini*`, `*haiku*`, `*flash*`, `llama-3-8b*`, `mistral-7b*`, `phi-3*` (case-insensitive). file = evaluator JSON, element = evaluator id. | Use GPT-4o, Claude Sonnet 4+, or equivalent for judge models. |
| `EVAL_JUDGE_NO_REASONING` | warning | evals | LLM judge prompt missing reasoning keywords | Walk LLM-judge evaluators. Read `.config.prompt` (or `.prompt`). Emit when prompt contains none of: `reason`, `explain`, `justify`, `step by step`, `rationale` (case-insensitive). file = evaluator JSON, element = evaluator id. | Add "explain your reasoning step by step" to the judge prompt — chain-of-thought lifts judge accuracy. |
| `EVAL_NO_TOOL_CALL_EVALUATORS` | warning | evals | Agent has tools (AST-detected) but no `tool-call-*` evaluators | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks evals --output json`; pick `rule_id == "EVAL_NO_TOOL_CALL_EVALUATORS"`. | Add a `uipath-tool-call-count` or `uipath-tool-call-order` evaluator. |
| `EVAL_BROKEN_EVALUATOR_REF` | error | evals | Eval set's `evaluatorRefs` reference an evaluator id with no matching `evaluations/evaluators/*.json` config | `Glob 'eval-sets/*.json'`, `'evals/eval-sets/*.json'`, `'evaluations/eval-sets/*.json'`. For each, read `.evaluatorRefs[]` and `.evaluations[].evaluationCriterias` keys. Build referenced-id set. Build configured-id set from `evaluations/evaluators/*.json` `.id` fields. Emit one finding per referenced id not in configured set. file = eval set JSON, element = `<eval_set_id>:<broken_ref>`. | Add the missing evaluator config or remove the dangling reference. |
| `EVAL_TRAJECTORY_NEEDS_TRACE_SPANS` | warning | evals | Eval set uses trajectory judge AND framework is `FUNCTION` only AND no `@traced` decorator anywhere in source | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks evals --output json`; pick `rule_id == "EVAL_TRAJECTORY_NEEDS_TRACE_SPANS"`. | Decorate orchestration functions with `@traced()` from `uipath.tracing`. |
| `EVAL_TEST_ID_NUMBERED_NOT_DESCRIPTIVE` | info | evals | >50% of test IDs in an eval set match `^test-\d+$`, min 3 entries | For each eval set, count entries with `.id` matching `/^test-\d+$/`. Emit per eval set when `total >= 3` AND `numbered/total > 0.5`. file = eval set JSON. | Rename entries to scenario-descriptive IDs (e.g. `test-empty-input`). |
| `EVAL_LABEL_LEAKAGE` | warning | evals | Eval entry's `expectedOutput` appears verbatim as a value in `inputs` (min 3 chars after strip) | For each eval datapoint, get `expectedOutput` (and `evaluationCriterias.*.expectedOutput`). Walk `.inputs` recursively. Emit when any input value equals the expected output (after strip) and `len(expected.strip()) >= 3`. file = eval set JSON, element = `<eval_set_id>:<datapoint_id>`. | Restructure the datapoint so expected output is not literally in the input. |
| `EVAL_FILENAME_MISMATCH` | warning | evals | `fileName` field in eval set does not match actual file name | For each eval set, read `.fileName`. Emit when set and ≠ basename. file = eval set JSON. | Update `fileName` to match the actual file name, or remove the field. |
| `EVAL_UNIFORM_EXPECTED_BEHAVIOR` | warning | evals | >80% of eval entries share the same `expectedAgentBehavior` string (min 4 entries) | For each eval set, build histogram of `.evaluations[].expectedAgentBehavior` (canonicalized). Emit when `total >= 4` AND `max-count/total > 0.8`. file = eval set JSON. | Diversify `expectedAgentBehavior` — uniform expectations let pass/fail hinge on a single behavior. |
| `EVAL_COPY_PASTE_INPUTS` | error | evals | Multiple eval entries share identical `inputs` (canonicalised JSON match) | For each eval set, canonicalize `.evaluations[].inputs` (sorted JSON). Emit one finding per duplicate group. file = eval set JSON, element = `<dup_id_1>,<dup_id_2>,...`. | Remove or alter duplicate inputs. |
| `EVAL_PLACEHOLDER_OUTPUTS` | warning | evals | `expectedOutput` is a placeholder literal | Read each `expectedOutput`. Emit when matches (case-insensitive): `TODO`, `FIXME`, `[Your Company Name]`, `<...>`, `xxx`, `placeholder`. Skip `None` / empty. file = eval set JSON, element = datapoint id. | Replace with the canonical expected output for the scenario. |
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
| `SCHEMA_DRIFT` | warning | schema | Entry-point schema fields don't match any Python Pydantic class in source | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks schema --output json`; pick `rule_id == "SCHEMA_DRIFT"`. | Sync the Pydantic class with `entry-points.json` (or `uipath.json[entryPoints]` for legacy). |
| `CODED_SCHEMA_COMPLETENESS` | warning | schema | `StateGraph` input/output schema is technically present but the fields are insufficient for the agent's contract | Read `StateGraph(input=..., output=...)` (or `_schema=` variants). Read the agent's actual behavior. Assess: are declared input/output fields meaningful and sufficient? An agent that needs `customer_history` + `recent_invoices` but only declares `query: str` is incomplete. file = source file. | Expand the schema to carry the context the agent actually needs / returns. |
| `CODED_SCHEMA_FIELD_NO_VALIDATION` | warning | schema | Constrained-value field declared as bare `str` (no `Literal`/`Enum`/regex pattern) | Read Pydantic / dataclass models. Assess per field: does the name suggest a constrained set (`category`, `status`, `severity`, `role`, `intent`, `classification`, `priority`)? AND is the type bare `str` (no `Literal`, no `Enum`, no validator)? AND does the agent's logic visibly map to a small enumerated set? Emit per concrete case. file = source file, element = `<Model>.<field>`. | Type the field as `Literal["a", "b", "c"]` or `Enum`, or add `Field(..., pattern="...")`. |
| `CODED_OUTPUT_ENUM_MISSING_ON_CLASSIFIER` | warning | schema | Classifier-shaped output field declared without enum | Read output schema (Pydantic field, `StateGraph` output annotation, dataclass). Identify classifier-shape fields by name (`class`, `classification`, `label`, `category`, `intent`, `severity`, `priority`, `status`) with `type: str`. Assess: is there a `Literal[...]` / `Enum` / pattern constraint? Both this rule and `CODED_SCHEMA_FIELD_NO_VALIDATION` can fire on the same field — the more-specific firing clarifies the issue. file = source file, element = field name. | Add `Literal[...]` / `Enum` / pattern constraint to the classifier output field. |
| `CODED_SCHEMA_ISSUE` | warning | schema | Schema observation that no specific rule above fits | Use ONLY when no specific Schema rule fits. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

---

## ToolsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `TOOL_PARAM_UNUSED` | warning | tools | `@tool`-decorated function declares a parameter never read in its body | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks tools --output json`; pick `rule_id == "TOOL_PARAM_UNUSED"`. | Either use the parameter or prefix it with `_` to suppress. |
| `CODED_TOOL_DOCSTRING_QUALITY` | warning | tools | Tool docstring missing, generic, or missing parameter mention | Read each tool-surface function (passed to `bind_tools`, `@tool`-decorated, registered via `Tool(...)`). Assess docstring: is it missing or <20 chars? Does it state what the tool does in plain language? Does it mention every declared parameter? Is it generic boilerplate? Fire when **at least one** of these holds. Don't fire when the docstring names every param and either describes the return shape or gives a usage cue. file = source file, element = function name. | Write a docstring that names every parameter, describes the return shape, and gives a usage cue (preconditions, side effects, example). |
| `CODED_PROMPT_TOOL_COVERAGE` | warning | tools | Fewer than half the registered tools are mentioned in the system prompt | Read system prompt (passed to `UiPathChat`/`UiPathAzureChatOpenAI`/`Agent(instructions=...)`). Read tool registrations. Assess: is each tool mentioned by name or described by purpose? Emit when `<50%` are referenced. file = source file. | Reference each tool by name in the system prompt with guidance on when to use it. |
| `CODED_PROMPT_REFERENCES_NONEXISTENT_TOOL` | warning | tools | System prompt names a tool that's not registered | Read system prompt. Extract tool names cited (backticked, quoted, "the X tool"). Build registered tool set (`@tool`-decorated, `Tool(...)` registered, `bind_tools` entries). Emit per cited name not in registered set. Skip prose references like "use a search tool" without specific identifiers. file = source file, element = missing tool name. | Either rename the tool, register the cited tool, or remove the prompt reference. |
| `CODED_TOOLS_ISSUE` | warning | tools | Tools observation that no specific rule above fits | Use ONLY when no specific Tools rule fits. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

---

## GuardrailsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `CODED_GUARDRAILS_ISSUE` | warning | guardrails | Guardrails / safety / PII observation that no specific rule fits | Use ONLY when no specific rule fits. Coded agents have most safety concerns covered under `## SecurityChecker` (`CODED_PROMPT_USER_INPUT_UNSANITIZED`, `CODED_PII_IN_TRACES`, `TRACING_DATA_LEAK`, `ENV_FILE_TRACKED`). Reach here only for guardrail / policy observations none of those cover. | (Defined per finding.) |

---

## CodeChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `MISSING_PYPROJECT` | error | code | No `pyproject.toml` found | `Glob 'pyproject.toml'`. Emit when zero matches. file = project root. | Create `pyproject.toml` with `[project]` metadata, `requires-python>=3.11`, and the appropriate `uipath-*` framework dependency. |
| `PYTHON_SYNTAX_ERROR` | error | code | `ast.parse()` fails on any `.py` file | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks code --output json`; pick `rule_id == "PYTHON_SYNTAX_ERROR"`. | Fix the syntax error reported in the finding's description. |
| `MISSING_RETURN_TYPE` | warning | code | Public function missing return type annotation | Run `uip agent review --checks code`; pick `rule_id == "MISSING_RETURN_TYPE"`. | Add `-> <ReturnType>` to the function signature. |
| `BARE_EXCEPT` | warning | code | Bare `except:` without exception type | Run `uip agent review --checks code`; pick `rule_id == "BARE_EXCEPT"`. | Catch a specific exception class. |
| `NO_TRACING` | info | code | `FUNCTION` framework project has async code but no `@traced` decorator anywhere | Run `uip agent review --checks code`; pick `rule_id == "NO_TRACING"`. | Decorate at least one orchestration function with `@traced()` from `uipath.tracing`. |
| `HARDCODED_CREDENTIALS` | error | security | Secret patterns in source | For each `.py` under project root (excluding `tests/`, `evals/`, `evaluations/`, `.venv/`, `__pycache__/`), `Grep -n` for: `(api_key\|secret\|password\|token\|credential)\s*=\s*["'][^"']{8,}["']`, `sk-[A-Za-z0-9]{20,}`, `ghp_[A-Za-z0-9]{20,}`, `gho_[A-Za-z0-9]{20,}`, `github_pat_[A-Za-z0-9_]{20,}`, `xoxb-[A-Za-z0-9-]{20,}`, `xoxp-[A-Za-z0-9-]{20,}`, `Bearer [A-Za-z0-9._-]{20,}`. Emit one finding per match. file = source file, line = match line. | Move the secret to an Orchestrator asset or environment variable and read it via `uipath.assets.get(...)` or `os.environ[...]`. |
| `FILE_READ_ERROR` | warning | code | Cannot read a Python source file | When the Read tool fails on a `.py` file during other checks (encoding error, permission denied), emit one finding per such file. file = source file. | Re-encode the file as UTF-8 or fix the permission bit. |
| `REQUIRES_PYTHON_TOO_LOW` | error | code | `requires-python` minimum below 3.11 | Run `uip agent review --checks code`; pick `rule_id == "REQUIRES_PYTHON_TOO_LOW"`. | Set `requires-python = ">=3.11"` in `[project]`. |
| `UIPATH_DEV_IN_RUNTIME_DEPS` | warning | code | `uipath-dev` in `[project] dependencies` instead of `[dependency-groups] dev` | Run `uip agent review --checks code`; pick `rule_id == "UIPATH_DEV_IN_RUNTIME_DEPS"`. | Move `uipath-dev` to `[dependency-groups] dev`. |
| `PYPROJECT_PLACEHOLDER` | warning | code | `name`, `description`, or `authors` contain known placeholder values | Run `uip agent review --checks code`; pick `rule_id == "PYPROJECT_PLACEHOLDER"`. | Replace placeholder values with project-specific metadata. |
| `ENTRY_POINTS_MISSING` | warning | code | Framework-config-using project missing `entry-points.json` or empty `entryPoints` | Run `uip agent review --checks code`; pick `rule_id == "ENTRY_POINTS_MISSING"`. | Add `entry-points.json` declaring at least one entry point. |
| `UIPATH_IMPORT_INCORRECT` | error | code | `from uipath import UiPath` (correct: `from uipath.platform import UiPath`) | `Grep -n '^from uipath import UiPath\b' '*.py'`. Emit one finding per match. file = source file, line = match line. | Change to `from uipath.platform import UiPath`. |
| `RAW_LLM_CLIENT` | info | code | Import of a direct provider client that bypasses the UiPath LLM Gateway | Run `uip agent review --checks code`; pick `rule_id == "RAW_LLM_CLIENT"`. | Consider routing through `uipath-langchain` / `uipath-openai-agents` for UiPath auth, billing, audit, and tenant-policy enforcement. |
| `FRAMEWORK_DEP_MISSING` | error | code | Framework config file present but matching integration package absent from `[project] dependencies` | For each of `langgraph.json` / `llama_index.json` / `openai_agents.json` / `google_adk.json` / `pydantic_ai.json` / `agent_framework.json` that exists, Grep its required package (`uipath-langchain` / `uipath-llamaindex` / `uipath-openai-agents` / `uipath-google-adk` / `uipath-pydantic-ai` / `uipath-agent-framework`) in `pyproject.toml`. Emit one finding per missing dep, file = `pyproject.toml`. | Add the matching `uipath-*` package to `[project] dependencies`. |
| `OPENAI_AGENTS_NO_CLIENT_SETUP` | info | code | OpenAI Agents project without `set_default_openai_client` call (`OPENAI_AGENTS` only) | Run `uip agent review --checks code`; pick `rule_id == "OPENAI_AGENTS_NO_CLIENT_SETUP"`. | Call `set_default_openai_client(...)` to route through the UiPath LLM Gateway, or accept direct OpenAI routing as intended. |
| `OPENAI_AGENTS_UNSUPPORTED_FEATURE` | error | code | `interrupt`, `MemorySaver`, or `InvokeProcess` called in OpenAI Agents project (`OPENAI_AGENTS` only) | Run `uip agent review --checks code`; pick `rule_id == "OPENAI_AGENTS_UNSUPPORTED_FEATURE"`. | Remove the unsupported call — these are LangGraph-specific. |
| `LLAMAINDEX_SYNC_STEP` | error | code | `@step`-decorated method is not `async def` (`LLAMAINDEX` only) | Run `uip agent review --checks code`; pick `rule_id == "LLAMAINDEX_SYNC_STEP"`. | Add `async` to the step method. |
| `HARDCODED_ASSIGNEE_EMAIL` | warning | security | `assignee=Constant(str)` matching email pattern | Run `uip agent review --checks code`; pick `rule_id == "HARDCODED_ASSIGNEE_EMAIL"`. | Read the assignee from an asset, environment variable, or input parameter. |
| `BOOLEAN_GATE_FAIL_OPEN` | warning | security | `<expr>.get("<approval-keyword>", True)` defaults missing approval to True | Run `uip agent review --checks code`; pick `rule_id == "BOOLEAN_GATE_FAIL_OPEN"`. | Default to `False` for missing approval/permission keys. |
| `SIMPLE_FUNCTION_NO_ENTRYPOINT` | warning | code | Simple Function agent: `uipath.json` has no `"functions"` key (`FUNCTION` only) | Run `uip agent review --checks code`; pick `rule_id == "SIMPLE_FUNCTION_NO_ENTRYPOINT"`. | Add `"functions": [...]` to `uipath.json` listing exported functions. |
| `LANGGRAPH_NO_GRAPH_VAR` | error | code | `langgraph.json` declares `<file>:<symbol>` but `<file>` exports no top-level `<symbol>` (`LANGGRAPH` only) | Run `uip agent review --checks code`; pick `rule_id == "LANGGRAPH_NO_GRAPH_VAR"`. | Define `<symbol> = StateGraph(...).compile()` at module scope. |
| `LLAMAINDEX_NO_WORKFLOW_VAR` | error | code | `llama_index.json` declares `<file>:<symbol>` but `<file>` exports no top-level `<symbol>` (`LLAMAINDEX` only) | Run `uip agent review --checks code`; pick `rule_id == "LLAMAINDEX_NO_WORKFLOW_VAR"`. | Define `<symbol> = MyWorkflow()` at module scope. |
| `OPENAI_AGENTS_NO_AGENT_VAR` | error | code | `openai_agents.json` declares `<file>:<symbol>` but `<file>` exports no top-level `<symbol>` (`OPENAI_AGENTS` only) | Run `uip agent review --checks code`; pick `rule_id == "OPENAI_AGENTS_NO_AGENT_VAR"`. | Define `<symbol> = Agent(...)` at module scope. |
| `LANGGRAPH_GRAPH_NOT_COMPILED` | error | code | Top-level `graph = StateGraph(...)` without trailing `.compile()` (`LANGGRAPH` only) | Run `uip agent review --checks code`; pick `rule_id == "LANGGRAPH_GRAPH_NOT_COMPILED"`. | Chain `.compile()` onto the `StateGraph(...)` expression. |
| `OPENAI_AGENTS_NO_GENERIC_TYPE` | warning | code | `Agent(...)` constructed without `Agent[ContextModel](...)` subscript (`OPENAI_AGENTS` only) | Run `uip agent review --checks code`; pick `rule_id == "OPENAI_AGENTS_NO_GENERIC_TYPE"`. | Subscript `Agent` with a Pydantic context model. |
| `OPENAI_AGENTS_NO_OUTPUT_TYPE` | warning | code | `Agent(...)` without `output_type=` keyword (`OPENAI_AGENTS` only) | Run `uip agent review --checks code`; pick `rule_id == "OPENAI_AGENTS_NO_OUTPUT_TYPE"`. | Pass `output_type=<PydanticModel>` to `Agent(...)`. |
| `STATEGRAPH_MISSING_INPUT_OUTPUT` | warning | code | `StateGraph(...)` without explicit `input=`/`input_schema=` and `output=`/`output_schema=` kwargs (`LANGGRAPH` only) | Run `uip agent review --checks code`; pick `rule_id == "STATEGRAPH_MISSING_INPUT_OUTPUT"`. | Pass `input_schema=` and `output_schema=` to `StateGraph(...)`. |
| `MAIN_NOT_PYDANTIC_TYPED` | warning | code | Coded Function entrypoint `main()` lacks a schema-typed input or return annotation (`FUNCTION` only) | Run `uip agent review --checks code`; pick `rule_id == "MAIN_NOT_PYDANTIC_TYPED"`. | Annotate `main(input: <Model>) -> <Model>` with a Pydantic class or `@dataclass`. |
| `MAIN_DOCSTRING_MISSING` | info | code | Coded Function entrypoint has no docstring (`FUNCTION` only) | Run `uip agent review --checks code`; pick `rule_id == "MAIN_DOCSTRING_MISSING"`. | Add a docstring to `main()` — Studio Web reads it as the agent's catalog description. |
| `INPUT_FIELD_NO_DESCRIPTION` | warning | code | Pydantic model has ≥2 `Field(...)` calls AND >50% lack `description=` | Run `uip agent review --checks code`; pick `rule_id == "INPUT_FIELD_NO_DESCRIPTION"`. | Add `description=` to each `Field(...)`. |
| `MOCKABLE_DECORATOR_MISSING` | info | code | Top-level public function calls external services without `@mockable()` | Run `uip agent review --checks code`; pick `rule_id == "MOCKABLE_DECORATOR_MISSING"`. | Add `@mockable()` from `uipath.testing` so eval `mockingStrategy.type: 'mockito'` can intercept the call. |
| `DEPLOY_VENV_NOT_EXCLUDED` | warning | code | `.venv/` exists AND `uipath.json:packOptions.directoriesExcluded` doesn't list `.venv` | Run `uip agent review --checks code`; pick `rule_id == "DEPLOY_VENV_NOT_EXCLUDED"`. | Add `".venv"` to `uipath.json:packOptions.directoriesExcluded`. |
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
| `MISSING_AGENT_CONFIG` | error | general | None of the framework config files exist | `Glob` for `langgraph.json`, `llama_index.json`, `openai_agents.json`, `uipath.json`, `agent.json`, `project.uiproj`, `google_adk.json`, `pydantic_ai.json`, `agent_framework.json`. Emit when none match. file = project root. | Add the framework config file appropriate for this agent (e.g., `langgraph.json` for LangGraph). |
| `CODED_FRAMEWORK_FIT` | info | general | Framework chosen is a genuine mismatch for the task | Read source + framework config. Assess: is the framework appropriate? Real mismatches: LangGraph used for a deterministic pipeline with no branching; Simple Function used for a multi-step orchestrator that needs persistent state; LlamaIndex used for an agent with no retrieval. **Fire ONLY on real mismatch** — never as a commentary slot when the framework genuinely fits. file = framework config. | Switch to the framework that matches the task pattern. |
| `CODED_UIPATH_JSON_FIELD_DRIFT` | warning | general | `uipath.json` field demonstrably wrong (`entryPoint` mismatch, `isConversational` wrong, `includeUvLock: false`, …) | Read `uipath.json` + source. Assess per field: does the declared value contradict the actual code shape or break the runtime contract? `entryPoint: main.py:classify` when the function is `main`; `isConversational: true` on a stateless agent; `packOptions.includeUvLock: false` (deployment-blocker). Skip stylistic preferences. file = `uipath.json`, element = field name. | Correct the field to match the code reality. |
| `CODED_DOC_CODE_DRIFT` | info | general | README / docstring describes a feature the code doesn't implement | Read README + main docstrings. Assess: do they mention integrations, evaluators, or behaviors absent from source? Trust hazard for future contributors. Skip outdated inline comments inside functions (different concern) and "Future work" / "Roadmap" sections. file = README or docstring source. | Update the doc to match what the code actually does, or implement the documented feature. |
| `CODED_PROMPT_QUALITY` | warning | general | System prompt has internal contradictions, circular logic, or ambiguous instructions | Read any system prompt embedded in coded source (`UiPathChat`/`UiPathAzureChatOpenAI`, `Agent(instructions=...)`, `ChatPromptTemplate` strings). Assess: (a) internal contradictions ("Always respond in JSON" + "Write as a friendly paragraph"); (b) circular logic (rule X says "see Y", Y says "see X"); (c) ambiguous instructions two readers would interpret differently. DO NOT fire merely because the prompt is long. Bar: literal reading produces inconsistent behaviour. file = source file. | Reconcile contradictions, break circular references, or disambiguate. |
| `CODED_MULTI_AGENT_HUMANMESSAGE_NAME` | info | general | (coded_workflow only) Worker `HumanMessage(...)` returns lack `name="<worker_name>"` | Read worker functions in a multi-agent / supervisor setup. Assess: do they return `HumanMessage(content=..., name="<worker_name>")`? Without `name`, the supervisor cannot attribute responses. file = source file, element = worker name. | Add `name="<worker_name>"` to each worker's `HumanMessage(...)`. |
| `CODED_MULTI_AGENT_ROUTING_COHERENCE` | warning | general | (coded_workflow only) Supervisor routing description doesn't match each worker's actual capability | Read supervisor routing prompt + each worker's system prompt. Assess: does the routing description match what each worker actually does? "Researcher handles fact-finding" + worker actually generates code → routing will be unreliable. file = supervisor source. | Reconcile routing description with worker capabilities; or rename / repurpose workers. |
| `CODED_MULTI_AGENT_ERROR_HANDLING` | warning | general | (coded_workflow only) Multi-agent project lacks supervisor-level error handling | Read supervisor. Assess: project has ≥2 sub-agents (workers / handoffs) AND supervisor lacks fallback edges, try/except, or error states in routing logic. An unhandled worker exception terminates the entire graph. For single-agent error handling use `CODED_ERROR_HANDLING`. file = supervisor source. | Add fallback edges / try-except at the supervisor level. |
| `CODED_MULTI_AGENT_CROSS_SCHEMA` | warning | general | (coded_workflow only) `sdk.processes.invoke(...)` targeting a sibling agent has cross-schema mismatch | Read source. For each `sdk.processes.invoke()` targeting another agent in the same repo, read both the call's `input_arguments` and the target agent's declared input schema. Assess: are keys + types consistent? Emit per concrete mismatch. file = source file. | Reconcile `input_arguments` with the target agent's input schema. |
| `CODED_SUB_AGENT_PROMPT_DUPLICATION` | warning | general | (coded_workflow only) Two or more sub-agent prompts are substantively the same (paraphrase-equivalent) | Read each sub-agent's system prompt (`create_react_agent` workers, `Agent[Ctx]` instances). Assess pairwise: are any two prompts paraphrase-equivalent (not literal byte-match)? Routing becomes unreliable when worker capabilities are indistinguishable. file = source file, element = `<agent_a>,<agent_b>`. | Differentiate prompts so each worker has a distinct, scoped responsibility. |
| `CODED_GENERAL_ISSUE` | warning | general | General-category observation that no specific rule above fits | Use ONLY when no other category fits — repository hygiene (committed log files, missing .gitignore entries), documentation drift, project structure. Emit with concrete description + suggested fix. file = source of the observation. | (Defined per finding.) |

---

## SecurityChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `ENV_FILE_TRACKED` | error | security | Project is a git repo AND `git ls-files .env` returns non-empty | `Bash: git -C <project> ls-files .env`. Emit when stdout non-empty. file = `.env`. Skip silently when not a git repo. | Remove `.env` from git (`git rm --cached .env`) and add `.env` to `.gitignore`. Rotate any committed secrets. |
| `GITIGNORE_INCOMPLETE` | info | security | Project is a git repo AND `.gitignore` is missing any of: `.env`, `.venv/`, `__pycache__/`, `.uipath/` | Read `.gitignore`. Check each of the four entries. Emit one finding per missing entry. file = `.gitignore`. Skip silently when not a git repo. | Append the missing entry to `.gitignore`. |
| `TRACING_DATA_LEAK` | warning | security | `@traced(...)` on a function with secret-named params and no `hide_input=`/`input_processor=` (`FUNCTION` only) | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks security --output json`; pick `rule_id == "TRACING_DATA_LEAK"`. | Pass `hide_input=True` or `input_processor=...` to `@traced(...)`. |
| `CODED_PROMPT_USER_INPUT_UNSANITIZED` | warning | security | User-controlled input interpolated into LLM prompt without sanitization | Read source. Identify user-controlled fields (function params from `input.X`, request body, attachment content, conversational history). Assess per use: (a) does the field reach a prompt template via concatenation / f-string (`f"Classify this email: {input.email_body}"`)? AND (b) is no `prompt_injection` guardrail registered? AND (c) is no sanitization helper (allowlist match, length cap, `html.escape`, regex-strip) between input and prompt? file = source file. | Sanitize the input before interpolation, or register a `prompt_injection` guardrail. |
| `CODED_PII_IN_TRACES` | warning | security | `@traced()` on a function receiving PII-suggesting fields without redaction | Read `@traced`-decorated function signatures. Assess: do params have names suggesting PII (`email_body`, `customer_email`, `personal_*`, `*_ssn`, `customer_name`)? AND does the decorator lack `hide_input=True` / `input_processor=...`? Skip when the function only handles non-PII data (item IDs, timestamps). Emit per concrete case. file = source file, element = function name. | Pass `hide_input=True` or `input_processor=<redaction_fn>` to `@traced(...)`. |

---

## RuntimeQuirksChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `LIST_ACCUMULATOR_NOT_FORWARDED` | warning | runtime | LangGraph state class with `Annotated[list[...], operator.add]` reducer; a node returns that key without forwarding (`LANGGRAPH` only) | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks runtime --output json`; pick `rule_id == "LIST_ACCUMULATOR_NOT_FORWARDED"`. | Forward the accumulator: return `{"items": [*state.get("items", []), "new"]}` instead of `{"items": ["new"]}`. |
| `MEMORYSAVER_PRODUCTION` | info | runtime | `MemorySaver()` instantiated in a project with `uipath.json` or `langgraph.json` | Run `uip agent review --checks runtime`; pick `rule_id == "MEMORYSAVER_PRODUCTION"`. | Remove `MemorySaver()` — the `uipath-langchain` runtime injects a persistent checkpointer. |

---

## EvalResultsChecker

Auto-skips when no `evaluations/output.json` is present.

| rule_id | severity | category | trigger | detection_method | suggested_fix | status |
|---|---|---|---|---|---|---|
| `EVAL_RUN_NEVER_EXECUTED` | error | eval-results | `eval_count > 0` AND no `uipath eval` output JSON found | Use `eval_count` from common catalog. `Glob 'evaluations/output.json'`, `'evaluations/results.json'`, `'evaluations/runs/*.json'`. Emit when `eval_count > 0` AND zero matches. file = project root. | Run `uip agent eval` (low-code) or `uip codedagent eval ...` (coded) and commit the output JSON. | |
| `EVAL_RUN_REGRESSION` | error | eval-results | A deterministic evaluator scored <1.0 on a datapoint | Read `evaluations/output.json`. For each `(datapoint, evaluator)` cell where evaluator type matches `^uipath-(exact-match\|json-similarity\|contains\|tool-call.*\|correct-operator)$` AND score < 1.0 AND `details` does not carry an exception trace, emit one finding. file = `evaluations/output.json`, element = `<datapoint_id>:<evaluator_id>`. | Investigate the agent's output for the failing datapoint and fix the regression. | |
| `EVAL_RUN_BROKEN_EVALUATOR` | error | eval-results | Evaluator returned 0.0 across ALL datapoints AND its `details` carry an exception trace | For each evaluator, check whether every score is 0.0 AND every cell's `details` contains `HTTP 4`/`HTTP 5`/`EnrichedException`/`ConnectionError`/`Timeout`. Emit one finding per such evaluator. file = `evaluations/output.json`, element = evaluator id. | Fix the evaluator config or upstream LLM Gateway connectivity. | |
| `EVAL_RUN_LOW_PASS_RATE` | warning | eval-results | Average score across all `(datapoint × evaluator)` cells <0.70 | Read `evaluations/output.json`. Compute mean score across all cells. Emit when mean < 0.70. file = `evaluations/output.json`. | Diagnose why the agent fails — start with the lowest-scoring datapoints. | |
| `EVAL_RUN_JUDGE_DISAGREEMENT` | warning | eval-results | ≥2 LLM judges on the same datapoint, score range >0.5 | For each datapoint, collect scores from evaluators whose type substring-matches `LLMJudge` / `Trajectory` / `Faithfulness` / `ContextPrecision`. Emit when count ≥ 2 AND (max − min) > 0.5. file = `evaluations/output.json`, element = datapoint id. | Investigate which judge is correct — large disagreement usually means an ambiguous expected output or a weak judge prompt. | |
| `EVAL_RUN_OUTDATED` | error | eval-results | `evaluations/output.json` older than at least one source file | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks eval-results --output json`; pick `rule_id == "EVAL_RUN_OUTDATED"`. | Re-run `uip agent eval` / `uip codedagent eval` to refresh the output JSON. | |

---

## Constants

| Constant | Value | Used by |
|---|---|---|
| `MIN_EVAL_COUNT` | 5 | (via [common rules](agents-common-rules.md)) |
| `TARGET_EVAL_COUNT` | 30 | (via [common rules](agents-common-rules.md)) |
| `MAX_TOOLS_WARNING` | 20 | (via [common rules](agents-common-rules.md)) |
| `MAX_TOOLS_ERROR` | 30 | (via [common rules](agents-common-rules.md)) |

## What this catalog cannot do

The agent applies these rules from the project source as it is *checked into the repo*. It cannot:

- Verify runtime behavior (whether the LLM follows the prompt, picks the right tool, routes correctly).
- Verify multi-agent correctness at runtime — routing logic can look structurally sound and still produce wrong results.
- Verify external dependencies (process schemas, connection IDs, index names).
- Catch deep code logic bugs (field-name mismatches, arithmetic errors) — those are for linters and human code review.

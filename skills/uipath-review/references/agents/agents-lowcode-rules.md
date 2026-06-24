# Agents — Low-code Judgment Rule Catalog

Judgment rules for **low-code** agents (`agent.json`). Each rule requires the agent to read source and reason — what a regex/count/schema-walk cannot decide reliably. Same row schema as elsewhere — see [`../rule-format.md`](../rule-format.md).

> **This catalog is judgment-only.** Run `uip agent review "<PROJECT_DIR>" --output json` **first** (SKILL.md Step 2.5) — it returns the deterministic low-code findings (structural gates, schema-property presence, placeholder cross-refs, eval counts/diversity, version/runtime/location checks) in the same rule format. Then apply the rules below, which the CLI cannot do.

Read [`../rule-format.md`](../rule-format.md) and [`../rule-catalog-workflow.md`](../rule-catalog-workflow.md) first.

Companion file:

- [`agents-common-rules.md`](agents-common-rules.md) — judgment rule shared with coded agents (schema-description informativeness)

## Layouts

Low-code agents exist in two layouts. Detect first, then apply the right `Read` path in each rule.

| Layout | Identifier | Key files |
|---|---|---|
| **Normalized** | A single JSON file with snake_case top-level keys (`system_prompt`, `tools`, `datasets`, `input_schema`, `output_schema`, `user_prompt`) | The single JSON file |
| **Agent-builder** | `agent.json` at project root with camelCase keys + sibling `entry-points.json`, `project.uiproj`, `resources/<Name>/resource.json` | `agent.json`, `entry-points.json`, `resources/*/resource.json`, `evals/eval-sets/*.json`, `evals/evaluators/*.json` |

Rules tagged `(agent-builder only)` skip silently on the normalized layout; `(normalized only)` skip on agent-builder. Untagged rules apply to both with layout-aware `detection_method`.

## How to read this file

One H2 section per checker class (`EvalsChecker`, `SchemaChecker`, `ToolsChecker`, `GuardrailsChecker`, `GeneralChecker`) groups related rules for navigation. Every row's `detection_method` is the **judgment form**: read the named source, reason about it, emit when the criteria hold. Log the reasoning in the finding's `description`.

---

## EvalsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `LC_EVAL_GROUND_TRUTH_SWAPPED` | warning | evals | ≥2 eval datapoints share substantially overlapping input shape but disagree on `expectedOutput` (suggests label swap) | Read `evals/eval-sets/*.json`. For each pair of datapoints, compare `inputs` content overlap (e.g., `email_subject` + `email_body` substring overlap > 80%). Assess: when inputs are near-identical but expected outputs differ, this is a likely label swap (the *opposite* failure pattern from the deterministic duplicate-output check). Emit one finding per swapped pair, element = `<id_1>,<id_2>`. file = eval set JSON. | Inspect both datapoints; correct the swapped label, or split them into clearly distinct scenarios. |
| `LC_EVAL_JUDGE_FOR_CLOSED_CLASS` | warning | evals | LLM-judge evaluator applied to a closed-class output field | Read eval set's `evaluatorRefs`. Read agent's `outputSchema.properties`. Assess: if any output property has `.enum` (closed set) AND an evaluator referenced by the eval set is an LLM-judge (`evaluatorTypeId: "uipath-llm-judge-output-semantic-similarity"` or similar), the LLM judge is the wrong tool — `uipath-multiclass-classification` / `uipath-exact-match` gives 100% of the signal at zero variance. Emit one finding per (eval-set, judge-evaluator) pair. file = eval set JSON. | Replace the LLM-judge with `uipath-multiclass-classification` or `uipath-exact-match` for closed-class outputs. |

---

## SchemaChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `LC_OUTPUT_FORMAT_PROMPT_DRIFT` | warning | schema | System prompt instructs an output shape that conflicts with `outputSchema` | Read system prompt + `outputSchema`. Assess: does the prompt instruct a shape (`"respond with a single sentence"`, `"answer in markdown"`) that conflicts with the schema's structure (structured JSON, flat string, etc.)? Emit when prompt-vs-schema drift is present. file = system prompt source. | Align the prompt's output-format instructions with `outputSchema` — pick one source of truth and have the other reference it. |
| `LC_INPUT_SCHEMA_OVERLAP` | warning | schema | Input schema has ≥2 fields with semantically overlapping names or descriptions | Read `inputSchema.properties`. Assess: are there fields with semantically overlapping names (`query` vs `question` vs `text` vs `prompt` vs `input`) or descriptions? Emit when ≥2 fields could reasonably hold the same content and the LLM would have to disambiguate at runtime. file = schema source, element = `<field_a>,<field_b>`. | Merge overlapping fields, or differentiate them with clear names + descriptions that scope each one. |
| `LC_OUTPUT_ENUM_VS_PROMPT_DRIFT` | warning | schema | Output enum disagrees with the prompt's category list (either side has extras) | Read `outputSchema.properties.<X>.enum` and the system prompt's classification list (`"Classify into: A, B, C"`). Assess: do the two sets agree? Emit when either has extras: prompt names a class the schema doesn't accept (runtime validation rejects), OR schema accepts a class the prompt never mentions (LLM never produces it). file = schema or prompt source. | Reconcile the prompt's class list with `outputSchema.enum`. |
| `LC_OUTPUT_CLASSIFIER_NO_ENUM` | warning | schema | Classifier-shaped agent has no `enum` constraint on the primary output field | Read `outputSchema`. Assess: is this a classifier? Heuristic — `outputSchema` has a single primary string field whose name matches `class` / `classification` / `label` / `category` / `intent` / `decision`, OR the system prompt enumerates fewer than 10 categories. Emit when that field has no `enum`. file = schema source, element = field name. | Add `"enum": [...]` to the field — without it, the LLM produces free-form strings the runtime can't disambiguate. |

---

## ToolsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `VAGUE_TOOL_DESCRIPTION` | judgment | tools | Tool description missing or too vague for the LLM to choose the tool correctly | Walk tools (normalized: `.tools[]`; agent-builder: each `resources/*/resource.json` with `.type == "tool"`). Read each `.description`. Assess: does it state purpose, side effects, and when to use vs not use — enough that the model can pick this tool over its siblings? A blank description, or boilerplate like `"Process invoice"` that names no effect or selection cue, fires; a 2-3 sentence description covering purpose + effects + usage does not. (The crude `<20-char` length check runs in the review CLI; this rule judges sufficiency.) file = tool source, element = tool name. | Write a 2-3 sentence description covering purpose, side effects, and when to use vs not use the tool. |
| `LC_TOOL_MINIMALITY_SUFFICIENCY` | warning | tools | Tools exist that the prompt never names, OR the prompt describes responsibilities with no tool to fulfill them | Read tool list + system prompt. Assess two directions: (a) every configured tool maps to a clearly stated responsibility in the prompt; (b) every prompt-stated responsibility has at least one tool to fulfill it. Emit one finding per gap, with `description` naming the unmapped tool or unmet responsibility. file = system prompt source. | Either add the responsibility to the prompt (for orphan tools), add a tool (for orphan responsibilities), or remove the unused tool. |
| `LC_TOOL_OVERLAP` | warning | tools | Two or more tools have substantially similar descriptions or overlapping input schemas | Read all tool descriptions + `inputSchema`s. Assess pairwise: do any two tools have descriptions a user could plausibly apply to the same request, or input schemas that look interchangeable? Emit one finding per overlapping pair, element = `<tool_a>,<tool_b>`. file = tool source. | Differentiate the tools — sharpen descriptions to make selection unambiguous, or merge if truly redundant. |
| `LC_TOOL_DANGEROUS_COMBINATION` | warning | tools | Tool combination creates risk no individual tool creates alone (e.g., read tool + write tool with no guardrail) | Read full tool list. Assess pairwise / N-wise: do any combinations create capabilities none of the individual tools has alone? Classic example: a read tool (search, retrieve, query) + a write tool (send email, create record, call API) with no output guardrail = data-exfiltration path. Emit per dangerous combination. file = tool source, element = `<tool_a>,<tool_b>`. | Add a guardrail (e.g., output `pii_detection`, scope-restriction policy) that breaks the dangerous flow, or remove one tool. |
| `LC_TOOL_DELEGATION_DEPTH` | warning | tools | Tool with `type: "agent"` has no prompt guidance on when to delegate vs handle directly | Read tool resources. Identify any with `.type == "agent"`. Read system prompt. Assess: does the prompt include delegation criteria? Emit when missing. file = tool source, element = tool name. | Add delegation criteria to the system prompt: when to call the sub-agent vs handle the query directly. |
| `LC_TOOL_DESCRIPTION_MISLEADING` | info | tools | Tool description contradicts its declared `inputSchema` or `outputSchema` | For each tool, read `.description`, `.inputSchema`, `.outputSchema`. Assess: does the description claim behavior that contradicts the schemas (e.g., "returns the customer's full name" but `outputSchema` is `{type: "boolean"}`, or "takes a customer ID and email" but `inputSchema.properties` lists only `id`)? Emit per clear semantic mismatch (return type, field set, or arg count). file = tool source, element = tool name. | Reconcile the description with the actual schemas — pick the source of truth and update the other. |
| `LC_MULTI_TOOL_NO_SEQUENCING` | warning | tools | Tools with implicit ordering exist together but the prompt establishes no order | Read tool list. Identify canonical ordered pairs: `search*` + `summarize*`; `get*` + `create*`; `validate` + `submit`. Read system prompt. Assess: does the prompt establish ordering with words like `first`, `then`, `after`, or numbered steps? Emit when tools-with-implicit-order exist together but no ordering language appears. file = system prompt source. | Add numbered steps or sequencing language to the system prompt. |
| `LC_TOOL_RESPONSE_NOT_GROUNDED` | warning | tools | Agent has RAG-shaped retrieval but no grounding instruction in prompt or context resource | First confirm RAG shape: a tool whose output is unstructured prose intended to be cited, OR a Context Grounding index resource (`$resourceType: "context"` with `contextType: "index"`). Structured-record tools (`searchOrders`, `lookupCustomer`) do NOT trigger. When RAG-shaped, read system prompt AND every context resource's `description` / `query.description`. Assess: does grounding instruction (`"answer based only on retrieved content"` / `"cite the source"` / `"if no result, say I don't know"`) appear in either location? Emit when missing. file = system prompt or context resource. | Add a grounding instruction either to the system prompt or to the context resource's description. |

---

## GuardrailsChecker

> **Validator name authority.** Not all validators have the same documentation status. Use only names you are confident the target layout supports:
>
> **SDK-documented built-ins** (confirmed by `uipath-python` SDK docs):
>
> | Validator | When it's needed | Valid scope | Valid stage |
> |---|---|---|---|
> | `pii_detection` | Agent handles personal data (names, emails, addresses, health info) | Agent, Llm, Tool | Pre or Post |
> | `prompt_injection` | Agent accepts free-text user input | Llm only | PreExecution only |
>
> **Agent Builder platform-documented** (not in `uipath-python` public SDK docs):
>
> | Validator | When it's needed | Valid scope | Valid stage |
> |---|---|---|---|
> | `harmful_content` | Agent generates open-ended content | Agent, Llm, Tool | Pre or Post |
> | `intellectual_property` | Agent generates code or text | Agent, Llm only | PostExecution only |
> | `user_prompt_attacks` | User-facing agent, jailbreak risk | Llm only | PreExecution only |
>
> When recommending the three "platform-documented" types, do NOT cite them by name unless the specific validator is already present in the project's `guardrails` array or agent-builder schema. Instead say: *"Add an appropriate content-safety guardrail supported by this agent layout."*

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `LC_GUARDRAIL_PII_MISSING` | warning | guardrails | Agent processes personal data but has no `pii_detection` guardrail | Read `inputSchema`, `outputSchema`, system prompt. Assess: does the agent process personal data? Infer from field names + descriptions (names, emails, addresses, IDs, health info, financial info). When yes, check `.guardrails[]` for `pii_detection`. Emit when absent. file = `agent.json` (or normalized JSON). | Add a `pii_detection` guardrail (SDK-confirmed; cite by name). |
| `LC_GUARDRAIL_INJECTION_MISSING` | warning | guardrails | User-facing free-text input but no `prompt_injection` guardrail | Read `inputSchema`. Assess: does it have free-text string fields users can fill with arbitrary content? When yes, check guardrails for `prompt_injection`. Emit when absent. Do NOT recommend `user_prompt_attacks` by name unless already present in the project's config — see validator authority note above. file = `agent.json`. | Add a `prompt_injection` guardrail (SDK-confirmed) or an appropriate injection-protection guardrail supported by this agent layout. |
| `LC_GUARDRAIL_EVALS_CONSISTENCY` | judgment | guardrails | `enabledForEvals: true` may interfere with the eval set's intent | Read guardrails. For each with `enabledForEvals: true`, read the eval set. Assess: is the eval set testing guardrail behavior (intentional) or testing agent behavior (where guardrails may interfere)? Emit when intent unclear; reason in the description. file = guardrail source, element = guardrail name. | Set `enabledForEvals: false` for agent-behavior tests, or document that the eval set is specifically testing guardrail behavior. |

---

## GeneralChecker

Covers system-prompt quality, settings fit, no-flow failure modes, and prompt-vs-schema concerns that need reasoning.

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `LC_PROMPT_ROLE_DEFINITION` | warning | general | System prompt does not open with a clear role / persona statement | Read system prompt. Assess: does the opening paragraph state what the agent is and what it does? Emit when missing. file = system prompt source. | Add an opening sentence: `"You are an X that does Y."` |
| `LC_PROMPT_WHEN_GUIDANCE` | warning | general | Prompt explains tool capabilities but not when to use each tool | Read prompt + tool list. Assess per tool: does the prompt explain *when* to use it, not just *what* it does? `"Use SearchKB when the user asks a factual question about company policy"` is good; `"SearchKB: searches the knowledge base"` is not. Emit per tool lacking WHEN guidance. file = system prompt source, element = tool name. | For each tool, add a "use this when …" sentence to the prompt. |
| `LC_PROMPT_SCOPE_BOUNDARIES` | warning | general | Prompt does not explicitly state what the agent should NOT do | Read system prompt. Assess: does it contain explicit boundaries (`"Do not …"`, `"Only handle questions about X"`, `"If unsure, escalate"`)? Emit when absent. file = system prompt source. | Add a "Scope & Boundaries" section listing what is in and out of scope. |
| `LC_PROMPT_OUTPUT_FORMAT` | warning | general | `outputSchema` is structured but prompt has no output-format instruction | Read `outputSchema`. Read system prompt. Assess: if the schema has specific named fields (not just a string), does the prompt instruct the agent how to populate them? Emit when missing. file = system prompt source. | Add an "Output Format" section showing the expected structure (or a sample). |
| `LC_PROMPT_INSTRUCTION_CONFLICTS` | warning | general | Prompt contains internally contradictory instructions | Read system prompt. Assess: are there contradictions (`"Always respond in JSON"` alongside `"Write your response as a friendly paragraph"`)? Emit per contradiction. file = system prompt source. | Pick one instruction; remove or reconcile the other. |
| `LC_PROMPT_OVERSPECIFICATION` | info | general | Prompt is so specific about exact phrases that it will break on reasonable paraphrase | Read system prompt. Assess: does it handle dozens of exact phrases that paraphrase trivially? A 3-page prompt with 47 explicit phrases is brittle. file = system prompt source. | Generalize the prompt — describe categories of input rather than enumerating phrases. |
| `LC_PROMPT_STOPPING_CRITERIA` | warning | general | Prompt has no explicit stopping criteria for unresolvable cases | Read system prompt. Assess: is there a soft stop (`"If you cannot determine the answer after 3 attempts, respond with what you have"`)? Without one the agent relies entirely on `maxIterations`. Emit when missing. file = system prompt source. | Add an explicit stopping instruction for the "I cannot resolve this" case. |
| `LC_SETTINGS_MAXITERATIONS_FIT` | judgment | general | `maxIterations` value inconsistent with the agent's stated purpose | Read `.settings.maxIterations` + system prompt. Assess: a simple classifier rarely needs >3-5; a complex multi-tool research agent may need 20-30. Extreme values inconsistent with the agent's purpose are flagged. Emit with reasoning. file = `agent.json` or normalized source. | Adjust `maxIterations` to match the agent's actual loop complexity. |
| `LC_SETTINGS_TEMPERATURE_FIT` | judgment | general | `temperature` value inappropriate for task | Read `.settings.temperature` + system prompt. Assess: temperature 0 fits deterministic tasks (classification, extraction); non-zero on a classifier produces inconsistent labels. Emit with reasoning. file = `agent.json` or normalized source. | Set temperature to 0 for deterministic tasks; raise to 0.3-0.7 for conversational generation. |
| `LC_FAILURE_HALLUCINATE_ARGS` | warning | general | Tool `inputSchema` has required fields with no descriptions, and the LLM must guess values | Walk tools. For each, read required fields. Assess: are required fields self-explanatory, or do they need descriptions to be filled correctly? Emit when the LLM would have to guess valid values. file = tool source, element = `<tool_name>:<param>`. | Add `description` to each required parameter explaining valid values and format. |
| `LC_FAILURE_WRONG_TOOL` | warning | general | ≥2 tools have descriptions the LLM could reasonably apply to the same user request | Read all tool descriptions. Assess from a user's perspective: could any two be selected for the same request? Emit per ambiguous pair. file = tool source, element = `<tool_a>,<tool_b>`. | Sharpen descriptions to make tool selection unambiguous. |
| `LC_FAILURE_PROMPT_INJECTION` | warning | general | Tool-output injection risk OR system-prompt-as-injection (jailbreak fragments) | Two shapes, fire on either: (a) **Tool-output injection** — a tool returns user-controlled content re-inserted into context without sanitisation, and no `prompt_injection` guardrail is active. (b) **System-prompt-as-injection** — the system prompt itself attempts to override platform safety, contains DAN-style markers (`"ignore previous"`, `"no restrictions"`, `"do anything now"`), or instructs the model to behave as another assistant (`"As ChatGPT, …"`). file = source of risk. | (a) Add `prompt_injection` guardrail and/or sanitize tool output. (b) Rewrite the system prompt to remove adversarial markers. |
| `LC_FAILURE_IRREVERSIBLE_ACTION` | warning | general | Tools that create / delete / modify records exist alongside no escalation resource and no prompt confirmation requirement | Walk tools. Identify create/delete/modify capabilities. Read escalation resources + system prompt. Assess: is there an escalation path or prompt instruction to confirm before destructive actions? Emit when absent. file = tool source. | Add an escalation resource gating destructive actions, or add a confirmation requirement to the system prompt. |
| `LC_FAILURE_AUTHORITY_ESCALATION` | warning | general | Agent has admin-level tools but no prompt restriction on context of use | Walk tools. Identify admin-level capabilities (process invocation, queue manipulation, entity modification). Read system prompt. Assess: does the prompt restrict the context in which these are used? Emit when unrestricted. file = system prompt source. | Restrict admin-level tools in the system prompt to specific user roles / scenarios, or add a guardrail. |
| `LC_ESCALATION_OVERBROAD` | warning | general | Escalation description uses universal quantifiers without a narrowing condition | Read escalation resource `description`s (and channel `description`s). Assess: does it use universal quantifiers (`"always escalate"`, `"every classification"`, `"all responses"`, `"any output"`, `"regardless of intent"`) near the start AND lack a narrowing condition (`"if confidence < X"`, `"when classification is Uncertain"`, `"only for"`)? Emit when both hold. file = escalation source, element = escalation name. | Add a narrowing condition to the escalation description; if the intent really is to escalate everything, document why. |
| `LC_PROMPT_FEW_SHOT_MISSING` | warning | general | Structured `outputSchema` (≥3 fields, or ≥2 with nested) but system prompt has no concrete output example | Read `outputSchema` (count fields, check for nested). Read system prompt. Assess: when schema is rich (≥3 fields OR ≥2 with at least one nested), does the prompt include a concrete example (`Example: {…}`, an `Output format:` block with values, in-prompt sample)? 1-2 flat fields don't trigger. Emit when missing. file = system prompt source. | Add a concrete example output to the system prompt — few-shot lifts structured-output accuracy on rich schemas. |
| `LC_PROMPT_NEGATIVE_HEAVY` | warning | general | >50% of distinct prompt instructions are negative (`do not`, `never`, `avoid`, `must not`, `don't`) | Read system prompt. Tokenize into instructions (sentences, bullets). Assess: what fraction are negative? Emit when >50%. file = system prompt source. | Rewrite negative instructions as positive ones — LLMs follow `"always do X"` more reliably than `"never do not-X"`. |
| `LC_USER_PROMPT_BIASED_EXAMPLE` | warning | general | User-role message ends with an example output containing a specific concrete class value, unconditioned on input | Read user-role message. Assess (must hold all three): (1) contains `"Example of correct output:"` / `"Example output:"` / `"For example:"` / `"Sample output:"` (or similar header); (2) the example body is JSON-shaped with specific concrete values for classification fields (`"classification": "Accepted"`, `"intent": "approve"`); (3) the template doesn't condition the example on the input (`"for an acceptance email, …"`, `"if the user is asking about billing, …"`). When all three hold, the LLM treats the example's class as the de-facto answer for ambiguous inputs. file = user message source. | Either remove the example, move it to the **system** prompt as one of several balanced examples, or condition it on input shape. |

---

## What this catalog cannot do

The agent applies these rules from the project source as it is *checked into the repo*. It cannot:

- Verify the LLM actually follows the prompt at runtime — prompt quality is assessed; LLM compliance can only be confirmed by running the agent.
- Verify whether tool selection is correct at runtime — overlapping descriptions are flagged as risk; actual selection behavior requires running.
- Verify whether guardrails fire correctly — structural configuration is checked; whether the underlying service catches a given input is a runtime question.
- Validate live IDs (connection IDs, index names, recipient addresses) — these require API calls.

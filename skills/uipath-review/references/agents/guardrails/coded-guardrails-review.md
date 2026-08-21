# Coded Guardrail Review — LLM-as-judge (audit + recommend)

The read-only **review** counterpart of the `uipath-agents` coded guardrail recommend/validate capability. It powers the coded guardrail judgment rules in [`../agents-coded-rules.md`](../agents-coded-rules.md) §GuardrailsChecker. Run it during a **coded** agent review (SKILL.md Step 2.5b) **after** `uip codedagent review` <!-- uip-check-skip --> (Step 2.5a).

Modes:
- **Audit Mode:** judge existing, CLI-clean guardrails for effectiveness, appropriateness, and wiring; emit **defects**.
- **Recommend Mode:** identify missing guardrails for matched use cases; emit **Info recommendations**.

Review only: emit findings; never write or fix code and never run mutating `uip codedagent` commands. The user or `uipath-agents` skill applies findings.

## Scope boundary

The CLI owns deterministic checks and emits `CODED_GUARDRAIL_WRONG_IMPORT` (LangChain imports from `uipath.platform.guardrails`, not `uipath_langchain.guardrails`), `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS` (Tool-scope middleware lacks `tools=`), and `CODED_GUARDRAIL_INVALID_CONTRACT` (local `action=`/`validator=` does not subclass the SDK base). Judge only unflagged guardrails and code-undecidable questions: whether a valid action protects its scope, whether a valid guardrail belongs on the agent, whether a decorator wraps its target, and whether a needed guardrail is missing. Never re-describe a CLI finding. <!-- uip-check-skip -->

The review is **live-catalog driven**. Use catalog fields `when_to_use`, `use_cases`, `security_risk_addressed`, `when_not_to_use`, `security_category`, and `examples[].config`. When naming Python classes/enums, use SDK documentation from Step 0, never memory.

## Deterministic CLI fast path — completed deliverable before Step 0

Run `uip codedagent review`. If any `Data.Issues[]` entry has a `RuleId` starting with <!-- uip-check-skip --> `CODED_GUARDRAIL_`, immediately create or update the requested review report before any catalog, validator-list, SDK-documentation, package research, or general architecture analysis. Include:

1. the project and review scope;
2. the `uip codedagent review` command and `Data.Grade`; <!-- uip-check-skip -->
3. every emitted `CODED_GUARDRAIL_*` issue with `RuleId`, `Severity`, `Description`, `File`, and `SuggestedFix` copied verbatim; and
4. an explicit note that the CLI finding is authoritative and the flagged guardrail was excluded from judgment re-verification.

Do not re-verify, rename, reword, or supplement deterministic findings by fetching SDK documentation, installing or inspecting packages, or probing framework APIs. Exclude CLI-flagged guardrails from Step 0 class mapping and Audit Mode. Run Step 0 after saving the report only if source inspection identifies a separate unflagged guardrail or distinct missing-guardrail recommendation.

After saving the report, return it immediately and end the review turn. Continue only if the user's initial request explicitly asks for an exhaustive review or additional non-guardrail checks. Preserve deterministic fields verbatim if the report is later extended.

If the CLI emits no `Data.Issues[]`, do not invent a deterministic rule ID (`CODED_GUARDRAIL_WRONG_IMPORT`, `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS`, and `CODED_GUARDRAIL_INVALID_CONTRACT` are CLI-only); list the deterministic CLI rule as skipped. Judgment IDs remain valid: `CODED_GUARDRAIL_ACTION_INEFFECTIVE`, `CODED_GUARDRAIL_MISAPPLIED`, and `CODED_GUARDRAIL_RECOMMENDED`. Report a source-observed problem covered by neither source as rule-ID-less prose.

## Conclusive audit fast path — completed report checkpoint

When an existing, CLI-clean guardrail directly contradicts a catalog clause—its action is in the scope's invalid set (`CODED_GUARDRAIL_ACTION_INEFFECTIVE`) or the agent context matches a disqualifying `when_not_to_use` / `NOT_recommended_for` condition (`CODED_GUARDRAIL_MISAPPLIED`, Relevance):

1. run `uip codedagent review`; retain deterministic findings and `Data.Grade`;
2. read the entry `.py` per [Read the agent first](#read-the-agent-first), including the wired guardrail's class, scope, stage, action, and target;
3. fetch the catalog and tenant validator list once as specified in Step 0;
4. compare the guardrail and agent context (system prompt, schemas, and tool docstrings) with `when_not_to_use` / `NOT_recommended_for` and `examples[].config`; and
5. on a direct match, establish the finding and immediately save the requested report.

Retain CLI findings and grade derivation. Include the finding's source location and identifiers, matched catalog clause, configured scope/action, and catalog-supported fix. End the review turn unless the initial request explicitly asks for exhaustive or additional non-guardrail checks. Do not fetch SDK documentation sites, read installed package sources (`site-packages/…`), probe framework APIs (`inspect.getsource` / signature checks), import or execute project or scratch agents, re-run the review CLI or catalog, or perform general architecture analysis. A plausible concern is insufficient; require a direct source-to-catalog contradiction.

## Missing-guardrail fast path — completed deliverable

When the entry source clearly matches a catalog use case and no matching middleware or `@guardrail` is wired:

1. run `uip codedagent review`; retain deterministic findings and `Data.Grade`;
2. read the entry `.py` per [Read the agent first](#read-the-agent-first);
3. fetch the catalog and tenant validator list once as specified in Step 0;
4. establish `CODED_GUARDRAIL_RECOMMENDED` using Recommend Mode steps 2–5, phrasing scope and action in catalog vocabulary (Agent / Llm / Tool · PRE / POST · block / escalate / log). SDK docs are not required unless the report names concrete Python classes not visible in source; and
5. immediately save the report with rule ID exactly `CODED_GUARDRAIL_RECOMMENDED`, the exact source-evidence clause (schema property names, prompt line, or tool docstring), and recommended scope/action.

After saving, end the review turn. Do not perform the fast path's catalog, SDK-doc, dependency, framework-API, execution, repeated-CLI, or architecture detours. Continue only for an explicitly exhaustive or additional non-guardrail request.

If the catalog fetch fails, retain `CODED_GUARDRAIL_RECOMMENDED` as the valid judgment-catalog ID, use generic scope/action wording, and note `catalog-limited`.

## Step 0 — Fetch Catalog, Available Validators, and SDK Docs

Run this once when there is an **unflagged** wired guardrail—any `*UiPath…Middleware(...)` in `create_agent(middleware=[...])` or any `@guardrail(...)` decorator—or when the agent matches a catalog use case for a distinct missing-guardrail recommendation. A CLI-flagged guardrail alone does not trigger Step 0. <!-- uip-check-skip -->

### Catalog (cacheable—30-minute TTL)

Run:

```bash
python3 -c "
import os, time
cache = '.guardrails-catalog-cache.json'
if os.path.exists(cache) and (time.time() - os.path.getmtime(cache)) < 1800:
    print('CACHE_HIT')
else:
    print('CACHE_MISS')
"
```

On **CACHE_HIT**, read `.guardrails-catalog-cache.json`. On **CACHE_MISS**, run `uip agent guardrails catalog --output json > .guardrails-catalog-cache.json`; the CLI writes success and error JSON to stdout, so do not add `2>&1`.

### Guardrails list (never cached—tenant-specific)

Run:

```bash
uip agent guardrails list --output json
```

Build `{ validatorId: status }` from the `Data` array and use only `Status == "Available"`.

`Validator` is not unique: key on `(Validator, IsByo)`, not `Validator` alone. For BYOG entries sharing a validator name, match a BYO construct to `IsByo: true` by its tenant-unique `ByoValidatorName` (the code passes no connection id), then read `Parameters`/scopes. A BYO entry with `Status: "Disabled"` is an administrative configuration switch, not a wiring/import defect; if targeted, treat it like `Unauthorised` and state that it cannot protect.

### SDK docs—only for required Python names

Fetch SDK docs only when a finding must map `validator_id` to a Python class and the class is not visible in source. The catalog and validator list are the verdict sources; SDK docs only translate names. Source-visible class names may be cited as observed wiring, while structural validity is the CLI's responsibility (`CODED_GUARDRAIL_WRONG_IMPORT` / `CODED_GUARDRAIL_INVALID_CONTRACT`). Prescribed classes must come from documentation.

For all agents, fetch with `WebFetch`:

- `https://uipath.github.io/uipath-python/core/guardrails/` — validators, entity enums, `GuardrailScope` / `GuardrailExecutionStage`, and action classes.
- For LangChain/LangGraph agents (`uipath-langchain` in `pyproject.toml` or `from langchain…` / `from langgraph…` imports), fetch `https://uipath.github.io/uipath-python/langchain/guardrails/` — middleware, supported scopes/stages, and `uipath_langchain.guardrails` imports.

Build `{ validator_id → { middleware_class, validator_class, entity_enum, allowed_scopes, allowed_stages, import_path } }` by joining catalog entries with documented SDK names. Use documentation as the sole source for class, enum, scope, stage, and import names.

If `WebFetch` is unavailable or denied, stop at the first successful fallback:

1. run `curl -fsSL <URL>` via Bash for the same two URLs;
2. locate installed SDKs with `python3 -c "import uipath; print(uipath.__file__)"` and the equivalent command for `uipath_langchain`, then read only `uipath/platform/guardrails/` and `uipath_langchain/guardrails/` for middleware, validator, action, scope, stage, and entity-enum names;
3. if neither works, use the SDK-docs skip path below.

Do not install or download dependencies, inspect unrelated framework APIs, or search package internals beyond those documented fallback modules.

### Unavailable catalog or SDK docs

If the catalog is unavailable, skip catalog-dependent Audit Mode (`CODED_GUARDRAIL_ACTION_INEFFECTIVE` and the relevance half of `CODED_GUARDRAIL_MISAPPLIED`) under the report's `Rules Skipped` subsection with reason `"guardrails catalog unavailable"`. The wiring half of `CODED_GUARDRAIL_MISAPPLIED` remains code-only. Recommend Mode may still detect missing guardrails from prompt/schema/tool evidence; use generic scope/action wording and note `catalog-limited`.

If all SDK-doc fallbacks fail, record mapping-dependent checks—scope/stage validity, import paths, and class names—under `Rules Skipped` with reason `"SDK docs unavailable"`. Catalog-only checks still run.

## Read the agent first

Resolve and read the entry `.py`: use the `langgraph.json` `graphs` value's file, otherwise `main.py`. Read:

- the system prompt;
- input/output schemas (`Pydantic BaseModel` / function signatures);
- `@tool` names, docstrings, and signatures;
- `*UiPath…Middleware(...)` in `create_agent(middleware=[...])` and `@guardrail(...)` decorators, including each target: `@tool`, an LLM factory `def create_llm(): return UiPathChat(...)`, an agent factory, or another target.

## Audit Mode — existing guardrails

For each wired guardrail not flagged by the CLI, run these checks.

### Actionability Check → `CODED_GUARDRAIL_ACTION_INEFFECTIVE`

Compare the action class with the catalog's `when_not_to_use` and representative `examples[].config` action for the chosen scope. Emit when the action is ineffective or counterproductive, including:

- a security-critical `adversarial_input` or `content_safety` guardrail using `LogAction` where the catalog uses block;
- `pii_detection` using `BlockAction` or filtering at Tool scope where the tool legitimately needs PII;
- `pii_detection` using `LogAction` at Agent / Llm scope, where logging does not prevent PII from entering or reaching the LLM.

Name the catalog-recommended action for that scope. Use severity `judgment`; a security gap or broken agent may be Critical, otherwise use Warning/Info by impact. The source plus catalog is conclusive. Do not import or execute project dependencies, inspect `uipath_langchain` / `langchain` sources, fetch SDK documentation sites, or run agent factories to prove ineffectiveness.

### Relevance + Wiring Check → `CODED_GUARDRAIL_MISAPPLIED`

Emit for either:

- **Relevance:** the system prompt, schemas, or tool docstrings match a disqualifying catalog `when_not_to_use` / `NOT_recommended_for` condition; cite the matched clause.
- **Wiring:** an LLM- or Agent-scope `@guardrail` decorates a plain helper, non-factory, or module-level value instead of a function returning `UiPathChat(...)` or `create_agent(...)`, so it will not wrap the intended target.

This wiring check is distinct from CLI `CODED_GUARDRAIL_WRONG_IMPORT`, `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS`, and `CODED_GUARDRAIL_INVALID_CONTRACT`; do not re-flag those.

## Recommend Mode — missing guardrails

Reuse catalog-driven recommend reasoning, but emit findings instead of writing code. Emit one Info finding per missing guardrail with rule ID `CODED_GUARDRAIL_RECOMMENDED`:

1. Read the system prompt, schemas, `@tool` docstrings, and existing guardrails.
2. For each catalog entry, compare `when_to_use`, `use_cases`, `description`, and `security_risk_addressed` with the agent's purpose, data, and threat model. Read `when_not_to_use` and skip disqualified matches. Recommend only `Available` validators; mention `Unauthorised` ones and skip validators absent from the list.
3. De-duplicate by `security_category` + scope + stage; drop catalog-deprecated entries, keep the best fit, and mention alternatives.
4. Recommend the outermost permitted PRE scope for input protection (Agent > Llm > Tool), Agent · POST for output protection, and Tool only for genuinely tool-specific concerns. Use coded vocabulary: Agent → `GuardrailScope.AGENT` middleware or `@guardrail` on the agent factory; Llm → `GuardrailScope.LLM` or `@guardrail` on the LLM factory; Tool → `GuardrailScope.TOOL` with `tools=[…]` or `@guardrail` on the `@tool`.
5. Use the catalog example's `action_type`. State **block / escalate** as protection needed and **log** as audit only; never silently downgrade block to log.

Each finding must state the guardrail or `security_category`, matched use case/data flow, recommended scope, and action plus its protection-vs-audit signal. Do not name `harmful_content`, `intellectual_property`, or `user_prompt_attacks` unless already present in code. `pii_detection` and `prompt_injection` may be named when SDK-confirmed; otherwise phrase generically.

## Report

Merge findings into the Step 5 Critical / Warning / Info tables (SKILL.md Step 2.5b), one row per finding:

```text
| <id> | `<rule_id>` | `<file>`: <message>. <suggested_fix>. |
```

Recommendations (`CODED_GUARDRAIL_RECOMMENDED`) use `I-D-` Info IDs. Defects (`CODED_GUARDRAIL_ACTION_INEFFECTIVE`, `CODED_GUARDRAIL_MISAPPLIED`) use the `judgment` band and Critical/Warning/Info according to impact. Set `file` to the entry `.py` and `element` to the guardrail name. If a deterministic checkpoint exists, update that same file into the complete Step 5 report without dropping or paraphrasing checkpointed CLI findings.

## Critical Rules

1. **Checkpoint deterministic findings first:** before Step 0 or research, write every CLI-emitted `CODED_GUARDRAIL_*` issue verbatim into the requested report, then update that same report to the complete Step 5 form.
2. Run after `uip codedagent review` (Step 2.5a) and judge only unflagged guardrails; never double-flag `CODED_GUARDRAIL_WRONG_IMPORT`, `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS`, or `CODED_GUARDRAIL_INVALID_CONTRACT`. <!-- uip-check-skip -->
3. Be catalog-driven: cite `when_not_to_use`, `when_to_use` / `use_cases`, and `examples[].config.action_type`; use SDK docs, never memory, for Python classes/enums/imports absent from source.
4. If the catalog is unavailable, defer catalog-dependent Audit Mode under `Rules Skipped`; retain source-only Recommend Mode and code-only wiring checks. Never guess.
5. Use one Info rule, `CODED_GUARDRAIL_RECOMMENDED`, per missing guardrail; distinguish **block/escalate** protection from **log** audit.
6. Never silently downgrade block → log. A security-critical guardrail at `log` is `CODED_GUARDRAIL_ACTION_INEFFECTIVE` unless the catalog or agent gives a stated reason.
7. Do not name `harmful_content`, `intellectual_property`, or `user_prompt_attacks` unless already present; `pii_detection` / `prompt_injection` may be named.
8. Review only: emit findings; never write guardrails, edit the entry `.py`, or run mutating `uip codedagent` commands.
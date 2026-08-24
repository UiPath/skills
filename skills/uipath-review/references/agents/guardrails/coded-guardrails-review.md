# Coded Guardrail Review — LLM-as-judge (audit + recommend)

The read-only **review** counterpart of the `uipath-agents` coded guardrail recommend/validate capability. It
powers the coded guardrail judgment rules in [`../agents-coded-rules.md`](../agents-coded-rules.md)
§GuardrailsChecker. Run it during a **coded** agent review (SKILL.md Step 2.5b) **after** `uip codedagent review` <!-- uip-check-skip -->
(Step 2.5a). Two modes:

- **Audit Mode** — the agent already wires guardrails → are they *effective, appropriate, and actually wired*?
  (emits **defects**)
- **Recommend Mode** — the agent is missing guardrails for use cases it matches → which should it add? (emits
  **Info recommendations**)

This is **review only** — never write, fix, or run `uip codedagent` mutating commands. The reviewer emits
findings; the user (or the `uipath-agents` skill) applies them.

> **Boundary with `uip codedagent review` — do not double-flag.** <!-- uip-check-skip --> The review CLI owns every **deterministic**
> coded guardrail check and emits them as rule IDs: `CODED_GUARDRAIL_WRONG_IMPORT` (LangChain agent imports
> guardrails from `uipath.platform.guardrails` and never from `uipath_langchain.guardrails`, so the adapter never
> registers and the guardrail silently no-ops), `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS` (a Tool-scope middleware with
> no `tools=`), and `CODED_GUARDRAIL_INVALID_CONTRACT` (a local custom `action=`/`validator=` that doesn't subclass
> the SDK base). The rules here fire **only on guardrails the CLI did not flag**, and judge only what code cannot
> decide: whether a valid action actually protects at its scope, whether a valid guardrail belongs on this agent at
> all, whether a decorator is wired where it will actually wrap the target, and whether a guardrail the agent should
> have is missing. Never re-describe a CLI deterministic finding here.

## Deterministic CLI fast path — completed deliverable before Step 0

If `uip codedagent review` returns any `Data.Issues[]` entry whose `RuleId` starts with <!-- uip-check-skip -->
`CODED_GUARDRAIL_`, **immediately create or update the requested review report before any catalog, validator-list,
SDK-documentation, package research, or general architecture analysis**. This report is the completed deliverable
for the deterministic guardrail path, not an in-progress checkpoint, and
contains at minimum:

1. the project and review scope;
2. the `uip codedagent review` command and `Data.Grade`; <!-- uip-check-skip -->
3. every emitted `CODED_GUARDRAIL_*` issue with its `RuleId`, `Severity`, `Description`, `File`, and `SuggestedFix`
   copied verbatim; and
4. an explicit note that the CLI finding is authoritative and the flagged guardrail was excluded from judgment
   re-verification.

The CLI description and suggested fix are authoritative. Do not re-verify, rename, reword, or supplement a
deterministic finding by fetching SDK documentation, installing or inspecting packages, or probing framework APIs.
Exclude every CLI-flagged guardrail from Step 0 class mapping and Audit Mode. Step 0 may still run **after the
report** only when source inspection has already identified a separate unflagged guardrail or distinct missing-
guardrail recommendation.

After saving this report, **return it immediately and end the current review turn**. Do not continue into catalog,
validator-list, SDK-doc, dependency, general checklist, or architecture work merely to make the report broader.
Continue beyond the deterministic report only when the user's initial request explicitly asks for an exhaustive
review or names additional non-guardrail checks. Preserve the deterministic fields verbatim if a later request
extends the report.

If the CLI does not emit `Data.Issues[]`, do not invent a substitute **deterministic** rule ID
(`CODED_GUARDRAIL_WRONG_IMPORT` / `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS` / `CODED_GUARDRAIL_INVALID_CONTRACT` are
CLI-only) and list the deterministic CLI rule as skipped. The judgment rule IDs — `CODED_GUARDRAIL_ACTION_INEFFECTIVE`,
`CODED_GUARDRAIL_MISAPPLIED`, `CODED_GUARDRAIL_RECOMMENDED` — come from `agents-coded-rules.md` and stay valid via the
judgment paths below. A source-observed problem covered by neither source is reported as rule-ID-less prose.

Like the recommend capability, this is **live-catalog driven** — the catalog's authored fields (`when_to_use`,
`use_cases`, `security_risk_addressed`, `when_not_to_use`, `security_category`, `examples[].config`) drive every
decision. When a finding names Python classes/enums, that vocabulary comes from the SDK docs (Step 0), never memory.
Do not hardcode which guardrail fits which agent, or which Python class implements which validator.

## Conclusive audit fast path — completed report checkpoint

When an existing, CLI-clean guardrail conclusively contradicts a catalog clause — its action is in the scope's
invalid set (→ `CODED_GUARDRAIL_ACTION_INEFFECTIVE`) or the agent's own context matches a disqualifying
`when_not_to_use` / `NOT_recommended_for` condition (→ `CODED_GUARDRAIL_MISAPPLIED`, Relevance) — use this bounded
sequence **before** general manual review:

1. run `uip codedagent review`; retain its deterministic findings and `Data.Grade`;
2. read the entry `.py` per [Read the agent first](#read-the-agent-first) — the wired guardrail's class, scope,
   stage, action, and target are all visible in that source; no SDK-doc mapping is needed;
3. fetch the catalog and tenant validator list once, as specified in Step 0;
4. compare the wired guardrail and the agent's context (system prompt, schemas, tool docstrings) against the
   catalog entry's `when_not_to_use` / `NOT_recommended_for` and `examples[].config`; and
5. on a direct match, establish the finding and immediately save the requested report.

The saved report is a completed checkpoint, not working notes: retained CLI findings, grade derivation, and the
finding with the guardrail's source location and identifiers, matched catalog clause, configured scope/action, and
catalog-supported fix. Then **end the current review turn** unless the user's initial request explicitly asks for
an exhaustive review or names additional non-guardrail checks. Do not delay the checkpoint to fetch SDK
documentation sites, read installed package sources (`site-packages/…`), probe framework APIs (`inspect.getsource`
/ signature checks), import or execute the project or scratch agents, re-run the review CLI or catalog, or do
general architecture analysis — none of that adds admissible evidence to a catalog-clause verdict.

This fast path requires a direct source-to-catalog contradiction, not a plausible concern. Canonical example: a
synthetic-data generator whose system prompt states it never receives real customer data carries a `pii_detection`
guardrail on its LLM factory — the catalog's `when_not_to_use` disqualifies PII detection where generated PII is
the intended product. If the clause does not directly match, continue normal Audit Mode.

## Missing-guardrail fast path — completed deliverable

When the entry source clearly matches a catalog use case and no matching guardrail is wired (no middleware, no
`@guardrail`), use this bounded sequence:

1. run `uip codedagent review`; retain its deterministic findings and `Data.Grade`;
2. read the entry `.py` per [Read the agent first](#read-the-agent-first);
3. fetch the catalog and tenant validator list once, as specified in Step 0;
4. establish `CODED_GUARDRAIL_RECOMMENDED` per Recommend Mode steps 2–5, phrasing scope and action in catalog
   vocabulary (Agent / Llm / Tool · PRE / POST · block / escalate / log). SDK docs are NOT required — fetch them
   only if the report names concrete Python classes not already visible in the source; and
5. immediately save the requested report with the rule ID exactly `CODED_GUARDRAIL_RECOMMENDED`, the exact
   source-evidence clause (schema property names, prompt line, tool docstring), and the recommended scope/action,
   then return it.

The saved report is the completed deliverable for this guardrail path. After saving it, **end the current review
turn**. Same detour denylist as the conclusive audit fast path. Continue beyond it only when the user's initial
request explicitly asks for an exhaustive review or names additional non-guardrail checks.

If the catalog fetch itself fails, `CODED_GUARDRAIL_RECOMMENDED` stays the correct, valid rule ID (a
judgment-catalog ID from `agents-coded-rules.md`, not a CLI ID) — use generic scope/action wording and note
"catalog-limited" in the message.

---

## Step 0 — Fetch Catalog, Available Validators, and SDK Docs

Run this once when the coded agent has at least one **unflagged** wired guardrail to audit (any
`*UiPath…Middleware(...)` inside `create_agent(middleware=[...])` or any `@guardrail(...)` decorator) **or** the
agent matches a catalog use case for a distinct missing-guardrail recommendation. A guardrail already flagged by
`uip codedagent review` does not, by itself, trigger Step 0. <!-- uip-check-skip --> This is the read-only review counterpart of the
guardrail recommend capability — it runs the same Step 0 fetches (specified in full below) but emits findings
instead of writing code.

### Catalog (cacheable — 30-minute TTL)

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

- **CACHE_HIT**: read `.guardrails-catalog-cache.json` directly.
- **CACHE_MISS**: fetch and save: `uip agent guardrails catalog --output json > .guardrails-catalog-cache.json`
  (the CLI writes both success and error JSON to stdout — do not add `2>&1`).

### Guardrails List (NEVER cached — tenant-specific)

```bash
uip agent guardrails list --output json
```

Build a `{ validatorId: status }` lookup from the `Data` array (use only `Status == "Available"`).

> **`Validator` is not unique — key on `(Validator, IsByo)`, not `Validator` alone.** A tenant with a bring-your-own (BYOG) configuration for a validator has two entries sharing the same `Validator` name — one built-in, one BYO (`IsByo: true`). If the code wires a BYO validator construct, match it against the `IsByo: true` entry (by its `ByoValidatorName` — tenant-unique; the code passes no connection id), not the built-in one, before reading `Parameters`/scopes. See [uipath-agents coded guardrails.md § BYO (bring-your-own) validators](/uipath:uipath-agents).

### SDK Docs (only when a finding must name Python classes)

Fetch SDK docs **only when** a finding's message must map `validator_id` ↔ Python class and the class is not
already visible in the agent source. The catalog and validator list speak `validator_id` only and carry no Python
class names — the SDK docs are the sole translation table between the two vocabularies, not a second verdict
authority. A source-visible class name may be cited as the **observed wiring** (its structural validity — real
class, correct module, valid contract — is the deterministic CLI's job: `CODED_GUARDRAIL_WRONG_IMPORT` /
`CODED_GUARDRAIL_INVALID_CONTRACT`); any class the report **prescribes** comes from the SDK docs, never memory.
Relevance verdicts and generically-phrased recommendations need no mapping — skip this subsection for them. When
the mapping IS needed, fetch via `WebFetch`:

- `https://uipath.github.io/uipath-python/core/guardrails/` — validators, entity enums, `GuardrailScope` /
  `GuardrailExecutionStage`, action classes.
- `https://uipath.github.io/uipath-python/langchain/guardrails/` — when the agent is LangChain/LangGraph
  (`uipath-langchain` in `pyproject.toml` or `from langchain…` / `from langgraph…` imports): middleware classes,
  their supported scopes/stages, and the `uipath_langchain.guardrails` import paths.

Build a `{ validator_id → { middleware_class, validator_class, entity_enum, allowed_scopes, allowed_stages,
import_path } }` lookup by joining catalog entries with the SDK class names. Use the fetched content as the sole
source of truth for class/enum/import names — never memory.

**If `WebFetch` is unavailable or denied**, fall back in order; stop at the first source that yields the
class/scope/enum names:

1. `curl -fsSL <URL>` via Bash (same two URLs).
2. Read the installed SDK sources. Locate the packages
   (`python3 -c "import uipath; print(uipath.__file__)"`, same for `uipath_langchain`) and read the guardrail
   modules (`uipath/platform/guardrails/`, `uipath_langchain/guardrails/`) for middleware/validator/action classes,
   scopes, stages, and entity enums.
3. Neither reachable → SDK-docs skip path in the next section.

Stop at the first successful documentation source. Guardrail review must not install or download dependencies,
inspect unrelated framework APIs, or search package internals beyond the documented fallback modules above.

### If the catalog (or SDK docs) is unavailable

Do **not** guess:
- **Audit Mode** (`CODED_GUARDRAIL_ACTION_INEFFECTIVE`, `CODED_GUARDRAIL_MISAPPLIED` relevance check) depends on the
  catalog → record these under the report's "Rules Skipped" subsection with reason
  `"guardrails catalog unavailable"`. (The **wiring** half of `CODED_GUARDRAIL_MISAPPLIED` — a decorator that won't
  wrap its target — is code-only and still applies.)
- **Recommend Mode** (`CODED_GUARDRAIL_RECOMMENDED`) can still detect a missing guardrail from the entry source
  alone (prompt / schema / tool inference); phrase the recommended scope/action generically and note
  "catalog-limited" in the message.
- **SDK docs unreachable by every fallback** (WebFetch, curl, installed sources) → the
  `validator_id ↔ Python class` mapping is unverified. Checks that need only the catalog still run; record
  mapping-dependent checks (scope/stage validity, import paths, class names) under "Rules Skipped" with reason
  `"SDK docs unavailable"`.

---

## Read the agent first

Resolve the entry `.py` (the `langgraph.json` `graphs` value's file, else `main.py`) and read:
- **System prompt** — what the agent does, its domain and behaviors.
- **Input / output schemas** (Pydantic `BaseModel` / function signatures) — the data it receives and produces.
- **`@tool` functions** — name, docstring, signature (the targets of Tool-scope guardrails).
- **Wired guardrails** — `*UiPath…Middleware(...)` inside `create_agent(middleware=[...])` and `@guardrail(...)`
  decorators, plus what each decorates (a `@tool`, an LLM factory `def create_llm(): return UiPathChat(...)`, an
  agent factory, or something else).

---

## Audit Mode — existing guardrails (findings are defects)

For each wired guardrail the review CLI did **not** flag, run the checks below.

> **A BYO-backed guardrail's tenant entry showing `Status: "Disabled"` is a configuration switch, not a wiring bug.** It means the tenant admin turned that specific BYOG configuration off (Admin → AI Trust Layer → Guardrails Configurations) — don't re-diagnose the code as a wiring/import defect. If the wired guardrail targets that disabled configuration, it can't protect; treat it like targeting an `Unauthorised` validator and note it in the report.

### Actionability Check → `CODED_GUARDRAIL_ACTION_INEFFECTIVE`

Compare the guardrail's action class against the catalog entry's `when_not_to_use` and its representative
`examples[].config` action for the chosen scope. Emit when the action is ineffective/counterproductive. Canonical
cases:

- A **security-critical** guardrail (`security_category` `adversarial_input` / `content_safety`) using
  `LogAction` where the catalog example uses block — it looks protected but isn't.
- `pii_detection` with `BlockAction` / a filtering action at **Tool** scope on a tool that legitimately needs the
  PII (e.g. a SendEmail tool needs the recipient address) — blocking breaks the tool.
- `pii_detection` with `LogAction` at **Agent** / **Llm** scope — log there does not prevent PII from entering or
  reaching the LLM.

Name the catalog-recommended action for that scope in the description. Severity `judgment` — a guardrail that breaks
the agent or leaves a security gap can be Critical; a milder ineffectiveness is Warning/Info.

**The catalog verdict IS the evidence — do not verify SDK behavior empirically.** Source read + catalog comparison
fully decides this check. Do NOT import or execute the project's dependencies, inspect `uipath_langchain` /
`langchain` package sources, fetch SDK documentation sites, or run the agent's factory code to "prove" an action is
ineffective — that forensic detour adds no admissible evidence to the finding and routinely burns the entire review
budget. Once the configured action diverges from the catalog's recommendation for that scope, write the finding and
move on to the report (the report file is the deliverable; an unwritten report scores zero regardless of analysis
depth).

### Relevance + Wiring Check → `CODED_GUARDRAIL_MISAPPLIED`

Two ways a format-valid guardrail can be misapplied:

- **Relevance** — establish the agent's real context (system prompt, schemas, tool docstrings); read the catalog
  entry's `when_not_to_use` / `NOT_recommended_for`; emit when the agent matches a disqualifying condition (e.g. a
  generate-only agent with no user input carrying a PII guardrail — the PII output is the intended product). Cite
  the matched clause.
- **Wiring** — a `@guardrail` decorator at LLM or Agent scope only wraps its target if the decorated function
  returns `UiPathChat(...)` (LLM factory) or `create_agent(...)` (agent factory). A decorator on a plain helper, a
  non-factory, or a module-level value silently no-ops at runtime. Emit when the decorated target won't be wrapped
  as intended. (This is the non-deterministic placement case; the CLI's `CODED_GUARDRAIL_WRONG_IMPORT` /
  `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS` / `CODED_GUARDRAIL_INVALID_CONTRACT` are separate — do not re-flag them.)

---

## Recommend Mode — missing guardrails (findings are Info recommendations)

Reuse the `uipath-agents` recommend capability's catalog-driven reasoning, but emit findings instead of writing
code. **All missing-guardrail recommendations use one rule_id — `CODED_GUARDRAIL_RECOMMENDED` (Info)** — one per
missing guardrail, specifics in the message.

1. **Read agent context** (done above): system prompt, schemas, `@tool` docstrings, and the already-wired
   guardrails (to avoid recommending what's there).
2. **Catalog-driven analysis** — for each catalog entry read `when_to_use`, `use_cases`, `description`,
   `security_risk_addressed`; does the agent's purpose / data / threat model match? Read `when_not_to_use` and skip
   if the agent matches a disqualifying condition. Cross-reference the Step 0 status lookup — only recommend
   `Available` validators (mention `Unauthorised` ones; skip ones absent from the list).
3. **De-duplicate by `security_category`** — group matched candidates by `security_category` + scope + stage; drop
   catalog-deprecated entries; keep the best fit; mention the alternative.
4. **Recommended scope (block as early as possible)** — the outermost PRE scope the validator's `allowed_scopes`
   permits for input protection (**Agent** > Llm > Tool), Agent · POST for output protection, Tool scope only for a
   genuinely tool-specific concern. In coded terms: Agent scope → `GuardrailScope.AGENT` middleware or `@guardrail`
   on the agent factory; Llm → `GuardrailScope.LLM` or `@guardrail` on the LLM factory; Tool →
   `GuardrailScope.TOOL` with `tools=[…]` or `@guardrail` on the `@tool`.
5. **Recommended action (the protection-vs-audit signal)** — default to the catalog example's `action_type`; state
   which it is: **block / escalate** (protection really needed) vs **log** (audit only). Never silently downgrade
   block → log.

### Emit the finding

One `CODED_GUARDRAIL_RECOMMENDED` (Info) per missing guardrail. The message carries: which guardrail /
`security_category`, why (the matched `when_to_use` / `use_cases` item or data flow), the recommended scope, and the
recommended action with the protection-vs-audit signal. Examples:

- *"Recommend a PII-detection guardrail at Agent scope with a **block** action — the input schema carries
  `customer_email` / `ssn`; blocking at `GuardrailScope.AGENT` · PRE stops unexpected PII before the LLM. Protection
  needed: block."*
- *"Recommend a Tool-scope **log** guardrail on `send_customer_email` for an audit trail — the tool legitimately
  handles the recipient email; use log (not block) so the tool keeps working. Audit only."*

**Validator-name caution:** do NOT name a platform-documented validator (`harmful_content`,
`intellectual_property`, `user_prompt_attacks`) unless already present in the code — phrase generically.
`pii_detection` / `prompt_injection` are SDK-confirmed and may be named.

---

## Report

Merge findings into the Step 5 Critical / Warning / Info findings tables (SKILL.md Step 2.5b), one row per finding:

```
| <id> | `<rule_id>` | `<file>`: <message>. <suggested_fix>. |
```

- Recommendations (`CODED_GUARDRAIL_RECOMMENDED`) → **`I-D-` (Info)** — improvements, not failures. The action
  signal lives in the message, not the severity.
- Defects (`CODED_GUARDRAIL_ACTION_INEFFECTIVE`, `CODED_GUARDRAIL_MISAPPLIED`) → the `judgment` band; pick
  Critical/Warning/Info by impact and show the reasoning.
- `file` = the entry `.py`; `element` = the guardrail name.
- If a deterministic checkpoint was created, update that same file into the complete report and remove its
  in-progress note. Do not recreate the report in a way that drops or paraphrases checkpointed CLI findings.

---

## Critical Rules

1. **Checkpoint deterministic findings first.** Before Step 0 or any research, write every CLI-emitted
   `CODED_GUARDRAIL_*` issue verbatim into the requested report; later update that same report to the complete
   Step 5 form.
2. **Run after `uip codedagent review` (Step 2.5a)** and only on guardrails the CLI did not flag — never <!-- uip-check-skip -->
   double-flag a `CODED_GUARDRAIL_WRONG_IMPORT` / `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS` /
   `CODED_GUARDRAIL_INVALID_CONTRACT` deterministic finding.
3. **Catalog-driven, not hardcoded** — every audit verdict and recommendation cites a catalog field
   (`when_not_to_use`, `when_to_use` / `use_cases`, `examples[].config.action_type`). Verdicts need only the
   catalog and the agent source; when the report names Python classes/enums/imports not already visible in the
   source, they come from the SDK docs, never memory.
4. **Catalog unavailable → defer Audit Mode** (Rules Skipped), keep Recommend Mode's source-only detection with
   generic wording and the code-only wiring half of `CODED_GUARDRAIL_MISAPPLIED`. Never guess
   effectiveness/relevance without the catalog.
5. **Recommendations are one Info rule** (`CODED_GUARDRAIL_RECOMMENDED`), one finding per missing guardrail, details
   in the message; signal **block/escalate** (protection) vs **log** (audit).
6. **Never silently downgrade block → log** — a security-critical guardrail at `log` is a defect
   (`CODED_GUARDRAIL_ACTION_INEFFECTIVE`), not an acceptable choice, unless the catalog/agent shows a stated reason.
7. **Do not name platform-documented validators** (`harmful_content` / `intellectual_property` /
   `user_prompt_attacks`) unless already present — phrase generically. `pii_detection` / `prompt_injection` may be
   named.
8. **Review only** — emit findings; never write guardrails, edit the entry `.py`, or run mutating `uip codedagent`
   commands.

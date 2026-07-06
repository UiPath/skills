# Guardrail Review — LLM-as-judge (audit + recommend)

The read-only **review** counterpart of the `uipath-agents` guardrail recommend/validate capability. It powers
the guardrail judgment rules in [`../agents-lowcode-rules.md`](../agents-lowcode-rules.md) §GuardrailsChecker.
Run it during a low-code agent review (SKILL.md Step 2.5b) **after** `uip agent review` (Step 2.5a). Two modes:

- **Audit Mode** — the agent already has guardrails → are they *effective and appropriate*? (emits **defects**)
- **Recommend Mode** — the agent is missing guardrails for use cases it matches → which should it add? (emits
  **Info recommendations**)

This is **review only** — never write, fix, or `uip agent validate`. The reviewer emits findings; the user
(or the `uipath-agents` skill) applies them.

> **Boundary with `uip agent review` — do not double-flag.** The review CLI owns every FORMAT / SCHEMA /
> SET-MEMBERSHIP guardrail check and emits them as `GUARDRAIL_*` / `GUARDRAIL_CUSTOM_*` / `LOWCODE_*GUARDRAIL*`
> rule IDs (unknown validator, scope-not-allowed, missing/unknown/type-mismatch/value-invalid parameters,
> custom-rule discriminators/operator/value/scope, tool-ref existence, missing name/description). The rules here
> fire **only on guardrails the CLI found format-valid**, and judge only what code cannot decide: whether a valid
> action actually protects at its scope, whether a valid guardrail belongs on this agent at all, and whether a
> guardrail the agent should have is missing. A format-invalid guardrail is skipped here until it is fixed — do
> not re-describe its format problem.

Like the recommend capability, this is **live-catalog driven** — the catalog's authored fields (`when_to_use`,
`use_cases`, `security_risk_addressed`, `when_not_to_use`, `security_category`, `examples[].config`) drive every
decision. Do not hardcode which guardrail fits which agent.

---

## Step 0 — Fetch Catalog and Available Validators

Run this once when the low-code `agent.json` has a non-empty `guardrails[]` **or** the agent matches any catalog
use case (so Recommend Mode can run). Same fetch the `uipath-agents` guardrail modes use.

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

### If the catalog is unavailable

If the catalog output contains `"Code": "GuardrailCatalogUnavailable"` (or the CLI is unavailable), **do not
guess**:

- **Audit Mode** (`LC_GUARDRAIL_ACTION_INEFFECTIVE`, `LC_GUARDRAIL_MISAPPLIED`) depends on the catalog → record
  these rules under the report's "Rules Skipped" subsection with reason `"guardrails catalog unavailable"`
  (SKILL.md Critical Rule 11). Do not emit catalog-grounded effectiveness/relevance verdicts without it.
- **Recommend Mode** (`LC_GUARDRAIL_RECOMMENDED`) can still detect a missing guardrail from `agent.json` alone
  (schema/prompt/tool inference); when the catalog is absent, phrase the recommended scope/action generically
  and note "catalog-limited" in the message.

---

## Audit Mode — existing guardrails (findings are defects)

For each guardrail in `agent.json`'s `guardrails[]` that the review CLI did **not** flag format-invalid, read
its `validator`, `selector.scopes`, and action `$actionType`, then run two checks.

### Actionability Check → `LC_GUARDRAIL_ACTION_INEFFECTIVE`

A format-valid guardrail's **action** can be ineffective or counterproductive for its **scope**. Compare the
configured action against the catalog entry's `when_not_to_use` and its representative `examples[].config`
action for the chosen scope. Emit when the action is in that scope's invalid set. Canonical cases:

- A **security-critical** guardrail (`security_category` `adversarial_input` / `content_safety`) set to `log`
  where the catalog example uses `block` — it looks protected but isn't (recommend capability Step 5: *never
  silently downgrade block → log*).
- `pii_detection` with `Block` / `Filter` at **Tool** scope on a tool that legitimately needs the PII — the
  catalog's `when_not_to_use` says *"Do not use at Tool scope with Block or Filter action if the tool requires
  PII to function (e.g., a SendEmail tool needs the recipient email address)"*; blocking breaks the tool.
- `pii_detection` with `Log` at **Agent** / **Llm** scope — Log there does **not** prevent PII from entering or
  reaching the LLM (recommend the blocking action the catalog example uses).

In the description, name the catalog-recommended action for that scope. Severity is `judgment` — a guardrail
that breaks the agent or leaves a security gap can be Critical; a milder ineffectiveness is Warning/Info.

### Relevance Check → `LC_GUARDRAIL_MISAPPLIED`

Establish the agent's real context (system prompt, `inputSchema`, `outputSchema`, tool resources). Read the
catalog entry's `when_not_to_use` / `NOT_recommended_for`. Emit when the agent matches a disqualifying condition
— the guardrail doesn't belong on this agent. Example: a generate-only agent with no user input carrying a PII
guardrail (PII `pattern_a`: the agent's PII output is the intended product; the guardrail adds no protection and
may block legitimate output). Cite the matched `when_not_to_use` clause in the description.

---

## Recommend Mode — missing guardrails (findings are Info recommendations)

Reuse the recommend capability's reasoning, but emit findings instead of writing config. **All missing-guardrail
recommendations use one rule_id — `LC_GUARDRAIL_RECOMMENDED` (Info)** — emitted **once per missing guardrail**,
with the specifics in the **message**.

### R1 — Read agent context

From `agent.json`: system prompt text, `inputSchema` / `outputSchema` property names + descriptions, tool
resource names + descriptions (`resources/`), and the existing `guardrails[]` (to avoid recommending what's
already there).

### R2 — Catalog-driven analysis

For each catalog entry, read `when_to_use`, `use_cases`, `description`, `security_risk_addressed`, and reason:
does the agent's purpose / data / threat model match? Read `when_not_to_use` and skip the entry if the agent
matches a disqualifying condition. Cross-reference the Step 0 status lookup — only recommend `Available`
validators (mention `Unauthorised` ones so the user can ask their admin; skip ones absent from the list).

### R3 — De-duplicate by `security_category`

Group matched candidates by `security_category` + scope + stage. For a group with more than one candidate, drop
catalog-deprecated entries, keep the single best fit, and mention the alternative in the message. Derive grouping
and deprecation from the catalog's own fields — do not hardcode validator names.

### R4 — Recommended scope (block as early as possible)

Recommend the outermost PRE scope the validator's `AllowedScopes` permits for input protection (**Agent** > Llm
> Tool), Agent · POST for output protection, Tool scope only for a genuinely tool-specific concern.

### R5 — Recommended action (the protection-vs-audit signal)

Default to the catalog example's `action_type`, and state which of the two the recommendation is:

- **block / escalate — protection really needed:** security-critical use cases (PII that must not enter,
  prompt-injection / jailbreak on free-text input, harmful content / IP on generated output). Recommend a
  blocking/escalating guardrail; say so plainly.
- **log — audit only:** a tool legitimately handles sensitive data, or the user wants observe-first. Recommend a
  Tool-scope **log** guardrail for an audit trail — **not** a block that would break the tool.

### Emit the finding

One `LC_GUARDRAIL_RECOMMENDED` (Info) per missing guardrail. The message must carry: which guardrail /
`security_category`, why (the matched `when_to_use` / `use_cases` item or the data flow), the recommended scope,
and the recommended action with the protection-vs-audit signal. Cite the catalog's `examples[].config` in the
fix. Examples:

- *"Recommend a PII-detection guardrail at Agent scope with a **block** action — the input schema carries
  `customer_email` / `ssn` (data_privacy); blocking at Agent · PRE stops unexpected PII before the LLM.
  Protection needed: block."*
- *"Recommend a Tool-scope **log** guardrail on `SendCustomerEmail` for an audit trail — the tool legitimately
  handles the recipient email; use log (not block) so the tool keeps working. Audit only."*

**Validator-name caution (carry over from the catalog/registry note):** do NOT name a platform-documented
validator (`harmful_content`, `intellectual_property`, `user_prompt_attacks`) unless it is already present in the
project's config — phrase generically (e.g. "an appropriate content-safety guardrail supported by this agent
layout"). `pii_detection` and `prompt_injection` are SDK-confirmed and may be named.

---

## Report

Merge findings into the Step 5 "Rule Findings" subsection (SKILL.md Step 2.5b), canonical line format:

```
[<prefix><n>] `<rule_id>` — <file> — <message>. Fix: <suggested_fix>.
```

- Recommendations (`LC_GUARDRAIL_RECOMMENDED`) → **`I-D-` (Info)** — the lowest grade; they are improvements, not
  failures. The action signal (block/escalate vs log) lives in the message, not the severity.
- Defects (`LC_GUARDRAIL_ACTION_INEFFECTIVE`, `LC_GUARDRAIL_MISAPPLIED`) → the `judgment` band; pick
  Critical/Warning/Info by impact and show the reasoning.
- `file` = `agent.json` (or the normalized JSON); `element` = the guardrail name (defects) or the
  `security_category` (recommendations).

---

## Critical Rules

1. **Run after `uip agent review` (Step 2.5a)** and only on format-valid guardrails — never double-flag a
   `GUARDRAIL_*` format finding.
2. **Catalog-driven, not hardcoded** — every audit verdict and recommendation cites a catalog field
   (`when_not_to_use`, `when_to_use` / `use_cases`, `examples[].config.action_type`).
3. **Catalog unavailable → defer Audit Mode** (Rules Skipped), keep Recommend Mode's `agent.json`-only detection
   with generic wording. Never guess effectiveness/relevance without the catalog.
4. **Recommendations are one Info rule** (`LC_GUARDRAIL_RECOMMENDED`), one finding per missing guardrail, details
   in the message; signal **block/escalate** (protection) vs **log** (audit).
5. **Never silently downgrade block → log** — a security-critical guardrail at `log` is a defect
   (`LC_GUARDRAIL_ACTION_INEFFECTIVE`), not an acceptable choice, unless the catalog/agent shows a stated reason.
6. **Do not name platform-documented validators** (`harmful_content` / `intellectual_property` /
   `user_prompt_attacks`) unless already present — phrase generically. `pii_detection` / `prompt_injection` may
   be named.
7. **Review only** — emit findings; never write guardrails, fix `agent.json`, or run `uip agent validate`.

# Guardrail Review — LLM-as-judge (audit + recommend)

The read-only **review** counterpart of the `uipath-agents` guardrail recommend/validate capability. It powers [`../agents-lowcode-rules.md`](../agents-lowcode-rules.md) §GuardrailsChecker and runs during low-code agent review (SKILL.md Step 2.5b), **after** `uip agent review` (Step 2.5a).

Modes:
- **Audit Mode:** existing guardrails → effective and appropriate? Emit **defects**.
- **Recommend Mode:** missing guardrails for matching use cases → emit **Info recommendations**.

Review only: never write, fix, or `uip agent validate`; emit findings for the user or `uipath-agents` skill to apply.

> **Boundary with `uip agent review` — do not double-flag.** The CLI owns FORMAT / SCHEMA / SET-MEMBERSHIP checks and emits `GUARDRAIL_*` / `GUARDRAIL_CUSTOM_*` / `LOWCODE_*GUARDRAIL*` IDs for unknown validator, scope-not-allowed, missing/unknown/type-mismatch/value-invalid parameters, custom-rule discriminators/operator/value/scope, tool-ref existence, and missing name/description. These rules apply only to CLI-format-valid guardrails and judge only what code cannot: whether a valid action protects at its scope, whether a valid guardrail belongs on the agent, and whether a required guardrail is missing. Skip format-invalid guardrails until fixed; do not restate their format problems.

Decisions are **live-catalog driven**. Use catalog `when_to_use`, `use_cases`, `security_risk_addressed`, `when_not_to_use`, `security_category`, and `examples[].config`; never hardcode validator-to-agent fit.

## Conclusive existing-guardrail fast path — completed report checkpoint

When a format-valid guardrail and its selected source conclusively match a catalog `when_not_to_use` clause:

1. Run `uip agent review` and retain deterministic findings and `Data.Grade`.
2. Read the guardrail's exact source path, `id`, `name`, `validatorType`, action, scopes, and `matchNames`, plus only its selected source or resource.
3. Fetch the catalog and tenant validator list once, as specified in Step 0.
4. Compare configured action and scope with the exact `when_not_to_use` clause and relevant `examples[].config`.
5. If the clause directly matches the selected source, establish `LC_GUARDRAIL_ACTION_INEFFECTIVE` and immediately save the requested report.

The completed checkpoint must include retained CLI findings, letter-grade derivation, and the Audit Mode finding with exact guardrail source path and identifiers, selected resource path and identifiers, matched catalog clause, configured scope/action, and catalog-supported fix. If the user explicitly requests additional exhaustive review, save this checkpoint first and update the same report afterward; otherwise return it and end the review turn. Do not delay it for solution packing, eval inspection, repeated validation or catalog calls, general architecture analysis, or unrelated project introspection.

Require a direct source-to-catalog contradiction, not a plausible concern. For example, `pii_detection` with `Block` or `Filter` at `Tool` scope selecting `SendCustomerEmail`, whose input schema requires `recipient_email`, directly matches a catalog clause saying that action breaks a tool requiring PII. If the input is optional or the clause does not directly match, continue normal Audit Mode.

## Missing-guardrail fast path — completed deliverable

When the source clearly matches a missing-guardrail use case and `guardrails[]` is absent or lacks the matching validator:

1. Run `uip agent review` and retain deterministic findings and `Data.Grade`.
2. Read the system prompt, schema property names, tool/resource names, and existing `guardrails[]` from the target agent source.
3. Fetch the catalog and tenant validator list once, as specified in Step 0.
4. Establish `LC_GUARDRAIL_RECOMMENDED` using R2–R5.
5. Immediately save the requested report with rule ID exactly `LC_GUARDRAIL_RECOMMENDED`, the exact source-evidence clause, and the R5 scope/action, then return it.

This saved report is the completed deliverable. After saving it, **end the current review turn** unless the initial request explicitly asks for exhaustive review or additional non-guardrail checks. Do not delay delivery for solution packing, eval inspection, repeated catalog/list calls, general architecture analysis, or unrelated project introspection.

Never invent `LC_GUARDRAIL_PII_MISSING`, `LC_GUARDRAIL_MISSING`, or other descriptive IDs. If the catalog fetch fails, still use `LC_GUARDRAIL_RECOMMENDED` per [Step 0 — If the catalog is unavailable](#if-the-catalog-is-unavailable): use generic scope/action wording and note `catalog-limited`.

## Step 0 — Fetch Catalog and Available Validators

Run this once when low-code `agent.json` has a non-empty `guardrails[]` or the agent matches any catalog use case.

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

- On **CACHE_HIT**, read `.guardrails-catalog-cache.json` directly.
- On **CACHE_MISS**, run `uip agent guardrails catalog --output json > .guardrails-catalog-cache.json` and save its output. The CLI writes success and error JSON to stdout; do not add `2>&1`.
- Never invoke `uip agent guardrails catalog` a second time in the same review. Read `.guardrails-catalog-cache.json` for every later look, parse, or re-check.

### Guardrails List (NEVER cached — tenant-specific)

Run:

```bash
uip agent guardrails list --output json
```

Build `{ validatorId: status }` from the `Data` array, using only `Status == "Available"`.

`Validator` is not unique: key on `(Validator, IsByo)`, not `Validator` alone. A BYOG tenant can have two entries with the same `Validator`, one built-in and one BYO (`IsByo: true`); collapsing them can use the wrong `Parameters`/`AllowedScopes`. When reviewed guardrail JSON has `byoValidatorName`, match it to `ByoValidatorName`, not only `Validator`. See [uipath-agents guardrails.md § BYO (bring-your-own) guardrails](/uipath:uipath-agents).

### If the catalog is unavailable

If output contains `"Code": "GuardrailCatalogUnavailable"` or the CLI is unavailable, do not guess:

- **Audit Mode:** put catalog-dependent `LC_GUARDRAIL_ACTION_INEFFECTIVE` and `LC_GUARDRAIL_MISAPPLIED` under the report's **Rules Skipped** subsection with reason `"guardrails catalog unavailable"` (SKILL.md Critical Rule 11). Emit no catalog-grounded effectiveness/relevance verdict.
- **Recommend Mode:** continue `agent.json`-only schema/prompt/tool inference; use generic scope/action wording and note `catalog-limited`.

## Audit Mode — existing guardrails (defects)

For each `agent.json` `guardrails[]` entry not flagged format-invalid by the CLI, read `validator`, `selector.scopes`, and action `$actionType`, then run both checks.

A BYO-backed entry with tenant `Status: "Disabled"` is a configuration switch, not a format problem. For a guardrail targeting that configuration through `byoValidatorName`, treat it like an `Unauthorised` validator: unable to protect, and report that condition.

### Actionability Check → `LC_GUARDRAIL_ACTION_INEFFECTIVE`

Compare the action with the catalog entry's `when_not_to_use` and representative `examples[].config` action for the chosen scope. Emit when the action is in that scope's invalid set. Include the catalog-recommended action for that scope. Severity is `judgment`: Critical when the guardrail breaks the agent or leaves a security gap; otherwise Warning/Info.

Relevant catalog-driven cases include:
- A security-critical guardrail (`security_category` `adversarial_input` / `content_safety`) using `log` where the catalog example uses `block`.
- `pii_detection` using `Block` / `Filter` at `Tool` scope for a tool that legitimately requires PII; match the catalog's `when_not_to_use` clause.
- `pii_detection` using `Log` at `Agent` / `Llm` scope, which does not prevent PII entering or reaching the LLM.

### Relevance Check → `LC_GUARDRAIL_MISAPPLIED`

Read system prompt, `inputSchema`, `outputSchema`, and tool resources to establish real context. Read catalog `when_not_to_use` / `NOT_recommended_for`. Emit when the agent matches a disqualifying condition, such as a generate-only agent with no user input carrying a PII guardrail when PII output is the intended product. Cite the matched catalog clause.

## Recommend Mode — missing guardrails (Info recommendations)

Reuse recommend reasoning but emit findings instead of writing configuration. Emit exactly one rule ID, `LC_GUARDRAIL_RECOMMENDED` (Info), once per missing guardrail.

### R1 — Read agent context

Read from `agent.json`: system prompt; `inputSchema` / `outputSchema` property names and descriptions; tool resource names and descriptions (`resources/`); and existing `guardrails[]`.

### R2 — Catalog-driven analysis

For each catalog entry, read `when_to_use`, `use_cases`, `description`, `security_risk_addressed`, `when_not_to_use`, and `security_category`. Match purpose, data, and threat model; skip disqualifying entries. Cross-reference the Step 0 status lookup: recommend only `Available` validators, mention `Unauthorised` validators so the user can ask an admin, and skip validators absent from the list.

### R3 — De-duplicate by `security_category`

Group matches by `security_category` + scope + stage. If a group has multiple candidates, use catalog fields to identify deprecated entries, keep the single best fit, and mention the alternative.

### R4 — Recommended scope (block as early as possible)

Recommend the outermost PRE scope allowed by the validator's `AllowedScopes` for input protection (**Agent** > Llm > Tool), Agent · POST for output protection, and Tool scope only for a genuinely tool-specific concern.

### R5 — Recommended action (protection vs audit)

Default to catalog `examples[].config` `action_type` and state the signal:
- **block / escalate — protection really needed:** security-critical PII that must not enter, prompt-injection / jailbreak on free-text input, or harmful content / IP on generated output.
- **log — audit only:** a tool legitimately handles sensitive data or the user wants observe-first; recommend Tool-scope **log**, not block, so the tool works.

### Emit the finding

Each message must include the guardrail / `security_category`, reason from the matching `when_to_use` / `use_cases` item or data flow, recommended scope, recommended action, protection-vs-audit signal, and a source-evidence clause exactly in the form `<source path>: <exact matching identifier(s)>`. Copy schema property paths/names, tool names, resource names, and other identifiers verbatim. Cite catalog `examples[].config` in the fix. For schema matches, cite the property path and names, for example `agent.json inputSchema.properties: customer_email, full_name, ssn`.

Do not name platform-documented validators (`harmful_content`, `intellectual_property`, `user_prompt_attacks`) unless already present in project config; use generic wording such as “an appropriate content-safety guardrail supported by this agent layout.” `pii_detection` and `prompt_injection` are SDK-confirmed and may be named.

## Report

Merge findings into the Step 5 Critical / Warning / Info findings tables (SKILL.md Step 2.5b), one row per finding:

```text
| <id> | `<rule_id>` | `<file>`: <message>. <suggested_fix>. |
```

- `LC_GUARDRAIL_RECOMMENDED` → **`I-D-` (Info)**, the lowest grade; recommendations are improvements, not failures. Put block/escalate versus log in the message, not severity.
- `LC_GUARDRAIL_ACTION_INEFFECTIVE` and `LC_GUARDRAIL_MISAPPLIED` → `judgment` band; choose Critical/Warning/Info by impact and show reasoning.
- `file` = `agent.json` (or normalized JSON); `element` = guardrail name for defects or `security_category` for recommendations.

## Critical Rules

1. **Run after `uip agent review` (Step 2.5a)** and only on format-valid guardrails; never double-flag a `GUARDRAIL_*` format finding.
2. **Catalog-driven, not hardcoded:** cite catalog `when_not_to_use`, `when_to_use` / `use_cases`, or `examples[].config.action_type` for every audit verdict and recommendation.
3. **Catalog unavailable → defer Audit Mode** to Rules Skipped; retain Recommend Mode's `agent.json`-only detection with generic wording. Never guess effectiveness/relevance.
4. Recommendations use one Info rule, `LC_GUARDRAIL_RECOMMENDED`, once per missing guardrail; preserve exact source path and identifiers and signal **block/escalate** versus **log**.
5. **Never silently downgrade block → log:** a security-critical guardrail at `log` is `LC_GUARDRAIL_ACTION_INEFFECTIVE`, unless the catalog/agent shows a stated reason.
6. Do not name `harmful_content` / `intellectual_property` / `user_prompt_attacks` unless already present; phrase generically. `pii_detection` / `prompt_injection` may be named.
7. **Review only:** emit findings; never write guardrails, fix `agent.json`, or run `uip agent validate`.
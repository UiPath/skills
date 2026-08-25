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

## Conclusive existing-guardrail fast path — completed report checkpoint

When a format-valid existing guardrail and the source it selects conclusively match a catalog
`when_not_to_use` clause, use this bounded sequence **before** general manual review:

1. run `uip agent review` and retain its deterministic findings and `Data.Grade`;
2. read the existing guardrail's exact source path, `id`, `name`, `validatorType`, action, scopes, and
   `matchNames`, plus only the source or resource selected by that guardrail;
3. fetch the catalog and tenant validator list once, as specified in Step 0;
4. compare the configured action and scope with the catalog's exact `when_not_to_use` clause and relevant
   `examples[].config`; and
5. when the clause directly matches the selected source, establish `LC_GUARDRAIL_ACTION_INEFFECTIVE` and
   immediately save the requested report.

The saved report is a completed checkpoint, not working notes. It must include the retained CLI findings, the
letter-grade derivation, and the Audit Mode finding with the exact guardrail source path and identifiers, selected
resource path and identifiers, matched catalog clause, configured scope/action, and catalog-supported fix. If the
user explicitly requested additional exhaustive review, save this checkpoint first and update the same report
after that work completes. Otherwise, return the report and end the current review turn. Do not delay the checkpoint
for solution packing, eval inspection, repeated validation or catalog calls, general architecture analysis, or
unrelated project introspection.

This fast path requires a direct source-to-catalog contradiction, not a plausible concern. Canonical example:
`pii_detection` uses `Block` or `Filter` at `Tool` scope, `matchNames` selects `SendCustomerEmail`, and that tool's
input schema requires `recipient_email`; the catalog says that action breaks a tool that requires PII to function.
If the selected input is optional or the catalog clause does not directly match, continue normal Audit Mode instead.

## Missing-guardrail fast path — completed deliverable

When the source clearly matches a missing-guardrail use case and `guardrails[]` is absent or lacks the matching
validator, use this bounded sequence:

1. run `uip agent review` and retain its deterministic findings and `Data.Grade`;
2. read the system prompt, schema property names, tool/resource names, and existing `guardrails[]` from the target
   agent source;
3. fetch the catalog and tenant validator list once, as specified in Step 0;
4. establish the `LC_GUARDRAIL_RECOMMENDED` finding using R2–R5; and
5. immediately save the requested report with the rule ID exactly
   `LC_GUARDRAIL_RECOMMENDED`, the exact source-evidence clause, and the R5 scope/action, then return it.

The saved report is the completed deliverable for this guardrail path. After saving it, **end the current review
turn**. Do not delay delivery for solution packing, eval inspection, repeated catalog/list calls, general
architecture analysis, or unrelated project introspection. Continue beyond it only when the user's initial request
explicitly asks for an exhaustive review or names additional non-guardrail checks.

`LC_GUARDRAIL_PII_MISSING`, `LC_GUARDRAIL_MISSING`, and other descriptive variants are not valid rule IDs — never
invent a new one. This is about invented IDs only: if the catalog fetch itself fails, do **not** fall back to
rule-ID-less prose for a missing-guardrail finding — `LC_GUARDRAIL_RECOMMENDED` stays the correct, valid rule ID
per [Step 0 — If the catalog is unavailable](#if-the-catalog-is-unavailable): use generic scope/action wording and
note "catalog-limited" in the message, but still cite `LC_GUARDRAIL_RECOMMENDED`.

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

**Never invoke `uip agent guardrails catalog` a second time in the same review.** Every later read — a quick
look, a `python3`/`jq` parse, a re-check — goes through `.guardrails-catalog-cache.json`, not a fresh CLI call.

### Guardrails List (NEVER cached — tenant-specific)

```bash
uip agent guardrails list --output json
```

Build a `{ validatorId: status }` lookup from the `Data` array (use only `Status == "Available"`).

> **`Validator` is not unique — key on `(Validator, IsByo)`, not `Validator` alone.** A tenant with a bring-your-own (BYOG) configuration for a validator has two entries sharing the same `Validator` name — one built-in, one BYO (`IsByo: true`). Collapsing them can point Audit Mode's Correctness/Actionability comparison at the wrong entry's `Parameters`/`AllowedScopes`. When the reviewed guardrail JSON carries `byoValidatorName`, match it against that entry's `ByoValidatorName`, not `Validator` alone. See [uipath-agents guardrails.md § BYO (bring-your-own) guardrails](/uipath:uipath-agents).

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

> **A BYO-backed guardrail's tenant entry showing `Status: "Disabled"` is a configuration switch, not a format problem.** It means the tenant admin turned that specific BYOG configuration off (Admin → AI Trust Layer → Guardrails Configurations) — don't re-diagnose it as a schema/discriminator issue. If the agent's guardrail targets that disabled configuration (via `byoValidatorName`), it functions the same as targeting an `Unauthorised` validator — treat it as unable to protect and note it in the report.

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
and the recommended action with the protection-vs-audit signal. It must also carry a source-evidence clause in
the form `<source path>: <exact matching identifier(s)>`. Copy schema property names, tool names, resource names,
and other matched identifiers verbatim from the source; never replace them with display-friendly prose. For a
schema match, cite the property path and names, for example
`agent.json inputSchema.properties: customer_email, full_name, ssn`. Cite the catalog's `examples[].config` in
the fix. Examples:

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

Merge findings into the Step 5 Critical / Warning / Info findings tables (SKILL.md Step 2.5b), one row per finding:

```
| <id> | `<rule_id>` | `<file>`: <message>. <suggested_fix>. |
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
4. **Recommendations are one Info rule** (`LC_GUARDRAIL_RECOMMENDED`), one finding per missing guardrail. The
   message preserves the exact source path and matched identifiers verbatim, then signals **block/escalate**
   (protection) vs **log** (audit).
5. **Never silently downgrade block → log** — a security-critical guardrail at `log` is a defect
   (`LC_GUARDRAIL_ACTION_INEFFECTIVE`), not an acceptable choice, unless the catalog/agent shows a stated reason.
6. **Do not name platform-documented validators** (`harmful_content` / `intellectual_property` /
   `user_prompt_attacks`) unless already present — phrase generically. `pii_detection` / `prompt_injection` may
   be named.
7. **Review only** — emit findings; never write guardrails, fix `agent.json`, or run `uip agent validate`.

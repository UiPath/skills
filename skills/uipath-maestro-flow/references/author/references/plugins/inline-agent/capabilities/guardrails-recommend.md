# Guardrail Recommendation and Validation

This reference covers two workflows for inline agents:
- **Recommend**: The agent has no guardrails (or insufficient ones) → which guardrails should be added?
- **Validate**: The agent already has guardrails → are they correctly configured and appropriate?

Both workflows are driven by live CLI data — the catalog for recommendation reasoning and the guardrails list for parameter/scope constraints. Do not hardcode assumptions about which guardrail fits which agent type. The catalog's authored fields (`WhenToUse`, `UseCases`, `SecurityRiskAddressed`, `WhenNotToUse`) drive recommendation decisions; the guardrails list's `Parameters`, `AllowedScopes`, and `GuardrailStages` drive correctness validation.

All `uip agent guardrails` commands are tenant-level — they run from the flow project directory with no agent project on disk.

> **This file covers WHEN to add guardrails and WHY. For the exact JSON schema, discriminator fields, parameter types, and action shapes, always read [guardrails.md](guardrails.md) before writing any guardrail JSON.**

---

## Step 0 — Fetch Catalog and Available Validators (MANDATORY — do this before any analysis)

### Catalog (cacheable — 30-minute TTL)

The catalog is the same for all tenants (authored metadata, rarely changes). Cache it locally for 30 minutes to avoid redundant calls.

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
- **CACHE_MISS**: fetch and save:
  ```bash
  uip agent guardrails catalog --output json > .guardrails-catalog-cache.json
  ```

Inspect the saved JSON. If the output contains `"Code": "GuardrailCatalogUnavailable"`, surface the message to the user and **stop** — do not fall back to guessing. This means the catalog endpoint is not yet available for this tenant. Note: the CLI writes all structured output (both success and error JSON) to stdout, so the redirect captures error responses correctly — do not add `2>&1`.

The cache file is `.guardrails-catalog-cache.json` in the current working directory. Add it to `.gitignore` if one exists.

### Guardrails List (NEVER cached — tenant-specific)

This returns only guardrails available to the current tenant (filtered by entitlements and feature flags). Run it fresh every time:

```bash
uip agent guardrails list --output json
```

Build a lookup of `{ validatorId: status }` from the `Data` array. You will use this in Steps 2 and 4 to filter recommendations.

> **Catalog vs. list — the key distinction:** The catalog lists all guardrails that exist on the platform (with rich metadata for reasoning). The guardrails list returns only those accessible to this tenant. Only recommend validators where `Status == "Available"` in the list.

---

## Recommend Mode

Use when the agent has no guardrails or when the user asks which guardrails to add.

### Step 1 — Read Agent Context

From the `uipath.agent.autonomous` node's `inputs` in the `.flow`, extract:
- **`systemPrompt` / `userPrompt` text** — what does the agent do? What domains and behaviors are described?
- **`agentInputVariables[]` + the `$vars` refs in the prompts** — what data does the agent receive?
- **`agentOutputVariables[]`** — property names and types — what data does the agent produce?
- **Wired tool nodes** — resource nodes on the agent's `tool` handle: their `inputs.name` and `inputs.description` — what external systems or operations does the agent invoke?
- **Existing `inputs.guardrails` array** — what is already configured? (to avoid duplicating)

Collect every wired tool's `inputs.name` (needed for Tool-scope recommendations).

### Exact Named-Tool Deterministic Rules — before catalog ranking

When the request gives both a named Tool and an exact mechanical predicate on
its input or output (literal word/phrase, regex, number, boolean, or always),
use the custom deterministic recipe below. This decision happens before
built-in catalog candidate ranking:

1. Treat quoted text and a distinct all-caps token such as `CONFIDENTIAL` as
   an exact literal predicate, even when the surrounding request is phrased
   semantically (for example, "worried it might publish CONFIDENTIAL content"
   or "what guardrails should I add?"). Do not broaden that literal into a
   semantic confidentiality classification.
2. Read the tool node's `inputs.name` and use that exact value as the only
   entry in `selector.matchNames`.
3. Set `$guardrailType: "custom"` and `selector.scopes: ["Tool"]`. This branch
   does not use a `builtInValidator` or `validatorParameters`.
4. For a literal word or phrase, use `$ruleType: "word"`,
   `operator: "contains"`, and preserve the exact requested literal as `value`.
   Use the matching custom rule type when the user explicitly requests a
   regex, number, boolean, or always condition.
5. Use a blocking action when the request says to prevent the Tool operation,
   then build the complete object from [guardrails.md](guardrails.md).

Broad semantic threats without an exact mechanical predicate continue through
the built-in catalog ranking in Step 2.

Once this deterministic branch matches, the catalog/list calls remain
mandatory discovery steps but cannot replace or override the custom rule with
`llm_as_judge`, PII detection, or any other built-in validator.

### Step 2 — Catalog-Driven Recommendation Analysis

For **each entry** in the catalog (`Guardrails[]` array from the cached JSON):

1. Read the entry's `WhenToUse`, `UseCases`, `Description`, and `SecurityRiskAddressed`.
2. Compare against agent context (prompts, variables, tool descriptions) using semantic reasoning:
   - Does the agent's purpose align with the `WhenToUse` scenario?
   - Do any `UseCases` items describe what this agent does or the data it handles?
   - Does the agent face the threat described in `SecurityRiskAddressed`?
3. Also read `WhenNotToUse`. If the agent matches a disqualifying condition, exclude this validator from recommendations (or mention it with an explanation).
4. Cross-reference with the guardrails list status lookup from Step 0:
   - `Available` → candidate for recommendation
   - `Unauthorised` → mention to the user ("this guardrail is not licensed for your tenant") but do NOT add it
   - Not in the list at all → skip silently (not available on this platform version)
5. If the validator is a candidate: use the catalog entry's `Examples[].Config` to determine the appropriate scope, stage, action, and parameters. The example config is the authoritative template for parameter shape.

Do **not** apply predetermined knowledge about which guardrail maps to which schema field. Let the catalog entry's authored fields drive every recommendation decision.

### Step 3 — De-duplicate Overlapping Validators

Several catalog validators address the same threat. Recommending more than one of them at the same scope and stage is redundant — it doubles latency and cost on every call for marginal benefit (the canonical case is `prompt_injection` and `user_prompt_attacks`: both have `SecurityCategory: "adversarial_input"` and both run at Llm · PRE).

After Step 2 produces the candidate list, group candidates by **(`SecurityCategory`, scope, stage)**. For any group with more than one candidate:

1. **Drop deprecated or unavailable entries first.** If the catalog marks an entry deprecated (via its `Status`, or a deprecation note in `Notes` / `WhenNotToUse`), remove it from the group. Never recommend a validator the catalog signals is being retired when an active alternative covers the same category.
2. **Keep the single best fit** for the agent's context — the one whose `WhenToUse` / `UseCases` most closely match. Recommend only that one.
3. **Mention the alternative(s)** you dropped and why (e.g. "also recommending only User Prompt Attacks, not Prompt Injection — both cover adversarial input at Llm PRE and the catalog marks Prompt Injection deprecated").

Do **not** hardcode validator names or a fixed "prefer X over Y" rule in your reasoning — derive the grouping from each entry's `SecurityCategory`, scope, and stage, and derive deprecation from the catalog's own fields. This keeps the behavior correct as the catalog evolves.

### Step 4 — Scoped or Tool-Specific Filtering (only when user requests)

If the user asks for recommendations for a **specific scope** (e.g., "only for Llm"):
- After Step 2, keep only candidates where the scope name appears in `AllowedScopes` (from the guardrails list output).
- Discard candidates that do not support that scope.

If the user asks for recommendations for a **specific tool** (e.g., "for the SendEmail tool"):
- Tool scope only. Confirm the tool node is wired to the agent's `tool` handle before writing.
- Set `selector.matchNames: ["<name>"]` where `<name>` is the tool node's `inputs.name` — **not** the node id or `display.label`.
- Note: custom guardrails (type `"Custom"` in catalog) also only support Tool scope.

#### Block as early as possible — default scope selection

When a validator supports **more than one scope** (e.g. `pii_detection` allows Agent / Llm / Tool per its `AllowedScopes`), pick the scope that stops a violation at the **outermost boundary the validator allows**, so a bad run is halted with the least wasted work:

| Guardrail intent | Prefer | Why |
|---|---|---|
| **Input protection** (block bad/sensitive input: PII, jailbreak, injection) | broadest **PRE** scope allowed → **Agent** > Llm > Tool | Agent · PRE fires once, before the agent reaches the LLM or any tool. Catching PII or an attack at Agent · PRE blocks the whole run immediately instead of after the model has already been called. |
| **Output protection** (block bad output the caller sees: harmful content, IP) | **Agent · POST** when allowed | Agent · POST inspects the agent's final answer — the thing the flow's downstream nodes actually receive. |
| **Tool I/O protection** (a specific tool's input/output) | **Tool** scope on that tool | Only narrow to Tool when the concern is genuinely that one tool, or the user scoped it there. |

Concretely: **PII detection meant to stop the agent handling personal data goes at `selector.scopes: ["Agent"]`, not `["Llm"]`** — both are listed in `AllowedScopes` for `pii_detection`, but Agent · PRE blocks the run earlier (before the LLM call) and covers the whole agent, not just one model invocation. Only drop to a narrower scope when the validator does not support the broader one (`prompt_injection` and `user_prompt_attacks` are Llm-only, so Llm · PRE is the earliest available for them) or when the user explicitly asks for a narrower scope.

Always confirm the chosen scope is in the validator's `AllowedScopes` from the guardrails list — never assume a scope the catalog/SDK does not permit.

### Step 5 — Choose the Action

The action (`{"$actionType": "block"}` vs `{"$actionType": "log"}` vs `escalate` / `filter`) is **not** a free choice — default to the `ActionType` in the catalog entry's representative `Examples[].Config`. For security-critical guardrails (`adversarial_input` — prompt injection / user prompt attacks; `content_safety` — harmful content / IP) the catalog examples use **`Block`**, because a logged-but-allowed violation provides no actual protection.

Rules:

1. **Default to the catalog example's `ActionType`.** If it is `Block`, generate `{"$actionType": "block", "reason": "..."}`. Do not substitute `log` for a security-critical guardrail on your own initiative.
2. **Never silently downgrade block → log.** A guardrail set to log-only when the user expected blocking is the dangerous failure mode — the agent looks protected but isn't. If you use `{"$actionType": "log"}` for any guardrail whose catalog `ActionType` default is `Block`, you **must** state it explicitly in the report and give the reason.
3. **Legitimate reasons to use `log` instead of `block`** (state which applies):
   - The user explicitly asked for observe-only / audit / "log first, block later" rollout.
   - A high false-positive risk where blocking would break normal operation (e.g. PII `Person` entity flagging ordinary words) — log so the user can tune thresholds before enforcing.
4. **When ambiguous, ask once.** If the user gave no action preference and the guardrail is security-critical, you may apply the `block` default and report it, or ask "block on violation, or log-only to start?" — but do not quietly pick `log`.

### Step 6 — Generate Config Blocks

For each recommended guardrail, use the catalog `Examples[].Config` as the template. Map it to the guardrail object shape using [guardrails.md](guardrails.md) (discriminators, UUID, PascalCase scopes, `$`-prefixed fields).

> Read [guardrails.md](guardrails.md) before writing any guardrail JSON. The `$guardrailType`, `$parameterType`, `$actionType`, `$ruleType`, and `$selectorType` discriminators cannot be guessed — they are specified there.

For parameters, use the `Parameters` array from the matching guardrails list entry to confirm correctness — see the [Correctness Check](#correctness-check) table in Validate Mode for the exact rules. Apply the same checks when generating config to avoid writing invalid parameters from the start.

Use the action chosen in Step 5.

Generate a fresh UUID for each guardrail `id`.

### Step 7 — Apply and Validate

Write the new guardrail blocks to the agent node's `inputs.guardrails[]` array in the `.flow`. Then run:

```bash
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

> `flow validate` is **silent on guardrail content** ([guardrails.md § validate silence](guardrails.md#flow-validate-does-not-check-guardrails)) — it gates the flow structure only. The correctness re-read below is the actual guardrail gate.

**Deterministic completion gate:** when the request matched the exact
named-Tool branch, re-read the `.flow` before validation and confirm the
written entry has `$guardrailType: "custom"`, Tool scope, the exact tool
`inputs.name`, and the requested custom rule type/value. If a built-in
validator was written, replace it with the required custom rule before
running validation or reporting completion.

Report to the user:
- What was added (by name)
- Why it was recommended (cite the catalog's `WhenToUse` or a specific `UseCases` item that matched the agent's context)
- What scope and action were chosen and why. If you dropped an overlapping validator in Step 3, name it and the reason. If you used `{"$actionType": "log"}` for a guardrail whose catalog `ActionType` default is `Block` (Step 5), call it out explicitly with the reason.
- What parameters were set and their meaning

---

## Validate Mode

Use when the agent already has guardrails and the user asks whether they are correctly configured or appropriate.

**Before any validation, run both CLI commands from Step 0** (catalog with cache, guardrails list without cache). The guardrails list output is the primary source of truth for correctness validation — it contains each validator's parameter definitions including valid types, options, and key sources.

For each existing guardrail in the agent node's `inputs.guardrails[]`:

### Correctness Check

Run `uip agent guardrails list --output json` (from Step 0) and find the matching validator by `Validator` name. The `Parameters` array is the authoritative source for all validation rules:

| CLI field | What to check |
|-----------|---------------|
| `Required: true` | Parameter must be present in `validatorParameters` |
| `Type` | Must match `$parameterType` — `"enum-list"`, `"map-enum"`, `"number"`, `"enum"`, `"text"`, or `"text-list"` |
| `Options` | For `enum-list`: every value must be in this list; array must be non-empty. For a scalar `enum` (e.g. `model` on `llm_as_judge`) whose `Options` is **empty**, the values come from LLM Gateway, not the catalog — run `uip agent guardrails llm-as-judge-models --output json` and use a `ModelId`; do **not** treat empty `Options` as invalid in that case |
| `KeySource` | For `map-enum`: keys must **exactly** match the values of the `Options`-sourced parameter named by `KeySource` — no extra, no missing keys |
| `Min` / `Max` | For `number` and `map-enum`: values must fall within this range |
| `Step` | For `number` and `map-enum`: values must be multiples of Step (e.g. Step=2, Min=0, Max=6 → valid values are 0, 2, 4, 6) |

Check that every parameter object has a `$parameterType` discriminator. Missing discriminators cause runtime failures — `flow validate` does not catch them.

### Actionability Check

1. From the guardrails list output, read `AllowedScopes` for the validator.
2. Check that `selector.scopes` values are all in `AllowedScopes`. If any scope is not allowed, flag it.
3. From the catalog entry's `WhenNotToUse` (if present), check whether the guardrail may be misapplied given the agent's actual context.
4. For Tool-scoped guardrails: does `selector.matchNames` list the intended tools? Does each name match the `inputs.name` of a resource node wired to the agent's `tool` handle? A ghost entry silently never fires.

### Relevance Check

1. Read the catalog entry's `WhenNotToUse` (from the catalog cache).
2. Compare against the agent's current context (prompts, variables, wired tools).
3. If the agent matches a `WhenNotToUse` condition, flag the guardrail as potentially misapplied and explain why.

### Report and Fix

Report per guardrail:
- **OK** — no issues found
- **Correctness issue** — describe the problem (e.g., "entityThresholds has key 'Sexual' but 'Sexual' is not in entities list — KeySource says keys must match the entities parameter's values") and the fix
- **Actionability issue** — describe the problem (e.g., "'Agent' is in selector.scopes but AllowedScopes for this validator is ['Llm', 'Tool'] — 'Agent' is not allowed; change scope to 'Llm' or 'Tool'") and the fix
- **Relevance issue** — describe why the guardrail may not be appropriate and what to consider instead

If the user asks to fix identified issues: apply corrections to the agent node's `inputs.guardrails[]`, then run `uip maestro flow format` + `uip maestro flow validate` (structure gate) and re-read the corrected objects against the Correctness Check table.

---

## Critical Rules

1. **Always fetch catalog first** (use cache if fresh); **always fetch guardrails list second** (no cache). Both are required before any analysis.
2. **If `GuardrailCatalogUnavailable`** → surface the message and stop. Do not fall back to guessing or hardcoded recommendations.
3. **Only recommend `Available` validators**. Mention `Unauthorised` ones to the user so they can contact their administrator.
4. **Every recommendation must cite** the catalog entry's `WhenToUse` or a specific `UseCases` item that matched the agent's context. Do not recommend a guardrail without explaining why it applies.
5. **Never recommend two validators with the same `SecurityCategory` at the same scope and stage** (e.g. `prompt_injection` + `user_prompt_attacks` at Llm PRE). De-duplicate per Step 3: drop catalog-deprecated entries, keep the best fit, mention the alternative. Derive the grouping and deprecation from the catalog's own fields — do not hardcode validator names.
6. **Default the action to the catalog example's `ActionType`; never silently downgrade `block` → `log`.** Security-critical guardrails (`adversarial_input`, `content_safety`) default to `{"$actionType": "block"}`. If you use `{"$actionType": "log"}` for a guardrail whose catalog `ActionType` default is `Block`, state it and the reason in the report (Step 5).
7. **Block as early as possible — pick the outermost scope the validator allows.** For input protection (PII, jailbreak, injection) prefer `selector.scopes: ["Agent"]` over `["Llm"]` over `["Tool"]`, so the run halts before the LLM call. PII meant to stop the agent handling personal data goes at **Agent**, not Llm. Only narrow when the validator is scope-restricted (e.g. `prompt_injection` / `user_prompt_attacks` are Llm-only) or the user asks for a narrower scope. See Step 4.
8. **For Tool scope**: verify the tool node is wired to the agent's `tool` handle before writing `matchNames`. If the agent has no wired tools, do not add a Tool-scoped guardrail.
9. **Correctness validation uses `uip agent guardrails list` output** — `Parameters[].Type`, `Options`, `KeySource`, `Min`, `Max`, `Step` are the authoritative source for all parameter rules. Do not hardcode validator-specific knowledge.
10. **The cache file is `.guardrails-catalog-cache.json`** in the working directory. Add it to `.gitignore` if one exists.
11. **Do not create separate guardrails per scope** — combine multiple scopes into a single guardrail's `scopes` array.
12. **All map-enum keys must exactly match the corresponding enum-list values** — no extra or missing keys. This is the most common correctness error.
13. **Read [guardrails.md](guardrails.md) before writing any JSON** — discriminator fields, PascalCase constraints, and parameter shapes are specified there and cannot be safely inferred. `flow validate` will not catch a wrong shape.
14. **Do NOT use TaskCreate, TaskUpdate, or other task-tracking tools for guardrail edits.** Edit the `.flow` directly — task management tools add bookkeeping turns without benefit and push runs over their turn budget.

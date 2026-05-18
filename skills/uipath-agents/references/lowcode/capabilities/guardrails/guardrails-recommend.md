# Guardrail Recommendation and Validation

This reference covers two workflows:
- **Recommend**: The agent has no guardrails (or insufficient ones) → which guardrails should be added?
- **Validate**: The agent already has guardrails → are they correctly configured and appropriate?

Both workflows are driven by live CLI data — the catalog for recommendation reasoning and the guardrails list for parameter/scope constraints. Do not hardcode assumptions about which guardrail fits which agent type. The catalog's authored fields (`when_to_use`, `use_cases`, `security_risk_addressed`, `when_not_to_use`) drive recommendation decisions; the guardrails list's `Parameters`, `AllowedScopes`, and `GuardrailStages` drive correctness validation.

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

Build a lookup of `{ validatorId: status }` from the `Data` array. You will use this in Steps 2 and 5 to filter recommendations.

> **Catalog vs. list — the key distinction:** The catalog lists all guardrails that exist on the platform (with rich metadata for reasoning). The guardrails list returns only those accessible to this tenant. Only recommend validators where `Status == "Available"` in the list.

---

## Recommend Mode

Use when the agent has no guardrails or when the user asks which guardrails to add.

### Step 1 — Read Agent Context

From `agent.json`, extract:
- **System prompt text** — what does the agent do? What domains and behaviors are described?
- **Input schema** — property names and types — what data does the agent receive?
- **Output schema** — property names and types — what data does the agent produce?
- **Tool resource names and descriptions** — from `resources/` — what external systems or operations does the agent invoke?
- **Existing guardrails array** — what is already configured? (to avoid duplicating)

Also read `resources/` to list all tool names (needed for Tool-scope recommendations).

### Step 2 — Catalog-Driven Recommendation Analysis

For **each entry** in the catalog (`guardrails[]` array from the cached JSON):

1. Read the entry's `when_to_use`, `use_cases`, `description`, and `security_risk_addressed`.
2. Compare against agent context (system prompt, schemas, tool descriptions) using semantic reasoning:
   - Does the agent's purpose align with the `when_to_use` scenario?
   - Do any `use_cases` items describe what this agent does or the data it handles?
   - Does the agent face the threat described in `security_risk_addressed`?
3. Also read `when_not_to_use`. If the agent matches a disqualifying condition, exclude this validator from recommendations (or mention it with an explanation).
4. Cross-reference with the guardrails list status lookup from Step 0:
   - `Available` → candidate for recommendation
   - `Unauthorised` → mention to the user ("this guardrail is not licensed for your tenant") but do NOT add it
   - Not in the list at all → skip silently (not available on this platform version)
5. If the validator is a candidate: use the catalog entry's `examples[].config` to determine the appropriate scope, stage, action, and parameters. The example config is the authoritative template for parameter shape.

Do **not** apply predetermined knowledge about which guardrail maps to which schema field. Let the catalog entry's authored fields drive every recommendation decision.

### Step 3 — Scoped or Tool-Specific Filtering (only when user requests)

If the user asks for recommendations for a **specific scope** (e.g., "only for Llm"):
- After Step 2, keep only candidates where the scope name appears in `AllowedScopes` (from the guardrails list output).
- Discard candidates that do not support that scope.

If the user asks for recommendations for a **specific tool** (e.g., "for the SendEmail tool"):
- Tool scope only. Confirm the tool exists in `resources/` before writing.
- Set `selector.matchNames: ["<name>"]` where `<name>` is the `name` field from the tool's `resource.json` — **not** the folder name under `resources/`.
- Note: custom guardrails (type `"Custom"` in catalog) also only support Tool scope.

### Step 4 — Generate Config Blocks

For each recommended guardrail, use the catalog `examples[].config` as the template. Map it to `agent.json` format using `guardrails.md` for the exact JSON shape (discriminators, UUID, PascalCase scopes, `$`-prefixed fields).

> Read [guardrails.md](guardrails.md) before writing any guardrail JSON. The `$guardrailType`, `$parameterType`, `$actionType`, `$ruleType`, and `$selectorType` discriminators cannot be guessed — they are specified there.

For parameters, use the `Parameters` array from the matching guardrails list entry to confirm correctness — see the [Correctness Check](#correctness-check) table in Validate Mode for the exact rules. Apply the same checks when generating config to avoid writing invalid parameters from the start.

Generate a fresh UUID for each guardrail `id`.

### Step 5 — Apply and Validate

Write the new guardrail blocks to `agent.json`'s `guardrails[]` array. Then run:

```bash
uip agent validate "<AgentName>" --output json
```

Report to the user:
- What was added (by name)
- Why it was recommended (cite the catalog's `when_to_use` or a specific `use_cases` item that matched the agent's context)
- What scope and action were chosen and why (cite `AllowedScopes` from the guardrails list or `when_not_to_use` from the catalog if relevant)
- What parameters were set and their meaning

---

## Validate Mode

Use when the agent already has guardrails and the user asks whether they are correctly configured or appropriate.

**Before any validation, run both CLI commands from Step 0** (catalog with cache, guardrails list without cache). The guardrails list output is the primary source of truth for correctness validation — it contains each validator's parameter definitions including valid types, options, and key sources.

For each existing guardrail in `agent.json`'s `guardrails[]`:

### Correctness Check

Run `uip agent guardrails list --output json` (from Step 0) and find the matching validator by `Validator` name. The `Parameters` array is the authoritative source for all validation rules:

| CLI field | What to check |
|-----------|---------------|
| `Required: true` | Parameter must be present in `validatorParameters` |
| `Type` | Must match `$parameterType` — `"enum-list"`, `"map-enum"`, or `"number"` |
| `Options` | For `enum-list`: every value must be in this list; array must be non-empty |
| `KeySource` | For `map-enum`: keys must **exactly** match the values of the `Options`-sourced parameter named by `KeySource` — no extra, no missing keys |
| `Min` / `Max` | For `number` and `map-enum`: values must fall within this range |
| `Step` | For `number` and `map-enum`: values must be multiples of Step (e.g. Step=2, Min=0, Max=6 → valid values are 0, 2, 4, 6) |

Check that every parameter object has a `$parameterType` discriminator. Missing discriminators cause schema validation failures.

### Actionability Check

1. From the guardrails list output, read `AllowedScopes` for the validator.
2. Check that `selector.scopes` values are all in `AllowedScopes`. If any scope is not allowed, flag it.
3. From the catalog entry's `when_not_to_use` (if present), check whether the guardrail may be misapplied given the agent's actual context.
4. For Tool-scoped guardrails: does `selector.matchNames` list the intended tools? Do those tools exist in `resources/`?

### Relevance Check

1. Read the catalog entry's `when_not_to_use` (from the catalog cache).
2. Compare against the agent's current context (system prompt, schemas, tools).
3. If the agent matches a `when_not_to_use` condition, flag the guardrail as potentially misapplied and explain why.

### Report and Fix

Report per guardrail:
- **OK** — no issues found
- **Correctness issue** — describe the problem (e.g., "entityThresholds has key 'Sexual' but 'Sexual' is not in entities list — KeySource says keys must match the entities parameter's values") and the fix
- **Actionability issue** — describe the problem (e.g., "'Agent' is in selector.scopes but AllowedScopes for this validator is ['Llm', 'Tool'] — 'Agent' is not allowed; change scope to 'Llm' or 'Tool'") and the fix
- **Relevance issue** — describe why the guardrail may not be appropriate and what to consider instead

If the user asks to fix identified issues: apply corrections to `agent.json` and run `uip agent validate` again to confirm.

---

## Critical Rules

1. **Always fetch catalog first** (use cache if fresh); **always fetch guardrails list second** (no cache). Both are required before any analysis.
2. **If `GuardrailCatalogUnavailable`** → surface the message and stop. Do not fall back to guessing or hardcoded recommendations.
3. **Only recommend `Available` validators**. Mention `Unauthorised` ones to the user so they can contact their administrator.
4. **Every recommendation must cite** the catalog entry's `when_to_use` or a specific `use_cases` item that matched the agent's context. Do not recommend a guardrail without explaining why it applies.
5. **For Tool scope**: verify the tool exists in `resources/` before writing `matchNames`. If the agent has no tool resources, do not add a Tool-scoped guardrail.
6. **Correctness validation uses `uip agent guardrails list` output** — `Parameters[].Type`, `Options`, `KeySource`, `Min`, `Max`, `Step` are the authoritative source for all parameter rules. Do not hardcode validator-specific knowledge.
7. **The cache file is `.guardrails-catalog-cache.json`** in the working directory. Add it to `.gitignore` if one exists.
8. **Do not create separate guardrails per scope** — combine multiple scopes into a single guardrail's `scopes` array.
9. **All map-enum keys must exactly match the corresponding enum-list values** — no extra or missing keys. This is the most common correctness error.
10. **Read [guardrails.md](guardrails.md) before writing any JSON** — discriminator fields, PascalCase constraints, and parameter shapes are specified there and cannot be safely inferred.

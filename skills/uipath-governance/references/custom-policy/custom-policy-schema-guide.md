# Custom Policy — Rego Authoring Reference

Single source of truth for the Rego file format, OPA METADATA annotations, the Rego input shape at each hook, common Rego patterns, and what can't be expressed in the current runtime.

> **Verdicts are always recorded in the audit trail.** In enforce mode, a deny verdict raises a `GovernanceBlockException` and blocks the agent run. In audit mode, the verdict is logged but the run continues. Enforcement mode is a runtime configuration — not controlled by the Rego file itself.

---

## Rego File Format (`--file` format)

The `--file` argument for `create` and `update` must be a plain `.rego` file. The server extracts all policy metadata from **OPA METADATA annotations** embedded directly in the Rego source — no separate JSON envelope is needed.

Submission pipeline: `regal lint` → `opa inspect --annotations` → `validateNameMatchesPackage` → store. A file that fails any step is rejected with a descriptive error.

---

## OPA METADATA Annotations

### Package-level annotation (required)

Placed immediately before the `package` declaration. Declares the policy identity.

```rego
# METADATA
# title: block_ssn_in_prompts
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
package policy.block_ssn_in_prompts
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | **yes** | Policy name. **Must exactly match the package suffix** (e.g. `block_ssn_in_prompts` for `package policy.block_ssn_in_prompts`). Used as the DB policy name and must be unique within the org partition. |
| `custom.version` | no | Free-form version string (default: `"1.0"`). |
| `custom.hooks` | **yes** | Array of lifecycle hooks this policy fires on. Only `[a-zA-Z0-9_-]` characters allowed. |

**Package naming:** `package policy.<snake_case_name>` — one package per file, no nesting.

**Title constraint:** `title` and the package suffix must be **identical strings**. `"Block SSN In Prompts"` does NOT match `block_ssn_in_prompts` — the server rejects it with `metadata-name-package-mismatch`.

### Rule-level annotation (one per deny/allow rule)

Placed immediately before the rule definition.

```rego
# METADATA
# title: BLOCK_SSN-ssn-in-prompt
# description: SSN pattern detected in model input.
# custom:
#   priority: 80
deny_rules contains "BLOCK_SSN-ssn-in-prompt" if {
    input.hook == "before_model"
    regex.match(`\b\d{3}-\d{2}-\d{4}\b`, json.marshal(input.model_input))
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | **yes** | Rule ID. Must match the string in `deny_rules contains "<ID>"` exactly. |
| `description` | no | Message shown in the audit trail for this verdict. Defaults to the rule ID if omitted. |
| `custom.priority` | no | Evaluation priority (higher = first). Default `0`. |

---

## Regal Lint Rules

The server runs `regal lint` with two rules suppressed; everything else is active at the default level.

| Rule | Status | Reason |
|------|--------|--------|
| `idiomatic/directory-package-mismatch` | **ignored** | Policies are compiled in ephemeral temp dirs — no on-disk project structure to mirror. |
| `performance/non-loop-expression` | **ignored** | `deny_rules contains "RULE-id" if { ... }` is the canonical pattern; the ID is intentionally a constant string, not a loop variable. |
| `bugs/constant-condition` | **active** | Do NOT write `if false` or `if { false }` in your policy — the server rejects it. |

**Do NOT include sentinel lines** (`deny_rules contains "__sentinel__" if { false }`) in user-authored policies. The server's merge rego adds them automatically. Including them triggers the active `constant-condition` rule.

**`input.hook` guards are optional.** Each WASM is compiled for a specific hook at bundle time, so `input.hook` is already scoped — adding a guard is redundant but harmless. Examples in this guide include them for clarity.

**Use `==` for single-value hook checks**, not `in {single}`:
```rego
# ✓ correct
input.hook == "before_model"

# ✓ correct for multiple hooks
input.hook in {"before_model", "after_model"}

# ✗ regal flags this — use == for single values
input.hook in {"before_model"}
```

---

## Hook Input Reference

All fields available in `input` when Rego is evaluated. Fields not populated at a given hook are `null` — always null-guard before using.

| Field | Type | Populated at hooks |
|-------|------|-------------------|
| `input.hook` | string | all |
| `input.agent_name` | string | all |
| `input.ring` | string | all |
| `input.session_state.tool_calls` | int | all |
| `input.session_state.llm_calls` | int | all |
| `input.agent_input` | any | `before_agent` |
| `input.agent_output` | any | `after_agent` |
| `input.model_input` | any | `before_model`, `after_model` |
| `input.model_output` | any | `after_model` |
| `input.model_name` | string | `before_model`, `after_model` |
| `input.messages` | array | `before_model`, `after_model` |
| `input.tool_name` | string | `tool_call`, `after_tool` |
| `input.tool_args` | any | `tool_call` |
| `input.tool_result` | any | `after_tool` |

**Pre-computed features** — available in `input.features` when the policy declares them in `custom.required_features`. Only features listed are computed; omit what you don't need.

**Text statistics**

| Feature | Type | Description |
|---------|------|-------------|
| `word_count` | int | Whitespace-separated token count of the primary content field |
| `char_count` | int | Character count of the primary content field |
| `shannon_entropy` | float | Shannon entropy (bits/symbol) — English prose ~3.5–4.5; binary noise ~8 |
| `vader_compound` | float | VADER sentiment compound score (-1.0 to 1.0); negative = negative sentiment |

**Encoding integrity**

| Feature | Type | Description |
|---------|------|-------------|
| `encoding_concern_events` | int | Raw count of encoding corruption events (U+FFFD, `â€œ`, `\xHH`, mojibake bigrams) |
| `encoding_concern_ratio` | float | Weighted corruption density (0.0–1.0); threshold > 0.05 is a strong signal |

**Incident detection**

| Feature | Type | Description |
|---------|------|-------------|
| `incident_categories` | `dict[str, bool]` | Keyed by category: `safety_refusal`, `tool_failure`, `auth_failure`, `quota_exceeded`, `hallucination` |

Usage: `input.features.incident_categories.safety_refusal == true`

**Commitment language**

| Feature | Type | Description |
|---------|------|-------------|
| `commitment_verb` | bool | True if commitment verb or SOW marker found (will deliver, guarantee, fixed price, …) |
| `commitment_amount` | bool | True if currency-anchored amount found ($500, 200 EUR, …) |
| `commitment_deadline` | bool | True if deadline phrase found (within 3 days, by tomorrow, …) |

Declare features in the package annotation:

```rego
# METADATA
# title: my_policy
# custom:
#   hooks:
#   - before_model
#   required_features:
#   - word_count
#   - vader_compound
#   - commitment_verb
#   - incident_categories
package policy.my_policy
```

---

## Common Rego Patterns

### 1. Regex match on model input

```rego
# METADATA
# title: block_ssn_in_prompts
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
package policy.block_ssn_in_prompts

# METADATA
# title: BLOCK_SSN-ssn-in-prompt
# description: SSN pattern detected in model input.
# custom:
#   priority: 80
deny_rules contains "BLOCK_SSN-ssn-in-prompt" if {
    input.hook == "before_model"
    regex.match(`\b\d{3}-\d{2}-\d{4}\b`, json.marshal(input.model_input))
}
```

> `input.model_input` may be a string or a structured object — always use `json.marshal()` before regex matching to handle both cases safely.

---

### 2. Model allowlist

```rego
# METADATA
# title: approved_models_only
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
package policy.approved_models_only

allowed_models := {"gpt-4o", "claude-sonnet-4-6"}

# METADATA
# title: APPROVED_MODELS-model-approval
# description: Model not in approved list.
# custom:
#   priority: 90
deny_rules contains "APPROVED_MODELS-model-approval" if {
    input.hook == "before_model"
    input.model_name != ""
    not allowed_models[input.model_name]
}
```

---

### 3. Tool allowlist

```rego
# METADATA
# title: approved_tools_only
# custom:
#   version: "1.0"
#   hooks:
#   - tool_call
package policy.approved_tools_only

allowed_tools := {"search", "calculator", "send_email"}

# METADATA
# title: APPROVED_TOOLS-tool-allowlist
# description: Tool not in approved list.
# custom:
#   priority: 85
deny_rules contains "APPROVED_TOOLS-tool-allowlist" if {
    input.hook == "tool_call"
    input.tool_name != ""
    not allowed_tools[input.tool_name]
}
```

---

### 4. Session tool-call budget

```rego
# METADATA
# title: tool_call_budget
# custom:
#   version: "1.0"
#   hooks:
#   - tool_call
package policy.tool_call_budget

# METADATA
# title: TOOL_BUDGET-session-limit
# description: Session tool call budget exceeded.
# custom:
#   priority: 75
deny_rules contains "TOOL_BUDGET-session-limit" if {
    input.hook == "tool_call"
    input.session_state.tool_calls >= 20
}
```

---

### 5. Scope to a specific agent or ring

```rego
# METADATA
# title: production_finance_model_guard
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
package policy.production_finance_model_guard

allowed_models := {"gpt-4o", "claude-sonnet-4-6"}

# METADATA
# title: FINANCE_GUARD-model-approval
# description: Model not approved for finance agents in production.
# custom:
#   priority: 90
deny_rules contains "FINANCE_GUARD-model-approval" if {
    input.hook == "before_model"
    input.ring == "production"
    input.agent_name == "finance-agent"
    input.model_name != ""
    not allowed_models[input.model_name]
}
```

Omit `input.ring` or `input.agent_name` conditions to apply the rule to all agents on the tenant.

### 6. Pre-computed feature — commitment language detection

```rego
# METADATA
# title: commitment_language_guard
# custom:
#   version: "1.0"
#   hooks:
#   - after_model
#   required_features:
#   - commitment_verb
#   - commitment_amount
package policy.commitment_language_guard

# METADATA
# title: COMMIT_GUARD-financial-commitment
# description: Model output contains a financial commitment (verb + amount).
# custom:
#   priority: 85
deny_rules contains "COMMIT_GUARD-financial-commitment" if {
    input.hook == "after_model"
    input.features.commitment_verb == true
    input.features.commitment_amount == true
}
```

### 7. Pre-computed feature — incident detection

```rego
# METADATA
# title: safety_refusal_audit
# custom:
#   version: "1.0"
#   hooks:
#   - after_model
#   required_features:
#   - incident_categories
package policy.safety_refusal_audit

# METADATA
# title: SAFETY_AUDIT-refusal-detected
# description: Model issued a safety refusal response.
# custom:
#   priority: 30
deny_rules contains "SAFETY_AUDIT-refusal-detected" if {
    input.hook == "after_model"
    input.features.incident_categories.safety_refusal == true
}
```

### 8. Pre-computed feature — encoding integrity

```rego
# METADATA
# title: encoding_integrity_guard
# custom:
#   version: "1.0"
#   hooks:
#   - after_model
#   - after_tool
#   required_features:
#   - encoding_concern_ratio
#   - encoding_concern_events
package policy.encoding_integrity_guard

# METADATA
# title: ENCODING_GUARD-corruption-detected
# description: Output contains significant encoding corruption (mojibake or replacement characters).
# custom:
#   priority: 70
deny_rules contains "ENCODING_GUARD-corruption-detected" if {
    input.hook in {"after_model", "after_tool"}
    input.features.encoding_concern_events >= 3
}
```

---

## What Can't Be Expressed

The following rule types are outside the current `input.*` surface. Refuse these requests explicitly — do not approximate:

| Requested rule | Why it can't be expressed | Suggest instead |
|---------------|--------------------------|-----------------|
| User / caller identity | No user or group fields in `input` | Access ToolUsePolicy (`uip gov access-policy`) |
| Folder or tenant metadata | Not in `input` | AOps product policy (`uip gov aops-policy`) |
| Arbitrary HTTP calls or external lookups | WASM runs without network access | — |
| Persistent cross-session counters | `session_state` resets per run | — |
| File or environment access | Not available in WASM evaluation context | — |
| Semantic / intent checks (e.g. "detect hostile tone") | No general NLP available; use `vader_compound` for sentiment, `incident_categories` for known incident types | Declare the feature in `required_features` |
| Per-tool argument inspection | `tool_args` is available but no structured schema per tool | Use `tool_call` + regex on serialized args if pattern is known |

When refusing: name the missing field or capability and suggest the correct governance layer if one exists.

## Runtime Behavior Notes

**Fail-open:** If the governance server or CDN is unreachable at agent startup, the runtime falls back to the last cached WASM bundles on disk. If no cache exists (first ever startup with no connectivity), the Rego evaluator is skipped entirely and the agent runs without custom policies. A warning is logged. This is intentional — governance infrastructure outages should not take down agent operations.

**Policy changes take effect at the next run boundary**, not mid-run. A background thread refreshes bundles every 30 s (`UIPATH_GOVERNANCE_BUNDLE_REFRESH_SECONDS` to override), but a running agent is never interrupted.

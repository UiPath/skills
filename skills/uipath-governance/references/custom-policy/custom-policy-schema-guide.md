# Custom Policy — Rego Authoring Reference

Single source of truth for the Rego file format, OPA METADATA annotations, the Rego input shape at each hook, common Rego patterns, and what can't be expressed in the current runtime.

> **Audit mode only.** All rule verdicts (allow/deny) are recorded in the audit trail. The runtime does not yet stop or interrupt agent actions when a deny verdict fires. Be explicit with users: an active policy means its verdicts appear in audit logs, not that matching actions are blocked.

---

## Rego File Format (`--file` format)

The `--file` argument for `create` and `update` must be a plain `.rego` file. The server extracts all policy metadata from **OPA METADATA annotations** embedded directly in the Rego source — no separate JSON envelope is needed.

The server runs `opa inspect --annotations` on the submitted file to extract name, version, hooks, and rule messages/priorities. A submission missing the required package-level annotation is rejected with a descriptive error.

---

## OPA METADATA Annotations

### Package-level annotation (required)

Placed immediately before the `package` declaration. Declares the policy identity.

```rego
# METADATA
# title: My Policy
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
#   - after_model
package policy.my_policy
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | **yes** | Policy display name. Must be unique within the tenant. |
| `custom.version` | no | Free-form version string (default: `"1.0"`). |
| `custom.hooks` | **yes** | Array of lifecycle hooks this policy fires on. Controls which hook WASMs are recompiled. |

### Rule-level annotation (one per deny/allow rule)

Placed immediately before the rule definition. Declares the audit message and evaluation priority.

```rego
# METADATA
# title: MY_POLICY-model-approval
# description: Model not in approved list.
# custom:
#   priority: 90
deny_rules contains "MY_POLICY-model-approval" if {
    input.hook in {"before_model"}
    input.model_name != ""
    not allowed_models[input.model_name]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | **yes** | Rule ID. Must match the string in `deny_rules contains "<ID>"` exactly. |
| `description` | no | Message shown in the audit trail for this verdict. Defaults to the rule ID if omitted. |
| `custom.priority` | no | Evaluation priority (higher = first). Default `0`. |

**Constraint:** `title` in the annotation must exactly match the string literal used in `deny_rules`/`allow_rules`. The server enforces this at compile time.

---

## Package Naming and Required Structure

```rego
package policy.<snake_case_name>
```

Use the policy name lowercased with spaces replaced by underscores. One package per file.

Every policy **must** follow the `deny_rules` set pattern — NOT a `deny` boolean. The server's merge file aggregates across all active policies using:

```rego
deny_rules contains r if data.policy.<name>.deny_rules[r]
```

A policy that defines `deny if { ... }` (boolean) is a **silent no-op** — it contributes nothing to the merged bundle and produces no audit output.

**Required boilerplate in every policy:**

```rego
# Sentinel lines — required so the merge file sees a non-empty set definition
deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false
```

Rule ID naming: `<POLICY-PREFIX>-<description>` (e.g. `MY_POLICY-model-approval`). Must be unique within the policy and must match the annotation `title` exactly.

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
| `encoding_concern_events` | int | Raw count of encoding corruption events (U+FFFD, `�`, `\xHH`, mojibake bigrams) |
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

Declare features in the package annotation to have them pre-computed before evaluation:

```rego
# METADATA
# title: My Policy
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
# title: Block SSN In Prompts
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
package policy.block_ssn_in_prompts

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

# METADATA
# title: BLOCK_SSN-ssn-in-prompt
# description: SSN pattern detected in model input.
# custom:
#   priority: 80
deny_rules contains "BLOCK_SSN-ssn-in-prompt" if {
    input.hook in {"before_model"}
    regex.match(`\b\d{3}-\d{2}-\d{4}\b`, json.marshal(input.model_input))
}
```

> `input.model_input` may be a string or a structured object — always use `json.marshal()` before regex matching to handle both cases safely.

---

### 2. Model allowlist

```rego
# METADATA
# title: Approved Models Only
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
package policy.approved_models_only

allowed_models := {"gpt-4o", "claude-sonnet-4-6"}

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

# METADATA
# title: APPROVED_MODELS-model-approval
# description: Model not in approved list.
# custom:
#   priority: 90
deny_rules contains "APPROVED_MODELS-model-approval" if {
    input.hook in {"before_model"}
    input.model_name != ""
    not allowed_models[input.model_name]
}
```

---

### 3. Tool allowlist

```rego
# METADATA
# title: Approved Tools Only
# custom:
#   version: "1.0"
#   hooks:
#   - tool_call
package policy.approved_tools_only

allowed_tools := {"search", "calculator", "send_email"}

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

# METADATA
# title: APPROVED_TOOLS-tool-allowlist
# description: Tool not in approved list.
# custom:
#   priority: 85
deny_rules contains "APPROVED_TOOLS-tool-allowlist" if {
    input.hook in {"tool_call"}
    input.tool_name != ""
    not allowed_tools[input.tool_name]
}
```

---

### 4. Session tool-call budget

```rego
# METADATA
# title: Tool Call Budget
# custom:
#   version: "1.0"
#   hooks:
#   - tool_call
package policy.tool_call_budget

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

# METADATA
# title: TOOL_BUDGET-session-limit
# description: Session tool call budget exceeded.
# custom:
#   priority: 75
deny_rules contains "TOOL_BUDGET-session-limit" if {
    input.hook in {"tool_call"}
    input.session_state.tool_calls >= 20
}
```

---

### 5. Scope to a specific agent or ring

```rego
# METADATA
# title: Production Finance Model Guard
# custom:
#   version: "1.0"
#   hooks:
#   - before_model
package policy.production_finance_model_guard

allowed_models := {"gpt-4o", "claude-sonnet-4-6"}

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

# METADATA
# title: FINANCE_GUARD-model-approval
# description: Model not approved for finance agents in production.
# custom:
#   priority: 90
deny_rules contains "FINANCE_GUARD-model-approval" if {
    input.hook in {"before_model"}
    input.ring == "production"
    input.agent_name == "finance-agent"
    input.model_name != ""
    not allowed_models[input.model_name]
}
```

Omit `input.ring` or `input.agent_name` conditions to apply the rule to all agents on the tenant.

### 6. Pre-computed feature — commitment language detection

Flag model output that makes financial or delivery commitments:

```rego
# METADATA
# title: Commitment Language Guard
# custom:
#   version: "1.0"
#   hooks:
#   - after_model
#   required_features:
#   - commitment_verb
#   - commitment_amount
package policy.commitment_language_guard

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

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

Audit when the model refuses a request (safety refusal):

```rego
# METADATA
# title: Safety Refusal Audit
# custom:
#   version: "1.0"
#   hooks:
#   - after_model
#   required_features:
#   - incident_categories
package policy.safety_refusal_audit

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

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

Flag suspicious output with encoding corruption (e.g. garbled binary data):

```rego
# METADATA
# title: Encoding Integrity Guard
# custom:
#   version: "1.0"
#   hooks:
#   - after_model
#   - after_tool
#   required_features:
#   - encoding_concern_ratio
#   - encoding_concern_events
package policy.encoding_integrity_guard

deny_rules  contains "__sentinel__" if false
allow_rules contains "__sentinel__" if false

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

## Regal Lint Rules

> Guidelines will be added here. The server enforces whatever Regal config is active at submission time — check this section before submitting.

*(empty — populated in a future update)*

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

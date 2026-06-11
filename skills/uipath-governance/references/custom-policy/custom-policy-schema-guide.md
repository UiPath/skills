# Custom Policy — Rego Authoring Reference

Single source of truth for the JSON policy file format, the Rego input shape at each hook, common Rego patterns, and what can't be expressed in the current runtime.

---

## JSON Envelope (`--file` format)

The `--file` argument for `create` and `update` must be a JSON file:

```json
{
  "rego": "package policy.my_policy\n\ndefault deny = false\n\ndeny if {\n    input.hook == \"before_model\"\n    input.model_name == \"forbidden-model\"\n}",
  "metadata": {
    "name": "My Policy",
    "version": "1.0",
    "hooks": ["before_model"],
    "rules": [
      { "id": "__POLICY_ID__/RULE-1", "message": "Forbidden model used", "priority": 80 }
    ]
  }
}
```

Constraints:

- `rego` — full Rego source. Must pass Regal lint or the request is rejected.
- `metadata.name` — must be unique within the tenant. Duplicate name returns an error.
- `metadata.hooks` — controls which hook WASMs are recompiled. List only hooks the Rego actually fires on.
- `metadata.rules[].id` — must follow `{policyId}/RULE-N` format. Use `__POLICY_ID__/RULE-1` as a placeholder at authoring time. Replace with the real `policyId` returned by `create` in any copy you keep locally.

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

---

## Package Naming

```rego
package policy.<snake_case_name>
```

Use the policy name lowercased with spaces replaced by underscores. One package per file.

---

## Common Rego Patterns

### 1. Regex match on model input

```rego
package policy.block_ssn_in_prompts

default deny = false

deny if {
    input.hook == "before_model"
    regex.match(`\b\d{3}-\d{2}-\d{4}\b`, input.model_input)
}
```

Metadata hooks: `["before_model"]`

---

### 2. Model allowlist

```rego
package policy.approved_models_only

default deny = false

allowed_models := {"gpt-4o", "claude-sonnet-4-6"}

deny if {
    input.hook == "before_model"
    not allowed_models[input.model_name]
}
```

Metadata hooks: `["before_model"]`

---

### 3. Tool allowlist

```rego
package policy.approved_tools_only

default deny = false

allowed_tools := {"search", "calculator", "send_email"}

deny if {
    input.hook == "tool_call"
    not allowed_tools[input.tool_name]
}
```

Metadata hooks: `["tool_call"]`

---

### 4. Session tool-call budget

```rego
package policy.tool_call_budget

default deny = false

deny if {
    input.hook == "tool_call"
    input.session_state.tool_calls >= 20
}
```

Metadata hooks: `["tool_call"]`

---

### 5. Scope to specific agent or ring

Add conditions to any pattern to limit it to a specific agent name or deployment ring:

```rego
deny if {
    input.hook == "before_model"
    input.ring == "production"
    input.agent_name == "finance-agent"
    not allowed_models[input.model_name]
}
```

Omit the filter to apply the rule to all agents on the tenant.

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
| Semantic / intent checks (e.g. "detect hostile tone") | No NLP check type in current runtime | — |
| Per-tool argument inspection | `tool_args` is available but no structured schema per tool | Use `tool_call` + regex on serialized args if pattern is known |

When refusing: name the missing field or capability and suggest the correct governance layer if one exists.

> **Audit mode only.** All rule verdicts (allow/deny) are recorded in the audit trail. The runtime does not yet stop or interrupt agent actions when a deny verdict fires. Be explicit with users: an active policy means its verdicts appear in audit logs, not that matching actions are blocked.

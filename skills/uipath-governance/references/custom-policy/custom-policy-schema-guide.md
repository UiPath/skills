# Custom Policy YAML Schema (v1)

> **Schema is evolving.** This file is the single source of truth for the v1 customer-facing YAML format. Update here when the schema changes — the overview guide and SKILL.md reference this file.

Customers author policies in YAML. The server compiles YAML → Rego → WASM. Customers never write Rego directly.

> **Audit mode only.** All rule verdicts (allow/deny) are recorded in the agent's audit trail. The runtime does not yet stop or interrupt agent actions when a deny verdict fires — enforcement is coming in a future release. When authoring policies, make clear to users that a `deny` rule means "this will be flagged in audit" not "this will be blocked."

## Not Yet Implemented

Tell users plainly if they ask for any of the following — do not attempt to approximate them:

- **Enforcement / blocking** — deny verdicts are audit-only; the agent is not stopped or interrupted.
- **Semantic / intent-based checks** — e.g. "flag hostile tone", "detect jailbreak attempts", "check if output is factually correct". No natural-language reasoning check type exists in v1.
- **Output length limits** — no check type for response token count or character length.
- **Rate limiting per user or group** — no per-identity quota check type in v1.
- **Cross-session state** — rules can only reference state within the current run (`session.tool_calls`). No persistent cross-run counters.
- **Dynamic data lookups** — rules cannot call external APIs or query databases at evaluation time.
- **Per-tool argument inspection** — `tool_call` hook exposes the tool name; inspecting specific argument values is not a v1 check type.

This list grows as the schema evolves. Add entries here when a user requests something unsupported.

---

## Top-Level Structure

```yaml
policy:
  name: <string>         # required — unique within tenant
  description: <string>  # optional
  version: "<string>"    # required — e.g. "1.0"
  scope:
    agent_tag: [<string>, ...]   # required — target agents with ANY of these tags
    hook: [<hook_name>, ...]     # required — lifecycle hooks this policy fires on
  rules:
    - <rule>
    - <rule>
```

### Valid `hook` values

| Hook | When it fires |
|------|--------------|
| `before_agent` | Before the agent run starts (agent input available) |
| `after_agent` | After the agent run ends (agent output available) |
| `before_model` | Before each LLM call (model input / prompt available) |
| `after_model` | After each LLM call (model output available) |
| `tool_call` | Before each tool invocation (tool name + args available) |
| `after_tool` | After each tool invocation (tool result available) |

---

## Rule Structure

```yaml
- id: <string>          # required — unique within policy, used in audit records
  name: <string>        # required — human-readable label
  when:
    <field>:
      <check_type>: <value>
  action: allow | deny  # required — verdict recorded in audit trail; does not yet stop agent actions
  priority: <integer>   # required — higher number = evaluated first; higher-priority allow beats lower-priority deny
  message: <string>     # optional — surfaced in audit records when the rule fires
```

### Conflict resolution

Most-restrictive by default: if any rule across any loaded policy returns `deny` for a given hook, that verdict wins — regardless of other rules allowing. `priority` is used within the same pack to order rule evaluation; it does not override cross-pack deny semantics. All verdicts are recorded in the audit trail; the agent is not yet stopped when a deny verdict fires.

---

## Check Types (v1)

### `matches` — Regex pattern match

Fires when the field value matches the regular expression.

```yaml
when:
  model_input:
    matches: '\b\d{3}-\d{2}-\d{4}\b'   # SSN pattern
```

Available fields: `model_input`, `model_output`, `agent_input`, `agent_output`, `tool_result`.

---

### `contains_pii` — PII entity detection

Fires when the field contains any of the listed PII entity types. Entity names follow [Microsoft Presidio standards](https://microsoft.github.io/presidio/supported_entities/).

```yaml
when:
  model_input:
    contains_pii: [EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD, LOCATION]
```

Available fields: `model_input`, `model_output`, `agent_input`, `agent_output`.

Common Presidio entity names: `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `LOCATION`, `PERSON`, `US_SSN`, `IBAN_CODE`, `IP_ADDRESS`, `NRP`, `DATE_TIME`.

---

### `tool_name.allowed_only` — Tool allowlist

Fires on `tool_call` hook when the called tool is NOT in the allowed list.

```yaml
when:
  tool_name:
    allowed_only: [search_web, read_file, send_email]
```

Only valid on `hook: [tool_call]`. When a tool outside the list is called, a deny verdict is recorded in the audit trail.

---

### `session.tool_calls.max` — Tool call budget

Fires when the cumulative tool call count for the session exceeds the threshold.

```yaml
when:
  session:
    tool_calls:
      max: 20
```

Evaluated on every `tool_call` hook. When the count reaches `max`, a deny verdict is recorded in the audit trail.

---

### `model_name.allowed` — Model allowlist / blocklist

Fires on `before_model` when the model identifier is not in the allowed list.

```yaml
when:
  model_name:
    allowed: [gpt-4o, claude-opus-4-7, claude-sonnet-4-6]
```

Model identifiers are the string the agent passes to the LLM gateway (e.g. `gpt-4o`, `claude-opus-4-7`). Match is exact.

---

## Worked Examples

### Example 1 — Audit SSN allowance and flag other PII

```yaml
policy:
  name: tax-agent-pii-guardrail
  description: Flag non-SSN PII in tax-filing agent prompts; allow SSN through.
  version: "1.0"
  scope:
    agent_tag: [tax-filing, finance]
    hook: [before_model, after_model]
  rules:
    - id: allow-ssn
      name: Allow SSN in tax context
      when:
        model_input:
          matches: '\b\d{3}-\d{2}-\d{4}\b'
      action: allow
      priority: 100
    - id: flag-other-pii
      name: Flag non-SSN PII
      when:
        model_input:
          contains_pii: [EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD, LOCATION]
      action: deny
      priority: 50
      message: "Non-SSN PII detected in prompt"
```

### Example 2 — Audit model usage and tool call volume

```yaml
policy:
  name: cost-control-guardrail
  description: Flag unapproved models and excess tool calls for audit.
  version: "1.0"
  scope:
    agent_tag: [internal]
    hook: [before_model, tool_call]
  rules:
    - id: approved-models
      name: Flag unapproved models
      when:
        model_name:
          allowed: [gpt-4o, claude-sonnet-4-6]
      action: deny
      priority: 80
      message: "Model not on the approved list"
    - id: tool-budget
      name: Flag when tool calls exceed 15
      when:
        session:
          tool_calls:
            max: 15
      action: deny
      priority: 70
      message: "Tool call budget exceeded"
```

---

## Authoring Checklist

- [ ] `policy.name` is unique within the tenant (`list` to verify no collision)
- [ ] `scope.agent_tag` matches the tags the target agents declare at startup
- [ ] `scope.hook` lists only hooks relevant to the check types used (e.g. `tool_name.allowed_only` requires `tool_call`)
- [ ] Every rule has a unique `id` (used in audit records)
- [ ] `priority` is set intentionally — allow rules that must override deny rules have a higher priority number
- [ ] `contains_pii` entity names match Presidio spelling exactly (UPPER_SNAKE_CASE)
- [ ] `model_name.allowed` values match the exact identifier string the agent uses at runtime

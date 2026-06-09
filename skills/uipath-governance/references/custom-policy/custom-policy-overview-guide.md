# Custom Policy (Branch C)

> **Branch C of `uipath-governance`.** The top-level [SKILL.md](../../SKILL.md) owns disambiguation — by the time you are reading this file, the branch is already chosen. This file owns the custom-policy-specific flow.

Runtime policy rules for UiPath agents, compiled to WASM and evaluated by the agent SDK at every lifecycle hook. Verdicts are recorded in the audit trail. Managed via `uip gov custom-policy`.

> **Audit mode only.** The current runtime records a verdict (allow/deny) for every rule evaluation. It does not yet stop or interrupt agent actions — enforcement is coming in a future release. Be explicit with users: a policy being active means its verdicts appear in audit logs, not that matching actions are blocked.

Two modes inside this branch:

| Mode | When | What happens |
|------|------|-------------|
| **Operate** | User references an existing policy by name/ID, or uses list/get/enable/disable/delete | Emit the matching CLI command |
| **Author** | User describes a new guardrail in natural language | Interview → YAML → offer to create via CLI |

---

## Critical Rules

1. **Tenant-scoped login is required.** Run `uip login --tenant <TENANT_NAME>` before any command. A user-scoped login returns `401` or silently hits the wrong tenant.
2. **Classify operate vs author before acting.** Do not run any CLI command until the mode is determined.
3. **Never fabricate policy IDs.** Always resolve policy names to IDs via `list` — never guess a GUID.
4. **For delete: always confirm.** Run `get`, show the policy summary, and ask for explicit user confirmation before running `delete`.
5. **For update: always get first.** Retrieve the current YAML via `get` and use it as the edit base — never start from scratch when updating.
6. **Author mode produces a file, then offers to create.** Write the YAML to a file in the session directory, show it to the user, and ask before running `create`.

---

## Pre-flight (both modes)

```bash
which uip && uip --version
uip login status --output json
```

If not installed: `npm install -g @uipath/uipcli`.
If not logged in (or login is user-scoped only): `uip login --tenant <TENANT_NAME>`.

---

## Operate Mode

Map the user's intent to a command from the table below. For commands that take a `<POLICY_ID>`, resolve it via `list` first if the user gave a name rather than a GUID.

**Custom policies** (`uip gov custom-policy`):

| Intent | Command |
|--------|---------|
| List custom policies | `uip gov custom-policy list --output json` |
| Get a policy's YAML | `uip gov custom-policy get <POLICY_ID> --output json` |
| Enable a custom policy | `uip gov custom-policy enable <POLICY_ID> --output json` |
| Disable a custom policy | `uip gov custom-policy disable <POLICY_ID> --output json` |
| Update a custom policy | Get current YAML → edit → `uip gov custom-policy update <POLICY_ID> --file <PATH> --output json` |
| Delete a custom policy | Get + confirm → `uip gov custom-policy delete <POLICY_ID> --output json` |
| Create from an existing file | `uip gov custom-policy create --file <PATH> --output json` |

### Resolve name → ID

For custom policies:
```bash
uip gov custom-policy list --output json
# Find entry where policyName matches user's input, extract policyId
```

---

## Author Mode

Goal: turn the user's natural-language description into a valid policy YAML file, then offer to upload it.

### Step 1 — Gather scope

Ask (or infer from context):

1. **Agent tags** — which agents does this policy target? (e.g. `tax-filing`, `internal`, `production`)
2. **Lifecycle hooks** — which events should the policy fire on? Offer the list: `before_agent`, `after_agent`, `before_model`, `after_model`, `tool_call`, `after_tool`. Match to the check type the user described.
3. **Policy name** — unique display name for the tenant.

### Step 2 — Build rules

For each guardrail the user described, determine the check type from [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) and fill in the rule fields:

| User says... | Check type | Hook |
|---|---|---|
| "flag emails / phone numbers / credit cards in prompts" | `contains_pii` | `before_model` or `after_model` |
| "match this pattern / regex" | `matches` | whichever hook exposes the field |
| "audit which tools the agent calls / flag calls outside this list" | `tool_name.allowed_only` | `tool_call` |
| "flag when tool calls exceed N per session" | `session.tool_calls.max` | `tool_call` |
| "audit model usage / flag calls to unapproved models" | `model_name.allowed` | `before_model` |

If the user's requested rule does not map to any of the v1 check types, tell them plainly: "That rule can't be expressed in the current v1 schema. The supported check types are: regex match, PII detection, tool allowlist, tool call budget, and model allowlist." Do not attempt to approximate it with an unsupported pattern.

Set `priority` so allow rules that must override deny rules have a higher number.

### Step 3 — Draft and validate

1. Compose the YAML following the schema in [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md).
2. Verify the authoring checklist at the bottom of that file.
3. Show the YAML to the user.

### Step 4 — Write file and offer create

```bash
# Write YAML to session file
cat > /tmp/custom-policy-draft.yaml << 'EOF'
<YAML_CONTENT>
EOF
```

Ask: "Ready to create this policy on the tenant? I'll run:
```bash
uip gov custom-policy create \
  --file /tmp/custom-policy-draft.yaml \
  --output json
```"

Run only after explicit confirmation. On success, show the returned `policyId` and confirm the policy is active (verdicts will appear in the audit trail at the next agent run). Remind the user that verdicts are currently recorded only — agent actions are not yet stopped by the policy.

### Author mode — common gaps

- **No agent tags supplied:** Ask "Which agent tag(s) should this policy target?" before drafting YAML.
- **Ambiguous hook:** If the user says "flag PII" without specifying input vs output, default to `[before_model, after_model]` and note the choice.
- **Unknown Presidio entity name:** Show the user the common names (`EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `LOCATION`, `PERSON`, `US_SSN`) and ask them to pick.
- **Model identifier unclear:** Ask for the exact model string the agent uses at runtime (e.g. `gpt-4o`, `claude-sonnet-4-6`).
- **Unsupported rule type:** If the user's guardrail can't be expressed with the five v1 check types, say so explicitly: "That rule isn't supported in the current schema." Do not approximate it or stay silent.

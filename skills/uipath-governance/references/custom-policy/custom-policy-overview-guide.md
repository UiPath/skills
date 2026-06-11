# Custom Policy (Branch C)

> **Branch C of `uipath-governance`.** The top-level [SKILL.md](../../SKILL.md) owns disambiguation — by the time you are reading this file, the branch is already chosen. This file owns the custom-policy-specific flow.

Runtime policy rules for UiPath agents, compiled to WASM and evaluated by the agent SDK at every lifecycle hook. Verdicts are recorded in the audit trail. Managed via `uip gov custom-policy`.

> **Audit mode only.** The current runtime records a verdict (allow/deny) for every rule evaluation. It does not yet stop or interrupt agent actions — enforcement is coming in a future release. Be explicit with users: a policy being active means its verdicts appear in audit logs, not that matching actions are blocked.

Two modes inside this branch:

| Mode | When | What happens |
|------|------|-------------|
| **Operate** | User references an existing policy by name/ID, or uses list/get/enable/disable/delete | Emit the matching CLI command |
| **Author** | User describes a new guardrail in natural language | Interview → Rego → JSON envelope → offer to create via CLI |

---

## Critical Rules

1. **Tenant-scoped login is required.** Run `uip login --tenant <TENANT_NAME>` before any command. A user-scoped login returns `401` or silently hits the wrong tenant.
2. **Classify operate vs author before acting.** Do not run any CLI command until the mode is determined.
3. **Never fabricate policy IDs.** Always resolve policy names to IDs via `list` — never guess a GUID.
4. **For delete: always confirm.** Run `get`, show the policy summary, and ask for explicit user confirmation before running `delete`.
5. **For update: always get first.** Retrieve the current Rego via `get` and use it as the edit base — never start from scratch when updating.
6. **Author mode produces a file, then offers to create.** Write the JSON envelope to a session file, show it to the user, and ask before running `create`.

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
| Get a policy's Rego | `uip gov custom-policy get <POLICY_ID> --output json` |
| Enable a custom policy | `uip gov custom-policy enable <POLICY_ID> --output json` |
| Disable a custom policy | `uip gov custom-policy disable <POLICY_ID> --output json` |
| Update a custom policy | Get current Rego → edit → `uip gov custom-policy update <POLICY_ID> --file <PATH> --output json` |
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

Goal: turn the user's natural-language description into a valid Rego policy, wrap it in the JSON envelope, then offer to upload it.

### Step 1 — Gather scope

Ask (or infer from context):

1. **Lifecycle hooks** — which events should the policy fire on? Options: `before_agent`, `after_agent`, `before_model`, `after_model`, `tool_call`, `after_tool`. Match to the check the user described.
2. **Agent name / ring** — optional. If the user wants to scope the policy to specific agents or deployment rings, note them for Rego conditions.
3. **Policy name** — unique display name for the tenant.

### Step 2 — Draft Rego

- Select patterns from [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) that match the user's request.
- Use `__POLICY_ID__` as a placeholder in all rule IDs (e.g. `__POLICY_ID__/RULE-1`). The server assigns the real `policyId` on create.
- If the request requires a field not in `input.*`, refuse explicitly: "That rule requires access to [X], which isn't available in the Rego input at any hook." Do not approximate with an unsupported field. See the "What Can't Be Expressed" section of [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) for the full list.

### Step 3 — Show Rego and confirm

Show the Rego to the user. Note: the server runs Regal lint on every create/update — if the submission is rejected, fix the lint error and retry.

### Step 4 — Write JSON and offer create

Write the JSON envelope to a session file:

```bash
cat > /tmp/custom-policy-draft.json << 'EOF'
<JSON_ENVELOPE_CONTENT>
EOF
```

Show the JSON to the user and ask: "Ready to create this policy on the tenant? I'll run:
```bash
uip gov custom-policy create \
  --file /tmp/custom-policy-draft.json \
  --output json
```"

Run only after explicit confirmation. On success:
- Show the returned `policyId`.
- Remind the user to replace `__POLICY_ID__` in any local copy they keep with the real `policyId`.
- Confirm the policy is active (verdicts will appear in the audit trail at the next agent run).
- Remind: verdicts are currently recorded only — agent actions are not yet stopped by the policy.

### Author mode — common gaps

| Gap | Resolution |
|-----|-----------|
| No hook specified | Default to `[before_model, after_model]`, note the choice to the user |
| Request uses a field not in `input.*` | Refuse explicitly, list available fields at the relevant hook from [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) |
| Model identifier unclear | Ask for the exact model string used at runtime (e.g. `gpt-4o`, `claude-sonnet-4-6`) |
| Agent name / ring not needed | Omit the filter condition — policy applies to all agents on the tenant |

# Custom Policy (Branch C)

> **Branch C of `uipath-governance`.** The top-level [SKILL.md](../../SKILL.md) owns disambiguation — by the time you are reading this file, the branch is already chosen. This file owns the custom-policy-specific flow.

Runtime policy rules for UiPath agents, compiled to WASM and evaluated by the agent SDK at every lifecycle hook. Verdicts are recorded in the audit trail. Managed via `uip gov custom-policy`.

> **Audit mode only.** The current runtime records a verdict (allow/deny) for every rule evaluation. It does not yet stop or interrupt agent actions — enforcement is coming in a future release. Be explicit with users: a policy being active means its verdicts appear in audit logs, not that matching actions are blocked.

> **Org-level storage, per-tenant activation.** Policies created with `create` are stored at the org level and must be explicitly enabled per tenant with `enable`.

Two modes inside this branch:

| Mode | When | What happens |
|------|------|-------------|
| **Operate** | User references an existing policy by name/ID, or uses list/get/enable/disable/delete | Emit the matching CLI command |
| **Author** | User describes a new guardrail in natural language | Interview → Rego → file → `create` → `enable` |

---

## Critical Rules

1. **Tenant-scoped login is required.** Run `uip login --tenant <TENANT_NAME>` before any command. A user-scoped login returns `401` or silently hits the wrong tenant.
2. **Classify operate vs author before acting.** Do not run any CLI command until the mode is determined.
3. **Never fabricate policy IDs.** Always resolve policy names to IDs via `list` — never guess a GUID.
4. **For delete: always confirm.** Run `list` to confirm the policy's `policyName` and `active` status, then ask for explicit user confirmation before running `delete`. Delete is hard — it removes the policy from all tenants.
5. **No update command.** To revise a policy: `get` the Rego source, edit it, `delete` the old policy, `create` the new one, then `enable`.
6. **Author mode produces a file, then offers to create + enable.** Write the `.rego` file, show it to the user, ask before running `create`, then offer `enable` after.

---

## Operate Mode

Map the user's intent to a command from the table below. For commands that take a `<POLICY_ID>`, resolve it via `list` first if the user gave a name rather than a GUID.

| Intent | Command |
|--------|---------|
| List agent policies | `uip gov custom-policy list --output json` |
| Get a policy's Rego | `uip gov custom-policy get <POLICY_ID> --output json` |
| Enable a policy for this tenant | `uip gov custom-policy enable <POLICY_ID> --output json` |
| Disable a policy for this tenant | `uip gov custom-policy disable <POLICY_ID> --output json` |
| Revise a policy | Get Rego → edit → delete old → create new → enable |
| Delete a policy (all tenants) | Confirm via list → `uip gov custom-policy delete <POLICY_ID> --output json` |
| Create from an existing file | `uip gov custom-policy create --file <PATH> --output json` → then `enable` |

### Resolve name → ID

```bash
uip gov custom-policy list --output json
# Find entry where policyName matches user's input, extract policyId
```

---

## Author Mode

Goal: turn the user's natural-language description into a valid Rego policy with embedded OPA METADATA annotations, create it org-wide, then enable it for the tenant.

### Step 1 — Gather scope

Ask (or infer from context):

1. **Lifecycle hooks** — which events should the policy fire on? Options: `before_agent`, `after_agent`, `before_model`, `after_model`, `tool_call`, `after_tool`, `memory_write`. Match to the check the user described.
2. **Agent name / ring** — optional. If the user wants to scope the policy to specific agents or deployment rings, note them for Rego conditions.
3. **Policy name** — unique display name for the org.

### Step 2 — Draft Rego

- Select patterns from [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) that match the user's request.
- Embed all metadata in OPA `# METADATA` annotations — package-level for name/version/hooks, rule-level for message/priority.
- Do NOT add `input.hook` guards in rule bodies — each hook WASM is scoped at compile time via the annotation's `hooks` list.
- If the request requires a field not in `input.*`, refuse explicitly: "That rule requires access to [X], which isn't available in the Rego input at any hook." See the "What Can't Be Expressed" section of [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) for the full list.

### Step 3 — Show Rego and confirm

Show the complete `.rego` file (including METADATA annotations) to the user. Note: the server runs Regal lint on every create — if the submission is rejected, fix the lint error and retry.

### Step 4 — Write .rego file and create

Write the Rego to a session file:

```bash
cat > /tmp/custom-policy-draft.rego << 'EOF'
<REGO_FILE_CONTENT>
EOF
```

Ask: "Ready to create this policy? I'll run:
```bash
uip gov custom-policy create \
  --file /tmp/custom-policy-draft.rego \
  --output json
```"

Run only after explicit confirmation. On success, show the returned `policyId`, then offer:

```bash
uip gov custom-policy enable <POLICY_ID> --output json
```

After enable:
- Confirm verdicts will appear in the audit trail at the next agent run.
- Remind: verdicts are currently recorded only — agent actions are not yet stopped by the policy.

### Author mode — common gaps

| Gap | Resolution |
|-----|-----------|
| No hook specified | Default to `[before_model, after_model]`, note the choice to the user |
| Request uses a field not in `input.*` | Refuse explicitly, list available fields at the relevant hook from [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) |
| Model identifier unclear | Ask for the exact model string used at runtime (e.g. `gpt-4o`, `claude-sonnet-4-6`) |
| Agent name / ring not needed | Omit the filter condition — policy applies to all agents on the org |
| Missing METADATA annotations | Add a `# METADATA` block before `package` with `title` and `custom.hooks`; add rule-level `# METADATA` blocks with `title` matching each rule ID |

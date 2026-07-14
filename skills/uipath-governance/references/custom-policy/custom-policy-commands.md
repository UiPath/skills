# uip gov custom-policy — CLI Command Reference

Single source of truth for every `uip gov custom-policy` subcommand, its flags, and its output shape. Use `--output json` for programmatic use.


> **Org-level storage, per-tenant activation.** `create` stores the policy org-wide but does NOT activate it. Run `enable` to activate for the current tenant.

---

## uip gov custom-policy list

List all agent policies for the org.

```bash
uip gov custom-policy list --output json
```

**Output:** Array of policy entries. Each entry has `policyId`, `policyName`, `policyVersion`, `source`, `active`, `createdAt`, `createdBy`, `updatedAt`.

`active` reflects activation status for the current tenant's login context.

---

## uip gov custom-policy get

Fetch the Rego source for an custom policy.

```bash
uip gov custom-policy get <POLICY_ID> --output json
```

**Output:** `policyId` and `regoSource` (full Rego string). Save to a `.rego` file if you need to revise it.

---

## uip gov custom-policy create

Upload a `.rego` file. Server validates the source, runs Regal lint, extracts OPA METADATA, and stores the policy org-wide. Does not activate — run `enable` after.

```bash
uip gov custom-policy create \
  --file <PATH_TO_REGO> \
  --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--file <PATH>` | yes | Path to the `.rego` file |

> `--file` must be a `.rego` file with valid OPA METADATA annotations. The server uses `opa inspect --annotations` to extract `title`, `hooks`, and rule `description`/`priority`. See [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) for the annotation format.

**Output:** `policyId` (GUID) and `policyName`. Policy is stored org-wide but **not yet active** — run `enable` to activate for the current tenant.

> **No update command.** To revise a policy: `get` the Rego source, edit it, `delete` the old policy, `create` the new one, then `enable`.

---

## uip gov custom-policy enable

Activate a policy for the current tenant. Idempotent.

```bash
uip gov custom-policy enable <POLICY_ID> --output json
```

The policy takes effect at the next agent poll.

---

## uip gov custom-policy disable

Deactivate a policy for the current tenant. Idempotent.

```bash
uip gov custom-policy disable <POLICY_ID> --output json
```

Running agents are not interrupted mid-run. The change takes effect at the next run boundary after the background refresh cycle.

---

## uip gov custom-policy delete

Hard-delete a policy from all tenants it was enabled on. Irreversible.

```bash
uip gov custom-policy delete <POLICY_ID> --output json
```

**Destructive — cannot be undone.** Always run `list` first, confirm the `policyName` and `active` status with the user before deleting.

**Output:** `Result: "Success"` on deletion.

---

## Common Options

| Option | Description |
|--------|-------------|
| `--output json` | Machine-readable output. Always pass when parsing output. |

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or missing | Surface auth error to user |
| `403 Forbidden` | Insufficient permissions | Surface auth error to user |
| `command not found: uip` | CLI not installed | `npm install -g @uipath/uipcli` |
| `Regal lint failed` | Rego violates lint rules | Fix the Rego against lint rules in [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) and resubmit |
| `missing package-level METADATA annotation` | No `# METADATA` block before `package` | Add required annotations — see [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) |
| `must declare at least one hook` | Package annotation has no `custom.hooks` array | Add `hooks:` to the package METADATA block |
| Policy active but audit trail empty | Agent has not polled yet | Wait for the background refresh interval, or restart the agent |

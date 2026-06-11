# uip gov custom-policy — CLI Command Reference

Single source of truth for every `uip gov custom-policy` subcommand, its flags, and its output shape. Use `--output json` for programmatic use.

> All commands require **tenant-scoped login**: `uip login --tenant <TENANT_NAME>`. A user-scoped login is not sufficient — commands will fail with `401` or `403`.

---

## uip gov custom-policy list

List all custom policies for the tenant (active and inactive).

```bash
uip gov custom-policy list --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--limit <N>` | no | Max results to return (default: server default) |
| `--offset <N>` | no | Pagination offset (default: 0) |

**Output:** Array of custom policy entries. Each entry has `policyId`, `policyName`, `policyVersion`, `active`, `createdAt`, `createdBy`, `updatedAt`.

---

## uip gov custom-policy get

Fetch the Rego source for a custom policy.

```bash
uip gov custom-policy get <POLICY_ID> --output json
```

Returns `403` for UiPath default policies. Always run before `update` to retrieve the current Rego.

**Output:** `Data` contains the Rego source string. Save it to a file to use as the update base.

---

## uip gov custom-policy create

Upload a YAML policy file. The server compiles it to WASM and stores both.

```bash
uip gov custom-policy create \
  --file <PATH_TO_YAML> \
  --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--file <PATH>` | yes | Path to the policy JSON file |

> `--file` must be a JSON file with `rego` (string) and `metadata` (object) fields — see [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) for the full envelope format. `metadata.rules[].id` must follow `{policyId}/RULE-N` format; use `__POLICY_ID__/RULE-1` as a placeholder at authoring time — the server assigns the real `policyId` on create.

**Output:** `Data` contains the new `policyId` (GUID) and `policyName`. Policies are created with `active: true` by default — they take effect at the next agent poll.

---

## uip gov custom-policy update

Upload a revised YAML file. The server recompiles to WASM and updates the stored bundle.

```bash
uip gov custom-policy update <POLICY_ID> \
  --file <PATH_TO_YAML> \
  --output json
```

Returns `403` for UiPath default policies. Always run `get` first to retrieve the current Rego before editing.

**Output:** `Data` contains `policyId` and updated metadata.

---

## uip gov custom-policy delete

Permanently remove a custom policy.

```bash
uip gov custom-policy delete <POLICY_ID> --output json
```

**Destructive — cannot be undone.** Always run `get` first and confirm with the user before deleting. Returns `403` for UiPath default policies.

**Output:** `Result: "Success"` on deletion.

---

## uip gov custom-policy enable

Activate a custom policy — sets `active=true`. Included in the next agent poll. Idempotent.

```bash
uip gov custom-policy enable <POLICY_ID> --output json
```

---

## uip gov custom-policy disable

Deactivate a custom policy — sets `active=false`. Excluded from the next agent poll. Idempotent.

```bash
uip gov custom-policy disable <POLICY_ID> --output json
```

Running agents are not interrupted mid-run. The change takes effect at the next run boundary after the agent's background refresh cycle.

---

## Common Options

| Option | Description |
|--------|-------------|
| `--login-validity <MINUTES>` | Override interactive-login token lifetime for this call |
| `--output json` | Machine-readable output. Always pass when parsing output. |

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or missing | Run `uip login --tenant <TENANT_NAME>` and retry |
| `command not found: uip` | CLI not installed | `npm install -g @uipath/uipcli` |
| `Regal lint failed` | Rego violates lint rules | Fix the Rego against lint rules in [`custom-policy-schema-guide.md`](./custom-policy-schema-guide.md) and resubmit |
| Policy active but audit trail empty | Agent has not polled yet | Wait for the background refresh interval, or restart the agent |

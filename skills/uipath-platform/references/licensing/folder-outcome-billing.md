# Folder Outcome Billing (Fully Loaded Transactions)

Read and change the outcome billing setting of an Orchestrator folder. Server-side the feature is called Fully Loaded Transactions (FLT); the CLI surface calls it outcome billing (`IsOutcomeBillingEnabled` in output, `--enabled` on input).

> For full option details, run `uip platform tenants folder-outcome-billing --help`.

---

## When to Use

- Checking whether outcome billing is turned on for a folder (`folder-outcome-billing get`)
- Enabling or disabling outcome billing on a folder (`folder-outcome-billing set`)
- Testing the round-trip on a tenant without touching shared folders

## Prerequisites

1. Authenticated — verify with `uip login status`; if not, ask the user to run `uip login` (interactive browser flow)
2. The **tenant id** (GUID) of the tenant that owns the folder — `uip login status` shows the current tenant, `uip login tenant list` lists `TenantName` + `TenantId`
3. The **folder key** (GUID) — from `uip or folders list --all`
4. Licensing authorization on the License Accountant for both commands (org admin, or an allow-listed licensing application)
5. For `set`: the organization holds the `Platform.FltEligible` entitlement. `get` works without it

---

## Commands

| Command | What it does |
|---------|--------------|
| `uip platform tenants folder-outcome-billing get <tenant-id> <folder-key>` | Read the setting: `Code: TenantFolderOutcomeBilling`, `Data: { FolderKey, IsOutcomeBillingEnabled }` |
| `uip platform tenants folder-outcome-billing set <tenant-id> <folder-key> --enabled <true\|false>` | Write the setting and return the configuration now in effect: `Code: TenantFolderOutcomeBillingSet` |

Both positional arguments are GUIDs. The setting is stored per (organization, tenant, folder key) and consumption charging reads it to decide how work in that folder is billed.

---

## Step 1: Resolve the Tenant Id and Folder Key

```bash
uip login status --output json                 # current tenant, or N/A
uip login tenant list --output json            # TenantName + TenantId (GUID)
uip login tenant set <tenant-name>             # select the tenant that owns the folder

uip or folders list --all --output json        # Key (GUID), Name, Path, Type for every folder
```

Useful `or folders list` filters: `--path <prefix>`, `--name <contains>`, `--type standard|solution|personal`, `--top-level`. Note the folder's `Key`, not its numeric `Id`.

## Step 2: Read the Current Setting

```bash
uip platform tenants folder-outcome-billing get <TENANT_ID> <FOLDER_KEY> --output json
```

```json
{
  "Result": "Success",
  "Code": "TenantFolderOutcomeBilling",
  "Data": {"FolderKey": "11111111-1111-1111-1111-111111111111", "IsOutcomeBillingEnabled": false}
}
```

## Step 3: Change It

```bash
uip platform tenants folder-outcome-billing set <TENANT_ID> <FOLDER_KEY> --enabled true --output json
```

```json
{
  "Result": "Success",
  "Code": "TenantFolderOutcomeBillingSet",
  "Data": {"FolderKey": "11111111-1111-1111-1111-111111111111", "IsOutcomeBillingEnabled": true}
}
```

`--enabled` is required and accepts only `true` or `false` (case-insensitive). Anything else fails with exit 1 **before any API call**.

## Step 4: Verify

Re-run Step 2 and confirm `IsOutcomeBillingEnabled` matches what was set. The write path round-trips: what was set is what the next read returns.

---

## Testing the Round-Trip Safely

Enabling outcome billing changes how a folder's executions are charged, so never leave a test change behind:

- **Flip and restore.** Read the current value, set the opposite, verify, then set the original back and verify again.
- **Or use an ephemeral folder.** `uip or folders create` a throwaway folder, run get/set/get against its key, then `uip or folders delete` it. Shared folders are never touched, and concurrent runs never share state.

---

## Error Conditions

| Error | Cause | Resolution |
|-------|-------|------------|
| `Invalid --enabled value '<x>'. Allowed values: true, false.` | `--enabled` is not `true`/`false` | Fix the flag; no API call was made |
| `Fully Loaded Transactions are not available for this organization.` (HTTP 403) | The organization lacks the `Platform.FltEligible` entitlement | The entitlement has to be granted on the organization's license; the CLI cannot work around it. `get` still works |
| HTTP 401 / 403 from the License Accountant | The caller lacks licensing authorization | Use an org admin session or an allow-listed licensing application |
| HTTP 404 | Unknown tenant id or folder key for this organization | Re-check both GUIDs with Step 1 |
| `Error connecting to the License Accountant.` | Auth expired or network issue | Re-run `uip login` |

---

## Gotchas

- **Tenant id, not tenant name.** Both arguments are GUIDs: the tenant id from `uip login tenant list` and the folder `Key` from `uip or folders list`.
- **`--organization <account-id>`** overrides the organization on both commands; it defaults to the organization from the current login.
- **`get` needs no entitlement, `set` does.** A `get` that works says nothing about whether `set` will; the `Platform.FltEligible` 403 only shows up on the write.
- **It is a billing switch.** Confirm with the user before enabling or disabling it on a production folder.

---

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [Consumables Report](consumables-report.md) — see the effect of outcome billing on consumption, per folder (`--mode folders`)
- [Setup Environment](../orchestrator/setup-environment.md) — creating and listing Orchestrator folders
- [Full CLI command reference](../uip-commands.md)

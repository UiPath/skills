# IP Range Management

Multi-step workflows for managing IP allowlist entries via `uip admin ip-restriction ip-ranges`. For per-command flag tables, output codes, and single-command examples, see [ip-restriction-commands.md](ip-restriction-commands.md).

## Concept

Each entry is one of:
- A **CIDR block** (e.g., `10.0.0.0/16`) — preferred shape.
- A **start/end IP range** (e.g., `10.0.0.1`–`10.0.0.50`) — legacy shape, still supported.
- A **list of CIDRs** under one named entry (pass `--cidr` multiple times).

Entries can carry an `--expires` duration (`<INTEGER><m|h|d|w>` — e.g. `15m`, `2h`, `30d`, `1w`).

When `enforcement get` returns `Enabled`, only addresses inside these entries can reach the org. See [enforcement-management.md](enforcement-management.md) for the switch.

## Workflow: Add an Entry (idempotent on CIDR)

`create` is idempotent on CIDR — running it twice with the same `--cidr` is a safe no-op.

### Single CIDR

```bash
uip admin ip-restriction ip-ranges create \
  --name "<DISPLAY_NAME>" \
  --cidr "<CIDR>" \
  --output json
```

### Multiple CIDRs under one entry

```bash
uip admin ip-restriction ip-ranges create \
  --name "<DISPLAY_NAME>" \
  --cidr "<CIDR_1>" \
  --cidr "<CIDR_2>" \
  --output json
```

### With expiry

```bash
uip admin ip-restriction ip-ranges create \
  --name "<DISPLAY_NAME>" \
  --cidr "<CIDR>" \
  --expires 30d \
  --output json
```

### Legacy start/end range

```bash
uip admin ip-restriction ip-ranges create \
  --name "<DISPLAY_NAME>" \
  --start-ip "<START_IP>" \
  --end-ip "<END_IP>" \
  --output json
```

### Full body via JSON file

```bash
uip admin ip-restriction ip-ranges create --file ./entry.json --output json
```

The body is `AddIpConfigurationRequest`.

## Workflow: Update an Entry

Patch an existing entry — rename, swap CIDRs, extend / shorten expiry, or migrate between CIDR and start/end shapes. Common scenarios: extending an expiring contractor allowlist, replacing a stale office CIDR after an ISP change.

1. Fetch the current entry so you can see what's there:
   ```bash
   uip admin ip-restriction ip-ranges get <ENTRY_ID> --output json
   ```
   Or lookup by CIDR if you only know that:
   ```bash
   uip admin ip-restriction ip-ranges get --cidr "<CURRENT_CIDR>" --output json
   ```
2. Apply the patch — only the flags you pass are updated:

   **Rename:**
   ```bash
   uip admin ip-restriction ip-ranges update <ENTRY_ID> --name "<NEW_NAME>" --output json
   ```

   **Replace CIDR(s):**
   ```bash
   uip admin ip-restriction ip-ranges update <ENTRY_ID> --cidr "<NEW_CIDR>" --output json
   ```

   **Swap to a start/end IP range:**
   ```bash
   uip admin ip-restriction ip-ranges update <ENTRY_ID> --start-ip "<IP>" --end-ip "<IP>" --output json
   ```

   **Full body via `--file`** (for fields not exposed inline):
   ```bash
   uip admin ip-restriction ip-ranges update <ENTRY_ID> --file ./entry-update.json --output json
   ```

> **Replacing a CIDR while enforcement is on is lockout-sensitive.** If you're swapping the CIDR that currently covers your IP, the new value must also cover it — verify against `my-ip` first. The CLI does not run a pre-flight on `update` (unlike `delete`).

## Workflow: Delete an Entry (lockout-sensitive)

**Lockout warning** — removing the wrong entry while enforcement is enabled can lock the caller (or the whole org) out of UiPath.

1. Confirm the entry to delete:
   ```bash
   uip admin ip-restriction ip-ranges get <ENTRY_ID> --output json
   ```
2. Check enforcement state — and mention it when confirming with the user:
   ```bash
   uip admin ip-restriction enforcement get --output json
   ```
3. Confirm with the user explicitly.
4. Delete with `--confirm`:
   ```bash
   uip admin ip-restriction ip-ranges delete <ENTRY_ID> --confirm --output json
   ```
   Or by CIDR:
   ```bash
   uip admin ip-restriction ip-ranges delete --cidr "<CIDR>" --confirm --output json
   ```

If enforcement is on, the CLI also runs a server-side safety pre-flight (`only-entry` / `caller-IP-uniquely-covered`) and may reject the delete. To bypass that check, run `enforcement disable` first — but only if you understand the consequences. See [enforcement-management.md](enforcement-management.md).

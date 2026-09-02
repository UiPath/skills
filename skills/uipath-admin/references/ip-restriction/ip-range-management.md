# IP Range Management

Manage IP allowlist entries with `uip admin ip-restriction ip-ranges`. See [ip-restriction-commands.md](ip-restriction-commands.md) for flag tables, output codes, and single-command examples.

## Concept

An entry is a preferred **CIDR block** (for example, `10.0.0.0/16`), a supported legacy **start/end IP range** (for example, `10.0.0.1`–`10.0.0.50`), or multiple CIDRs under one name using repeated `--cidr` flags.

Entries may use `--expires` with `<INTEGER><m|h|d|w>` (for example, `15m`, `2h`, `30d`, `1w`). When `enforcement get` returns `Enabled`, only addresses in these entries can reach the org. See [enforcement-management.md](enforcement-management.md).

## Add an Entry (idempotent on CIDR)

`create` is idempotent on CIDR: repeating the same `--cidr` is a safe no-op. Run the applicable command:

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

Run:

```bash
uip admin ip-restriction ip-ranges create --file ./entry.json --output json
```

The body is `AddIpConfigurationRequest`.

## Update an Entry

Update an entry to rename it, replace CIDRs, change expiry, or migrate between CIDR and start/end shapes. First run:

```bash
uip admin ip-restriction ip-ranges get <ENTRY_ID> --output json
```

If only the CIDR is known, run:

```bash
uip admin ip-restriction ip-ranges get --cidr "<CURRENT_CIDR>" --output json
```

Run only the needed patch command:

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

**Full body via `--file`:**

```bash
uip admin ip-restriction ip-ranges update <ENTRY_ID> --file ./entry-update.json --output json
```

> **Replacing a CIDR while enforcement is on is lockout-sensitive.** If the current CIDR covers your IP, the new value must also cover it. Verify against `my-ip` first. The CLI does not run a pre-flight on `update` (unlike `delete`).

## Delete an Entry (lockout-sensitive)

Removing the wrong entry while enforcement is enabled can lock the caller or the whole org out of UiPath.

1. Confirm the entry by running:
   ```bash
   uip admin ip-restriction ip-ranges get <ENTRY_ID> --output json
   ```
2. Check enforcement state and mention it when confirming with the user by running:
   ```bash
   uip admin ip-restriction enforcement get --output json
   ```
3. Confirm with the user explicitly.
4. Delete with `--confirm` by running:
   ```bash
   uip admin ip-restriction ip-ranges delete <ENTRY_ID> --confirm --output json
   ```
   Or delete by CIDR by running:
   ```bash
   uip admin ip-restriction ip-ranges delete --cidr "<CIDR>" --confirm --output json
   ```

When enforcement is on, the CLI also runs a server-side safety pre-flight (`only-entry` / `caller-IP-uniquely-covered`) and may reject the delete. To bypass it, run `enforcement disable` first—but only if you understand the consequences. See [enforcement-management.md](enforcement-management.md).

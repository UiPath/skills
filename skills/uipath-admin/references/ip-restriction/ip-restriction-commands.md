# IP-Restriction CLI Command Reference

Complete reference for all `uip admin ip-restriction` commands — org-wide IP allowlisting, the enforcement switch, URL-pattern bypass rules, and the `my-ip` lookup.

> **Internal acronym: `APMS`** (Access Policy Management Service). This is the platform's internal name for IP Restriction. **Never surface `APMS` in user-facing output** — always say "IP Restriction".

For workflow-level guidance, see [ip-range-management.md](ip-range-management.md), [enforcement-management.md](enforcement-management.md), and [bypass-rule-management.md](bypass-rule-management.md).

## Global Flags

Every command accepts these flags (omitted from per-command tables):

| Flag | Description |
|------|-------------|
| `--output <format>` | Output format: `json`, `table`, `yaml`, `plain` (default: json) |
| `--output-filter <expression>` | JMESPath expression to filter output |
| `--log-level <level>` | Log level: `debug`, `info`, `warn`, `error` (default: info) |
| `--log-file <path>` | Write logs to file instead of stderr |
| `--login-validity <minutes>` | Override token validity — forces refresh if token expires within this window |

Organization is resolved automatically from the active login session.

## Prerequisites

```bash
uip login status --output json
```

If not logged in: `uip login`.

## Concepts

- **Allowlist semantics.** When `enforcement` is `Enabled`, only IP networks in `ip-ranges list` can reach the org. Everything else is blocked.
- **Lockout risk is the dominant concern.** Removing the wrong CIDR or enabling enforcement with the caller's IP outside the list locks the caller (and possibly the whole org) out of UiPath. Safety rails:
  - `enforcement enable` runs a `my-ip` pre-flight and rejects the call if the caller's IP is not covered.
  - `ip-ranges delete` runs a server-side safety pre-flight (only-entry / caller-IP-uniquely-covered) when enforcement is on.
  - Both `ip-ranges delete` and `enforcement enable` require `--confirm`.
- **Idempotent ops.** `ip-ranges create` upserts on CIDR (safe to re-run). `enforcement enable` / `disable` are idempotent.
- **Bypass rules are server-compiled.** The CLI sends `regexEntry`; the platform compiles the regex.
- **Bypass rules only matter when enforcement is `Enabled`.** With enforcement disabled they have no effect.

---

## IP Ranges — `uip admin ip-restriction ip-ranges`

Each entry is one of:
- A **CIDR block** (e.g., `10.0.0.0/16`) — preferred shape.
- A **start/end IP range** (e.g., `10.0.0.1`–`10.0.0.50`) — legacy shape.
- A **list of CIDRs** under one named entry (pass `--cidr` multiple times).

Entries can carry an `--expires` duration (`15m`, `2h`, `30d`, `1w`).

### `ip-ranges list`

List allowlist entries.

```bash
uip admin ip-restriction ip-ranges list --output json
uip admin ip-restriction ip-ranges list --filter "<NAME_FRAGMENT>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--filter <fragment>` | No | Case-insensitive substring match on entry `name` (client-side) |

**Output code:** `ApmsIpRangesList`.

### `ip-ranges get`

Fetch an entry by id or by CIDR.

```bash
uip admin ip-restriction ip-ranges get <ENTRY_ID> --output json
uip admin ip-restriction ip-ranges get --cidr "<CIDR>" --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<ENTRY_ID>` | Conditional | Entry UUID (positional) — required unless `--cidr` |
| `--cidr <cidr>` | Conditional | Lookup by CIDR value instead of id |

**Output code:** `ApmsIpRangeGet`.

### `ip-ranges create`

Add an allowlist entry. **Idempotent on CIDR** — re-running with the same `--cidr` is a safe no-op.

```bash
uip admin ip-restriction ip-ranges create \
  --name "<DISPLAY_NAME>" \
  --cidr "<CIDR>" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | Yes (inline) | Display name for the entry |
| `--cidr <cidr>` | Conditional | CIDR block. Repeatable for multiple CIDRs under one entry |
| `--start-ip <ip>` | Conditional | Start of legacy IP range. Requires `--end-ip` |
| `--end-ip <ip>` | Conditional | End of legacy IP range. Requires `--start-ip` |
| `--expires <duration>` | No | Expiry: `<INTEGER><m\|h\|d\|w>` (e.g., `30d`, `2h`) |
| `--file <path>` | Alternative | Full `AddIpConfigurationRequest` body |

Either `--cidr` (one or more) **or** the `--start-ip`/`--end-ip` pair is required.

**Output code:** `ApmsIpRangeCreated`.

### `ip-ranges update`

Patch an entry.

```bash
uip admin ip-restriction ip-ranges update <ENTRY_ID> --name "<NEW_NAME>" --output json
uip admin ip-restriction ip-ranges update <ENTRY_ID> --cidr "<NEW_CIDR>" --output json
uip admin ip-restriction ip-ranges update <ENTRY_ID> --start-ip "<IP>" --end-ip "<IP>" --output json
uip admin ip-restriction ip-ranges update <ENTRY_ID> --file ./entry-update.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<ENTRY_ID>` | Yes | Entry UUID |
| `--name <name>` | No | New display name |
| `--cidr <cidr>` | No | Replace CIDR(s) |
| `--start-ip <ip>` | No | New range start |
| `--end-ip <ip>` | No | New range end |
| `--file <path>` | Alternative | Full update body |

**Output code:** `ApmsIpRangeUpdated`.

### `ip-ranges delete`

Remove an entry. **Lockout-sensitive — requires `--confirm`.**

```bash
uip admin ip-restriction ip-ranges delete <ENTRY_ID> --confirm --output json
uip admin ip-restriction ip-ranges delete --cidr "<CIDR>" --confirm --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<ENTRY_ID>` | Conditional | Entry UUID (positional) — required unless `--cidr` |
| `--cidr <cidr>` | Conditional | Delete by CIDR value instead of id |
| `--confirm` | Yes | Acknowledge lockout risk |

If enforcement is on, the CLI also runs a server-side safety pre-flight (only-entry / caller-IP-uniquely-covered) and may reject the delete. To bypass: run `enforcement disable` first (only if you understand the consequences).

**Output code:** `ApmsIpRangeDeleted`.

---

## Enforcement Switch — `uip admin ip-restriction enforcement`

Singleton per organization. **Idempotent** on both sides — flipping twice is a safe no-op.

### `enforcement get`

Current enforcement state.

```bash
uip admin ip-restriction enforcement get --output json
```

Returns `Data.status`: `Enabled` or `Disabled`.

**Output code:** `ApmsEnforcementGet`.

### `enforcement enable`

Turn enforcement on. **Lockout-sensitive — requires `--confirm` and a `my-ip` pre-flight.**

```bash
uip admin ip-restriction enforcement enable --confirm --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--confirm` | Yes | Acknowledge lockout risk |

The CLI runs its own `my-ip` pre-flight and rejects the call if the caller is not covered by any entry in `ip-ranges list`. If rejected, do NOT retry until the allowlist is fixed — see [enforcement-management.md](enforcement-management.md).

**Output code:** `ApmsEnforcementEnabled`.

### `enforcement disable`

Turn enforcement off. **Safe and idempotent.** No `--confirm` required.

```bash
uip admin ip-restriction enforcement disable --output json
```

Use this to recover from a near-lockout, or to bypass the `ip-ranges delete` safety pre-flight.

**Output code:** `ApmsEnforcementDisabled`.

---

## Bypass Rules — `uip admin ip-restriction bypass-rules`

URL-pattern exceptions to IP allowlisting. Each rule's `regexEntry` is compiled server-side.

### `bypass-rules list`

List rules.

```bash
uip admin ip-restriction bypass-rules list --output json
uip admin ip-restriction bypass-rules list --filter "<FRAGMENT>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--filter <fragment>` | No | Case-insensitive substring match on `regexEntry` or `appName` (client-side) |

**Output code:** `ApmsBypassRulesList`.

### `bypass-rules get`

Fetch a rule by id.

```bash
uip admin ip-restriction bypass-rules get <RULE_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<RULE_ID>` | Yes | Rule UUID |

**Output code:** `ApmsBypassRulesGet`.

### `bypass-rules create`

Create a rule. **File-only** — no inline shortcut.

```bash
uip admin ip-restriction bypass-rules create --file ./bypass-rule.json --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--file <path>` | Yes | `AddRegexBypassRequest` body |

`./bypass-rule.json`:

```json
{
  "regexEntry": "^.*\\.contoso\\.com$",
  "appName": "<OPTIONAL_APP_NAME>"
}
```

Authoring tips: escape dots (`\.`), anchor with `^` and `$`.

**Output code:** `ApmsBypassRulesCreated`.

### `bypass-rules update`

Patch a rule.

```bash
uip admin ip-restriction bypass-rules update <RULE_ID> --regex-entry "<NEW_PATTERN>" --output json
uip admin ip-restriction bypass-rules update <RULE_ID> --file ./bypass-rule-update.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<RULE_ID>` | Yes | Rule UUID |
| `--regex-entry <pattern>` | No | Replace the stored regex pattern |
| `--file <path>` | Alternative | Full `UpdateRegexBypassRequest` body (use for tenant / app metadata updates) |

**Output code:** `ApmsBypassRulesUpdated`.

### `bypass-rules delete`

Delete a rule. **No `--confirm`** — bypass-rule deletion only narrows access.

```bash
uip admin ip-restriction bypass-rules delete <RULE_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<RULE_ID>` | Yes | Rule UUID |

**Output code:** `ApmsBypassRulesDeleted`.

---

## My IP — `uip admin ip-restriction my-ip`

### `my-ip`

Return the public IP the platform sees for the current caller. Use before `enforcement enable` to verify the allowlist covers your IP.

```bash
uip admin ip-restriction my-ip --output json
```

Returns `Data.ipAddress`.

**Output code:** `ApmsMyIpGet`.

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `--confirm required` | `ip-ranges delete` or `enforcement enable` called without `--confirm` | Re-run with `--confirm` after user confirmation |
| Safety pre-flight rejected delete | Enforcement on + entry is the only / caller's covering entry | Add a new covering entry first, OR disable enforcement, OR target a different entry |
| `my-ip pre-flight failed` | Caller's IP is not in any `ip-ranges` entry | Add a covering CIDR with `ip-ranges create`, then retry |
| `entry not found` | Invalid id / CIDR not in allowlist | Run `ip-ranges list` to confirm available entries |
| `cidr already exists` (no error — create is idempotent) | Already-present CIDR | None — `create` is upsert-on-CIDR |
| `invalid expires` | Bad duration string | Use `<INTEGER><m\|h\|d\|w>` (e.g., `2h`, `30d`) |
| `invalid regex` | Server failed to compile `regexEntry` | Fix the regex in the body file |
| `rule not found` | Invalid rule UUID | Run `bypass-rules list` |
| Bypass rule has no effect | Enforcement is `Disabled` | Bypass rules only apply when `enforcement get` returns `Enabled` |
| `enforcement already <state>` (no error — idempotent) | Already in target state | None |
| Auth error | Login expired | `uip login status`, then `uip login` |

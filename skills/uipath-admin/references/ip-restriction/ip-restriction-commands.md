# IP-Restriction CLI Command Reference

Reference for `uip admin ip-restriction`: organization-wide IP allowlisting, enforcement, URL-pattern bypass rules, and `my-ip` lookup.

> **Internal acronym: `APMS`** (Access Policy Management Service). Never surface `APMS` in user-facing output; say “IP Restriction”.

For workflow guidance, see [ip-range-management.md](ip-range-management.md), [enforcement-management.md](enforcement-management.md), and [bypass-rule-management.md](bypass-rule-management.md).

## Global flags

All commands accept:

| Flag | Description |
|---|---|
| `--output <format>` | `json`, `table`, `yaml`, or `plain` (default: `json`) |
| `--output-filter <expression>` | JMESPath output filter |
| `--log-level <level>` | `debug`, `info`, `warn`, or `error` (default: `info`) |
| `--log-file <path>` | Write logs instead of stderr |
| `--login-validity <minutes>` | Force token refresh when it expires within this window |

Organization is resolved from the active login session.

## Prerequisites and safety

Run:

```bash
uip login status --output json
```

If not logged in, run `uip login`.

- When `enforcement` is `Enabled`, only networks in `ip-ranges list` can reach the organization; all others are blocked.
- Lockout is the primary risk. `enforcement enable` runs a `my-ip` pre-flight and rejects callers not covered by the allowlist. `ip-ranges delete` runs a server-side only-entry/caller-IP-uniquely-covered pre-flight when enforcement is on. Both commands require `--confirm`.
- `ip-ranges create` upserts on CIDR; `enforcement enable` and `disable` are idempotent.
- Bypass rules send `regexEntry`; the platform compiles it. They apply only when enforcement is `Enabled`.

## IP ranges — `uip admin ip-restriction ip-ranges`

An entry may contain a CIDR block, a legacy start/end IP range, or multiple CIDRs under one name. `--expires` accepts `15m`, `2h`, `30d`, or `1w`.

### List

Run:

```bash
uip admin ip-restriction ip-ranges list --output json
uip admin ip-restriction ip-ranges list --filter "<NAME_FRAGMENT>" --output json
```

`--filter <fragment>` is an optional, client-side, case-insensitive substring match on `name`.

**Output code:** `ApmsIpRangesList`.

### Get

Run either:

```bash
uip admin ip-restriction ip-ranges get <ENTRY_ID> --output json
uip admin ip-restriction ip-ranges get --cidr "<CIDR>" --output json
```

`<ENTRY_ID>` is required unless `--cidr` is supplied. `--cidr <cidr>` looks up by CIDR.

**Output code:** `ApmsIpRangeGet`.

### Create

Run:

```bash
uip admin ip-restriction ip-ranges create \
  --name "<DISPLAY_NAME>" --cidr "<CIDR>" --output json
```

This is idempotent on CIDR and is safe to rerun with the same `--cidr`.

| Flag | Requirement | Description |
|---|---|---|
| `--name <name>` | Required inline | Display name |
| `--cidr <cidr>` | Conditional | CIDR; repeat for multiple CIDRs under one entry |
| `--start-ip <ip>` | Conditional | Legacy range start; requires `--end-ip` |
| `--end-ip <ip>` | Conditional | Legacy range end; requires `--start-ip` |
| `--expires <duration>` | Optional | `<INTEGER><m\|h\|d\|w>` |
| `--file <path>` | Alternative | Full `AddIpConfigurationRequest` body |

Supply either one or more `--cidr` flags or the `--start-ip`/`--end-ip` pair.

**Output code:** `ApmsIpRangeCreated`.

### Update

Run one of:

```bash
uip admin ip-restriction ip-ranges update <ENTRY_ID> --name "<NEW_NAME>" --output json
uip admin ip-restriction ip-ranges update <ENTRY_ID> --cidr "<NEW_CIDR>" --output json
uip admin ip-restriction ip-ranges update <ENTRY_ID> --start-ip "<IP>" --end-ip "<IP>" --output json
uip admin ip-restriction ip-ranges update <ENTRY_ID> --file ./entry-update.json --output json
```

`<ENTRY_ID>` is required. Optional patch flags are `--name <name>`, `--cidr <cidr>` (replace CIDR(s)), `--start-ip <ip>`, `--end-ip <ip>`, or alternative `--file <path>` containing the full update body.

**Output code:** `ApmsIpRangeUpdated`.

### Delete

Run with confirmation:

```bash
uip admin ip-restriction ip-ranges delete <ENTRY_ID> --confirm --output json
uip admin ip-restriction ip-ranges delete --cidr "<CIDR>" --confirm --output json
```

`<ENTRY_ID>` is required unless `--cidr` is supplied. `--confirm` is required. When enforcement is on, the server may reject deletion if the entry is the only entry or uniquely covers the caller’s IP. To bypass that check, first run `enforcement disable`, only if the consequences are understood.

**Output code:** `ApmsIpRangeDeleted`.

## Enforcement switch — `uip admin ip-restriction enforcement`

There is one switch per organization. Both states are idempotent.

### Get

Run:

```bash
uip admin ip-restriction enforcement get --output json
```

`Data.status` is `Enabled` or `Disabled`.

**Output code:** `ApmsEnforcementGet`.

### Enable

Run with confirmation:

```bash
uip admin ip-restriction enforcement enable --confirm --output json
```

`--confirm` is required. The CLI runs a `my-ip` pre-flight and rejects the call if the caller is not covered by any `ip-ranges list` entry. If rejected, do not retry until the allowlist is fixed; see [enforcement-management.md](enforcement-management.md).

**Output code:** `ApmsEnforcementEnabled`.

### Disable

Run:

```bash
uip admin ip-restriction enforcement disable --output json
```

This is safe and idempotent; it requires no `--confirm`. Use it to recover from a near-lockout or bypass the `ip-ranges delete` safety pre-flight.

**Output code:** `ApmsEnforcementDisabled`.

## Bypass rules — `uip admin ip-restriction bypass-rules`

Rules are URL-pattern exceptions. The server compiles each `regexEntry`; rules have no effect while enforcement is `Disabled`.

### List

Run:

```bash
uip admin ip-restriction bypass-rules list --output json
uip admin ip-restriction bypass-rules list --filter "<FRAGMENT>" --output json
```

`--filter <fragment>` is optional and performs a client-side, case-insensitive substring match on `regexEntry` or `appName`.

**Output code:** `ApmsBypassRulesList`.

### Get

Run:

```bash
uip admin ip-restriction bypass-rules get <RULE_ID> --output json
```

`<RULE_ID>` is required and is a rule UUID.

**Output code:** `ApmsBypassRulesGet`.

### Create

Create is file-only. Run:

```bash
uip admin ip-restriction bypass-rules create --file ./bypass-rule.json --output json
```

`--file <path>` is required and contains an `AddRegexBypassRequest` body:

```json
{
  "regexEntry": "^.*\\.contoso\\.com$",
  "appName": "<OPTIONAL_APP_NAME>"
}
```

Escape dots (`\.`) and anchor patterns with `^` and `$`.

**Output code:** `ApmsBypassRulesCreated`.

### Update

Run either:

```bash
uip admin ip-restriction bypass-rules update <RULE_ID> --regex-entry "<NEW_PATTERN>" --output json
uip admin ip-restriction bypass-rules update <RULE_ID> --file ./bypass-rule-update.json --output json
```

`<RULE_ID>` is required. Optional `--regex-entry <pattern>` replaces the stored pattern. Alternatively, `--file <path>` supplies the full `UpdateRegexBypassRequest`, including tenant/app metadata updates.

**Output code:** `ApmsBypassRulesUpdated`.

### Delete

Run:

```bash
uip admin ip-restriction bypass-rules delete <RULE_ID> --output json
```

`<RULE_ID>` is required. No `--confirm` is required because deletion only narrows access.

**Output code:** `ApmsBypassRulesDeleted`.

## My IP — `uip admin ip-restriction my-ip`

When asked for the user’s public IP or the IP the platform sees, run this standalone command; no enforcement context is needed:

```bash
uip admin ip-restriction my-ip --output json
```

It returns `Data.ipAddress` and is also the safety pre-flight for `enforcement enable`.

**Output code:** `ApmsMyIpGet`.

## Error handling

| Error | Cause | Fix |
|---|---|---|
| `--confirm required` | Delete or enable omitted `--confirm` | After user confirmation, rerun with `--confirm` |
| Safety pre-flight rejected delete | Enforcement is on and the entry is the only or caller-covering entry | Add a covering entry first, disable enforcement, or target another entry |
| `my-ip pre-flight failed` | Caller’s IP is not in an `ip-ranges` entry | Run `ip-ranges create` with a covering CIDR, then retry |
| `entry not found` | Invalid ID or CIDR absent | Run `ip-ranges list` |
| `cidr already exists` (no error — create is idempotent) | CIDR already exists | None |
| `invalid expires` | Invalid duration | Use `<INTEGER><m\|h\|d\|w>` such as `2h` or `30d` |
| `invalid regex` | Server could not compile `regexEntry` | Fix the regex in the body file |
| `rule not found` | Invalid rule UUID | Run `bypass-rules list` |
| Bypass rule has no effect | Enforcement is `Disabled` | Run `enforcement get`; rules apply only when it returns `Enabled` |
| `enforcement already <state>` (no error — idempotent) | Already in target state | None |
| Auth error | Login expired | Run `uip login status`, then `uip login` |
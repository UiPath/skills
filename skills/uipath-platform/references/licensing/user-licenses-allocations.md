# User & Group License Allocations

Assign user-bundle licenses (for example, `RPADEVPRONU`, `ATTUNU`, `TSTNU`) directly to users or through group rules with optional quotas. For full options, run `uip platform users licenses --help` or `uip platform groups rules --help`.

---

## When to Use

- Assign or audit user bundles: `users licenses set` / `get`
- Check account seats: `users licenses available`
- Entitle an AD/AAD group, optionally capped: `groups rules set`
- Inspect group members' bundles: `groups rules details`

## Prerequisites

1. Verify authentication with `uip login status`; if unauthenticated, ask the user to run `uip login` (interactive browser flow).
2. Require org-admin permissions.
3. `users licenses set/get` requires a directory name or email-prefix match to **exactly one** user.
4. `groups rules details/set` requires a group-name prefix match to **exactly one** group.

## Commands

| Command | Purpose |
|---|---|
| `uip platform users licenses available` | Account totals per user-bundle: `total`, `allocated`, `available` |
| `uip platform users licenses get <user>` | User leases and `source` (`direct` or `group`) |
| `uip platform users licenses set <user> --input <path>` | Replace direct bundle allocation |
| `uip platform groups rules get` | List group rules, quotas, and usage (paginated) |
| `uip platform groups rules details <group>` | Per-user group leases; quota summary goes to stderr |
| `uip platform groups rules set <group> --input <path>` | Replace group bundles and quotas |

## Bundle Code ↔ Friendly Name Resolution

The CLI emits raw codes (`RPADEVPRONU`, `ATTUNU`, `TSTNU`); for user bundles, `name` is the code. Resolve every code in both directions through the authoritative page:

> **Source of truth:** [UiPath Licensing Product Codes](https://docs.uipath.com/automation-cloud/automation-cloud/latest/api-guide/license-codes)

Fetch on demand; do not cache because UiPath revises bundle codes.

### Input: user phrase → code

Both `users licenses set` and `groups rules set` require `code`; the CLI does not validate it, so typos produce an opaque “not allocated” result:

1. Fetch the docs page and match the user's phrase to a `code`.
2. Confirm ownership by running `uip platform users licenses available --output json | jq '.Data[].code'`; if absent, state that the account does not own the bundle and do not allocate it.
3. Write the resolved code to the input file and run `users licenses set` or `groups rules set`.

If the phrase is ambiguous or absent, ask the user to clarify or choose from `users licenses available`.

### Output: code → friendly name (mandatory when reporting to the user)

For every output or error from `users licenses available/get/set`, `groups rules get/details/set`, and bundle-code errors, **always replace raw codes with the docs-page friendly name** while retaining the code: `<Friendly Name> (<CODE>)` — e.g., `Automation Developer Named User (RPADEVPRONU)`, `Attended Named User (ATTUNU)`, `Tester Named User (TSTNU)`. Never show the CLI's user-bundle `name` verbatim. If the docs omit a returned code, show it verbatim and say its friendly name could not be resolved; do not invent one.

Example — raw CLI output:

```json
{"code": "RPADEVPRONU", "name": "RPADEVPRONU", "total": 100, "allocated": 42, "available": 58}
```

Reported to the user as: **Automation Developer Named User (`RPADEVPRONU`): 58 of 100 seats available.**

## Direct User Assignment

### Check Account-Level Availability

Run:

```bash
uip platform users licenses available --output json
```

```json
{"Result":"Success","Code":"UserLicensesAvailable","Data":[{"code":"RPADEVPRONU","name":"RPADEVPRONU","total":100,"allocated":42,"available":58},{"code":"ATTUNU","name":"ATTUNU","total":50,"allocated":50,"available":0}]}
```

`available = max(0, total - allocated)`; `available: 0` cannot be assigned to a new user until seats are purchased or allocations revoked.

### Inspect a User's Current Leases

Run:

```bash
uip platform users licenses get "<USER_NAME_OR_EMAIL_PREFIX>" --output json
```

```json
{"Result":"Success","Code":"UserLicenses","Data":[{"source":"direct","code":"RPADEVPRONU","name":"RPADEVPRONU","leasedAt":"2026-04-15T10:30:00.000Z"},{"source":"group","code":"ATTUNU","name":"ATTUNU","leasedAt":"2026-04-20T08:15:00.000Z"}]}
```

`source` is `direct` for `users licenses set` or `group` for a group rule; the same `code` may appear once from each source.

### Assign Bundles to a User

Create the input file:

```json
[
  {"code": "RPADEVPRONU"},
  {"code": "ATTUNU"},
  {"code": "TSTNU"}
]
```

Each entry must be `{"code": "<non-empty-string>"}`; at least one entry is required (empty `[]` is rejected). Run:

```bash
uip platform users licenses set "<USER_NAME_OR_EMAIL_PREFIX>" --input ./user-licenses.json --output json
```

```json
{"Result":"Success","Code":"UserLicensesSet","Data":[{"code":"RPADEVPRONU","name":"RPADEVPRONU"},{"code":"ATTUNU","name":"ATTUNU"},{"code":"TSTNU","name":"TSTNU"}]}
```

This replaces, rather than merges, direct allocations; group-inherited leases are unaffected.

## Group Rule-Based Allocation

### List All Group Rules

Run:

```bash
uip platform groups rules get --output json
```

To filter, run:

```bash
uip platform groups rules get --limit 20 --sort-by name --sort-order Desc --output json
```

Returns one row per `(group, bundle)` pair:

```json
{"Result":"Success","Code":"GroupRules","Data":[{"groupId":"35551807-06b1-4cda-90a1-2fb84851eee7","groupName":"RPA Developers","code":"RPADEVPRONU","name":"RPADEVPRONU","quota":25,"currentUsage":12,"useExternalLicense":false}],"Pagination":{"Returned":1,"Limit":50,"Offset":0,"HasMore":false}}
```

`quota` is `null` for no enforcement or an enforced integer; `currentUsage` is users leasing the bundle; `useExternalLicense` indicates an external license source.

### Drill into One Group

Run `groups rules details`, not `uip admin groups members list` plus per-user `users licenses get`: the latter shows only direct leases, loses `orphan` and `quota`, and costs one call per user.

```bash
uip platform groups rules details "<GROUP_NAME_PREFIX>" --output json
uip platform groups rules details "<GROUP_NAME_PREFIX>" --limit 100 --offset 0 --output json
```

The CLI writes the rule-entitlement/quota summary to **stderr** and one row per `(user, bundle leased)` to stdout. A group user with no leased bundle appears once with `bundleCode: null`.

```json
{"Result":"Success","Code":"GroupRuleDetails","Data":[{"userDisplayName":"Dan Dinu","email":"dan.dinu@uipath.com","lastInUse":"2026-05-10T08:15:00.000Z","orphan":false,"bundleCode":"RPADEVPRONU","bundleName":"RPADEVPRONU","quota":25,"currentUsage":12}],"Pagination":{"Returned":1,"Limit":50,"Offset":0,"HasMore":false}}
```

`orphan: true` means the user still holds a lease but is no longer a group member; clean it up by re-running `groups rules set` or removing the user from the group.

### Set a Group Rule

Create the rule file:

```json
[
  {"code": "RPADEVPRONU"},
  {"code": "ATTUNU", "quota": 10}
]
```

`code` must be a non-empty string. Optional `quota` must be an integer ≥ 1 (`quota: 0` is rejected); omission means **no enforcement**, so every group member claiming the bundle gets one. Run:

```bash
uip platform groups rules set "<GROUP_NAME_PREFIX>" --input ./group-rule.json --output json
```

```json
{"Result":"Success","Code":"GroupRuleSet","Data":[{"code":"RPADEVPRONU","name":"RPADEVPRONU","quota":null,"currentUsage":null},{"code":"ATTUNU","name":"ATTUNU","quota":10,"currentUsage":0}]}
```

Entries without a quota return `quota: null, currentUsage: null`. `set` replaces the entire rule; omitted bundles are removed.

## Direct vs Group: When to Use Each

| Need | Use |
|---|---|
| Specific developer's Studio license | `users licenses set` (direct) |
| Entire AD group entitled to a bundle | `groups rules set` (no quota) |
| Cap group consumption | `groups rules set` with `quota: N` |
| Audit current ownership | `users licenses get` or `groups rules details` |
| Remaining seats | `users licenses available` |

Both mechanisms can coexist for one user; `users licenses get` reports separate `source` rows.

## Error Conditions

| Error | Cause | Resolution |
|---|---|---|
| `No directory user found matching '<input>'.` | No matching user | Use a more specific or correct prefix |
| `Multiple directory users matched '<input>'.` | More than one match; CLI shows up to 10 candidates | Use a more specific prefix or full email |
| `Input file contains no user license bundles.` | Empty `[]` for `users licenses set` | Add an entry |
| `"quota" for code '<X>' must be an integer >= 1` | `quota: 0` or non-integer | Use a positive integer or omit `quota` |
| `Invalid --sort-order.` | Value is not `Asc` or `Desc` | Pass exactly `Asc` or `Desc` (case-sensitive) |
| `Error connecting to the License Accountant.` | Expired auth or network issue | Re-run `uip login` |

## Gotchas

- User/group resolution is a starts-with search requiring exactly one match; use enough name/email to disambiguate.
- `users licenses set` replaces direct bundles; `groups rules set` replaces the whole group rule. Group leases are unaffected by the former.
- `quota: 0` is rejected; exclude the bundle to remove its entitlement. `quota` applies only to group rules.
- Sort order accepts only case-sensitive `Asc`/`Desc`; `asc`, `ASC`, and `ascending` fail.
- `orphan: true` rows continue consuming a lease until the rule is reapplied or the user is fully removed.
- `useExternalLicense` from `groups rules get` is informational and is not set by these commands.
- `uip admin groups` knows membership, not bundles or leases; “who in this group holds which bundle” requires `groups rules details`.
- `groups rules details` puts its summary on stderr so stdout remains JSON for `jq`. Save JSON with `> details.json`; `2>&1` prepends the header and makes the file unparsable.

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [Tenant Allocations](tenant-allocations.md) — separate license type for tenant runtime pools
- [Consumables Report](consumables-report.md) — consumption tracking
- [Full CLI command reference](../uip-commands.md)
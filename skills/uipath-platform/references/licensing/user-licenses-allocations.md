# User & Group License Allocations

Assign user-bundle licenses (for example, `RPADEVPRONU`, `ATTUNU`, `TSTNU`) directly to users or through group rules with optional quotas. For full options, run `uip platform users licenses --help` or `uip platform groups rules --help`.

## Prerequisites and license-code resolution

1. Run `uip login status`. If unauthenticated, ask the user to run `uip login` (interactive browser flow).
2. Require org-admin permissions for allocation.
3. For `users licenses set|get`, require a name or email prefix matching exactly one directory user.
4. For `groups rules details/set`, require a group-name prefix matching exactly one group.

Use `users licenses set|get` for direct Studio/Attended allocation or auditing, `users licenses available` for account-level availability, `groups rules set` for group entitlements and optional quotas, and `groups rules details` for group-member leases.

The CLI emits raw codes; for user bundles, `name` is identical to the code and is not human-readable. Resolve codes in both directions from this authoritative page, fetched on demand:

> **Source of truth:** [UiPath Licensing Product Codes](https://docs.uipath.com/automation-cloud/automation-cloud/latest/api-guide/license-codes)

Do not cache the table; UiPath may revise bundle codes as SKUs are added or discontinued.

Before writing an input file for either `users licenses set` or `groups rules set`:

1. Fetch the docs page and match the user's license phrase to a `code`.
2. Run `uip platform users licenses available --output json | jq '.Data[].code'` and confirm the account owns that code.
3. If the code is absent, report that the account does not own the bundle; do not allocate it.
4. Write the resolved code and run `users licenses set` or `groups rules set`.

If the phrase is ambiguous, has multiple matches, or is absent from the docs page, ask the user to clarify or choose from `users licenses available` output.

When reporting output from `available`, `get`, `set`, `groups rules get`, `groups rules details`, or `groups rules set`, replace every raw code with the docs-page friendly name and retain the code as `<Friendly Name> (<CODE>)`. Apply this to errors mentioning a bundle code. Never show the CLI's user-bundle `name` value verbatim. If the docs page lacks a returned code, show the code verbatim and state that its friendly name could not be resolved; do not invent a name.

## Commands

| Command | Purpose |
|---|---|
| `uip platform users licenses available` | Account totals per bundle: `total`, `allocated`, `available` |
| `uip platform users licenses get <user>` | User leases and `source` (`direct` or `group`) |
| `uip platform users licenses set <user> --input <path>` | Replace direct bundle allocation |
| `uip platform groups rules get` | List group rules, quotas, and usage; paginated |
| `uip platform groups rules details <group>` | Per-user group leases and quota summary on stderr |
| `uip platform groups rules set <group> --input <path>` | Replace group entitlements and quotas |

## Direct user assignment

Run:

```bash
uip platform users licenses available --output json
```

The response contains `Result`, `Code`, and `Data` rows with `code`, `name`, `total`, `allocated`, and `available`; `available = max(0, total - allocated)`. Do not assign a new user a bundle with `available: 0` until an allocation is revoked or more seats are purchased.

Run:

```bash
uip platform users licenses get "<USER_NAME_OR_EMAIL_PREFIX>" --output json
```

Rows contain `source`, `code`, `name`, and `leasedAt`. `source` is `direct` for `users licenses set` assignments and `group` for group-rule leases. The same code may appear once for each source.

Write an input file containing at least one entry, each exactly `{"code": "<non-empty-string>"}`. Reject an empty array. Run:

```bash
uip platform users licenses set "<USER_NAME_OR_EMAIL_PREFIX>" --input ./user-licenses.json --output json
```

The response contains `Result`, `Code`, and `Data` entries with `code` and `name`. `set` replaces direct allocation: omitted direct bundles are revoked, while group-inherited leases are unaffected.

## Group rules

### List rules

Run:

```bash
uip platform groups rules get --output json
```

For filtering and sorting, run:

```bash
uip platform groups rules get --limit 20 --sort-by name --sort-order Desc --output json
```

The paginated response contains `Result`, `Code`, `Data`, and `Pagination`. Each `Data` row is one `(group, bundle)` pair and may contain `groupId`, `groupName`, `code`, `name`, `quota`, `currentUsage`, and `useExternalLicense`.

- `quota: null` means no quota enforcement; an integer means an enforced quota.
- `currentUsage` is the number of users currently leasing the bundle from the rule.
- `useExternalLicense: true` indicates an external license source and is informational; these commands do not set it.
- `Pagination` contains `Returned`, `Limit`, `Offset`, and `HasMore`.
- Accept only case-sensitive `Asc` or `Desc` for `--sort-order`.

### Inspect a group

Run:

```bash
uip platform groups rules details "<GROUP_NAME_PREFIX>" --output json
```

For pagination, run:

```bash
uip platform groups rules details "<GROUP_NAME_PREFIX>" --limit 100 --offset 0 --output json
```

Do not reconstruct this result with `uip admin groups members list` plus `users licenses get` per member: that shows direct leases only, loses `orphan` and `quota`, and costs one call per user.

The command writes a rule-entitlement and quota summary to stderr and emits JSON rows to stdout. Each row is a `(user, bundle leased)` pair; a member with no leased bundle has `bundleCode: null`. Rows may contain `userDisplayName`, `email`, `lastInUse`, `orphan`, `bundleCode`, `bundleName`, `quota`, and `currentUsage`, plus standard `Result`, `Code`, and `Pagination` fields.

`orphan: true` means the user still holds a lease but is no longer a group member. Clean it up by re-running `groups rules set` or removing the user from the group. Orphaned leases continue consuming a lease until cleaned up.

### Set a group rule

Write an input file with a non-empty-string `code`; `quota` is optional and, when present, must be an integer `>= 1`. Reject `quota: 0` and non-integers. Omitting `quota` means no enforcement, so every group member claiming the bundle gets one. Run:

```bash
uip platform groups rules set "<GROUP_NAME_PREFIX>" --input ./group-rule.json --output json
```

The response contains `Result`, `Code`, and `Data` entries with `code`, `name`, `quota`, and `currentUsage`. `set` replaces the entire group rule; omitted bundles are removed from the entitlement.

## Direct versus group allocation

| Need | Command |
|---|---|
| Assign one developer a license | `users licenses set` |
| Entitle a group without a cap | `groups rules set` without `quota` |
| Cap group consumption | `groups rules set` with `quota: N` |
| Audit one user's leases | `users licenses get` |
| Audit all leases in a group | `groups rules details` |
| Check remaining seats | `users licenses available` |

Direct and group allocation can coexist; `users licenses get` reports separate `source` rows.

## Errors and gotchas

| Error | Cause and resolution |
|---|---|
| `No directory user found matching '<input>'.` | No matching user; use a correct or more specific name/email prefix. |
| `Multiple directory users matched '<input>'.` | Prefix is ambiguous; the CLI shows up to 10 candidates. Use a more specific prefix or full email. |
| `Input file contains no user license bundles.` | `users licenses set` received `[]`; add at least one entry. |
| `"quota" for code '<X>' must be an integer >= 1` | `quota: 0` or a non-integer; use a positive integer or omit `quota`. |
| `Invalid --sort-order.` | Use exactly `Asc` or `Desc`. |
| `Error connecting to the License Accountant.` | Authentication or network issue; re-run `uip login`. |

- User and group resolution uses a starts-with search and requires exactly one match; email addresses are usually unique.
- `users licenses set` replaces direct assignments and does not affect group leases.
- `groups rules set` replaces the whole group rule; omitted bundles are removed.
- Remove a group bundle by omitting it; `quota: 0` is invalid.
- Quotas apply only to group rules, not direct assignments.
- `uip admin groups` answers membership questions, not licensing questions; use `groups rules details` for group bundle leases.
- The `groups rules details` summary is on stderr. Redirect stdout alone when saving JSON (`> details.json`); `2>&1` places the header above the JSON and breaks parsing.

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [Tenant Allocations](tenant-allocations.md) — separate license type for tenant runtime pools
- [Consumables Report](consumables-report.md) — consumption tracking
- [Full CLI command reference](../uip-commands.md)
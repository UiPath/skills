# User & Group License Allocations

Assign user-bundle licenses (e.g., `RPADEVPRONU`, `ATTUNU`, `TSTNU`) directly to individual users, or via group rules with optional quotas.

> For full option details, run `uip platform users licenses --help` or `uip platform groups rules --help`.

---

## When to Use

- Assigning Studio/Attended licenses to individual developers (`users licenses set`)
- Auditing what bundles a user currently has and where the lease came from (`users licenses get`)
- Checking how many seats per bundle remain at the account level (`users licenses available`)
- Managing license entitlement for an AD/AAD group (`groups rules set`) — every group member auto-leases
- Capping how many of a bundle a group can consume via quota (`groups rules set` with `quota`)
- Drilling into who in a group currently holds which bundle (`groups rules details`)

## Prerequisites

1. Authenticated — verify with `uip login status`; if not, ask the user to run `uip login` (interactive browser flow)
2. Org admin permissions for license allocation
3. For `users licenses set/get`: the user is resolvable from a directory search — name or email prefix must match **exactly one** user
4. For `groups rules details/set`: the group name prefix must match **exactly one** group

---

## Commands

| Command | What it does |
|---------|--------------|
| `uip platform users licenses available` | Account-level totals per user-bundle: `total`, `allocated`, `available` |
| `uip platform users licenses get <user>` | List user-bundle leases a user currently holds, with `source` (`direct` or `group`) |
| `uip platform users licenses set <user> --input <path>` | Replace the user's direct bundle allocation |
| `uip platform groups rules get` | List all group rules with quota config and current usage (paginated) |
| `uip platform groups rules details <group>` | Per-user view of a single group: who holds which bundle, plus quota summary on stderr |
| `uip platform groups rules set <group> --input <path>` | Replace the bundle entitlement + quotas for a group |

---

## Bundle Code ↔ Friendly Name Resolution

The CLI emits raw codes (`RPADEVPRONU`, `ATTUNU`, `TSTNU`) and a `name` field that is **identical to the code** for user bundles — it is not human-readable. Resolve every code via the authoritative docs page in **both directions**:

> **Source of truth:** [UiPath Licensing Product Codes](https://docs.uipath.com/automation-cloud/automation-cloud/latest/api-guide/license-codes)

Fetch on demand — do not cache the table here, since UiPath revises bundle codes as SKUs are added or discontinued.

### Input: user phrase → code

`users licenses set` and `groups rules set` both require a `code` per entry. The CLI does **not** validate codes against a known list — typos pass through and result in an opaque "not allocated" outcome. Resolve every code before writing the input file.

1. The user names a license (e.g., "give Dan an Attended license").
2. Fetch the docs page and match the user's phrase to a `code`.
3. Confirm the code is owned by the account: `uip platform users licenses available --output json | jq '.Data[].code'`. If absent, surface that the account does not own this bundle — do not allocate.
4. Write the input file with the resolved code and run `users licenses set` or `groups rules set`.

If the phrase is ambiguous (multiple matches) or absent from the docs page, ask the user to clarify or pick from `users licenses available` output.

### Output: code → friendly name (mandatory when reporting to the user)

When relaying CLI output back to the user, **always replace raw codes with the friendly name from the docs page**, keeping the code in parentheses for traceability. The `name` field returned by the CLI for user bundles is the code itself and MUST NOT be shown verbatim.

Format: `<Friendly Name> (<CODE>)` — e.g., `Automation Developer Named User (RPADEVPRONU)`, `Attended Named User (ATTUNU)`, `Tester Named User (TSTNU)`.

Apply to every user-facing summary derived from these commands:
- `users licenses available` — seat totals per bundle
- `users licenses get` — a user's current leases
- `users licenses set` — post-assignment confirmation
- `groups rules get` / `groups rules details` — group rule listings
- `groups rules set` — post-write confirmation
- Error messages that reference a bundle code

If the docs page does not list a returned code (newly added SKU, deprecated code still leased), display the code verbatim and tell the user the friendly name could not be resolved — do not invent one.

Example — raw CLI output:

```json
{"code": "RPADEVPRONU", "name": "RPADEVPRONU", "total": 100, "allocated": 42, "available": 58}
```

Reported to the user as: **Automation Developer Named User (`RPADEVPRONU`): 58 of 100 seats available.**

---

## Direct User Assignment

### Check Account-Level Availability

Run this before assignment to confirm the bundle has free seats:

```bash
uip platform users licenses available --output json
```

```json
{
  "Result": "Success",
  "Code": "UserLicensesAvailable",
  "Data": [
    {"code": "RPADEVPRONU", "name": "RPADEVPRONU", "total": 100, "allocated": 42, "available": 58},
    {"code": "ATTUNU", "name": "ATTUNU", "total": 50, "allocated": 50, "available": 0}
  ]
}
```

`available = max(0, total - allocated)`. A bundle with `available: 0` cannot be assigned to a new user until existing allocations are revoked or more seats are purchased.

### Inspect a User's Current Leases

```bash
uip platform users licenses get "<USER_NAME_OR_EMAIL_PREFIX>" --output json
```

```json
{
  "Result": "Success",
  "Code": "UserLicenses",
  "Data": [
    {"source": "direct", "code": "RPADEVPRONU", "name": "RPADEVPRONU", "leasedAt": "2026-04-15T10:30:00.000Z"},
    {"source": "group",  "code": "ATTUNU",      "name": "ATTUNU",      "leasedAt": "2026-04-20T08:15:00.000Z"}
  ]
}
```

`source` field:
- `"direct"` — assigned through `users licenses set`
- `"group"` — leased through a group rule the user belongs to

A user may hold the same `code` from both sources (one row each).

### Assign Bundles to a User

Create the input file:

```json
[
  {"code": "RPADEVPRONU"},
  {"code": "ATTUNU"},
  {"code": "TSTNU"}
]
```

Validation rules:
- Each entry must be `{"code": "<non-empty-string>"}`
- At least one entry required (empty array is rejected)

Apply it:

```bash
uip platform users licenses set "<USER_NAME_OR_EMAIL_PREFIX>" --input ./user-licenses.json --output json
```

```json
{
  "Result": "Success",
  "Code": "UserLicensesSet",
  "Data": [
    {"code": "RPADEVPRONU", "name": "RPADEVPRONU"},
    {"code": "ATTUNU", "name": "ATTUNU"},
    {"code": "TSTNU", "name": "TSTNU"}
  ]
}
```

The set is **replace, not merge** — the input fully defines the user's direct allocation. Group-inherited leases are unaffected.

---

## Group Rule-Based Allocation

### List All Group Rules

```bash
uip platform groups rules get --output json

# Filter to first 20 sorted by name descending
uip platform groups rules get --limit 20 --sort-by name --sort-order Desc --output json
```

Returns one row per `(group, bundle)` pair:

```json
{
  "Result": "Success",
  "Code": "GroupRules",
  "Data": [
    {
      "groupId": "35551807-06b1-4cda-90a1-2fb84851eee7",
      "groupName": "RPA Developers",
      "code": "RPADEVPRONU",
      "name": "RPADEVPRONU",
      "quota": 25,
      "currentUsage": 12,
      "useExternalLicense": false
    }
  ],
  "Pagination": {"Returned": 1, "Limit": 50, "Offset": 0, "HasMore": false}
}
```

| Field | Meaning |
|-------|---------|
| `quota` | `null` if no quota set (no enforcement); integer if enforced |
| `currentUsage` | Number of users currently leasing this bundle from the rule |
| `useExternalLicense` | True if external license source is in effect for the group |

### Drill into One Group

```bash
uip platform groups rules details "<GROUP_NAME_PREFIX>" --output json

# Page through users
uip platform groups rules details "<GROUP_NAME_PREFIX>" --limit 100 --offset 0 --output json
```

The CLI writes a summary header to **stderr** (rule entitlements and quota totals), then emits one row per `(user, bundle leased)` to stdout. Users in the group with no bundle leased appear as a single row with `bundleCode: null`.

```json
{
  "Result": "Success",
  "Code": "GroupRuleDetails",
  "Data": [
    {
      "userDisplayName": "Dan Dinu",
      "email": "dan.dinu@uipath.com",
      "lastInUse": "2026-05-10T08:15:00.000Z",
      "orphan": false,
      "bundleCode": "RPADEVPRONU",
      "bundleName": "RPADEVPRONU",
      "quota": 25,
      "currentUsage": 12
    }
  ],
  "Pagination": {"Returned": 1, "Limit": 50, "Offset": 0, "HasMore": false}
}
```

`orphan: true` means the user still holds a lease but is no longer a member of the group — clean these up by re-running `groups rules set` or removing the user from the group.

### Set a Group Rule

Create the rule file:

```json
[
  {"code": "RPADEVPRONU"},
  {"code": "ATTUNU", "quota": 10}
]
```

Validation rules:
- `code` must be a non-empty string
- `quota` is optional. When present, must be an integer ≥ 1. `quota: 0` is rejected
- Omitting `quota` means **no enforcement** — every group member who claims this bundle gets one

Apply it:

```bash
uip platform groups rules set "<GROUP_NAME_PREFIX>" --input ./group-rule.json --output json
```

```json
{
  "Result": "Success",
  "Code": "GroupRuleSet",
  "Data": [
    {"code": "RPADEVPRONU", "name": "RPADEVPRONU", "quota": null,  "currentUsage": null},
    {"code": "ATTUNU",      "name": "ATTUNU",      "quota": 10,    "currentUsage": 0}
  ]
}
```

`set` replaces the entire rule — bundles not in the input are removed from the group's entitlement.

---

## Direct vs Group: When to Use Each

| Need | Use |
|------|-----|
| Assign a specific developer their Studio license | `users licenses set` (direct) |
| Entitle the entire RPA Developers AD group to a bundle | `groups rules set` (no quota) |
| Cap how many users from a group can consume a bundle | `groups rules set` with `quota: N` |
| Audit who has what right now | `users licenses get` (per user) or `groups rules details` (per group) |
| Quickly see remaining seats | `users licenses available` |

Both mechanisms can co-exist for the same user; rows appear with separate `source` values in `users licenses get`.

---

## Error Conditions

| Error | Cause | Resolution |
|-------|-------|------------|
| `No directory user found matching '<input>'.` | No user with that name/email prefix | Use a more specific or correct prefix |
| `Multiple directory users matched '<input>'.` | Prefix matches more than one user; CLI shows up to 10 candidates | Use a more specific prefix or the full email |
| `Input file contains no user license bundles.` | Empty `[]` for `users licenses set` | Add at least one entry |
| `"quota" for code '<X>' must be an integer >= 1` | `quota: 0` or non-integer in `groups rules set` | Use a positive integer or omit `quota` |
| `Invalid --sort-order.` | Value other than `Asc` or `Desc` | Case-sensitive; pass exactly `Asc` or `Desc` |
| `Error connecting to the License Accountant.` | Auth expired or network issue | Re-run `uip login` |

---

## Gotchas

- **User/group resolver requires exactly one match.** The directory search is a "starts with" match; pass enough of the name or email to disambiguate. Email addresses are usually unique.
- **`users licenses set` replaces, not merges.** Passing one bundle revokes any other direct bundles the user previously held. Group-inherited bundles are unaffected.
- **`groups rules set` replaces the whole rule.** Any bundle not in the new input file is removed from the group's entitlement.
- **`quota: 0` is rejected.** To zero a bundle out, exclude it from the input file (which removes the entitlement entirely) rather than setting `quota: 0`.
- **`quota` only applies to group rules.** Direct user assignment has no quota — it's an explicit per-user grant.
- **Sort order is case-sensitive.** `Asc`/`Desc` only. `asc`, `ASC`, or `ascending` are all rejected.
- **`orphan: true` rows** still consume a lease until the rule is re-applied or the user is fully removed.
- **`useExternalLicense`** in `groups rules get` is informational — set externally, not via these commands.
- **Group rule summary goes to stderr.** When piping `groups rules details` output, the rule header (entitled bundles, quotas) is on `stderr` so the JSON on `stdout` stays clean for `jq`.

---

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [Tenant Allocations](tenant-allocations.md) — separate license type for tenant runtime pools
- [Consumables Report](consumables-report.md) — consumption tracking
- [Full CLI command reference](../uip-commands.md)

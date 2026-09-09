# RBAC Read Commands

Use this guide when the request concerns tenant-scoped Insights users, roles, and groups. These commands read Insights role assignments, not org identity: creating users or managing org-level groups and roles is outside this skill. All commands use the active CLI session.

Tenant and organization context comes from the session. Never take it from the user and never invent a flag for it. User, role, and group GUIDs are different: accept one the user supplied or one a list returned, and pass it as the positional argument to the matching `get`. Never construct or guess one.

## Safe Output

These rows carry personal data that the other Insights commands do not: user and group email addresses, role IDs nested inside a principal, and a role `Resource` string that embeds the organization and tenant GUIDs.

The CLI withholds all three unless the caller explicitly chooses a structured format (`--output json`, `--output yaml`, or the `--json` alias). Run these six commands without `--output`. The format still resolves to json, so the envelope parses exactly the same, and the safe view is what you get: no `Email` on a user or group, roles as names rather than `{Id, Name}`, and no `Resource` on a role. This is the one place in the skill where Critical Rule 1 does not apply.

Add `--output json` only when the user asked for a field the safe view withholds. The whole workflow below runs without it, including the name-to-GUID join.

Keep these values out of what you write even on a call that returns them. Summarize with names and counts. Quote an email, a nested role ID, or a `Resource` string only when the user asked for that specific field. The same restriction covers anything written outside the conversation: a file, a commit, a ticket, or a PR body.

Some commands here are read-shaped rather than pure reads. See [Read-Shaped Side Effects](#read-shaped-side-effects) before reporting one as a plain lookup.

## Commands

### users list

List tenant users visible to the current caller with their Insights role names.

```bash
uip insights users list
```

**Key Data fields:** `Id`, `Name`, `Roles` as names. `Email` and the role `Id`s need `--output json`; keep both out of prose.

**Use when:** User asks which users have Insights access or needs a user ID for an exact lookup.

### users get

Get one Insights user by its GUID.

```bash
uip insights users get <user-id>
```

**Key Data fields:** `Id`, `Name`, `Roles` as names. `Email` and the role `Id`s need `--output json`; keep both out of prose.

**Use when:** User asks which Insights roles are assigned to one known user.

### roles list

List Insights roles visible to the current caller and their actions.

```bash
uip insights roles list
```

**Key Data fields:** `Id`, `Name`, `Actions`. `Resource` needs `--output json`; keep it out of prose.

**Use when:** User asks which Insights roles or actions are available. The list can be entitlement-filtered.

### roles get

Get one Insights role by its GUID.

```bash
uip insights roles get <role-id>
```

**Key Data fields:** `Id`, `Name`, `Actions`. `Resource` needs `--output json`; keep it out of prose.

**Use when:** User asks what one role permits, including a role omitted from the entitlement-filtered list.

### groups list

List tenant groups visible to the current caller with their Insights role names.

```bash
uip insights groups list
```

**Key Data fields:** `Id`, `Name`, `Roles` as names. `Email` and the role `Id`s need `--output json`; keep both out of prose.

**Use when:** User asks which groups have Insights roles or needs a group ID.

### groups get

Get one Insights group by its GUID.

```bash
uip insights groups get <group-id>
```

**Key Data fields:** `Id`, `Name`, `Roles` as names. `Email` and the role `Id`s need `--output json`; keep both out of prose.

**Use when:** User asks which Insights roles are assigned to one known group.

## Interpretation Rules

`Data` keys are PascalCase in the CLI's JSON output in both views: `Id`, `Name`, `Roles`, `Actions`. Reading a lowercase key returns `undefined`.

The three list commands take `--limit` and `--offset`. `--limit` defaults to 50, so a 50-row result is a full page rather than a complete list. Read `Pagination.Total` for the row count and `Pagination.HasMore` to tell whether rows remain. Keep going until `HasMore` is false before deciding a resource is absent, and say in the answer whether every page was retrieved. Raising `--limit` in one call is cheaper than walking `--offset`, because every offset page re-fetches the whole list from the backend. A `--limit` above 10000 is rejected locally.

These lists take no subject filters. There is no `--name`, `--email`, `--role`, or `--group`, so match a person or group by scanning the retrieved rows. The global flags still apply, `--output` among them.

The three `get` commands need a GUID. A value that is not a GUID is rejected locally as `ValidationError` with `ErrorCode: invalid_argument` and no request is sent, so that failure says nothing about whether the resource exists.

`roles list` and `roles get` return the role definitions with GUIDs and actions. On `users list` and `groups list` in the safe view, each role on a row is a bare name string, so the way to its definition is to match that name in `roles list` and use that row's `Id` with `roles get`. That join is the reason the safe view costs nothing here. Under the full view the same role arrives as `{Id, Name}` and the `Id` is on the row already, which saves one call and is not worth turning on the email for.

Passing an identifier as a command argument is not disclosure. Critical Rule 16 governs the answer you write, not the commands you run. Refer to the role by name in the answer.

A role name absent from the entitlement-filtered `roles list` can still resolve through `roles get`, whether the GUID came from the user or from a nested role on a user or group row.

The backend always sends the roles and actions arrays, and the CLI's projection emits `Roles` and `Actions` on every output row, so `[]` means the principal holds no Insights roles in this tenant or the role carries no actions. `Roles: []` is ordinary. `Actions: []` is not, because a role cannot be stored without at least one action, so name it as unexpected instead of summarizing it as an empty list.

`Name` can be null on a principal, and so can `Email` and `Resource` on the calls that return them. `Id` is never null. A row with a null `Name` is still a principal holding the roles on that row, so refer to it by `Id` and say the display name is unset.

A user whose directory lookup fails keeps its row with the name and email already stored, and nothing in the response marks that the lookup failed. So a display name on `users list` can be stale, and there is no way to tell from the output alone. Do not present a name as current identity evidence. Groups behave differently on the same failure: see Read-Shaped Side Effects.

## Failure Branches

Read the `Instructions` sentence the CLI returns with each of these. It carries the tenant-specific detail.

- `Data: []` with `Pagination.Total` of 0. The tenant answered and nothing was visible to the caller. On `roles list` it can also be entitlement filtering. It does not prove the tenant has no users, roles, or groups.
- `Data: []` with `Pagination.Total` above 0. `--offset` is past the last row. Lower it and run again.
- HTTP 404 on a list. A list route cannot miss for data reasons, so this is most likely a tenant without the Insights Portal service. Confirm by running the other two lists. If all three answer the same way, report it once as a provisioning gap rather than as an empty tenant.
- HTTP 404 on a `get`. The ID is not in the active tenant or is not visible to the caller. It is not proof the resource exists nowhere. On `groups get` this also covers a group that is in the tenant but whose directory entry does not resolve for this caller, which is the same condition that omits the row from `groups list`. A group missing from the list and 404ing on `get` is one cause, not two.
- HTTP 403, `ErrorCode: permission_denied`. The caller lacks the Insights Management View permission in the active tenant.
- HTTP 401 or no usable session. `Result: AuthenticationError`, exit 2. Correct the session and run again.
- HTTP 429, `ErrorCode: rate_limited` with `Retry: RetryLater`. This is the one branch where a later retry is right.
- HTTP 500 or 503, no `ErrorCode`, with the status in `Message`. The service or something it depends on failed. A directory outage surfaces here on the two groups commands, while `users list` and `users get` absorb the same outage and answer 200 with the stored name and email. Do not read a groups 5xx next to a users 200 as the two subjects disagreeing.
- A malformed response. `ErrorCode: unknown_error`, so read `Message` for the shape violation.

Outside the list 404 above, a failure on one list says nothing about the other two. When the request names users, groups, and roles, run all three and report each outcome separately.

## Read-Shaped Side Effects

Three of these commands do more than fetch:

- `roles list` can make a cached entitlement call to Licensing.
- `groups get` can persist refreshed directory name and email fields for the group.
- `groups list` can omit a group whose directory entry does not resolve.

The group omission is invisible in the response: `Pagination.Total` counts only the rows that survived, and no field marks the drop. So carry the caveat on every groups answer instead of waiting for a signal. Directory filtering can omit an unresolved group, which makes `groups list` a lower bound on the groups that hold Insights roles.

`users list` keeps a row whose directory enrichment failed, so it needs no such caveat. It is still bounded by the caller's visibility and by the pages retrieved.

Name the Licensing call only when the user asks what `roles list` costs or why a role is missing.

## Investigation Workflow: Inspect Insights RBAC Configuration

1. Run one list per subject the request names: `users list` for who has access, `groups list` for group assignments, `roles list` for what roles permit. A request naming more than one subject gets more than one list. Add a further list call only to resolve a name or ID an earlier one surfaced.
2. Use a `get` command only for an ID the user supplied or a list returned.
3. Page each list until `Pagination.HasMore` is false before summarizing.
4. If a command is denied, run `uip login status --output json` and report its `Tenant` value with the boundary: reading Insights RBAC needs the Insights Management View permission in that tenant. Do not suggest changing access from this skill.
5. If no row matches a name the user gave, report that no visible row in the active tenant matched and say which pages were retrieved. Do not report that the user or group does not exist, and do not fall back to org-level identity commands.

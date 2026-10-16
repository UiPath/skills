# Group Management

Workflows for managing groups and group membership via `uip admin groups`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#groups--uip-admin-groups).

## Group Types

| Type | Description | Can Delete? |
|------|-------------|-------------|
| `BuiltIn` | System groups (e.g., Administrators) | No |
| `Custom` | User-created groups | Yes |

## Workflow: List and Inspect Groups

```bash
uip admin groups list --output json
uip admin groups get <GROUP_ID> --output json
uip admin groups members list <GROUP_ID> --output json
```

## Workflow: Create a Group

1. Check for duplicates: `uip admin groups list --output json`
2. Create: `uip admin groups create "<GROUP_NAME>" --output json`
3. Verify: `uip admin groups list --output json`

## Workflow: Manage Group Membership

Group membership commands use **user IDs** (UUIDs), not usernames. Always resolve IDs first.

### Add Members

1. Resolve user IDs: `uip admin users list --search "<USER_NAME>" --output json`
2. Add: `uip admin groups members add <GROUP_ID> --user-ids "<USER_ID_1>,<USER_ID_2>" --output json`
3. Verify: `uip admin groups members list <GROUP_ID> --output json`

### Remove Members

1. List current members: `uip admin groups members list <GROUP_ID> --output json`
2. Remove: `uip admin groups members revoke <GROUP_ID> --user-ids "<USER_ID>" --output json`

## Workflow: Rename a Group

```bash
uip admin groups update <GROUP_ID> --name "<NEW_NAME>" --output json
```

## Workflow: Delete a Group

1. Verify it is a custom group (not built-in): `uip admin groups get <GROUP_ID> --output json` — check `type` is `Custom`.
2. Confirm with user.
3. Delete: `uip admin groups delete <GROUP_ID> --output json`

## Pagination for Members

`--all` fetches every member in one call, and the envelope states whether you have
the whole group:

```bash
uip admin groups members list <GROUP_ID> --all --output json
```

Read `Pagination.HasMore`, never the row count. `false` means these rows are the
complete membership. `true` means they are not, and a `Warning` says so in words.
`--all` walks up to 10,000 members and reports `HasMore: true` if it stops there.

Without `--all` the command returns **one page, 50 entries by default**: a group
with 80 members looks like a group with 50. `Pagination` still rides the envelope,
so the page is self-describing either way.

```bash
uip admin groups members list <GROUP_ID> --limit 50 --offset 0 --output json
uip admin groups members list <GROUP_ID> --limit 50 --offset 50 --output json
```

Keep raising `--offset` by `--limit` until `Pagination.HasMore` is `false`. `--all`
conflicts with both flags, so past the 10,000 cap the offset walk is the only route.

**On a CLI that rejects `--all`** as an unknown option, `Pagination` is absent too:
page until one comes back short or empty, and treat that as the weaker signal it is
— a service that clamps `top` can return a short page that is not the last.

### Never conclude non-membership from a `members list` page

A user missing from a page is **not** evidence they are not in the group — they may
be on a page you did not fetch. This has already caused an outage: an agent read one
page, decided an admin account was not an admin, and “fixed” it with `members add`
+ `members revoke`, removing access the account genuinely had.

Resolve membership from the account side instead — one call, no paging:

```bash
uip admin users list --search "<email>" --output json   # read GroupIDs on the match
```

If `GroupIDs` contains the group id, the user is a member.

An `--all` listing that reports `HasMore: false` is also conclusive — that is the
whole group. The account-side lookup still wins for a single account: one call, no
10,000-member cap, and it works on a CLI too old to have `--all`.

Whatever the answer, changing it is not a remedy for an authorization error — see
Critical Rule 34.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Group name taken | Choose a different name |
| `No fields to update` | No `--name` flag provided | Provide `--name` to rename |
| `group not found` | Invalid group ID | Run `groups list` to find the correct ID |
| Cannot delete built-in group | Attempting to delete a system group | Only custom groups can be deleted |

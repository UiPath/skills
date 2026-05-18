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

```bash
uip admin groups members list <GROUP_ID> --limit 50 --offset 0 --output json
uip admin groups members list <GROUP_ID> --limit 50 --offset 50 --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Group name taken | Choose a different name |
| `No fields to update` | No `--name` flag provided | Provide `--name` to rename |
| `group not found` | Invalid group ID | Run `groups list` to find the correct ID |
| Cannot delete built-in group | Attempting to delete a system group | Only custom groups can be deleted |

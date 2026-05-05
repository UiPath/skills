# Group Management

Workflows for managing Identity Server groups and group membership via `uip admin groups`.

## Group Types

| Type | Description | Can Delete? |
|------|-------------|-------------|
| `BuiltIn` | System groups (e.g., Administrators) | No |
| `Custom` | User-created groups | Yes |

## Workflow: List and Inspect Groups

```bash
# List all groups
uip admin groups list --output json

# Get group details
uip admin groups get <GROUP_ID> --output json

# List group members
uip admin groups get-members <GROUP_ID> --output json
```

## Workflow: Create a Group

1. List existing groups to avoid duplicates:
   ```bash
   uip admin groups list --output json
   ```

2. Create the group:
   ```bash
   uip admin groups create "<GROUP_NAME>" \
     --output json
   ```

3. Verify creation:
   ```bash
   uip admin groups list --output json
   ```

## Workflow: Manage Group Membership

Group membership commands use **user IDs** (UUIDs), not usernames. Always resolve IDs first.

### Add Members

1. Resolve user IDs:
   ```bash
   uip admin users list --search "<USER_NAME>" --output json
   ```

2. Add users to the group:
   ```bash
   uip admin groups add-members <GROUP_ID> \
     --user-ids "<USER_ID_1>,<USER_ID_2>" \
     --output json
   ```

3. Verify membership:
   ```bash
   uip admin groups get-members <GROUP_ID> --output json
   ```

### Remove Members

1. List current members to get IDs:
   ```bash
   uip admin groups get-members <GROUP_ID> --output json
   ```

2. Remove specific users:
   ```bash
   uip admin groups remove-members <GROUP_ID> \
     --user-ids "<USER_ID>" \
     --output json
   ```

## Workflow: Rename a Group

```bash
uip admin groups update <GROUP_ID> \
  --name "<NEW_NAME>" \
  --output json
```

## Workflow: Delete a Group

1. Verify it is a custom group (not built-in):
   ```bash
   uip admin groups get <GROUP_ID> --output json
   ```
   Check that `type` is `Custom`. Built-in groups cannot be deleted.

2. Confirm with the user.

3. Delete:
   ```bash
   uip admin groups delete <GROUP_ID> --output json
   ```

## Pagination for Members

```bash
# First page
uip admin groups get-members <GROUP_ID> \
  --limit 50 --offset 0 --output json

# Next page
uip admin groups get-members <GROUP_ID> \
  --limit 50 --offset 50 --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Group name taken | Choose a different name |
| `No fields to update` | No `--name` flag provided | Provide `--name` to rename |
| `group not found` | Invalid group ID | Run `groups list` to find the correct ID |
| Cannot delete built-in group | Attempting to delete a system group | Only custom groups can be deleted |

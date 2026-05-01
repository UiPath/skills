# Robot Account Management

Workflows for managing Identity Server robot accounts via `uip admin identity robot-accounts`.

Robot accounts represent unattended automation identities — they authenticate using Client ID + Secret (OAuth2) and run processes without human interaction.

## Workflow: List and Inspect Robot Accounts

```bash
# List all robot accounts
uip admin identity robot-accounts list --organization <ORG_ID> --output json

# Search for a specific robot account
uip admin identity robot-accounts list --organization <ORG_ID> --search "bot-name" --output json

# Get full details
uip admin identity robot-accounts get <ROBOT_ACCOUNT_ID> \
  --organization <ORG_ID> --output json
```

## Workflow: Create a Robot Account

1. Check for existing robot accounts to avoid name collisions:
   ```bash
   uip admin identity robot-accounts list --organization <ORG_ID> \
     --search "<NAME>" --output json
   ```

2. Create the robot account:
   ```bash
   uip admin identity robot-accounts create "<NAME>" \
     --organization <ORG_ID> \
     --display-name "<DISPLAY_NAME>" \
     --output json
   ```

3. Verify creation:
   ```bash
   uip admin identity robot-accounts list --organization <ORG_ID> \
     --search "<NAME>" --output json
   ```

4. **Next step:** Generate credentials for the robot account. See [external-app-management.md](external-app-management.md) for creating an external app with Client ID/Secret.

## Workflow: Update a Robot Account

```bash
uip admin identity robot-accounts update <ROBOT_ACCOUNT_ID> \
  --organization <ORG_ID> \
  --display-name "<NEW_DISPLAY_NAME>" \
  --output json
```

## Workflow: Delete a Robot Account

1. Confirm the robot account exists:
   ```bash
   uip admin identity robot-accounts get <ROBOT_ACCOUNT_ID> \
     --organization <ORG_ID> --output json
   ```

2. Confirm with the user before proceeding.

3. Delete:
   ```bash
   uip admin identity robot-accounts delete <ROBOT_ACCOUNT_ID> \
     --organization <ORG_ID> --output json
   ```

## Pagination and Sorting

```bash
# Paginated list
uip admin identity robot-accounts list --organization <ORG_ID> \
  --limit 10 --offset 0 --output json

# Sorted by name
uip admin identity robot-accounts list --organization <ORG_ID> \
  --order-by "Name" --order-direction "asc" --output json
```

## Robot Account vs External App

Robot accounts and external apps serve different purposes but work together:

| Concept | Purpose |
|---------|---------|
| **Robot account** | The identity — who the robot is |
| **External app** | The credentials — how the robot authenticates (Client ID + Secret) |

To fully onboard a robot, you need both. See [onboarding-workflows.md](onboarding-workflows.md) for the end-to-end flow.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Robot account name taken | Choose a unique name |
| `No fields to update` | No `--display-name` flag | Provide `--display-name` |
| `not found` | Invalid robot account ID | Run `robot-accounts list` to find the correct ID |

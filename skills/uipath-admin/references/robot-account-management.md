# Robot Account Management

Workflows for managing Identity Server robot accounts via `uip admin robot-accounts`.

Robot accounts represent unattended automation identities that run processes without human interaction.

## Credential Model

Robot accounts use a dedicated credential mechanism managed by Orchestrator — when a robot is connected to a machine, Orchestrator provisions a robot-specific Client ID + Secret bound to the system-level `Robot.S2S` client. This is **separate from external apps**.

| Concept | Purpose | Managed By |
|---------|---------|------------|
| **Robot account** | Identity — who the robot is | Identity Server (`uip admin`) |
| **Robot credentials** | Per-robot Client ID + Secret for machine auth | Orchestrator (machine connection) |
| **External app** | OAuth2 client for API integrations, CI/CD pipelines | Identity Server (`uip admin`) |

> **Do not create external apps as robot credentials.** External apps are for third-party integrations and CI/CD — not for connecting robots to machines. Robot credentials are provisioned automatically when configuring a machine connection in Orchestrator.

## Workflow: List and Inspect Robot Accounts

```bash
# List all robot accounts
uip admin robot-accounts list --output json

# Search for a specific robot account
uip admin robot-accounts list --search "bot-name" --output json

# Get full details
uip admin robot-accounts get <ROBOT_ACCOUNT_ID> \
  --output json
```

## Workflow: Create a Robot Account

1. Check for existing robot accounts to avoid name collisions:
   ```bash
   uip admin robot-accounts list \
     --search "<NAME>" --output json
   ```

2. Create the robot account:
   ```bash
   uip admin robot-accounts create "<NAME>" \
     --display-name "<DISPLAY_NAME>" \
     --output json
   ```

3. Verify creation:
   ```bash
   uip admin robot-accounts list \
     --search "<NAME>" --output json
   ```

4. **Next steps:** Assign to groups for role-based access, then configure machine connection in Orchestrator (which provisions robot credentials automatically).

## Workflow: Update a Robot Account

```bash
uip admin robot-accounts update <ROBOT_ACCOUNT_ID> \
  --display-name "<NEW_DISPLAY_NAME>" \
  --output json
```

## Workflow: Delete a Robot Account

1. Confirm the robot account exists:
   ```bash
   uip admin robot-accounts get <ROBOT_ACCOUNT_ID> \
     --output json
   ```

2. Confirm with the user before proceeding.

3. Delete:
   ```bash
   uip admin robot-accounts delete <ROBOT_ACCOUNT_ID> \
     --output json
   ```

## Pagination and Sorting

```bash
# Paginated list
uip admin robot-accounts list \
  --limit 10 --offset 0 --output json

# Sorted by name
uip admin robot-accounts list \
  --order-by "Name" --order-direction "asc" --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Robot account name taken | Choose a unique name |
| `No fields to update` | No `--display-name` flag | Provide `--display-name` |
| `not found` | Invalid robot account ID | Run `robot-accounts list` to find the correct ID |

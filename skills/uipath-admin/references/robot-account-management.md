# Robot Account Management

Workflows for managing robot accounts via `uip admin robot-accounts`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#robot-accounts--uip-admin-robot-accounts).

Robot accounts represent unattended automation identities that run processes without human interaction.

## Credential Model

See [SKILL.md — Robot Accounts vs External Apps](../SKILL.md#robot-accounts-vs-external-apps) for the full distinction. Key point: robot credentials are provisioned by Orchestrator during machine connection — do not create external apps as robot credentials.

## Workflow: Create a Robot Account

1. Check for duplicates: `uip admin robot-accounts list --search "<NAME>" --output json`
2. Create: `uip admin robot-accounts create "<NAME>" --display-name "<DISPLAY_NAME>" --output json`
3. Verify: `uip admin robot-accounts list --search "<NAME>" --output json`
4. **Next steps:** Assign to groups for role-based access, then configure machine connection in Orchestrator (which provisions robot credentials automatically).

## Workflow: Update a Robot Account

```bash
uip admin robot-accounts update <ROBOT_ACCOUNT_ID> --display-name "<NEW_DISPLAY_NAME>" --output json
```

## Workflow: Delete a Robot Account

1. Confirm exists: `uip admin robot-accounts get <ROBOT_ACCOUNT_ID> --output json`
2. Confirm with user.
3. Delete: `uip admin robot-accounts delete <ROBOT_ACCOUNT_ID> --output json`

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Robot account name taken | Choose a unique name |
| `No fields to update` | No `--display-name` flag | Provide `--display-name` |
| `not found` | Invalid robot account ID | Run `robot-accounts list` to find the correct ID |

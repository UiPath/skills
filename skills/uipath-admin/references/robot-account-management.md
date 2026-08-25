# Robot Account Management

Manage robot accounts with `uip admin robot-accounts`. For syntax and flags, see [identity-commands.md](identity-commands.md#robot-accounts--uip-admin-robot-accounts).

Robot accounts are unattended automation identities that run processes without human interaction.

## Credential Model

See [Key Concepts — Robot Accounts vs External Apps](key-concepts.md#robot-accounts-vs-external-apps). Orchestrator provisions robot credentials during machine connection; do not create external apps as robot credentials.

## Create a Robot Account

1. Run `uip admin robot-accounts list --search "<NAME>" --output json` to check for duplicates.
2. Run `uip admin robot-accounts create "<NAME>" --display-name "<DISPLAY_NAME>" --output json`.
3. Run `uip admin robot-accounts list --search "<NAME>" --output json` to verify.
4. Assign the account to groups for role-based access, then configure machine connection in Orchestrator, which provisions robot credentials automatically.

## Update a Robot Account

Run:

```bash
uip admin robot-accounts update <ROBOT_ACCOUNT_ID> --display-name "<NEW_DISPLAY_NAME>" --output json
```

## Delete a Robot Account

1. Run `uip admin robot-accounts get <ROBOT_ACCOUNT_ID> --output json` to confirm it exists.
2. Confirm deletion with the user.
3. Run `uip admin robot-accounts delete <ROBOT_ACCOUNT_ID> --output json`.

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `already exists` | Robot account name taken | Choose a unique name |
| `No fields to update` | No `--display-name` flag | Provide `--display-name` |
| `not found` | Invalid robot account ID | Run `robot-accounts list` to find the correct ID |
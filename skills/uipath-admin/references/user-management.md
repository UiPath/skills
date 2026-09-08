# User Management

Workflows for `uip admin users`. See [identity-commands.md](identity-commands.md#users--uip-admin-users) for full syntax and flags.

## Onboard a User (canonical flow)

1. Verify login:

   ```bash
   uip login status --output json
   ```

   If not logged in, run `uip login`. The CLI reads the org ID from the active session automatically.

2. Default to inviting human users:

   ```bash
   uip admin users invite \
     --email "<USER_EMAIL>" \
     --name "<FIRST_NAME>" \
     --surname "<LAST_NAME>" \
     --output json
   ```

   If the user asks to “add” or “create” a user, default to `invite` and confirm before using `create`. The invite sends an email for credential setup and organization acceptance; the user must accept it to complete onboarding. Include `--name` and `--surname` when known, parsing first and last names from context. Invite one user at a time; these flags apply to the entire request.

3. After acceptance, find the user once:

   ```bash
   uip admin users list \
     --search "<USER_EMAIL>" --output json
   ```

4. List groups and assign the user:

   ```bash
   uip admin groups list --output json
   uip admin groups members add <GROUP_ID> \
     --user-ids "<USER_ID>" \
     --output json
   ```

   Before `members add`, apply the principal-resolution protocol: echo `Principal: <displayName> (<userName>) — <id>` from the `users list` result (SKILL.md Rule 5).

## Discover Existing Users

```bash
uip admin users list --output json
uip admin users list --search "john" --output json
uip admin users get <USER_ID> --output json
```

## Create a User (Direct Provisioning)

Ask for confirmation before using `create`. Explain that `users invite` is standard for human onboarding and confirm that direct account creation is intended. Use `create` only when direct provisioning is required, such as service accounts, migrations, or batch imports.

1. Check for duplicates:

   ```bash
   uip admin users list --search "<USERNAME>" --output json
   ```

2. Create the user:

   ```bash
   uip admin users create "<USERNAME>" --email "<EMAIL>" --name "<FIRST_NAME>" --surname "<LAST_NAME>" --output json
   ```

3. Verify:

   ```bash
   uip admin users list --search "<USERNAME>" --output json
   ```

## Update a User

1. Get current details:

   ```bash
   uip admin users get <USER_ID> --output json
   ```

2. Update at least one field:

   ```bash
   uip admin users update <USER_ID> --email "<NEW_EMAIL>" --output json
   ```

## Delete a User

1. Confirm the user ID:

   ```bash
   uip admin users get <USER_ID> --output json
   ```

2. Confirm with the user before proceeding.

3. Delete:

   ```bash
   uip admin users delete <USER_ID> --output json
   ```

## Pagination and Sorting

```bash
uip admin users list --limit 20 --offset 0 --output json
uip admin users list --sort-by "UserName" --sort-order "asc" --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Username taken | Choose a different username |
| `No fields to update` | No flags provided to update | Provide `--email`, `--name`, or `--surname` |
| `user not found` | Invalid user ID | Run `users list` to find the correct ID |
| `HTTP 403` | Insufficient permissions | User needs admin role in the organization |

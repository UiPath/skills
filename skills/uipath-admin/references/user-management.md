# User Management

Workflows for managing users via `uip admin users`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#users--uip-admin-users).

## Workflow: Discover Existing Users

```bash
uip admin users list --output json
uip admin users list --search "john" --output json
uip admin users get <USER_ID> --output json
```

## Workflow: Invite Users by Email (Preferred)

> **`users invite` is the preferred method for adding users.** It sends an invitation email, letting the user set up their own credentials and accept the org invitation. Use `users create` only when direct account provisioning is required (e.g., service accounts, migration scripts). If the user asks to "add" or "create" a user, default to `invite` and confirm before using `create` instead.

```bash
uip admin users invite \
  --email "user@example.com" \
  --name "John" \
  --surname "Doe" \
  --output json
```

- **Always include `--name` and `--surname` when the user's name is known.** Parse first/last name from context (e.g., "Alice Chen" → `--name "Alice" --surname "Chen"`).
- Invite one user at a time — `--name`/`--surname` apply to the entire request
- The invited user receives an email and must accept to complete onboarding

## Workflow: Create a User (Direct Provisioning)

> **Ask for confirmation before using this command.** Explain that `users invite` is the standard method for human onboarding and confirm the user specifically wants direct account creation.

Use `create` instead of `invite` when:
- **Migrations & batch imports** — syncing users from external systems
- **Service accounts** — accounts with admin-set passwords, no email workflow needed
- **Admin-provisioned access** — user needs immediate login without waiting for email acceptance
- **No email available** — `create` does not require an email address; `invite` does

1. Check for duplicates: `uip admin users list --search "<USERNAME>" --output json`
2. Create: `uip admin users create "<USERNAME>" --email "<EMAIL>" --name "<FIRST_NAME>" --surname "<LAST_NAME>" --output json`
3. Verify: `uip admin users list --search "<USERNAME>" --output json`

## Workflow: Update a User

1. Get current details: `uip admin users get <USER_ID> --output json`
2. Update (at least one field required): `uip admin users update <USER_ID> --email "<NEW_EMAIL>" --output json`

## Workflow: Delete a User

1. Confirm user ID: `uip admin users get <USER_ID> --output json`
2. Confirm with user before proceeding.
3. Delete: `uip admin users delete <USER_ID> --output json`

## Pagination and Sorting

```bash
uip admin users list --limit 20 --offset 0 --output json
uip admin users list --order-by "UserName" --order-direction "asc" --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Username taken | Choose a different username |
| `No fields to update` | No flags provided to update | Provide `--email`, `--name`, or `--surname` |
| `user not found` | Invalid user ID | Run `users list` to find the correct ID |
| `HTTP 403` | Insufficient permissions | User needs admin role in the organization |

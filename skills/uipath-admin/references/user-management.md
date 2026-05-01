# User Management

Workflows for managing Identity Server users via `uip admin identity users`.

## Workflow: Discover Existing Users

Before creating or modifying users, list what exists.

```bash
# List all users in the organization
uip admin identity users list --organization <ORG_ID> --output json

# Search for a specific user
uip admin identity users list --organization <ORG_ID> --search "john" --output json

# Get full details for a specific user
uip admin identity users get <USER_ID> --output json
```

## Workflow: Create a User

1. List existing users to avoid duplicates:
   ```bash
   uip admin identity users list --organization <ORG_ID> --search "<USERNAME>" --output json
   ```

2. If the user does not exist, create them:
   ```bash
   uip admin identity users create "<USERNAME>" \
     --organization <ORG_ID> \
     --email "<EMAIL>" \
     --name "<FIRST_NAME>" \
     --surname "<LAST_NAME>" \
     --output json
   ```

3. Verify creation:
   ```bash
   uip admin identity users list --organization <ORG_ID> --search "<USERNAME>" --output json
   ```

## Workflow: Invite Users by Email

Invite one or more users to join the organization via email.

```bash
uip admin identity users invite \
  --email "user1@example.com,user2@example.com" \
  --name "John" \
  --surname "Doe" \
  --output json
```

- `--name` and `--surname` are applied to all invited users (use for single invites)
- For bulk invites with different names, invite one at a time
- The invited user receives an email and must accept to complete onboarding

## Workflow: Update a User

1. Get current user details:
   ```bash
   uip admin identity users get <USER_ID> --output json
   ```

2. Update the desired fields (at least one is required):
   ```bash
   uip admin identity users update <USER_ID> \
     --email "<NEW_EMAIL>" \
     --name "<NEW_NAME>" \
     --surname "<NEW_SURNAME>" \
     --output json
   ```

## Workflow: Delete a User

1. Confirm the user ID:
   ```bash
   uip admin identity users get <USER_ID> --output json
   ```

2. Confirm with the user before proceeding.

3. Delete:
   ```bash
   uip admin identity users delete <USER_ID> --output json
   ```

## Pagination

For large user lists, use `--limit` and `--offset`:

```bash
# First page (20 users)
uip admin identity users list --organization <ORG_ID> --limit 20 --offset 0 --output json

# Second page
uip admin identity users list --organization <ORG_ID> --limit 20 --offset 20 --output json
```

## Sorting

Sort results by field and direction:

```bash
uip admin identity users list --organization <ORG_ID> \
  --order-by "UserName" \
  --order-direction "asc" \
  --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | Username taken | Choose a different username |
| `No fields to update` | No flags provided to update | Provide `--email`, `--name`, or `--surname` |
| `user not found` | Invalid user ID | Run `users list` to find the correct ID |
| `HTTP 403` | Insufficient permissions | User needs admin role in the organization |

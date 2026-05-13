# PAT Management

Workflows for managing personal access tokens via `uip admin pat`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#personal-access-tokens--uip-admin-pat).

PATs provide scoped API authentication for users — an alternative to OAuth2 client credentials when a user-context token is needed.

## Workflow: Create a PAT

1. Discover available scopes: `uip admin scopes list --output json`
2. Create with description, expiration, and scopes:
   ```bash
   uip admin pat create \
     --description "CI/CD pipeline token" \
     --expiration "2027-01-15" \
     --scopes "OR.Folders.Read,OR.Jobs.Read" \
     --output json
   ```
3. **Save the token value immediately.** It appears only in the creation response.

## Workflow: List PATs

List your own tokens:
```bash
uip admin pat list --output json
```

List all tokens in the organization (admin only):
```bash
uip admin pat list --scope all --output json
```

Search by user:
```bash
uip admin pat list --search "john" --output json
```

## Workflow: Revoke a PAT

Confirm with user before revoking — this permanently invalidates the token.

```bash
uip admin pat revoke <TOKEN_ID> --output json
```

## Workflow: Regenerate a PAT

Regenerate with a new expiration. Returns new token value (shown only once):

```bash
uip admin pat regenerate <TOKEN_ID> --expiration "2028-01-15" --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `not found` | Invalid token ID | Run `pat list` to find correct ID |
| `Invalid expiration` | Bad date format | Use ISO 8601: `YYYY-MM-DD` |
| `scope not found` | Invalid scope name | Run `uip admin scopes list` to find valid scopes |
| `HTTP 403` | Listing all tokens without admin role | Omit `--scope all` to list only your own |

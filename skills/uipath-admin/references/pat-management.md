# PAT Management

Manage personal access tokens with `uip admin pat`. See [identity-commands.md](identity-commands.md#personal-access-tokens--uip-admin-pat) for full syntax and flags.

PATs provide scoped API authentication for users when user-context authentication is required instead of OAuth2 client credentials.

## Lifetime Constraints

- Minimum expiration: 1 day from now
- Default maximum: 360 days (~1 year)
- Hard maximum: 1,800 days (~5 years), configurable per org
- Maximum tokens per user: 5 by default, up to 50
- Maximum description length: 256 characters

## Create a PAT

1. Run `uip admin scopes list --output json` to discover available scopes.
2. Run:
   ```bash
   uip admin pat create \
     --description "CI/CD pipeline token" \
     --expiration "2027-01-15" \
     --scope "OR.Folders.Read,OR.Jobs.Read" \
     --output json
   ```
3. Save the token value immediately; it appears only in the creation response.

## List PATs

- Run `uip admin pat list --output json` to list your own tokens.
- Run `uip admin pat list --scope all --output json` to list all organization tokens; admin access is required.
- Run `uip admin pat list --search "john" --output json` to search by user.

## Revoke a PAT

Confirm with the user before revoking; revocation permanently invalidates the token. Run:

```bash
uip admin pat revoke <TOKEN_ID> --output json
```

## Regenerate a PAT

Run the following with a new expiration. The new token value is returned only once:

```bash
uip admin pat regenerate <TOKEN_ID> --expiration "2028-01-15" --output json
```

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `not found` | Invalid token ID | Run `pat list` to find the correct ID |
| `Invalid expiration` | Bad date format | Use ISO 8601: `YYYY-MM-DD` |
| `expiration too small` | Less than 1 day from now | Set expiration at least 1 day in the future |
| `expiration too large` | Exceeds the organization maximum (default 360 days) | Shorten the expiration |
| `limit reached` | Maximum tokens per user reached (default 5) | Revoke unused tokens first |
| `scope not found` | Invalid scope name | Run `uip admin scopes list` to find valid scopes |
| `HTTP 403` | Attempted to list all tokens without the admin role | Omit `--scope all` to list only your own tokens |

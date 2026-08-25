# External App Management

Workflows for OAuth2 external clients via `uip admin external-apps`. See [identity-commands.md](identity-commands.md#external-apps--uip-admin-external-apps) for full syntax and flags.

External apps provide Client ID and Secret credentials for API integrations, CI/CD, and external systems. **They are not robot credentials.** See [Key Concepts — Robot Accounts vs External Apps](key-concepts.md#robot-accounts-vs-external-apps).

## Scopes and Grant Types

Run `uip admin scopes list --output json` to discover valid scopes.

- `--app-scope` grants app permissions for `client_credentials` (for example, `uip login --client-id`).
- `--user-scope` delegates user permissions for the `authorization_code` browser flow.
- Apps may have both, but each grant must use its matching scopes. Requesting user scopes through `client_credentials` fails with `not allowed to access User scopes`.

## Create an External App

### Confidential app (server-side)

1. Check for duplicates by running `uip admin external-apps list --output json`.
2. Run:
   ```bash
   uip admin external-apps create "<APP_NAME>" \
     --app-scope "OR.Folders,OR.Assets,OR.Jobs" \
     --output json
   ```
3. Save the response immediately: `id` is the Client ID and `secret` is the Client Secret, shown only once.

### Public app (SPA/mobile)

Run:
```bash
uip admin external-apps create "<APP_NAME>" \
  --non-confidential \
  --user-scope "OR.Folders.Read,OR.Jobs.Read" \
  --redirect-uri "https://myapp.example.com/callback" \
  --output json
```

Public apps have no client secret, require `--redirect-uri`, and support only `--user-scope`. Do not use `--app-scope` with `--non-confidential`; create a confidential app for app-only scopes.

### App with both scope types

Run:
```bash
uip admin external-apps create "<APP_NAME>" \
  --app-scope "OR.Folders,OR.Jobs" \
  --user-scope "OR.Folders.Read" \
  --redirect-uri "https://myapp.example.com/callback" \
  --output json
```

Any app with `--user-scope` requires `--redirect-uri` for authorization-code flow.

## Secrets

Run the following to generate a secret; its value is shown only once:
```bash
uip admin external-apps generate-secret <CLIENT_ID> --description "Rotated secret" --expiration "2027-06-01" --output json
```

Confirm with the user first, then run the following to delete a secret; only the secret ID is required:
```bash
uip admin external-apps delete-secret <SECRET_ID> --output json
```

## Update an External App

Provide at least one update flag. Scopes are replaced, not merged; provide the complete list.

```bash
uip admin external-apps update <CLIENT_ID> \
  --name "<NEW_NAME>" \
  --app-scope "OR.Folders,OR.Jobs" \
  --output json
```

Valid update fields are `--name`, `--app-scope`, `--user-scope`, and `--redirect-uri`.

## Delete an External App

Confirm with the user first; deletion revokes all secrets and access. Then run:
```bash
uip admin external-apps delete <CLIENT_ID> --output json
```

## Federated Credentials

Use workload identity federation with external identity providers such as GitHub Actions or Azure AD to authenticate without client secrets.

### Create

```bash
uip admin external-apps federated-credentials create <CLIENT_ID> \
  --name "GitHub Actions" \
  --issuer "https://token.actions.githubusercontent.com" \
  --audience "<AUDIENCE>" \
  --subject "repo:myorg/myrepo:ref:refs/heads/main" \
  --output json
```

### List

```bash
uip admin external-apps federated-credentials list <CLIENT_ID> --output json
```

### Update

All fields are required; updates are full replacements.

```bash
uip admin external-apps federated-credentials update <CLIENT_ID> <CREDENTIAL_ID> \
  --name "Updated Name" \
  --issuer "https://token.actions.githubusercontent.com" \
  --audience "<AUDIENCE>" \
  --subject "repo:myorg/myrepo:ref:refs/heads/release" \
  --output json
```

### Delete

Confirm with the user first, then run:
```bash
uip admin external-apps federated-credentials delete <CLIENT_ID> <CREDENTIAL_ID> --output json
```

## Authenticate with an External App

Run this for non-interactive login:
```bash
uip login --client-id "<CLIENT_ID>" --client-secret "<CLIENT_SECRET>" --tenant "<TENANT_NAME>" --output json
```

Use it for CI/CD pipelines, external API integrations, service-to-service calls, and automated scripts.

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `already exists` | App name taken | Choose a unique name |
| `No fields to update` | No update flags provided | Provide `--name`, `--app-scope`, `--user-scope`, or `--redirect-uri` |
| `not found` | Invalid client ID | Run `external-apps list` to find the correct ID |
| `scope not found` | Invalid scope name | Run `uip admin scopes list` to find valid scopes |
| Non-confidential + `--app-scope` | Public apps cannot use app scopes | Use `--user-scope` only |
| User scopes without redirect URI | Authorization-code flow requires redirect | Add `--redirect-uri` |
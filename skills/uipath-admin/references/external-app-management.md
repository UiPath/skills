# External App Management

Workflows for managing OAuth2 external clients via `uip admin external-apps`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#external-apps--uip-admin-external-apps).

External apps provide Client ID + Secret credentials for API integrations, CI/CD pipelines, and external systems.

> **External apps are NOT robot credentials.** See [SKILL.md — Robot Accounts vs External Apps](../SKILL.md#robot-accounts-vs-external-apps).

## Scope Types

See [SKILL.md — Scope Types](../SKILL.md#scope-types) for the `--app-scope` vs `--user-scope` distinction. Discover available scopes: `uip admin scopes list --output json`

## Workflow: Create a Confidential App (Server-Side)

1. Check for duplicates: `uip admin external-apps list --output json`
2. Create with app scopes:
   ```bash
   uip admin external-apps create "<APP_NAME>" \
     --app-scope "OR.Folders,OR.Assets,OR.Jobs" \
     --output json
   ```
3. **Save the response immediately.** It contains `id` (Client ID) and `secret` (Client Secret — shown only once).

## Workflow: Create a Public App (SPA/Mobile)

Non-confidential apps have no client secret. Require `--redirect-uri` and only support user scopes.

```bash
uip admin external-apps create "<APP_NAME>" \
  --non-confidential \
  --user-scope "OR.Folders.Read,OR.Jobs.Read" \
  --redirect-uri "https://myapp.example.com/callback" \
  --output json
```

## Workflow: Create App with Both Scope Types

```bash
uip admin external-apps create "<APP_NAME>" \
  --app-scope "OR.Folders,OR.Jobs" \
  --user-scope "OR.Folders.Read" \
  --redirect-uri "https://myapp.example.com/callback" \
  --output json
```

Apps with `--user-scope` require `--redirect-uri` for OAuth2 authorization code flow.

## Workflow: Generate/Delete Secrets

Generate (value shown only once):
```bash
uip admin external-apps generate-secret <CLIENT_ID> --description "Rotated secret" --expiration "2027-06-01" --output json
```

Delete (only secret ID needed):
```bash
uip admin external-apps delete-secret <SECRET_ID> --output json
```

## Workflow: Update an External App

At least one field required. Scopes are **replaced, not merged** — provide complete list.

```bash
uip admin external-apps update <CLIENT_ID> \
  --name "<NEW_NAME>" \
  --app-scope "OR.Folders,OR.Jobs" \
  --output json
```

## Federated Credentials

Enable workload identity federation with external identity providers (GitHub Actions, Azure AD) — authenticate without client secrets.

### Create a Federated Credential

```bash
uip admin external-apps federated-credentials create <CLIENT_ID> \
  --name "GitHub Actions" \
  --issuer "https://token.actions.githubusercontent.com" \
  --audience "api://AzureADTokenExchange" \
  --subject "repo:myorg/myrepo:ref:refs/heads/main" \
  --output json
```

### List Federated Credentials

```bash
uip admin external-apps federated-credentials list <CLIENT_ID> --output json
```

### Update a Federated Credential

All fields are required on update (full replace):

```bash
uip admin external-apps federated-credentials update <CLIENT_ID> <CREDENTIAL_ID> \
  --name "Updated Name" \
  --issuer "https://token.actions.githubusercontent.com" \
  --audience "api://AzureADTokenExchange" \
  --subject "repo:myorg/myrepo:ref:refs/heads/release" \
  --output json
```

### Delete a Federated Credential

```bash
uip admin external-apps federated-credentials delete <CLIENT_ID> <CREDENTIAL_ID> --output json
```

## Using Credentials for Authentication

After creating an external app, use Client ID and Secret for non-interactive login:

```bash
uip login --client-id "<CLIENT_ID>" --client-secret "<CLIENT_SECRET>" --tenant "<TENANT_NAME>" --output json
```

Used by: CI/CD pipelines, external API integrations, service-to-service calls, automated scripts.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | App name taken | Choose a unique name |
| `No fields to update` | No update flags provided | Provide `--name`, `--app-scope`, `--user-scope`, or `--redirect-uri` |
| `not found` | Invalid client ID | Run `external-apps list` to find correct ID |
| `scope not found` | Invalid scope name | Run `uip admin scopes list` to find valid scopes |
| Non-confidential + `--app-scope` | Public apps can't use app scopes | Use `--user-scope` only |
| User scopes without redirect URI | OAuth2 auth code flow needs redirect | Add `--redirect-uri` |

# External App Management

Workflows for managing OAuth2 external clients and their secrets via `uip admin identity external-apps`.

External apps provide Client ID + Secret credentials used by robot accounts, API integrations, and external systems to authenticate with the UiPath platform.

## Key Concepts

- **External app** = an OAuth2 confidential client registered in Identity Server
- **Scopes** = permissions granted to the app (e.g., `OR.Folders`, `OR.Jobs`)
- **Secret** = a credential value paired with the Client ID for authentication
- **Secrets are shown only once** — the secret value appears only in the creation/generation response

## Common Scopes

| Scope | Description |
|-------|-------------|
| `OR.Folders` | Access to Orchestrator folders |
| `OR.Assets` | Access to Orchestrator assets |
| `OR.Queues` | Access to queues and queue items |
| `OR.Jobs` | Access to start and monitor jobs |
| `OR.Machines` | Access to machine management |
| `OR.Robots` | Access to robot management |
| `OR.Execution` | Access to execution resources |
| `OR.Monitoring` | Access to monitoring data |

## Workflow: List and Inspect External Apps

```bash
# List all external apps
uip admin identity external-apps list --organization <ORG_ID> --output json

# Get details including scopes and resources
uip admin identity external-apps get <CLIENT_ID> \
  --organization <ORG_ID> --output json
```

## Workflow: Create an External App

1. Check for existing apps:
   ```bash
   uip admin identity external-apps list --organization <ORG_ID> --output json
   ```

2. Create with required scopes:
   ```bash
   uip admin identity external-apps create "<APP_NAME>" \
     --organization <ORG_ID> \
     --scope "OR.Folders,OR.Assets,OR.Jobs" \
     --output json
   ```

3. **Save the response immediately.** The response contains:
   - `id` — the Client ID (persistent, used for authentication)
   - `secret` — the Client Secret (shown only once)

4. Warn the user: *"Save the Client ID and Secret now. The secret cannot be retrieved again."*

## Workflow: Generate a New Secret

Use this when the original secret is lost or needs rotation.

```bash
uip admin identity external-apps generate-secret <CLIENT_ID> \
  --organization <ORG_ID> \
  --description "Rotated secret for production" \
  --expiration "2027-06-01" \
  --output json
```

- A new secret is generated without invalidating existing secrets
- The new secret value is shown only once in the response
- Use `--expiration` to set an expiry date (ISO 8601 format)

## Workflow: Delete a Secret

1. Get the app details to find secret IDs:
   ```bash
   uip admin identity external-apps get <CLIENT_ID> \
     --organization <ORG_ID> --output json
   ```

2. Delete the specific secret:
   ```bash
   uip admin identity external-apps delete-secret <SECRET_ID> \
     --organization <ORG_ID> --output json
   ```

## Workflow: Update an External App

Update name, scopes, or redirect URI. At least one field is required.

```bash
uip admin identity external-apps update <CLIENT_ID> \
  --organization <ORG_ID> \
  --name "<NEW_NAME>" \
  --scope "OR.Folders,OR.Jobs,OR.Queues" \
  --output json
```

> **Scopes are replaced, not merged.** When updating `--scope`, provide the complete list of desired scopes. Omitting `--scope` preserves existing scopes.

## Workflow: Delete an External App

1. Confirm with the user — this revokes all secrets and access.

2. Delete:
   ```bash
   uip admin identity external-apps delete <CLIENT_ID> \
     --organization <ORG_ID> --output json
   ```

## Using Credentials for Authentication

After creating an external app, use the Client ID and Secret for non-interactive login:

```bash
uip login \
  --client-id "<CLIENT_ID>" \
  --client-secret "<CLIENT_SECRET>" \
  --tenant "<TENANT_NAME>" \
  --output json
```

This is the authentication method used by:
- Unattended robots running on machines
- CI/CD pipelines
- External API integrations
- Service-to-service calls

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | App name taken | Choose a unique name |
| `No fields to update` | No update flags provided | Provide `--name`, `--scope`, or `--redirect-uri` |
| `not found` | Invalid client ID | Run `external-apps list` to find correct ID |
| `scope not found` | Invalid scope name | Use exact scope names (e.g., `OR.Folders`, not `Folders`) |

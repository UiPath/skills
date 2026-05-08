# External App Management

Workflows for managing OAuth2 external clients and their secrets via `uip admin external-apps`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#external-apps--uip-admin-external-apps).

External apps provide Client ID + Secret credentials for API integrations, CI/CD pipelines, and external systems to authenticate with the UiPath platform.

> **External apps are NOT robot credentials.** Robot accounts use a separate, dedicated credential mechanism provisioned by Orchestrator during machine connection. Use external apps for third-party integrations and service-to-service authentication only.

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

## Workflow: Create an External App

1. Check for duplicates: `uip admin external-apps list --output json`
2. Create with scopes: `uip admin external-apps create "<APP_NAME>" --scope "OR.Folders,OR.Assets,OR.Jobs" --output json`
3. **Save the response immediately.** It contains `id` (Client ID) and `secret` (Client Secret — shown only once).
4. Warn user: *"Save the Client ID and Secret now. The secret cannot be retrieved again."*

## Workflow: Generate a New Secret

Use when original secret is lost or needs rotation:

```bash
uip admin external-apps generate-secret <CLIENT_ID> --description "Rotated secret" --expiration "2027-06-01" --output json
```

New secret is generated without invalidating existing secrets. Value shown only once.

## Workflow: Delete a Secret

1. Find secret IDs: `uip admin external-apps get <CLIENT_ID> --output json`
2. Delete (only secret ID needed — no client ID): `uip admin external-apps delete-secret <SECRET_ID> --output json`

## Workflow: Update an External App

At least one field required. Scopes are **replaced, not merged** — provide complete list.

```bash
uip admin external-apps update <CLIENT_ID> --name "<NEW_NAME>" --scope "OR.Folders,OR.Jobs" --output json
```

## Workflow: Delete an External App

1. Confirm with user — this revokes all secrets and access.
2. Delete: `uip admin external-apps delete <CLIENT_ID> --output json`

## Using Credentials for Authentication

After creating an external app, use Client ID and Secret for non-interactive login:

```bash
uip login --client-id "<CLIENT_ID>" --client-secret "<CLIENT_SECRET>" --tenant "<TENANT_NAME>" --output json
```

Used by:
- CI/CD pipelines
- External API integrations
- Service-to-service calls
- Automated scripts on headless machines

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `already exists` | App name taken | Choose a unique name |
| `No fields to update` | No update flags provided | Provide `--name`, `--scope`, or `--redirect-uri` |
| `not found` | Invalid client ID | Run `external-apps list` to find correct ID |
| `scope not found` | Invalid scope name | Use exact scope names (e.g., `OR.Folders`, not `Folders`) |

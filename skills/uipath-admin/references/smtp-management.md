# SMTP Management

Workflows for managing SMTP email settings via `uip admin smtp`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#smtp--uip-admin-smtp).

SMTP settings control how the platform sends emails (invitations, notifications, password resets).

## Workflow: View Current Settings

```bash
uip admin smtp get --output json
```

Returns host, port, SSL config, sender address, and display name. Password is never returned.

## Workflow: Configure SMTP

1. Get current settings: `uip admin smtp get --output json`
2. Update desired fields (only provided fields change):
   ```bash
   uip admin smtp update \
     --host "smtp.example.com" \
     --port 587 \
     --enable-ssl "true" \
     --username "smtp-user" \
     --password "smtp-pass" \
     --from-address "noreply@example.com" \
     --from-display-name "UiPath Platform" \
     --output json
   ```
3. Test the configuration: `uip admin smtp test --recipient "admin@example.com" --output json`
4. Verify by sending a user invite or password reset

## Workflow: Test SMTP (Without Saving)

Test custom settings before committing them — pass SMTP options directly to `test`:

```bash
uip admin smtp test \
  --recipient "admin@example.com" \
  --host "smtp.newprovider.com" \
  --port 465 \
  --enable-ssl "true" \
  --username "new-user" \
  --password "new-pass" \
  --from-address "test@example.com" \
  --output json
```

When custom options are provided, `--password` is required.

## Workflow: Delete SMTP Settings

Removes all SMTP configuration. Confirm with user first — platform emails will stop working.

```bash
uip admin smtp delete --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `No fields to update` | No SMTP flags provided | Provide at least one flag (e.g., `--host`, `--port`) |
| SMTP test fails | Incorrect settings | Verify host, port, credentials, and SSL settings |
| `HTTP 403` | Insufficient permissions | Needs admin role |

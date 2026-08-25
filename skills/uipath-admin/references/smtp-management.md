# SMTP Management

Workflows for managing SMTP email settings via `uip admin smtp`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#smtp--uip-admin-smtp).

SMTP settings control how the platform sends emails (invitations, notifications, password resets).

## Workflow: View Current Settings

```bash
uip admin smtp get --output json
```

Returns host, port, SSL config, sender address, and display name. Password is never returned.

## Workflow: Configure SMTP (Recommended)

**Test first, then save.** This prevents saving broken settings that would disrupt platform emails.

1. Get current settings: `uip admin smtp get --output json`
2. Test the new settings without saving — pass all SMTP options to `test`:
   ```bash
   uip admin smtp test \
     --recipient "admin@example.com" \
     --host "smtp.example.com" \
     --port 587 \
     --enable-ssl "true" \
     --username "smtp-user" \
     --password "smtp-pass" \
     --from-address "noreply@example.com" \
     --from-display-name "UiPath Platform" \
     --output json
   ```
3. If test succeeds, save the settings:
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
4. If test fails, fix the settings and re-test before saving.

When custom options are provided to `test`, `--password` is required.

> If user explicitly asks to update without testing first, proceed — but note this is not recommended as broken settings will disrupt platform emails until corrected.

## Workflow: Test Saved Settings

Test the currently saved SMTP configuration:

```bash
uip admin smtp test --recipient "admin@example.com" --output json
```

## Workflow: Delete SMTP Settings

Removes custom SMTP configuration, reverting to platform defaults. Confirm with user first.

```bash
uip admin smtp delete --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `No fields to update` | No SMTP flags provided | Provide at least one flag (e.g., `--host`, `--port`) |
| SMTP test fails | Incorrect settings | Verify host, port, credentials, and SSL settings |
| `HTTP 403` | Insufficient permissions | Needs admin role |

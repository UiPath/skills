# SMTP Management

Workflows for managing SMTP email settings via `uip admin smtp`. For full command syntax and flags, see [identity-commands.md](identity-commands.md#smtp--uip-admin-smtp).

SMTP settings control platform emails, including invitations, notifications, and password resets.

## View Current Settings

Run:

```bash
uip admin smtp get --output json
```

The response includes host, port, SSL configuration, sender address, and display name. Password is never returned.

## Configure SMTP (Recommended)

Test first, then save to avoid disrupting platform emails.

1. Get current settings:
   ```bash
   uip admin smtp get --output json
   ```
2. Test the new settings without saving. Pass all SMTP options to `test`:
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
3. If the test succeeds, save the settings:
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
4. If the test fails, fix the settings and re-test before saving.

When custom options are provided to `test`, `--password` is required.

If the user explicitly asks to update without testing first, proceed, but note that broken settings will disrupt platform emails until corrected.

## Test Saved Settings

Run:

```bash
uip admin smtp test --recipient "admin@example.com" --output json
```

## Delete SMTP Settings

Confirm with the user first. Deletion removes custom SMTP configuration and reverts to platform defaults.

```bash
uip admin smtp delete --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `No fields to update` | No SMTP flags provided | Provide at least one flag (e.g., `--host`, `--port`) |
| SMTP test fails | Incorrect settings | Verify host, port, credentials, and SSL settings |
| `HTTP 403` | Insufficient permissions | Needs admin role |

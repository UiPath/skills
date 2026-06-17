# Identity & Authentication Failure Playbooks

Prescriptive diagnostic workflows for common identity/auth failures. Each playbook: symptom → investigation steps → resolution.

## Playbook 1: User Cannot Log In

**Symptom:** User reports login failure — `uip login` returns error, or Portal/UI login redirects or rejects.

1. Verify CLI session: `uip login status --output json`
2. Check user exists:
   ```bash
   uip admin users list --search "<USER_EMAIL>" --output json
   ```
3. If user not found → they were never invited or were deleted. Invite: `uip admin users invite --email "<EMAIL>" --name "<FIRST>" --surname "<LAST>" --output json`
4. If user found → check login history at **org** scope (logins are org-scoped, not tenant):
   ```bash
   uip admin audit org sources --output json
   ```
   Discover the login source/type GUIDs, then:
   ```bash
   uip admin audit org events \
     --user-id "<USER_ID>" --status "Failure" \
     --from-date "<7_DAYS_AGO>" --to-date "<TODAY>" \
     --output json
   ```
5. Inspect failure events for root cause:
   - **Bad credentials** → user must reset password via Portal
   - **IP blocked** → check `uip admin ip-restriction enforcement get --output json`; if enabled, verify user's IP is in allowlist
   - **Account locked** → too many failed attempts; wait or admin unlock via Portal
   - **No org access** → user exists in identity but not assigned to org; re-invite

## Playbook 2: External App OAuth2 Flow Failing

**Symptom:** CI/CD pipeline or integration using an external app's Client ID returns auth errors.

1. Verify app exists and inspect configuration:
   ```bash
   uip admin external-apps get "<CLIENT_ID>" --output json
   ```
2. Check grant type vs scope alignment:
   - `client_credentials` flow → app MUST use `--app-scope` (not `--user-scope`)
   - `authorization_code` flow → app MUST use `--user-scope` + valid `--redirect-uri`
   - Error `"not allowed to access User scopes"` → app was created with `--app-scope` but caller is requesting user-scoped tokens. Recreate with `--user-scope` or switch grant type.
3. Check secret validity:
   - Secrets have optional expiration. If expired, generate a new one:
     ```bash
     uip admin external-apps generate-secret "<CLIENT_ID>" --output json
     ```
   - **Secret shown only once** — warn user to save immediately.
4. For `authorization_code` flow, verify redirect URI matches exactly (scheme, host, port, path). Update if wrong:
   ```bash
   uip admin external-apps update "<CLIENT_ID>" \
     --redirect-uri "https://correct-url/callback" --output json
   ```
5. For `--non-confidential` apps: these have NO client secret. If caller is sending a secret, they need a confidential app instead.
6. Check scopes cover the required API — compare app's `resources` list against the API being called. Update scopes if needed (note: `update --app-scope` **replaces** all scopes, not merges — re-fetch first).

## Playbook 3: Robot Account Not Authenticating

**Symptom:** Automation fails with "robot not authenticated" or similar credential errors.

1. Verify robot account exists:
   ```bash
   uip admin robot-accounts list --search "<ROBOT_NAME>" --output json
   ```
2. If not found → create: `uip admin robot-accounts create "<NAME>" --display-name "<DISPLAY>" --output json`
3. **Critical distinction:** Robot accounts (Identity Server) are **identities** — they do NOT carry API credentials (Client ID + Secret). Robot **credentials** are provisioned by Orchestrator during machine connection setup.
   - For API access from external systems → use an **external app** (`uip admin external-apps create`), not a robot account
   - For unattended robot execution → the robot's machine connection in Orchestrator provisions credentials automatically
4. Check robot account's group membership (determines role inheritance):
   ```bash
   uip admin groups list --output json
   ```
   Then for each relevant group:
   ```bash
   uip admin groups members list "<GROUP_ID>" --output json
   ```
5. Check audit for recent robot login events:
   ```bash
   uip admin audit org events \
     --user-id "<ROBOT_ACCOUNT_ID>" \
     --from-date "<7_DAYS_AGO>" --to-date "<TODAY>" \
     --output json
   ```

## Playbook 4: PAT Rejected / Not Working

**Symptom:** API call with a personal access token returns 401 or 403.

1. List tokens and check status:
   ```bash
   uip admin pat list --output json
   ```
2. For each token, inspect:
   - **`expirationDate`** — if past today, token is expired. Create a new one or regenerate: `uip admin pat regenerate "<PAT_ID>" --output json`
   - **`isRevoked`** — if true, token was explicitly revoked. Create a new one.
   - **`scopes`** — compare against the API being called. A 403 with a valid token means scope mismatch (e.g., token has `OR.Folders.Read` but API requires `OR.Folders.Write`).
3. Check per-user token limit (default 5, max 50). If limit reached, revoke unused tokens first:
   ```bash
   uip admin pat revoke "<PAT_ID>" --output json
   ```
4. If token was working before and suddenly stopped → check audit for revocation events:
   ```bash
   uip admin audit org events \
     --from-date "<7_DAYS_AGO>" --to-date "<TODAY>" \
     --output json
   ```
   Filter for PAT-related events in the response.

## Playbook 5: SMTP Emails Not Delivering

**Symptom:** Platform invitation emails, password resets, or notifications are not being received.

1. Check current SMTP configuration:
   ```bash
   uip admin smtp get --output json
   ```
   If no configuration exists (empty/error response) → SMTP was never configured or was deleted. Set up with `uip admin smtp update`.
2. Test the current configuration:
   ```bash
   uip admin smtp test \
     --recipient "<TEST_EMAIL>" \
     --output json
   ```
3. Branch on test result:
   - **Connection refused** → wrong `--host` or `--port`, or firewall blocking outbound SMTP
   - **Authentication failure** → wrong `--user` or `--password` credentials
   - **SSL/TLS mismatch** → toggle `--secure` (true/false) to match server's TLS config
   - **DNS resolution failure** → verify hostname resolves; check for typos
   - **Timeout** → network connectivity issue; verify egress rules allow SMTP traffic
4. Fix and re-test:
   ```bash
   uip admin smtp update \
     --host "<CORRECT_HOST>" --port <PORT> \
     --secure <true|false> \
     --user "<SMTP_USER>" --password "<SMTP_PASS>" \
     --from-email "<FROM_ADDR>" \
     --output json
   ```
   Then re-run `smtp test` to verify.

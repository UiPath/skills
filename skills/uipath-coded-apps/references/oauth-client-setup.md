# OAuth Client (External Application) Setup via `uip admin`

Create and update UiPath External Applications (OAuth clients) with the **`uip admin external-apps` CLI** — the primary, supported path. Used by `create-web-app.md` / `create-action-app.md` to create the app, and by `debug.md` to autonomously fix a misconfigured app (add redirect URIs / scopes) without a browser.

> **CLI-first.** Do NOT drive the admin portal with browser automation. Every create/update below is one CLI call. Fall back to the [Manual portal steps](#manual-portal-fallback) ONLY when the CLI can't run (see [When the CLI can't be used](#when-the-cli-cant-be-used)).

## Prerequisites

1. Install the admin tool (provides the `uip admin external-apps` commands): `uip tools install admin-tool`
2. `uip` authenticated against the target org/tenant: `uip login status --output json`. If not logged in: `uip login` (or the org's SSO flow).
3. The signed-in identity has permission to manage external applications (identity admin). Without it, create/update return `403` — see [When the CLI can't be used](#when-the-cli-cant-be-used).

Needed inputs: app name, redirect URI(s), required OAuth scopes (from [oauth-scopes.md](oauth-scopes.md)).

## Cloud Host URLs

| Environment | Cloud Host |
|---|---|
| cloud | `https://cloud.uipath.com` |
| staging | `https://staging.uipath.com` |
| alpha | `https://alpha.uipath.com` |

## Scope model — CLI vs portal

The CLI takes **flat, comma-separated scope names** (e.g. `OR.Assets,OR.Tasks.Read`) — no portal resource-label grouping. Identity resolves each scope to its resource. Coded web apps use the browser PKCE (authorization_code) flow, so they need **`--user-scope`** (delegated), and a non-confidential client:

- `--non-confidential` — public client, no secret (required for browser PKCE).
- Non-confidential apps support `--user-scope` only. Do NOT pass `--app-scope` with `--non-confidential` — the CLI rejects it.
- `--redirect-uri` is required for non-confidential / `--user-scope` apps.

Pick scope names from [oauth-scopes.md](oauth-scopes.md). Discover valid names: `uip admin scopes list --output json`.

## Create an External Application

For a coded **web** app (dev on `http://localhost:5173`):

```bash
uip admin external-apps create "<APP_NAME>" \
  --non-confidential \
  --user-scope "OR.Assets,OR.Execution,OR.Tasks.Read" \
  --redirect-uri "http://localhost:5173,http://localhost:5173/" \
  --output json
```

- Register the redirect **with and without** the trailing slash — the SDK may send either.
- Production redirect URIs are registered automatically by `uip codedapp deploy` — do not add them here.
- Parse `id` from the JSON response — that is the **Client ID**. Write it to `uipath.json` as `clientId`.

## Add redirect URIs to an existing app

`update` **replaces** the redirect list — it does not merge. Read the current URIs first, then pass existing **+** new together.

```bash
uip admin external-apps get <CLIENT_ID> --output json     # read current redirect URIs
uip admin external-apps update <CLIENT_ID> \
  --redirect-uri "<existing_uris>,http://localhost:5173,http://localhost:5173/" \
  --output json
```

Use this for `redirect_uri_mismatch`, or when a new dev port/host needs registering. Include both the failing URL and its trailing-slash variant.

## Add scopes to an existing app

Same replace semantics — `--user-scope` **replaces** all user scopes. Read current scopes, pass the full union.

```bash
uip admin external-apps get <CLIENT_ID> --output json     # read current scopes
uip admin external-apps update <CLIENT_ID> \
  --user-scope "<existing_scopes>,OR.Tasks.Read" \
  --output json
```

After adding a scope: also update the `scope` field in `uipath.json` to include it (both the app and `uipath.json` must list it), then clear browser state and re-authenticate so the new token carries the scope (see `debug.md` Step 3).

## Verify

```bash
uip admin external-apps get <CLIENT_ID> --output json
```

Confirm the redirect URIs and scopes match what you set.

---

## When the CLI can't be used

Fall back to the [Manual portal steps](#manual-portal-fallback) only when:

- `uip` is not authenticated and cannot be (no interactive login available), OR
- the signed-in identity lacks external-app admin permission (`403`) — hand the manual steps to an org admin, OR
- the CLI genuinely lacks the verb (`uip admin external-apps --help` shows nothing — very old CLI; prefer upgrading).

A missing scope name (`scope not found`) is NOT a fallback trigger — fix the name via `uip admin scopes list` and retry.

## Manual portal fallback

### Create a new External Application

1. Go to `https://{cloudHost}/{orgName}/portal_/admin/external-apps/oauth`
2. Click **"Add application"**
3. Set **Application name** to `<app name>`
4. Select **"Non-Confidential application"** (required for browser/PKCE flow)
5. For each resource, click **"Add scopes"**, pick the resource, check the required scopes, confirm
6. Add the localhost redirect URIs (with and without trailing slash) in **Redirect URL**, pressing Enter after each. Production URIs are registered by `uip codedapp deploy`.
7. Click **"Add"** and copy the generated **Application ID** (a UUID) — this is the Client ID
8. Write the Client ID into `uipath.json` → `clientId`

### Add redirect URIs to an existing app

1. Portal → external-apps as above
2. Paste the first 8 chars of the Client ID into search to filter (the Application ID column is truncated, so a **prefix** matches where the full UUID won't; it's also the only reliable disambiguator when apps share a display name)
3. Click the **pencil Edit icon** on the row (clicking the row text does not open the edit form)
4. In **Redirect URL**, enter each new URI (with and without trailing slash), Enter after each
5. Click **"Save"**

### Add scopes to an existing app

1. Portal → external-apps, filter by Client-ID prefix, click the **pencil Edit icon**
2. For each resource:
   - **Already listed** (e.g. `UiPath.Orchestrator` is attached and you're adding another `OR.*` scope): click the **pencil Edit icon next to that resource's row**, check the additional scopes, confirm. Do NOT click "Add scopes" for an attached resource — it won't appear in that dropdown.
   - **Not yet listed**: click **"Add scopes"**, pick the resource, check the scopes, confirm.
3. Click **"Save"**
4. Update the `scope` field in `uipath.json` to include the new scopes
5. Clear browser storage and re-test

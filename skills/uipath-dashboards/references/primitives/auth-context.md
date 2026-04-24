# auth-context

## Purpose
Resolve `env`, `orgName`, `tenantName`, `userId` from the `uip` CLI session. Never ask the user for values we can infer.

## Inputs
None. Reads from filesystem (`~/.uipath/.auth`) and CLI (`uip login status --output json`).

## Outputs
```ts
{
  env: 'cloud' | 'staging' | 'alpha',
  orgName: string,
  tenantName: string,
  userId: string,
  loggedIn: boolean
}
```

## Rules
1. Run `uip login status --output json` on every mode dispatch — NEVER cache across runs. Token state changes (logout, tenant switch) must be detected.
2. Parse `Data.Status === "Logged in"` to determine `loggedIn`. If false, return `{loggedIn: false, ...}` with other fields undefined.
3. If logged in, read `~/.uipath/.auth` for `orgName` / `tenantName` / `userId` — the CLI keeps these in a JSON file per https://docs.uipath.com/automation-cloud/docs/uipath-cli.
4. Derive `env` from the authority URL stored alongside (`https://alpha.uipath.com` → `alpha`, `https://staging.uipath.com` → `staging`, `https://cloud.uipath.com` → `cloud`).
5. **Never decode JWTs.** The access token is in `.auth` but we don't parse it — the `uip` CLI handles token validation.

## Details

### Reading `~/.uipath/.auth`
Format (subject to change across `uip` versions; verify by inspection):
```json
{
  "orgName": "acme",
  "tenantName": "default",
  "userId": "abc-...",
  "authority": "https://alpha.uipath.com",
  "accessToken": "...",
  "expiresAt": "..."
}
```
Use `jq` or a minimal Node script to parse — do NOT `source` the file (it's JSON, not shell).

### When not logged in
Return early with actionable message:
```
You're not logged into the uip CLI.

  uip login --authority https://alpha.uipath.com   # or staging / cloud
```

Halt the caller. Never proceed to folder-list fetches or deploys without a session.

### Error paths
| Condition | Action |
|---|---|
| `uip` not on PATH | Instruct `npm install -g @uipath/cli` or resolve via `$(npm root -g)/@uipath/cli/bin/uip`. |
| `~/.uipath/.auth` missing despite `Status: Logged in` | Re-run `uip login`; the file is created on login. |
| Authority URL is not an allow-listed UiPath cloud domain | Warn that the skill only supports UiPath Cloud hosts in v1. |

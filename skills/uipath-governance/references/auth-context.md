# Auth Context — `~/.uipath/.auth`

Every capability in this skill reads tenant, org, and token identifiers from the `uip` CLI auth file. This is the canonical source — never decode JWTs or ask the user when the file is available.

## File location

- Linux / macOS: `~/.uipath/.auth`
- Windows: `C:\Users\<user>\.uipath\.auth`

## Format

`KEY=VALUE` per line (env-style, **NOT** JSON). Written by `uip login`, kept current by the CLI.

## Read recipe

```bash
AUTH_FILE="$HOME/.uipath/.auth"
UIPATH_URL=$(grep               '^UIPATH_URL='                "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ORGANIZATION_NAME=$(grep '^UIPATH_ORGANIZATION_NAME='  "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ORGANIZATION_ID=$(grep   '^UIPATH_ORGANIZATION_ID='    "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_TENANT_NAME=$(grep       '^UIPATH_TENANT_NAME='        "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_TENANT_ID=$(grep         '^UIPATH_TENANT_ID='          "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ACCESS_TOKEN=$(grep      '^UIPATH_ACCESS_TOKEN='       "$AUTH_FILE" | cut -d'=' -f2-)
```

## Available fields

| Key | Example | Used by |
|---|---|---|
| `UIPATH_URL` | `https://alpha.uipath.com` | principals-lookup (URL construction) |
| `UIPATH_ORGANIZATION_NAME` | `procodeapps` | principals-lookup (URL path segment) |
| `UIPATH_ORGANIZATION_ID` | `3aa10965-a82d-4d9e-8366-0eff8e87bf7a` | principals-lookup (Directory Search GUID) |
| `UIPATH_TENANT_NAME` | `DefaultTenant` | display / audit records |
| `UIPATH_TENANT_ID` | `edb2c1a2-246e-4cd3-a5f1-08aea1cbecec` | `deployment tenant configure/get` target, diagnosis tenant fetch |
| `UIPATH_ACCESS_TOKEN` | `eyJ...` (JWT) | Raw API calls (principals lookup, until CLI wraps it) |
| `UIPATH_REFRESH_TOKEN` | `...` | Do not use — CLI manages refresh |

## Preflight check

Before any capability runs, verify:

1. `uip login status --output json` returns `Data.Status == "Logged in"`.
2. `~/.uipath/.auth` exists and `UIPATH_TENANT_ID` is non-empty.

If either fails, halt and ask the user to run `uip login` (or `uip login --authority https://alpha.uipath.com` for non-prod).

## Tenant-intent validation (Apply / Advise / Diagnose)

When the user's prompt names a specific tenant (e.g., *"on staging tenant"*, *"in production"*, *"apply to the prod tenant"*), compare their named tenant against `UIPATH_TENANT_NAME` and `UIPATH_URL` **before** taking any mutation action.

Detection: match the named tenant against these substrings — `staging`, `prod`, `production`, `alpha`, `dev`, `development`, `sandbox`, `qa`, `test`, or any explicit tenant display name the user gives (e.g., *"MedCore-Prod"*).

On mismatch, halt with:

```
⚠ Your prompt says 'staging tenant' but you are logged into 'DefaultTenant' on
  https://cloud.uipath.com (organization: procodeapps).

  To apply on the tenant you named, run one of:
    uip login                                      # interactive pick
    uip login --authority https://alpha.uipath.com # non-prod authority

  Or, if this IS the tenant you meant, reply 'yes, continue on <currentTenantName>'.
```

Accept a literal yes-with-tenant-name to proceed; anything else halts with no side effects. This prevents the most expensive category of mistakes — applying a pack or a policy update to the wrong tenant.

**Diagnose and Check are read-only** and still perform this validation. Read-only operations against the wrong tenant waste time and pollute caches with mismatched state; better to catch it upfront.

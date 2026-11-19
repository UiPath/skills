# Auth Context — `uip login status`

Every capability in this skill reads tenant and organization identifiers from `uip login status --output json`. This is the canonical source — never decode JWTs, never read the CLI's credentials file (it holds the access and refresh tokens), and never ask the user for values the command returns.

## Read recipe

```bash
uip login status --output json
```

Read the values from the JSON output; none of them is a secret.

## Available fields

| Field | Example | Used by |
|---|---|---|
| `Data.Status` | `Logged in` | Preflight check |
| `Data.BaseUrl` | `https://cloud.uipath.com` | Tenant-intent validation, display |
| `Data.Organization` | `procodeapps` | Organization name — display, confirmation gates |
| `Data.OrganizationId` | `3aa10965-a82d-4d9e-8366-0eff8e87bf7a` | `organizationId` in a `PolicyDefinition` |
| `Data.Tenant` | `DefaultTenant` | Tenant name — display, audit records |
| `Data.TenantId` | `edb2c1a2-246e-4cd3-a5f1-08aea1cbecec` | `tenantId` in a `PolicyDefinition`, `deployment tenant configure/get` target, diagnosis tenant fetch |
| `Data.Identity` | `admin@example.com` | "Applied by" line in audit records |

When a profile is active (`--profile <name>`), pass the same flag to `uip login status` so the values match the login the other commands use.

## Preflight check

Before any capability runs, verify that `uip login status --output json` returns `Data.Status == "Logged in"` and a non-empty `Data.TenantId`.

If either fails, halt and ask the user to run `uip login` (or `uip login --authority "<AUTHORITY_URL>"` for a non-default host).

## Tenant-intent validation (Apply / Advise / Diagnose)

When the user's prompt names a specific tenant (e.g., *"on staging tenant"*, *"in production"*, *"apply to the prod tenant"*), compare their named tenant against `Data.Tenant` and `Data.BaseUrl` **before** taking any mutation action.

Detection: match the named tenant against these substrings — `staging`, `prod`, `production`, `alpha`, `dev`, `development`, `sandbox`, `qa`, `test`, or any explicit tenant display name the user gives (e.g., *"MedCore-Prod"*).

On mismatch, halt with:

```
⚠ Your prompt says 'staging tenant' but you are logged into 'DefaultTenant' on
  https://cloud.uipath.com (organization: procodeapps).

  To switch to the tenant you named:

  If the tenant is in the same org — faster, no browser needed:
    uip login tenant list --output json         # see available tenants
    uip login tenant set <TENANT_NAME>          # switch to the right one

  If you need a different org or authority:
    uip login                                   # interactive (cloud.uipath.com)
    uip login --authority "<AUTHORITY_URL>"     # non-default host

  Or, if this IS the tenant you meant, reply 'yes, continue on <currentTenantName>'.
```

Accept a literal yes-with-tenant-name to proceed; anything else halts with no side effects. This prevents the most expensive category of mistakes — applying a pack or a policy update to the wrong tenant.

**Diagnose and Check are read-only** and still perform this validation. Read-only operations against the wrong tenant waste time and pollute caches with mismatched state; better to catch it upfront.

## Switching tenants

When the user is logged in to the right **org** but needs a different **tenant** within that org:

```bash
# 1. List available tenants in the current org
uip login tenant list --output json
# → returns Data[].TenantName

# 2. Switch to the target tenant (no browser auth needed)
uip login tenant set <TENANT_NAME> --output json

# 3. Verify
uip login status --output json
# → Data.Tenant should now show the new tenant
```

When the user needs a different **org** or **authority** (e.g. an Automation Suite host vs cloud.uipath.com):

```bash
# Full re-login — browser OAuth flow
uip login                                       # cloud.uipath.com (default)
uip login --authority "<AUTHORITY_URL>"         # non-default host (Automation Suite, dedicated)
```

**Show this to the user** when the mismatch block fires — the tenant set path is much faster than a full re-login when they're already in the right org.

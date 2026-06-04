# Auth Context Resolution

Read BEFORE any dashboard build. Extracts the four values needed for `intent.json`.

## Values you need

| Variable | What it is | Where it comes from |
|----------|-----------|---------------------|
| `orgName` | Organisation name | `uip login status` output |
| `tenantName` | Tenant name | `uip login status` output |
| `cloudUrl` | Cloud base URL | `uip login status` output |
| `apiUrl` | API base URL | Derived from `cloudUrl` |
| `tenantId` | Tenant UUID | `~/.uipath/.auth` file |

---

## Step 1 — Verify login and extract org/tenant/cloudUrl

```bash
uip login status --output json
```

Expected output:
```json
{
  "Result": "Success",
  "Data": {
    "Status": "Logged in",
    "BaseUrl": "https://alpha.uipath.com",
    "Organization": "myorg",
    "Tenant": "myorgDefault"
  }
}
```

Read these fields from the JSON response:
- `orgName` ← `Data.Organization`
- `tenantName` ← `Data.Tenant`
- `cloudUrl` ← `Data.BaseUrl`

**If `Data.Status` is not `"Logged in"`:** stop and tell the user to run `uip login`.

---

## Step 2 — Derive apiUrl from cloudUrl

The SDK API uses a different subdomain than the cloud portal:

| cloudUrl | apiUrl |
|----------|--------|
| `https://alpha.uipath.com` | `https://alpha.api.uipath.com` |
| `https://staging.uipath.com` | `https://staging.api.uipath.com` |
| `https://cloud.uipath.com` | `https://api.uipath.com` |

Rule: insert `api.` before `uipath.com`. Exception: `cloud.uipath.com` → `api.uipath.com` (drop the `cloud.` prefix).

---

## Step 3 — Read tenantId from the auth file

The tenant UUID is not in `uip login status` output — it lives in `~/.uipath/.auth`.

Run this script (works on Windows and Unix):

```bash
node -e "
const fs   = require('fs')
const path = require('path')

// Locate the auth file on any OS
const home     = process.env.HOME || process.env.USERPROFILE
const authPath = path.join(home, '.uipath', '.auth')
const content  = fs.readFileSync(authPath, 'utf8')

// Try env-file format first (KEY=VALUE lines — most common)
const envMatch = content.match(/^UIPATH_TENANT_ID=(.+)$/m)
if (envMatch) {
  console.log(envMatch[1].trim())
  process.exit(0)
}

// Fall back to JSON format (older CLI versions)
const parsed = JSON.parse(content)
console.log(parsed.UIPATH_TENANT_ID || parsed.tenantId || '')
"
```

The printed value is `tenantId`. It is a UUID like `a1b2c3d4-e5f6-7890-abcd-ef1234567890`.

**If empty:** Insights RTM calls will return 400 but SDK calls still work. Warn the user.

---

## Summary

After these three steps you have everything needed to write `intent.json`:

```
orgName    = Data.Organization   (from uip login status)
tenantName = Data.Tenant         (from uip login status)
cloudUrl   = Data.BaseUrl        (from uip login status)
apiUrl     = derived             (insert "api." subdomain)
tenantId   = UIPATH_TENANT_ID    (from ~/.uipath/.auth)
```

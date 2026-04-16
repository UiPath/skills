# Deployment · Principals (group & user lookup)

Resolve a human-friendly group or user name → identity GUID so [../aops/impl.md](../aops/impl.md) can call `assign-group` / `assign-user`.

Used only when `scope.level ∈ {group, user}` and a `targetId` is not already known.

## Auth context from `~/.uipath/.auth`

All required values come from the `uip` CLI auth file. Read it first:

```bash
AUTH_FILE="$HOME/.uipath/.auth"
# File format: KEY=VALUE (one per line, env-style, NOT JSON)
UIPATH_URL=$(grep '^UIPATH_URL=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ORGANIZATION_NAME=$(grep '^UIPATH_ORGANIZATION_NAME=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ORGANIZATION_ID=$(grep '^UIPATH_ORGANIZATION_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ACCESS_TOKEN=$(grep '^UIPATH_ACCESS_TOKEN=' "$AUTH_FILE" | cut -d'=' -f2-)
```

On Windows: `C:\Users\<user>\.uipath\.auth`. Written by `uip login`, kept current by the CLI.

**If the file is missing or `UIPATH_ORGANIZATION_ID` is empty:** `uip login` has not been run. Halt and ask the user to log in.

## Identity Directory Search API

Both groups and users come from the same endpoint, distinguished by `sourceFilter`.

```
{UIPATH_URL}/{UIPATH_ORGANIZATION_NAME}/identity_/api/Directory/Search/{UIPATH_ORGANIZATION_ID}?startsWith=<prefix>&sourceFilter=<filter>[&sourceFilter=<filter>]
```

| Target | `sourceFilter` values |
|---|---|
| Groups | `localGroups`, `directoryGroups` |
| Users  | `localUsers`, `directoryUsers` |

Pass both filters simultaneously to get local (org-managed) and directory (AAD / external IdP) principals in one call.

### Inputs

| Value | Source | Example |
|---|---|---|
| Base URL | `UIPATH_URL` from auth file | `https://alpha.uipath.com` |
| Org name | `UIPATH_ORGANIZATION_NAME` from auth file | `procodeapps` |
| Org GUID | `UIPATH_ORGANIZATION_ID` from auth file | `3aa10965-a82d-4d9e-8366-0eff8e87bf7a` |
| Bearer token | `UIPATH_ACCESS_TOKEN` from auth file | `eyJ...` |
| `startsWith` prefix | First letter(s) of the user's hint (`"Finance team"` → `F`). If no hint, ask. Do not wildcard-scan. | `F` |

## Fetch recipe — groups

```bash
curl -sS -G \
  "$UIPATH_URL/$UIPATH_ORGANIZATION_NAME/identity_/api/Directory/Search/$UIPATH_ORGANIZATION_ID" \
  --data-urlencode "startsWith=<prefix>" \
  --data "sourceFilter=localGroups" \
  --data "sourceFilter=directoryGroups" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN"
```

## Fetch recipe — users

```bash
curl -sS -G \
  "$UIPATH_URL/$UIPATH_ORGANIZATION_NAME/identity_/api/Directory/Search/$UIPATH_ORGANIZATION_ID" \
  --data-urlencode "startsWith=<prefix>" \
  --data "sourceFilter=localUsers" \
  --data "sourceFilter=directoryUsers" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN"
```

## Expected response shape

Directory Search returns a list of candidates:

```jsonc
[
  {
    "key":         "<guid>",         // the identifier for assign-group / assign-user
    "displayName": "Finance Team",
    "source":      "localGroups",    // or directoryGroups / localUsers / directoryUsers
    "type":        "Group"           // or "User"
    // users may also have: email, upn — pass through to the display
  }
]
```

Field names are preliminary — confirm against the live response on first call and update this doc.

## Prompting for selection

1. Narrow to ≤10 candidates. If >10: ask user for a narrower prefix. Do NOT paginate silently.
2. Show a numbered list: `[1] Finance Team (localGroups) · [2] Finance Ops (directoryGroups) · ...`
3. Accept a number, the displayName, or `cancel` to halt deployment.
4. On selection, return `{ targetId: key, targetName: displayName }` to the orchestrator.

## Return to orchestrator

```jsonc
{
  "status":      "success",
  "targetId":    "<guid>",
  "targetName":  "<displayName>",
  "targetKind":  "group | user",
  "source":      "localGroups | directoryGroups | localUsers | directoryUsers",
  "warnings":    []
}
```

## Error map

| Situation | Action |
|---|---|
| `~/.uipath/.auth` missing or empty | Halt. Ask user to run `uip login`. |
| `UIPATH_ACCESS_TOKEN` expired (401 response) | Ask user to run `uip login` to refresh, then retry once. |
| Empty result set | Tell the user. Ask for a different prefix. Do NOT default to any principal. |
| >10 results | Ask for a narrower prefix. Do NOT paginate silently. |

## Known follow-up

Wrap this endpoint with a first-class `uip` command (e.g. `uip admin directory search-groups` / `search-users`) so the plugin does not need raw curl. Until then, `~/.uipath/.auth` is the canonical source for all auth context.

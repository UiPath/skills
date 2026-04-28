# Principals Lookup — group & user GUID resolution

Primitive: turn a human-friendly group or user name into an identity GUID so [policy-assign.md](policy-assign.md) can include the principal in a `deployment group configure` / `deployment user configure` call.

Used when `scope.level ∈ {group, user}` and a `targetId` is not already known.

## Auth context

Read tenant / org / token from `~/.uipath/.auth` — see [auth-context.md](auth-context.md). Required here: `UIPATH_URL`, `UIPATH_ORGANIZATION_NAME`, `UIPATH_ORGANIZATION_ID`, `UIPATH_ACCESS_TOKEN`.

## Identity Directory Search API

No `uip` wrapper yet — raw `curl`. Same endpoint for groups and users; filtered by `sourceFilter`.

```
{UIPATH_URL}/{UIPATH_ORGANIZATION_NAME}/identity_/api/Directory/Search/{UIPATH_ORGANIZATION_ID}?startsWith=<prefix>&sourceFilter=<filter>[&sourceFilter=<filter>]
```

| Target | `sourceFilter` values |
|---|---|
| Groups | `localGroups`, `directoryGroups` |
| Users | `localUsers`, `directoryUsers` |

Pass both filters simultaneously to get local (org-managed) and directory (AAD / external IdP) principals in one call.

## Fetch recipes

### Groups

```bash
curl -sS -G \
  "$UIPATH_URL/$UIPATH_ORGANIZATION_NAME/identity_/api/Directory/Search/$UIPATH_ORGANIZATION_ID" \
  --data-urlencode "startsWith=<prefix>" \
  --data "sourceFilter=localGroups" \
  --data "sourceFilter=directoryGroups" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN"
```

### Users

```bash
curl -sS -G \
  "$UIPATH_URL/$UIPATH_ORGANIZATION_NAME/identity_/api/Directory/Search/$UIPATH_ORGANIZATION_ID" \
  --data-urlencode "startsWith=<prefix>" \
  --data "sourceFilter=localUsers" \
  --data "sourceFilter=directoryUsers" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN"
```

### Prefix rule

`startsWith=<prefix>` is required — the API does not accept wildcard-everything scans. Use the first letter(s) of the user's hint (`"Finance team"` → `F`). If no hint, ask. Do not guess a prefix.

## Expected response shape

```jsonc
[
  {
    "key":         "<guid>",         // this is the group/user identifier used in deployment * configure payloads
    "displayName": "Finance Team",
    "source":      "localGroups",    // or directoryGroups / localUsers / directoryUsers
    "type":        "Group"           // or "User"
    // users may also have: email, upn
  }
]
```

Field names are preliminary — confirm against the live response on first call and update this doc.

## Prompting for selection

1. Narrow to ≤10 candidates. If >10: ask user for a narrower prefix. Do NOT paginate silently.
2. Show a numbered list: `[1] Finance Team (localGroups) · [2] Finance Ops (directoryGroups) · ...`
3. Accept a number, the `displayName`, or `cancel` to halt.
4. On selection, return `{ targetId: key, targetName: displayName, targetKind: "group"|"user" }` to the caller.

## Return shape

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

Wrap this endpoint with a first-class `uip` command (e.g. `uip gov directory search-groups` / `search-users`) so the plugin does not need raw curl.

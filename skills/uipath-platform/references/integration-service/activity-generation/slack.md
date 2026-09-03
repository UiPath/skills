# Worked example: Slack — add users to a user group

A complete end-to-end trace of the workflow for the Slack connector
(`uipath-salesforce-slack`). The shape transfers to any connector.

## 1. Connection
```
uip is connections list
```
Slack connections have `ConnectorKey: uipath-salesforce-slack`. Note the `Id`.
Base URL is `https://slack.com/api`, so a vendor path `/usergroups.users.list`
resolves to `https://slack.com/api/usergroups.users.list`.

## 2. The objects involved
For "add users to a group without dropping members" the relevant objects are:

| Purpose                | Object name                    | Vendor path (verbatim)      |
|------------------------|--------------------------------|-----------------------------|
| Resolve group by handle| `usergroups_list_GET`          | `/usergroups.list`          |
| Read current members   | `usergroups_users_list_GET`    | `/usergroups.users.list`    |
| Write members          | `usergroups_users_update_POST` | `/usergroups.users.update`  |

The listing shows underscored object names, but the action (and the exec
endpoint) use the **dotted `Path`** verbatim — that's the routing key. You never
need the underscored name in code.

## 3. The write object's shape
From Slack's own API docs (step 2 of activity-generation.md — the vendor is the source):
- Path param is `usergroups_users_updateId` (the group ID).
- Required request field `users` — the vendor wire format is ONE comma-separated
  string of user IDs (`"U060R4BJ4,U060RNRCZ"`), not a true array — so the
  action's input is typed `string`.
- The op is **"Add or Replace Users of User Group"** — it REPLACES the whole
  member list. So to add without dropping, you must read current members and
  write back the union.

## 4. What the reads actually return
Through `intsvc.http` you get whatever the vendor sent, verbatim, as `resp.body`
— for Slack that is its own envelope (`{ ok, usergroups: [] }` /
`{ ok, users: [] }`), so the action names the records key itself.
`usergroups.list` records have `id`, `handle`, `name`; `usergroups.users.list`
records are bare user-ID strings.

Don't confirm this through Integration Service: the CLI's list route returns a
bare array, having stripped the envelope, so you would code against the wrong
shape. Run the action (step 4 of activity-generation.md) instead.

Resolving a user email → Slack ID is a GETBYID object, `UsersByEmail_GET`
(`/users.lookupByEmail`), taking `usersByEmailId=<email>`.

## 5. The actions (no descriptor)
Two actions. The group handle is a **lookup field** (the main call needs the
group's Slack ID), so resolution goes through a normal LIST action — a
separate activity in a flat file, run first and filtered externally: the
headless design-time lookup (activity-generation.md step 3). The SR records the mapping as the
field's `design.scriptRef`:
```js
// listUserGroups.js — a normal list action script; it returns the RELEVANT
// RECORDS ARRAY (vendor envelope unwrapped), does NO matching (you filter the
// output for the handle), and returns ONE page per invocation.
async function execute(context) {
  const query = {};
  // Slack pages by cursor; the helpers do the token transport (the sandbox has
  // no base64, so a script cannot).
  Object.assign(query, intsvc.decodePageToken(context.request.headers) ?? {});

  const listed = await intsvc.http({
    method: 'GET',
    url: '/usergroups.list',
    query,
    headers: context.request.headers,
  });
  if (!listed?.body?.ok) {
    throw new Error('Failed to retrieve user groups' + JSON.stringify(listed?.body ?? listed?.raw));
  }
  return intsvc.handlePagination(
    { status: 200, headers: [], body: listed.body.usergroups ?? [] },
    'body.response_metadata.next_cursor',   // Slack's token location
    'cursor',                               // Slack's paging parameter
    listed,                                 // look for the token in the vendor response —
  );                                        // omitting this loses it SILENTLY
}
```
Slack's `next_cursor` is `""` on the last page, which `handlePagination` treats
as "no next page" — so the header is simply absent and the consumer stops.
The main action takes vendor-canonical IDs only. Its `usergroups.users.list`
read is part of the OPERATION (read-merge-write), not a lookup, so it stays
inside — and the final vendor call's response is returned verbatim:
```js
async function execute(context) {
  const { usergroup, users, include_count, team_id } = context.request.body;
  const toAdd = users ?? [];

  const listed = await intsvc.http({                   // operation read (internal)
    method: 'GET',
    url: '/usergroups.users.list',
    query: { usergroup, team_id },                     // serialized for you
    headers: context.request.headers,
  });
  if (!listed?.body?.ok) {                             // Slack fails with HTTP 200
    throw new Error('Failed to retrieve users list' + JSON.stringify(listed?.body ?? listed?.raw));
  }

  const current = listed.body.users ?? [];
  const merged = Array.from(new Set([...current, ...toAdd]));

  return await intsvc.http({                           // UNTOUCHED ⇒ relayed verbatim
    method: 'POST',
    url: '/usergroups.users.update',
    body: { usergroup, users: merged, include_count, team_id },
    headers: context.request.headers,
  });
}
```
The full action scripts are `example-list-action.js.txt` and
`example-action.js.txt`.

## 6. Run
Lookup first (a read — safe to run automatically): run the list action, filter
its output for the handle, then run the main action with the resolved ID:
```bash
# activity-generation.md step 4 has the full recipe
export CONN=<connectionId>

run() {   # run <script.js> <json-body>
  uip is resources scripts execute --connection-id "$CONN" \
    --inline-script "@$1" --body "$2" --output json | jq -r '.Data.Body'
}

run ./listUserGroups.js '{}'
# → [ ..., { "id": "S07CZR2B8CX", "handle": "is-shield-dev", ... }, ... ]
# filter for handle === "is-shield-dev" → S07CZR2B8CX

run ./addUsersToUserGroup.js '{"usergroup":"S07CZR2B8CX","users":["U03V8PM2ZDE"]}'
```
The write is idempotent — when every requested user is already a member, it
replaces the member list with itself — and Slack's response
(`{ ok: true, usergroup: {...} }`) is relayed verbatim, because the script
returns the `intsvc.http` result untouched.

## Slack gotchas
- The `httpRequest` / "Slack HTTP Request" passthrough object returns
  `unknown_method` for the usergroups methods — use the specific objects above.
- **Slack signals failures with `{ ok: false, error: "..." }` on HTTP 200, and
  the script DOES see it — so every action needs a guard.** (This used to say the
  opposite: the old IS exec endpoint absorbed the in-band failure into its own
  400 with the body in `providerMessage`, so the action never saw it. Execution
  relays the vendor verbatim now — the 200 arrives
  as a 200 and an unguarded script treats failure as success.)
- `usergroups.users.update` REPLACES members — the action reads current members
  and writes the union `[...existing, ...new]`.

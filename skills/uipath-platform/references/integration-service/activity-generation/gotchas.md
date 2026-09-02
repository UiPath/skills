# Common gotchas (all connectors)
- **Use the vendor's own path from its docs** as `url` — never the v3 object name
  (`usergroups_users_list_GET`) or the `httpRequest` passthrough. Both are IS
  identifiers, not vendor routes, and the vendor rejects them (Slack answers
  `unknown_method`). The exact form is the vendor's own: Slack is dotted
  (`/usergroups.users.list`), Jira is REST-pathed (`/rest/api/3/search`).
- **Pass query values in `query`, never hand-built into `url`.** The runtime
  encodes them correctly; hand-encoding does not. Measured on Jira: a JQL string
  with spaces (`project = ENGCE AND sprint in openSprints()`) is rejected when the
  spaces arrive as `+` — what `URLSearchParams` produces — because Jira's parser
  treats `+` as reserved. `%20` is required, and `query` produces it.
- **A relative `url` resolves UNDER the connection's `base.url`, its path
  included.** With Slack's `https://slack.com/api`, `/users.list` hits
  `https://slack.com/api/users.list` — never repeat the base's own path in `url`.
- **Vendor errors do NOT throw — check them, with the RIGHT check.**
  `intsvc.http` returns the vendor's status verbatim, so a 404 is
  `resp.status === 404` and nothing is raised; an unguarded script treats failure
  as success. But the guard is **vendor-specific**, and the wrong one fails in
  both directions:
  - `resp.status >= 400` — REST-conventional (Jira, most APIs). Misses a
    Slack-family `{ ok: false }` returned with HTTP 200.
  - `!resp?.body?.ok` — Slack-family. Throws on **every successful call** against
    any API that has no `ok` field, which is most of them.
  - `resp?.body?.error` — Graph-style error objects.

  Take the convention from the vendor's docs, not from an example written for a
  different vendor. Checking both status and payload is always safe. A `throw`
  from your script becomes `script_runtime` (422) carrying your message, which is
  the right signal for the caller.
- **Replace vs append**: confirm in step 2. If the write replaces,
  read-merge-write — both halves inside the one action (step 4), never a
  separate "read" action stitched together afterwards.
- **List envelopes**: `resp.body` is the vendor's own envelope, verbatim —
  `{ ok, users: [] }`, or a bare array. **There is no `{ items }` wrapping** —
  that was the old aliased-route behaviour and this path does not have it, so
  `resp.items` is always `undefined`. A list action unwraps the vendor's
  envelope INSIDE `execute()` and returns the **relevant records array** — you
  filter that array yourself. Pagination is NOT concatenated
  into that array: one invocation is one page, with the token on the
  `elements-next-page-token` header (step 3). Inside a main action,
  operation-internal reads (e.g. the read half of read-merge-write) unwrap
  `resp.body` the same way, and the main action returns the final `intsvc.http`
  result untouched.
- **Why IS metadata is NOT the authoring source** (the concrete reason behind the
  step-2 hard rule): `resources describe` lists request fields with dotted names
  (e.g. `message.toRecipients`) that are just *display* keys. Vendors like MS
  Graph / Outlook `send-mail` reject those flat keys and require the nested object
  (`{ message: { toRecipients, body: { content, contentType } } }`) — which is
  exactly what the vendor's public API/OpenAPI spec shows. Build from the vendor
  spec; if a write 400s with "missing parameter: X", the vendor-nested shape is
  the fix, and the step-2 probe confirms it. (Lookup *detection* — step 3 — is
  the one sanctioned authoring-time metadata use: which fields are IDs, and
  which resource resolves them.)
- **Match the verb to the operation**: a "send"/"create" object is a POST, not
  an update. The script's `method` is carried through verbatim, so the
  verb you write is the verb the vendor gets — a POST-only op like `send-mail`
  fails under the wrong one.
- **Budgets apply per run**: **4** brokered `intsvc.http`
  calls, 10 MiB total egress, 1 MiB request body, 1 s CPU, 64 MiB memory, 30 s
  wall clock. Exceeding calls/egress is `script_quota` (429); the deadline is
  `script_deadline` (504). A list action costs ONE of those calls because it
  returns one page (step 3); a script that walks the cursor itself is what makes
  the budget a problem.
- **No Node globals in the sandbox**: `Buffer`, `btoa`/`atob`,
  `TextEncoder`/`TextDecoder` are absent (`JSON` and `Uint8Array` are present).
  This is not academic — it is why the page token is encoded and decoded by
  `intsvc.handlePagination` / `intsvc.decodePageToken` instead of in your script.
  Anything else needing base64 has the same problem.

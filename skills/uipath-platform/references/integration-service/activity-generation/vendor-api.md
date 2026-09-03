# Constructing the vendor call — the vendor's API is the only source

The script calls `intsvc.http({ method, url, body })` with the **verbatim vendor
path** as `url`, and that path *is* the vendor's own public API method. Its form
is the vendor's own — Slack is dotted (`/users.list`), Jira REST-pathed
(`/rest/api/3/search`), MS Graph segmented (`/users`). **Derive
path + HTTP method + request body entirely from vendor-side sources — never from
IS metadata.** IS metadata plays **no part in authoring at all** — not the
path, not the method, not the body, and not lookup detection either. `describe`
is unreliable for the shape (display keys ≠ real body, and it omits
nested/replace/enum facts), and lookup detection does not need it: the vendor's
own docs say which fields are IDs, and the ID itself is fetched at run time by
running a lookup action **through the CLI** (step 3). There is no
authoring-time metadata step, and the skill ships no IS client of its own —
connections come from `uip is connections list` (step 1) and execution from the
the CLI (step 4).

Source the API shape, in this order:
1. **Vendor OpenAPI / Swagger spec.** If the vendor publishes one, fetch it and
   read the operation directly — it gives path, method, and request schema
   verbatim. This is the strongest source.
2. **Vendor public API docs.** For the major vendors you already know these:
   - Outlook `/send-mail` ↔ MS Graph `sendMail`; `/messages` ↔ `/me/messages`
   - Slack `/usergroups.users.list`, `/chat.postMessage` ↔ Slack Web API methods
   - the HTTP verb follows the operation (send/create → POST, list/get → GET).
   Use `WebFetch`/`WebSearch` to pull the exact method + body when unsure.
3. **When nothing is publicly available** (private/OEM connector, undocumented
   API): **STOP and ask the human** where to fetch it — a spec URL, a developer
   portal, an internal doc, or one example request/response. Do not guess a path
   or body for an undocumented API; a wrong path is rejected by the vendor (Slack
   answers `unknown_method`) and a wrong body fails opaquely.

Then **confirm the body empirically against the live endpoint** — this is a
verification of the vendor-derived shape, not a discovery step. The exec
endpoint's error responses act as a check: seed with the vendor's canonical body,
POST it, and read the 400 — patch until the error stops being **structural**
(missing/misplaced field) and becomes a **value** complaint (bad recipient,
invalid enum). That transition confirms the shape. This catches where the IS
connector reshapes the vendor API (e.g. Outlook wants comma-separated recipient
strings, not Graph's arrays) — but the *starting point* is always the vendor
spec, never IS metadata.

For a **read** object, note the vendor's response envelope from its docs, then
confirm it when you run the action (step 4): it arrives verbatim as `resp.body`,
and the action names the records key itself (`resp.body.users`, or `resp.body`
when the vendor returns a bare array). Don't probe it through Integration
Service — the aliased route imposes its own `{ items }` wrapper, so you would be
confirming the wrong shape.

For a **write** object, converge the body by hand — there is no tool for this.
Send it, read the vendor's rejection, patch, and send again:

```bash
uip is resources scripts execute --connection-id <id> \
  --url <absolute-vendor-url> --method POST --body '{}' --output json
```

Read `Data.Body` — the vendor's own text, verbatim, not an IS wrapper — and
iterate. A complaint that a field is **missing or misplaced** is structural: patch
the body and retry. A complaint about a **value** means the shape is already
right. Note the SAFETY rule:

- For a side-effecting object with no safe invalid value, pass `--dry` to stop
  after one probe and emit from whatever structure was learned.
- **Do not** run the converge loop against a production write endpoint without
  the user's go-ahead. It sends many deliberately malformed calls to learn a
  schema, which is a different thing from a single verified write. Confirm the
  object and connection with the user first.

Worked example (Outlook `/send-mail`), the exact convergence signal:
- `{}` → 400 *"missing parameters: **Message**"* → structural: add top-level `message`.
- `{message:{subject}}` → 400 *"ErrorInvalidRecipients / no recipients"* → the
  error is now about the DATA, not the shape → **converged**. Body is
  `{ message: { toRecipients, subject, body:{ content, contentType } } }` — the
  NESTED shape, which is exactly what `describe`'s flat `message.toRecipients`
  keys would have gotten wrong.


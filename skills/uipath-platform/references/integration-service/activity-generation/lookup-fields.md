# Lookup fields — the headless equivalent of a design-time lookup


**What lookup fields are.** In Integration Service, activities configured in
Studio resolve human-friendly values into vendor IDs at *design time*:
connector metadata declares that a field like `channel` is populated from
another resource on the same connector (the conversations list), the designer
picks a name from a dropdown through the live connection, and the workflow
stores the underlying ID. At runtime the activity receives the ID directly and
never resolves names. A code-generated action has no design-time step, so this
skill reproduces the same split explicitly: resolution runs as its own action,
BEFORE the main action.

**Spotting one:** the main call's body requires a vendor-internal ID
(`channel`, `user`, `sys_id` — field descriptions read "ID of ...") but the
user supplied a name/handle/email. The resolver resource comes from the
**vendor's API** — the resource whose list contains that entity type (channel →
conversations list, user → users list). You do not need connector metadata to
work this out, and you should not go looking for it: the vendor documents which
fields are IDs, and the ID's actual VALUE is fetched at run time by running the
lookup action through the CLI (item 3 below).

**Not everything multi-call is a lookup.** Apply the litmus test: would this
call still be needed if every input were already a vendor-canonical ID? A
members read before a replace-style write, or a metadata call whose response
feeds the next request (`files.info` → download URL), is needed regardless of
how the inputs were expressed — that's the OPERATION, and it belongs inside
the main action's `execute()` (step 4), never in a lookup action. Only pure
name/handle/email → ID translation is resolved outside.

A lookup is served by **a normal action, a separate activity in its own
right** — a plain list action over the resolver resource, named for the vendor
operation (`listConversations`, `listUserGroups`), returning the **relevant
records array** (the vendor's own envelope — `{ ok, users: [] }` off
`resp.body` — is unwrapped inside the action; the consumer gets the array,
e.g. `users`). The action does NO matching; **you run it and
filter its output**. The SR records which lookup serves the field, as that
field's `design.scriptRef` (step 5).

The procedure, per lookup field:
1. **Reuse before create.** Search the working dir for an existing action
   covering this resolver — match by the vendor path it calls (grep the action
   files for the list path), not by filename. If one exists, use it.

   **Some lookups make no vendor call.** A field whose choices come from the
   *connection* rather than the vendor needs a lookup script that makes **zero**
   `intsvc.http` calls and computes the array from
   `context.connectionConfiguration`. Slack's token picker is the example: it
   returns `[{name:'Bot',value:'bot'}, …]` by reading which tokens the connection
   holds. Recognise these by the question they answer — "which of the things this
   connection is configured with?" rather than "which of the things the vendor
   has?" — and note the redaction rule: secrets are stripped from
   `connectionConfiguration`, so derive from a non-secret key (a scope list, a
   base URL), never from a token value.
2. **Else generate it** as `List<Entities>.js` (see [example-list-action.js.txt](example-list-action.js.txt)) —
   same naming style as a main action, since its base name is its `scriptRef`:
   a normal list action whose inputs pass through the resource's query params,
   and whose output is the **relevant records array**.

   **Pagination: ONE page per invocation — the script never walks the list.**
   The runtime carries no page token. The script returns the page the vendor
   answers with; if a caller needs another page, the vendor's own paging
   parameter (`cursor`, `offset`, `page`) is an ordinary input passed through in
   `query`.

   ```js
   async function execute(context) {
     const { limit, cursor } = context.request.body ?? {};
     const query = { limit: String(limit ?? 200) };
     if (cursor) query.cursor = cursor;   // the vendor's own paging param, passed through

     const listed = await intsvc.http({ method: 'GET', url: '/users.list', query });
     // Slack's failure signal. Use YOUR vendor's — see the gotchas.
     if (!listed?.body?.ok) {
       throw new Error('Failed to list users' + JSON.stringify(listed?.body ?? listed?.raw));
     }

     // A LIST action returns the RELEVANT RECORDS ARRAY — the vendor envelope
     // unwrapped, and nothing else. Mutate the intsvc.http result so its
     // status and content-type header travel with it.
     listed.body = listed.body.members ?? [];
     return listed;
   }
   ```

   **Do NOT loop inside the script.** An internal `do…while` over the cursor
   concatenates pages the caller did not ask for and dies mid-walk with
   `script_quota` (429) on a large tenant — there are only 4 brokered calls per
   request.

3. **Run it (step 4) and filter the array yourself** for the target entity:
   ```
   uip is resources run script --connection-id "$CONN" \
     --inline-script @./listConversations.js --output json | jq -r '.Data.Body'
   # → [ { "id": "C0A66...", "name": "...", ... }, ... ]
   # filter for name === "sanjeet-test" → its id
   ```
   One call returns one page. If the target is not in it, run again with the
   vendor's paging parameter passed as an input (e.g. `--body '{"cursor":"…"}'`
   for a script that forwards `cursor`), until the vendor stops returning one.
4. **Pass the ID as the main action's input.** Main-action ID inputs are
   always vendor-canonical IDs.

Lookups are READS — safe to run automatically. When the user already supplied
the raw ID, skip the lookup and pass it through (the design-time analogy:
pasting an ID instead of picking from the dropdown). For a destructive write,
prefer running the lookup anyway as a verification read — the filtered entity
IS the echo step 4 requires before a write, and it catches wrong-entity mistakes (e.g. a
*user* named `user_test` shadowing a *channel* named `user-test`).


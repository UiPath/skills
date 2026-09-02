# Activity Generation

Generate a connector activity from the **vendor's own API documentation**, when
the connector exists but neither an activity nor a resource covers the operation
you need — [agent-workflow.md — Step 4b](agent-workflow.md#step-4-discover-capabilities)
is where that is established.

Start from [vendor-docs-registry.json](vendor-docs-registry.json) for the docs URL:
it maps 28 vendors to their authoritative API reference, plus a `dynamic` flag and
per-vendor notes. Never guess a docs URL when the registry has one.

Produces four artifacts in a temporary directory: the action script, one script
per lookup field, the reviewable contract, and the activity metadata. Whether you
then execute the script or keep the activity depends on how you were asked — see
[Two ways this is invoked](#two-ways-this-is-invoked).

> **Do not start here on a hunch.** Confirm the operation is genuinely
> unreachable first: an activity list has far fewer entries than the resource
> list behind it, so most "missing" operations are reachable as a resource.

## Prerequisites

- `uip login`
- an **Enabled** connection for the connector — `uip is connections list <key> --all-folders`
- a running IPE Runtime Proxy reachable by `uip is resources scripts execute`

## Can this connector host a generated activity?

```bash
uip is connectors metadata <connector-key> --output json
```

Read `Data[0].Flags.SupportsV4Activity`. Generate only when it is `true`.

**Test the value, not the presence of `Flags`.** `Flags` is `{}` on most
connectors rather than absent, so `Flags && …` passes while
`Flags.SupportsV4Activity` is `undefined`. Measured: `uipath-salesforce-slack`
returns `{"SupportsV4Activity": true}`; `uipath-atlassian-jira`,
`uipath-microsoft-teams` and `uipath-google-drive` all return `{}`.

This is a **capability check, not an authorization decision** — it says the
connector can host a generated activity, not that the caller may call anything.
Auth remains the connector's own IS connection, enforced at runtime.

---

## References

Everything needed to generate an activity from nothing lives here — this skill
carries its own copies and depends on no other skill.

| Read when | File |
|---|---|
| **Before writing your first script** — the runtime contract: `context`, every `intsvc.http` parameter, the response shape, failure detection, pagination, budgets, what the sandbox lacks | [activity-generation/runtime.md](activity-generation/runtime.md) |
| Deriving the call from the vendor's API, and converging a write body | [activity-generation/vendor-api.md](activity-generation/vendor-api.md) |
| The vendor's authoritative docs URL, and whether its objects carry custom fields | [vendor-docs-registry.json](vendor-docs-registry.json) |
| Any input that is a vendor-internal ID | [activity-generation/lookup-fields.md](activity-generation/lookup-fields.md) |
| Authoring the min.json — the schema and every derivation rule | [activity-generation/minimal-metadata-design.md](activity-generation/minimal-metadata-design.md) |
| The metadata procedure, and its field-by-field contract | [activity-generation/standard-resource.md](activity-generation/standard-resource.md) · [contract](activity-generation/standard-resource-contract.md) |
| Mistakes that recur across connectors | [activity-generation/gotchas.md](activity-generation/gotchas.md) |
| A complete worked connector, end to end | [activity-generation/slack.md](activity-generation/slack.md) |
| Target shapes to copy | [example-action.js.txt](activity-generation/example-action.js.txt) · [example-list-action.js.txt](activity-generation/example-list-action.js.txt) |

## Two ways this is invoked

The steps are the same either way. What differs is **whether the caller already
supplied the values and asked for the operation to be performed**.

| | **Fulfilling a request** | **Authoring for later** |
|---|---|---|
| the caller gave you | the operation **and** its values, and wants it done | the operation only |
| a write | **just run it** — the request is the authorisation | **stop and ask** (step 4) |
| a missing required value | ask for that value, then run | ask for it as part of step 4 |
| artifacts | still produced, still discarded with `/tmp` | the deliverable |

**Fulfilling a request** is the case where someone asked for the operation
itself — "create a channel named `test`". Creating it *is* the goal, so there is
nothing to seek permission for and no dummy value to propose. Ask only for values
the request left out, then execute.

**Authoring for later** is the case where the activity is the product and no one
has asked for its side effect to happen yet. That is where step 4's write prompt
applies.

Either way you produce all four artifacts — a script verified by a real call is
worth nothing later if its contract was never written down.

## Workflow

### 1. Scratch workspace

```bash
WORK=$(mktemp -d /tmp/ipe-activity-<connector>.XXXXXX) && echo "$WORK"
```

Everything is generated here. **Nothing is installed or moved** unless the user
asks — the artifacts are the deliverable, not a change to any repository.

### 2. Derive the call from the VENDOR's public API

Path, method and request body come from the vendor's own docs or OpenAPI spec —
**never from IS metadata**. IS is the execution path, not an API catalogue, and
its resource shapes carry v3 artifacts that will mislead you.

**Ground the endpoint first**, the same way
[http-request.md](http-request.md#step-0-ground-against-the-vendors-api-docs-registry--connector-mode-only) does — a wrong-but-plausible
path often still "completes", because many vendors answer an unknown method with
HTTP 200 and an error body (Slack: `{"ok":false,"error":"unknown_method"}`).

1. Look the connector up in
   [vendor-docs-registry.json](vendor-docs-registry.json) — match by
   `connectorKey`.
2. **If listed:** read its `docsUrl` (authoritative reference) and `notes`
   (vendor-specific conventions — GitHub wants
   `Accept: application/vnd.github+json`, Slack is method-per-operation).
   **Honor the notes verbatim**, then let step 4's run confirm the exact path: the
   live call is the final authority; the registry only grounds the baseline.
   `dynamic: true` means the object carries tenant-specific custom fields (Jira's
   `customfield_*`), so the documented field set is incomplete by design and the
   live response is the only way to see the real shape.
3. **If NOT listed:** grounding does not apply — derive from the vendor's public
   docs as usual, and ask the user for the spec if nothing public exists.

**Pass vendor paths verbatim — do not "REST-ify" them.** A dotted method is one
path segment: `/chat.postMessage`, never `/chat/postMessage`.

This step also **reveals the lookup fields**: any input that is a vendor-internal
ID a human would not type (`C0A66HP9KKM`, `S07CZR2B8CX`).

### 3. Resolve lookup fields FIRST

For each ID-typed input, write a **list action** — a flat script that returns the
relevant records array and does **no matching** — then verify it (step 4) and run
it, filtering the output yourself for the target entity.

You need this before the main script for two reasons:

- the main call takes vendor-canonical IDs, and inventing one gets you
  `channel_not_found` rather than a working call;
- the contract (step 5) references each lookup by its script's base name.

A lookup is a **read**, needs no invented input, and is therefore the cheapest
thing to verify — it doubles as the first proof that the connection, credential
and routing all work.

### 4. Write the main script, then test it

**Decide first whether the operation has side effects.** Reads may be run
immediately; writes may not be run at all until the user chooses to. Do not
execute anything before you have placed the operation on one side of that line.

#### Reads — converge automatically

`List`, `Retrieve` and `Download` change nothing, so iterate them without asking:

```bash
uip is resources scripts execute \
  --connection-id <connectionId> \
  --inline-script @$WORK/<Name>.js \
  --body '{ "channel": "C0A66HP9KKM" }' \
  --output json
```

Read `Data.Body` — the vendor's own response text, verbatim — and loop:

| the vendor says | do |
|---|---|
| a field is missing or misplaced | patch the body, run again |
| a **value** is bad | ask the user for the real one — do not substitute another guess |
| success | done; keep the response, step 5 needs it |

**Converge to success, not to a rejection.** A `404`, a `403 missing_scope` or an
in-band `{ ok: false }` proves the script compiles, routes and carries its logic —
and proves nothing about whether the activity works. A value chosen *because* it
will be rejected is not a test.

#### Writes — run only if asked for

`Create`, `Update`, `Replace`, `Delete` and `Upload` change state in a real
tenant. `Unknown` counts as a write — if you cannot tell what the operation does,
you cannot tell that it is safe.

**If the caller asked for the operation to be performed and gave you its values,
run it.** The request is the authorisation; ask only for required values the
request left out, and do not offer to test something the caller already asked for.

**Otherwise — you are authoring the activity, not performing it — do not run a
write on your own initiative.** Stop, say what the call would do, and offer three
choices:

| option | what happens |
|---|---|
| **1. Test with example values** | You propose concrete dummy values and show them before running — e.g. a channel named `test-<timestamp>`, a record titled `probe-<timestamp>`. The user approves, then you converge as for a read. |
| **2. The user supplies the values** | The user names the real entities. Echo them back before running — the step-3 lookup output gives you the readable names for free. |
| **3. Skip the test** | The script is delivered **unverified**, on the strength of the generation alone. |

Propose option 1 with the values already filled in — an option the user has to
invent values for is not really an option. Name what the call will create or
change, not just the field values.

**Option 3 ships an unproven script**, and the report must say so: it is not
`✅ generated`, it is `⚠️ untested`. Never present an untested write as working,
and never quietly pick option 3 because a write looked risky — that is the
choice the user is being asked to make.

Only once the user has picked option 1 or 2 do you run it — the same command as
for a read, with the agreed values:

```bash
uip is resources scripts execute \
  --connection-id <connectionId> \
  --inline-script @$WORK/<Name>.js \
  --body '{ "name": "test-1756900000" }' \
  --output json
```

From there it converges on the same rule as a read: a real vendor operation, not
a rejection.

#### Either way

Ask **once, for the whole batch** — list every input you need in a single
question rather than interrupting per attempt.

**Two failures are environmental and acceptable**: a scope the connection's token
lacks, and a vendor host the egress guard blocks. Record those as caveats.
Everything else blocks, including a rejection caused by a value you invented.

**The script contract is in
[activity-generation/runtime.md](activity-generation/runtime.md)** — one top-level
`execute(context)`, no imports, no TypeScript, `intsvc.http` as the only egress,
`resp.body` not `resp`, a vendor 4xx is a normal return, one page per invocation
for a list. Read it before writing your first script rather than inferring the
signature from an example.

### 5. Author the min.json

The **minimal-metadata file is the reviewable source of truth**; the activity
metadata is compiled from it. Write it only now, because its output half cannot
be written before the script has run.

| half | source |
|---|---|
| **inputs** | the FULL vendor surface — every parameter and field, required and optional, from the vendor spec |
| **outputs** | **minimal** — the record identifier(s) and the value the operation exists to return |
| `design.scriptRef` per lookup field | the lookup script base names from step 3 |

**Outputs stay minimal, and not merely to keep them short.** They would otherwise
be enumerated from a *single observed response* — a sample, not a contract.
Optional fields may be absent from it, nullable ones vary by entity, and a
different input may return a different shape. Declaring all of it asserts more
than the evidence supports.

So: mark each identifier `primaryKey: true` and list it in `metadata.primaryKey`,
add any value that is the *purpose* of the operation (the download URL a get-file
operation exists to return), and omit everything else the vendor happened to
return. The envelope's own error signalling (`ok`, `error`) stays out — the
script detects failure and raises it, so it never reaches a consumer as data.

For a **List**, the records array is the single top-level output, and its element
fields get the same trim.

### 6. Compile the metadata

```bash
uip is activities metadata build $WORK/<Name>.min.json
uip is activities metadata types $WORK/<Name>.json $WORK/<Name>.js
```

`build` validates before it writes — a rejected build leaves no artifact behind.
It enforces the contract rules that would otherwise fail at runtime: `scriptRef`
must be a bare base name, `primaryKey` only on a returned field, a true array
never carries a delimiter, required inputs are `primary` and optional ones
`secondary`, a reference never carries `objectName`, and a List declares exactly
one `[*]` output.

**Never hand-edit generated metadata** — fix the min.json and rebuild.

`types` stamps the `/* type … */` header onto the script, derived from the
metadata so the two cannot drift. Re-running replaces the header in place.

---

## What you produce

```
$WORK/<Name>.js            the main action, verified, with its type header
$WORK/<Lookup>.js          one per lookup field, each verified
$WORK/<Name>.min.json      the reviewable contract
$WORK/<Name>.json          the compiled activity metadata
```

## Keep the scripts readable

The type header plus a **one- or two-line** description of what the activity does
is the baseline. Beyond that, comment only what a reader cannot get from the
code: a vendor quirk that explains the shape of the call, or a behaviour
deliberately preserved.

Do **not** restate the runtime contract, the sandbox's constraints, or how
credentials are injected. It is identical in every script, and a script embedded
in a JSON field pays for every line twice.

## Report

Finish with one table covering every activity you generated, including any you
could not complete:

| Activity | Status | Verified by | Lookups | Notes |
|---|---|---|---|---|
| `ListChannels` | ✅ generated | 200, 12 records | — | read — converged automatically |
| `ArchiveChannel` | ✅ generated | 200, `ok:true` | `ListChannels` | write — tested on `test-1756…` (option 1) |
| `DeleteMessage` | ⚠️ untested | not run | `ListChannels` | write — user chose not to test |
| `UploadFile` | ⚠️ caveat | 1st call 200; 2nd blocked | — | `files.slack.com` not in the egress allowlist |

- **Status** — `✅ generated` means a real vendor operation completed.
  `⚠️ untested` means the script was delivered on the strength of generation alone
  (a write the user chose not to test). `⚠️ caveat` means only a missing scope or a
  blocked egress host stopped it — say what would unblock it.
- **Verified by** is the evidence — "it ran" is not evidence; name the vendor's answer.
  For an untested write, write `not run`, not something that implies otherwise.
- For a write, say **which option** was used and against what entity, so a reader
  can tell a real test from a dummy one.

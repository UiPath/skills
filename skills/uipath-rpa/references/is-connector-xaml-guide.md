# Authoring Integration Service `ConnectorActivity` XAML

End-to-end playbook for building a headlessly-runnable IS `ConnectorActivity` XAML from a known connector + operation. Use this whenever the request is **"call connector X for operation Y from a XAML workflow"** and Studio's designer is not available or not desired.

## When to Use

- Headless / scripted authoring of IS workflows (no Studio GUI in the loop).
- CI-style generation where the XAML must be portable across machines.
- Any time you know the connector key and operation name upfront (e.g., `uipath-salesforce-slack` + `send_message_to_channel_v2`).

**Prefer this over per-product BAF activity packages** (`UiPath.Slack.Activities`, etc.). Those wrap IS internally and use a more complex BAF (Business Activity Framework) XAML shape that is equally fragile to hand-author. The IS `ConnectorActivity` flow below is schema-driven and mechanical.

## Activity Shape

```xml
<isactr:ConnectorActivity
    Configuration="<base64-gzip-blob>"
    ConnectionId="<CONNECTION_GUID>"
    UiPathActivityTypeId="<ACTIVITY_TYPE_GUID>"
    xmlns:isactr="http://schemas.uipath.com/workflow/integration-service-activities/isactr">
  <isactr:ConnectorActivity.FieldObjects>
    <isactr:FieldObject Name="<fieldName>" Type="FieldArgument">
      <isactr:FieldObject.Value>
        <InArgument x:TypeArguments="x:String">
          <CSharpValue x:TypeArguments="x:String">"<literal>"</CSharpValue>
        </InArgument>
      </isactr:FieldObject.Value>
    </isactr:FieldObject>
    <!-- repeat per field; include every field from the default XAML even if unset -->
  </isactr:ConnectorActivity.FieldObjects>
</isactr:ConnectorActivity>
```

Three ingredients:
1. **`UiPathActivityTypeId`** — the operation's type GUID (from `activities find`).
2. **`ConnectionId`** — the IS connection's GUID (from `uip is connections list`).
3. **`Configuration`** — an opaque base64 + gzip JSON blob encoding connector/operation identity. **Never hand-edit.** Always take the value from `activities get-default-xaml`.

## IS activity types & how fields resolve

`get-default-xaml` produces all four IS activity shapes from a `typeId` (+ a live connection). What *unlocks* an activity's fields differs by type — hand the tool the right selector and it returns the resolved `FieldObjects`:

| Activity | What it is | How to resolve its fields |
|---|---|---|
| `ConnectorActivity` | A connector operation (create / get / update …) | `typeId` + connection. A **generic** operation needs `--object-name <obj>` (the record type); criteria fields fed back via `--field-values` expand the rest (Step 4). |
| `ConnectorTriggerActivity` | Fires when a connector event occurs | Curated triggers resolve from `typeId` + connection; a **generic** trigger needs `--object-name <obj>` (the object whose changes it watches). |
| `ConnectorPersistenceActivity` | Suspends the workflow until a connector event | Discover events with `uip is activities list <connector> --triggers`, then `--event-operation <op>` resolves the event's fields. A named event auto-resolves its single object; a generic/multi-object event also needs `--object-name <obj>` (Step 4). |
| `ConnectorHttpActivity` | Generic HTTP-request escape hatch | Standard request fields (`method`, `url`, `headers`, `query`, `body`) — author them directly; they are the same for every connector. |

Same principle throughout: **pass the selector the activity needs, get back its resolved schema.** A bare call (no selector) returns the correctly-typed activity with its baseline fields.

## Step-by-Step Flow

### Prereq: `uip login`

`uip is *` commands silently fail without an authenticated session. Log in first:

```bash
uip login                                                       # production (cloud.uipath.com)
uip login --authority https://alpha.uipath.com/identity_        # alpha
uip login --authority https://staging.uipath.com/identity_      # staging
```

The command is **interactive** (opens a browser). If you need the user to run it themselves, ask them to type `! uip login` so the token lands in the current session.

### Step 1 — Install `UiPath.IntegrationService.Activities`

Required for the `isactr:ConnectorActivity` type.

```bash
uip rpa packages versions --package-id UiPath.IntegrationService.Activities --project-dir "<PROJECT_DIR>" --output json
uip rpa packages install --packages id=UiPath.IntegrationService.Activities --project-dir "<PROJECT_DIR>" --output json
```

### Step 2 — Find the operation's `activityTypeId`

```bash
uip rpa activities find --query "<search terms>" --project-dir "<PROJECT_DIR>" --output json
```

In each result, look for:
- `activityTypeId` → populated only for IS/dynamic activities. Copy this value.
- `description` → identifies which operation (e.g. `"Send messages to public or private Slack channels."` vs `"Send a reply to a message in a Slack channel."`).

If `activityTypeId` is empty, the activity is a non-dynamic BAF/vendor activity (e.g. `UiPath.Slack.Activities.Messages.SendMessage`) — different flow, not covered here.

**`activities find` is not exhaustive — be ready to iterate.** Results vary by connector: some expose 6+ typed operations with rich descriptions (Slack); others expose only 1-2 (Outlook). Try several query phrasings (`"send email"`, `"<connector> send"`, the literal operation name from `uip is activities list`). If no typeId surfaces:

- The operation may only be reachable via the generic `ConnectorHttpActivity` typeId (suffix `...httpRequest...`). Use it as a fallback — see [Typed Operation vs Generic HTTP](#typed-operation-vs-generic-http) for its standard, connector-independent request fields.
- Different connectors that share a schema (e.g. a mock connector + its real counterpart) often share typeIds. The same `fbdeec58-...` "Send Email" typeId works for both `uipath-mock-outlook` and `uipath-microsoft-outlook365` — the `ConnectionId` at runtime determines which backend receives the call. Don't be surprised if the discovered typeId's description mentions a different connector than the one you're targeting.

### Step 3 — Get the connection ID

```bash
uip is connectors list --output json                            # find connector key
uip is connections list <connector-key> --output json           # list tenant's connections
```

If none exist: `uip is connections create <connector-key>` (interactive OAuth). If that can't be done in-session, use a placeholder `00000000-0000-0000-0000-000000000000` and flag it for the user — but the workflow will fail at runtime until a real connection is wired up.

### Step 4 — Get the fully-populated default XAML

**This is the unlock step.** With both the type ID and connection ID:

```bash
uip rpa activities get-default-xaml \
    --activity-type-id "<TYPE_ID>" \
    --connection-id "<CONNECTION_ID>" \
    --project-dir "<PROJECT_DIR>" \
    --output json
```

The response contains the complete `ConnectorActivity` element with:
- A real `Configuration` blob for that specific connector+operation combo.
- A `FieldObjects` list with one entry per field of the operation's resolved schema (older CLI versions emit only the curated/visible-by-default subset).
- A real `ConnectionId` (uses the supplied one, or auto-resolves a tenant default).

**Without `--activity-type-id`**, the default comes back essentially empty (`Configuration={x:Null}`, no fields). That generic default is not runnable.

#### Pass field values with `--field-values`

`get-default-xaml` accepts literal input-field values as repeatable `key=value` pairs (one `--field-values` per field). Two effects:

1. **Values are pre-bound** as literals in the returned `FieldObjects` — no hand-editing of `InArgument`/`CSharpValue` for literal values (expressions still go through Step 6).
2. **Schema expansion.** Many operations expose only a few "criteria" fields by default and reveal the rest of the schema only once those criteria have values. In Studio's designer the re-resolve fires when the user commits a criteria field in the canvas; headlessly, passing the criteria via `--field-values` triggers the same re-resolve, and the `Configuration` blob comes back with the **expanded** field set as new `FieldObjects`.

**Run it twice — discover, then expand.** You won't know a connector's criteria fields ahead of time, so make two calls:

1. **First call — no `--field-values`.** Whatever `FieldObjects` come back are the operation's prerequisite fields. **Those returned field names _are_ your criteria candidates** — there is no separate place to look them up; the curated baseline is the list.
2. **Second call — feed those same field names back inline** with `--field-values`. The response now carries the expanded schema; author against it.

```bash
# 1. discover the criteria fields (curated baseline)
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN>" --project-dir "<P>" --output json
# 2. feed those field names back inline to expand the rest
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN>" \
    --field-values <fieldFromStep1>=<value> --project-dir "<P>" --output json
```

When you already know valid criteria values up front, the second call alone does both.

> **Expansion requires a LIVE connection and real values — there is no offline path.** It is a design-time cloud round-trip to the connector. `--connection-id` must be an enabled connection that resolves on your current `uip login` (correct org + tenant), and each value must actually exist in that system. If the connection is dead / wrong-tenant, or a value is invalid, the call returns the **curated baseline unchanged, with no error and no new fields** — a silent no-op, not a visible failure. So when expansion "does nothing", suspect the connection or the values, never the flag; re-confirm the connection is live (Step 3) before concluding the activity has no more fields.

**Field-name encoding.** Pass names **exactly as they appear in the returned `FieldObjects`** — copy them verbatim from the previous call's output. Don't hand-encode or invent names: the connector's encoding (nested paths, arrays — see § FieldObject Name Encoding Rules) is already applied in what it hands you. An unknown name fails fast with the list of available fields, so use that error as discovery rather than guessing.

**Older CLI fallback:** if `--field-values` is not recognized, upgrade `uip`. Until then the expansion is not reachable headlessly — bind only fields present in the returned XAML and treat missing ones per § Hidden Secondary Fields.

#### Resolve persistence event fields with `--event-operation`

A `ConnectorPersistenceActivity` ("suspend until an event") exposes no event fields until an **event operation** is chosen — the headless equivalent of picking the event in the designer before its fields appear. The event operation is a connector-specific value (e.g. `TICKET_UPDATED`, never the prose "ticket updated"), so **discover it — do not guess it.**

**Step A — list the connector's events** (the same catalog the designer's dropdown uses; no connection needed):

```bash
uip is activities list <connector-key> --triggers --output json
```

Each entry's **`Name`** is the value for `--event-operation`; its **`ObjectName`** tells you the kind:

```
Name            DisplayName      ObjectName   IsCurated
TICKET_UPDATED  Ticket Updated   tickets      Yes        ← named event: object is built in
CREATED         Record Created   N/A          No         ← generic op: choose an object too
```

- **Named event** (`ObjectName` populated, e.g. `TICKET_UPDATED`) — pass its `Name` to `--event-operation`; its single object auto-resolves, so no `--object-name` is needed.
- **Generic op** (`CREATED` / `UPDATED` / `DELETED`, `ObjectName` is `N/A`) — also pass `--object-name <obj>`. List the objects it applies to with:
  ```bash
  uip is triggers objects <connector-key> CREATED --output json
  ```

**Step B — resolve the activity** with the chosen operation:

```bash
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN>" \
    --event-operation "TICKET_UPDATED" --project-dir "<P>" --output json
```

The returned `Configuration` carries the resolved event fields as `FieldObjects`. Without `--event-operation` you get the bare activity (correct default, no event fields). It is the persistence analogue of `--field-values` criteria — a selector that unlocks the schema — and the resolution needs a live connection (same cloud round-trip and silent-no-op caveat as above). Combine with `--field-values` to also pre-bind values.

#### Select the object for generic activities with `--object-name`

A **generic** `ConnectorActivity` (Insert / Get / Delete a record) or a generic event has no object baked into its `typeId`, so `get-default-xaml` returns it bare until you name the object — the headless equivalent of the designer's object dropdown. Pass `--object-name <obj>`:

```bash
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN>" \
    --object-name issue --project-dir "<P>" --output json
```

Discover valid object names (use the `Name` field, not the display name):

- Generic activity → `uip is resources list <connector-key> --output json`
- Generic event → `uip is triggers objects <connector-key> <EVENT> --output json`

A named event auto-resolves its single object, so `--object-name` is only needed for generic operations and multi-object events. It is the same kind of selector as `--event-operation` (identity that unlocks the schema), needs a live connection, and combines with `--event-operation` and `--field-values`.

### Step 5 — Read the operation's field schema

For each field you want to bind, you need its declared `name` and `dataType`. Read the schema from Integration Service:

```bash
uip is resources describe <connector-key> <object-name> --operation Create --output json
```

The second positional is the **object/resource name** (from `uip is resources list`), not the operation; the operation goes in `--operation`. Note: it's `resources describe` (not `activities describe`). `activities` only has `list`.

The response includes a `metadataFile` path like:
```
~/.uipath/cache/integrationservice/<connector>/_static/<operation>.Create.json
```

Read that file directly for the full schema — `parameters`, `requestFields`, `responseFields`, each with `name`, `dataType`, `required`, `description`, and any enum values. **Never guess field names from memory** — the schema is the source of truth, and guessed names trigger a `Configuration contains a breaking change` runtime error.

### Step 6 — Bind values using `InArgument` + `CSharpValue`

Only needed for **expression** values or when editing an existing XAML — literal values are better passed via `--field-values` in Step 4, which pre-binds them in the returned XAML.

For each field you want populated:

```xml
<isactr:FieldObject Name="<fieldName>" Type="FieldArgument">
  <isactr:FieldObject.Value>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">"<literal or expression>"</CSharpValue>
    </InArgument>
  </isactr:FieldObject.Value>
</isactr:FieldObject>
```

Leave the rest as bare `<isactr:FieldObject Name="..." Type="FieldArgument" />` entries — **keep every FieldObject from the default XAML**, even if you don't bind a value. Removing fields causes schema-mismatch errors.

**Do not put literal values in the `FieldObject Value=""` attribute** — Studio silently ignores that path. Use the element form above.

For VB projects, swap `CSharpValue` → `[bracket]` expression shorthand on the `InArgument` element per the project's expression language (see [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md)).

#### FieldObject `Name` Encoding Rules

Schema field names from `describe` / the cached JSON (`message.toRecipients`, `send-mail-v2`, etc.) must be **translated** when written as `FieldObject Name`:

| Schema character | XAML encoding | Example |
|---|---|---|
| `.` (dot) | `_sub_` | `message.body.content` → `message_sub_body_sub_content` |
| `-` (hyphen) | `minus_sign` | `send-mail` (in `Jit_send-mail`) → `Jit_sendminus_signmail` |
| `_` (underscore) | unchanged | `send_as` → `send_as` |
| `[*]` (array suffix) | `_array` | `tags[*]` → `tags_array`, `fields[*].id` → `fields_array_sub_id` |

Apply rules in order; translate every segment for nested paths (`collaborator_ids[*]` → `collaborator_ids_array`).

Default XAML reflects correct encoded names for fields it returns — **copy verbatim**. With current CLI versions the returned `FieldObjects` cover the blob schema exhaustively; a schema-documented field that is still absent is criteria-gated or a query parameter — see [Hidden Secondary Fields](#hidden-secondary-fields).

#### Matching `x:TypeArguments` to the Field's Data Type

The schema's `type` (or `dataType`) determines the `x:TypeArguments` on both the `InArgument` and the inner `CSharpValue`:

| Schema type | XAML | Value literal |
|---|---|---|
| `string` | `x:String` | `"hello"` |
| `boolean` | `x:Boolean` | `true` / `false` (no quotes) |
| `integer` / `int32` | `x:Int32` | `42` |
| `number` / `double` | `x:Double` | `3.14` |
| `date-time` | `s:DateTime` (plus `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`) | `DateTime.UtcNow` |
| enum | `x:String` with allowed value | `"high"` |
| object / array | `x:String` with JSON-encoded content | `"{\"key\":\"value\"}"` |

Mismatched types (e.g., binding `saveToSentItems` with `x:String` when the field is `boolean`) cause a `Configuration contains a breaking change` error at runtime.

Example — boolean field:
```xml
<isactr:FieldObject Name="saveToSentItems" Type="FieldArgument">
  <isactr:FieldObject.Value>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">true</CSharpValue>
    </InArgument>
  </isactr:FieldObject.Value>
</isactr:FieldObject>
```

#### Hidden Secondary Fields

A field is only honored at runtime if it exists in the **`Configuration` blob's schema** — the blob, not the `FieldObjects` list, is the contract. A hand-added `FieldObject` whose field is missing from the blob's schema passes `validate` and `build` clean and is **silently dropped** by the connector at runtime — the API call goes out without it, typically surfacing later as a confusing connector/runtime error (a 4xx about missing or invalid fields) far from the XAML that caused it.

When a schema-documented field is absent from the returned `FieldObjects`:

1. **Criteria-gated field** (most common — body/custom fields revealed by prerequisite values): re-run `get-default-xaml` with `--field-values <criteria>=<value> ...` (Step 4) and author against the returned XAML — its blob carries the expanded schema and the field now has a `FieldObject`. Do **not** graft the field into the previous XAML; the old blob does not know it.
2. **Query parameter**: check the schema's `queryParameters` — those never appear as `FieldObjects` and have no per-field XAML override (see Gotchas).
3. **Older CLI without `--field-values`**: the expansion is not reachable headlessly. Have a developer commit the criteria fields once in Studio's designer and copy the resulting `Configuration` + `FieldObjects`, or upgrade `uip`.

The name-encoding rules above apply to expanded fields too — reference them by the encoded name **exactly as the expanded XAML returns it**, both in `--field-values` and when binding expression values in Step 6.

### Step 7 — Validate and run

```bash
uip rpa validate --file-path "<your-workflow>.xaml" --project-dir "<PROJECT_DIR>" --output json
uip rpa run --file-path "<your-workflow>.xaml" --project-dir "<PROJECT_DIR>" --output json
```

If `HasErrors: true`, the `ErrorMessage` field carries the compile/runtime error.

## Operation output is strongly typed

The operation's result is exposed as an output FieldObject named `Jit_<operation>`, typed to a **generated record type** for that object — so downstream expressions that read its members (`record.id`, `records.First().name`) compile, and `uip rpa build` binds the consuming variable to the right type.

That typed shape is generated from the **live connection's** schema while `get-default-xaml` resolves the activity; there is no flag for it — typing is automatic when resolution succeeds against a connection. If it cannot be generated — no usable connection at resolve time, or a connector schema that won't compile — the output **degrades to `System.Object`**: the activity stays valid, but typed member access no longer compiles. Re-resolve with a valid, enabled connection; treat a `System.Object` output as the signal that typing was skipped.

## Typed Operation vs Generic HTTP

Every connector exposes a `ConnectorHttpActivity` with a typeId suffixed like `...httpRequest...` — a generic escape hatch for arbitrary HTTP calls. Prefer a **typed operation** (e.g. `send_message_to_channel_v2`) whenever one exists: it encodes the endpoint, method, and field schema for you. Only fall back to the HTTP activity when the connector lacks a modeled operation for what you need.

`get-default-xaml` for an HTTP typeId returns a correctly-typed `ConnectorHttpActivity` with a valid `Configuration`. Its fields are the **standard HTTP request fields** — `method`, `url`, `headers`, `query`, `body` (inputs), plus `out_body` / `out_headers` / `out_code` (outputs) — identical across connectors, so author the ones you need directly per Step 6 instead of reading a per-operation schema. The `ConnectionId` still scopes the call at runtime.

## Worked Example: Slack "Send Message to Channel"

End-to-end skeleton. Assumes `uip login` done and `UiPath.IntegrationService.Activities` installed.

```bash
# 1. Discover typeId
uip rpa activities find --query "Send Message to Channel" --project-dir "$P" --output json
#    → 37a305b2-89b1-315d-b73f-1778839a6c47

# 2. Find connection
uip is connections list uipath-salesforce-slack --output json
#    → c57d4fd4-9dc1-46f8-8add-a835283077fa

# 3. Get default XAML (returns Configuration blob + FieldObjects)
uip rpa activities get-default-xaml \
    --activity-type-id "37a305b2-89b1-315d-b73f-1778839a6c47" \
    --connection-id "c57d4fd4-9dc1-46f8-8add-a835283077fa" \
    --project-dir "$P" --output json

# 4. Read the schema to know which fields are required
uip is resources describe uipath-salesforce-slack send_message_to_channel_v2 --operation Create --output json
cat ~/.uipath/cache/integrationservice/uipath-salesforce-slack/_static/send_message_to_channel_v2.Create.json
#    → `send_as` is required (default "bot"); `channel` + `messageToSend` are the relevant optional fields
```

Resulting `ConnectorActivity` body (truncated — preserve the full FieldObject list from the default):

```xml
<isactr:ConnectorActivity
    Configuration="H4sIAAAAAAAACu1a624b..."
    ConnectionId="c57d4fd4-9dc1-46f8-8add-a835283077fa"
    UiPathActivityTypeId="37a305b2-89b1-315d-b73f-1778839a6c47"
    xmlns:isactr="http://schemas.uipath.com/workflow/integration-service-activities/isactr">
  <isactr:ConnectorActivity.FieldObjects>
    <isactr:FieldObject Name="channel" Type="FieldArgument">
      <isactr:FieldObject.Value>
        <InArgument x:TypeArguments="x:String">
          <CSharpValue x:TypeArguments="x:String">"C09UZSPDANP"</CSharpValue>
        </InArgument>
      </isactr:FieldObject.Value>
    </isactr:FieldObject>
    <isactr:FieldObject Name="messageToSend" Type="FieldArgument">
      <isactr:FieldObject.Value>
        <InArgument x:TypeArguments="x:String">
          <CSharpValue x:TypeArguments="x:String">"hello"</CSharpValue>
        </InArgument>
      </isactr:FieldObject.Value>
    </isactr:FieldObject>
    <isactr:FieldObject Name="send_as" Type="FieldArgument">
      <isactr:FieldObject.Value>
        <InArgument x:TypeArguments="x:String">
          <CSharpValue x:TypeArguments="x:String">"bot"</CSharpValue>
        </InArgument>
      </isactr:FieldObject.Value>
    </isactr:FieldObject>
    <!-- keep all remaining FieldObject entries from the default as bare Name/Type pairs -->
  </isactr:ConnectorActivity.FieldObjects>
</isactr:ConnectorActivity>
```

## Worked Example: criteria-gated expansion

Some "edit/update record" operations surface only their prerequisite fields by default (e.g. a record's project + type + key) and reveal the full body schema only once those criteria have values — the headless equivalent of committing those fields in the designer canvas:

```bash
# Criteria values trigger the schema expansion AND get pre-bound as literals in one call.
uip rpa activities get-default-xaml \
    --activity-type-id "<TYPE_ID>" \
    --connection-id "<LIVE_CONNECTION_ID>" \
    --field-values <criteria1>=<value> --field-values <criteria2>=<value> \
    --project-dir "$P" --output json
```

The returned `Configuration` blob now carries the expanded schema, and the previously hidden body/custom fields appear in `FieldObjects`. Bind remaining values there directly in the same call (literal) or via Step 6 (expression). Authoring one of those expanded fields against the *unexpanded* blob is the silent-drop failure in § Hidden Secondary Fields. Needs a live connection and valid criteria values — see the silent-no-op note in Step 4.

## Gotchas

1. **JIT OutArgument corruption** — When Studio's designer modifies an IS XAML, it can inject a `<OutArgument x:TypeArguments="uiascb:...<op>_Create" />` into the `Jit_<operation>` FieldObject that references a dynamically-compiled Studio-local assembly. Fresh loads (new Studio session, CI) can't resolve that type and fail to compile with `Unable to create activity builder`. **Strip the offending OutArgument back to `<isactr:FieldObject Name="Jit_<op>" Type="FieldArgument" />`** before shipping or running headlessly. Also remove the `xmlns:uiascb` namespace declaration from the root `<Activity>` element if nothing else references it. Tracked as PILOT-4812.
2. **Connector-backend errors surface at runtime, not validation** — Things like `channel_not_found`, `not_authed`, rate-limit failures etc. are returned by the connector's backend after the activity calls out. They appear in the `ErrorMessage` of an actual run (with `HasErrors: true`) or in streamed log entries from the workflow's own logging, never from `validate`. Validation can only tell you the XAML is structurally correct and the connection slot is filled — not that the target entity exists or that the bot has permission.

3. **Configuration blob's `ConnectorKey` may be a mock/template — it is not routing metadata** — Decompressing the Configuration blob can reveal `"ConnectorKey": "uipath-mock-<something>"` even when you're targeting the real production connector (e.g. `uipath-microsoft-outlook365`). The typeId encodes the *operation schema*; the `ConnectionId` attribute determines which backend actually gets called at runtime. Don't try to "correct" the blob — it's baked, and any edit invalidates it (`Configuration contains a breaking change`). A mismatch between `ConnectorKey` in the blob and the connection's connector is expected for connectors that share schemas (mocks, legacy vs. v2, etc.) and is not an error.

4. **Query parameters vs request fields** — Some operation params (e.g. Outlook's `saveAsDraft`) live in the schema's `queryParameters` block, not `requestFields`, and do **not** appear as `FieldObject` entries in the default XAML. Their defaults come from the Configuration blob and are applied server-side. There is no per-field XAML override for query parameters — if the default doesn't match your need, either use a different typeId (e.g. a v2 variant), or switch the connector. Always check the schema's `queryParameters` array for hidden-by-default toggles before running.

5. **Primary vs Secondary field designation** — Decompressing the Configuration blob exposes an `InputFields` list where each entry has a `"Design": { "Position": "Primary" | "Secondary" }`. Primary fields are what the connector considers "must-bind for the call to be meaningful" (e.g. `To`, `Subject`, `Body` for Send Email). Useful discovery hint when the schema marks most fields as `required: false` but the call actually requires several to be bound to succeed.

## Anti-Patterns

- **Do not** guess `FieldObject Name` values. Read the schema JSON from `~/.uipath/cache/integrationservice/<connector>/_static/<operation>.Create.json`.
- **Do not** hand-edit the `Configuration` blob. It's base64 + gzip of an internal serialization — any edit triggers a `breaking change` runtime rejection.
- **Do not** use `activities get-default-xaml` without `--activity-type-id` for IS activities — the generic default is empty and unusable.
- **Do not** drop FieldObjects from the default. The full list is part of the schema contract.
- **Do not** hand-add a `FieldObject` for a field absent from the returned XAML — it validates clean and is silently dropped at runtime. Re-run `get-default-xaml` with `--field-values` to expand the schema instead (§ Hidden Secondary Fields).
- **Do not** put values in the `FieldObject Value=""` attribute — use `<FieldObject.Value><InArgument><CSharpValue>` elements.

## Related References

- [connector-capabilities.md](connector-capabilities.md) — connection lifecycle commands (list, create, ping, edit).
- [xaml/workflow-guide.md § Step 1.9](xaml/workflow-guide.md) — where this flow slots into the overall XAML phase structure.
- [xaml/common-pitfalls.md § IS ConnectorActivity](xaml/common-pitfalls.md) — JIT OutArgument, `Configuration` blob opacity, schema-driven field names.

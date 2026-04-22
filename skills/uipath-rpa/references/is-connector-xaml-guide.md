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
1. **`UiPathActivityTypeId`** — the operation's type GUID (from `find-activities`).
2. **`ConnectionId`** — the IS connection's GUID (from `uip is connections list`).
3. **`Configuration`** — an opaque base64 + gzip JSON blob encoding connector/operation identity. **Never hand-edit.** Always take the value from `get-default-activity-xaml`.

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
uip rpa get-versions --package-id UiPath.IntegrationService.Activities --project-dir "<PROJECT_DIR>" --output json
uip rpa install-or-update-packages --packages '[{"id":"UiPath.IntegrationService.Activities"}]' --project-dir "<PROJECT_DIR>" --output json
```

### Step 2 — Find the operation's `activityTypeId`

```bash
uip rpa find-activities --query "<search terms>" --project-dir "<PROJECT_DIR>" --output json
```

In each result, look for:
- `activityTypeId` → populated only for IS/dynamic activities. Copy this value.
- `description` → identifies which operation (e.g. `"Send messages to public or private Slack channels."` vs `"Send a reply to a message in a Slack channel."`).

If `activityTypeId` is empty, the activity is a non-dynamic BAF/vendor activity (e.g. `UiPath.Slack.Activities.Messages.SendMessage`) — different flow, not covered here.

**`find-activities` is not exhaustive — be ready to iterate.** Results vary by connector: some expose 6+ typed operations with rich descriptions (Slack); others expose only 1-2 (Outlook). Try several query phrasings (`"send email"`, `"<connector> send"`, the literal operation name from `uip is activities list`). If no typeId surfaces:

- The operation may only be reachable via the generic `ConnectorHttpActivity` typeId (suffix `...httpRequest...`). Use it as a fallback — the field schema is still read from `uip is resources describe`, but the HTTP method/path live in the Configuration blob's `InstanceParameters`.
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
uip rpa get-default-activity-xaml \
    --activity-type-id "<TYPE_ID>" \
    --connection-id "<CONNECTION_ID>" \
    --project-dir "<PROJECT_DIR>" \
    --output json
```

The response contains the complete `ConnectorActivity` element with:
- A real `Configuration` blob for that specific connector+operation combo.
- A complete `FieldObjects` list enumerating every input/output field name.
- A real `ConnectionId` (uses the supplied one, or auto-resolves a tenant default).

**Without `--activity-type-id`**, the default comes back essentially empty (`Configuration={x:Null}`, no fields). That generic default is not runnable.

### Step 5 — Read the operation's field schema

For each field you want to bind, you need its declared `name` and `dataType`. Read the schema from Integration Service:

```bash
uip is resources describe <connector-key> <operation-name> --operation Create --output json
```

Note: it's `resources describe` (not `activities describe`). `activities` only has `list`.

The response includes a `metadataFile` path like:
```
~/.uipath/cache/integrationservice/<connector>/_static/<operation>.Create.json
```

Read that file directly for the full schema — `parameters`, `requestFields`, `responseFields`, each with `name`, `dataType`, `required`, `description`, and any enum values. **Never guess field names from memory** — the schema is the source of truth, and guessed names trigger a `Configuration contains a breaking change` runtime error.

### Step 6 — Bind values using `InArgument` + `CSharpValue`

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

The default XAML from `get-default-activity-xaml --activity-type-id` always reflects the correct encoded names — **copy the FieldObject list verbatim from there** rather than constructing names from the schema. Check the encoding only when you have to choose whether a specific field is the right one.

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

### Step 7 — Validate and run

```bash
uip rpa get-errors --file-path "<your-workflow>.xaml" --project-dir "<PROJECT_DIR>" --output json
uip rpa run-file  --file-path "<your-workflow>.xaml" --project-dir "<PROJECT_DIR>" --output json
```

If `HasErrors: true`, the `ErrorMessage` field carries the compile/runtime error.

## Typed Operation vs Generic HTTP

Every connector exposes a `ConnectorHttpActivity` with a typeId suffixed like `...httpRequest...` — a generic escape hatch for arbitrary HTTP calls. Prefer a **typed operation** (e.g. `send_message_to_channel_v2`) whenever one exists: it encodes the endpoint, method, and field schema for you. Only fall back to the HTTP activity when the connector lacks a modeled operation for what you need. For the generic one, the field names are NOT `method`/`path`/`body` — they're still connector-defined. Read the schema.

## Worked Example: Slack "Send Message to Channel"

End-to-end skeleton. Assumes `uip login` done and `UiPath.IntegrationService.Activities` installed.

```bash
# 1. Discover typeId
uip rpa find-activities --query "Send Message to Channel" --project-dir "$P" --output json
#    → 37a305b2-89b1-315d-b73f-1778839a6c47

# 2. Find connection
uip is connections list uipath-salesforce-slack --output json
#    → c57d4fd4-9dc1-46f8-8add-a835283077fa

# 3. Get default XAML (returns Configuration blob + FieldObjects)
uip rpa get-default-activity-xaml \
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

## Gotchas

1. **JIT OutArgument corruption** — When Studio's designer modifies an IS XAML, it can inject a `<OutArgument x:TypeArguments="uiascb:...<op>_Create" />` into the `Jit_<operation>` FieldObject that references a dynamically-compiled Studio-local assembly. Fresh loads (new Studio session, CI) can't resolve that type and fail to compile with `Unable to create activity builder`. **Strip the offending OutArgument back to `<isactr:FieldObject Name="Jit_<op>" Type="FieldArgument" />`** before shipping or running headlessly. Also remove the `xmlns:uiascb` namespace declaration from the root `<Activity>` element if nothing else references it. Tracked as PILOT-4812.
2. **Connector-backend errors surface at runtime, not validation** — Things like `channel_not_found`, `not_authed`, rate-limit failures etc. are returned by the connector's backend after the activity calls out. They only appear in the `ErrorMessage` / `logEntries` of an actual run, never from `get-errors`. Validation can only tell you the XAML is structurally correct and the connection slot is filled — not that the target entity exists or that the bot has permission.

3. **Configuration blob's `ConnectorKey` may be a mock/template — it is not routing metadata** — Decompressing the Configuration blob can reveal `"ConnectorKey": "uipath-mock-<something>"` even when you're targeting the real production connector (e.g. `uipath-microsoft-outlook365`). The typeId encodes the *operation schema*; the `ConnectionId` attribute determines which backend actually gets called at runtime. Don't try to "correct" the blob — it's baked, and any edit invalidates it (`Configuration contains a breaking change`). A mismatch between `ConnectorKey` in the blob and the connection's connector is expected for connectors that share schemas (mocks, legacy vs. v2, etc.) and is not an error.

4. **Query parameters vs request fields** — Some operation params (e.g. Outlook's `saveAsDraft`) live in the schema's `queryParameters` block, not `requestFields`, and do **not** appear as `FieldObject` entries in the default XAML. Their defaults come from the Configuration blob and are applied server-side. There is no per-field XAML override for query parameters — if the default doesn't match your need, either use a different typeId (e.g. a v2 variant), or switch the connector. Always check the schema's `queryParameters` array for hidden-by-default toggles before running.

5. **Primary vs Secondary field designation** — Decompressing the Configuration blob exposes an `InputFields` list where each entry has a `"Design": { "Position": "Primary" | "Secondary" }`. Primary fields are what the connector considers "must-bind for the call to be meaningful" (e.g. `To`, `Subject`, `Body` for Send Email). Useful discovery hint when the schema marks most fields as `required: false` but the call actually requires several to be bound to succeed.

## Anti-Patterns

- **Do not** guess `FieldObject Name` values. Read the schema JSON from `~/.uipath/cache/integrationservice/<connector>/_static/<operation>.Create.json`.
- **Do not** hand-edit the `Configuration` blob. It's base64 + gzip of an internal serialization — any edit triggers a `breaking change` runtime rejection.
- **Do not** use `get-default-activity-xaml` without `--activity-type-id` for IS activities — the generic default is empty and unusable.
- **Do not** drop FieldObjects from the default. The full list is part of the schema contract.
- **Do not** put values in the `FieldObject Value=""` attribute — use `<FieldObject.Value><InArgument><CSharpValue>` elements.

## Related References

- [connector-capabilities.md](connector-capabilities.md) — connection lifecycle commands (list, create, ping, edit).
- [xaml/workflow-guide.md § Step 1.9](xaml/workflow-guide.md) — where this flow slots into the overall XAML phase structure.
- [xaml/common-pitfalls.md § IS ConnectorActivity](xaml/common-pitfalls.md) — JIT OutArgument, `Configuration` blob opacity, schema-driven field names.

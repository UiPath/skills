# Connectors: choosing the operation, and the loop that fills it in

An Integration Service connector activity is `.connector(id, key, action, inputs, opts)`.
`key` and `action` identify one operation in the connector library, and everything the emitted node carries — `objectName`, `operation`, `method`, `path`, which input is a path parameter and which is a query parameter — is resolved from that library entry.
None of it is yours to spell.

## Two registries, near-identical names

| Command | What it answers |
| --- | --- |
| `uip maestro registry search` / `pull` / `prepare` | the **connector library** — Integration Service operations. Shared by flow, case and bpmn; there is no family word in the verb. |
| `uip maestro bpmn registry search` / `get` / `list` | the **Maestro extension-type catalog** — the `uipath:*` node types (`Intsvc.ActivityExecution`, `Orchestrator.StartJob`, `Maestro.ReceiveMessageEvent`, …). |

A connector key is not an extension type.
`uip maestro bpmn registry get uipath-atlassian-jira` answers

```
Extension type not found. No extension type found matching: uipath-atlassian-jira.
```

which is correct and is not evidence the connector is missing.
Ask the connector library instead.
The two caches are separate and refreshing one does nothing to the other.

## 1. Find the operation

```bash
uip maestro registry search 'jira create issue' --limit 5
```

Each hit carries what the call needs:

```jsonc
{
  "nodeType": "uipath.connector.uipath-atlassian-jira.create-issue",
  "connectorKey": "uipath-atlassian-jira",   // → key
  "label": "Create Issue",
  "markdownPath": "…/library-md/uipath-atlassian-jira/create-issue@1.0.0.md"
}
```

The **action** is `nodeType`'s last segment — `create-issue` — not the label and not the REST path.
`markdownPath` is that operation's field reference: read it rather than guessing input names.

`"total": 0` is a real miss, and means either `http()` or a connector the library does not carry (see §4).
A usage error saying no library is cached means `uip maestro registry pull` first.

## 2. Write the node

```ts
.connector('createIssue', 'uipath-atlassian-jira', 'create-issue',
  {
    'fields.project.key': lookup('uipath-atlassian-jira', 'create-issue', 'fields.project.key').by('name', 'Coder Eval'),
    'fields.issuetype.id': '10001',
    'fields.summary': '=vars.summary',
  },
  { connection: 'jira', folder: 'jiraFolder' })
```

- Inputs are keyed by the operation's **declared field names**, flat (`fields.project.key`) or as the natural nested object (`fields: { project: { key } }`); both reach the same wire slot.
- `connection` and `folder` are symbolic names resolved through `bindings.json`, never ids pasted inline. The folder binding is the connection's companion — see [Connections and bindings](bpmn-runtime.md#connectors-and-bindings).
- A field that takes an **id** takes a `lookup()`, not a pasted value. §3 resolves it.
- An `=`-expression is left alone; a plain string is checked against the field's declared type.

Authoring never waits on discovery beyond §1.
Write the node from the task's own words and let `check` tell you what is missing.

## 3. The loop: author → check → prepare → check → compile

```bash
uip maestro bpmn check <Name>.bpmn.ts --source
```

`check` reads the same library `compile` serializes against, so it names every gap with the command that closes it:

| Code | What it means |
| --- | --- |
| `CONNECTOR_INPUT` | a missing required input, an unknown key, or a value of the wrong type. The message lists every required field and its location. |
| `LOOKUP_UNRESOLVED` | a `lookup()` with no recorded value. |
| `LOOKUP_LITERAL_ID` | a pasted id in a field that resolves. Legal, but it means nothing in review and resolves to nothing — or to something else — on another connection. |
| `LOOKUP_RUNTIME_VALUE` | a runtime expression bound to an id field. An e-mail address into an account-id slot is an error, not a warning. |
| `OBJECT_UNPREPARED` | a generic operation's object has no local schema. |
| `CUSTOM_FIELDS_UNPREPARED` | an input outside the tenant-agnostic snapshot, on a connector that discovers fields per connection. |
| `BINDING_SELF_NAME` | a binding whose value is its own name. That packs into `bindings_v2.json` as a stub where a connection id belongs, and the deploy is what notices. |
| `BINDING_UNDECLARED` | a label a populated `bindings.json` does not declare. |

Each of these names one `uip maestro registry prepare`:

```bash
uip maestro registry prepare uipath-atlassian-jira --action create-issue \
    --resolve 'fields.project.key:name=Coder Eval'
```

`--object`, `--resolve` and `-f NAME=VALUE` compose in a single invocation.
It discovers the connection itself (`--connection` or `--connection-folder` picks among several), writes `bindings.json` under the names your source already uses, and writes the resolved schema and the recorded ids to `./connectors-local/`.

Then re-run `check` and compile.
`compile` and `check` both auto-detect `./connectors-local/`; `--connectors-local <dir>` names another one.

**`prepare` is a live call.** It reads through a real connection, so it needs `uip login` and a connection on the tenant. Run it when `check` asks for it, not speculatively.

## 4. When the connector is not in the library

The shipped library covers roughly 150 connectors.
A tenant can serve more, and `compile` says so:

```
connector not in library: uipath.connector.uipath-uipath-testmanager.create-v2-attachment-upload.
Connector "uipath-uipath-testmanager" is present but carries no "…".
```

Two routes, in order:

1. **`uip maestro registry prepare <key> --action <name>`** — it resolves the operation through the live connection and writes an overlay the compiler reads, which is the whole point of the overlay.
2. **A hand-filled `.activity(id, 'Intsvc.ActivityExecution', …)`**, when prepare cannot reach it. Take the identity from the registry, never from the connector's OpenAPI document:

```bash
uip is connections list <connector-key> --all-folders --output json      # the connection id
uip is activities list <connector-key> --output json                     # Name + ObjectName + IsCurated
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <ObjectName> --output json        # the node template
```

`objectName` is the **registry's** object (`UploadAttachment`, `TestSet`), and `operation` is its CRUD verb (`Create`, `List`, `Retrieve`, `Delete`).
Neither is the connector's REST slug.
A node carrying `objectName="v2::attachment::upload"` validates and then dispatches to nothing — the platform matches on the curated pair, and so do the graders that compare against a real export.

## 5. Data Fabric is not this

Data Fabric (Data Service) records and file fields are `.dataService(id, { entity, connection, folder, op, … })`, one of eight operations.
The library ships one Data Service operation, so `.connector()` cannot author the rest, and a hand-filled `.activity()` gets `objectName`, the parameter targets and the folder binding wrong in ways `validate` does not report.
See [Connections and bindings](bpmn-runtime.md#connectors-and-bindings) and `examples/ContractRegistry.bpmn.ts`.

## 6. Connector events

`.eventTrigger(id, connector, event, opts)` starts the process on a connector event; `.waitForEvent(id, connector, event, opts)` pauses one mid-flow.
Both resolve against the same library and both take the same `connection` / `folder` bindings.

- `filter` is the subscription's **scope** — the connector's own event parameters, e.g. `{ parentFolderId: '<mail folder id>' }` for Outlook `email-received`. Omitting it subscribes to everything the connection can see, which `check` reports as `EVENT_NO_SCOPE` and names the parameters the operation declares.
- `object` names what a **generic** event watches — `record-created` and its kin on Data Fabric, Salesforce, ServiceNow, Jira. Such an entry carries no default, so without it the node emits `objectName: ""`, validates, and watches nothing. `check` reports `EVENT_GENERIC_NO_OBJECT`. A curated event has its object built in and refuses one (`EVENT_OBJECT_NOT_GENERIC`).

```bash
uip is triggers objects <connector> <EVENT> --connection-id <id> --output json   # what a generic event can watch
uip is triggers describe <connector> <EVENT> <object> --connection-id <id> --output json
```

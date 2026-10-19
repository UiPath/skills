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
- The response lands in `outputVar` (default `<id>_response`) and the failure in `errorVar` (default `<id>_Error`); `outputs: { poCount: { source: '=response.length', name: 'POCount', type: 'integer' } }` adds a mapped output row per extra variable, each declared by the task like the two standard ones. These are what a decompiled import's `.connector()` calls carry, so an edit keeps the variables the process already reads.

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
connector not in library: uipath.connector.uipath-uipath-testmanager.create-test-set.
```

**`uip maestro registry prepare <key> --action <name>` resolves it through the live connection and writes an overlay the compiler reads** — one call per operation, the action named the way the connector's activity catalog spells it in kebab case (`uip is activities list <key> --output json` lists the names: `CreateTestSet` → `create-test-set`, `GetAssignedTestCasesForTestSet` → `get-assigned-test-cases-for-test-set`).
This covers a connector the Flow node catalog does not carry at all (Test Manager is one): when `registry search <key>` answers nothing, `prepare` refreshes the local catalog copy once (`uip maestro flow registry pull --force`, since a stale copy answers nothing for any connector) and, if it still serves nothing, reads Integration Service itself, the activity catalog for the identity and `is resources describe` for the path, parameters and fields, and says so:

```
  source: Integration Service activity CreateTestSet (TestSet POST) — the Flow node catalog, refreshed with `uip maestro flow registry pull --force`, serves no node for uipath-uipath-testmanager, so this operation compiles in BPMN only (a Flow step or agent tool needs the registry's node definition).
prepare-connector: uipath.connector.uipath-uipath-testmanager.create-test-set → connectors-local/ (overlay + …, 1 variant(s), 3 input field(s))
prepare-connector: next: .connector("<id>", "uipath-uipath-testmanager", "create-test-set", { ProjectId: /* string, required */, name: /* string, required */ }, { connection: "testmanager", folder: "shared" })
```

Author the call it prints; `bpmn check` then holds the inputs to the operation's real contract (a Test Manager update is a JSON-patch body, `path` and `value`, not the record's columns, and `execute-test-set` takes `testSetId`, `executionType` and `asyncMode`), and `compile` emits the task the platform matches on: `objectName` and `method` from the catalog, the path and its `target="path"` rows from the describe.
On a Flow project such an entry is refused (`CONNECTOR_NO_FLOW_DEFINITION`); if the source line says the pull failed, run `uip maestro flow registry pull --force` yourself and re-run `prepare` before trusting that the catalog lacks the connector.

An action `prepare` cannot find is refused with the activities Integration Service does list, as action ids; re-run with one of them.
It never asks Integration Service for a connector the catalog does serve: a misspelt action on Jira gets the catalog's closest action.

Only when `prepare` cannot reach the tenant at all, fall back to **a hand-filled `.activity(id, 'Intsvc.ActivityExecution', …)`** — and only on evidence gathered while the tenant was reachable: the commands below are the same tenant reads `prepare` makes, so they fail for the same reason.
Use a connection id, an activity row and a `registry get` template saved from an earlier session (or carried in the task), never a guess; with none of those, connector authoring waits for access, because an invented identity validates and dispatches to nothing.
The identity comes from the catalog, never from the connector's OpenAPI document:

```bash
uip is connections list <connector-key> --all-folders --output json      # the connection id
uip is activities list <connector-key> --output json                     # Name + ObjectName + MethodName + IsCurated
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <ObjectName> --operation <Verb> --output json   # the node template, with the describe
```

`objectName` is the **catalog's** object (`UploadAttachment`, `TestSet`) and `method` its verb (`POST`, `GETBYID`, `PATCH`, `DELETE`).
Neither is the connector's REST slug.
A node carrying `objectName="v2::attachment::upload"` validates and then dispatches to nothing — the platform matches on the curated pair, and so do the graders that compare against a real export.

## 5. Data Fabric is not this

Data Fabric (Data Service) records and file fields are `.dataService(id, { entity, connection, folder, op, … })`, one of eight operations.
The library ships one Data Service operation, so `.connector()` cannot author the rest, and a hand-filled `.activity()` gets `objectName`, the parameter targets and the folder binding wrong in ways `validate` does not report.
See [Connections and bindings](bpmn-runtime.md#connectors-and-bindings) and `examples/ContractRegistry.bpmn.ts`.

## 6. Connector events

`.eventTrigger(id, connector, event, opts)` starts the process on a connector event; `.waitForEvent(id, connector, event, opts)` pauses one mid-flow.
Both resolve against the same library and both take the same `connection` / `folder` bindings.

- `filter` is the subscription's **scope**: the connector's own event parameters, e.g. `{ parentFolderId: lookup('uipath-microsoft-outlook365', 'email-received', 'parentFolderId').by('displayName', 'Inbox') }` for Outlook `email-received`. Omitting it subscribes to everything the connection can see, which `check` reports as `EVENT_NO_SCOPE` and names the parameters the operation declares.
  Same rule as §2: a scope value that is an **id** (a mail folder, a channel, a workspace) takes a `lookup()`, never a pasted value; §3 resolves it (`--action email-received`).
- `object` names what a **generic** event watches — `record-created` and its kin on Data Fabric, Salesforce, ServiceNow, Jira. Such an entry carries no default, so without it the node emits `objectName: ""`, validates, and watches nothing. `check` reports `EVENT_GENERIC_NO_OBJECT`. A curated event has its object built in and refuses one (`EVENT_OBJECT_NOT_GENERIC`).

```bash
uip is triggers objects <connector> <EVENT> --connection-id <id> --output json   # what a generic event can watch
uip is triggers describe <connector> <EVENT> <object> --connection-id <id> --output json
```

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
<!--skill-flavor:field-reference:start-->
`markdownPath` is that operation's field reference: read it rather than guessing input names.
<!--skill-flavor:field-reference:end-->

`"total": 0` is a real miss, and means either `http()` or a connector the catalog searched does not carry (see §4).
A connector-mode `http()` calls the vendor's own method for the user's ask, relative to the connection's base URL, such as Slack's `/emoji.list` for "list the custom emoji". Never an Integration Service resource name or `Path` from `uip is resources list` or `describe` (those are what `.connector()` and `.activity()` take), and never an `admin.*` method (Enterprise Grid org admin, such as `admin.emoji.list`) unless the ask is org administration: [HTTP and Orchestrator work](bpmn-runtime.md#http-and-orchestrator-work).
<!--skill-flavor:library-pull:start-->
With no library pulled the search answers from the tenant's live catalog through `uip` (`"source": "tenant"`), and its rows carry no `markdownPath`: read the page with `uip maestro registry describe <nodeType>`, which fetches it.
A failed search gives `uip`'s reason; fix what it names: log in again for a session problem, or run the upgrade it names for an old SDK.
<!--skill-flavor:library-pull:end-->

## 2. Write the node

```ts
.connector('createIssue', 'uipath-atlassian-jira', 'create-issue',
  {
    'fields.project.key': lookup('uipath-atlassian-jira', 'create-issue', 'fields.project.key').by('name', 'Coder Eval'),
    'fields.issuetype.id': '10001',
    'fields.summary': '=js:vars.summary',
  },
  { connection: 'jira', folder: 'jiraFolder' })
```

- Inputs are keyed by the operation's **declared field names**, flat (`fields.project.key`) or as the natural nested object (`fields: { project: { key } }`); both reach the same wire slot.
- `connection` and `folder` are symbolic names resolved through `bindings.json`, never ids pasted inline. The folder binding is the connection's companion — see [Connections and bindings](bpmn-runtime.md#connectors-and-bindings).
- A field that takes an **id** takes a `lookup()`, not a pasted value. §3 resolves it.
  `lookup` imports from `@uipath/maestro-builder-sdk`, not `/bpmn` (`TS2305`). In the string form above write `.by('<Field>', value)`; `.byFullName()` exists only on a prepared module.
- OneDrive and SharePoint file and folder fields (`referenceID`, `parentFolderId`) are picker lookups: `lookup('uipath-microsoft-onedrive', '<ACTION>', 'referenceID').by('FullName', '<ITEM_PATH>')`, then `uip maestro registry prepare uipath-microsoft-onedrive --action <ACTION> --resolve referenceID:FullName=<ITEM_PATH>`. Never paste an item id.
- Outlook `send-email`: `message.toRecipients`, `ccRecipients` and `bccRecipients` are ONE comma-separated string, never an array (`CONNECTOR_INPUT … expected string, got object`). Always set `saveAsDraft`: `false` to send, `true` to draft. The definition's default (`true`) is not compiled into the task, and the response (`status: "success"`) does not say which happened.
- An `=`-expression is left alone; a plain string is checked against the field's declared type.
- The response lands in `outputVar` (default `<id>_response`) and the failure in `errorVar` (default `<id>_Error`); `outputs: { poCount: { source: '=response.Count', name: 'POCount', type: 'integer' } }` adds a mapped output row per extra variable, each declared by the task like the two standard ones. These are what a decompiled import's `.connector()` calls carry, so an edit keeps the variables the process already reads. `.Count` counts an array, and on an object silently returns its field count: a list operation's runtime response is the bare array, even where `uip is resources run` prints `{ items, Pagination }`.

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
| `BINDING_UNDECLARED` | a label a populated `bindings.json` does not declare (reported by `compile`, and by `check` given `--bindings`). |
| `CONNECTION_BINDING_NOT_GUID` (warning) | a connection binding whose default is not a connection id. `check` and `compile` accept a symbolic label offline; `refresh` refuses it (`Connection binding "<id>" default must be a GUID.`). `prepare` writes the real id; never invent one. |

When one of these comes from a missing schema, lookup value or binding, its message names the `uip maestro registry prepare` that closes it.
An unknown key, a wrong value type (`CONNECTOR_INPUT`) or a runtime value in an id field (`LOOKUP_RUNTIME_VALUE`) is a mistake in your source: fix it there, since `prepare` doesn't touch the source.
When a step reads a record by a key the process is given and the operation also needs lookups nobody supplies (Jira `get-issue`'s `project`, `issuetype`), never derive them from the key, and never pin one value while a generic Retrieve (`object:`) whose required inputs are all plain, none a lookup, can read the record instead.
List the connector's Retrieves with `uip maestro registry search retrieve --connector <CONNECTOR_KEY> --limit 50 --output json` (re-run with `--limit <TOTAL>` when `Data.Total` is higher) and read each row's field reference. With none, each lookup is an open question: ask the user, or, when the request says nobody will answer, pick one of the values the lookup lists and name it on the final report's `Assumed:` line.

```bash
uip maestro registry prepare uipath-atlassian-jira --action create-issue \
    --resolve 'fields.project.key:name=Coder Eval'
```

`--object`, `--resolve` and `-f NAME=VALUE` compose in a single invocation.
It discovers the connection itself (`--connection` or `--connection-folder` picks among several), writes `./.flow-sdk/bindings.json` under the names your source already uses, and writes the resolved schema and the recorded ids to `./.flow-sdk/connectors-local/` (its `--help` names `./bindings.json` and `./connectors-local/`, but it writes under `.flow-sdk/`).

When `--resolve` reports no matching record, the value is absent on that connection only. Re-run the same `prepare` with `--connection-id <ID>` (or `--connection-folder`) for each other Enabled connection its error lists, and stop only after every one misses. `prepare` scans every page. Never decide a value is absent from `uip is resources run list`: it returns one page, and `Data.Pagination.HasMore: true` means more records exist.

Then re-run `check` and compile from the directory you ran `prepare` in. `compile` reads `.flow-sdk/bindings.json` and both read `.flow-sdk/connectors-local/` under the current directory, not beside the source: from any other directory, `compile` writes a stand-in connection id, not the one `prepare` bound. When you must run from elsewhere, pass the paths explicitly:

```bash
uip maestro bpmn compile <SOURCE> -o <OUTPUT> --bindings <PREPARE_DIR>/.flow-sdk/bindings.json --connectors-local <PREPARE_DIR>/.flow-sdk/connectors-local
```

Add `--resources <PREPARE_DIR>/.flow-sdk/resources.json` only when that file exists: `prepare --entity` or `--kind … --name …` writes it, a connector `prepare` does not, and `compile` refuses a missing one (`RESOURCE_LEDGER_MISSING`).

`check` reads `.flow-sdk/bindings.json` only when given `--bindings .flow-sdk/bindings.json`; without it, its `CONNECTION_BINDING_NOT_GUID` warning stays.

**Bind only an Enabled connection.** List the candidates and check the one you pick:

```bash
uip is connections list <CONNECTOR_KEY> --all-folders --output json   # Id, Name, State, Owner, Folder, FolderKey
uip is connections ping <CONNECTION_ID> --output json                 # Data.Status must be "Enabled"
```

- With several Enabled matches, `prepare` refuses and lists them; re-run it with `--connection-id <CONNECTION_ID>` (or `--connection <CONNECTION_NAME>`, `--connection-folder <FOLDER>`). It never picks the default connection for you. Ask the user which one when the request does not say; when the request says nobody will answer, bind the Enabled match in the folder the process runs in, else the one with `IsDefault: Yes`, else the first one listed, skipping every connection the next bullet rules out (including the requester's own personal one), and name it on the final report's `Assumed:` line.
- A connection is a sender's identity. Never bind, or offer on an outline, another person's personal connection (its folder is `<USER_NAME>'s workspace`).
  A connection in a shared folder belongs to the team whoever its `Owner` is, even when its Name is an email: it is a normal candidate, chosen by the bullet above. "Use whatever exists" means nobody will answer which one.
  Never bind any connection as a stand-in for a mailbox, channel or account the request names (`ar@…`) that has no connection.
  Bind the requester's own personal connection only when they say to, or pick *Build it* on a draft gate that named it. When no connection is left to bind, leave the step unbound (§7; for an `http()`, the next bullet) and name the missing connection on `Needs:`.
- Bind a connection to an `http()` only when `uip is connections base-url <CONNECTION_ID> --output json` is the host of the API the request targets. A connection on another vendor's base URL (a generic HTTP connection on `https://api.spotify.com/v1` for a Google call) is the wrong connection even when it is the only one or the user names it: say its base URL cannot reach that API, and write the manual `.http()` with the absolute URL instead, under its SDK note (`RULE:bpmn.http.manual` in [HTTP and Orchestrator work](bpmn-runtime.md#http-and-orchestrator-work)). That call carries no credential, so an API that needs one rejects it (Slack answers HTTP 200 with `ok: false`): name the missing `<API_HOST>` connection on `Needs:` and say the step must be rebuilt as the connected `.http()` once it exists.
- `prepare` refuses a connection that is not Enabled; `check`, `compile` and `refresh` do not. `validate` reports it as `MISSING_BINDING`, and `debug` faults with `[102002] Integration Services operation failed`. Never bind one: ask the user to re-authenticate it.
- `prepare`'s JSON `Message` keeps only the last line of its explanation; read stderr for the full refusal.
- Report the bound connection by Name and Folder, from the `connections list` row whose `Id` is `prepare`'s `Data.ConnectionId` (`Owner` is a user id, not a name).
- `uip maestro bpmn validate` checks connection bindings against the tenant: outside Studio Web, pass the same `--profile` as `prepare`, or a correct binding reports `MISSING_BINDING`.

<!--skill-flavor:prepare-live:start-->
**`prepare` is a live call.** It reads through a real connection, so it needs `uip login` and a connection on the tenant. Run it when `check` asks for it, not speculatively.
<!--skill-flavor:prepare-live:end-->

These codes are mistakes in your own source, and `prepare` does not close them; fix the source and re-run `check`:

| Code | What it means | Fix |
| --- | --- | --- |
| `INTSVC_CONNECTION_NOT_BINDING` | a connector node's connection that is not `=bindings.<id>`. | Write the value as `=bindings.<id>`; a hand-filled wait reads `connectionId: '=bindings.<id>'`. |
| `INTSVC_CONNECTION_BINDING_MISSING` | a `=bindings.<id>` with no root binding of resource `Connection` and property `ConnectionId`, spelled exactly. | Declare that root binding. |
| `INTSVC_EVENT_NO_CONNECTION` | a wait or trigger with no connection: the runtime faults on it. | Give the node a `connection:`. |
| `INTSVC_CONNECTION_MISSING` | an activity with no connection (error on a V1 activity, warning otherwise). | Give the node a `connection:`. |
| `INTSVC_CONNECTION_FOLDER_MISMATCH` | an activity whose connection and folder bindings name different connection resources: `refresh` or `validate` refuses it. | Point the connection and folder at the same connection's bindings. |
| `INTSVC_CONNECTION_RESOURCE_CONFLICT` | one connection resource used by nodes with different connectors or connections. | Give each connector or connection its own binding. |
| `INTSVC_CONNECTOR_KEY_MISSING` | a node bound to a connection with no `connectorKey` (or an HTTP request with no `body.targetConnector`): `refresh` refuses it before it looks at the binding. | Set the node's `connectorKey`; on an HTTP request, set `body.targetConnector` to the connection's connector key. |

## 4. When the connector is not in the library

With no library pulled, `check` and `compile` fetch an operation through `uip` themselves, from the Flow node catalog, so a connector the tenant serves there needs nothing more; with a pulled library they refuse one it lacks, and `uip maestro registry pull` refreshes it.
What they cannot fetch they refuse, and the refusal's last sentence says why:

```
connector not in library: uipath.connector.uipath-uipath-testmanager.create-test-set. … The tenant was asked through uip (`uip maestro flow registry get`) and does not serve it.
```

Any other note gives `uip`'s own reason; fix what it names (log in again only when the session is the problem), then re-run `check`.
"does not serve it" is either a misspelt action or a connector the Flow node catalog lacks, which `prepare` below covers.

**`uip maestro registry prepare <key> --action <name>` resolves it through the live connection and writes an overlay the compiler reads** — one call per operation, the action named the way the connector's activity catalog spells it in kebab case (`uip is activities list <key> --output json` lists the names: `CreateTestSet` → `create-test-set`, `GetAssignedTestCasesForTestSet` → `get-assigned-test-cases-for-test-set`).
This covers a connector the Flow node catalog does not carry at all (Test Manager is one): when `registry search <key>` answers nothing, `prepare` refreshes the local catalog copy once (`uip maestro flow registry pull --force`, since a stale copy answers nothing for any connector) and, if it still serves nothing, reads Integration Service itself, the activity catalog for the identity and `is resources describe` for the path, parameters and fields, and says so:

```
  source: Integration Service activity CreateTestSet (TestSet POST) — the Flow node catalog, refreshed with `uip maestro flow registry pull --force`, serves no node for uipath-uipath-testmanager, so this operation compiles in BPMN only (a Flow step or agent tool needs the registry's node definition).
prepare-connector: uipath.connector.uipath-uipath-testmanager.create-test-set → .flow-sdk/connectors-local/ (overlay + …, 1 variant(s), 3 input field(s))
prepare-connector: next: .connector("<id>", "uipath-uipath-testmanager", "create-test-set", { ProjectId: /* string, required */, name: /* string, required */ }, { connection: "testmanager", folder: "shared" })
```

Author the call it prints; `bpmn check` then holds the inputs to the operation's real contract (a Test Manager update is a JSON-patch body, `path` and `value`, not the record's columns, and `execute-test-set` takes `testSetId`, `executionType` and `asyncMode`), and `compile` emits the task the platform matches on: `objectName` and `method` from the catalog, and the path from the describe, with its parameters in the `pathParameters` row.
On a Flow project such an entry is refused (`CONNECTOR_NO_FLOW_DEFINITION`); if the source line says the pull failed, run `uip maestro flow registry pull --force` yourself and re-run `prepare` before trusting that the catalog lacks the connector.

An action `prepare` cannot find is refused with the activities Integration Service does list, as action ids; re-run with one of them.
It never asks Integration Service for a connector the catalog does serve: a misspelt action on Jira gets the catalog's closest action.

Only when `prepare` cannot reach the tenant at all, fall back to **a hand-filled `.activity(id, 'Intsvc.ActivityExecution', …)`** — and only on evidence gathered while the tenant was reachable: the commands below are the same tenant reads `prepare` makes, so they fail for the same reason.
Use a connection id, an activity row and a `registry get` template saved from an earlier session (or carried in the task), never a guess; with none of those, connector authoring waits for access, because an invented identity validates and dispatches to nothing.
A draft that cannot wait for access takes the form in §7.
The identity comes from the catalog, never from the connector's OpenAPI document:

```bash
uip is connections list <CONNECTOR_KEY> --all-folders --output json      # the connection id
uip is activities list <CONNECTOR_KEY> --output json                     # Name + ObjectName + MethodName + IsCurated
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <ObjectName> --operation <Verb> \
    --input-details '{}' --output json                                     # the V2 element (Data.V2.ElementXml), with the describe
```

`objectName` is the **catalog's** object (`UploadAttachment`, `TestSet`) and `method` its verb (`POST`, `GETBYID`, `PATCH`, `DELETE`).
Neither is the connector's REST slug.
A node carrying `objectName="v2::attachment::upload"` validates and then dispatches to nothing — the platform matches on the curated pair, and so do the graders that compare against a real export.
`check` holds a hand-filled task to the catalog (`INTSVC_*`), which `validate` does not; fix what it reports.
On this `.activity()`, `path` is the operation's route under the connector, copied from `Operation.Path` of `uip is resources describe <CONNECTOR_KEY> <OBJECT_NAME> --operation <VERB> --output json`, saved or run now (`/curated_create_issue`, `/curated_get_issue/{issueId}`). It differs per operation and is not always `/<objectName>` (`issue_properties` is `/issue/{issueIdOrKey}/properties`), so never derive it.
Never the provider's REST route (`/rest/api/2/issue`): `validate` accepts it, and the debug run faults at the node (observed on Jira Create Issue: `102002 Integration Services operation failed`, provider 401).
Copy the `<uipath:context>` rows of `Data.V2.ElementXml` into the `.activity()` context, `activityConfigurationVersion: 'v2'` included.
Without `--input-details` the command returns only the extension type's V1 template (`activityConfigurationVersion` defaults to `v1` there), whose context a V2 task does not carry.
`--input-details` takes the node's values as JSON, `'{}'` when you have none yet; `Data.V2.MissingRequired` lists the required inputs still unset.
A `{param}` in the path goes in `inputs: { pathParameters: { <param>: … } }` and a query parameter in `inputs: { queryParameters: { … } }`, the element's two json rows; a bare `inputs: { <param> }` lands in the body (see [the parameter rows](bpmn-runtime.md#connectors-and-bindings)).
For a generic record verb (`Create Record`, `Delete Record`), the catalog row's `N/A` is not the answer: `objectName` is the object you pick from `uip is resources list <key> --connection-id <id> --output json`, `method` is the catalog's **Integration Service method** for that verb (`GETBYID` for a single record (Retrieve), `GET` for a list, `POST` to create, `PATCH`/`PUT` to update, `DELETE`), not the HTTP verb (both retrieval and listing travel as HTTP GET; the platform matches on `GETBYID` vs `GET`), and `path` comes from `uip is resources describe <key> <object> --operation <Verb> --connection-id <id> --output json`.

## 5. Data Fabric is not this

Data Fabric (Data Service) records and file fields are `.dataService(id, { entity, connection, folder, op, … })`, one of eight operations.
A folder-scoped entity is `entity: { name, folder: '<folder path>' }`, which writes the connector's `_V3` operation once `check`'s `prepare` has recorded its keys: `create`, `update`, `get` and `query` as the V2 task Studio Web saves, `delete` as a V1 task; see [the folder-entity rule](bpmn-runtime.md#connectors-and-bindings) for these and the other V1 cases.
The library ships one Data Service operation, so `.connector()` cannot author the rest, and a hand-filled `.activity()` gets `objectName`, the parameter targets and the folder binding wrong in ways `validate` does not report.
See [Connections and bindings](bpmn-runtime.md#connectors-and-bindings) and `examples/ContractRegistry.bpmn.ts`.

## 6. Connector events

`.eventTrigger(id, connector, event, opts)` starts the process on a connector event; `.waitForEvent(id, connector, event, opts)` pauses one mid-flow.
Both resolve against the same library and both take the same `connection` / `folder` bindings.

- `filter` is the subscription's **scope**: the connector's own event parameters, e.g. `{ parentFolderId: lookup('uipath-microsoft-outlook365', 'email-received', 'parentFolderId').by('displayName', 'Inbox') }` for Outlook `email-received`. Omitting it subscribes to everything the connection can see, which `check` reports as `EVENT_NO_SCOPE` and names the parameters the operation declares.
  Same rule as §2: a scope value that is an **id** (a mail folder, a channel, a workspace) takes a `lookup()`, never a pasted value; §3 resolves it (`--action email-received`).
- `object` names what a **generic** event watches — `record-created` and its kin on Data Fabric, Salesforce, ServiceNow, Jira. Such an entry carries no default, so without it the node emits `objectName: ""`, validates, and watches nothing. `check` reports `EVENT_GENERIC_NO_OBJECT`. A curated event has its object built in and refuses one (`EVENT_OBJECT_NOT_GENERIC`).
- A folder entity on a Data Fabric entity trigger (`record-created-preview-`, `record-updated-preview-`; object `EntityTriggers_V3`) is `entity: { name, folder: '<folder path>' }`, never `filter: { entityScope, folderEntityName }`: a literal filter watches the records but writes no picker, so `refresh` declares no entity and a deploy cannot re-point it.
<!--skill-flavor:sdk-event-entity:start-->
  Needs `@uipath/maestro-builder-sdk` 6.123.0 or later; an older SDK reports `TS2353` on `entity`, so upgrade the copy `uip` resolves, local copy first, then global. From the directory you run `uip` in (the workspace root), run `node -e "console.log(require.resolve('@uipath/maestro-builder-sdk/package.json',{paths:[process.cwd()]}))"`. When it prints a path, that `node_modules` (possibly in a parent directory) owns the copy: run `npm install --save-dev @uipath/maestro-builder-sdk@latest` in the directory holding it when a `package.json` sits beside it; otherwise tell the user the path, and never create a `package.json`. On error, run `npm install -g @uipath/maestro-builder-sdk@latest`. Then run `check` again. Never fall back to the literal `filter`.
<!--skill-flavor:sdk-event-entity:end-->
  `check` reports `RESOURCE_UNRESOLVED` and prints the `uip maestro registry prepare --entity <name> --folder-path <path>` that records the keys, as for `.dataService()`; the trigger and a task on that entity share one binding pair. Run `uip maestro bpmn refresh` after `compile`.

```bash
uip is triggers objects <connector> <EVENT> --connection-id <id> --output json   # what a generic event can watch
uip is triggers describe <connector> <EVENT> <object> --connection-id <id> --output json
```

- The payload lands in `outputVar` (default `<id>_result`) and a failure in `<id>_Error`; the node declares both, so `=js:vars.<id>_result.subject` reads a payload field downstream.
  `outputs` maps payload fields onto variables of their own, and its sources read the payload under `response`: `outputs: { subject: '=response.subject' }`.
  A bare `'=subject'` reads nothing: the payload is not at the top level.
- `folderPath` is deprecated and ignored: the task names its folder by the `folder` binding alone, so drop it.
- Test Manager (`uipath-uipath-testmanager`) has no event a process can use: the library has none, and `uip is triggers` uppercases its operation names (`Created` → 404 "Event operation 'CREATED' was not found"). Do not author `.eventTrigger()` or `.waitForEvent()` for it; tell the user, and poll with an activity instead.

## 7. Draft with an unresolved connector

A source-only draft (offline, no connection on the tenant, or a task that forbids real ids) is missing the connection, and sometimes the operation.
Write the step so that `check` passes and the CLI, not prose, says what is missing:

- **The operation's metadata is local**: §1 finds it in the library (a local cache, so this works offline), and `check` names no `uip maestro registry prepare` for it (`OBJECT_UNPREPARED`, `CUSTOM_FIELDS_UNPREPARED`, or a `CONNECTOR_INPUT` for a field only the connection discovers), since only a live `prepare` clears those.
  Write the `.connector()` call of §2 with symbolic `connection` and `folder` names and no `bindings.json`.
  Leave no `lookup()` in it, because `compile` refuses one until `prepare` records it (`LOOKUP_UNRESOLVED`); a lookup field takes a runtime `=js:vars.<id>` or a fixed-vocabulary literal (`send_as: 'bot'`), which `check` only warns about (`LOOKUP_RUNTIME_VALUE`, `LOOKUP_LITERAL_ID`).
  `check`, `compile` and `format` pass and emit a real `Intsvc.ActivityExecution` task reading `=bindings.<name>`.
  `refresh` then refuses (`Connection binding "<name>" default must be a GUID.`) and `validate` reports `MISSING_BINDING`: that is the draft's blocker, so stop there, and do not edit a binding or a package file to get past it.
- **Otherwise, with no tenant for `prepare` to reach** (the operation is not in the library, or `check` asks for a `prepare`): write the step as a bare `.task(id, { name })` whose name says what it does and carries the connector key and the operation, such as `'Send Slack digest (uipath-salesforce-slack / send-message-to-channel, unresolved)'`.
  The name must contain the connector key exactly as the library spells it (`uipath-salesforce-slack`, not "Slack" or "Integration Service") and a verb for what the step does:

  ```ts
  .task('sendDigest', { name: 'Send digest via uipath-salesforce-slack' })
  ```

  The whole loop passes; the node is a placeholder, and the notes say so.
- **Never a placeholder `.activity(id, 'Intsvc.ActivityExecution', …)`.**
  `check` refuses empty context (`EMPTY_REQUIRED_FIELD`) and sentinel values (`INTSVC_METHOD_UNKNOWN`, `INTSVC_OPERATION_NOT_IDENTIFIER`), and a file compiled past it is one `validate` rejects.
  §4's hand-filled form needs evidence read from a reachable tenant.

Then leave a notes file (`README.md` beside the source) that names each CLI-owned blocker in these exact words, says what it is, and names the step that resolves it:

| Blocker | What it is | Resolved by |
| --- | --- | --- |
| connection binding | the tenant connection, and its folder companion, that `=bindings.<name>` reads; the draft carries only the symbolic name | `uip maestro registry prepare <key> --action <action>` against a live connection writes `./.flow-sdk/bindings.json` |
| dynamic schemas | the connection-specific input and output schemas, custom fields, objects and lookup ids | the same `prepare`, with `--resolve` / `--object`, which writes `./.flow-sdk/connectors-local/` |
| connector operation metadata (bare `.task()` only) | `objectName`, `method`, path and the generated outputs (`<id>_response`, `<id>_Error`) | `prepare`, then replace the `.task()` with the `.connector()` call it prints |
| `bindings_v2.json` | the packaged binding resources | `uip maestro bpmn refresh <project>` after `compile`, once the connection binding resolves |
<!--skill-flavor:package-metadata-row:start-->
| package metadata | `entry-points.json`, `operate.json`, `package-descriptor.json` | the same `refresh`; `uip solution resources refresh --solution-folder <solution-dir>` for the solution |
<!--skill-flavor:package-metadata-row:end-->

Name them as written, not paraphrased ("the connection", "the schema"), because the user acts on the artifact each one names.
Name no private value: no connection id, folder key, tenant URL, resource key or schema copied from a tenant.

# Connectors: choosing the operation, and the loop that fills it in

An Integration Service connector activity is `.connector(id, key, action, inputs, opts)`. `key` and `action` identify a connector-library operation; the library resolves `objectName`, `operation`, `method`, `path`, and path/query placement. Do not spell those yourself.

## Two registries, near-identical names

| Command | Answers |
| --- | --- |
| `uip maestro registry search` / `pull` / `prepare` | Connector-library operations for flow, case, and bpmn; no family word in the verb. |
| `uip maestro bpmn registry search` / `get` / `list` | Maestro extension-type catalog: `uipath:*` nodes such as `Intsvc.ActivityExecution`, `Orchestrator.StartJob`, and `Maestro.ReceiveMessageEvent`. |

A connector key is not an extension type. `uip maestro bpmn registry get uipath-atlassian-jira` returns `Extension type not found. No extension type found matching: uipath-atlassian-jira.`, which is correct and is not evidence the connector is missing; ask the connector library instead. Caches are separate; refreshing one does not refresh the other.

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

The **action** is the final `nodeType` segment (`create-issue`), not the label or REST path.
<!--skill-flavor:field-reference:start-->
`markdownPath` is the field reference; read it instead of guessing input names.
<!--skill-flavor:field-reference:end-->

`"total": 0` is a real miss: the step is either `http()` or a connector the searched catalog does not carry (§4). Connector-mode `http()` calls the vendor method relative to the connection base URL, such as Slack `/emoji.list` for custom emoji; not an Integration Service resource name or `Path` from `uip is resources list`/`describe` (those belong to `.connector()` and `.activity()`), and not an `admin.*` method (Enterprise Grid org admin, such as `admin.emoji.list`) unless the request is org administration. See [HTTP and Orchestrator work](bpmn-runtime.md#http-and-orchestrator-work).
<!--skill-flavor:library-pull:start-->
Without a pulled library, search uses the tenant catalog through `uip` (`"source": "tenant"`) and omits `markdownPath`; run `uip maestro registry describe <nodeType>` to fetch the page. On failure, fix `uip`'s stated reason: log in again for a session problem or run the named upgrade for an old SDK.
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

Use declared names, flat (`fields.project.key`) or naturally nested (`fields: { project: { key } }`); both target the same wire slot. `connection` and `folder` are symbolic `bindings.json` names, never inline ids; the folder is the connection's companion. See [Connections and bindings](bpmn-runtime.md#connectors-and-bindings).

- Id fields take `lookup()`, not pasted values; §3 resolves them. Import `lookup` from `@uipath/maestro-builder-sdk`, not `/bpmn` (`TS2305`). In string form use `.by('<Field>', value)`; `.byFullName()` exists only on a prepared module.
- OneDrive/SharePoint `referenceID` and `parentFolderId` are picker lookups: `lookup('uipath-microsoft-onedrive', '<ACTION>', 'referenceID').by('FullName', '<ITEM_PATH>')`; then run `uip maestro registry prepare uipath-microsoft-onedrive --action <ACTION> --resolve referenceID:FullName=<ITEM_PATH>`. Never paste an item id.
- Outlook `send-email` requires one comma-separated string, never an array, for `message.toRecipients`, `ccRecipients`, and `bccRecipients` (`CONNECTOR_INPUT … expected string, got object`). Always set `saveAsDraft`: `false` to send or `true` to draft; definition default (`true`) is not compiled, and `status: "success"` does not identify which occurred.
- An `=`-expression is left alone; a plain string is checked against the field's declared type.
- Response/failure go to `outputVar` (default `<id>_response`) and `errorVar` (default `<id>_Error`). `outputs: { poCount: { source: '=response.Count', name: 'POCount', type: 'integer' } }` adds one mapped output row per extra variable, each declared like the two standard rows; preserve variables read by a decompiled import. `.Count` counts arrays but silently counts object fields; list runtime responses are bare arrays even if `uip is resources run` prints `{ items, Pagination }`.

Authoring never waits on discovery beyond §1. Write the node from the task's own words and let `check` tell you what is missing.

## 3. The loop: author → check → prepare → check → compile

```bash
uip maestro bpmn check <Name>.bpmn.ts --source
```

`check` reads the library used by `compile` and reports:

| Code | Meaning |
| --- | --- |
| `CONNECTOR_INPUT` | Missing required input, unknown key, or wrong type; the message lists required fields and locations. |
| `LOOKUP_UNRESOLVED` | `lookup()` has no recorded value. |
| `LOOKUP_LITERAL_ID` | Pasted id in a resolving field; legal but connection-dependent and may resolve to nothing or another item. |
| `LOOKUP_RUNTIME_VALUE` | Runtime expression in an id field; an e-mail address in an account-id slot is an error. |
| `OBJECT_UNPREPARED` | Generic operation object lacks a local schema. |
| `CUSTOM_FIELDS_UNPREPARED` | Connection-specific input outside the tenant-agnostic snapshot. |
| `BINDING_SELF_NAME` | Binding value equals its name; `bindings_v2.json` gets a stub and deployment detects it. |
| `BINDING_UNDECLARED` | Populated `bindings.json` lacks the label; `compile` and `check --bindings` report it. |
| `CONNECTION_BINDING_NOT_GUID` (warning) | Default is not a connection id. `check`/`compile` accept a symbolic label offline; `refresh` refuses `Connection binding "<id>" default must be a GUID.` `prepare` writes the real id; never invent one. |

For missing schema, lookup, or binding, run the named `uip maestro registry prepare`; fix unknown keys, wrong types, and `LOOKUP_RUNTIME_VALUE` in source; `prepare` does not. If a record key is supplied but the operation also requires unsupplied lookups (for example Jira `get-issue` `project` and `issuetype`), never derive them from the key, and never pin one value while a generic Retrieve (`object:`) whose required inputs are all plain, none a lookup, can read the record instead: use that Retrieve. List Retrieves with:

```bash
uip maestro registry search retrieve --connector <CONNECTOR_KEY> --limit 50 --output json
```

Read each row's field reference; rerun with `--limit <TOTAL>` when `Data.Total` is higher. If none exists, ask the user, or, when the request says nobody will answer, choose a listed value and put it on the final report's `Assumed:` line.

`--object`, `--resolve`, and `-f NAME=VALUE` compose in one invocation, for example:

```bash
uip maestro registry prepare uipath-atlassian-jira --action create-issue \
    --resolve 'fields.project.key:name=Coder Eval'
```

`prepare` discovers the connection (`--connection` or `--connection-folder` selects among several), writes `./.flow-sdk/bindings.json` using source names, and writes schemas/recorded ids under `./.flow-sdk/connectors-local/` despite help naming `./bindings.json` and `./connectors-local/`.

When `--resolve` reports no matching record, the value is absent on that connection only. Re-run the same `prepare` with `--connection-id <ID>` (or `--connection-folder`) for each other Enabled connection (its error lists them; else `uip is connections list`); treat the value as absent (ask the user, or `Assumed:` as above) only after every one misses. `prepare` scans every page. Never decide a value is absent from `uip is resources run list`: it returns one page, and `Data.Pagination.HasMore: true` means more records exist.

Re-run `check` and compile from the directory you ran `prepare` in. `compile` reads `.flow-sdk/bindings.json` and both read `.flow-sdk/connectors-local/`, relative to the current directory, not beside the source; elsewhere `compile` writes a stand-in connection id. When you must run from elsewhere, pass the paths explicitly:

```bash
uip maestro bpmn compile <SOURCE> -o <OUTPUT> --bindings <PREPARE_DIR>/.flow-sdk/bindings.json --connectors-local <PREPARE_DIR>/.flow-sdk/connectors-local
```

Add `--resources <PREPARE_DIR>/.flow-sdk/resources.json` only when it exists: `prepare --entity` or `--kind … --name …` writes it; connector `prepare` does not; a missing file causes `RESOURCE_LEDGER_MISSING`.

`check` reads `.flow-sdk/bindings.json` only when given `--bindings .flow-sdk/bindings.json`; without it, its `CONNECTION_BINDING_NOT_GUID` warning stays.

**Bind only an Enabled connection.** List the candidates and check the one you pick:

```bash
uip is connections list <CONNECTOR_KEY> --all-folders --output json   # Id, Name, State, Owner, Folder, FolderKey
uip is connections ping <CONNECTION_ID> --output json                 # Data.Status must be "Enabled"
```

If several Enabled matches exist, `prepare` refuses and lists them; rerun with `--connection-id <CONNECTION_ID>` (or `--connection <CONNECTION_NAME>`, `--connection-folder <FOLDER>`). It never chooses the default. Ask the user which one when the request does not say; when the request says nobody will answer, bind the Enabled match in the process folder, else `IsDefault: Yes`, else first listed, skipping every connection the next paragraph rules out (including the requester's own personal one), and report it on `Assumed:`.

A connection is a sender's identity. Never bind or offer another person's personal connection (folder `<USER_NAME>'s workspace`). A shared-folder connection belongs to the team whoever its `Owner` is, even when its Name is an email: a normal candidate, chosen by the preceding rule. "Use whatever exists" means nobody will answer which one. Never bind any connection as a stand-in for a mailbox, channel or account the request names (`ar@…`) that has no connection. Bind the requester's personal connection only when explicitly requested or *Build it* is selected on a draft gate naming it. If none remains, leave the step unbound (§7; for `http()`, use the next rule) and put the missing connection on `Needs:`.

Bind `http()` only when `uip is connections base-url <CONNECTION_ID> --output json` is the target API host. A different host is wrong even if sole or named; state that and write manual `.http()` with the absolute URL under `RULE:bpmn.http.manual` in [HTTP and Orchestrator work](bpmn-runtime.md#http-and-orchestrator-work). It carries no credential; credentialed APIs reject it (Slack can return HTTP 200 with `ok: false`). Put missing `<API_HOST>` connection on `Needs:` and say to rebuild as connected `.http()`.

`prepare` refuses non-Enabled connections; `check`, `compile`, and `refresh` do not. `validate` reports `MISSING_BINDING`; `debug` faults `[102002] Integration Services operation failed`. Never bind one; ask the user to re-authenticate. `prepare` JSON `Message` retains only the last explanation line; read stderr for the full refusal. Report Name and Folder from the `connections list` row whose `Id` equals `prepare` `Data.ConnectionId`; `Owner` is a user id. `uip maestro bpmn validate` checks tenant bindings; outside Studio Web pass the same `--profile` as `prepare`, or a correct binding reports `MISSING_BINDING`.

<!--skill-flavor:prepare-live:start-->
**`prepare` is a live call.** It reads through a real connection, so it needs `uip login` and a connection on the tenant. Run it when `check` asks for it, not speculatively.
<!--skill-flavor:prepare-live:end-->

Fix these source errors and rerun `check`; `prepare` does not:

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

Without a pulled library, `check` and `compile` fetch through `uip` from the Flow node catalog, so a connector the tenant serves there needs nothing more; with one they refuse absent operations, and `uip maestro registry pull` refreshes it. A refusal's final sentence explains why:

```
connector not in library: uipath.connector.uipath-uipath-testmanager.create-test-set. … The tenant was asked through uip (`uip maestro flow registry get`) and does not serve it.
```

"does not serve it" means a misspelled action or absent Flow catalog connector; use `prepare`. For any other reason, fix what `uip` names (log in again only for a session issue), then rerun `check`.

Run `uip maestro registry prepare <key> --action <name>` to resolve through the live connection and write the compiler overlay, one operation per call. Use activity-catalog kebab-case names from `uip is activities list <key> --output json` (`CreateTestSet` → `create-test-set`, `GetAssignedTestCasesForTestSet` → `get-assigned-test-cases-for-test-set`). If Flow lacks the connector, `prepare` refreshes once with `uip maestro flow registry pull --force`; if still absent it reads Integration Service activity identity and `is resources describe` path, parameters, and fields. It reports BPMN-only compilation; Flow or agent tools still need a registry node definition:

```
  source: Integration Service activity CreateTestSet (TestSet POST) — the Flow node catalog, refreshed with `uip maestro flow registry pull --force`, serves no node for uipath-uipath-testmanager, so this operation compiles in BPMN only (a Flow step or agent tool needs the registry's node definition).
prepare-connector: uipath.connector.uipath-uipath-testmanager.create-test-set → .flow-sdk/connectors-local/ (overlay + …, 1 variant(s), 3 input field(s))
prepare-connector: next: .connector("<id>", "uipath-uipath-testmanager", "create-test-set", { ProjectId: /* string, required */, name: /* string, required */ }, { connection: "testmanager", folder: "shared" })
```

Author the printed `.connector()` call. `check` enforces the real contract (for example, Test Manager update uses JSON-patch `path`/`value`, and `execute-test-set` uses `testSetId`, `executionType`, and `asyncMode`); `compile` emits catalog `objectName`/`method`, describe `path`, and `pathParameters`; Flow rejects it with `CONNECTOR_NO_FLOW_DEFINITION`. If source says pull failed, run `uip maestro flow registry pull --force` and rerun `prepare` before concluding it is absent.

An unfindable action is refused with Integration Service action ids; rerun with one. `prepare` does not query Integration Service for a catalog-served connector, so a misspelled Jira action receives the catalog's closest action.

Only when `prepare` cannot reach the tenant may you use a hand-filled `.activity(id, 'Intsvc.ActivityExecution', …)`, and only on evidence gathered while the tenant was reachable: the commands below are the same tenant reads `prepare` makes, so they fail for the same reason. Use a connection id, an activity row and a `registry get` template saved from an earlier session (or carried in the task), never a guess; with none of those, wait for access. A draft that cannot wait for access takes the form in §7. The reads that produce that evidence:

```bash
uip is connections list <CONNECTOR_KEY> --all-folders --output json      # the connection id
uip is activities list <CONNECTOR_KEY> --output json                     # Name + ObjectName + MethodName + IsCurated
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <ObjectName> --operation <Verb> \
    --input-details '{}' --output json                                     # the V2 element (Data.V2.ElementXml), with the describe
```

The identity comes from the catalog, never from the connector's OpenAPI document. Use catalog `objectName` (`UploadAttachment`, `TestSet`) and verb `method` (`POST`, `GETBYID`, `PATCH`, `DELETE`), not REST slugs; curated matching is exact. A node carrying `objectName="v2::attachment::upload"` validates and then dispatches to nothing. `check` holds a hand-filled task to the catalog (`INTSVC_*`), which `validate` does not; fix what it reports. Set the `.activity()` `path` to `Operation.Path` from this describe, saved from an earlier session or run now:

```bash
uip is resources describe <CONNECTOR_KEY> <OBJECT_NAME> --operation <VERB> --output json
```

Examples: `/curated_create_issue`, `/curated_get_issue/{issueId}`. It differs per operation and is not always `/<objectName>` (`issue_properties` is `/issue/{issueIdOrKey}/properties`), so never derive it.

Use the operation-specific route, not the provider's REST route (`/rest/api/2/issue`); provider routes can validate but debug faults `[102002] Integration Services operation failed` (observed Jira Create Issue provider 401). Copy `<uipath:context>` rows of `Data.V2.ElementXml` into the `.activity()` context, including `activityConfigurationVersion: 'v2'`. Without `--input-details`, `registry get` returns only V1 (`activityConfigurationVersion` defaults to `v1`); pass the node's values as JSON to `--input-details` (`'{}'` when none) and use `Data.V2.MissingRequired` for remaining required inputs. Put `{param}` path values in `inputs: { pathParameters: { <param>: … } }`, query values in `inputs: { queryParameters: { … } }`; a bare `inputs: { <param> }` lands in the body. See [the parameter rows](bpmn-runtime.md#connectors-and-bindings).

For a generic record verb (`Create Record`, `Delete Record`), the catalog row's `N/A` is not the answer: obtain `objectName` from `uip is resources list <key> --connection-id <id> --output json`; use the catalog Integration Service method, not the HTTP verb: `GETBYID` (single Retrieve), `GET` (list), `POST` to create, `PATCH`/`PUT` to update, or `DELETE`; obtain `path` from `uip is resources describe <key> <object> --operation <Verb> --connection-id <id> --output json`.

## 5. Data Fabric is not this

Data Fabric records/files use `.dataService(id, { entity, connection, folder, op, … })`, one of eight operations. A folder entity is `entity: { name, folder: '<folder path>' }`; once `check`'s `prepare` records its keys, it writes the connector's `_V3` operation: `create`, `update`, `get`, `query` as V2 Studio Web tasks, `delete` as V1; see [the folder-entity rule](bpmn-runtime.md#connectors-and-bindings) for these and the other V1 cases. The library has one Data Service operation, so `.connector()` cannot author the rest, and hand-filled `.activity()` gets object, parameter targets, and folder binding wrong in ways `validate` does not report. See [Connections and bindings](bpmn-runtime.md#connectors-and-bindings) and `examples/ContractRegistry.bpmn.ts`.

## 6. Connector events

`.eventTrigger(id, connector, event, opts)` starts a process; `.waitForEvent(id, connector, event, opts)` pauses it. Both use the same library and `connection`/`folder` bindings.

- `filter` is subscription scope: connector event parameters, e.g. `{ parentFolderId: lookup('uipath-microsoft-outlook365', 'email-received', 'parentFolderId').by('displayName', 'Inbox') }` for Outlook `email-received`. Omitting it subscribes to everything and `check` reports `EVENT_NO_SCOPE` with declared parameters. Id scope values always use `lookup()`; §3 resolves them with `--action email-received`.
- `object` names what a generic event watches (`record-created` and related Data Fabric, Salesforce, ServiceNow, Jira events). It is required: omission emits `objectName: ""`, which validates and watches nothing; `check` reports `EVENT_GENERIC_NO_OBJECT`; curated events reject it with `EVENT_OBJECT_NOT_GENERIC`.
- Data Fabric folder entity triggers `record-created-preview-`/`record-updated-preview-` (object `EntityTriggers_V3`) use `entity: { name, folder: '<folder path>' }`, never `filter: { entityScope, folderEntityName }`; the literal filter watches the records but writes no picker, so `refresh` declares no entity and a deploy cannot re-point it.
<!--skill-flavor:sdk-event-entity:start-->
  Needs `@uipath/maestro-builder-sdk` 6.123.0 or later; an older SDK reports `TS2353` on `entity`, so upgrade the copy `uip` resolves, local copy first, then global. From the directory you run `uip` in (the workspace root), run `node -e "console.log(require.resolve('@uipath/maestro-builder-sdk/package.json',{paths:[process.cwd()]}))"`. When it prints a path, that `node_modules` (possibly in a parent directory) owns the copy: run `npm install --save-dev @uipath/maestro-builder-sdk@latest` in the directory holding it when a `package.json` sits beside it; otherwise tell the user the path, and never create a `package.json`. On error, run `npm install -g @uipath/maestro-builder-sdk@latest`. Then run `check` again. Never fall back to the literal `filter`.
<!--skill-flavor:sdk-event-entity:end-->
  `check` reports `RESOURCE_UNRESOLVED` and prints the `uip maestro registry prepare --entity <name> --folder-path <path>` that records the keys, as for `.dataService()`; the trigger and a task on that entity share one binding pair. Run `uip maestro bpmn refresh` after `compile`.

```bash
uip is triggers objects <connector> <EVENT> --connection-id <id> --output json   # what a generic event can watch
uip is triggers describe <connector> <EVENT> <object> --connection-id <id> --output json
```

Payload/failure go to `outputVar` (default `<id>_result`) and `<id>_Error`; downstream payload fields use `=js:vars.<id>_result.subject`. `outputs` sources read under `response`, e.g. `outputs: { subject: '=response.subject' }`; bare `'=subject'` reads nothing. `folderPath` is deprecated and ignored: the task names its folder by the `folder` binding alone, so drop it. Test Manager (`uipath-uipath-testmanager`) has no usable event: the library has none and `uip is triggers` uppercases names (`Created` → 404 `Event operation 'CREATED' was not found`). Do not author event nodes; tell the user and poll with an activity.

## 7. Draft with an unresolved connector

A source-only draft may lack a connection, operation, tenant access, or permitted real ids. Write the step so that `check` passes and the CLI, not prose, says what is missing:

- If operation metadata is local (§1 finds it in the library, a local cache, so this works offline; and `check` names no `uip maestro registry prepare` for it: `OBJECT_UNPREPARED`, `CUSTOM_FIELDS_UNPREPARED`, or a `CONNECTOR_INPUT` for a field only the connection discovers), write the §2 `.connector()` with symbolic `connection`/`folder` and no `bindings.json`. Leave no `lookup()`, because `compile` refuses one until `prepare` records it (`LOOKUP_UNRESOLVED`); use runtime `=js:vars.<id>` or fixed-vocabulary literals such as `send_as: 'bot'`. `check`, `compile`, and `format` pass, emitting `Intsvc.ActivityExecution` reading `=bindings.<name>`, while `LOOKUP_RUNTIME_VALUE`/`LOOKUP_LITERAL_ID` are warnings. `refresh` refuses `Connection binding "<name>" default must be a GUID.` and `validate` reports `MISSING_BINDING`; stop there; do not edit bindings or package files.
- Otherwise, with no tenant for `prepare` to reach (the operation is not in the library, or `check` asks for a `prepare`), write a bare `.task(id, { name })` naming the action, exact connector key, and operation, such as `'Send Slack digest (uipath-salesforce-slack / send-message-to-channel, unresolved)'` or `.task('sendDigest', { name: 'Send digest via uipath-salesforce-slack' })`. The operation may be unresolved, but the name must contain the exact library key (`uipath-salesforce-slack`, not "Slack" or "Integration Service") and a verb; notes must say it is a placeholder.

Never use placeholder `.activity(id, 'Intsvc.ActivityExecution', …)`: `check` rejects empty context (`EMPTY_REQUIRED_FIELD`) and sentinels (`INTSVC_METHOD_UNKNOWN`, `INTSVC_OPERATION_NOT_IDENTIFIER`), and `validate` rejects a compiled file. §4 hand-filled activity requires reachable-tenant evidence.

Leave `README.md` beside the source with each blocker named exactly and its resolution:

| Blocker | What it is | Resolved by |
| --- | --- | --- |
| connection binding | Tenant connection and folder companion read by `=bindings.<name>`; draft has only symbolic name. | `uip maestro registry prepare <key> --action <action>` against a live connection writes `./.flow-sdk/bindings.json`. |
| dynamic schemas | Connection-specific input/output schemas, custom fields, objects, and lookup ids. | Same `prepare`, with `--resolve` / `--object`, writes `./.flow-sdk/connectors-local/`. |
| connector operation metadata (bare `.task()` only) | `objectName`, `method`, path, and generated outputs (`<id>_response`, `<id>_Error`). | `prepare`, then replace `.task()` with its printed `.connector()` call. |
| `bindings_v2.json` | Packaged binding resources. | `uip maestro bpmn refresh <project>` after `compile`, once the connection binding resolves. |
<!--skill-flavor:package-metadata-row:start-->
| package metadata | `entry-points.json`, `operate.json`, `package-descriptor.json` | the same `refresh`; `uip solution resources refresh --solution-folder <solution-dir>` for the solution |
<!--skill-flavor:package-metadata-row:end-->

Name blockers exactly as written, not "the connection" or "the schema"; name the artifact and resolution step. Never include private connection id, folder key, tenant URL, resource key, or tenant schema.

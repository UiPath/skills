# Integration Service Connectors

*Exact signatures, fields, and defaults: `connector()`.*

Call a curated or generic Integration Service operation.

**Some Data Fabric entity operations are Integration Service connector actions.** "Data Fabric" and "Data Service" name one product; the tenant displays connector key `uipath-uipath-dataservice` as *UiPath Data Fabric*. CRUD is NATIVE: `core.datafabric.*` has `dataFabricRead()`, `dataFabricCreate()`, `dataFabricUpdate()`, and `dataFabricDelete()`; read covers filters, paging, and sort. Route here only get-by-id when the whole long-text value is needed (native reads, including `Id` filters, return a 10,000-character preview), file record fields, and Record Created / Updated events; see [`data-fabric.md`](data-fabric.md).

Signatures:

- `connector(descriptor, inputs, opts?)`
- `connector(key, action, inputs?, { connection, folder, object?, version? })`; `connection` and `folder` are required: `check` reports `BINDING_MISSING` without them.

```ts
.step('issue', connector('uipath-atlassian-jira', 'get-issue',
  { issueId: input('issueId'), project: 'IN', issuetype: 'Task' },
  { connection: 'jira', folder: 'shared' }))
```

## At a glance

Call a curated or generic operation through a generated descriptor or key/action pair. Use connector `uipath-uipath-dataservice` for file record fields, Record Created/Updated events, or scenarios naming the connector; record CRUD is native ([Data Fabric](data-fabric.md)). Discover tenant-specific fields and ids and preserve every scenario-named input.

**Bindings: [`bindings.md`](bindings.md)**

## Author first — `check` names every prepare you owe

Authoring never waits on `prepare`, and no discovery command precedes the source:

1. **Search** the library and read the operation page.
2. **Author** intended fields, `lookup()` id tokens, and `{ object: '<name-as-the-task-said-it>' }` for generic operations.
<!--skill-flavor:check-source:start-->
3. **Run** `uip maestro flow check .flow-sdk/<Name>.flow.ts --source`. It names each
<!--skill-flavor:check-source:end-->
   gap with the exact command — `LOOKUP_UNRESOLVED`, `OBJECT_UNPREPARED`, `CUSTOM_FIELDS_UNPREPARED`, `CONNECTOR_INPUT`.
   `CONNECTOR_NOT_IN_LIBRARY`, `CONNECTOR_OBJECT_REQUIRED`, and `CONNECTOR_OBJECT_NOT_GENERIC` mean the operation itself does not resolve; no prepare fixes them. Edit the source and re-run `check`:
   - `CONNECTOR_NOT_IN_LIBRARY`: no library layer has the operation, connector, or version, and with no library pulled neither does the tenant. The message lists operations and a `Closest:` match. Use the node type slug, not tenant `objectName` (`send-email`, not `send-mail-v2`).
<!--skill-flavor:not-in-library-pull:start-->
     With no library pulled, `check` and `compile` already ask the tenant through `uip`; the last sentence says what it answered. With a pulled library they do not ask; refresh a newer operation with `uip maestro registry pull`. "The tenant was asked … and does not serve it" means the name is wrong or the connector is not available on this tenant: fix the name or use `http()`. Otherwise the sentence gives `uip`'s reason: run `uip login` only when it says `uip` is not logged in or the session expired; for anything else report `uip`'s reason and stop.
<!--skill-flavor:not-in-library-pull:end-->
   - `CONNECTOR_OBJECT_REQUIRED`: add `{ object: '<name>' }`; the message lists objects.
   - `CONNECTOR_OBJECT_NOT_GENERIC`: remove `object` from a single, non-generic operation.
4. **Prepare once**: run one invocation composing `--object`, `--resolve`, and `-f`; it finds the connection and writes `bindings.json`. It repoints the import and asks only when two flows import the same connector or `--no-source-rewrite` was passed.
5. **Run `check` again, then compile.**

Every prepare command below is the command `check` prints at step 3, documented here rather than prescribed before source authoring.

## Three contracts to settle before authoring

1. Runtime strings use `tmpl`, not `js`: ``where: tmpl`invoiceNumber = '${input('invoiceNumber')}'` `` builds a string; ``js`invoiceNumber = '${input('invoiceNumber')}'` `` evaluates to only the assigned value. See [Structured filters](#structured-filters-ceql).
2. Schema-dynamic fields require a prepared descriptor; parent values alone are insufficient. Run `registry prepare` with them and import its generated descriptor so schema-replay metadata remains. See [the parent-field loop](#schema-dynamic-operations-the-parent-field-loop).
3. Paged reference lookups use exactly `nextPage`: when `Pagination.HasMore` is true, pass `Pagination.NextPageToken` as `--query "nextPage=<token>"`; never use `page`, `pageToken`, or `nextPageToken`. See [Resolving connection-scoped reference values](#resolving-connection-scoped-reference-values).

## Discovering operations and fields

<!--skill-flavor:library-discovery:start-->
`uip maestro registry pull` downloads the published library to `~/.uipath/cache/flow-sdk/library/current/`; `compile`, `check`, and `registry search` resolve it without a flag. The project receives only `.flow-sdk/connectors/`, one descriptor per referenced connector.

```bash
uip maestro registry pull
```

If download fails or none is published (Automation Suite), pull is optional: `pull` fetches referenced connectors through `uip` into `.flow-sdk/connectors-local/` (use `--connector <key>` for a key not yet in source); `registry search` searches the tenant catalog; `check`, `compile`, `decompile`, `merge`, and `registry describe` fetch missing operations through `uip` into `.flow-sdk/connectors-local/` and continue. These require logged-in `uip` and an SDK recent enough to fetch; see [CLI-LOOP.md](CLI-LOOP.md#installing-the-package). With neither a library nor a working `uip`, connector work stops at a message giving the reason; fix what it names (`uip login` only for a session problem). `$FLOW_SDK_LIBRARY_JSON`, when set, overrides the cache.

Library verbs are `pull`, `search`, `describe`, `path`, and `prepare`; they require prerelease `@uipath/cli` and run the installed `@uipath/maestro-builder-sdk`. `uip` is the entry point and is present here. The package also exposes `flow-sdk`; printed remedies use it when `FLOW_SDK_INVOKED_AS` is unset.
<!--skill-flavor:library-discovery:end-->

**`uip maestro registry` is not `uip maestro flow registry`.** The names are one
word apart and the jobs are unrelated: this one is the connector library the
compilers resolve operations against, while `uip maestro flow registry
pull|search|get` syncs the tenant's **node manifests** — the node types other
references reach for (`uipath.core.function`, `uipath.core.agent.<name>`).
Connectors are never node-registry entries and nodes are never library entries, so a miss in one is not evidence about the other.

<!--skill-flavor:library-search:start-->
Search static contracts, then read an operation page:

```bash
uip maestro registry search 'send email'
uip maestro registry describe uipath.connector.uipath-microsoft-outlook365.send-email
```

`describe` renders from the operation entry with or without a pulled library; tenant-fetched pages identify that on their first line.
<!--skill-flavor:library-search:end-->

When `check` rejects a connection-specific field or warns that schema is unprepared, materialize live schema with the diagnostic command; do not guess or edit emitted Flow. It needs a live Integration Service connection and logged-in `uip`; otherwise author only fields listed by `registry describe`.

```bash
uip maestro registry prepare <connector-key> --action <action>
# Generic operation: materialize the one connected object the task uses.
uip maestro registry prepare <connector-key> --action <action> --object <api-object-name>
# Use --all-objects only when the task truly needs the full connected catalog.
```

Results land in `.flow-sdk/connectors-local/`, which compilers union over the library; calls accumulate. `prepare` chooses a connection. Pass `--connection-id <id>` only to pin one; non-`Enabled` connections are refused with enabled alternatives. A `Failed` connection returns an empty schema, so preparing through it would write a no-field overlay and the next compile would reject every input as unknown; the refusal is the only signal that says "connection", not "field".

<!--skill-flavor:descriptor-imports:start-->
Import descriptors from either tree with the real `.ts` extension (a `.js` specifier does not resolve); paths are relative to the source in `.flow-sdk/`:

```ts
import { CreateInvoiceShare } from './connectors-local/uipath-salesforce-sfdc.ts';
import { SendMessageToChannel } from './connectors/uipath-salesforce-slack.ts';
```
<!--skill-flavor:descriptor-imports:end-->

Older environments expose bare `prepare-connector` with identical arguments except connector version is `--connector-version` (not Commander's `--version`). For many connectors the first prepare is insufficient; use the parent-field loop before concluding a field does not exist.

### A Generic operation is authored from the LIBRARY, not through registry prepare

Use the library action id and object option directly:

```ts
.step('users', connector('uipath-servicenow-servicenow', 'list-records',
  {}, { connection: 'sn', folder: 'shared', object: 'acr_user' }))
```

This generic form needs no live resolution and compiles from the baked library. `registry prepare` is for curated schema-dynamic operations; for a generic operation use it only when a needed field is genuinely missing (a generic list usually has none, so preparing resolves nothing). The library and the registry use the same id, `list-records`. Older libraries called it `list-all-records`; against the current library that id is `CONNECTOR_NOT_IN_LIBRARY`. ServiceNow's `list-records` is one object-less entry, so `object: 'acr_user'` is accepted with a warning and the tenant resolves it at dispatch; a connector with static objects (Coupa) has one `list-records` entry per object.

### Finding the object id for a Generic operation

Author `{ object: '<name-as-the-task-said-it>' }` and let `check` name the `OBJECT_UNPREPARED` command. `--object` matches exact, then case-insensitive API/display names, narrowed to objects supporting the action verb:

```bash
uip maestro registry prepare <connector-key> --action <action> --object Company__C
#   object: matched "Company__C" -> Company__c
```

Multiple matches are refused with API name, display name, custom, and operations; `Custom: yes` marks tenant-only objects; a task that says "custom" means one of those rows. Pick by the task's wording, or present the candidates and let the user choose—never pick for them—then re-run with the chosen `Name`. No match after catalog refresh means the object is not on that connection; report it. Do not use `uip is resources list` plus `--output-filter`; prepare performs matching, verb narrowing, retry, and records it in `.flow-sdk/connectors-local/resolutions.json` under `objects`.

## Structured filters (CEQL)

List operations accept a server-side FilterBuilder parameter, usually `where`, sometimes `q`. **Write the CEQL string; the SDK derives the tree.**

```ts
connector('uipath-microsoft-azureactivedirectory', 'list-groups',
  { where: "displayName = 'active' AND createdDateTime >= '2026-01-01T00:00:00Z'" },
  { connection: 'entra', folder: 'shared' })
```

The artifact must contain both runtime `inputs.detail.queryParameters.where` and design-time `configuration.essentialConfiguration.savedFilterTrees.where`. Studio Web renders the FilterBuilder from the tree; product
validation rejects a literal filter that has only one of the two, so a
hand-written literal without its tree fails `validate` even though the run
would have worked (a runtime `tmpl` filter is exempt; see below). If the task asks for the filter, or its tree, as a separate file, compile first and copy `configuration.essentialConfiguration.savedFilterTrees.<parameter>` verbatim, directly or under a named top-level property, never an ad hoc `{ field, operator, value }` object or only the CEQL string; retain numeric `groupOperator` and `filters`.

Supported operators: `=` `!=` `<` `<=` `>` `>=`, `Contains`, `Starts With`, `Ends With`, `Like`, their `Not` forms, and `Is Null` / `Is Not Null`; combine with `AND` or `OR`, and parenthesise to nest — `(a = 1 OR b = 2) AND c = 'x'`. Mixing `AND` and `OR` at one level is refused.

Three spellings are compile errors here rather than a tenant-side
`[102003] Integration Services bad request`:

| Wrong | Why | Right |
|---|---|---|
| `'accountNumber' = 'ACC123'` | a quoted token is a VALUE to CEQL | `accountNumber = 'ACC123'` |
| `accountNumber = "ACC123"` | double quotes mark a COLUMN reference | `accountNumber = 'ACC123'` |
| `status eq 'Open'` | `eq`/`ne`/`gt`/`ge`/`lt`/`le` are OData | `status = 'Open'` |

**A filter built from a runtime value has no filter tree, and that is valid.**
The tree holds literals only, so a runtime-expression (`tmpl`) filter in `where`
(for example ``tmpl`displayName = '${input('name')}'` ``) emits the query with no tree.
`validate` accepts it, and the runtime resolves the whole value. The only cost is
at design time: the Studio Web filter widget shows no tree for that step. If the
widget must show the constant terms, put them in a literal filter and narrow the
rest downstream.

## Schema-dynamic operations: the parent-field loop

For `loadByDefault`, dependent dropdowns, and `customFieldsRequestDetails`, the static descriptor is insufficient. Run the prepare named by `check`, including every `-f NAME=VALUE`; it creates schema-replay metadata. Do not substitute manual `resources run list` lookups plus a static `./connectors/<key>.ts` import (lookups do not create that cache), nor `rawNode`, emitted-flow edits, or hand-written `connectors-local/` overlays; each produces a node the platform cannot run. After compile, inspect connector configuration: completion requires non-null `customFieldsRequestDetails` whose parent values match runtime inputs, even though `flow validate` may accept a missing cache.

Field sets depend on parent **values**, not merely connection, and `fields.summary` — *required* — appears in none of Jira `create-issue`'s static inputs. Parent ids recorded by `--resolve` are exactly the values `-f` needs; combine them:

```bash
uip maestro registry prepare uipath-atlassian-jira --action create-issue \
  --resolve fields.project.key:key=UIP --resolve fields.issuetype.id:name=Bug \
  -f fields.project.key=UIP -f fields.issuetype.id=10732
```

If all parents were resolved separately, paste the exact `-f NAME=VALUE` re-run printed by prepare. Missing parents are refused (`No api-type ObjectAction matched for fields [fields.project.key]`); a value absent from the connection passes the describe silently and yields only parent fields, so treat "I passed `-f` and still got only the parents" as a wrong value, never as "this operation has no other inputs". `prepare` fails in both cases rather than writing the overlay.

**1. Find parents.** Describe with no values and inspect each input's reference. A parent has `Reference.Path` containing a `{placeholder}` naming another field; resolve the field a placeholder names first (`fields.project.key` before `fields.issuetype.id`):

```bash
uip is resources describe <connector-key> <object> \
  --connection-id <connection-id> --operation <Operation> --output json
```

```jsonc
{ "Name": "fields.issuetype.id",
  "Reference": { "ObjectName": "project",
                 "Path": "/project/{fields.project.key}/issuetypes" } }
```

Data Service (`uipath-uipath-dataservice`) actions such as `create-entity-record`, `update-entity-record`, and file-record-field operations instead use `GenerateSchema` over `entityName`; no-value describe returns only the static inputs (`entityName`, `expansionLevel`), so `compile` refuses the entity's fields (`title`, …) as unknown; the fix is always the entity name:

```bash
uip maestro registry prepare uipath-uipath-dataservice --action create-entity-record \
  -f entityName=FlowCodeEvalEntity
# → 8 input field(s): entityName, expansionLevel + the entity's own fields
```

Do not work around the refusal — not with `rawNode`, not by editing the emitted `.flow`, not by hand-writing a `connectors-local/` overlay. Each produces a node the platform cannot run.

Copy parent names exactly from this operation's describe; they are operation-specific (Jira `get-issue` uses `project` and `issuetype`).

**2. Resolve each value outermost first.** Match `Reference.Path`, not `Reference.ObjectName`; find the object whose path covers it when the subcollection is not listable:

```bash
uip is resources list <connector-key> --connection-id <connection-id> --output json   # find the object
uip is resources describe <connector-key> <object> --connection-id <connection-id>    # confirm its Path
uip is resources run list <connector-key> <object> --connection-id <connection-id> \
  --query "<path-param>=<value-from-the-previous-parent>" --output json
```

For Jira, `/project/{key}/issuetypes` is covered by `project_statuses` (`/project/{projectIdOrKey}/statuses`).

**3. Prepare with every parent.**

```bash
uip maestro registry prepare <connector-key> --action <action> \
  -f fields.project.key=IN -f fields.issuetype.id=10620
```

Prepare separately reports service rejection and accepted values that resolve only to parents. Values are parent-scoped (Jira `Task` is `10620` in `IN`, `10005` in `AP`): never copy ids between projects, connections, or tasks; resolve against the connection bound by the flow. Standard `summary` and `description` are portable; custom fields such as `fields.storyPointEstimate_Customfield10016` may not be.

Use the generated descriptor import and `connector(...)` call; it carries connection-resolved operation/object identity even when action ids differ. `connectors-local/` is authoring input; emitted Flow is self-contained. Prefer curated operations. For a raw call the curated surface lacks, use the managed HTTP node (`core.action.http.v2`) with the connector's connection and `targetConnector: '<connector-key>'` ([http.md](http.md)); the library has no per-connector `*-http-request` operation.

Preparation needs a live connection. For explicitly offline/validate-only evidence without connection-specific fields, use the baked descriptor and published static inputs; do not invent fields or use placeholder discovery. If the published list is empty, pass `{}`; offline evidence then proves operation identity/control-flow routing, not provider payload/dispatch.

[`bindings.json`](bindings.md) defines symbolic connection/folder bindings and compile-time resolution; populate resource keys from live connection/folder listings. A plausible GUID is not evidence of existence or tenant membership; resource refresh and product debug are the evidence.

### File uploads are multipart Flow inputs

If the catalog omits an upload field, prepare against its connection and pass the upstream file as a connector input:

```ts
.step('upload', connector(SendFileToChannel, {
  file: out('download', 'Response'),
  channels: channelId,
  send_as: 'user',
}, { connection: 'slack', folder: 'shared' }))
```

The compiler emits `multipartParameters`; `uip is resources run` has no multipart flag and is not the execution surface. Only a **file** part is an input. String-typed parts (Teams `body`, Gmail `body`, GenAI `RagRequest`) are containers; pass body fields (`'body.content'`, `Body`, `prompt`), never the part itself.

```ts
.step('notify', connector(SendChannelMessage, {
  team_id: lookup(SendChannelMessage, 'team_id').byDisplayName('Sales'),
  channel_id: lookup(SendChannelMessage, 'channel_id').byDisplayName('alerts'),
  body: { content: 'A request was routed to Sales.' },   // or 'body.content': …
}, { connection: 'teams', folder: 'shared' }))
```

## Resolving connection-scoped reference values

Lookup fields store ids, not display names. If marked LOOKUP, author its helper and do not guess or manually resolve it:

```ts
channel: lookup(SendMessageToUser, 'channel').byRealName('Ada Lovelace')
```

Slack omits `profile.email` unless the connection's app may read emails, so `.byEmail(…)` can match no one; prefer `.byRealName(…)` or `.byId(…)`. When prepare says `none carries '<field>'` (an SDK with builder-sdk#2096), the value is not wrong: search by a field the message lists after `Search by`. A real name need not be unique; prepare takes the first exact match without warning, so use `.byId(…)` when two users may share it.

| form | when | helpers |
|---|---|---|
| `lookup(SendMessageToUser, 'channel')` | prepared descriptor | `.byEmail(v)`, `.byRealName(v)`, … (as the descriptor's `LOOKUP:` header lists them) and `.by(name, v)` |
| `lookup('uipath-salesforce-slack', 'send-message-to-user', 'channel')` | generic CRUD/no descriptor | `.by(name, v)` only |

Never use an alias (`.byEmail`, `.byRealName`, generated onto the descriptor) in the second form; it throws. Use `.by('profile.real_name', …)` there. Searchable names are in the descriptor `LOOKUP:` header and `check` diagnostics.

A folder-tree lookup (OneDrive's `referenceID` by `FullName`) matches a bare name only at the top or one level below; deeper paths start at the root picker's top entry, not drive root:

```ts
referenceID: lookup(DownloadFile, 'referenceID').by('FullName', 'OneDrive/<folder>/<file>')
```

Expect a walk to take four to six minutes; a wrong first segment fails quickly, but a wrong file name fails only after the walk, naming its stopping segment. So confirm the name first with:

```bash
uip is resources run list uipath-microsoft-onedrive EventFolderPicker --connection-id <connection-id> --query '{"parentReference":"<folder ReferenceID>","includeFiles":"true"}' --output json
```

Drop `parentReference` at top level. When source contains unresolved tokens, run the one prepare command `check` prints; it records every lookup and writes connection and folder to `bindings.json`; it is the only tenant call the loop needs:

```bash
uip maestro registry prepare uipath-salesforce-slack --action send-message-to-user \
  --resolve 'channel:profile.real_name=Ada Lovelace'
```

Do not find the connection first: prepare searches `uip is connections list` (own folder then tenant), writes connection id and folder key, and accepts `--connection <name>` only to disambiguate candidates. If a value is absent, it tries other enabled connections and re-runs itself against the one that resolves (which `bindings.json` then names), unless `--connection-id` or `--connection` pinned one; it does not retry transport/permission failures or choose between two resolving connections. When one was pinned or two resolve, the message names alternatives; choose and re-run with the printed `--connection-id`.

Do not crawl Integration Service after lookup failure: the message names the connection read and, once every candidate is tried, the one command that shows what the collection holds. When the candidates share a name or several resolve, choose as [bindings.md](bindings.md#where-both-values-come-from) says, and pass the `--connection-id <id>` its candidate line prints. `bindings.json` entries take the source's `connection:` and `folder:` labels, which [must differ](bindings.md#where-both-values-come-from); a source with none gets the connector's last segment (for example `slack`) and `shared`; `--bind-connection` / `--bind-folder` override. If a label cannot be traced from source, prepare prints `bindings:` and binds the readable label or default. It refuses multiple labels for one connector or one connection label shared by two connectors, and prints bound names on `next:`. `compile` refuses a label that a `bindings.json` with entries does not declare (`BINDING_UNDECLARED`) and warns unresolved declared entries (`CONNECTION_STUB`).

`check` reports unresolved lookups as `LOOKUP_UNRESOLVED`, warns on literal ids, and warns runtime expressions as `LOOKUP_RUNTIME_VALUE` with the sent id (for example `reporter.accountId`); it errors when an e-mail expression feeds a lookup that neither sends nor searches by e-mail. Resolve a required lookup field you have no value for with its helper, never from a look-alike input. Run `check` before compile so the one expensive prepare call is last.

<!--skill-flavor:connection-user:start-->
**When the task names nobody for a person-shaped required field** (`reporter`, `requester`, `owner`), use the connection's own user: take the account from `uip login status` and resolve by **display name**. Search only names declared by the field's "matches on" list; do not query raw collections. Jira user search hides e-mail addresses, so `emailAddress=` returns nothing while `displayName=` finds the user; the spec (`matches on displayName | accountId`) excludes e-mail.
<!--skill-flavor:connection-user:end-->

Operation pages and generated-descriptor comments list lookup helpers and searchable fields; `grep -B6 'export const SendMessageToUser'` finds the latter. Plain strings are correct for enumerated legal values and tenant-invariant collections (country lists, timezones) when the page says so and supplies the accepted-value command.

Use this manual route only when a field carries no lookup, or to inspect a collection; resolve against the same bound connection, never by copying an id from another connection or session. Prepare first, then read the target input's `reference` in `.flow-sdk/connectors-local/*.v1def.json`: `reference.path` identifies the exact collection and placeholders; `reference.objectName` is only a starting point. Use `objectName` only when `uip is resources describe <connector-key> <objectName>` reports a matching `Path`; otherwise find the object whose `Path` covers it and pass placeholders as query parameters. Never substitute a similar collection.

```bash
uip is resources run list <connector-key> <object-name> \
  --connection-id <connection-id> \
  --output-filter '{items:items[].{Id:Id,Name:Name},page:Pagination.{HasMore:HasMore,NextPageToken:NextPageToken}}' \
  --output json
```

`--output-filter` selects from `Data`; replace `Id` and `Name` with exact prepared-reference fields and retain pagination fields. When `Data.Pagination.HasMore` is `"true"`, keep operation/connection and pass the token as `nextPage`:

```bash
uip is resources run list <connector-key> <object-name> \
  --connection-id <connection-id> \
  --query "nextPage=<value-from-NextPageToken>" \
  --output-filter '{items:items[].{Id:Id,Name:Name},page:Pagination.{HasMore:HasMore,NextPageToken:NextPageToken}}' \
  --output json
```

Stop when the target appears; otherwise continue until `Data.Pagination.HasMore` is `"false"`. A first-page miss proves nothing; the parameter is `nextPage`, not `nextPageToken`.

## Response judgments

A get-by-id not-found is a service error. Add `.onError(...)` when the scenario wants a not-found answer; otherwise failing loud may be intentional.

<!--skill-flavor:output-names:start-->
Output field names are case-sensitive and `check` does not verify them: `out('upload', 'WebUrl')` compiles but reads `null` when the field is `webUrl`. Copy names from the operation's `## Outputs` in `uip maestro registry describe <nodeType>`.
<!--skill-flavor:output-names:end-->

For responses without declared fields, read the whole output into a script local before inspecting service properties:

```ts
.step('report', script({ code: `
  const issue = $vars.issue.output;
  return { key: issue.key, status: issue.fields.status.name };
` }))
```

Measured list operations return bare arrays; prefer that for unmeasured lists while allowing live evidence to disprove it. Add genuine wrappers found in product debug to the list-envelope ledger. One call is one page; use operation filtering/paging for narrower or later pages.

## Scenario and evidence boundary

Include every scenario-named input even when provider schema marks it optional; replay proves threading. Integration Service live mode proves dispatch and service response. Only product Flow debug proves deployed bindings and whole-graph execution.

Generated descriptors provide the typed alternative: `connector(CreateIssue, inputs, opts)`. Use `opts.object` to disambiguate a generic operation covering several objects.

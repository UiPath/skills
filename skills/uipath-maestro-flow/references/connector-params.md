# Integration Service Connectors

*Exact signatures, fields, and defaults: `connector()`.*

Call a curated or generic Integration Service operation.

**Some Data Fabric entity operations are Integration Service connector actions.** "Data Fabric" and "Data Service" name one product; the tenant displays connector key `uipath-uipath-dataservice` as *UiPath Data Fabric*. CRUD is NATIVE: `core.datafabric.*` has `dataFabricRead()`, `dataFabricCreate()`, `dataFabricUpdate()`, and `dataFabricDelete()`; read covers filters, paging, and sort. Route here only get-by-id when the whole long-text value is needed (native reads, including `Id` filters, return a 10,000-character preview), file record fields, Record Created / Updated events, or a scenario that names the connector; see [`data-fabric.md`](data-fabric.md).

Signatures:

- `connector(descriptor, inputs, opts?)`
- `connector(key, action, inputs?, { connection, folder, object?, version? })` (`connection` and `folder` are required; `check` reports `BINDING_MISSING` without them)

```ts
.step('issue', connector('uipath-atlassian-jira', 'get-issue',
  { issueId: input('issueId'), project: 'IN', issuetype: 'Task' },
  { connection: 'jira', folder: 'shared' }))
```

## At a glance

Call a curated or generic operation by descriptor or key/action. For Data Fabric, use the connector only for file fields, Record Created/Updated events, explicitly named connector scenarios, or get-by-id requiring the whole long-text value; CRUD is native ([Data Fabric](data-fabric.md)). Discover tenant-specific fields and ids and preserve every scenario-named input.

**Bindings: [`bindings.md`](bindings.md)**

## Author first — `check` names every prepare you owe

Never wait on `prepare` while authoring or run discovery before authoring:

1. **Search** the library and read the operation page.
2. **Author** from the task's words, including intended fields, `lookup()` id tokens, and `{ object: '<name-as-the-task-said-it>' }` for generic operations.
3. **Check** with `uip maestro flow check .flow-sdk/<Name>.flow.ts --source`. It names each gap and remedy: `LOOKUP_UNRESOLVED`, `OBJECT_UNPREPARED`, `CUSTOM_FIELDS_UNPREPARED`, `CONNECTOR_INPUT`.

These codes mean the operation itself does not resolve; edit the source and rerun `check`:

- `CONNECTOR_NOT_IN_LIBRARY`: no operation, connector, or version exists. The message lists operations and a `Closest:` match. Use the node type slug, not tenant `objectName` (`send-email`, not `send-mail-v2`).
<!--skill-flavor:not-in-library-pull:start-->
  If newer than the library, run `uip maestro registry pull`.
<!--skill-flavor:not-in-library-pull:end-->
- `CONNECTOR_OBJECT_REQUIRED`: generic operation; add `{ object: '<name>' }`. The message lists objects.
- `CONNECTOR_OBJECT_NOT_GENERIC`: single non-generic operation; remove `object`.

4. **Prepare once**: combine `--object`, `--resolve`, and `-f` in one invocation. It finds the connection and writes `bindings.json`; it repoints the import and prompts only when two flows import the same connector or `--no-source-rewrite` was passed.
5. **Check again, then compile.**

Every prepare command below is the command printed by `check`, documented here rather than prescribed before source exists.

## Three contracts to settle before authoring

1. Runtime strings use `tmpl`, not `js`: ``where: tmpl`invoiceNumber = '${input('invoiceNumber')}'` `` builds a string, whereas ``js`invoiceNumber = '${input('invoiceNumber')}'` `` is assignment syntax and returns only the assigned value. See [Structured filters](#structured-filters-ceql).
2. Schema-dynamic fields require a prepared descriptor. Resolving parent values alone is insufficient: run `registry prepare` with those values and import its descriptor so schema-replay metadata remains in the Flow. See [the parent-field loop](#schema-dynamic-operations-the-parent-field-loop).
3. Paged reference lookups use exactly `nextPage`: when `Pagination.HasMore` is true, pass `Pagination.NextPageToken` as `--query "nextPage=<token>"`; never use `page`, `pageToken`, or `nextPageToken`. See [Resolving connection-scoped reference values](#resolving-connection-scoped-reference-values).

## Discovering operations and fields

<!--skill-flavor:library-discovery:start-->
`$FLOW_SDK_LIBRARY_MD` (Markdown) and `$FLOW_SDK_LIBRARY_JSON` (machine-readable) point to the staged connector library, not npm. If unset, run:

```bash
uip maestro registry pull
```

The library and Markdown go to `~/.uipath/cache/flow-sdk/library/current/`; `compile`, `check`, and `registry search` resolve them automatically. The project gets only `.flow-sdk/connectors/`, with one descriptor per referenced connector. Ask for the Markdown path:

```bash
FLOW_SDK_LIBRARY_MD="$(uip maestro registry path --library-md --output plain)" \
  || echo "no connector library yet: run uip maestro registry pull" >&2
```

The four library verbs are `pull`, `search`, `path`, and `prepare`. They require prerelease `@uipath/cli` and delegate to the workspace's `@uipath/maestro-builder-sdk`; `uip` is the entry point and is present wherever this guidance is read. The package also exposes `flow-sdk` for the same commands; printed remedies use it when `FLOW_SDK_INVOKED_AS` is unset.
<!--skill-flavor:library-discovery:end-->

**`uip maestro registry` is not `uip maestro flow registry`.** The names are one
word apart and the jobs are unrelated: this one is the connector library the
compilers resolve operations against, while `uip maestro flow registry
pull|search|get` syncs the tenant's **node manifests** — the node types other
references reach for (`uipath.core.function`, `uipath.core.agent.<name>`). A
connector operation is never in the node registry and a node type is never in
the library, so a miss in one is not evidence about the other.

<!--skill-flavor:library-search:start-->
Search static contracts:

```bash
jq '.entries[] | select(.label | test("send email"; "i")) | {label,nodeType,path}' \
  "$FLOW_SDK_LIBRARY_MD/index.json"
sed -n '1,220p' "$FLOW_SDK_LIBRARY_MD/<path-from-index>"
```
<!--skill-flavor:library-search:end-->

When `check` reports an unknown connection-specific field or unprepared schema, materialize the live schema; do not guess or edit emitted Flow. The diagnostic names this command, which needs a logged-in `uip` and live Integration Service connection; otherwise use the curated Markdown operation:

```bash
uip maestro registry prepare <connector-key> --action <action>
# Generic operation: materialize the one connected object the task uses.
uip maestro registry prepare <connector-key> --action <action> --object <api-object-name>
# Use --all-objects only when the task truly needs the full connected catalog.
```

The result is `.flow-sdk/connectors-local/`, unioned over the library; calls accumulate. `prepare` selects the connection. Pass `--connection-id <id>` only to pin one; non-`Enabled` `State` is refused with enabled alternatives. A `Failed` connection returns an empty schema, so preparation through it would write an empty overlay and subsequent inputs would remain unknown.

<!--skill-flavor:descriptor-imports:start-->
Import descriptors from either tree with the real `.ts` extension (not `.js`); paths are relative to the source in `.flow-sdk/`:

```ts
import { CreateInvoiceShare } from './connectors-local/uipath-salesforce-sfdc.ts';
import { SendMessageToChannel } from './connectors/uipath-salesforce-slack.ts';
```
<!--skill-flavor:descriptor-imports:end-->

Older environments provide bare `prepare-connector` on `PATH`; arguments are identical except connector version is `--connector-version` (not `--version`, which is Commander's CLI-version flag). For many connectors that first command is **not enough on its own** — see [the parent-field loop](#schema-dynamic-operations-the-parent-field-loop) below before concluding a field does not exist.

### A Generic operation is authored from the LIBRARY, not through registry prepare

Author with the library action id and object option:

```ts
.step('users', connector('uipath-servicenow-servicenow', 'list-all-records',
  {}, { connection: 'sn', folder: 'shared', object: 'acr_user' }))
```

This generic form needs no live resolution and compiles from the library. `registry prepare` is for curated schema-dynamic operations or a genuinely missing field: the library action is `list-all-records`, while the registry action is `list-records`; the latter yields a different curated node. Author the generic call above unless you specifically want that.

### Finding the object id for a Generic operation

Do not hunt for it, and do not resolve it before authoring: write the step with `{ object: '<name-as-the-task-said-it>' }` and let `check` name this command (`OBJECT_UNPREPARED`). `--object` matches API/display names case-insensitively, narrowed to objects supporting the action verb:

```bash
uip maestro registry prepare <connector-key> --action <action> --object Company__C
#   object: matched "Company__C" -> Company__c
```

Multiple matches are refused with API name, display name, custom, and operations. `Custom: yes` identifies tenant-only objects. Pick by the task's wording, or present the candidates and let the user choose — never pick for them — then re-run with the chosen `Name`. When **nothing** matches, the command has already retried a refreshed catalog: the object is not on this connection, so surface that rather than inventing a name. Do not use `uip is resources list` plus `--output-filter`; prepare performs matching, verb narrowing, staleness retry, and records `.flow-sdk/connectors-local/resolutions.json` (`objects`).

## Structured filters (CEQL)

List operations take a server-side FilterBuilder parameter, usually `where`, sometimes `q`. **Write CEQL; the SDK derives the tree.**

```ts
connector('uipath-microsoft-azureactivedirectory', 'list-groups',
  { where: "displayName = 'active' AND createdDateTime >= '2026-01-01T00:00:00Z'" },
  { connection: 'entra', folder: 'shared' })
```

The artifact must contain runtime `inputs.detail.queryParameters.where` and design-time `essentialConfiguration.savedFilterTrees.where` in node `configuration`; Studio Web renders the FilterBuilder from the tree; product validation rejects a filter that has only one of the two, so a string alone fails `validate` even though the run would have worked. If a separate review artifact is requested, compile and copy `configuration.essentialConfiguration.savedFilterTrees.<parameter>` verbatim, directly or under a named top-level property; retain numeric `groupOperator` and `filters`. Do not replace it with an ad hoc `{ field, operator, value }` object or only the CEQL string.

Supported operators are `=` `!=` `<` `<=` `>` `>=`, `Contains`, `Starts With`, `Ends With`, `Like`, their `Not` forms, and `Is Null` / `Is Not Null`; combine with `AND` or `OR` and parenthesize. Mixing `AND` and `OR` at one level is refused. Column tokens are unquoted, values use single quotes, double quotes mark columns, and OData `eq`/`ne`/`gt`/`ge`/`lt`/`le` are invalid; these are compile errors rather than tenant `[102003] Integration Services bad request`:

| Wrong | Why | Right |
|---|---|---|
| `'accountNumber' = 'ACC123'` | a quoted token is a VALUE to CEQL | `accountNumber = 'ACC123'` |
| `accountNumber = "ACC123"` | double quotes mark a COLUMN reference | `accountNumber = 'ACC123'` |
| `status eq 'Open'` | `eq`/`ne`/`gt`/`ge`/`lt`/`le` are OData | `status = 'Open'` |

A runtime-varying `js` template keeps only the runtime half and `validate` rejects it; filter server-side on constants and narrow downstream, or deliberately accept the design-time gap.

## Schema-dynamic operations: the parent-field loop

For `loadByDefault`, dependent dropdowns, and `customFieldsRequestDetails`, the static descriptor is insufficient. Run the `prepare` command `check` names with every required `-f NAME=VALUE`; it creates the schema-replay cache. Do not substitute `resources run list` plus static `./connectors/<key>.ts`. After compiling, inspect connector configuration: `flow validate` may accept a missing cache, but completion requires non-null `customFieldsRequestDetails` whose parent values match runtime inputs.

The field set depends on parent **values**, not merely connection. Measured on one live Jira tenant, `create-issue`:

| parent values | fields |
| --- | --- |
| none | **2** — just the parents themselves |
| project `IN` + issue type `Task` | **19** |
| project `IN` + issue type `Epic` | **22**, a different set |
| project `AP` + issue type `Task` | **15** |

Both dimensions matter independently, and `fields.summary` — *required* — appears in none of the snapshot's static inputs. Parents are lookups, and each `--resolve` id is the value required by `-f`; pass both together or paste the exact rerun command printed by resolve-only prepare:

```bash
uip maestro registry prepare uipath-atlassian-jira --action create-issue \
  --resolve fields.project.key:key=UIP --resolve fields.issuetype.id:name=Bug \
  -f fields.project.key=UIP -f fields.issuetype.id=10732
```

Missing parents are refused (`No api-type ObjectAction matched for fields [fields.project.key]`); a value absent from the connection can silently produce only parent fields, so treat "I passed `-f` and still got only the parents" as a wrong value. `registry prepare` fails on both cases rather than writing the overlay.

**1. Find parents.** Describe without values and inspect each input's reference. A parent has `Reference.Path` containing a `{placeholder}` naming another field:

```bash
uip is resources describe <connector-key> <object> \
  --connection-id <connection-id> --operation <Operation> --output json
```

```jsonc
{ "Name": "fields.issuetype.id",
  "Reference": { "ObjectName": "project",
                 "Path": "/project/{fields.project.key}/issuetypes" } }
```

The placeholder orders resolution. Data Service (`uipath-uipath-dataservice`) operations such as `create-entity-record`, `update-entity-record`, and file-record-field operations instead declare the parent through `GenerateSchema` over `entityName`; no-value describe returns only `entityName`, `expansionLevel`, and other static inputs. Prepare with the entity name:

```bash
uip maestro registry prepare uipath-uipath-dataservice --action create-entity-record \
  -f entityName=FlowCodeEvalEntity
# → 8 input field(s): entityName, expansionLevel + the entity's own fields
```

Never bypass this with `rawNode`, emitted-Flow edits, or a hand-written `connectors-local/` overlay. Copy parent `Name` values exactly for each operation; names are not portable between actions (for example, Jira `get-issue` uses `project` and `issuetype`).

**2. Resolve each outermost first.** Match `Reference.Path`, not `Reference.ObjectName`; find the object whose declared path covers the collection when needed:

```bash
uip is resources list <connector-key> --connection-id <connection-id> --output json   # find the object
uip is resources describe <connector-key> <object> --connection-id <connection-id>    # confirm its Path
uip is resources run list <connector-key> <object> --connection-id <connection-id> \
  --query "<path-param>=<value-from-the-previous-parent>" --output json
```

For Jira, `/project/{key}/issuetypes` is covered by `project_statuses` (`/project/{projectIdOrKey}/statuses`).

**3. Prepare all parents:**

```bash
uip maestro registry prepare <connector-key> --action <action> \
  -f fields.project.key=IN -f fields.issuetype.id=10620
```

Preparation separately fails for service rejection and accepted values resolving to no fields beyond parents. Parent ids are connection- and scope-specific (`Task` is `10620` in `IN` and `10005` in `AP`); resolve against the bound connection. Custom fields may not exist on another tenant; standard `summary` and `description` are portable.

Use the generated descriptor and call; it carries resolved operation/object identity even when action ids differ from the catalog. `connectors-local/` is authoring input; emitted Flow is self-contained. Prefer curated operations; use raw `*-http-request` only for raw/generic needs absent from the curated surface.

Preparation requires a working live connection. For explicitly offline/validate-only evidence without connection-specific fields, use the baked descriptor and published static inputs; do not use a placeholder connection or invent fields. If the list is empty, pass `{}`; offline evidence proves identity/control-flow routing, not provider payload or dispatch.

[`bindings.json`](bindings.md) defines symbolic connection/folder bindings, schema, compile-time resolution, and the emitted-artifact boundary. Populate resource keys from live connection/folder listings. A plausible GUID is not proof that a resource exists or belongs to the intended tenant; resource refresh and product debug are the evidence.

### File uploads are multipart Flow inputs

Prepare against the connection when the static catalog omits an upload field, then pass the upstream file as a normal connector input:

```ts
.step('upload', connector(SendFileToChannel, {
  file: out('download', 'Response'),
  channels: channelId,
  send_as: 'user',
}, { connection: 'slack', folder: 'shared' }))
```

The compiler emits `multipartParameters`. This is Flow artifact transport; `uip is resources run` has no multipart flag and is not the execution surface. Only a **file** part is input. String parts such as Teams `body`, Gmail `body`, and GenAI `RagRequest` are runtime containers; supply body fields (`'body.content'`, `Body`, `prompt`), never the part itself.

```ts
.step('notify', connector(SendChannelMessage, {
  team_id: lookup(SendChannelMessage, 'team_id').byDisplayName('Sales'),
  channel_id: lookup(SendChannelMessage, 'channel_id').byDisplayName('alerts'),
  body: { content: 'A request was routed to Sales.' },   // or 'body.content': …
}, { connection: 'teams', folder: 'shared' }))
```

## Resolving connection-scoped reference values

Reference fields store ids, not display names. If marked LOOKUP, do not guess or resolve manually: author its helper and continue.

```ts
channel: lookup(SendMessageToUser, 'channel').byEmail('dustin@example.com')
```

`.byEmail` is an alias generated only on descriptors. Forms and helpers:

| form | use | helpers |
|---|---|---|
| `lookup(SendMessageToUser, 'channel')` | prepared descriptor | `.byEmail(v)`, `.byRealName(v)`, … and `.by(name, v)` |
| `lookup('uipath-salesforce-slack', 'send-message-to-user', 'channel')` | generic/no descriptor | `.by(name, v)` only |

Never carry an alias into the second form; use `.by('profile.email', …)`. Searchable names are in the descriptor `LOOKUP:` header and `check` diagnostics.

A folder-tree lookup (OneDrive's `referenceID` by `FullName`) matches a bare name only at the top of the tree or one level below. For anything deeper, give the path from the root picker's own top entry, not from the drive root (`<folder>/<file>` fails at its first segment):

```ts
referenceID: lookup(DownloadFile, 'referenceID').by('FullName', 'OneDrive/<folder>/<file>')
```

Expect a walk to take four to six minutes. A wrong first segment fails within seconds, but a wrong file name fails only after that walk, naming the segment it stopped at (`stops at segment 3, '<file>'`). So confirm the name first: list the folder through the picker's `childPath`, `uip is resources run list uipath-microsoft-onedrive EventFolderPicker --connection-id <connection-id> --query '{"parentReference":"<folder ReferenceID>","includeFiles":"true"}' --output json` (drop `parentReference` for the top level).

When `check` reports `LOOKUP_UNRESOLVED`, run one prepare for all tokens:

```bash
uip maestro registry prepare uipath-salesforce-slack --action send-message-to-user \
  --resolve channel:profile.email=dustin@example.com
```

Do not find the connection first: prepare searches `uip is connections list` (your folder, then tenant), writes connection id and folder key to `bindings.json`, and accepts `--connection <name>` only to disambiguate candidates. If absent, it tries other enabled connections and reruns against one resolving everything:

```text
fields.project.key: not on this connection; trying 1 other uipath-atlassian-jira connection(s)
connection: is-sandboxes-test@…-sandbox-380 (uipath-maestro-flow) resolves fields.project.key;
  re-running against it (--connection-id f5273a4d-…)
```

It does not retry a pinned `--connection-id` / `--connection`, transport or permission failures, or choose between multiple successful connections; report candidates and choose.

Do not crawl Integration Service after lookup failure. Use the failure's connection and candidate command. When the candidates share a name or several resolve, choose as [bindings.md](bindings.md#where-both-values-come-from) says, and pass the `--connection-id <id>` its candidate line prints; `bindings.json` is written on that route too. The entries are named after the `connection:` and `folder:` labels your source already uses for this connector, which [must differ](bindings.md#where-both-values-come-from); a source that uses none gets `<connector's last segment>` (`slack`) and `shared`; `--bind-connection` / `--bind-folder` override both. If a computed/untraceable source label cannot be read, prepare prints `bindings:` and binds the one readable label or default. It refuses one connector with several labels or two connectors sharing a connection label; `next:` prints bound names. `compile` refuses undeclared labels as `BINDING_UNDECLARED` and warns `CONNECTION_STUB` for declarations lacking tenant ids.

`check` warns on literal lookup ids and runtime lookup expressions (`LOOKUP_RUNTIME_VALUE`), stating the sent id (for example `reporter.accountId`, not a name); it errors when an e-mail expression feeds a lookup that neither sends nor searches e-mail. (A field that sends an e-mail, such as SendGrid's `from`, takes one silently.) A required lookup field you have no value for is resolved with its helper, not filled from a look-alike input. Run `check` before compile so the expensive prepare is last.

<!--skill-flavor:connection-user:start-->
**When the task names nobody for a person-shaped required field** (`reporter`, `requester`, `owner`), use the connection's own user: take the account from `uip login status` and resolve by **display name**. Search only by the names the field's "matches on" list declares — do not improvise queries against raw collections. Jira in particular hides e-mail addresses from user search, so an `emailAddress=` query returns nothing for a user that plainly exists, while `displayName=` finds them; the field's spec (`matches on displayName | accountId`) already told you e-mail was not searchable.
<!--skill-flavor:connection-user:end-->

Operation pages and generated-descriptor comments list lookup helpers and searchable fields; `grep -B6 'export const SendMessageToUser'` finds the latter. Plain strings are correct for enumerated legal values and tenant-invariant collections (countries, timezones); their pages give accepted-value commands.

For manual inspection or fields without helpers, use the same bound connection. **Choose the collection from the prepared action definition before the first `resources run list` call.** Run `registry prepare`, inspect the target input's `reference` in `.flow-sdk/connectors-local/*.v1def.json`, and use exact `reference.path`; placeholders require earlier resolution. `reference.objectName` is only a starting point. Use it only when `uip is resources describe <connector-key> <objectName>` reports a matching `Path`; otherwise find the object whose path covers it and pass placeholders as `--query` parameters. Do not substitute by name resemblance.

```bash
uip is resources run list <connector-key> <object-name> \
  --connection-id <connection-id> \
  --output-filter '{items:items[].{Id:Id,Name:Name},page:Pagination.{HasMore:HasMore,NextPageToken:NextPageToken}}' \
  --output json
```

`--output-filter` selects from `Data`; list responses place `items` and `Pagination` there. Replace `Id` and `Name` with exact prepared-reference fields and retain page fields. If `Data.Pagination.HasMore` is `"true"`, keep operation/connection and run:

```bash
uip is resources run list <connector-key> <object-name> \
  --connection-id <connection-id> \
  --query "nextPage=<value-from-NextPageToken>" \
  --output-filter '{items:items[].{Id:Id,Name:Name},page:Pagination.{HasMore:HasMore,NextPageToken:NextPageToken}}' \
  --output json
```

Stop when the target appears; otherwise continue until `Data.Pagination.HasMore` is `"false"`. A first-page miss proves nothing. The parameter is `nextPage`, not `nextPageToken`.

## Response judgments

A get-by-id not-found is a service error. Add `.onError(...)` when the scenario wants a not-found answer; otherwise loud failure may be intentional.

<!--skill-flavor:output-names:start-->
Output names are case-sensitive and unchecked by `check`: `out('upload', 'WebUrl')` compiles but reads `null` when the field is `webUrl`. Copy names from the operation's `## Outputs` in `$FLOW_SDK_LIBRARY_MD`.
<!--skill-flavor:output-names:end-->

For responses without declared fields, read whole output into a script local before inspecting service properties:

```ts
.step('report', script({ code: `
  const issue = $vars.issue.output;
  return { key: issue.key, status: issue.fields.status.name };
` }))
```

Measured list operations return a bare array; prefer that for unmeasured lists while allowing live evidence to disprove it. Add genuine wrappers to the list-envelope ledger. One call is one page; use operation filtering/paging for narrower or later pages.

## Scenario and evidence boundary

Include every scenario-named input even when provider schema marks it optional; replay proves threading. Integration Service live mode proves dispatch and service response; only product Flow debug proves deployed binding resolution and whole-graph execution.

Generated descriptors are a typed alternative: `connector(CreateIssue, inputs, opts)`. Use `opts.object` to disambiguate a generic operation covering several objects.

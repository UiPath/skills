# Integration Service Connectors

*Exact signatures, fields, and defaults: [`connector()`](api.md#connector-function).*

Call a curated or generic Integration Service operation.

**Data Service is an Integration Service connector, not Data Fabric.** For a
task that names a Data Service entity, use connector key
`uipath-uipath-dataservice` (for example, action `query-entity-records`) and
never replace it with `dataFabricRead()` / `core.datafabric.read`.

Signatures:

- `connector(descriptor, inputs, opts?)`
- `connector(key, action, inputs?, { connection?, folder?, object?, version? })`

```ts
.step('issue', connector('uipath-atlassian-jira', 'get-issue',
  { issueId: input('issueId'), project: 'IN', issuetype: 'Task' },
  { connection: 'jira', folder: 'shared' }))
```

## Three contracts to settle before authoring

Check these before the first connector call; they are the common places where a
plausible Flow compiles but loses the intended runtime or Studio Web contract:

1. **Runtime strings use `tmpl`, not `js`.** For example,
   ``where: tmpl`invoiceNumber = '${input('invoiceNumber')}'` `` builds a string.
   ``js`invoiceNumber = '${input('invoiceNumber')}'` `` is JavaScript assignment
   syntax and evaluates to only the assigned value. See
   [Structured filters](#structured-filters-ceql).
2. **Schema-dynamic fields require a prepared descriptor.** Resolving parent
   values is not enough: run `registry prepare` with those values and import the
   generated descriptor so the Flow retains its schema-replay metadata. See
   [the parent-field loop](#schema-dynamic-operations-the-parent-field-loop).
3. **Paged reference lookups use exactly `nextPage`.** When
   `Pagination.HasMore` is true, pass `Pagination.NextPageToken` as
   `--query "nextPage=<token>"`; do not guess `page`, `pageToken`, or
   `nextPageToken`. See
   [Resolving connection-scoped reference values](#resolving-connection-scoped-reference-values).

## Discovering operations and fields

`$FLOW_SDK_LIBRARY_MD` (markdown, for reading) and `$FLOW_SDK_LIBRARY_JSON`
(machine-readable, for compiling) point at a connector library staged by the
environment. It is not baked into the npm package, so when those variables are
unset, fetch one into the project:

```bash
uip maestro registry pull
```

The library and its Markdown go to a shared cache
(`~/.uipath/cache/flow-sdk/library/current/`), and `compile`, `check` and
`registry search` resolve them from there with no flag. The project gets only
`./connectors/`, holding a descriptor per connector it references.

To read the Markdown directly, ask where it is:

```bash
FLOW_SDK_LIBRARY_MD="$(uip maestro registry path --library-md)"
```

The four library verbs are `pull`, `search`, `path` and `prepare`. Like the
authoring verbs they need a prerelease `@uipath/cli`, and they hold no logic of
their own — each one runs the `@uipath/flow-sdk` installed in this workspace. In
a workspace with no `uip`, `npx flow-sdk registry <verb>` is the same command
with the same arguments.

**`uip maestro registry` is not `uip maestro flow registry`.** The names are one
word apart and the jobs are unrelated: this one is the connector library the
compilers resolve operations against, while `uip maestro flow registry
pull|search|get` syncs the tenant's **node manifests** — the node types other
references reach for (`uipath.core.function`, `uipath.core.agent.<name>`). A
connector operation is never in the node registry and a node type is never in
the library, so a miss in one is not evidence about the other.

Search that library for static contracts:

```bash
jq '.entries[] | select(.label | test("send email"; "i")) | {label,nodeType,path}' \
  "$FLOW_SDK_LIBRARY_MD/index.json"
sed -n '1,220p' "$FLOW_SDK_LIBRARY_MD/<path-from-index>"
```

When a connection-specific field is absent, materialize the live schema rather
than guessing or hand-editing the emitted Flow. This reads the schema through
the tenant, so it needs a live Integration Service connection and a logged-in
`uip`; without one, fall back to the curated operation in the markdown library.

```bash
npx flow-sdk registry prepare <connector-key> <action>
# Generic operation: materialize the one connected object the task uses.
npx flow-sdk registry prepare <connector-key> <action> --object <api-object-name>
# Use --all-objects only when the task truly needs the full connected catalog.
```

The result lands in `./connectors-local/`, which the compilers union over the
library. Calls accumulate, so preparing a second operation keeps the first.

`prepare` picks the connection itself (see below). Pass `--connection-id <id>`
only to pin a specific one, and expect it to be checked: a connection whose
`State` is not `Enabled` is refused, naming the enabled alternatives. A `Failed`
connection answers field discovery with an empty schema, so preparing through
it would write an overlay with no fields and the next compile would still
reject every input as unknown — the refusal is the only signal that says
"connection", not "field".

Descriptors from either tree are imported with their real `.ts` extension — a
`.js` specifier does not resolve, because these are sources rather than compiled
output:

```ts
import { CreateInvoiceShare } from './connectors-local/uipath-salesforce-sfdc.ts';
import { SendMessageToChannel } from './connectors/uipath-salesforce-slack.ts';
```

Older environments provide the same tool as a bare `prepare-connector` on
`PATH`. The arguments are identical apart from one name: a connector version is
`--connector-version` here, because `--version` is Commander's own flag and
would print the CLI version instead of reaching the generator.

For many connectors that first command is **not enough on its own** — see the
parent-field loop below before concluding a field does not exist.

### A Generic operation is authored from the LIBRARY, not through registry prepare

Author it directly, with the **library's** action id and the object as an option:

```ts
.step('users', connector('uipath-servicenow-servicenow', 'list-all-records',
  {}, { connection: 'sn', folder: 'shared', object: 'acr_user' }))
```

That is the generic form, and it needs no live resolution: it compiles off the
baked library, validates, and runs. `registry prepare` is for a **curated,
schema-dynamic** op whose real fields the connection decides (Jira create-issue
and friends) — a generic list usually has no connection-specific input fields at
all, so preparing one resolves nothing and costs a round trip.

Reach for it here only when a field you need is genuinely missing, and know what
it changes. The two namespaces differ: the library calls this `list-all-records`
and materializes it per object, while the registry serves `list-records`, so
`registry get` finds nothing under the library id and `registry prepare` reports
the connector's real action list with the closest matches first. Re-running with
the registry id succeeds — and yields a CURATED descriptor pinned to one object
(`ListAccountRecoveryEnrolledUser`), whose node type is `…list-records`. That is
a different node from the generic one you were asked for. Author the generic call
above unless you specifically want that.

### Finding the object id for a Generic operation

`--object` takes the connection's **API** name (`acr_user`), not its display
name. Filter the catalog server-side — a real tenant has tens of thousands of
objects, and paging them client-side is what makes this expensive:

```bash
# By API name, when the task names it outright.
uip is resources list <connector-key> --connection-id <id> \
  --output-filter "[?Name=='acr_user']" --output json
# By human label, when the task only gives you that. `lower()` is available.
uip is resources list <connector-key> --connection-id <id> \
  --output-filter "[?contains(lower(DisplayName),'account recovery')]" --output json
```

Each row is `{Name, DisplayName, Path, Type, SubType, Custom, ElementKey}` —
`Name` is what `--object` wants. To see one object's parameters for a single
operation without preparing it:

```bash
uip is resources describe <connector-key> <object> --connection-id <id> \
  --operation List --output json
```

## Structured filters (CEQL)

An Integration Service list operation takes a server-side filter through a
FilterBuilder parameter — usually `where`, sometimes `q`. **Write the CEQL
string; the SDK derives the tree.**

```ts
connector('uipath-microsoft-azureactivedirectory', 'list-groups',
  { where: "displayName = 'active' AND createdDateTime >= '2026-01-01T00:00:00Z'" },
  { connection: 'entra', folder: 'shared' })
```

That emits BOTH halves the artifact must carry: the runtime query at
`inputs.detail.queryParameters.where`, and the design-time tree at
`essentialConfiguration.savedFilterTrees.where` inside the node's
`configuration`. Studio Web renders the FilterBuilder from the tree; product
validation rejects a filter that has only one of the two, so a string alone
fails `validate` even though the run would have worked.

If the task also asks for the filter tree as a separate review artifact,
compile first and copy the emitted
`configuration.essentialConfiguration.savedFilterTrees.<parameter>` value
verbatim into that file (directly or under a named top-level property). Do not
replace it with an ad hoc `{ field, operator, value }` object or only the CEQL
string. The serialized tree must retain its numeric `groupOperator` and
`filters` array.

Supported: `=` `!=` `<` `<=` `>` `>=`, `Contains`, `Starts With`, `Ends With`,
`Like`, their `Not` forms, and `Is Null` / `Is Not Null`. Combine with `AND` or
`OR`, and parenthesise to nest — `(a = 1 OR b = 2) AND c = 'x'`. Mixing `AND`
and `OR` at one level is refused rather than guessed, because a tree carries one
operator per level.

Three spellings are compile errors here rather than a tenant-side
`[102003] Integration Services bad request`:

| Wrong | Why | Right |
|---|---|---|
| `'accountNumber' = 'ACC123'` | a quoted token is a VALUE to CEQL | `accountNumber = 'ACC123'` |
| `accountNumber = "ACC123"` | double quotes mark a COLUMN reference | `accountNumber = 'ACC123'` |
| `status eq 'Open'` | `eq`/`ne`/`gt`/`ge`/`lt`/`le` are OData | `status = 'Open'` |

**A filter built from a runtime value keeps the runtime half only.** The tree
holds literals, so a `js` template in `where` emits the query and no tree — which
`validate` rejects. Where the filter must vary per run, filter server-side on
what is constant and narrow the rest downstream, or accept the design-time gap
deliberately.

## Schema-dynamic operations: the parent-field loop

A connection alone does not resolve these operations. Their real field set is a
function of the **values** of a few *parent* fields, so the same operation on the
same connection has many different shapes. Measured on one live Jira tenant,
`create-issue`:

| parent values | fields |
| --- | --- |
| none | **2** — just the parents themselves |
| project `IN` + issue type `Task` | **19** |
| project `IN` + issue type `Epic` | **22**, a different set |
| project `AP` + issue type `Task` | **15** |

Both dimensions matter independently, and `fields.summary` — *required* — appears
in none of the snapshot's static inputs.

**Two ways to get this wrong, and only one of them is loud.**

*Naming too few parents is refused*, clearly:

```
Result:  Failure
Message: No api-type ObjectAction matched for fields [fields.project.key]
         on operation 'Create'
```

*Naming them all but passing a value the connection does not have is not.* The
shape is accepted, the describe succeeds, and it resolves to exactly the parent
fields again — the same 2-field answer as passing no `-f` at all, with no error.
Treat "I passed `-f` and still got only the parents" as a wrong value, never as
"this operation has no other inputs." `registry prepare` fails on both cases
rather than writing the overlay.

**1. Find the parents.** Describe with no values and read the reference block of
each input. A parent is any input whose `Reference.Path` contains a
`{placeholder}` naming another field:

```bash
uip is resources describe <connector-key> <object> \
  --connection-id <connection-id> --operation <Operation> --output json
```

```jsonc
{ "Name": "fields.issuetype.id",
  "Reference": { "ObjectName": "project",
                 "Path": "/project/{fields.project.key}/issuetypes" } }
```

That placeholder is also the **ordering**: resolve `fields.project.key` before
you can resolve `fields.issuetype.id`.

**A second declaration shape has no placeholder.** Data Service
(`uipath-uipath-dataservice`) operations such as `create-entity-record`,
`update-entity-record` and the file-record-field operations declare their parent
through the registry's schema action (`GenerateSchema` over `entityName`), not
through a reference path. Their describe with no values returns only the static
inputs (`entityName`, `expansionLevel`) — not one field of the entity — so
`compile` refuses `title`, `description`, … as unknown. `prepare` names the
parent when you omit it; the fix is always the entity name:

```bash
npx flow-sdk registry prepare uipath-uipath-dataservice create-entity-record \
  -f entityName=FlowCodeEvalEntity
# → 8 input field(s): entityName, expansionLevel + the entity's own fields
```

Do not work around the refusal — not with `rawNode`, not by editing the emitted
`.flow`, not by hand-writing a `connectors-local/` overlay. Each produces a node
the platform cannot run.

Parent-field names are operation-specific. Copy each `Name` exactly from this
operation's describe response; do not reuse the dotted names from the
`create-issue` example for another action (for example, Jira `get-issue` uses
`project` and `issuetype`).

**2. Resolve a value for each, outermost first.** Match the collection on
`Reference.Path`, *not* on `Reference.ObjectName` — `ObjectName` is often the
root resource shared by several fields (both Jira parents above report
`project`), and the sub-collection the path names may not be a listable object at
all. When it is not, find the object whose own path covers it:

```bash
uip is resources list <connector-key> --connection-id <connection-id> --output json   # find the object
uip is resources describe <connector-key> <object> --connection-id <connection-id>    # confirm its Path
uip is resources run list <connector-key> <object> --connection-id <connection-id> \
  --query "<path-param>=<value-from-the-previous-parent>" --output json
```

For Jira, `/project/{key}/issuetypes` has no object of its own; `project_statuses`
(`/project/{projectIdOrKey}/statuses`) covers it and returns the ids.

**3. Prepare with every parent.** Pass them all as `-f NAME=VALUE`:

```bash
npx flow-sdk registry prepare <connector-key> <action> \
  -f fields.project.key=IN -f fields.issuetype.id=10620
```

`prepare` quotes the service's rejection, and separately fails when the
values were accepted but resolved to nothing beyond the parents — so both
mistakes surface here rather than as a puzzling compile error later.

**Values are parent-scoped and non-portable.** A Jira issue-type id is valid only
inside its project (`Task` is `10620` in `IN` and `10005` in `AP`), so ids cannot
be copied between projects, connections, or tasks — resolve them against the
connection the flow actually binds. The materialized field set is likewise
tenant-specific: custom fields captured from one connection
(`fields.storyPointEstimate_Customfield10016`) may not exist on another at deploy.
Standard fields (`summary`, `description`) are portable.

The command prints the generated descriptor import and `connector(...)` call.
Use that descriptor directly: it carries the connection-resolved operation and
object identity even when the live action id differs from the baked catalog.
The `connectors-local/` overlay is authoring input; emitted Flow is self-contained.
Prefer curated operations for their stable contract. Use the connector's raw
`*-http-request` operation only for raw/generic needs the curated surface lacks.

File uploads are multipart Flow inputs. If the static catalog omits an upload
field, prepare the operation against its connection, then pass the upstream file
like any other connector input:

```ts
.step('upload', connector(SendFileToChannel, {
  file: out('download', 'Response'),
  channels: channelId,
  send_as: 'user',
}, { connection: 'slack', folder: 'shared' }))
```

The compiler emits the product's `multipartParameters` envelope. This is a Flow
artifact transport; the separate `uip is resources run` command does not expose
a multipart flag and is not the execution surface for this wiring.

Preparation requires a working live connection. When a task explicitly uses
offline/validate-only evidence and does not require connection-specific fields,
use the baked descriptor with its published static inputs; do not run discovery
with a placeholder connection or invent fields that were not measured. If the
published input list is empty, pass `{}`; offline evidence then proves operation
identity and control-flow routing, not the provider payload or dispatch.

[`bindings.json`](bindings.md) names symbolic connection/folder bindings used by
the source. Its reference defines the schema, compile-time resolution rules,
and boundary with emitted-artifact bindings. Populate its resource keys from
the live connection and folder listings. A plausible GUID is not proof that a
resource exists or belongs to the intended tenant; resource refresh and product
debug are the evidence.

## Resolving connection-scoped reference values

Fields such as Slack channels and mailbox folders store ids, not display names.

**If a field is marked LOOKUP, do not guess it and do not resolve it by hand.**
Use the field's helper and record the value once with `prepare`. This one rule
covers 1,071 fields across 104 connectors, so it is worth knowing before any
particular connector is:

```ts
channel: lookup(SendMessageToUser, 'channel').byEmail('dustin@example.com')
```

```bash
npx flow-sdk registry prepare uipath-salesforce-slack send-message-to-user \
  --resolve channel:profile.email=dustin@example.com
```

**You do not need to find the connection first.** `prepare` discovers it from
`uip is connections list` — your own folder first, the tenant second — and writes
both the connection id AND its folder key into `bindings.json`. So one command
covers the lookup, the connection binding and the folder binding. Pass
`--connection <name>` only when several connections match the same connector;
it reports the candidates rather than guessing, because connections for one
connector are not interchangeable.

`check` names the exact command when a lookup is unresolved, and warns when a
lookup field is given a literal id. It also speaks up when a lookup field is
bound to a runtime expression (`LOOKUP_RUNTIME_VALUE`): a warning that states
the id the field sends (`reporter.accountId`, not a name), and an error when
the expression reads an e-mail field into a lookup that neither sends nor
searches by e-mail — there an address is never that id, and the provider
refuses it only once the flow runs. (A field that sends an e-mail, such as
SendGrid's `from`, takes one silently.) A required lookup field you have no
value for is resolved with its helper, not filled from a look-alike input. Run
`check` before compiling: it finds everything else that is wrong first, so the
one expensive call is spent last.

Each operation's markdown page lists its lookup fields, the helper for each, and
what it can be searched by. The generated descriptor carries the same facts as a
comment above the `export const`, so `grep -B6 'export const SendMessageToUser'`
answers it too.

Two cases have **no** helper on purpose, and for them a plain string is correct:
a field whose `reference` merely enumerates legal values (what you send back is
what you searched for), and a collection that is the same in every tenant
(country lists, timezones). Their pages say so and print the command that shows
the accepted values.

The rest of this section is the manual route — needed only when a field carries
no lookup, or when you are inspecting a collection rather than resolving a value.
Resolve against the same connection the flow binds, never by copying an id from
another connection or session:

**Choose the collection from the prepared action definition before the first
`resources run list` call.** Run `registry prepare` first and find the target
input's `reference` block in its generated `connectors-local/*.v1def.json`.
`reference.path` is the contract — it names the exact collection, and any
`{placeholder}` in it names a field whose value must be resolved first.
`reference.objectName` is only a starting point: it is frequently the shared root
resource (several Jira inputs report `project` while their paths differ), so it
cannot by itself identify the collection.

Use `objectName` as `<object-name>` below **only when** `uip is resources
describe <connector-key> <objectName>` reports a `Path` matching
`reference.path`. When it does not — a sub-collection often has no listable
object of its own — find the object whose declared `Path` covers
`reference.path` and use that, passing the placeholder as a `--query` parameter.
Do not substitute a similar generic collection on name resemblance alone: two
collections can return the same records while only the one on `reference.path`
is the action's contract.

```bash
uip is resources run list <connector-key> <object-name> \
  --connection-id <connection-id> \
  --output-filter '{items:items[].{Id:Id,Name:Name},page:Pagination.{HasMore:HasMore,NextPageToken:NextPageToken}}' \
  --output json
```

`--output-filter` selects from `Data`; list responses place both `items` and
`Pagination` there. Replace `Id` and `Name` with the exact id/display fields in
the prepared reference contract. Keep the page fields in the same projection
so a match read does not need a second `cat`/`jq` pass.

When `Data.Pagination.HasMore` is `"true"`, keep the operation and connection
unchanged and pass `Data.Pagination.NextPageToken` as `nextPage` on the next
call:

```bash
uip is resources run list <connector-key> <object-name> \
  --connection-id <connection-id> \
  --query "nextPage=<value-from-NextPageToken>" \
  --output-filter '{items:items[].{Id:Id,Name:Name},page:Pagination.{HasMore:HasMore,NextPageToken:NextPageToken}}' \
  --output json
```

Stop early when the target record appears. Otherwise continue until
`Data.Pagination.HasMore` is `"false"`; a first-page miss is not evidence that
the record does not exist. The parameter name is `nextPage`, not
`nextPageToken`.

## Response judgments

A get-by-id not-found is a service error. Add `.onError(...)` when the scenario
wants a not-found answer; otherwise failing loud can be intentional.

For a response with no declared fields, read the whole output into a script
local before inspecting service-specific properties:

```ts
.step('report', script({ code: `
  const issue = $vars.issue.output;
  return { key: issue.key, status: issue.fields.status.name };
` }))
```

Every measured list operation has returned the bare array, so prefer that shape
for an unmeasured list too, while allowing live evidence to disprove it. Add a
new measurement to the list-envelope ledger when product debug shows a genuine
wrapper. One call is one page; use the operation's filtering/paging inputs when
the business operation needs a narrower or later page.

## Scenario and evidence boundary

Include every input named by the scenario even when the provider schema marks
it optional. Replay proves values are threaded. Integration Service live mode
proves the connector dispatch and service response. Only product Flow debug
proves the deployed runtime can resolve the emitted bindings and execute the
whole graph.

Generated descriptors provide a typed alternative: `connector(CreateIssue, inputs, opts)`.
Use `opts.object` to disambiguate a generic operation covering several objects.

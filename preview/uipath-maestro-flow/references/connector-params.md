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

## Discovering operations and fields

`$FLOW_SDK_LIBRARY_MD` (markdown, for reading) and `$FLOW_SDK_LIBRARY_JSON`
(machine-readable, for compiling) point at a **separately staged** connector
library. It is not part of the npm package and there is no default: if the
variables are unset, the library is not on this machine, so search the paths
your environment provides and pass `--library <dir>` explicitly.

Search that library for static contracts:

```bash
jq '.entries[] | select(.label | test("send email"; "i")) | {label,nodeType,path}' \
  "$FLOW_SDK_LIBRARY_MD/index.json"
sed -n '1,220p' "$FLOW_SDK_LIBRARY_MD/<path-from-index>"
```

When a connection-specific field is absent, materialize the live schema rather
than guessing or hand-editing the emitted Flow. `prepare-connector` is an
authoring tool **provided by the environment**, not by the npm package — it
needs a live Integration Service connection. If it is not on `PATH`, this route
is unavailable; fall back to the curated operation in the markdown library.

```bash
prepare-connector <connector-key> <action> \
  --connection-id <connection-id>
# Generic operation: materialize the one connected object the task uses.
prepare-connector <connector-key> <action> \
  --connection-id <connection-id> --object <api-object-name>
# Use --all-objects only when the task truly needs the full connected catalog.
```

For many connectors that first command is **not enough on its own** — see the
parent-field loop below before concluding a field does not exist.

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
"this operation has no other inputs." `prepare-connector` fails on both cases
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
prepare-connector <connector-key> <action> --connection-id <connection-id> \
  -f fields.project.key=IN -f fields.issuetype.id=10620
```

`prepare-connector` quotes the service's rejection, and separately fails when the
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
Resolve them against the same connection the flow binds instead of copying an id
from another connection or session:

**Choose the collection from the prepared action definition before the first
`resources run list` call.** Run `prepare-connector` first and find the target
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

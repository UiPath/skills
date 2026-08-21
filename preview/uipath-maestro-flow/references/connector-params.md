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
`resources run list` call.** Run `prepare-connector` first, find the target
input's `reference` block in its generated `connectors-local/*.v1def.json`, and
use the collection segment of `reference.objectName` (the part before `?`) as
`<object-name>` below. Confirm it against `reference.path`. Do not guess or
substitute a similar generic collection: two collections can return the same
records while only the declared reference collection is the action's contract.

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

# Symbolic connector bindings

`bindings.json` maps the short connection and folder names in authored
TypeScript to tenant resource keys. Keep it at the project root beside the
`<Name>.flow.ts` file.

## Project layout

```text
<Name>.flow.ts
bindings.json
connectors-local/
  <connector-key>.ts
  descriptors/
    <connector-key>/
      index.json
      ...generated descriptor data...
```

`npx flow-sdk registry prepare` prints the import for
`connectors-local/<connector-key>.ts`.
The generated descriptor data lives below `connectors-local/descriptors/`; do
not import it directly. `bindings.json` stays at the root and is independent of
that descriptor overlay.

## Schema

Use `schemaVersion: "1"` and a `bindings` array. Version `1` is the current
authored-file format marker. The current loader does not branch on this value,
but including it keeps the file explicit and compatible with shipped examples.

Each connector entry should carry the complete shape below. Resolution needs a
matching `name` or `id` and a `resourceKey` or `default`; the other fields keep
the resource kind and emitted binding purpose explicit.

| Field | Required for resolution | Meaning |
|---|:---:|---|
| `id` | one of `id` / `name` | Stable binding identifier; may be used as the symbolic source name. |
| `name` | one of `id` / `name` | Symbolic name normally passed to `connection` or `folder`. |
| `resource` | no | `"Connection"` for Integration Service connection and folder entries. |
| `resourceKey` | one of `resourceKey` / `default` | Tenant connection id or folder key. This value wins when both value fields exist. |
| `default` | one of `resourceKey` / `default` | Fallback when `resourceKey` is absent. Shipped examples repeat the resource key here. |
| `propertyAttribute` | no | `"ConnectionId"` for a connection or `"FolderKey"` for a folder. |

## Where both values come from

**Usually you do not fill these in at all.**
`npx flow-sdk registry prepare <connector-key> <action>` discovers the connection and writes both entries into `bindings.json` for you — see [connector-params.md](connector-params.md#resolving-connection-scoped-reference-values).
Reach for the manual route below only when you are authoring bindings without
running `prepare`.

If you are doing it by hand: `uip is connections list` returns the connection id
**and its folder key** on the same record, so one call answers both:

```bash
uip is connections list --output json
```

```text
{
  "Name": "dustin.metzgar",
  "Id": "c03a1967-f702-47d2-9ede-917aed159805",
  "Folder": "dustin.metzgar@uipath.com's workspace",
  "FolderKey": "b53217ce-25b2-46cd-a6b0-b73c6ba5894c",
  "ConnectorKey": "uipath-salesforce-slack",
  "State": "Enabled"
}
```

`Id` is the connection binding's `resourceKey`; **`FolderKey` is the folder
binding's**. Add `--all-folders` if the connection you want is not in the
default listing.

**Do not go looking in Orchestrator for the folder.** `uip or folders list` is a
different resource with different keys, and a folder binding wants the one the
CONNECTION lives in — which you already have. Measured on the eval corpus: an
agent that had already listed the connection went on to spend three to four
further calls on `uip or --help`, `uip or folders --help` and `folders list`,
searching for a folder matching the symbolic name in its prompt. The symbolic
name (`slack`, `shared`) is just the label you pass to `connector()`; it is never
something to search the tenant for.

Copy this two-connector, one-folder example and replace all three placeholders
with values from the connection listing above:

```json
{
  "schemaVersion": "1",
  "bindings": [
    {
      "id": "slack",
      "name": "slack",
      "resource": "Connection",
      "resourceKey": "<slack-connection-id>",
      "default": "<slack-connection-id>",
      "propertyAttribute": "ConnectionId"
    },
    {
      "id": "jira",
      "name": "jira",
      "resource": "Connection",
      "resourceKey": "<jira-connection-id>",
      "default": "<jira-connection-id>",
      "propertyAttribute": "ConnectionId"
    },
    {
      "id": "shared",
      "name": "shared",
      "resource": "Connection",
      "resourceKey": "<folder-key>",
      "default": "<folder-key>",
      "propertyAttribute": "FolderKey"
    }
  ]
}
```

Use unique `id` and `name` values. The resolver takes the first entry whose
`name` or `id` matches the authored symbol.

## Resolution and precedence

The compile commands load `--bindings <file>` when supplied. Otherwise they
load `./bindings.json` from the current directory when it exists. `emitFlow()`
uses the same current-directory default unless `bindingsFile` or a `Bindings`
instance is supplied.

```ts
.step('notify', connector(SendMessage, {
  channel: 'C123',
  text: 'Ready',
}, { connection: 'slack', folder: 'shared' }))
```

During emission, `connection: 'slack'` matches the entry whose `name` or `id`
is `slack`; `folder: 'shared'` is resolved the same way. For each match,
`resourceKey` wins over `default`. An unmatched symbol is emitted unchanged, so
do not treat a successful compile as proof that an invented id exists.

Only compile/emission reads the authored file. `uip maestro flow validate`,
solution resource refresh, and product debug read the emitted `.flow`, not the
root `bindings.json`. A compile regenerates the artifact from the authored
mapping. A later direct edit to the artifact remains in effect only until the
next compile.

## Emitted-artifact bindings

`uip maestro flow binding add` edits bindings inside an already emitted `.flow`;
it does not create or update the symbolic root file. SDK-authored Integration
Service actions and managed HTTP nodes should instead keep symbolic names in
source plus `bindings.json`, so recompilation deterministically restores the
same node detail and product bindings. Use direct artifact edits only for a
brownfield `.flow` with no source representation.

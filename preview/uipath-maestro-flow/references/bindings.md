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

`prepare-connector` prints the import for `connectors-local/<connector-key>.ts`.
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

Copy this two-connector, one-folder example and replace all three placeholders
with values from the live connection listing:

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

`uip maestro flow binding add` edits bindings inside an already emitted `.flow`.
It does not create or update the symbolic root file. This distinction matters
for managed HTTP: it has no authored connector symbol, but product debug still
needs its connection and folder bindings added to the artifact as described in
[the CLI loop](CLI-LOOP.md#product-validation-and-conditional-bindings).

If a workflow requires `binding add`, run it after the final compile because
re-emission replaces the artifact. For Integration Service connector source,
keep using symbolic names plus `bindings.json`; do not substitute artifact edits
for the authored mapping.

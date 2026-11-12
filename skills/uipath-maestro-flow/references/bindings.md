# Symbolic connector bindings

`.flow-sdk/bindings.json` maps authored TypeScript connection and folder names to tenant resource keys beside `<Name>.flow.ts` in the SDK work directory.

## Project layout

```text
.flow-sdk/
  <Name>.flow.ts
  bindings.json
  connectors/
    <connector-key>.ts
  connectors-local/
    <connector-key>.ts
    descriptors/
      <connector-key>/
        index.json
        ...generated descriptor data...
```

Run `uip maestro registry prepare` to write `.flow-sdk/bindings.json` and print the source-relative import for `./connectors-local/<connector-key>.ts`. Generated descriptor data is under `connectors-local/descriptors/`; do not import it directly. `bindings.json` is independent of that overlay. Studio Web reads neither; `uip solution pack` and `upload` omit `.flow-sdk/`.

## Schema

Use `schemaVersion: "1"` and a `bindings` array. Version `1` is the current authored-file format marker; the current loader does not branch on it, but it keeps the file explicit and compatible with shipped examples.

Each connector entry should carry the complete shape below. Each entry resolves when a matching `name` or `id` and a `resourceKey` or `default` exist; the other fields identify resource kind and purpose.

| Field | Required for resolution | Meaning |
|---|:---:|---|
| `id` | one of `id` / `name` | Stable binding identifier; may be the symbolic source name. |
| `name` | one of `id` / `name` | Symbol passed to `connection` or `folder`. |
| `resource` | no | Use `"Connection"` for Integration Service connection and folder entries. |
| `resourceKey` | one of `resourceKey` / `default` | Tenant connection id or folder key; wins when both value fields exist. |
| `default` | one of `resourceKey` / `default` | Fallback when `resourceKey` is absent; shipped examples repeat the resource key here. |
| `propertyAttribute` | no | Use `"ConnectionId"` for a connection and `"FolderKey"` for a folder. |

## Where both values come from

Usually do not fill values manually. Run `uip maestro registry prepare <connector-key> --action <action>` to discover the connection and write both entries; see [connector-params.md](connector-params.md#resolving-connection-scoped-reference-values). Use the manual route only without `prepare`.

If you are doing it by hand: `uip is connections list --all-folders` returns the
connection id **and its folder key** on the same record, so one call answers both.
Always pass `--all-folders`: the default listing is your own folder only, and a
connection shared from another folder (the usual case on a team tenant) is
invisible without it — an empty or unrelated default listing is not evidence
that the connection does not exist.

```bash
uip is connections list --all-folders --output json
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

The connection `Id` is the connection binding's `resourceKey`; `FolderKey` is the folder binding's. Never invent a GUID or use the binding's name.

`compile` refuses a binding whose `resourceKey` is its own name (`BINDING_SELF_NAME`) and a `connection:` / `folder:` label that an entries-containing `bindings.json` does not declare (`BINDING_UNDECLARED`; e.g. source `mySlack` versus declared `slack` and `shared`). `check` reports both first. It warns `CONNECTION_STUB` for an all-zero GUID, an `<angle-bracket>` placeholder, any other non-GUID value, or a label when no `bindings.json` is loaded or it has no entries. Such a run faults at dispatch with `'Connection' has an invalid GUID value` or `401 Invalid Organization or User secret`. A plausible but wrong GUID compiles and faults at run time; use only an id read from the tenant.

If several connections share a name, run `prepare … --connection <name>`; it lists candidates with `--connection-id <id>` and folders. Pass the id in the intended folder; `prepare` still writes both entries.

`prepare` binds one connection from your folder, `--connection-folder`, or the solution record, and prints `connection: <Name> (<id>)` plus the reason. When it refuses with several candidates, ask a user who can answer. Headless, pass `--connection-folder` for the folder the request names. With no folder named, or when that refuses (no match or several), pass the first candidate line's `--connection-id`: that connection is guessed. Do not debug on it, report the flow unverified, and list the pick under Open questions as **[REQUIRED]** ([completion output](author.md#completion-output)).

`Folder` is the folder's own name, not its path. For `Shared/uipath-maestro-flow`, use the row whose `Folder` is `uipath-maestro-flow`; pass `--connection-folder uipath-maestro-flow` to `prepare`, or select that row manually. If that name matches multiple connector rows, run `uip or folders get "Shared/uipath-maestro-flow" --output json`, obtain `Data.Key`, then pass `--connection-folder <Key>` or select the row whose `FolderKey` equals it.

**Do not go looking in Orchestrator for the folder** beyond that one `folders get`. The folder binding uses the folder containing the CONNECTION, which the connection listing provides. Measured on the eval corpus: an agent that had already listed the connection spent three to four further calls on `uip or --help`, `uip or folders --help` and `folders list`, searching for a folder matching the symbolic name in its prompt. The symbolic name (`slack`, `shared`) is only the label passed to `connector()` and is never a tenant search target.

Use unique `id` and `name` values. Copy this two-connector, one-folder example and replace all three placeholders with values from the connection listing above:

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

The resolver uses the first entry whose `name` or `id` matches the authored symbol. Give `connection:` and `folder:` different labels (`slack` / `shared`). If they share one label, `prepare` writes one `FolderKey` entry, the connection resolves to the folder key, and the run faults `401 Invalid Organization or User secret`, although `check`, `compile` and `validate` pass. An emitted node whose `connectionId` equals its `connectionFolderKey` proves the collision: rename the `folder:` label and re-run `prepare`.

## Resolution and precedence

Compile commands load `--bindings <file>` when supplied; otherwise load `.flow-sdk/bindings.json` under the current directory if present. A pre-`.flow-sdk/` workspace with only root `./bindings.json` continues using that file. If both exist, `.flow-sdk/` wins and stderr names the ignored root file. `emitFlow()` follows the same default unless `bindingsFile` or a `Bindings` instance is supplied.

```ts
.step('notify', connector(SendMessage, {
  channel: 'C123',
  text: 'Ready',
}, { connection: 'slack', folder: 'shared' }))
```

During emission, each `connection` or `folder` symbol matches `name` or `id`; `resourceKey` wins over `default`. An unmatched symbol is emitted unchanged, so successful compilation does not prove an invented id exists.

Only compile/emission reads the authored file. `uip maestro flow validate`, solution resource refresh, and product debug read the emitted `.flow`, not `.flow-sdk/bindings.json`. Compilation regenerates the artifact from the authored mapping; a direct artifact edit lasts only until the next compile.

## Emitted-artifact bindings

`uip maestro flow binding add` edits bindings inside an emitted `.flow`; it does not create or update `.flow-sdk/bindings.json`. SDK-authored Integration Service actions and managed HTTP nodes should keep symbolic names in source plus `bindings.json`, so recompilation deterministically restores node detail and product bindings. Use direct artifact edits only for a brownfield `.flow` with no source representation.

# External agent and automation

An agent or automation hosted outside UiPath (CrewAI, Snowflake Cortex, Salesforce Agentforce, Power Automate) is a connector node: identify it by its node type, `uipath.connector.<connector-key>.<operation>`. The registry's `Category` (`external-agent` / `external-workflow`) is only a hint; a tenant may list the node as `connector`. It runs on a connection of that connector.

## Find it

```bash
uip maestro flow registry search '<agent or connector name>' --output json   # the uipath.connector.<key>.<operation> node type
uip maestro registry search '<agent or connector name>' --output json        # is it in the SDK connector library?
uip is connections list <connector-key> --all-folders --output json           # an enabled connection and its FolderKey
```

Search a short name (`'Cortex'`, not `'Snowflake Cortex'`): a full product name can match only a connector's HTTP-request tool.

- **In the connector library** (Snowflake Cortex is): author it with `connector(...)` like any connector ([connector-params.md](connector-params.md)).
- **Not in the library** (CrewAI returns `"total": 0`): build it with the product CLI, below. `rawNode` is not an option for a `uipath.connector.*` type. Build the whole flow that holds it with the CLI too, from `flow init <Name>` (no `--sdk-source`), and give it no SDK source: `compile` from SDK source rewrites the `.flow`.

## Build it with the product CLI

```bash
uip maestro flow registry get <node-type> --output json        # method and path: connectorMethodInfo; objectName for describe
uip is resources describe <connector-key> <objectName> --operation Create --connection-id <id> --output json
uip maestro flow nodes create <Name>/<Name>.flow <node-type> --label "<label>" --position <x>,<y> --output json
uip maestro flow nodes configure <Name>/<Name>.flow <node-id> --detail '{"connectionId":"<id>","folderKey":"<folder-key>","method":"POST","endpoint":"<path>","bodyParameters":{"<field>":"<value>"}}' --output json
uip maestro flow edges create <Name>/<Name>.flow <source-node-id> <node-id> --output json
uip maestro flow validate <Name>/<Name>.flow --output json
```

- Required inputs are the `RequestFields` with `Required: true` from `is resources describe`; `registry get` may not list them (CrewAI's `inputs.email_content`). Keep a dotted field name as one key: `"inputs.email_content": "..."`.
- Use the node id `nodes create` returns; it is not derived from the operation name.
- Agent nodes are Curated activities, so `--detail` takes no `objectName`; only Generic activities need one.
- The node definition from the registry may say `Intsvc.AsyncAgentExecution` even for a sync agent (Snowflake Cortex on alpha, 2026-10-19). The flow still ran it as sync, from `executionType: sync` in the configured detail. Leave the service type as the CLI wrote it.
- Then `uip solution resources refresh` and `uip maestro flow debug <Name>` ([CLI-LOOP.md](CLI-LOOP.md)).

# External agent and automation

An agent or automation hosted outside UiPath (CrewAI, Snowflake Cortex, Salesforce Agentforce, Power Automate) is a connector node whose registry category is `external-agent` or `external-workflow`. Its node type is `uipath.connector.<connector-key>.<operation>`, and it runs on a connection of that connector.

## Find it

```bash
uip maestro flow registry search '<agent or connector name>' --output json   # Category external-agent / external-workflow
uip maestro registry search '<agent or connector name>'                      # is it in the SDK connector library?
uip is connections list <connector-key> --all-folders --output json           # an enabled connection and its FolderKey
```

- **In the connector library** (Snowflake Cortex is): author it with `connector(...)` like any connector ([connector-params.md](connector-params.md)).
- **Not in the library** (CrewAI returns `"total": 0`): build it on a `.flow` with the product CLI, below. `rawNode` is not an option for a `uipath.connector.*` type. `compile` from SDK source rewrites the `.flow`, so give these nodes a flow of their own, made with `flow init <Name>` (no `--sdk-source`).

## Build it with the product CLI

```bash
uip maestro flow registry get <node-type> --output json        # method and path: connectorMethodInfo; objectName
uip is resources describe <connector-key> <objectName> --operation Create --connection-id <id> --output json
uip maestro flow nodes create <Name>/<Name>.flow <node-type> --label "<label>" --position <x>,<y> --output json
uip maestro flow nodes configure <Name>/<Name>.flow <node-id> --detail '{"connectionId":"<id>","folderKey":"<folder-key>","method":"POST","endpoint":"<path>","bodyParameters":{"<field>":"<value>"}}' --output json
uip maestro flow edges create <Name>/<Name>.flow <source-node-id> <node-id> --output json
uip maestro flow validate <Name>/<Name>.flow --output json
```

- Required inputs are the `RequestFields` with `Required: true` from `is resources describe`; `registry get` may not list them (CrewAI's `inputs.email_content`). Keep a dotted field name as one key: `"inputs.email_content": "..."`.
- Use the node id `nodes create` returns; it is not derived from the operation name.
- The `.flow` stores `Intsvc.AsyncAgentExecution` for every agent node. A sync agent (`executionType: sync` in the configured detail) still runs as sync. Do not edit the service type.
- Then `uip solution resources refresh` and `uip maestro flow debug <Name>` ([CLI-LOOP.md](CLI-LOOP.md)). A `500` at `prepare-custom-debug` is transient: retry once.

# External agent and automation

An agent or automation hosted outside UiPath (CrewAI, Snowflake Cortex, Salesforce Agentforce, Power Automate) is a connector node: identify it by its node type, `uipath.connector.<connector-key>.<operation>`. The registry's `Category` (`external-agent` / `external-workflow`) is only a hint; a tenant may list the node as `connector`. It runs on a connection of that connector.

## Find it

```bash
uip maestro flow registry search '<agent or connector name>' --output json   # the uipath.connector.<key>.<operation> node type
uip maestro registry search '<agent or connector name>' --output json        # is it in the connector library, or the tenant's catalog when none was pulled?
uip is connections list <connector-key> --all-folders --output json           # an enabled connection and its FolderKey
```

Search a short name (`'Cortex'`, not `'Snowflake Cortex'`): a full product name can match only a connector's HTTP-request tool.

- **In the connector library** (Snowflake Cortex is): author it with `connector(...)` like any connector ([connector-params.md](connector-params.md)).
- **Not in the library** (CrewAI returns `"total": 0`): prepare it, then author it with `connector(...)` like a library operation. `rawNode` is not an option for a `uipath.connector.*` type.

## Prepare it when the library lacks it

```bash
uip maestro registry prepare <connector-key> --action <operation>
```

`prepare` reads the tenant's node (`uip maestro flow registry get`) and the object's request fields (`uip is resources describe`). It writes the operation to `./.flow-sdk/connectors-local/`, adds the connection to `.flow-sdk/bindings.json`, and prints the `connector(...)` call to paste. The source in `.flow-sdk/` imports the module as `./connectors-local/<connector-key>.ts`. For example, Salesforce Agentforce's Execute Salesforce Agent:

```ts
import { ExecuteSalesforceAgent } from './connectors-local/uipath-salesforce-agent.ts';

.step('ask', connector(ExecuteSalesforceAgent, { message: { text: input('question') }, agent_id: lookup(ExecuteSalesforceAgent, 'agent_id').byDeveloperName('<agent name>') },
  { connection: 'agent', folder: 'shared' }))
```

- Required inputs are the describe's `RequestFields` with `Required: true`, and the descriptor types them as required; `registry get` may not list them (CrewAI's `inputs.email_content`). A dotted field is a nested object in the source (`inputs: { email_content: ... }`); compile writes it back as the one key `inputs.email_content`.
- A picker input such as `agent_id` is a lookup: author `lookup(...)` as above, and record its id with the `--resolve agent_id:DeveloperName=<agent name>` that `prepare` prints, rather than pasting an id ([connector-params.md](connector-params.md#resolving-connection-scoped-reference-values)).
- The node runs as the connector object says (`sync`, `async` or `hybrid`). With `@uipath/maestro-builder-sdk` 6.116.0 or later, compile writes that as `inputs.detail.executionType`, as `nodes configure` does, and the runtime picks the sync or async service type from it. Leave the definition's service type alone (`Intsvc.AsyncAgentExecution` even for a sync agent). If `prepare` warns that Integration Service reported no execution type, run `uip update` and prepare again. If it warns that an async or hybrid object names no event, the node has nothing to wait on: tell the user it may never finish. An older SDK writes no execution type, so the node runs under the definition's service type: upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
- To run it, `uip solution resources refresh` and `uip maestro flow debug <Name>` ([CLI-LOOP.md](CLI-LOOP.md)); ask first ([operate.md](operate.md#debug--a-real-end-to-end-run)).

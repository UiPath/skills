<!--skill-flavor:external-agent-cli:start-->
- **Not in the library** (CrewAI returns `"total": 0`): prepare it, then author it with `connector(...)` like a library operation, by [the connector loop in Studio Web](../SKILL.md#the-connector-loop-in-studio-web). `rawNode` is not an option for a `uipath.connector.*` type.

## Prepare it when the library lacks it

From the project folder `/solution/<Project>`, with the connection the user chose:

```bash
uip maestro registry prepare <connector-key> --action <operation> --connection-id <id>
```

`prepare` reads the tenant's node and the object's request fields, and writes `.flow-sdk/connectors-local/<connector-key>.ts`. The draft in `.flow-sdk/` imports it as `./connectors-local/<connector-key>.ts`. For example, Salesforce Agentforce's Execute Salesforce Agent:

```ts
import { ExecuteSalesforceAgent } from './connectors-local/uipath-salesforce-agent.ts';

.step('ask', connector(ExecuteSalesforceAgent, { message: { text: input('question') }, agent_id: lookup(ExecuteSalesforceAgent, 'agent_id').byDeveloperName('<agent name>') },
  { connection: 'agent', folder: 'shared' }))
```

- Required inputs are the describe's `RequestFields` with `Required: true`, and the descriptor types them as required. A dotted field such as CrewAI's `inputs.email_content` is a nested object in the source (`inputs: { email_content: ... }`).
- `agent_id` is a lookup: record its id with the `--resolve agent_id:DeveloperName=<agent name>` that `prepare` prints, rather than pasting an id.
- Compile writes the object's execution type (`sync`, `async` or `hybrid`) as `inputs.detail.executionType`, and the runtime picks the sync or async service type from it. That needs `@uipath/maestro-builder-sdk` 6.116.0 or later. Studio Web owns the SDK copy, so when the one it ships is older, tell the user the node runs under the definition's service type. Leave the definition's service type alone. If `prepare` warns that the execution type is missing or that an async object names no event, tell the user: the node may not finish when it runs.
<!--skill-flavor:external-agent-cli:end-->

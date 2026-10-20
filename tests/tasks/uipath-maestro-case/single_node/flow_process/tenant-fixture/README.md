# CaseEvalFlowFixture

The deployed flow `single_node/flow_process` starts. It must exist in the eval tenant at `Shared/CaseEvalFlowFixture`; the eval does not deploy it.

- Input `invoiceNumber` (string); output `status` (string) = `received-<invoiceNumber>`, from one script node. No connectors.
- Source: [`CaseEvalFlowFixture.flow.ts`](CaseEvalFlowFixture.flow.ts) (Flow builder SDK).

To redeploy, from an empty directory:

```bash
uip solution init "CaseEvalFlowFixture"
( cd CaseEvalFlowFixture && uip maestro flow init CaseEvalFlowFixture --sdk-source )
cp <this folder>/CaseEvalFlowFixture.flow.ts CaseEvalFlowFixture/CaseEvalFlowFixture/.flow-sdk/
( cd CaseEvalFlowFixture/CaseEvalFlowFixture && uip maestro flow compile .flow-sdk/CaseEvalFlowFixture.flow.ts -o CaseEvalFlowFixture.flow )
uip maestro flow validate CaseEvalFlowFixture/CaseEvalFlowFixture/CaseEvalFlowFixture.flow --output json
( cd CaseEvalFlowFixture && uip solution resources refresh --solution-folder . --output json )
uip solution pack CaseEvalFlowFixture out --output json
uip solution publish out/CaseEvalFlowFixture_1.0.0.zip --wait --output json
uip solution deploy run --name CaseEvalFlowFixture --package-name CaseEvalFlowFixture --package-version 1.0.0 --parent-folder-path Shared --folder-name CaseEvalFlowFixture --output json
```

`flow init` mints a new flow id; that is fine, the eval binds the flow by name and folder.

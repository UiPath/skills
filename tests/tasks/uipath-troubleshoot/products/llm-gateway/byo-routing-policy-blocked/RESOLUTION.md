# Final Resolution

Root Cause: BYO routing is being bypassed because the effective AI Trust Layer
policy blocks the BYO Azure OpenAI model/provider for this tenant. The BYO
configuration itself is enabled and points at a healthy Integration Service
connection.

Evidence:

- `uip traces spans get dddddddddddddddddddddddddddddddd --output json` shows
  the failing Agents operation group `agenthub-llm-call` invoked the platform
  default model instead of the tenant BYO Azure OpenAI model.
- `uip llm-configuration byo-connections list --include-connection-details
  --output json` shows BYO config `byo-azure-agents` is enabled for product
  `agents`, feature `agenthub-llm-call`, model `gpt-4o-enterprise`, and its
  connection state is `Enabled`.
- `uip llm-configuration byo-connections list-product-configs --product agents
  --feature agenthub-llm-call --output json` shows the feature supports the
  configured Azure OpenAI model.
- `uip gov aops-policy deployed-policy get NoLicense AITrustLayer
  00000000-0000-4000-8000-000000000100 --output json` returns an effective
  policy whose model governance rules allow platform defaults but block
  `AzureOpenAi` / `gpt-4o-enterprise`.

Immediate fix:

1. Route to the tenant governance owner. Amend the effective AI Trust Layer
   policy to allow the intended BYO provider/model, or choose a BYO target that
   is allowed by policy.
2. Re-run the same policy check with the current command shape:

   ```bash
   uip gov aops-policy deployed-policy get NoLicense AITrustLayer 00000000-0000-4000-8000-000000000100 --output json
   ```

3. Re-test the failing agent call and verify trace evidence shows the BYO model
   is invoked.

Must NOT attribute to: disabled BYO config, disabled IS connection, product
catalog drift, or missing trace evidence. Must NOT recommend a deployed-policy
resolve command.

---
confidence: medium
---

# BYO LLM Routing Bypassed

## Context

What this looks like:
- A BYO LLM product configuration is registered and `enabled: true`
- Agent / product LLM calls succeed — but trace spans show the **platform default** model / provider was invoked, not the customer's BYO key
- The customer expected vendor charges on their own account but is seeing platform charges (or vice versa)
- No validation error, no auth error — the routing simply did not pick up the BYO record

What can cause it:
- The BYO record's `enabled` field is `false` (paused but not deleted)
- The feature's `modelsConfigurationOption` is `AllModels` or `AnyModel`, the BYO config uses single-mapping shorthand, and the gateway falls back to default for any unmapped catalog model
- An AI Trust Layer policy (tenant-wide governance) blocks the chosen vendor / model and the gateway falls back to default
- The agent / product call uses a model the BYO config did not map (multi-mapping configs need one entry per catalog model)
- The call hit a feature / operation group that does NOT have a BYO record at all — only some product features support BYO

What to look for:
- Trace spans naming a different provider / model than the BYO record declares
- `enabled: false` on the BYO record
- `modelsConfigurationOption: AllModels | AnyModel` with fewer `--mapping` entries than catalog `models[]`
- An AOps `AITrustLayer` policy deployed on the tenant
- The (product, operationGroupName) on the failing trace does not match any BYO record

## Investigation

1. **Read the failing trace** — confirm which (product, model, provider) the agent actually called and which one was actually invoked:

   ```bash
   uip traces spans get <trace-id> --output json
   ```

2. **Confirm the BYO record exists for that (product, feature) and is enabled:**

   ```bash
   uip llm-configuration byo-connections list \
     --output json --output-filter "Data[?product=='<product>' && operationGroupName=='<feature>']"
   ```

   If the result is empty — there is no BYO record for this feature. The platform default is expected behavior, not a bug.
   If `enabled: false` — re-enable via `byo-connections update <id> --enabled` (or via the UI).

3. **Check feature shape — is this an `AllModels` / `AnyModel` feature with incomplete mapping?**

   ```bash
   uip llm-configuration byo-connections list-product-configs \
     --product <product> --feature <feature> --output json
   ```

   Read `modelsConfigurationOption`. If it's `AllModels` or `AnyModel`, every catalog model must have a `--mapping`. Compare the BYO record's `llmConfigurations[]` against `models[]` from the catalog — any model in `models[]` without a corresponding mapping falls back to default.

4. **Check whether AI Trust Layer policy is overriding routing:**

   ```bash
   uip gov aops-policy deployed-policy resolve \
     --product AITrustLayer --license-type <type> --tenant <name> --output json
   ```

   If a deployed policy blocks the vendor or model the BYO record references, the gateway will fall back to default. Route to [`uipath-governance`](/uipath:uipath-governance) for full AOps policy investigation.

5. **Trace identity match.** Cross-check the trace's `product` / `operationGroupName` fields against the BYO record's identity fields. A common mistake: registering BYO for `agents-design-eval-deploy` while the failing call is for `agents-design-eval-run` — different operation groups, different records.

## Resolution

- **`enabled: false`** — re-enable the BYO record:

  ```bash
  uip llm-configuration byo-connections update <id> --enabled --output json
  ```

- **`AllModels` / `AnyModel` incomplete mapping** — re-issue `update` with one `--mapping` per catalog model. `update` is full-PUT, so every mapping the customer wants in the resulting record must be supplied in the call:

  ```bash
  uip llm-configuration byo-connections update <id> \
    --mapping '...' --mapping '...' --mapping '...' --output json
  ```

- **AI Trust Layer policy override** — route to [`uipath-governance`](/uipath:uipath-governance). Either the policy needs to be amended to allow the vendor / model, or the customer needs to pick a different BYO target.

- **No BYO record for the failing feature** — register one via `byo-connections create`, or accept the platform default. See [`uipath-platform` BYO reference](/uipath:uipath-platform).

- **Cannot explain routing from current state + traces** — this is the structural ceiling of the LLM Gateway CLI. There are no per-request gateway invocation logs. Open a support ticket with the failing trace ID and the BYO config ID.

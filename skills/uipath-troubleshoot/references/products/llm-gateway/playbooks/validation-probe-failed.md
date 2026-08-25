---
confidence: medium
---

# BYO LLM Validation Probe Failing

## Context

What this looks like:
- `uip llm-configuration byo-connections create` or `update` exits non-zero with `Result: Failure`
- The error references the validation probe: `isAvailable: false`, `isCompatible: false`, or `isModelNameSimilar: false` for one or more models
- The save was aborted (server-side validation is mandatory; there is no skip flag)

What can cause it:
- The vendor key behind the IS connection does not have access to the requested model (subscription / region / deployment mismatch)
- The chosen `--api-flavor` is not supported by the model — e.g., a Bedrock-only model with `OpenAiResponses`
- The product's allowed-model catalog (`models[]` or `addYourOwn[<connector-type>]`) changed since the config was created and the saved `--llm-name` is no longer valid against preflight rules
- `--llm-identifier` (the value sent to the vendor) does not match the deployment name / inference profile ID the vendor expects — e.g., Azure OpenAI deployment names, AWS Bedrock region-prefixed inference profiles (`eu.anthropic.claude-...`)
- The IS connection itself is dead (route to [byo-connection-dead.md](./byo-connection-dead.md) first if the probe error mentions auth)

What to look for:
- Which model in the probe summary failed (multi-mapping configs return one verdict per model)
- The `Message` and `Instructions` fields on the error envelope
- Whether the failure is `isAvailable` (vendor access / key scope), `isCompatible` (model × api-flavor mismatch), or `isModelNameSimilar: false` (typo / deprecated model name)

## Investigation

1. **Pin down the failure mode.** Read the validation block in the error payload. Note which model and which probe field failed.

2. **Confirm the catalog still allows the chosen (model, connector, api-flavor) combination:**

   ```bash
   uip llm-configuration byo-connections list-product-configs \
     --product <product> --feature <feature> --output json
   ```

   For `AnyModelWithOwnAdditions` features, check `addYourOwn[<connector-type>]` for the list of allowed api-flavors when adding a custom model.
   For `AllModels` / `AnyModel` features, check the catalog `models[]` for `allowedApiFlavors` and `allowedConnectors` per model.

3. **If `isAvailable: false`** — the vendor key cannot reach the model. Verify with the vendor (does the API key have access to this deployment / model / region?). If the vendor key was recently rotated, check the IS connection state via `uip llm-configuration byo-connections get <id> --force-refresh`.

4. **If `isCompatible: false`** — the (model, api-flavor) pair is not allowed. Pick a different api-flavor from the catalog probe data.

5. **If `isModelNameSimilar: false`** — `--llm-name` is not a recognized model. Either the customer is on `AnyModelWithOwnAdditions` and the catalog needs widening, or the name is a typo / deprecated variant. Cross-check against `models[]` in the catalog response.

6. **If `--llm-identifier` differs from `--llm-name`** — confirm the deployment name / inference profile ID the vendor expects matches what was passed. Ask the user explicitly.

## Resolution

- For vendor-side access issues — fix the key scope with the vendor, then re-run `create` / `update` with the same flags. Validation will re-probe.
- For catalog drift — pick a model from the current `list-product-configs` response and re-issue the `create` / `update` with the new value. For multi-mapping (`AllModels` / `AnyModel`), every catalog model must be supplied in the call.
- For api-flavor mismatch — re-issue with an api-flavor present in the model's `allowedApiFlavors` (or `addYourOwn[<connector-type>]` for `AnyModelWithOwnAdditions`).
- For `--llm-identifier` mismatch — re-issue with the vendor's deployment name / inference profile ID, leaving `--llm-name` as the catalog name.
- There is no skip flag — every save must pass validation. If the customer needs a workaround, route to the BYO config description in [`uipath-platform`](/uipath:uipath-platform).

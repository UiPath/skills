<!--skill-flavor:connector-surface-summary:start-->
How to author an Integration Service connector activity (HTTP Request, Gmail, Outlook, GitHub, Slack, Salesforce, etc.) so it renders cleanly in Studio Web and executes through approved `RunProject`. Use `uip api-workflow registry` to resolve a keyword to an activity-type GUID and build a ready-to-paste activity object from Studio Web's TypeCache and Integration Service Elements metadata.
<!--skill-flavor:connector-surface-summary:end-->

<!--skill-flavor:host-command-scope:start-->
> **Studio Web scope:** use `registry resolve` / `stub` and read-only `uip is` discovery through the host-registered embedded CLI. Authentication comes from the active Studio Web session. Treat host-exposed connection resources and metadata as authoritative, and use freshly inspected ProxyTool schemas for resource operations.

<!--skill-flavor:host-command-scope:end-->

<!--skill-flavor:registry-auth:start-->
> The `registry` subcommand is available in Studio Web's embedded CLI with tenant authentication inherited from the active session.
<!--skill-flavor:registry-auth:end-->

<!--skill-flavor:discovery-flow:start-->
```
1. uip api-workflow registry resolve "<keyword>" --output json     -> candidate GUIDs
2. (IntSvc only) use read-only uip is list/describe/ping commands -> connector, resource, and healthy connection data
3. uip api-workflow registry stub <activity-type-id> [...] --output json -> ready-to-paste activity
4. Insert Data.Activity into /solution/<projectName>/Workflow.json; fill required fields and replace placeholders.
5. uip api-workflow validate Workflow.json --output json          -> autonomous static validation
6. State external side effects and ask for explicit consent.
7. On approval, inspect /skills/synthetic/proxy-tools-Api/SKILL.md and invoke its live RunProject schema.
```

Set `workingDirectory` to the exact target project root for project-relative commands. Treat the Studio Web resource model and host-generated metadata as authoritative.
<!--skill-flavor:discovery-flow:end-->

<!--skill-flavor:connection-remediation:start-->
Inspect filtered, unfiltered, and `--all-folders` connection listings, then select a UUID that succeeds under `ping`. When every candidate fails, ask the user to repair or create the connection through Studio Web before authoring the activity.
<!--skill-flavor:connection-remediation:end-->

<!--skill-flavor:validate-and-run:start-->
Run static validation autonomously from the target project root:

```bash
uip api-workflow validate Workflow.json --output json
```

Fix and re-validate until `Data.Status` is `Valid`. Then explain concrete vendor side effects and ask for explicit consent. On approval, inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and invoke the live `RunProject` operation with exactly its schema-declared fields. Use the actual host result as runtime evidence.
<!--skill-flavor:validate-and-run:end-->

<!--skill-flavor:required-field-cloud-validation:start-->
Before validating, run the **Required-field cross-check** above and populate every `required: true` field in `queryParameters`, `pathParameters`, or `bodyParameters`. This gives the Studio Web picker and approved host execution a complete activity shape.
<!--skill-flavor:required-field-cloud-validation:end-->

<!--skill-flavor:http-example-execution-proof:start-->
The resulting activity is compatible with Studio Web's unified HTTP Request card. Validate the workflow through the embedded static validator; after explicit consent, verify end-to-end behavior through the schema-inspected `proxy-tools-Api` / `RunProject` operation. See [../assets/templates/connector-call-example.json](../assets/templates/connector-call-example.json) for the complete stub-generated workflow.
<!--skill-flavor:http-example-execution-proof:end-->

<!--skill-flavor:resource-lookup-runtime:start-->
Well-known folder-name shortcuts such as `"inbox"`, `"sentitems"`, and `"drafts"` work for `parentFolderId`-style fields, while a real lookup-cache ID gives the Studio Web picker a friendly name. For exact UI fidelity, inspect the relevant host resource ProxyTool's live schema and use a declared read/list operation. When a host lookup capability is unavailable, explain the display limitation and ask whether the well-known shortcut is acceptable.
<!--skill-flavor:resource-lookup-runtime:end-->

<!--skill-flavor:generic-resource-runtime-diagnostic:start-->
- **Path-parameter value formats are connector-specific.** Use read-only `uip is resources describe` for the parameter description and lookup hints. When `RunProject` returns a 404, inspect a relevant host resource ProxyTool and use its schema-declared read/get operation. When the lookup capability is unavailable, report the diagnostic gap and ask whether to switch to a Curated activity or Http kind.
<!--skill-flavor:generic-resource-runtime-diagnostic:end-->

<!--skill-flavor:export-bucket-stability:start-->
- **Slot key carries the operation; export bucket carries the object name:** slot `ListUserRepos_1`, export bucket `user_repos_1` (objectName-based, like every Curated example). Copy `Data.ExportBucketKey` verbatim. After each host rewrite of `Workflow.json`, re-check that downstream `$context.outputs.<X>` reads match the on-disk `export.as` keys; runtime `undefined` results reveal dangling output references.
<!--skill-flavor:export-bucket-stability:end-->

<!--skill-flavor:runtime-content-normalization-comment:start-->
// In a JsInvoke script body, normalize content supplied as either a JSON string or a parsed value:
<!--skill-flavor:runtime-content-normalization-comment:end-->

<!--skill-flavor:solution-metadata:start-->
### Step 5 — Use Studio Web Connection and Solution Metadata

Studio Web maintains the connection and solution resource model. For additional resource operations, inspect the relevant exposed ProxyTool's live schema and pass exactly its declared fields. Report the exact host gap when the requested operation is unavailable.
<!--skill-flavor:solution-metadata:end-->

<!--skill-flavor:solution-resource-fields:start-->
### Solution Resources as Activity Fields in Studio Web

Use `--resource-key` when a live Studio Web resource capability exposes the exact key. Continue to pass the resource name through `--inputs`. When the key or resource operation is unavailable, report the exact host capability gap.
<!--skill-flavor:solution-resource-fields:end-->

<!--skill-flavor:worked-example-solution-metadata:start-->
# 5. Use Studio Web's host resource capability for connection-resource metadata.
<!--skill-flavor:worked-example-solution-metadata:end-->

<!--skill-flavor:registry-auth-limit:start-->
4. **Studio Web supplies authentication for `resolve` and `stub`.** Report a host-authentication failure with its exact result and retry after the active session or tenant state changes.
<!--skill-flavor:registry-auth-limit:end-->

<!--skill-flavor:solution-metadata-antipattern:start-->
- **Use a schema-inspected host resource capability for solution metadata and report an unavailable operation as an exact host gap.**
<!--skill-flavor:solution-metadata-antipattern:end-->

<!--skill-flavor:required-field-antipattern:start-->
- **Cross-check every stub against the resource schema.** Use `uip is resources describe <connector-key> <object-name> --operation <op> --connection-id <uuid> --output json` or the stub's `metadata.configuration.optionalConfiguration.fieldsContainer.inputFields`, then populate every `required: true` field before validation and approved host execution.
<!--skill-flavor:required-field-antipattern:end-->

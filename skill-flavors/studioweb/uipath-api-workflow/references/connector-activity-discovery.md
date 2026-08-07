<!--skill-flavor:host-command-scope:start-->
> **Studio Web scope:** run `registry resolve` / `stub` and read-only `uip is` discovery through the host-registered embedded CLI. Authentication is inherited. Do not run login, connection-edit, binding-sync, resource-refresh, local lifecycle, or solution-metadata commands, and do not edit host-owned metadata files.

<!--skill-flavor:host-command-scope:end-->

<!--skill-flavor:registry-auth:start-->
> The `registry` subcommand is already available in Studio Web's embedded CLI. Tenant authentication is inherited from the active session; do not install the CLI or run `uip login`.
<!--skill-flavor:registry-auth:end-->

<!--skill-flavor:discovery-flow:start-->
```
1. uip api-workflow registry resolve "<keyword>" --output json     -> candidate GUIDs
2. (IntSvc only) use read-only uip is list/describe/ping commands -> connector, resource, and healthy connection data
3. uip api-workflow registry stub <activity-type-id> [...] --output json -> ready-to-paste activity
4. Drop Data.Activity into /solution/<projectName>/Workflow.json; fill required fields and replace placeholders.
5. uip api-workflow validate Workflow.json --output json          -> autonomous static validation
6. State external side effects and ask for explicit consent.
7. On yes, inspect /skills/synthetic/proxy-tools-Api/SKILL.md and invoke its live RunProject schema.
```

Run project-relative commands with `workingDirectory` set to the exact project root. Do not sync bindings or write solution resource files; Studio Web owns that metadata.
<!--skill-flavor:discovery-flow:end-->

<!--skill-flavor:connection-remediation:start-->
Only after the filtered, unfiltered, and `--all-folders` listings yield no UUID that pings cleanly, stop and ask the user to repair or create the connection through Studio Web. Do not run `uip is connections edit`; it changes connection state and is outside the read-only embedded CLI scope. Never author against a connection that has not pinged successfully.
<!--skill-flavor:connection-remediation:end-->

<!--skill-flavor:validate-and-run:start-->
Then run static validation autonomously from the target project root:

```bash
uip api-workflow validate Workflow.json --output json
```

Fix and re-validate until `Data.Status` is `Valid`. Then explain concrete vendor side effects and ask for explicit consent. On "yes," inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and invoke the live `RunProject` operation with exactly its schema-declared fields. Studio Web supplies authentication automatically, so never run `uip login`; the embedded runner is unsupported and must not be used as a smoke test.
<!--skill-flavor:validate-and-run:end-->

<!--skill-flavor:http-example-execution-proof:start-->
The resulting activity is compatible with Studio Web's unified HTTP Request card. Validate the workflow through the embedded static validator; after explicit consent, verify end-to-end behavior through the schema-inspected `proxy-tools-Api` / `RunProject` operation. See [../assets/templates/connector-call-example.json](../assets/templates/connector-call-example.json) for the complete stub-generated workflow.
<!--skill-flavor:http-example-execution-proof:end-->

<!--skill-flavor:resource-lookup-runtime:start-->
Well-known folder-name shortcuts such as `"inbox"`, `"sentitems"`, and `"drafts"` work for `parentFolderId`-style fields, but the Studio Web picker shows a friendly name only for a real lookup-cache ID. For exact UI fidelity, inspect a relevant host resource ProxyTool's live schema and use only a declared read/list operation. Do not invoke a generic embedded resource runner or guess its payload. If no host lookup capability exists, explain the display limitation and ask whether the well-known shortcut is acceptable.
<!--skill-flavor:resource-lookup-runtime:end-->

<!--skill-flavor:generic-resource-runtime-diagnostic:start-->
- **Path-parameter value formats are connector-specific.** Use read-only `uip is resources describe` for the parameter description and lookup hints. If `RunProject` returns a 404, inspect a relevant host resource ProxyTool and use a schema-declared read/get operation only when it is available. If the host exposes no safe lookup, report the diagnostic gap and ask before switching to a Curated activity or Http kind; do not invoke a generic embedded resource runner.
<!--skill-flavor:generic-resource-runtime-diagnostic:end-->

<!--skill-flavor:solution-metadata:start-->
### Step 5 — Let Studio Web Own Connection and Solution Metadata

Do not run `uip api-workflow bindings sync` or `uip solution resources refresh`. Do not inspect, create, or edit `.uipx`, `bindings_v2.json`, `resources/`, or `userProfile/`. Studio Web maintains these backend entities and metadata. If a connector requires a resource operation beyond the allowed registry and read-only `uip is` discovery flow, inspect an exposed resource ProxyTool's live schema; if no suitable capability exists, report the host gap.
<!--skill-flavor:solution-metadata:end-->

<!--skill-flavor:solution-resource-fields:start-->
### Solution Resources as Activity Fields in Studio Web

Use `--resource-key` only when a live Studio Web resource capability exposes the exact key. Continue to pass the resource name through `--inputs`, but never derive the key by reading or editing solution metadata. If Studio Web exposes neither the key nor a suitable resource tool, report the capability gap instead of guessing.
<!--skill-flavor:solution-resource-fields:end-->

<!--skill-flavor:worked-example-solution-metadata:start-->
# 5. Studio Web owns connection-resource metadata; do not write a Solution/resources file.
<!--skill-flavor:worked-example-solution-metadata:end-->

<!--skill-flavor:registry-auth-limit:start-->
4. **Studio Web supplies authentication for `resolve` and `stub`.** Do not run `uip login`. A host-authentication failure is a capability blocker to report, not a cue to configure local credentials.
<!--skill-flavor:registry-auth-limit:end-->

<!--skill-flavor:solution-metadata-antipattern:start-->
- **Do NOT** run binding-sync/resource-refresh commands or write solution catalogue/debug-overwrite files in Studio Web. The host owns them; use a schema-inspected host resource capability or report that it is unavailable.
<!--skill-flavor:solution-metadata-antipattern:end-->

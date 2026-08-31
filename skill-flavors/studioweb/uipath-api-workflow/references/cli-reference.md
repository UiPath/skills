<!--skill-flavor:reference-surface-summary:start-->
Studio Web command and tool reference for authoring, static validation, approved execution, and active-solution publication. Apply the capability map below for each operation.
<!--skill-flavor:reference-surface-summary:end-->

<!--skill-flavor:host-command-scope:start-->
> **Studio Web command surface:** use the host-registered embedded CLI for `api-workflow validate`, `api-workflow registry resolve` / `stub`, read-only `uip is` discovery (`list`, `describe`, `ping`), and `uip solution publish --help` plus approved host-intercepted active-solution publication. Authentication comes from the active Studio Web session. Use consent-gated, schema-inspected `proxy-tools-Api` / `RunProject` for execution and live host schemas for project, resource, and lifecycle operations.

<!--skill-flavor:host-command-scope:end-->

<!--skill-flavor:local-project-lifecycle:start-->
## Project Creation and Lifecycle in Studio Web

Create each project from the freshly inspected `proxy-tools-Solution` / `CreateProjects` schema. After success, verify the returned `/solution/<projectName>` directory and target `/solution/<projectName>/Workflow.json`. For build or packaging requests, inspect the available Studio Web lifecycle capabilities and report the exact host gap when the requested capability is unavailable.
<!--skill-flavor:local-project-lifecycle:end-->

<!--skill-flavor:runtime-execution:start-->
## Execute an API Workflow in Studio Web

After `uip api-workflow validate Workflow.json --output json` returns `Data.Status: "Valid"`:

1. Explain the concrete external side effects and ask for explicit user consent.
2. On approval, read `/skills/synthetic/proxy-tools-Api/SKILL.md` and inspect the live `RunProject` operation schema immediately before invocation.
3. Invoke `RunProject` with exactly the fields declared by that schema for the target project.
4. Use the actual host tool result as execution evidence. Report an unavailable operation or failed result with its exact host details.
<!--skill-flavor:runtime-execution:end-->

<!--skill-flavor:registry-auth:start-->
Look up DAP / connector activities (StudioWeb TypeCache, `projectType=Api`) and emit api-workflow-shaped activity stubs. This is the Studio Web registry flow for API Workflow authoring.
Both subcommands use authentication inherited from the active Studio Web session.
<!--skill-flavor:registry-auth:end-->

<!--skill-flavor:registry-auth-remediation:start-->
<!--skill-flavor:registry-auth-remediation:end-->

<!--skill-flavor:solution-resource-key:start-->
| `--resource-key <field>=<key>` | no (repeatable) | Use the exact key exposed by a live Studio Web resource capability. Report the resource-key capability gap when that field is unavailable. |
<!--skill-flavor:solution-resource-key:end-->

<!--skill-flavor:connector-typical-sequence:start-->
### Typical Studio Web sequence

Run these commands from the target project root (`CurrentProject.AbsolutePath` for an existing open project, or `/solution/<projectName>` after `CreateProjects`):

```bash
uip api-workflow registry resolve "outlook newest email" --output json
uip is connections list uipath-microsoft-outlook365 --output json
uip is connections ping <uuid> --output json
uip is resources describe uipath-microsoft-outlook365 getNewestEmail \
  --operation List --connection-id <uuid> --output json
uip api-workflow registry stub <activity-type-id> \
  --connection-id <uuid> --inputs '{"parentFolderId":"Inbox"}' --output json
```

Insert `Data.Activity` into `Workflow.json`, then run `uip api-workflow validate Workflow.json --output json` until valid. State concrete side effects and ask for explicit consent. On approval, inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and invoke its live `RunProject` operation with exactly the schema-declared fields.

See [connector-activity-discovery.md](connector-activity-discovery.md) for field-shape rules and worked examples under the same Studio Web capability map.
<!--skill-flavor:connector-typical-sequence:end-->

<!--skill-flavor:local-solution-metadata:start-->
## Connection and Solution Metadata in Studio Web

Treat the connection and solution metadata maintained by Studio Web as authoritative. For resource operations, inspect the relevant host ProxyTool's live schema and use exactly its declared fields. Report the exact host capability gap when the requested resource operation is unavailable.
<!--skill-flavor:local-solution-metadata:end-->

<!--skill-flavor:local-solution-lifecycle:start-->
## Solution Lifecycle in Studio Web

Use `CreateProjects` for project creation and schema-inspected Studio Web capabilities for lifecycle operations.

### Publish the active Studio Web solution

Studio Web intercepts `solution:publish` through Unified Build. The help form is read-only and lists the supported flags and publish destinations:

```bash
uip solution publish --help
```

For an explicit user publish request or approval, run the active-solution form:

```bash
uip solution publish [--description <text>] [--release-notes <text>] [--version <version>] [--location <value>] [--location-name <value>] [--personal-workspace]
```

Supported bridge flags:

| Flag | Purpose |
|---|---|
| `--description <text>` | Publication description. |
| `--release-notes <text>` | Release notes for this publication. |
| `--version <version>` | Requested solution version. |
| `--location <value>` | Target location identifier accepted by the Studio Web bridge. |
| `--location-name <value>` | Target location name accepted by the Studio Web bridge. |
| `--personal-workspace` | Publish to the personal workspace target. |

The active Studio Web solution is implicit. A successful command result names the state reached: package built and uploaded, packaging on the server, or packaging still running in the tab; a nonzero exit means the publish failed. Orchestrator deployment is never confirmed here — confirm the published version with `uip or packages versions <packageName> --folder-path <path>`.
<!--skill-flavor:local-solution-lifecycle:end-->

<!--skill-flavor:command-existence-guidance:start-->
Treat this Studio Web command surface as the execution map: embedded static validation, registry authoring, read-only Integration Service discovery, consent-gated `RunProject`, and approved active-solution publication. Use live host schemas for every project, resource, runtime, and lifecycle operation.
<!--skill-flavor:command-existence-guidance:end-->

<!--skill-flavor:command-surface-heading:start-->
## Studio Web Command Surface

Use the embedded authoring commands and schema-inspected host operations described in this reference.
<!--skill-flavor:command-surface-heading:end-->

<!--skill-flavor:api-workflow-publish-guidance:start-->
- For an explicit publish request, use the approved host-intercepted `uip solution publish` active-solution form documented above.
<!--skill-flavor:api-workflow-publish-guidance:end-->

<!--skill-flavor:api-workflow-alias-guidance:start-->
- Use the full command spelling for the embedded authoring surface: `uip api-workflow validate`, `uip api-workflow registry resolve`, and `uip api-workflow registry stub`.
<!--skill-flavor:api-workflow-alias-guidance:end-->

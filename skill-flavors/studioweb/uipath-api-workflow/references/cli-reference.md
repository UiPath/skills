<!--skill-flavor:host-command-scope:start-->
> **Studio Web command scope:** run only the host-registered embedded CLI. Allowed here: `api-workflow validate`; `api-workflow registry resolve` / `stub`; read-only `uip is` discovery (`list`, `describe`, `ping`); read-only `uip solution publish --help`; and approved host-intercepted active-solution publication. Authentication is inherited. Execute workflows through consent-gated, schema-inspected `proxy-tools-Api` / `RunProject`. Project creation, embedded execution, local build/pack/deploy, machine-local or positional-package publication, login/config, binding sync, resource refresh, and solution-metadata edits are forbidden even when this reference documents their default/local syntax.
<!--skill-flavor:host-command-scope:end-->

<!--skill-flavor:local-project-lifecycle:start-->
## Project Creation, Build, and Pack in Studio Web

Do not run `uip api-workflow init`, `build`, or `pack`. Create a project with the live `proxy-tools-Solution` / `CreateProjects` schema. The tool does not switch the active project; after success, verify `/solution/<projectName>` and target `/solution/<projectName>/Workflow.json`. Use a Studio Web lifecycle tool for build or packaging when one is exposed, otherwise report the capability gap.
<!--skill-flavor:local-project-lifecycle:end-->

<!--skill-flavor:runtime-execution:start-->
## Execute an API Workflow in Studio Web

The embedded API Workflow runner is not a Studio Web execution surface: it fails before `WorkflowStart` with `No worker implementation available`. Do not use it, with or without authentication flags.

After `uip api-workflow validate Workflow.json --output json` returns `Data.Status: "Valid"`:

1. Explain the concrete external side effects and ask for explicit user consent.
2. If the user says yes, read `/skills/synthetic/proxy-tools-Api/SKILL.md` and inspect the live `RunProject` operation schema immediately before invocation.
3. Invoke `RunProject` with exactly the fields declared by that schema for the target project. Do not hardcode the payload, infer optional fields, or reuse parameters from a previous session.
4. Require the actual host tool result as execution evidence. If `RunProject` is absent or fails, report that host capability/result; do not switch to a local runner.
<!--skill-flavor:runtime-execution:end-->

<!--skill-flavor:registry-auth:start-->
Both subcommands use authentication inherited from the active Studio Web session; do not run `uip login`.
<!--skill-flavor:registry-auth:end-->

<!--skill-flavor:registry-auth-remediation:start-->
- `"Not logged in. Run 'uip login' first."` — report a Studio Web host-authentication blocker; do not run login or retry unchanged.
<!--skill-flavor:registry-auth-remediation:end-->

<!--skill-flavor:solution-resource-key:start-->
| `--resource-key <field>=<key>` | no (repeatable) | Use only when a live Studio Web resource capability exposes the key. Do not discover it by reading or editing solution metadata. If the key is unavailable, report the capability gap. |
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

Insert `Data.Activity` into `Workflow.json`, then run `uip api-workflow validate Workflow.json --output json` autonomously until valid. Ask for explicit consent before execution; on "yes," inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and invoke its live `RunProject` operation with exactly the schema-declared fields. Do not run binding-sync or resource-refresh commands; Studio Web owns that metadata.

See [connector-activity-discovery.md](connector-activity-discovery.md) for field-shape rules and worked examples under the same host command scope.
<!--skill-flavor:connector-typical-sequence:end-->

<!--skill-flavor:local-solution-metadata:start-->
## Connection and Solution Metadata in Studio Web

Do not run `uip api-workflow bindings sync` or `uip solution resources refresh`, and do not edit `bindings_v2.json`, `resources/`, `userProfile/`, or `.uipx`. Studio Web owns those files and backend entities. Use an exposed resource ProxyTool after inspecting its live schema; if no suitable capability exists, report the gap rather than creating local metadata.
<!--skill-flavor:local-solution-metadata:end-->

<!--skill-flavor:local-solution-lifecycle:start-->
## Solution Lifecycle in Studio Web

Do not run embedded or machine-local `uip solution init`, project add/remove, pack, deploy, login, or logout commands. Use `CreateProjects` for project creation and schema-inspected Studio Web capabilities for lifecycle operations other than publication.

### Publish the active Studio Web solution

Studio Web intercepts `solution:publish` through Unified Build. The help form is read-only and may be inspected without publish approval:

```bash
uip solution publish --help
```

For an explicit user publish request or approval, run the active-solution form with no positional package path:

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

Do not pass a `.zip`, package path, solution directory, or output directory. The active Studio Web solution is implicit. A successful command result means Unified Build accepted the request and background packaging began; it does not prove publication completed. Check Studio Web's Publish history for the final success or failure state. Do not substitute `uip solution pack` or deploy commands.
<!--skill-flavor:local-solution-lifecycle:end-->

<!--skill-flavor:command-existence-guidance:start-->
Some default/local commands documented in this reference exist in the desktop CLI but remain forbidden in Studio Web. The embedded API Workflow commands in scope are `validate` and `registry resolve` / `stub`; read-only `uip is` discovery is also in scope. Consent-gated execution uses the schema-inspected host `RunProject` operation. Publication uses only the approved, host-intercepted `uip solution publish` active-solution form above. Existence is not permission to call embedded execution, local pack/deploy, positional-package publication, or metadata commands.
<!--skill-flavor:command-existence-guidance:end-->

<!--skill-flavor:api-workflow-publish-guidance:start-->
- `uip api-workflow publish` does not exist. In Studio Web, an explicit publish request uses the host-intercepted `uip solution publish` active-solution form documented above; never invent the nonexistent API Workflow verb.
<!--skill-flavor:api-workflow-publish-guidance:end-->

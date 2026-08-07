<!--skill-flavor:surface-summary:start-->
Author, validate, execute, and publish API Workflow JSON in Studio Web. Use the host's embedded CLI only for allowed authoring operations and the host-intercepted publish bridge; use schema-inspected Studio Web tools for project creation, execution, and other lifecycle operations.
<!--skill-flavor:surface-summary:end-->

<!--skill-flavor:host-command-contract:start-->
## Studio Web Embedded Command Contract

Studio Web provides a browser sandbox, a virtual `/solution` filesystem, and a registered `uip` command. Use `ExecuteBashCommand` for the allowed embedded CLI operations below; do not substitute a machine-local shell or CLI.

- **Allowed embedded CLI:** `uip api-workflow validate` (autonomous), `uip api-workflow registry resolve` / `stub`, and read-only Integration Service discovery such as `uip is connectors list`, `activities list`, `connections list` / `ping`, and `resources list` / `describe`. Keep `--output json` whenever output is parsed.
- **Execution:** never use the embedded API Workflow runner in Studio Web; it has no worker implementation. After static validation passes and the user explicitly consents, inspect the live `/skills/synthetic/proxy-tools-Api/SKILL.md` and its `RunProject` operation schema, then invoke `RunProject` with exactly the schema-declared fields. Do not hardcode a payload from an earlier run.
- **Publication:** `uip solution publish --help` is read-only. Run host-intercepted `uip solution publish` only for an explicit user publish request or approval. It operates on the active solution and accepts no positional package path. A successful command means Unified Build accepted the request and started background packaging; confirm final completion in Studio Web's Publish history.
- **Forbidden:** every project/solution init command; `uip api-workflow build` / `pack`; `uip solution pack`; `uip solution deploy`; machine-local or positional-package `uip solution publish`; `uip login` / `logout` / `auth` / `config`; `uip api-workflow bindings sync`; `uip solution resources refresh`; and local edits to `.uipx`, `bindings_v2.json`, `project.uiproj`, `entry-points.json`, `resources/`, or `userProfile/`. Studio Web owns scaffolding, authentication, lifecycle, and solution metadata.
- **Working directory:** commands start at `/solution`, not in the designer's active project. For the existing open project, set the command's `workingDirectory` to `CurrentProject.AbsolutePath` or use that absolute path. After `CreateProjects`, the new project is not made active: use `/solution/<projectName>` from the successful tool call, verify it with `LsDirectory`, and target `/solution/<projectName>/Workflow.json` explicitly. Never put `CurrentSolution.SolutionName` in a filesystem path.

Authentication is inherited from the active Studio Web session. If an allowed command reports an authentication or capability error, report the host-level blocker; never try to repair it with login, install, or local lifecycle commands.
<!--skill-flavor:host-command-contract:end-->

<!--skill-flavor:connector-solution-registration:start-->
    - **(Studio Web + IntSvc only)** do not run `uip api-workflow bindings sync`, `uip solution resources refresh`, or edit `bindings_v2.json`, `resources/`, or `userProfile/`. Treat connection and solution resources exposed by Studio Web as authoritative. Use the allowed embedded registry and read-only `uip is` discovery commands to author the activity. If the host exposes a relevant resource ProxyTool, inspect its live schema before calling it and use only schema-declared fields and values; never reconstruct the call from memory.
<!--skill-flavor:connector-solution-registration:end-->

<!--skill-flavor:surface-lifecycle-scope:start-->
- User wants to **run, package, publish, or deploy** an API workflow through capabilities exposed by Studio Web
<!--skill-flavor:surface-lifecycle-scope:end-->

<!--skill-flavor:surface-operations-scope:start-->
- User wants to **debug or operate** an API workflow using Studio Web validation, run, lifecycle, connection, or diagnostic capabilities
<!--skill-flavor:surface-operations-scope:end-->

<!--skill-flavor:project-creation:start-->
19. **Create API Workflow projects with the Studio Web project tool — never with a CLI init command.** First distinguish an explicit request for a new project from a request to add workflow content to the current project; the current project's type alone does not decide that intent. For a new project, inspect the live `proxy-tools-Solution` / `CreateProjects` schema and invoke the API Workflow project type using exactly the fields and enum values it declares. Do not hardcode the request shape or tool parameters; the live schema is the contract.

19a. **Let Studio Web own project scaffolding and solution metadata.** Do not run `uip solution init`, `uip api-workflow init`, `uip login`, or any other local project-setup command. Do not search for, create, or edit `.uipx`, `project.uiproj`, `entry-points.json`, or `bindings_v2.json`. `CreateProjects` does not switch the active designer project: after success, verify `/solution/<projectName>` and edit `/solution/<projectName>/Workflow.json` explicitly, or open that project before relying on `CurrentProject.AbsolutePath`. If the creation tool, project type, or generated tree is unavailable, report that capability gap instead of fabricating a scaffold.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:runtime-validation-contract:start-->
3. **Validate statically, execute through the host.** `uip api-workflow validate` is the autonomous offline pre-flight. Runtime behavior, expressions, connections, and side effects must be tested only through the live `proxy-tools-Api` / `RunProject` host operation after explicit user consent. See rules 20–21.
<!--skill-flavor:runtime-validation-contract:end-->

<!--skill-flavor:runtime-validation-limit:start-->
    **What validate catches:** malformed JSON; unknown `activityType` values; per-activity required keys; missing activity metadata (warnings); invalid evaluation settings; duplicate or empty-named variables; and empty task lists. **What it does NOT catch:** wrong resource or connection IDs, runtime expression failures, designer normalization faults, and real connector behavior. After explicit consent, test those through the schema-inspected `RunProject` host operation.
<!--skill-flavor:runtime-validation-limit:end-->

<!--skill-flavor:runtime-execution-consent:start-->
21. **Never start a Studio Web run without an explicit user "yes."** Once static validation passes, ask whether to run now or skip and state concrete external side effects. If the user consents, read `/skills/synthetic/proxy-tools-Api/SKILL.md`, inspect the live `RunProject` schema immediately before invocation, and call it with exactly the declared fields for the target project. Do not guess parameters, reuse a stale schema, or substitute the embedded API Workflow runner. If `RunProject` is absent, report the host capability gap.
<!--skill-flavor:runtime-execution-consent:end-->

<!--skill-flavor:runtime-invocation-io:start-->
17. **Take runtime inputs only from the live `RunProject` schema.** Do not translate desktop CLI flags into guessed host-tool fields. If required input fields are absent or ambiguous, report that schema gap and ask the user rather than inventing a payload.
18. **Interpret execution from the actual `RunProject` tool result and its live contract.** Do not expect a desktop CLI `WorkflowRun` envelope or exit code. Keep `--output json` for allowed embedded CLI discovery and static-validation commands whose output is parsed.
<!--skill-flavor:runtime-invocation-io:end-->

<!--skill-flavor:validation-run-lifecycle:start-->
Use Studio Web's embedded CLI from the target project directory only for static validation: run `uip api-workflow validate Workflow.json --output json`, fixing and re-validating until `Data.Status` is `Valid`. Then state concrete external side effects and ask for explicit consent. On "yes," inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and the live `RunProject` schema, then invoke `RunProject` using exactly its declared fields. The embedded runner is unsupported in Studio Web (`No worker implementation available`); do not use it, even as a no-auth smoke test. If validation or `RunProject` is unavailable, report the host capability gap instead of switching to a machine-local CLI.
<!--skill-flavor:validation-run-lifecycle:end-->

<!--skill-flavor:deployment-lifecycle:start-->
Once the workflow is ready, keep local pack and deployment commands forbidden. For an explicit publish request, `uip solution publish --help` may be inspected without approval; then obtain publish approval and invoke host-intercepted `uip solution publish` for the active solution with only supported flags: `--description`, `--release-notes`, `--version`, `--location`, `--location-name`, and `--personal-workspace`. Never pass a package path or run `uip solution pack`. Command success means the request was accepted for background packaging, not that publication completed; verify the terminal status in Studio Web's Publish history. Use schema-inspected host capabilities for other lifecycle and published-workflow operations, or report the missing capability.
<!--skill-flavor:deployment-lifecycle:end-->

<!--skill-flavor:runtime-troubleshooting:start-->
Fix failures in category order — **Structure > Expression > Activity Config > Logic**. Use the embedded static validator autonomously; ask for consent before each `RunProject` diagnostic execution and inspect its live schema first. Use read-only `uip is` discovery for connection diagnosis, but do not use the embedded runner, connection edits, login, local metadata sync, or local lifecycle commands. Report a missing host capability instead of switching environments.
<!--skill-flavor:runtime-troubleshooting:end-->

<!--skill-flavor:quick-start-create:start-->
## Quick Start (CREATE from scratch in Studio Web)

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and `CreateProjects`.
2. Call `CreateProjects` for an API Workflow project using only schema-declared parameters and values; never guess or hardcode the request shape.
3. Remember that creation does not switch the active project. Verify `/solution/<projectName>`, then edit `/solution/<projectName>/Workflow.json` and add user activities after `WorkflowStart` inside the root sequence.
4. Set the embedded command working directory to `/solution/<projectName>`. Run `uip api-workflow validate Workflow.json --output json` autonomously. State side effects and ask for explicit consent; on "yes," inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and invoke the live `RunProject` operation with exactly its schema-declared fields.
5. When publication is explicitly requested, optionally inspect `uip solution publish --help`, obtain approval, then run host-intercepted `uip solution publish` against the active solution with no positional path and only supported bridge flags. Treat acceptance as background work and verify completion in Studio Web's Publish history. Do not run local pack, deploy, or login commands.
<!--skill-flavor:quick-start-create:end-->

<!--skill-flavor:project-creation-antipatterns:start-->
- **Do NOT** run `uip solution init`, `uip api-workflow init`, or any local setup command in Studio Web. Inspect and call the live `proxy-tools-Solution` / `CreateProjects` schema instead.
- **Do NOT** search for, create, or edit `.uipx` solution metadata in Studio Web; the host owns that metadata.
- **Do NOT** run local build/pack/deploy, positional-package publication, binding-sync, resource-refresh, authentication, or solution-metadata commands. The only publish command in scope is the host-intercepted active-solution form after explicit approval.
- **Do NOT** hand-assemble a replacement project when `CreateProjects` is unavailable. Report the missing capability so the user can choose how to proceed.
- **Do NOT** use successful local validation, packaging, or publication as evidence that a project was created correctly in Studio Web. The `CreateProjects` result and host-exposed project tree are authoritative.
<!--skill-flavor:project-creation-antipatterns:end-->

<!--skill-flavor:authentication-remediation:start-->
- `Not authenticated` / `Organization ID not available` → do not ask the user to run `uip login`. Use an exposed Studio Web authentication or connection capability after inspecting its live schema; if none exists, report the host-level authentication blocker and do not retry.
<!--skill-flavor:authentication-remediation:end-->

<!--skill-flavor:reference-navigation-extra:start-->

> **Studio Web reference scope.** Keep the shared references available for JSON authoring, troubleshooting, and CLI operations that Studio Web exposes, including validation, `uip api-workflow registry resolve` / `stub`, and the host-intercepted active-solution publish bridge. A reference documents the complete API Workflow surface; it does not grant permission to run every listed command in this host. Project creation must use the live `proxy-tools-Solution` / `CreateProjects` schema, and the Studio Web rules above still prohibit local init, pack, deploy, login, solution-metadata, and machine-local lifecycle fallbacks.
<!--skill-flavor:reference-navigation-extra:end-->

<!--skill-flavor:cli-reference-navigation:start-->
| [references/cli-reference.md](references/cli-reference.md) | Studio Web command contract: embedded authoring commands, schema-inspected `RunProject`, and approved host-intercepted active-solution publication; forbidden default/local lifecycle forms |
<!--skill-flavor:cli-reference-navigation:end-->

<!--skill-flavor:template-execution-proof:start-->
| [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json) | **Http kind** — HTTP Request curated activity (`call: "UiPath.Http"`) for arbitrary REST calls. Generated by `registry stub` against the catfacts URL and compatible with the Studio Web designer. Validate it through the embedded static validator and execute it only through consent-gated, schema-inspected `RunProject`. |
<!--skill-flavor:template-execution-proof:end-->

<!--skill-flavor:runtime-execution-antipattern:start-->
- **Do NOT** invoke the embedded API Workflow runner in Studio Web. It fails before `WorkflowStart` because no worker implementation is available. After explicit consent, use the live `proxy-tools-Api` / `RunProject` operation instead. See rules 20–21.
<!--skill-flavor:runtime-execution-antipattern:end-->

<!--skill-flavor:published-reference-navigation:start-->
| [references/operating-published-workflows.md](references/operating-published-workflows.md) | Operate and diagnose published workflows through live Studio Web capabilities; report missing job/log/trace/lifecycle surfaces instead of invoking local platform CLI commands |
<!--skill-flavor:published-reference-navigation:end-->

<!--skill-flavor:solution-resource-template:start-->
| [assets/templates/solution-connection-resource-template.json](assets/templates/solution-connection-resource-template.json) | **Local/default reference only.** Do not copy or write this solution-resource file in Studio Web; the host owns connection resources and solution metadata. |
<!--skill-flavor:solution-resource-template:end-->

<!--skill-flavor:surface-summary:start-->
Author, validate, execute, and publish API Workflow JSON in Studio Web. Use `CreateProjects` for project creation, the Studio Web VFS for authoring, the embedded CLI for static validation and activity discovery, `RunProject` for approved execution, and the host publish bridge for publication.

<!--skill-flavor:surface-summary:end-->

<!--skill-flavor:host-command-contract:start-->
## Studio Web Capability Map

Studio Web provides a browser sandbox, a virtual `/solution` filesystem, an embedded `uip` command, and live ProxyTools. Treat this map as the executable contract for Studio Web; shared references provide authoring context. For requests beyond this map, report the exact host capability gap and ask how the user wants to proceed.

- **Project creation:** inspect the live `proxy-tools-Solution` / `CreateProjects` schema and invoke the API Workflow project type with exactly its declared fields and enum values.
- **Project files:** for the open project, use `CurrentProject.AbsolutePath`. After creation, verify the returned `/solution/<projectName>` directory with `LsDirectory` and edit `/solution/<projectName>/Workflow.json`. Treat the host-generated tree and metadata as authoritative.
- **Activity discovery:** use `ExecuteBashCommand` for `uip api-workflow registry resolve` / `stub` and read-only Integration Service discovery such as `uip is connectors list`, `activities list`, `connections list` / `ping`, and `resources list` / `describe`. Authentication comes from the active Studio Web session. Keep `--output json` whenever output is parsed.
- **Validation:** from the target project root, run `uip api-workflow validate Workflow.json --output json` until `Data.Status` is `Valid`.
- **Execution:** state concrete external side effects and require an explicit user yes. Then inspect `/skills/synthetic/proxy-tools-Api/SKILL.md`, inspect the live `RunProject` schema, invoke exactly its declared fields for the target project, and use the actual tool result as evidence.
- **Publication:** for an explicit approved publish request, run host-intercepted `uip solution publish` with supported flags. The active solution is implicit. Treat command success as request acceptance and verify final completion in Studio Web's Publish history.

Authentication and tenant context are inherited from the active Studio Web session. Report authentication or capability failures as host-level blockers and retry after the relevant host state changes.
<!--skill-flavor:host-command-contract:end-->

<!--skill-flavor:connector-solution-registration:start-->
    - **(Studio Web + IntSvc only)** treat the connection and solution resources exposed by Studio Web as authoritative. Use registry resolution, read-only `uip is` discovery, and relevant resource ProxyTools for authoring. Inspect each live ProxyTool schema immediately before invocation and pass exactly its declared fields and values.
<!--skill-flavor:connector-solution-registration:end-->

<!--skill-flavor:surface-lifecycle-scope:start-->
- User wants to **run, publish, or manage the lifecycle of** an API workflow through capabilities exposed by Studio Web
<!--skill-flavor:surface-lifecycle-scope:end-->

<!--skill-flavor:surface-operations-scope:start-->
- User wants to **debug or operate** an API workflow using Studio Web validation, execution, lifecycle, connection, or diagnostic capabilities
<!--skill-flavor:surface-operations-scope:end-->

<!--skill-flavor:project-creation:start-->
19. **Create API Workflow projects with the Studio Web project tool.** First distinguish an explicit request for a new project from a request to add workflow content to the current project. For a new project, inspect the live `proxy-tools-Solution` / `CreateProjects` schema and invoke the API Workflow project type using exactly the fields and enum values it declares.

19a. **Continue from the project returned by Studio Web.** Verify `/solution/<projectName>` with `LsDirectory`, then edit `/solution/<projectName>/Workflow.json`; alternatively, open that project before using `CurrentProject.AbsolutePath`. Preserve the host-generated project tree and metadata. When the creation operation, project type, or generated tree is unavailable, report the exact capability gap.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:runtime-validation-contract:start-->
2. **Start minimal, iterate to correct.** Add one activity at a time. Run the offline static validator after each addition. Fix what breaks and repeat. Start runtime execution after the explicit consent required by rule 21.
3. **Validate statically, execute through the host.** `uip api-workflow validate` is the autonomous offline pre-flight. After explicit consent, use the live `proxy-tools-Api` / `RunProject` host operation to verify runtime behavior, expressions, connections, and side effects. See rules 20–21.
<!--skill-flavor:runtime-validation-contract:end-->

<!--skill-flavor:designer-literal-runtime-comparison:start-->
5. **String literals in `Assign.set` / `Response` / If `when` MUST be wrapped as `"${'literal'}"`** — a JS string inside an expression. Studio Web's designer normalizes unwrapped values to `"${literal}"` on save, so use single quotes inside the expression: `"set": { "tier": "${'PLATINUM'}" }`. Numbers, booleans, and references like `${$context.variables.X}` need no extra wrapping. (Response payloads have a related but distinct constraint — see rule 15.) **Scope:** this rule applies to Assign / Response / If / variable contexts. Connector `bodyParameters` / `queryParameters` / `pathParameters` use BARE literals; `${'...'}` there is read as an expression and the field is cleared on save. See rule 16 and [references/connector-activity-discovery.md#field-shape-rules-flat-keys-bare-literals-renamed-export-hub-prefix](references/connector-activity-discovery.md#field-shape-rules-flat-keys-bare-literals-renamed-export-hub-prefix). See [references/troubleshooting.md](references/troubleshooting.md#studioweb-roundtrip-pitfalls).
<!--skill-flavor:designer-literal-runtime-comparison:end-->

<!--skill-flavor:runtime-validation-limit:start-->
    **Static coverage:** malformed JSON; unknown `activityType` values; per-activity required keys; missing activity metadata (warnings); invalid evaluation settings; duplicate or empty-named variables; and empty task lists. **Runtime coverage:** resource and connection IDs, expression evaluation, designer normalization, and real connector behavior. After explicit consent, verify runtime coverage through the schema-inspected `RunProject` host operation.
<!--skill-flavor:runtime-validation-limit:end-->

<!--skill-flavor:response-roundtrip-validation:start-->
    - **On-disk is authoritative.** Every Studio Web designer save can re-trigger normalization passes that may corrupt the Response shape. After each designer roundtrip, run the offline static validator. When runtime revalidation is needed, obtain the explicit consent required by rule 21, invoke `RunProject`, inspect the Response, and re-apply the single-expression workaround when needed. Until the designer fix ships, treat the file on disk as the source of truth.
<!--skill-flavor:response-roundtrip-validation:end-->

<!--skill-flavor:runtime-execution-consent:start-->
21. **Start each Studio Web run after an explicit user "yes."** Once static validation passes, state the concrete external side effects and ask whether to run now or skip. On approval, read `/skills/synthetic/proxy-tools-Api/SKILL.md`, inspect the live `RunProject` schema immediately before invocation, and call it with exactly the declared fields for the target project. Use the actual tool result as execution evidence. When `RunProject` is unavailable, report the exact host capability gap.
<!--skill-flavor:runtime-execution-consent:end-->

<!--skill-flavor:runtime-invocation-io:start-->
17. **Map runtime inputs directly from the live `RunProject` schema.** When a required input is absent or ambiguous, report the schema gap and ask the user for the needed value or host capability.
18. **Interpret execution from the actual `RunProject` result and its live contract.** Keep `--output json` for embedded discovery and static-validation commands whose output is parsed.
<!--skill-flavor:runtime-invocation-io:end-->

<!--skill-flavor:validation-run-lifecycle:start-->
From the target project directory, run `uip api-workflow validate Workflow.json --output json`, fixing and re-validating until `Data.Status` is `Valid`. Then state concrete external side effects and ask for explicit consent. On approval, inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and the live `RunProject` schema, then invoke `RunProject` using exactly its declared fields. Report validation or execution capability gaps with the exact host result.
<!--skill-flavor:validation-run-lifecycle:end-->

<!--skill-flavor:deployment-lifecycle:start-->
For an explicit publish request, obtain publish approval first; then optionally inspect `uip solution publish --help` and invoke host-intercepted `uip solution publish` for the active solution with supported flags: `--description`, `--release-notes`, `--version`, `--location`, `--location-name`, and `--personal-workspace`. Command success means Unified Build accepted the request and started background packaging. Verify the terminal status in Studio Web's Publish history. Use schema-inspected host capabilities for other lifecycle and published-workflow operations.
<!--skill-flavor:deployment-lifecycle:end-->

<!--skill-flavor:runtime-troubleshooting:start-->
Fix failures in category order — **Structure > Expression > Activity Config > Logic**. Use the embedded static validator autonomously, read-only `uip is` discovery for connection diagnosis, and consent-gated `RunProject` invocations for runtime diagnosis. Inspect each live schema immediately before invocation and report the exact host result or capability gap.
<!--skill-flavor:runtime-troubleshooting:end-->

<!--skill-flavor:quick-start-create:start-->
## Quick Start (CREATE from scratch in Studio Web)

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and `CreateProjects`.
2. Call `CreateProjects` for an API Workflow project using the schema-declared parameters and enum values.
3. Verify the returned `/solution/<projectName>` directory, then edit `/solution/<projectName>/Workflow.json` and add user activities after `WorkflowStart` inside the root sequence.
4. Set the embedded command working directory to `/solution/<projectName>`. Run `uip api-workflow validate Workflow.json --output json` until valid. State side effects and ask for explicit consent; on approval, inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and invoke the live `RunProject` operation with exactly its schema-declared fields.
5. When publication is explicitly requested, obtain approval and run host-intercepted `uip solution publish` for the active solution with supported bridge flags. Treat acceptance as background work and verify completion in Studio Web's Publish history.
<!--skill-flavor:quick-start-create:end-->

<!--skill-flavor:project-creation-antipatterns:start-->
- **Use the freshly inspected `proxy-tools-Solution` / `CreateProjects` schema** for every explicit new-project request.
- **Use the successful `CreateProjects` result and host-exposed project tree as creation evidence.**
- **Preserve the host-generated project tree and solution metadata** while authoring `/solution/<projectName>/Workflow.json`.
- **Report an unavailable creation capability or project type as an exact host gap** and ask how the user wants to proceed.
<!--skill-flavor:project-creation-antipatterns:end-->

<!--skill-flavor:authentication-remediation:start-->
- `Not authenticated` / `Organization ID not available` → inspect any exposed Studio Web authentication or connection capability through its live schema. Report the host-level authentication blocker and retry after the Studio Web session or tenant state changes.
<!--skill-flavor:authentication-remediation:end-->

<!--skill-flavor:reference-navigation-extra:start-->

> **Studio Web reference scope.** Use the shared references for JSON authoring, troubleshooting, static validation, `uip api-workflow registry resolve` / `stub`, read-only Integration Service discovery, and the host-intercepted active-solution publish bridge. Apply the Studio Web capability map above and inspect live host schemas for project, runtime, resource, and lifecycle operations.
<!--skill-flavor:reference-navigation-extra:end-->

<!--skill-flavor:cli-reference-navigation:start-->
| [references/cli-reference.md](references/cli-reference.md) | Studio Web capability map: embedded authoring commands, schema-inspected `RunProject`, and approved host-intercepted active-solution publication |
<!--skill-flavor:cli-reference-navigation:end-->

<!--skill-flavor:template-execution-proof:start-->
| [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json) | **Http kind** — HTTP Request curated activity (`call: "UiPath.Http"`) for arbitrary REST calls. Generated by `registry stub` against the catfacts URL and compatible with the Studio Web designer. Validate it through the embedded static validator and, after explicit consent, execute it through schema-inspected `RunProject`. |
<!--skill-flavor:template-execution-proof:end-->

<!--skill-flavor:runtime-execution-antipattern:start-->
- **After static validation and explicit consent, execute through the freshly inspected `proxy-tools-Api` / `RunProject` operation and use its actual result as evidence.** See rules 20–21.
<!--skill-flavor:runtime-execution-antipattern:end-->

<!--skill-flavor:published-reference-navigation:start-->
| [references/operating-published-workflows.md](references/operating-published-workflows.md) | Operate and diagnose published workflows through live Studio Web capabilities; report unavailable job, log, trace, or lifecycle surfaces and hand off deeper platform investigation |
<!--skill-flavor:published-reference-navigation:end-->

<!--skill-flavor:solution-resource-template:start-->
| [assets/templates/solution-connection-resource-template.json](assets/templates/solution-connection-resource-template.json) | **Studio Web resource reference.** Inspect the relevant host resource capability and use its declared fields for connection-resource authoring. |
<!--skill-flavor:solution-resource-template:end-->

<!--skill-flavor:connector-solution-registration:start-->
    - **(Studio Web + IntSvc only)** do not run local binding-sync/resource-refresh commands or edit solution catalogue files. Treat the connection and solution resources exposed by Studio Web as authoritative. If the host exposes a relevant ProxyTool, inspect its live schema before calling it and use only the fields and values that schema declares; never reconstruct the call from memory.
<!--skill-flavor:connector-solution-registration:end-->

<!--skill-flavor:surface-lifecycle-scope:start-->
- User wants to **run, package, publish, or deploy** an API workflow through capabilities exposed by Studio Web
<!--skill-flavor:surface-lifecycle-scope:end-->

<!--skill-flavor:surface-operations-scope:start-->
- User wants to **debug or operate** an API workflow using Studio Web validation, run, lifecycle, connection, or diagnostic capabilities
<!--skill-flavor:surface-operations-scope:end-->

<!--skill-flavor:project-creation:start-->
19. **Create API Workflow projects with the Studio Web project tool — never with a CLI init command.** Before creating a project, inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation. Invoke that operation with the API Workflow project type using exactly the fields and enum values present in the current schema. Do not hardcode the request shape or tool parameters in the skill; the live schema is the contract.

19a. **Let Studio Web own project scaffolding and solution metadata.** Do not run `uip solution init`, `uip api-workflow init`, `uip login`, or any other local project-setup command. Do not search for, create, or edit a local `.uipx` file. After `CreateProjects` succeeds, inspect the project files exposed by the Studio Web workspace/VFS and edit the generated workflow entrypoint. If the creation tool or required project type is unavailable, report that capability gap instead of fabricating a local scaffold.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:validation-run-lifecycle:start-->
Validate and run through capabilities exposed by Studio Web, inspecting each live schema before calling it. Validation without external side effects may proceed autonomously; preserve the explicit-consent requirement before any run that can call a vendor system. Do not ask the user to establish a local CLI login or fall back to a local command when Studio Web does not expose the required capability; report the capability gap.
<!--skill-flavor:validation-run-lifecycle:end-->

<!--skill-flavor:deployment-lifecycle:start-->
Once the workflow is ready, use only the lifecycle tools exposed by Studio Web for packaging, publishing, deployment, and published-workflow operations. Inspect each tool's live schema before calling it. Do not substitute local solution, authentication, Orchestrator, Integration Service, or trace CLI commands when the corresponding Studio Web capability is absent; report the missing capability and ask how the user wants to proceed.
<!--skill-flavor:deployment-lifecycle:end-->

<!--skill-flavor:runtime-troubleshooting:start-->
Fix run failures in category order — **Structure > Expression > Activity Config > Logic** — using diagnostics exposed by the Studio Web validation/run capability. Do not switch to a local CLI troubleshooting workflow or local authentication setup when a host capability is missing; report the capability gap.
<!--skill-flavor:runtime-troubleshooting:end-->

<!--skill-flavor:quick-start-create:start-->
## Quick Start (CREATE from scratch in Studio Web)

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and `CreateProjects`.
2. Call `CreateProjects` for an API Workflow project using only schema-declared parameters and values; never guess or hardcode the request shape.
3. Inspect the files generated in the Studio Web workspace/VFS, open the generated workflow entrypoint, and add user activities after `WorkflowStart` inside the root sequence.
4. Validate and run only through capabilities exposed in Studio Web. Preserve the explicit-consent rule before any run that can invoke a vendor system or create external side effects.
5. When packaging or publishing is requested, use the available Studio Web lifecycle tool after inspecting its live schema. If none is exposed, report the capability gap rather than falling back to local CLI setup.
<!--skill-flavor:quick-start-create:end-->

<!--skill-flavor:project-creation-antipatterns:start-->
- **Do NOT** run `uip solution init`, `uip api-workflow init`, or any local setup command in Studio Web. Inspect and call the live `proxy-tools-Solution` / `CreateProjects` schema instead.
- **Do NOT** search for, create, or edit `.uipx` solution metadata in Studio Web; the host owns that metadata.
- **Do NOT** hand-assemble a replacement project when `CreateProjects` is unavailable. Report the missing capability so the user can choose how to proceed.
- **Do NOT** use successful local validation, packaging, or publication as evidence that a project was created correctly in Studio Web. The `CreateProjects` result and host-exposed project tree are authoritative.
<!--skill-flavor:project-creation-antipatterns:end-->

<!--skill-flavor:authentication-remediation:start-->
- `Not authenticated` / `Organization ID not available` → do not ask the user to run `uip login`. Use an exposed Studio Web authentication or connection capability after inspecting its live schema; if none exists, report the host-level authentication blocker and do not retry.
<!--skill-flavor:authentication-remediation:end-->

<!--skill-flavor:reference-navigation-extra:start-->

> **Studio Web reference scope.** Keep the shared references available for JSON authoring, troubleshooting, and CLI operations that Studio Web exposes, including validation and `uip api-workflow registry resolve` / `stub` for connector discovery. A reference documents the complete API Workflow surface; it does not grant permission to run every listed command in this host. Project creation must use the live `proxy-tools-Solution` / `CreateProjects` schema, and the Studio Web rules above still prohibit local init, login, solution-metadata, and lifecycle fallbacks.
<!--skill-flavor:reference-navigation-extra:end-->

<!-- skill-flavor:run-lifecycle:start -->
Execute the current Flow through capabilities exposed by Studio Web.

## Controlled run

1. Obtain explicit user consent when the Flow can have real side effects.
2. Read `/skills/synthetic/proxy-tools-Flow/SKILL.md` if advertised and use its live `RunProject` schema through `ProxyTool`.
3. If no project ProxyTool is advertised, use a Flow debug command only when the current browser-bundle list exposes it. In the browser form, the optional positional value is a project display name, and `--inputs` must be an inline JSON object. `@file` inputs and local project-directory semantics are unsupported.
4. Report terminal status plus the returned trace/log excerpt. Use any returned trace or instance identifier for follow-up diagnosis.

Do not run `uip login` or `uip solution resources refresh`; authentication and solution resources are host-owned. Do not infer that a missing ProxyTool exists because RunProject supports the project type internally. If neither route is exposed, report the capability gap and ask the user to run from the Studio Web UI.

## Published process and instance operations

Use only commands or host tools advertised in the current session. Preserve folder/instance identifiers returned by the run. Diagnose a fault before retrying, and never invent a legacy `uip maestro flow` command when the browser advertises a different prefix.
<!-- skill-flavor:run-lifecycle:end -->

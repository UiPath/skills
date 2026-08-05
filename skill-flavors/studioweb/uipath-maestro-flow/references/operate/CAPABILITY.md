<!-- skill-flavor:operate-contract:start -->
Capability index for running, publishing, and diagnosing a Flow that is already open in Studio Web. Authentication and solution identity come from the host; there is no local `.uipx` lifecycle.

## Studio Web workflow

1. Read `/skills/synthetic/proxy-tools-Flow/SKILL.md` when the per-turn directives advertise it.
2. For validation or project actions, prefer a tool listed by that live skill and invoke it through `ProxyTool` using its exact schema. Otherwise use only a Flow command shown by the current browser-bundle list.
3. Obtain explicit consent before any run with external side effects.
4. Run with the advertised `RunProject` capability. A live-advertised Flow debug command is a fallback; pass a project display name and inline JSON inputs, not a local project-directory path or `@file` inputs.
5. Publish with the Studio Web publish surface, normally `uip solution publish` or a live-advertised Flow publish command. Packaging and upload are host-owned and completion is asynchronous.
6. Diagnose with the returned trace/log excerpt and only the project/diagnostic operations available in the current session.

## Critical rules

- Never run `uip login`, `uip solution resources refresh`, `uip solution upload`, a local Flow pack, or `uip solution deploy` in Studio Web.
- Never promise `proxy-tools-Flow` or a particular lifecycle method unless the per-turn directives advertise it.
- Never run a Flow without explicit consent when it may call connectors, send messages, mutate data, or invoke other systems.
- Treat a missing live capability as a product boundary. Report it rather than falling back to desktop solution commands.
<!-- skill-flavor:operate-contract:end -->

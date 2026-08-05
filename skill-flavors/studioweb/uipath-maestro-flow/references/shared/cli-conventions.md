<!-- skill-flavor:cli-availability:start -->
## 1. Use the Studio Web browser CLI

`uip` is already registered in the browser sandbox. Never probe its location or version, and never install or update it. Read the per-turn browser-bundle subcommand list and use the top-level prefix it advertises. Desktop examples in this skill use `uip maestro flow`; when Studio Web advertises a flat `uip flow` group, use that flat group. Inspect `<advertised-prefix> <subcommand> --help` only when exact nested syntax is needed.
<!-- skill-flavor:cli-availability:end -->

<!-- skill-flavor:external-parser-fallback:start -->
### When to fall back to `jq`

Prefer `--output-filter` for extraction. When JMESPath cannot express a required join or format conversion, use the sandbox-provided `jq`, `yq`, `awk`, or coreutils after confirming the response shape. Python, Node, package managers, and executable helper scripts are unavailable in Studio Web. An empty filtered result is not evidence that a resource is absent until field casing and the full untruncated result have been verified.
<!-- skill-flavor:external-parser-fallback:end -->

<!-- skill-flavor:authentication:start -->
## 5. Authentication

Authentication is inherited from the active Studio Web session. Call an advertised Flow, Integration Service, or platform command directly. Never run `uip login`, `uip logout`, `uip auth`, or `uip config`. If a command reports an authentication or entitlement error, surface the host-level blocker instead of attempting local login or token repair.
<!-- skill-flavor:authentication:end -->

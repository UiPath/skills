<!--skill-flavor:libraries-api-fallback:start-->
     2. no Orchestrator API fallback in Studio Web, whose browser bundle has no API command — go to 3;
<!--skill-flavor:libraries-api-fallback:end-->

<!--skill-flavor:fallback-chain-anti-pattern:start-->
2. **Inventing a verb or flag after a CLI rejection.** The surface drifts across versions (`--search` / `--feed-id` exist only on newer CLIs; older CLIs may lack `or libraries` entirely). On `unknown command` / `unknown option`, discover with `--help` and use the preflight's fallback chain (packages feed) — never guess.
<!--skill-flavor:fallback-chain-anti-pattern:end-->

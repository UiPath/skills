<!-- skill-flavor:command-reference:start -->
Studio Web supplies a browser-specific `uip` bundle. Read the per-turn browser-bundle list before choosing a command prefix, then use `<advertised-prefix> <subcommand> --help` for exact nested syntax.

## Supported command classes

- **Registry, node, validation, and format:** use only when the current Flow prefix advertises the operation. Prefer `--output json` and `--output-filter` where accepted.
- **Run:** prefer the advertised `proxy-tools-Flow` / `RunProject` host tool after explicit consent. A live browser Flow debug command is a fallback; its optional positional is a project display name, and inputs must be inline JSON.
- **Publish:** use the Studio Web publish surface, normally `uip solution publish` or an advertised Flow publish operation. Do not pass a local package or solution path.
- **Inline agent:** `uip agent init "/solution/<FlowProject>" --inline-in-flow` is the only allowed init form. Use matching inline refresh/validate operations only when advertised.

## Unavailable desktop command classes

Never run solution/Flow init, `.uipx` registration, `uip login`, CLI probing/installing, `uip solution resources refresh`, `uip solution upload`, local Flow pack, or `uip solution deploy`. Do not rewrite a desktop `uip maestro flow` example to a guessed flat command; the live bundle is authoritative. If the required operation is missing, report the capability gap.
<!-- skill-flavor:command-reference:end -->

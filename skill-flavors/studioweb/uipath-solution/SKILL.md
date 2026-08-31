<!--skill-flavor:solution-lifecycle-steps:start-->
```
1. Create projects   → CreateProjects tool / New Project UI
2. resources refresh → Sync bundled artefacts with cloud state (if needed)
3. publish           → uip solution publish (packaging and auth handled by Studio Web)
```

> **No `pack`, `restore`, `login`, `upload`, or `deploy` steps in Studio Web.** The packager is Node-only and excluded from the browser bundle, authentication is injected by the host, and `uip solution upload` / `deploy` decline as unavailable. Publishing packages the solution for you; deployment runs from Studio Web's Manage → Deploy wizard.

> **Publish destination — the user's choice.** Run `uip solution publish` with no destination flags first. With one destination it publishes there. With several it publishes nothing and lists them: ask the user in chat which destination to use — personal workspace (visible only to them) vs shared location (visible to others with access) — then rerun with `--location "<key or name>"` (or `--personal-workspace`). Skip the question when the user already named a destination; remember their answer for the rest of the conversation. Unknown flags fail the command — the destination flag is `--location`.

> **Publish is asynchronous.** Success means Unified Build accepted the request and packaging continues in the background — submitted is not shipped. Report destination, version, and request id; verify the terminal state in Studio Web's Publish history.
<!--skill-flavor:solution-lifecycle-steps:end-->

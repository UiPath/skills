<!--skill-flavor:solution-verb-probe:start-->
- **Never create a solution.** Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. `uip agent init "<AgentName>"` creates the agent project inside it at `/solution/<AgentName>/`. The CLI is post-rename: `uip solution deploy run` takes `--parent-folder-path` / `--parent-folder-key`.
<!--skill-flavor:solution-verb-probe:end-->

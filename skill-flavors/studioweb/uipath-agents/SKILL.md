<!--skill-flavor:solution-verb-probe:start-->
- **Never create a solution.** Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. `uip agent init "<AgentName>"` creates the agent project inside it at `/solution/<AgentName>/`. The CLI is post-rename: `uip solution deploy run` takes `--parent-folder-path` / `--parent-folder-key`.
<!--skill-flavor:solution-verb-probe:end-->

<!--skill-flavor:git-studioweb-rule:start-->
- **Leave `.git` and `.git-studioweb` entries alone.** Studio Web manages the solution's local repository itself, in a `.git-studioweb` folder when the browser cannot create `.git`. Never create, edit or delete a `.git` or `.git-studioweb` entry with file tools. For desktop git or VS Code on that folder, tell the user to link it from a terminal on their own machine (`uipath-solution` skill, Git Studio Web Layout).
<!--skill-flavor:git-studioweb-rule:end-->

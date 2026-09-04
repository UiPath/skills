<!--skill-flavor:create-solution:start-->
### Solution

Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. Agents are created inside it.
<!--skill-flavor:create-solution:end-->

<!--skill-flavor:register-project:start-->
`uip agent init "<AgentName>"` creates the project inside the open solution at `/solution/<AgentName>/`. Studio Web owns the solution manifest — there is no `.uipx` on disk to register with and no auto-scaffolded sibling solution, so `--skip-solution-registration` and `uip solution projects add` have nothing to do here.
<!--skill-flavor:register-project:end-->

<!--skill-flavor:e2e-scaffold:start-->
```bash
# Studio Web creates the project inside the open solution; there is no
# solution to create and no `.uipx` to register with.
uip agent init "<AGENT_NAME>" --output json
```

Run it from the solution root (`/solution`). The agent lands at `/solution/<AGENT_NAME>/` — wherever the steps below write `<SOLUTION_NAME>/<AGENT_NAME>`, use that path.
<!--skill-flavor:e2e-scaffold:end-->

<!--skill-flavor:create-solution-row:start-->
<!--skill-flavor:create-solution-row:end-->

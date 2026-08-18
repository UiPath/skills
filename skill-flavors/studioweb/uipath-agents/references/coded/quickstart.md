<!--skill-flavor:scenario-two-ownership:start-->
Use when the coded agent is tightly coupled to one flow and lives as a sibling folder inside the same solution. The agent is wired to the flow via `--local` registry discovery — no separate Orchestrator deployment for the agent, no separate skill hand-off. **`uipath-agents` owns this scenario end-to-end** — Flow project creation, agent build, registration, and flow wiring all happen here. Do not read or invoke `uipath-maestro-flow` as a separate skill; use the `CreateProjects` tool to create the Flow project, then continue with the remaining steps in this workflow.
<!--skill-flavor:scenario-two-ownership:end-->

<!--skill-flavor:flow-project-creation:start-->
1. **Create the Flow project with the `CreateProjects` tool** (skip if it already exists). Inspect the live `CreateProjects` schema, invoke it for a Flow project using exactly the fields and enum values it declares, then locate the generated project in the Studio Web workspace/VFS.

2. **Resolve the names the later steps need — no commands to run here.** `CreateProjects` returns the generated project name in its result, so read `<FlowName>` from there (or from the VFS listing) rather than inventing it. In the current Studio Web harness the solution is always named `solution`: the solution root is `/solution` and its manifest is `solution.uipx`, so read every `<SolutionName>` below as `solution`. Steps 5–8 pass these names to the CLI as arguments. Run steps 3–8 from `/solution` unless a step changes directory.
<!--skill-flavor:flow-project-creation:end-->

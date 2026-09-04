<!--skill-flavor:scenario-two-ownership:start-->
Use when the coded agent is tightly coupled to one flow and lives as a sibling folder inside the same solution. The agent is wired to the flow via `--local` registry discovery — no separate Orchestrator deployment for the agent, no separate skill hand-off. **`uipath-agents` owns this scenario end-to-end** — Flow project creation, agent build, registration, and flow wiring all happen here. Do not read or invoke `uipath-maestro-flow` as a separate skill; use the `CreateProjects` tool to create the Flow project, then continue with the remaining steps in this workflow.
<!--skill-flavor:scenario-two-ownership:end-->

<!--skill-flavor:flow-project-creation:start-->
1. **Create the Flow project with the `CreateProjects` tool** (skip if it already exists). Inspect the live `CreateProjects` schema, invoke it for a Flow project using exactly the fields and enum values it declares, then locate the generated project in the Studio Web workspace/VFS.

2. **Resolve the names the later steps need — no commands to run here.** `CreateProjects` returns the generated project name in its result, so read `<FlowName>` from there (or from the VFS listing) rather than inventing it. The solution root is `/solution`; run steps 3–8 from there unless a step changes directory. Studio Web owns the solution manifest and does not expose it, so the later steps identify the solution by its `/solution` root alone.
<!--skill-flavor:flow-project-creation:end-->

<!--skill-flavor:agent-solution-registration:start-->
   cd ..
   uip solution projects add "<AgentName>" --output json
<!--skill-flavor:agent-solution-registration:end-->

<!--skill-flavor:agent-scaffold-solution-root:start-->
3. **Scaffold the coded agent as a sibling folder.** From the solution root (`/solution`):
<!--skill-flavor:agent-scaffold-solution-root:end-->

<!--skill-flavor:agent-scaffold-result-paths:start-->
   Result: `/solution/<AgentName>/` sibling to `/solution/<FlowName>/`.
<!--skill-flavor:agent-scaffold-result-paths:end-->

<!--skill-flavor:delivery-option-b-row:start-->
<!--skill-flavor:delivery-option-b-row:end-->

<!--skill-flavor:delivery-option-b:start-->
<!--skill-flavor:delivery-option-b:end-->

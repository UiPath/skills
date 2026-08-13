<!--skill-flavor:scenario-two-ownership:start-->
Use when the coded agent is tightly coupled to one flow and lives as a sibling folder inside the same solution. The agent is wired to the flow via `--local` registry discovery — no separate Orchestrator deployment for the agent, no separate skill hand-off. **`uipath-agents` owns this scenario end-to-end** — Flow project creation, agent build, registration, and flow wiring all happen here. Do not read or invoke `uipath-maestro-flow` as a separate skill; use the `CreateProjects` tool to create the Flow project, then continue with the remaining steps in this workflow.
<!--skill-flavor:scenario-two-ownership:end-->

<!--skill-flavor:flow-project-creation:start-->
1. **Create the Flow project if needed with the `CreateProjects` tool.**
<!--skill-flavor:flow-project-creation:end-->

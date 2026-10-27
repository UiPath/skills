<!--skill-flavor:scenario-two-ownership:start-->
Use when the coded agent is tightly coupled to one flow and lives as a sibling folder inside the same solution. The agent is wired to the flow via `--local` registry discovery — no separate Orchestrator deployment for the agent, no separate skill hand-off. **`uipath-agents` owns this scenario end-to-end** — Flow project creation, agent build, registration, and flow wiring all happen here. Do not read or invoke `uipath-maestro-flow` as a separate skill; use the `CreateProjects` tool to create the Flow project, then continue with the remaining steps in this workflow.
<!--skill-flavor:scenario-two-ownership:end-->

<!--skill-flavor:flow-project-creation:start-->
1. **Create the Flow project with the `CreateProjects` tool** (skip if it already exists). Inspect the live `CreateProjects` schema, invoke it for a Flow project using exactly the fields and enum values it declares, then locate the generated project in the Studio Web workspace/VFS.

2. **Resolve the names the later steps need — no commands to run here.** `CreateProjects` returns the generated project name in its result, so read `<FlowName>` from there (or from the VFS listing) rather than inventing it. The solution root is `/solution`; run steps 3–8 from there unless a step changes directory. Studio Web owns the solution manifest and does not expose it, so the later steps identify the solution by its `/solution` root alone.
<!--skill-flavor:flow-project-creation:end-->

<!--skill-flavor:agent-solution-registration:start-->
   # No registration command in Studio Web: the host registers every project it creates under
   # /solution, and `uip solution projects add` is Node-CLI-only. If step 3 was refused
   # ("coded-agent projects are not among the types Studio Web can create"), this scenario needs
   # the Node CLI on your machine — stop and tell the user.
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

<!--skill-flavor:deploy-reachability:start-->
9. **Deploy.** Reachable from any `project_state` after option **Skip** at step 8 (greenfield or local-workspace), after the auto-push in branch (2), or after option **A** in greenfield. After option **C** at step 8, the run ends — do not ask. Stop and ask the user (single choice, "Deploy target").
<!--skill-flavor:deploy-reachability:end-->

<!--skill-flavor:local-workspace-delivery:start-->
   - **(1) `project_state == local-workspace`** → Studio Web auto-syncs saves to the remote SW project, so option A (manual push) is skipped — it would be redundant or break sync identity. The user may still want a local dev console. Stop and ask the user (single choice, "Delivery"):
<!--skill-flavor:local-workspace-delivery:end-->

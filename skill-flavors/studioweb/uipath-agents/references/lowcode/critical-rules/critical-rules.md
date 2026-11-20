<!--skill-flavor:solution-must-exist:start-->
10. **The open Studio Web solution is the only solution** — never create one. Scaffold agents into it with `uip agent init "<AgentName>"` from `/solution`.
<!--skill-flavor:solution-must-exist:end-->

<!--skill-flavor:flow-sdk-inline-agent-refresh-rule:start-->
21. **Inline-in-flow agents are authored by the `uipath-maestro-flow` skill.** It writes one `inlineAgent({...})` step, and `compile` emits the node, its edges and the `agent.json` sidecar — see [inline-agent.md](../../../../uipath-maestro-flow/references/inline-agent.md). Never hand-edit `bindings_v2.json`.
<!--skill-flavor:flow-sdk-inline-agent-refresh-rule:end-->

<!--skill-flavor:solution-resources-refresh:start-->
7. **Never run `uip solution resources refresh` in Studio Web; declare each tenant resource with `uip solution resources add`.** Studio Web keeps no `.uipx` on disk, so refresh always fails with `no .uipx manifest` and imports nothing. After `uip agent refresh` and `uip agent validate`, add every Orchestrator resource the agent uses (its Integration Service connections, memory spaces, indexes, external processes) that `uip solution resources list --source local --output json` does not list yet:
   - a connection: `uip solution resources add --source remote --kind Connection --cloud-key <ConnectionId> --output json`
   - any other kind: `uip solution resources add --source remote --kind <Kind> --name "<Name>" --folder-path "<Folder>" --output json` (for example `--kind MemorySpace`)

   Then list the local resources again and confirm each one is there. A resource the solution does not declare stays unresolved when the solution is deployed.
<!--skill-flavor:solution-resources-refresh:end-->

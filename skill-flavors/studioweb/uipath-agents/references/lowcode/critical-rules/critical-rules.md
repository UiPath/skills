<!--skill-flavor:solution-must-exist:start-->
10. **The open Studio Web solution is the only solution** — never create one. Scaffold agents into it with `uip agent init "<AgentName>"` from `/solution`.
<!--skill-flavor:solution-must-exist:end-->

<!--skill-flavor:flow-sdk-inline-agent-refresh-rule:start-->
21. **Inline-in-flow agents are authored by the `uipath-maestro-flow` skill.** It writes one `inlineAgent({...})` step, and `compile` emits the node, its edges and the `agent.json` sidecar — see [inline-agent.md](../../../../uipath-maestro-flow/references/inline-agent.md). Never hand-edit `bindings_v2.json`.
<!--skill-flavor:flow-sdk-inline-agent-refresh-rule:end-->

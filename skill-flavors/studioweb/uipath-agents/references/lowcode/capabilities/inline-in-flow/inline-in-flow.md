<!--skill-flavor:flow-sdk-prompt-wiring:start-->
The **flow side** — the trigger global and the node `agentInputVariables[]` binding (the only thing the converter turns into `JobArguments`) — is authored through the `uipath-maestro-flow` skill (Critical Rule 15). The full four-piece contract, the converter behavior, and the `content`↔`contentTokens` invariant + validator errors all live there: [inline-agent prompt-wiring guide § Wiring Flow Variables into Agent Prompts](../../../../../uipath-maestro-flow/references/author/plugins/inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).
<!--skill-flavor:flow-sdk-prompt-wiring:end-->

<!--skill-flavor:flow-sdk-inline-agent-debug:start-->
**Verify at `flow debug`, not after refresh:** `refresh` never fills `inputSchema` — it is non-empty only because you authored it (`DerivedFiles: 0` is normal and does **not** mean input is missing). The end-to-end check (run `uip maestro flow debug` and confirm the agent resolves the input rather than echoing the literal `input.<key>` token) is owned by the `uipath-maestro-flow` skill — see its [inline-agent guide § Debug](../../../../../uipath-maestro-flow/references/author/plugins/inline-agent/impl.md#debug).
<!--skill-flavor:flow-sdk-inline-agent-debug:end-->

<!--skill-flavor:flow-sdk-inline-agent-prompts:start-->
- `inputs.systemPrompt` / `inputs.userPrompt` — **do not write these keys.** A prompt string on the node makes the flow converter drop every `agentInputVariables[]` entry the prompt text does not reference. Empty strings fail `uip maestro flow validate`. The canonical prompts live in `agent.json.messages[]`. Validator behavior and the older-CLI fallback: [inline-agent guide § Refresh and Validate](../../../../../uipath-maestro-flow/references/author/plugins/inline-agent/impl.md#refresh-and-validate).
<!--skill-flavor:flow-sdk-inline-agent-prompts:end-->

<!--skill-flavor:flow-sdk-inline-agent-gate:start-->
<!--skill-flavor:flow-sdk-inline-agent-gate:end-->

<!--skill-flavor:flow-sdk-inline-agent-ordering:start-->
> **Ordering constraint:** run the final `uip agent refresh --inline-in-flow --bindings-target …` after all flow graph edits are complete. The `uipath-maestro-flow` skill owns direct `.flow` authoring for the inline-agent node, capability-resource nodes, and edges; refresh last so the generated bindings land in the flow project's `bindings_v2.json` before `uip solution resources refresh`. See the [Walkthrough](#walkthrough--end-to-end) for the correct sequence.
<!--skill-flavor:flow-sdk-inline-agent-ordering:end-->

<!--skill-flavor:flow-sdk-inline-agent-wiring:start-->
After creating the inline agent, the flow needs a `uipath.agent.autonomous` node whose `inputs.source` is the inline agent's `projectId` UUID, plus edges connecting it to the rest of the flow.

**Hand off to the `uipath-maestro-flow` skill for the actual node and edge authoring.** Per Critical Rule 15, this skill does not invoke flow operations directly. Tell the user:

> The inline agent has been scaffolded at `<FlowProjectDir>/<projectId>/`. To wire it into the flow, use the `uipath-maestro-flow` skill — pass it `projectId = <uuid>` so it can add a `uipath.agent.autonomous` node with `inputs.source = <uuid>` and connect the input/success edges via direct `.flow` authoring. **After all flow graph edits are complete**, run `uip agent refresh --inline-in-flow`, then `uip agent validate --inline-in-flow`; for inline agents with external capabilities, include `--bindings-target <FlowProjectDir>/bindings_v2.json` on the refresh call.

The node JSON shape that the flow skill must produce is documented in § Flow Node Structure below — keep it as a reference, not as a CLI walkthrough.
<!--skill-flavor:flow-sdk-inline-agent-wiring:end-->

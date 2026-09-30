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

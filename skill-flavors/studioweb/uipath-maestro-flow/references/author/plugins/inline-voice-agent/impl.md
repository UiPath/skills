<!--skill-flavor:voice-impl-scaffold-command:start-->

`<FlowProjectDir>` = `/solution/<FlowProject>` = `CurrentProject.AbsolutePath`; this form runs the real CLI in Studio Web and `--conversational` is honoured.
<!--skill-flavor:voice-impl-scaffold-command:end-->

<!--skill-flavor:voice-delivery-binding-note:start-->
   Omit the Delivery binding and `flow debug` still works (it back-fills from `inputSchema`) while the package built on publish ships empty `JobArguments` — the published call gets no inputs. Full contract: [inline-agent/impl.md § Wiring Flow Variables into Agent Prompts](../inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).
<!--skill-flavor:voice-delivery-binding-note:end-->

<!--skill-flavor:voice-validate-and-debug:start-->
## Validate and Debug

```bash
uip maestro flow format /solution/<FlowProject>/new.flow --output json
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
```
<!--skill-flavor:voice-validate-and-debug:end-->

<!--skill-flavor:voice-validate-and-debug-2:start-->
There is no local pack step in Studio Web (`uip flow pack` is a no-op). The package built on publish (`uip solution publish --location "<FolderPathOrKey>"`) serializes the voice agent to an `Orchestrator.StartInlineAgentJob` serviceTask that **embeds the complete built agent definition** (`agentDefinition` in the BPMN context: agent.json + resources + features), and sets `runtimeOptions.isConversational: true` in the generated `operate.json`. That embedding is why publish and debug fail early when the agent directory is missing — a package without it would deploy and then drop every call, so this never ships silently.
<!--skill-flavor:voice-validate-and-debug-2:end-->

<!--skill-flavor:voice-validate-and-debug-3:start-->
An **inbound** flow cannot be debugged: only a real call can raise a `core.trigger.voice`, so `uip flow debug` has nothing to answer and the run never advances (the Node CLI states it as `Inbound voice flows cannot be debugged from the CLI.`).

The inbound test loop is publish, bind a number (§ Bind an Inbound Phone Number), then dial it. Swapping the trigger for a manual one lifts the rejection but leaves the inbound flow itself unexercised.

An **outbound** flow does run under `uip flow debug`, and it dials for real. The host debug waits at most 5 minutes for the run to finish and prints only at exit — call it with `timeoutSeconds` up to 600 and keep the conversation short enough to end inside that window (`--timeout` is not honoured). If it prints `TimedOut after 300s` with `(no run logs emitted)`, ask the user to run Debug from the designer. Get user consent first and confirm the `to` number — the flow **places a real phone call**.
<!--skill-flavor:voice-validate-and-debug-3:end-->

<!--skill-flavor:voice-bind-inbound-number:start-->
An inbound flow does nothing until a trunk points at its deployed process. Nothing in the `.flow` carries the number — the binding is made against the **release key** after publish.

> **Confirm with the user before running step 1.** Publishing mutates the tenant, and this skill never defaults to it — ask the destination first (`uip solution publish --help` lists `PublishLocations`); see [operate/ship.md](../../../operate/ship.md).

```bash
# 1. publish the open solution — nothing to pack or upload, the flow is already in Studio Web
#    (no --location publishes to the personal workspace immediately)
uip solution publish --location "<FolderPathOrKey>" --output json

# 2. read the release key + folder key back
uip or processes list --folder-path "<FolderPath>" --output json   # Key, FolderKey

# 3. point the trunk at it
uip conversational trunks assign <E164-number> \
  --process-key <Key> --folder-key <FolderKey> --yes --output json
```
<!--skill-flavor:voice-bind-inbound-number:end-->

<!--skill-flavor:voice-bind-inbound-number-2:start-->
- `<FolderPath>` in step 2 is the folder the publish destination deploys into — the personal workspace or the Orchestrator folder chosen in step 1. No publish output confirms deployment; confirm with `uip or packages versions <name> --folder-path <path>` before step 3.
<!--skill-flavor:voice-bind-inbound-number-2:end-->

<!--skill-flavor:voice-bind-inbound-number-3:start-->
Outbound needs no binding step — `inputs.from` names the trunk directly, so the flow is complete once `flow debug` places its call. To run it on a schedule or trigger it as a process, publish the open solution the same way (`uip solution publish --location "<FolderPathOrKey>"`, consent gate per SKILL.md rule #2) — there is nothing to upload; the flow is already in Studio Web.
<!--skill-flavor:voice-bind-inbound-number-3:end-->

<!--skill-flavor:voice-impl-debug-table:start-->
| `flow validate` / publish: `voice agent nodes are not supported inside subflows` | The voice agent node was placed in a `core.subflow`. Only top-level voice nodes get an embedded definition, so the package build raises the same thing validate does | Move the node to the top-level flow. There is no flag for this and no partial support — a subflow voice agent would ship a serviceTask with no `agentDefinition` |
| `flow debug` on an inbound flow fails or never advances | The flow starts from `core.trigger.voice`, which only a real call raises | Not a bug and not fixable locally — publish, bind a number, dial it (§ Bind an Inbound Phone Number). Do not swap in a manual trigger to force a run |
| Publish / `flow debug`: `Missing agent definition for voice agent node …` | Agent directory deleted or moved after validate | Restore `<FlowProjectDir>/<projectId>/agent.json` or fix `inputs.source`; the BPMN is never written without the embedded definition |
| Publish / `flow debug`: `Converted BPMN carries no agentDefinition for voice agent node(s) …` | Different failure from the row above — the agent directory is fine, but the host's bundled `@uipath/flow-converter` does not forward `voiceAgentDefinitions` to the BPMN serializer. The check catches it rather than shipping a package that deploys and drops every call | The CLI version is fixed by the Studio Web host and cannot be probed or updated — report the gap to the user. Nothing in the project can work around an old converter |
| `registry get` reports the voice type not found | The host's CLI predates voice support (the types ship in its bundled registry, so this is a CLI-version problem, not a tenant one) | The CLI version is fixed by the Studio Web host and cannot be updated — report the gap |
| `uip conversational trunks …`: `unknown command 'trunks'` (and `uip conversational --help` lists no `trunks`) | The host's CLI predates the trunk commands. Independent of node support: the voice node types ship in the bundled registry, so authoring, `registry get`, and `validate` all work on a CLI whose `conversational` tool has no `trunks` | The CLI version is fixed by the Studio Web host and cannot be probed or updated — report the gap. A trunk's number and direction flags are also readable from the Phone numbers page |
| Call never connects on a tenant that publishes fine | No SIP trunk provisioned, or the number lacks the direction your topology needs — not detectable from the CLI at author time | `uip conversational trunks list` to see whether the tenant has any trunk at all. Adding a number, enabling a direction on it, and releasing it are portal-only — send the user to `{baseUrl}/{orgName}/agents_/phone-numbers` (e.g. `https://alpha.uipath.com/conversationalagents/agents_/phone-numbers`). Raise it as an Open Question rather than re-authoring the flow |
| Call connects but the agent is silent / call drops immediately | The published package was built without the embedded `agentDefinition` (agent directory or `settings.voice` broken at publish time) | Restore the agent directory and `settings.voice`, re-validate, and publish again — the host builds the package server-side |
| Outbound call never dials | `from` is not a SIP trunk number on the tenant, or `to` is malformed, or the trunk exists but is not outbound-enabled | `uip conversational trunks list --direction outbound --output json`; use a number with `outboundEnabled: true` for `from`; `to` must be E.164 in a literal binding. Turning outbound *on* for an existing number is portal-only — the Phone numbers page, `{baseUrl}/{orgName}/agents_/phone-numbers` |
| Inbound number rings but nothing runs | Trunk not bound, bound to a different process, or bound to an older build | `uip conversational trunks list --direction inbound --output json` — check `processName` and that `entryPoint` matches the trigger's `inputs.entryPointId`; re-run `trunks assign` (§ Bind an Inbound Phone Number) |
<!--skill-flavor:voice-impl-debug-table:end-->

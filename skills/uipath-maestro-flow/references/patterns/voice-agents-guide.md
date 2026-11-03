# Pattern: `voice-agents`

A phone call handled by voice agents. Each agent owns a stretch of one live
call, and the flow passes the call along; it does not drive turns the way a chat
flow does. Node details: [voice.md](../voice.md).

## Why it works

- **The whole call happens inside the voice agent node.** There is no turn loop
  to build. A handoff is the flow passing the same call to the next agent.
- **Every voice step reads the same call context.** The trigger's (or the dialed
  call's) whole `callContext` object goes to every voice agent and to `endCall`.
- **Hang up before slow work.** `endCall` comes before the process step, so the
  caller is not left waiting on the line.
- **Voice agents have no typed outputs.** Route a handoff on the session's end
  `reason` (`uipath__voice_session.reason`), which the triage agent sets.

## Shape

The `incoming-call` variant:

| Step | Node | Builder | Role |
| --- | --- | --- | --- |
| `start` | `core.trigger.voice` | `.trigger(voiceTrigger())` | Entry: replaces the manual trigger |
| `voiceIntake` | `uipath.agent.voice` | `voiceAgent({ callContext: out('start', 'callContext') })` | Mechanism |
| `endCall` | `uipath.conversational.voice.end-call` | `endCall({ callContext })` | Mechanism: before the process |
| `startProcess` | the process's node | per SKILL.md's node table | Placeholder |
| `endSubmitted` | `core.control.end` | `.return(...)` | Entry: the flow continues here when steps follow |

| From | Port | To |
| --- | --- | --- |
| `start` | `output` | `voiceIntake` |
| `voiceIntake` | `success` | `endCall` |
| `endCall` | `success` | `startProcess` |
| `startProcess` | | `endSubmitted` |

`voiceIntake`'s prompt collects what the process needs, one question at a time,
and confirms before finishing. `startProcess` reads `out('voiceIntake')`. What the
caller said is lost if they hang up before the agent ends the session.

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| `incoming-call` | (default) | The shape above |
| `handoff` | Does the caller need one of several specialists? | A triage agent, a switch on its session reason, one specialist per route |
| `remember-caller` | Should the next call know about this one? | After `endCall`: read the conversation, distill it, save it |

**`handoff`.** `triageAgent` finds out what the caller needs and ends its own
session, not the call, with `reason` set to a route name. `routeCall`, a switch
on `$vars.triageAgent.output.uipath__voice_session.reason`, sends each route to
its specialist voice agent and `default` to a general agent. Every specialist
reads the same `callContext` and converges on one `endCall`. Change a route name
in the triage prompt and the switch together. The canvas version places the call
with `createOutgoingCall`; for an incoming call, start with `voiceTrigger()` and
bind every `callContext` to the trigger.

**`remember-caller`.** After `endCall`, `readConversation`
(`conversationContext({ conversationId: out('start', 'callContext.conversationId') })`)
reads the transcript, `distillMemory` (an inline agent) returns `summary`,
`preferences` and `openItems`, and `saveMemory` writes them to the caller's record,
such as a Data Fabric entity. The canvas attaches a lookup on that record to the
voice agent as a tool; `voiceAgent()` takes no tools, so read the record before
the agent and pass it in through `inputs`.

## What to bind

- **Each voice agent**: system prompt, voice model and persona (`voice.md`). The
  `callContext` is the whole object, never a field inside it
  (`VOICE_CALL_CONTEXT_NOT_OBJECT`).
- **`startProcess` / `saveMemory`**: the downstream, chosen by rule 1.
- **`createOutgoingCall`** (outbound only): E.164 `from` and `to`; `from` must be
  provisioned on the tenant.

## Adapting it

The trigger comes with the pattern, so an inbound pattern begins the flow. An
outbound call can sit mid-flow, started by `createOutgoingCall`. Nothing local
places a call: a green `validate` proves the wiring, and the call itself is
platform evidence ([voice.md](../voice.md#evidence-boundary)).


# Voice

*Exact signatures, fields, and defaults: [`voiceTrigger()`](api.md#voicetrigger-function), [`createOutgoingCall()`](api.md#createoutgoingcall-function), [`endCall()`](api.md#endcall-function), [`voiceAgent()`](api.md#voiceagent-function).*

A voice call is a conversation with an audio front end. It is identified by a
`callContext` OBJECT — not a bare conversation id — and that object is what
every voice step is keyed by.

```ts
// Inbound: the platform hands you the call.
export default flow('support-line')
  .trigger(voiceTrigger())
  .step('greet', voiceAgent({
    systemPrompt: 'Greet the caller and find out why they called.',
    callContext: out('start', 'callContext'),
    voice: { model: 'gemini-3.1-flash-live-preview', persona: 'Kore' },
  }))
  .step('hangUp', endCall({ callContext: out('start', 'callContext') }))
  .build();

// Outbound: the flow places the call.
.step('dial', createOutgoingCall({ from: '+15550001111', to: input('customerPhone') }))
.step('talk', voiceAgent({ systemPrompt: '…', callContext: out('dial', 'callContext') }))
```

## The call context

`out('start', 'callContext')` (inbound) or `out('<dialStep>', 'callContext')`
(outbound) is the whole object — `{ type, id, conversationId, … }` — and that is
what to pass. **Reaching inside it is the mistake this family invites**:
`out('dial', 'callContext.conversationId')` is a string, the node's schema types
the field as `object`, and a scalar there passes the file's schema and then
fails at dispatch. `check` catches it (`VOICE_CALL_CONTEXT_NOT_OBJECT`).

Both numbers on `createOutgoingCall` are E.164 — a leading `+` and 7–15 digits
(`'+15551234567'`). `from` must be a number provisioned on the tenant's
telephony provider; anything else is rejected when the call is placed, not when
the flow is validated. `endCall` reads `out('<step>', 'ended')`.

## How the agent sounds

`voice` takes a VOICE model (a live/realtime one — not the text models
`inlineAgent` takes) and one of THAT model's personas; the two travel together:

| Model | Personas |
| --- | --- |
| `gemini-3.1-flash-live-preview` (default) | Aoede, Charon, Fenrir, Kore, Leda, Orus, Puck, Zephyr |
| `gpt-realtime-2` | alloy, ash, ballad, coral, echo, sage, shimmer, verse |

Omit `voice` entirely for the platform default. `maxIterations` is capped at
**8**, tighter than a text agent's 100, because a caller is waiting on the turn.
There is no prompt templating and no declared `returns`: the turn arrives as
audio and the definition declares what comes back. Compile writes a
voice-dialect `<source>/agent.json` sidecar (`settings.mode: 'voice'`) beside
the `.flow`.

## Evidence boundary

`uipath.agent.voice` is served on this tenant; the trigger and the two call
actions are `AvailableOnTenant: false` and ship bundled from the workbench
manifests. Nothing local dials a phone: a green ladder proves the node types,
the call-context threading and the voice settings. A real call, real audio, and
what the caller heard are platform evidence.

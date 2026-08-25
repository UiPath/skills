# Conversational

*Exact signatures, fields, and defaults: [`conversationTrigger()`](api.md#conversationtrigger-function), [`waitForMessage()`](api.md#waitformessage-function), [`sendMessage()`](api.md#sendmessage-function), [`conversationContext()`](api.md#conversationcontext-function), [`conversationalAgent()`](api.md#conversationalagent-function).*

A chat-driven flow. A person opens a conversation; the flow waits for their
message, answers it, and can post messages of its own. Every step is keyed by a
`conversationId`, which the conversation TRIGGER publishes as
`out('start', 'conversationId')`.

```ts
export default flow('support-chat')
  .trigger(conversationTrigger())
  .step('listen', waitForMessage({ conversationId: out('start', 'conversationId') }))
  .step('reply', conversationalAgent({
    model: 'gpt-5.4',
    systemPrompt: 'You are a support agent. Be brief.',
    settings: { context: out('listen', 'conversationContext') },
  }))
  .step('closing', sendMessage({
    conversationId: out('start', 'conversationId'),
    exchangeId: out('listen', 'conversationContext.latestExchangeId'),
    content: 'Anything else I can help with?',
  }))
  .build();
```

## Conversations, exchanges, and messages

Three nested things, and the field names follow them:

- a **conversation** is the whole thread (`conversationId`);
- an **exchange** is one user turn plus the answers to it (`exchangeId`);
- a **message** is one utterance inside an exchange.

`waitForMessage` returns the conversation CONTEXT, so the exchange to answer is
a path inside it: `out('<waitStep>', 'conversationContext.latestExchangeId')`,
and the transcript is `…conversationContext.messages`. (`out(step, path)`
already inserts `.output` — do not write it again.)

## Waiting versus reading

`waitForMessage` **suspends** the flow — it is a `bpmn:IntermediateCatchEvent`
on `Maestro.ReceiveMessageEvent`, the same mechanism as `waitForEvent`, so the
run parks until the person speaks. `conversationContext` does NOT wait: it reads
the transcript so far and continues. Reach for the first when the flow's next
step depends on what the person says next, the second when it only needs
history. Both cap how much history they return (`numExchanges` /
`exchangeLimit`, 1–40, platform default 20).

## Saying something: agent or flow

`sendMessage` posts a message the FLOW composed — the role is always
`assistant` and the content is Markdown (the node's only supported type), so
neither is authored. `conversationalAgent` posts what a MODEL composed, reading
the turn from `settings`:

- `'simple'` mode (the default) takes ONE binding, `context`, and the platform
  derives the conversation id, exchange id, transcript and user settings from
  it. This is what you want almost always.
- `'custom'` mode binds each field yourself, for a turn assembled from more
  than one source; `conversationId` is then required.

Either way the four derived fields are what the runtime reads — the platform's
own editor calls them the source of truth and its validator rejects a node
without `conversationId`, so the SDK emits them from your `context` binding
rather than leaving them out. The agent's reply is
`out('<step>', 'uipath__agent_response_messages')`, and compile writes a stable
`<source>/agent.json` sidecar beside the `.flow` as it does for `inlineAgent`.

## Evidence boundary

The whole family is `AvailableOnTenant: false` today — the definitions are
bundled from the workbench manifests, so a flow compiles and `validate`s
offline, but nothing local starts a conversation or delivers a message. A green
ladder proves the node types, the conversation/exchange wiring and the derived
turn settings. A real thread, a real reply, and the agent's answer quality are
platform evidence.

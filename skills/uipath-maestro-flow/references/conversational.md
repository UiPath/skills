# Conversational

*Exact signatures, fields, and defaults: `conversationTrigger()`, `waitForMessage()`, `sendMessage()`, `conversationContext()`, `conversationalAgent()`.*

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

## At a glance

Work a live CHAT: wait for the person's message, answer it, post a reply. Every
step is keyed by a `conversationId` — the conversation trigger publishes it.

Signatures: `.trigger(conversationTrigger({ welcomeTitle?, welcomeDescription?, startingPrompts?, personalWorkspaceConnectionsOnly? }))`; `waitForMessage({ conversationId, numExchanges? })`; `conversationalAgent({ model, systemPrompt, settings })`; `sendMessage({ conversationId, exchangeId, content, endExchange? })`; `conversationContext({ conversationId, exchangeLimit? })`.

```ts
.trigger(conversationTrigger())
.step('listen', waitForMessage({ conversationId: out('start', 'conversationId') }))
.step('reply', conversationalAgent({ model: 'gpt-5.4', systemPrompt: 'Answer briefly.',
  settings: { context: out('listen', 'conversationContext') } }))
```

`waitForMessage` SUSPENDS the flow (a catch event), it does not poll. Use `sendMessage` when the flow decides what to say, an agent when the model does.

## The chat's appearance

What the chat shows before the user types is set on the trigger.
Every field is optional; `conversationTrigger()` with no argument is a chat with no welcome text or prompts, and the switch below is still on.

```ts
.trigger(conversationTrigger({
  welcomeTitle: 'Library desk',
  welcomeDescription: 'Ask about loans, renewals and holds.',
  startingPrompts: [
    'Renew my loans',
    { displayPrompt: 'Place a hold', actualPrompt: 'I want to place a hold on a book.' },
  ],
}))
```

A starting prompt is a chip: the user sees `displayPrompt`, and the agent receives `actualPrompt`.
A string sets both `displayPrompt` and `actualPrompt`.
Leave `id` out; compile mints a stable one, and decompile prints it back so a recompile keeps it.
`check` refuses a prompt with no display prompt (`CONVERSATION_TRIGGER_DISPLAY_PROMPT_REQUIRED`), because the chat drops it.
`personalWorkspaceConnectionsOnly` limits the chat's connection settings menu to personal workspace connections.
It defaults to `true`, as the designer sets on a new trigger; set `false` to show every connection.

The appearance is the trigger's 1.3 definition, which `conversationTrigger()` writes by default.
Decompiled source of an older flow pins `{ version: '1.0' }`, which has no appearance, and compile refuses one there (`CONVERSATION_TRIGGER_APPEARANCE_VERSION`); drop the pin to add one, and set `personalWorkspaceConnectionsOnly: false` to keep the chat's full connection menu as it was.

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

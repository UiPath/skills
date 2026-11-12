# Conversational

Exact signatures, fields, and defaults: `conversationTrigger()`, `waitForMessage()`, `sendMessage()`, `conversationContext()`, `conversationalAgent()`.

A chat flow waits for a person's message, answers it, and may post messages. Every step uses the `conversationId` published by the conversation TRIGGER as `out('start', 'conversationId')`.

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

Signatures: `.trigger(conversationTrigger({ welcomeTitle?, welcomeDescription?, startingPrompts?, personalWorkspaceConnectionsOnly? }))`; `waitForMessage({ conversationId, numExchanges? })`; `conversationalAgent({ model, systemPrompt, settings, tools?, context?, escalation? })`; `sendMessage({ conversationId, exchangeId, content, endExchange? })`; `conversationContext({ conversationId, exchangeLimit? })`.

```ts
.trigger(conversationTrigger())
.step('listen', waitForMessage({ conversationId: out('start', 'conversationId') }))
.step('reply', conversationalAgent({ model: 'gpt-5.4', systemPrompt: 'Answer briefly.',
  settings: { context: out('listen', 'conversationContext') } }))
```

`waitForMessage` SUSPENDS the flow as a catch event; it does not poll. Use `sendMessage` for flow-composed text and `conversationalAgent` for model-composed text.

## The chat's appearance

Use `@uipath/maestro-builder-sdk` 6.88.0 or later. Older SDKs' `conversationTrigger()` takes no argument and writes the 1.0 trigger,
<!--skill-flavor:conversation-appearance-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:conversation-appearance-sdk-upgrade:end-->

The trigger controls pre-input chat appearance. All fields are optional; `conversationTrigger()` has no welcome text or prompts, while the switch below remains on.

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

A starting prompt is a chip: the user sees `displayPrompt` and the agent receives `actualPrompt`; a string sets both. Omit `id`: compile mints a stable one and decompile prints it back, preserving recompilation. `check` refuses a prompt without a display prompt (`CONVERSATION_TRIGGER_DISPLAY_PROMPT_REQUIRED`) because the chat drops it.

`personalWorkspaceConnectionsOnly` limits the connection-settings menu to personal workspace connections. It defaults to `true` for a new trigger; set `false` to show every connection.

The default appearance is the trigger's 1.3 definition. Decompiled older flows pin `{ version: '1.0' }`, which has no appearance, and compile refuses one there (`CONVERSATION_TRIGGER_APPEARANCE_VERSION`). Drop the pin to add appearance, and set `personalWorkspaceConnectionsOnly: false` to preserve the former full connection menu.

## Conversations, exchanges, and messages

A **conversation** is the whole thread (`conversationId`); an **exchange** is one user turn plus its answers (`exchangeId`); a **message** is one utterance within an exchange.

`waitForMessage` returns conversation CONTEXT. Answer with `out('<waitStep>', 'conversationContext.latestExchangeId')`; read the transcript at `…conversationContext.messages`. `out(step, path)` already inserts `.output`; do not write it again.

## Waiting versus reading

`waitForMessage` **suspends** the flow as a `bpmn:IntermediateCatchEvent` on `Maestro.ReceiveMessageEvent`, like `waitForEvent`, parking the run until the person speaks. `conversationContext` only reads the transcript and continues. Use the former when the next step depends on what the person says next, and the latter for history. Both limit returned history to 1–40 (`numExchanges` / `exchangeLimit`), with platform default 20.

## Saying something: agent or flow

`sendMessage` posts flow-composed Markdown; its role is always `assistant`, and neither role nor content type is authored. `conversationalAgent` posts model-composed text and reads the turn from `settings`:

- `'simple'` mode (default) takes one `context` binding; the platform derives conversation id, exchange id, transcript, and user settings. Use it almost always.
- `'custom'` mode binds each field for a turn assembled from multiple sources; `conversationId` is required.

These four derived fields are runtime inputs and the editor's source of truth; its validator rejects a node without `conversationId`, so the SDK emits them from `context` rather than omitting them. The reply is `out('<step>', 'uipath__agent_response_messages')`; compile writes a stable `<source>/agent.json` sidecar beside the `.flow`, as for `inlineAgent`.

## Tools, context and escalations

`conversationalAgent` accepts the same `tools`, `context`, and `escalation` options as `inlineAgent` ([agent-resources.md](agent-resources.md)). For instance a tool the chat client runs:

```ts
conversationalAgent({
  model: 'gpt-5.4', systemPrompt: 'Help the customer.',
  settings: { context: out('wait', 'conversationContext') },
  tools: [{ kind: 'clientside', name: 'showOrder', inputs: { orderId: 'string' } }],
})
```

The SDK versions required by these options, their `check` codes, and what decompile does not yet carry back are documented here:
[agent-resources.md](agent-resources.md#voice-and-conversational-agents).

## Evidence boundary

The whole family is `AvailableOnTenant: false` today. Definitions come from workbench manifests, so a flow compiles and `validate`s offline, but nothing local starts conversations or delivers messages. A green ladder proves node types, conversation/exchange wiring, and derived turn settings; real threads, replies, and agent answer quality require platform evidence.

/**
 * CAPABILITY: work a live CHAT — wait for a message, answer it, post a reply.
 *
 * Every conversational step is keyed by a `conversationId`, and
 * `conversationTrigger()` publishes it as `out('start', 'conversationId')`.
 *
 * `waitForMessage` SUSPENDS the flow — it is a catch event, not a poll. Use
 * `conversationalAgent` when the model decides what to say and `sendMessage`
 * when the flow does; this example shows both, so the agent answers and the
 * flow closes the exchange itself.
 *
 * Generic scenario: answer a question at a library help desk.
 */
import {
  flow, conversationTrigger, waitForMessage, conversationalAgent, sendMessage,
  out, types,
} from '@uipath/flow-sdk';

export default flow('library-desk-chat')
  .name('LibraryDeskChat')
  .version('1.0.0')
  .output({ answered: types.string })
  .trigger(conversationTrigger())
  .step('listen', waitForMessage({
    conversationId: out('start', 'conversationId'),
  }))
  .step('answer', conversationalAgent({
    model: 'gpt-5.4',
    systemPrompt: 'Answer library questions in one or two sentences. Say so when unsure.',
    settings: { mode: 'simple', context: out('listen', 'conversationContext') },
  }))
  .step('closeExchange', sendMessage({
    conversationId: out('start', 'conversationId'),
    exchangeId: out('listen', 'exchangeId'),
    content: 'Ask again any time — the desk is open until six.',
    endExchange: true,
  }))
  .return({ answered: out('answer') })
  .build();

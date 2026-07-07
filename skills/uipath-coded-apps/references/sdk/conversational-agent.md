# Conversational Agent — Session Choreography & Chat Wiring

Signatures/params/examples for services, event-helper classes, options, enums: `dist/conversational-agent/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> **Scope fork warning:** scopes differ per METHOD GROUP inside this one service (agent reads vs conversation create/update vs sessions vs feedback vs user settings each need a different scope set). Never assume service-uniform scopes — check the shipped per-method table; task-level bundles: [../oauth-scopes.md](../oauth-scopes.md).

## Session Lifecycle (WebSocket)

The real-time WebSocket session is the core of this domain. Event ordering spans five helper classes (session → exchange → message → content part / tool call) and is NOT derivable from the per-class types — follow it exactly:

```
startSession → onSessionStarted → startExchange → sendMessageWithContentPart →
  onExchangeStart (agent response) → onMessageStart → onContentPartStart → onChunk →
  ... → sendSessionEnd
```

Register handlers top-down: exchange handlers inside `onExchangeStart`, message handlers inside `onMessageStart`, content-part handlers inside `onContentPartStart`. Every `on*` handler returns a cleanup function — capture and call on unmount.

## Chat Interface Wiring — Mandatory Design Decisions

**IMPORTANT:** This pattern matches the working sample app in `samples/conversational-agent-app/`. The key design decisions:

1. **Add the assistant placeholder message IMMEDIATELY in `sendMessage()`** — before `startExchange()`. Do NOT wait for `onMessageStart`. This ensures the typing dots show up instantly.
2. **Pre-register exchangeId → assistantMessageId mapping** so `onExchangeStart` can wire up handlers for the right message.
3. **Use a single `isStreaming` state** — set `true` in `sendMessage()`, set `false` in `onExchangeEnd()` (not `onMessageEnd`).
4. **Show bouncing dots inside the assistant message bubble** when content is empty and `isStreaming` is true. Once chunks arrive, the dots are replaced by growing text.
5. **Use `echo: true`** on `startSession()` so all exchanges (including user-initiated) fire through `onExchangeStart` — one code path renders both user and assistant messages.

Handler wiring skeleton (session setup once per conversation; UI omitted):

```typescript
const session = conv.startSession({ echo: true });
sessionRef.current = session;

// Handle all exchanges (both user-initiated via echo and agent responses)
session.onExchangeStart((exchange) => {
  // Look up the pre-registered assistant message ID for this exchange
  const assistantId = exchangeAssistantIdRef.current.get(exchange.exchangeId);
  if (!assistantId) return;
  setIsStreaming(true);

  exchange.onMessageStart((message) => {
    if (!message.isAssistant) return;
    message.onContentPartStart((contentPart) => {
      if (contentPart.isMarkdown || contentPart.isText) {
        contentPart.onChunk((chunk) => {
          if (chunk.data) appendToMessage(assistantId, chunk.data);
        });
      }
    });
  });

  exchange.onExchangeEnd(() => {
    exchangeAssistantIdRef.current.delete(exchange.exchangeId);
    markMessageDone(assistantId);
    setIsStreaming(false);
  });
});

// Cleanup on unmount / agent switch
return () => {
  convRef.current?.endSession();
  sessionRef.current = null;
};
```

Sending a message — pre-register the mapping BEFORE starting the exchange:

```typescript
// Add assistant placeholder IMMEDIATELY — shows typing dots right away
const assistantId = `assistant-${Date.now()}`;
addMessages(userMessage, { id: assistantId, role: 'assistant', content: '', isStreaming: true });
setIsStreaming(true);

// Pre-register the exchange → assistant mapping BEFORE starting the exchange
const exchangeId = `exchange-${Date.now()}-${crypto.randomUUID().slice(0, 12)}`;
exchangeAssistantIdRef.current.set(exchangeId, assistantId);

// Start exchange with pre-determined ID and send user message
const exchange = sessionRef.current.startExchange({ exchangeId });
const message = exchange.startMessage({ role: MessageRole.User });
await message.sendContentPart({ data: input });
message.sendMessageEnd();
```

## Tool Call Confirmation (Interrupts)

```typescript
session.onExchangeStart((exchange) => {
  exchange.onMessageStart((message) => {
    if (message.isAssistant) {
      // Handle tool call confirmations
      message.onInterruptStart(({ interruptId, startEvent }) => {
        // Show confirmation dialog to user
        const confirmed = window.confirm(`Agent wants to use tool. Allow?`);
        message.sendInterruptEnd(interruptId, { approved: confirmed });
      });
    }
  });
});
```

## OAuth Client Setup

See [oauth-client-setup.md](../oauth-client-setup.md) for browser automation steps to configure the External Application in UiPath Cloud.

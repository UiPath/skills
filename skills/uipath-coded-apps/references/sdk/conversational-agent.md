# Conversational Agent — Session Choreography & Chat Wiring

Signatures/params/examples for services, event-helper classes, options, enums: `dist/conversational-agent/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> **Scope fork warning:** scopes differ per METHOD GROUP inside this one service (agent reads vs conversation create/update vs sessions vs feedback vs user settings each need a different scope set). Never assume service-uniform scopes — check the shipped per-method table; task-level bundles: [../oauth-scopes.md](../oauth-scopes.md).

## Session Lifecycle (WebSocket)

The event flow is documented IN the package — read it there: the module JSDoc in `dist/conversational-agent/index.d.ts` has a mermaid graph of the full stream hierarchy (session → exchange → message → content part / tool call) plus an end-to-end walkthrough, and `onExchangeStart`'s JSDoc carries complete nested examples: streaming chunks, whole-message handling (`onMessageCompleted`), tool-call events, and interrupt confirmation (with the `startEvent.type` check — use that version, not a blind approve).

Skill-only discipline the JSDoc doesn't state: every `on*` registration returns a cleanup function — capture them and call on unmount / agent switch, or handlers leak across React re-renders.

## Chat Interface Wiring — Mandatory Design Decisions

**IMPORTANT:** This pattern matches the working sample app in the SDK repo (`uipath-typescript/samples/conversational-agent-app/` — repo only, not shipped in the npm package). The key design decisions:

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

## OAuth Client Setup

See [oauth-client-setup.md](../oauth-client-setup.md) for browser automation steps to configure the External Application in UiPath Cloud.

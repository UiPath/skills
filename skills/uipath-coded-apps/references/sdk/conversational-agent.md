# Conversational Agent Reference — Scopes, Conventions, Traps

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/conversational-agent/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

## Imports

```typescript
import { ConversationalAgent, Exchanges, Messages } from '@uipath/uipath-typescript/conversational-agent';
```

Types, options, enums, and event helper classes export from the same subpath as their service class.

## Scopes

Combined scopes needed: `OR.Execution` `OR.Folders` `OR.Jobs` `ConversationalAgents` `Traces.Api`

- Agents (getAll, getById): `OR.Execution` or `OR.Execution.Read`
- Conversations (create): `OR.Execution`, `OR.Folders`, `OR.Jobs`
- Conversations (read): `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read`
- Conversations (update/delete): `OR.Execution`, `OR.Jobs`
- Conversations (uploadAttachment / getAttachmentUploadUri): `OR.Execution`, `OR.Jobs`
- startSession: `OR.Execution`, `OR.Jobs`, `ConversationalAgents`
- Exchanges (read): `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read`
- Feedback: `OR.Execution`, `OR.Jobs`, `Traces.Api`
- User Settings (getSettings): `OR.Users` or `OR.Users.Read`
- User Settings (updateSettings): `OR.Users`

See [../oauth-scopes.md](../oauth-scopes.md) for the app-wide scope catalog.

## Traps

### Agent-attached shorthand

Each agent returned by `getAll()` or `getById()` carries `agent.conversations` — a scoped conversation service where `agentId` and `folderId` are pre-filled. Use `agent.conversations.create(options?)` instead of `conversationalAgent.conversations.create(agentId, folderId, options?)`. Conversations returned by `create()`/`getById()`/`getAll()` likewise carry attached methods (`conversation.exchanges`, `conversation.startSession()`, `conversation.uploadAttachment()`, …) — prefer them. Full list in the `.d.ts`.

### User settings — fields not fully published

`conversationalAgent.user.getSettings()` includes `name`, `email`, `role`, `department`, `company`, `country`, `timezone`, plus identifiers and timestamps. **Note:** Exact fields are not fully published; check the TypeScript types. `updateSettings()` is a partial update — send only the fields you want to change; pass `null` to clear a field.

### `disconnect()` vs `endSession()`

`conversations.disconnect()` tears down the underlying WebSocket connection and ends **all** active sessions for this service. Use on app unmount / agent switch to release the socket; `endSession(conversationId)` ends just one conversation's session.

### `uploadAttachment()` vs `getAttachmentUploadUri()`

`uploadAttachment(id, file)` handles the two-step upload (create attachment entry, then upload to blob storage). `getAttachmentUploadUri(conversationId, fileName)` is the lower-level alternative — registers the attachment and returns a pre-signed upload URL but does NOT upload bytes. Use this when you need to stream large files yourself or upload from a non-`File` source. Service-level only (no conversation-attached shorthand).

```typescript
const { uri, fileUploadAccess } = await conversationalAgent.conversations
  .getAttachmentUploadUri(conversationId, file.name);

await fetch(fileUploadAccess.url, {
  method: fileUploadAccess.verb,
  body: file,
  headers: { 'Content-Type': file.type },
});

// Reference `uri` in subsequent messages
```

## Real-Time Sessions (WebSocket)

The core of conversational agent is the real-time WebSocket session. This enables streaming chat with agents. This lifecycle choreography is NOT derivable from the types — follow it exactly.

### Session Lifecycle

```
startSession → onSessionStarted → startExchange → sendMessageWithContentPart →
  onExchangeStart (agent response) → onMessageStart → onContentPartStart → onChunk →
  ... → sendSessionEnd
```

### Starting a Session

```typescript
const session = conversation.startSession({ echo: true });
// or
const session = conversationalAgent.conversations.startSession(conversationId, { echo: true });
```

`echo: true` means events you emit are also dispatched back to your handlers (useful for rendering your own messages in the UI).

### SessionStream API

The session object (`SessionStream`) provides:

**Sending:**
- `session.startExchange(options?)` — returns `ExchangeEventHelper` to send messages
- `session.sendSessionEnd()` — end the session
- `session.sendMetaEvent(metaEvent)` — send metadata
- `session.sendErrorStart(args)` / `session.sendErrorEnd(args)` — send error events
- `session.emit(event)` — emit raw conversation event

**Receiving (register handlers):**
- `session.onSessionStarted(handler)` — session is ready
- `session.onSessionEnding(handler)` — session is about to end
- `session.onSessionEnd(handler)` — session ended
- `session.onExchangeStart(handler)` — new exchange started (agent responding)
- `session.onLabelUpdated(handler)` — conversation label changed

**State:**
- `session.exchanges` — iterator over active exchanges
- `session.getExchange(exchangeId)` — get specific exchange
- `session.conversationId` — the conversation ID

All `on*` handlers return a cleanup function: `const cleanup = session.onExchangeStart(handler); cleanup();`

### ExchangeEventHelper (ExchangeStream)

Returned by `session.startExchange()` or received in `session.onExchangeStart(handler)`.

**Sending:**
- `exchange.startMessage(options?)` — returns `MessageEventHelper`
- `exchange.sendMessageWithContentPart({ data, role?, mimeType? })` — convenience: start message + content part + end in one call
- `exchange.sendExchangeEnd()` — end the exchange
- `exchange.sendMetaEvent(metaEvent)` — send metadata

**Receiving:**
- `exchange.onMessageStart(handler)` — new message in exchange
- `exchange.onMessageCompleted(handler)` — complete message after all content parts end
- `exchange.onExchangeEnd(handler)` — exchange ended

**State:**
- `exchange.messages` — iterator over messages
- `exchange.getMessage(messageId)` — get specific message
- `exchange.exchangeId` — the exchange ID
- `exchange.session` — parent session

### MessageEventHelper (MessageStream)

Returned by `exchange.startMessage()` or received in `exchange.onMessageStart(handler)`.

**Role checks:**
- `message.isUser` — boolean
- `message.isAssistant` — boolean
- `message.isSystem` — boolean
- `message.role` — `MessageRole` enum value

**Sending:**
- `message.startContentPart({ mimeType, ... })` — returns `ContentPartEventHelper`
- `message.sendContentPart({ data, mimeType? })` — convenience: start + chunk + end
- `message.startToolCall({ toolName, input?, ... })` — returns `ToolCallEventHelper`
- `message.sendMessageEnd()` — end the message
- `message.sendInterrupt(interruptId, startInterrupt)` — send interrupt
- `message.sendInterruptEnd(interruptId, endInterrupt)` — end interrupt

**Receiving:**
- `message.onContentPartStart(handler)` — new content part streaming
- `message.onContentPartCompleted(handler)` — complete content part with all data
- `message.onToolCallStart(handler)` — tool call started
- `message.onToolCallCompleted(handler)` — tool call finished with result
- `message.onInterruptStart(handler)` — interrupt (e.g., tool call confirmation)
- `message.onInterruptEnd(handler)` — interrupt resolved
- `message.onMessageEnd(handler)` — message ended
- `message.onCompleted(handler)` — complete message with all content parts and tool calls

**State:**
- `message.contentParts` — iterator over content parts
- `message.getContentPart(contentPartId)` — get specific content part
- `message.toolCalls` — iterator over tool calls
- `message.getToolCall(toolCallId)` — get specific tool call

### ContentPartEventHelper (ContentPartStream)

Received in `message.onContentPartStart(handler)`.

**Type checks:**
- `contentPart.isMarkdown` — `text/markdown`
- `contentPart.isText` — `text/plain`
- `contentPart.isHtml` — `text/html`
- `contentPart.isAudio` — `audio/*`
- `contentPart.isImage` — `image/*`
- `contentPart.isTranscript` — speech-to-text transcript
- `contentPart.mimeType` — raw MIME type string

**Sending:**
- `contentPart.sendChunk({ data, sequence? })` — send text chunk
- `contentPart.sendChunkWithCitation(...)` — chunk with citation
- `contentPart.sendContentPartEnd()` — end the content part

**Receiving:**
- `contentPart.onChunk(handler)` — streaming data chunk received
- `contentPart.onContentPartEnd(handler)` — content part ended
- `contentPart.onCompleted(handler)` — complete content part with all accumulated data, citations, and citation errors

### ToolCallEventHelper (ToolCallStream)

Received in `message.onToolCallStart(handler)`.

**Properties:**
- `toolCall.toolCallId` — string
- `toolCall.startEvent` — `{ toolName, input?, timestamp }`

**Sending:**
- `toolCall.sendToolCallEnd({ output?, isError?, cancelled? })` — end with result

**Receiving:**
- `toolCall.onToolCallEnd(handler)` — tool call ended with result

## Chat Interface Wiring — Mandatory Design Decisions

**IMPORTANT:** This pattern matches the working sample app in `samples/conversational-agent-app/`. The key design decisions:

1. **Add the assistant placeholder message IMMEDIATELY in `sendMessage()`** — before `startExchange()`. Do NOT wait for `onMessageStart`. This ensures the typing dots show up instantly.
2. **Pre-register exchangeId → assistantMessageId mapping** so `onExchangeStart` can wire up handlers for the right message.
3. **Use a single `isStreaming` state** — set `true` in `sendMessage()`, set `false` in `onExchangeEnd()` (not `onMessageEnd`).
4. **Show bouncing dots inside the assistant message bubble** when content is empty and `isStreaming` is true. Once chunks arrive, the dots are replaced by growing text.
5. **Use `echo: true`** on `startSession()` so all exchanges (including user-initiated) fire through `onExchangeStart`.

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

# Conversational Agent Reference

## Imports

```typescript
import { ConversationalAgent, Exchanges, Messages } from '@uipath/uipath-typescript/conversational-agent';
```

## Scopes

Combined scopes needed: `OR.Execution` `OR.Folders` `OR.Jobs` `ConversationalAgents` `Traces.Api`

- Agents (getAll, getById): `OR.Execution` or `OR.Execution.Read`
- Conversations (create): `OR.Execution`, `OR.Folders`, `OR.Jobs`
- Conversations (read): `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read`
- Conversations (update/delete): `OR.Execution`, `OR.Jobs`
- startSession: `OR.Execution`, `OR.Jobs`, `ConversationalAgents`
- Exchanges (read): `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read`
- Feedback: `OR.Execution`, `OR.Jobs`, `Traces.Api`

## Types to Import

```typescript
// Agent types
import type {
  RawAgentGetResponse,
  RawAgentGetByIdResponse,
  AgentGetResponse,
  AgentGetByIdResponse,
  AgentAppearance,
  AgentStartingPrompt,
} from '@uipath/uipath-typescript/conversational-agent';

// Conversation types
import type {
  RawConversationGetResponse,
  ConversationGetResponse,
  ConversationCreateResponse,
  ConversationUpdateResponse,
  ConversationDeleteResponse,
  ConversationCreateOptions,
  ConversationGetAllOptions,
  ConversationUpdateOptions,
  ConversationSessionOptions,
  ConversationAttachmentUploadResponse,
} from '@uipath/uipath-typescript/conversational-agent';

// Exchange types
import type {
  ExchangeGetResponse,
  ExchangeGetAllOptions,
  ExchangeGetByIdOptions,
  CreateFeedbackOptions,
  FeedbackCreateResponse,
} from '@uipath/uipath-typescript/conversational-agent';

// Message types
import type {
  MessageGetResponse,
  ContentPartGetResponse,
} from '@uipath/uipath-typescript/conversational-agent';

// Core conversation types
import type {
  Exchange,
  Message,
  ContentPart,
  ToolCall,
  Citation,
  Interrupt,
} from '@uipath/uipath-typescript/conversational-agent';

// Real-time session stream types
import type {
  SessionStream,
  ExchangeStream,
  MessageStream,
  ContentPartStream,
  ToolCallStream,
} from '@uipath/uipath-typescript/conversational-agent';

// Event helper types (for real-time sessions)
import {
  SessionEventHelper,
  ExchangeEventHelper,
  MessageEventHelper,
  ContentPartEventHelper,
  ToolCallEventHelper,
} from '@uipath/uipath-typescript/conversational-agent';
```

## Enums

```typescript
import {
  MessageRole,        // System, User, Assistant
  InterruptType,      // ToolCallConfirmation
  FeedbackRating,     // Positive, Negative
  SortOrder,          // Ascending, Descending
} from '@uipath/uipath-typescript/conversational-agent';

import { LogLevel } from '@uipath/uipath-typescript/conversational-agent';
```

## ConversationalAgent Service

The main entry point. Instantiate with the SDK instance.

```typescript
const conversationalAgent = new ConversationalAgent(sdk);
```

### getAll(folderId?: number)

Returns `Promise<AgentGetResponse[]>`. Each agent has: `id`, `name`, `description`, `processVersion`, `processKey`, `folderId`, `feedId`, `createdTime`. Each returned agent also has attached methods (see Agent-Attached Methods below).

### getById(id: number, folderId: number)

Returns `Promise<AgentGetByIdResponse>`. Same fields as `AgentGetResponse` plus `appearance?: AgentAppearance` with optional `welcomeTitle`, `welcomeDescription`, and `startingPrompts: AgentStartingPrompt[]` (each has `displayPrompt`, `actualPrompt`, `id`).

### onConnectionStatusChanged(handler)

Registers a handler called whenever the WebSocket connection status changes. Returns cleanup function.

### conversations (property)

Access to `ConversationService` for conversation CRUD and real-time sessions. See Conversation Service below.

## Agent-Attached Methods (AgentMethods)

Each agent returned by `getAll()` or `getById()` has these attached properties:

- `agent.conversations` — A scoped conversation service where `agentId` and `folderId` are pre-filled. Use `agent.conversations.create(options?)` instead of `conversationalAgent.conversations.create(agentId, folderId, options?)`.
- `agent.connectionStatus` — Current WebSocket `ConnectionStatus`
- `agent.isConnected` — `boolean`
- `agent.connectionError` — `Error | null`

## Conversation Service

Accessed via `conversationalAgent.conversations`.

### create(agentId: number, folderId: number, options?: ConversationCreateOptions)

Returns `Promise<ConversationCreateResponse>`. Options: `{ label?, autogenerateLabel?, traceId?, jobStartOverrides?: { runAsMe? } }`. The response is a `ConversationGetResponse` with attached methods.

**Via agent shorthand:** `agent.conversations.create(options?)` — agentId and folderId are auto-filled.

### getById(id: string)

Returns `Promise<ConversationGetResponse>` with attached methods.

### getAll(options?: ConversationGetAllOptions)

Returns `NonPaginatedResponse<ConversationGetResponse>` or `PaginatedResponse<ConversationGetResponse>`. Options extend `PaginationOptions` with `{ sort?: SortOrder }`. Token-based pagination.

### updateById(id: string, options: ConversationUpdateOptions)

Returns `Promise<ConversationUpdateResponse>`. Options: `{ label?, autogenerateLabel?, jobKey?, isLocalJobExecution? }`.

### deleteById(id: string)

Returns `Promise<ConversationDeleteResponse>`.

### uploadAttachment(id: string, file: File)

Returns `Promise<ConversationAttachmentUploadResponse>` with `{ uri, name, mimeType }`. Handles the two-step upload (create attachment entry, then upload to blob storage).

### startSession(conversationId: string, options?: ConversationSessionOptions)

Returns `SessionStream` for real-time WebSocket communication. Options: `{ echo?, logLevel? }`. See Real-Time Sessions below.

### getSession(conversationId: string)

Returns `SessionStream | undefined` — the active session for the conversation, or undefined if none.

### endSession(conversationId: string)

Ends the active session. No-op if no session exists.

### sessions (getter)

`Iterable<SessionStream>` — iterator over all active sessions.

### connectionStatus / isConnected / connectionError

WebSocket connection state properties.

### onConnectionStatusChanged(handler)

Registers handler for connection status changes. Returns cleanup function.

## ConversationGetResponse Fields

`id: string`, `createdTime: string`, `updatedTime: string`, `lastActivityTime: string`, `label: string`, `autogenerateLabel: boolean`, `userId: string`, `orgId: string`, `tenantId: string`, `folderId: number`, `agentId?: number`, `traceId: string`, `spanId?: string`, `jobStartOverrides?: ConversationJobStartOverrides`, `jobKey?: string`, `isLocalJobExecution?: boolean`. Plus all Conversation-Attached Methods.

## Conversation-Attached Methods (ConversationMethods)

Each conversation returned by `create()`, `getById()`, or `getAll()` has:

- `conversation.exchanges` — Scoped `ExchangeService` (conversationId pre-filled)
  - `conversation.exchanges.getAll(options?)` — list exchanges
  - `conversation.exchanges.getById(exchangeId, options?)` — get one exchange
  - `conversation.exchanges.createFeedback(exchangeId, options)` — submit feedback
- `conversation.update(options)` — update conversation (label, etc.)
- `conversation.delete()` — delete conversation
- `conversation.startSession(options?)` — start real-time session
- `conversation.getSession()` — get active session
- `conversation.endSession()` — end active session
- `conversation.uploadAttachment(file)` — upload file attachment

## Exchange Service

Standalone: `new Exchanges(sdk)`. Or scoped via `conversation.exchanges`.

### getAll(conversationId: string, options?: ExchangeGetAllOptions)

Returns `NonPaginatedResponse<ExchangeGetResponse>` or `PaginatedResponse<ExchangeGetResponse>`. Options extend `PaginationOptions` with `{ exchangeSort?: SortOrder, messageSort?: SortOrder }`.

### getById(conversationId: string, exchangeId: string, options?: ExchangeGetByIdOptions)

Returns `Promise<ExchangeGetResponse>`. Options: `{ messageSort?: SortOrder }`.

### createFeedback(conversationId: string, exchangeId: string, options: CreateFeedbackOptions)

Returns `Promise<FeedbackCreateResponse>`. Options: `{ rating: FeedbackRating, comment?: string }`.

## ExchangeGetResponse Fields

`id: string`, `exchangeId: string`, `createdTime: string`, `updatedTime: string`, `spanId?: string`, `feedbackRating?: FeedbackRating`, `messages: MessageGetResponse[]`.

## MessageGetResponse Fields

`id: string`, `messageId: string`, `role: MessageRole`, `contentParts?: ContentPartGetResponse[]`, `toolCalls: ToolCall[]`, `interrupts: Interrupt[]`, `createdTime: string`, `updatedTime: string`, `spanId?: string`.

## ContentPartGetResponse Fields

Extends `ContentPart` with helper methods:
- `isDataInline: boolean` — whether data is inline (string)
- `isDataExternal: boolean` — whether data is an external URL
- `getData(): Promise<string | Response>` — resolves inline data (string) or fetches external data (Response)

`ContentPart` fields: `id`, `contentPartId`, `mimeType`, `data` (inline string or external URL), `citations: Citation[]`, `isTranscript?: boolean`, `isIncomplete?: boolean`, `name?: string`, `createdTime`, `updatedTime`.

## Message Service

Standalone: `new Messages(sdk)`.

### getById(conversationId: string, exchangeId: string, messageId: string)

Returns `Promise<MessageGetResponse>`.

### getContentPartById(conversationId: string, exchangeId: string, messageId: string, contentPartId: string)

Returns `Promise<ContentPartGetResponse>`.

## Real-Time Sessions (WebSocket)

The core of conversational agent is the real-time WebSocket session. This enables streaming chat with agents.

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

## Usage Example — Chat Interface Component

**IMPORTANT:** This pattern matches the working sample app in `samples/conversational-agent-app/`. The key design decisions:

1. **Add the assistant placeholder message IMMEDIATELY in `sendMessage()`** — before `startExchange()`. Do NOT wait for `onMessageStart`. This ensures the typing dots show up instantly.
2. **Pre-register exchangeId → assistantMessageId mapping** so `onExchangeStart` can wire up handlers for the right message.
3. **Use a single `isStreaming` state** — set `true` in `sendMessage()`, set `false` in `onExchangeEnd()` (not `onMessageEnd`).
4. **Show bouncing dots inside the assistant message bubble** when content is empty and `isStreaming` is true. Once chunks arrive, the dots are replaced by growing text.
5. **Use `echo: true`** on `startSession()` so all exchanges (including user-initiated) fire through `onExchangeStart`.

```typescript
import { useMemo, useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { ConversationalAgent, MessageRole } from '@uipath/uipath-typescript/conversational-agent';
import type {
  AgentGetResponse,
  ConversationGetResponse,
  SessionStream,
} from '@uipath/uipath-typescript/conversational-agent';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

function ChatInterface() {
  const { sdk } = useAuth();
  const conversationalAgent = useMemo(() => new ConversationalAgent(sdk), [sdk]);
  const [agents, setAgents] = useState<AgentGetResponse[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentGetResponse | null>(null);
  const convRef = useRef<ConversationGetResponse | null>(null);
  const sessionRef = useRef<SessionStream | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Pre-registered mapping: exchangeId → assistant message ID
  // Registered in sendMessage() BEFORE startExchange() so onExchangeStart can look it up
  const exchangeAssistantIdRef = useRef<Map<string, string>>(new Map());

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load available agents
  useEffect(() => {
    const load = async () => {
      const result = await conversationalAgent.getAll();
      setAgents(result);
      if (result.length > 0) setSelectedAgent(result[0]);
    };
    load();
  }, [conversationalAgent]);

  // Create conversation and start session when agent is selected
  useEffect(() => {
    if (!selectedAgent) return;

    const setup = async () => {
      const conv = await selectedAgent.conversations.create({ label: 'Chat session' });
      convRef.current = conv;

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
                if (chunk.data) {
                  setMessages(prev =>
                    prev.map(m =>
                      m.id === assistantId ? { ...m, content: m.content + chunk.data } : m
                    )
                  );
                }
              });
            }
          });
        });

        exchange.onExchangeEnd(() => {
          exchangeAssistantIdRef.current.delete(exchange.exchangeId);
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId ? { ...m, isStreaming: false } : m
            )
          );
          setIsStreaming(false);
        });
      });
    };

    setup();

    return () => {
      convRef.current?.endSession();
      sessionRef.current = null;
    };
  }, [selectedAgent]);

  // Send a message
  const sendMessage = useCallback(async () => {
    if (!sessionRef.current || !input.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
    };

    // Add assistant placeholder IMMEDIATELY — shows typing dots right away
    const assistantId = `assistant-${Date.now()}`;
    const assistantPlaceholder: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMessage, assistantPlaceholder]);
    setInput('');
    setIsStreaming(true);

    // Pre-register the exchange → assistant mapping BEFORE starting the exchange
    const exchangeId = `exchange-${Date.now()}-${crypto.randomUUID().slice(0, 12)}`;
    exchangeAssistantIdRef.current.set(exchangeId, assistantId);

    // Start exchange with pre-determined ID and send user message
    const exchange = sessionRef.current.startExchange({ exchangeId });
    const message = exchange.startMessage({ role: MessageRole.User });
    await message.sendContentPart({ data: input });
    message.sendMessageEnd();
  }, [input, isStreaming]);

  return (
    <div className="flex flex-col h-full">
      {/* Agent selector */}
      <div className="p-4 border-b">
        <select
          value={selectedAgent?.id ?? ''}
          onChange={(e) => {
            const agent = agents.find(a => a.id === Number(e.target.value));
            if (agent) setSelectedAgent(agent);
          }}
          className="w-full p-2 border rounded"
        >
          {agents.map(agent => (
            <option key={agent.id} value={agent.id}>{agent.name}</option>
          ))}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] p-3 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'
            }`}>
              {/* Show typing dots INSIDE the bubble when streaming with no content yet */}
              {msg.isStreaming && !msg.content ? (
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type a message..."
          className="flex-1 p-2 border rounded"
          disabled={isStreaming}
        />
        <button
          onClick={sendMessage}
          disabled={isStreaming || !input.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

## Usage Example — Loading Conversation History

```typescript
import { ConversationalAgent, Exchanges, FeedbackRating, SortOrder } from '@uipath/uipath-typescript/conversational-agent';

// Load past conversations
const allConversations = await conversationalAgent.conversations.getAll({
  pageSize: 20,
  sort: SortOrder.Descending,
});

// Load exchanges for a conversation
const exchanges = await conversation.exchanges.getAll({
  pageSize: 50,
  exchangeSort: SortOrder.Ascending,
  messageSort: SortOrder.Ascending,
});

// Access message content
for (const exchange of exchanges.items) {
  for (const message of exchange.messages) {
    console.log(`[${message.role}]:`);
    if (message.contentParts) {
      for (const part of message.contentParts) {
        const data = await part.getData();
        console.log(data);
      }
    }
  }
}

// Submit feedback on an exchange
await conversation.exchanges.createFeedback(exchangeId, {
  rating: FeedbackRating.Positive,
  comment: 'Helpful response!',
});
```

## Usage Example — File Attachments

```typescript
// Upload a file to a conversation
const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
const file = fileInput.files![0];

const attachment = await conversation.uploadAttachment(file);
console.log(`Uploaded: ${attachment.name} (${attachment.mimeType}) -> ${attachment.uri}`);

// Reference the attachment URI in a message if needed
const exchange = session.startExchange();
await exchange.sendMessageWithContentPart({
  data: `Please analyze the uploaded file: ${attachment.uri}`,
});
```

## Usage Example — Tool Call Confirmation (Interrupts)

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

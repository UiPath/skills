# Chat Guide

Deep dive on the `uip cas chat` command -- WebSocket architecture, streaming behavior, multi-turn conversations, and known limits discovered through stress testing.

## Chat Modes

### Single-Message Mode (`-m`)

Send one message, receive the response, and exit. This is the correct mode for AI agents and programmatic use.

```bash
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> -m "Your question"
```

If no `--conversation-id` is provided, a new conversation is auto-created. The agent's response streams to stdout. The process exits after the response completes.

### Interactive Mode (no `-m`)

Opens a readline prompt for multi-turn human conversation over a single persistent WebSocket.

```bash
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --verbose
```

- Prompt: `You: ` (printed to stderr)
- Agent responses prefixed with `Agent: ` (on stderr), actual text on stdout
- Exit with `/quit` or `/exit`
- Ctrl+C triggers graceful cleanup (endSession + disconnect)

> **AI agents must never use interactive mode.** Interactive mode uses Node's `readline` on stdin, which requires a TTY. AI agent Bash tool calls pipe stdin or use `/dev/null`, causing unreliable buffering, stalled input, and unpredictable output. Always use `-m` flag for deterministic behavior.

## WebSocket Lifecycle

Each chat session follows this lifecycle:

```
1. Create conversation       (REST API, or auto-created by chat)
2. Connect WebSocket         (socket.io, wss:// transport)
3. Start session             (ConversationEvent: startSession)
4. Session acknowledged      (ConversationEvent: sessionStarted)
5. For each user message:
   a. Start exchange         (ConversationEvent: startExchange)
   b. Send user message      (ConversationEvent: message with user content)
   c. Receive agent message  (ConversationEvent: message chunks streamed)
   d. End exchange           (ConversationEvent: endExchange)
6. End session               (ConversationEvent: endSession)
7. Disconnect WebSocket
```

### Connection Details

- **Transport:** WebSocket only (no HTTP polling fallback)
- **URL:** `wss://<host>/autopilotforeveryone_/websocket_/socket.io`
- **Auth:** Token refreshed automatically on every connection/reconnection attempt
- **Reconnection:** Enabled with exponential backoff (200ms initial, 30s max, infinite retries)
- **Connection timeout:** 5 seconds

## Streaming Output

The chat command writes to two streams:

### stdout (response content)

The agent's actual response text. In single-message mode, capture this for the answer:

```bash
RESPONSE=$(uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> -m "What is 2+2?" 2>/dev/null)
echo "$RESPONSE"  # "2 + 2 equals 4."
```

### stderr (metadata, with `--verbose`)

Session lifecycle events, tool calls, label updates, and citations:

```
[Created conversation: <UUID>]
[Session started]
[Label updated: Topic Summary (auto)]
[Tool call: Web_Search]
[Tool call: Web_Search]

--- Citations ---
  [1] Source Title - https://example.com
  [2] Another Source - https://example.com/page (page 5)
```

Without `--verbose`, only errors appear on stderr.

## Multi-Turn Conversations

### Approach 1: Explicit Conversation (recommended for AI agents)

Create a conversation once, then reuse it across multiple `-m` calls:

```bash
# Create
CONV_ID=$(uip cas conversations create <AGENT_ID> --folder-id <FOLDER_ID> --output json | jq -r '.Data.Id')

# Turn 1
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --conversation-id "$CONV_ID" -m "My name is Alice"

# Turn 2 (agent remembers Turn 1)
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --conversation-id "$CONV_ID" -m "What is my name?"
# Response: "Your name is Alice."
```

Each `-m` call creates a fresh WebSocket session, but the conversation state persists server-side. Context is fully retained across turns.

### Approach 2: Auto-Created Conversation

When you omit `--conversation-id`, the chat command auto-creates a conversation. To continue it, extract the conversation ID from verbose output:

```bash
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> -m "Hello" --verbose 2>&1 | grep "Created conversation"
# [Created conversation: 7858dd3b-5600-4c56-a98f-f1a1dd7dae0c]
```

Then pass it on subsequent calls.

## Tool Calls and Interrupts

Agents may invoke tools (e.g., web search, API calls) during their response. With `--verbose`:

```
[Tool call: Web_Search]
[Tool call: GetWeather]
```

Some agents may also request approval for actions via **interrupts**. The CLI auto-approves all interrupts. With `--verbose`:

```
[Interrupt: ToolApproval]
  Tool: SendEmail
```

## Label Auto-Updates

As the conversation progresses, the server may auto-generate labels summarizing the topic:

```
[Label updated: Travel Planning and Itinerary (auto)]
```

These appear on stderr with `--verbose` and are informational only.

## Known Limits (from Stress Testing)

These limits were discovered through systematic WebSocket stress testing:

### What Works

| Scenario | Result |
|---|---|
| Single-message mode | Reliable, clean response |
| Multi-turn, same conversation, sequential | Full context retention across turns |
| Single WebSocket, 2-minute idle gaps | Connection survives via ping/pong keepalive |
| Single WebSocket, 10+ minutes | Stable, no disconnects |
| 5 concurrent different conversations | All succeed with correct responses |
| Conversation resume via `--conversation-id` | Context fully preserved |
| 33 KB message payload | Processed correctly |
| Tool calls during response | Rendered correctly with `--verbose` |
| Citations in response | Footnotes displayed on stderr |

### What Breaks

| Scenario | Symptom | Workaround |
|---|---|---|
| Message payload >90 KB | Slow processing; client has no timeout so it appears to hang | Wait longer, or upload large content as an attachment |
| Concurrent sessions on same conversation | Interleaved messages, `AGENT_INVALID_INPUT` error | One session per conversation |
| `--log-level` on chat command | Ignored (global flag conflict) | Use `--verbose` |
| Process exit after chat (SDK bug) | Process hangs due to socket.io reconnect loop | Being fixed; process eventually exits |

### Idle Connection Behavior

The WebSocket uses socket.io's ping/pong keepalive mechanism. Tested idle periods:

- **60 seconds:** Connection survives, agent responds immediately
- **120 seconds:** Connection survives, full context retention
- **Multiple 120-second gaps over 10 minutes:** All turns successful

The connection will eventually be closed by the server after extended inactivity (exact timeout depends on server configuration).

## Best Practices for AI Agent Use

1. **Always use `-m` flag** -- never interactive mode
2. **Redirect stderr** to capture clean response: `2>/dev/null`
3. **Create conversation explicitly** for multi-turn flows -- don't rely on auto-creation
4. **Be patient with large messages (>90 KB)** -- they process slower and the client has no timeout; use attachments for very large content
5. **One session at a time** per conversation -- no parallel sends
6. **Capture the conversation-id** early and reuse it
7. **Delete conversations** after completing the task

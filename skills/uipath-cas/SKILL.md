---
name: uipath-cas
description: "UiPath Conversational Agent Service (CAS) -- discover agents, chat via WebSocket, manage conversations, exchanges, messages, citations, attachments, and user settings through the uip cas CLI. TRIGGER when: user wants to chat with a UiPath agent, interact with conversational agents, list or discover available agents, manage conversations (create, resume, list, delete), review exchanges or messages, upload attachments to conversations, manage CAS user settings, or uses 'uip cas' commands. DO NOT TRIGGER when: user wants to create/build/code a Python agent (use uipath-coded-agents), deploy an agent to Orchestrator (use uipath-platform), or build RPA/flow automations."
metadata:
  allowed-tools: Bash, Read, Grep
---

# UiPath Conversational Agents (CAS)

Interact with UiPath Conversational Agents via the `uip cas` CLI -- discover agents, chat in real time, and manage conversations.

**Prerequisite:** The user must be authenticated. Check with `uip login status --output json`. If not logged in, run `uip login --output json`. Auth credentials are stored at `~/.uipath/.auth`.

## When to Use This Skill

- User wants to **discover** available conversational agents
- User wants to **chat** with an agent (single message or multi-turn)
- User wants to **manage conversations** (create, resume, list, update, delete)
- User wants to **review exchanges or messages** from past conversations
- User wants to **upload file attachments** to a conversation
- User wants to **submit feedback** on agent responses
- User wants to **manage CAS user settings** (name, role, department, timezone)
- User references `uip cas` commands

## Critical Rules

1. **Always authenticate first.** Run `uip login status --output json` before any CAS command. If not logged in, run `uip login --output json` then `uip login tenant set "<TENANT>" --output json`. Every CAS command requires a valid auth token.

2. **Always use `--output json` on non-chat commands.** All `uip cas agents`, `conversations`, `exchanges`, `messages`, and `user` commands support `--output json` for machine-readable output. The `chat` command does NOT support `--output json` -- it streams text directly to stdout.

3. **Always use single-message mode (`-m`) for programmatic use.** Interactive mode uses Node's `readline` on stdin, which expects a human typing at a terminal. AI agent Bash tool calls have no interactive TTY -- stdin is a pipe or `/dev/null`, causing unreliable buffering, stalled input, and unpredictable output flushing. The `-m` flag is deterministic: send one message, get the response on stdout, process exits. For multi-turn, chain multiple `-m` calls with `--conversation-id`. When an AI agent needs to send a message, always use:
   ```bash
   uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> -m "Your message" 2>/dev/null
   ```
   Capture stdout for the agent's response text. Never attempt to drive the interactive readline prompt.

4. **Always obtain both agent-id AND folder-id before chatting.** The `chat` command requires both values. Discover them with:
   ```bash
   uip cas agents list --output json
   ```
   This returns `Id` (agent-id) and `FolderId` (folder-id) for each agent.

5. **Save the conversation-id for multi-turn conversations.** The first `chat` call auto-creates a conversation. Capture the conversation ID from `--verbose` output or create one explicitly:
   ```bash
   uip cas conversations create <AGENT_ID> --folder-id <FOLDER_ID> --output json
   ```
   Then pass `--conversation-id <ID>` on subsequent calls to retain context across turns.

6. **Expect slower responses for large messages.** Messages over ~90 KB may take significantly longer to process, and the client currently lacks a timeout -- so it can appear to hang. If a large message seems stuck, wait longer before assuming failure. For very large content, consider uploading as a file attachment instead:
   ```bash
   uip cas conversations attachments upload <CONV_ID> --file <PATH> --output json
   ```

7. **Never open concurrent sessions on the same conversation.** Multiple simultaneous WebSocket sessions targeting the same conversation-id cause interleaved messages and unhandled errors. Use one session per conversation at a time.

8. **Do not use `--log-level` on the chat command.** This option conflicts with the global CLI `--log-level` flag and has no effect. Use `--verbose` instead to see tool calls, session events, and label updates on stderr.

9. **stdout = response text, stderr = metadata.** The `chat` command streams the agent's response to stdout. With `--verbose`, session lifecycle events, tool call names, label updates, and citations go to stderr. Parse stdout for the actual response content.

10. **Clean up conversations when done.** Delete conversations that are no longer needed:
    ```bash
    uip cas conversations delete <CONV_ID> --output json
    ```

## Quick Start

### Step 1 -- Authenticate

```bash
uip login status --output json
# If not logged in:
uip login --output json
uip login tenant set "<TENANT_NAME>" --output json
```

For non-default environments (e.g., alpha):
```bash
uip login --authority "https://alpha.uipath.com" --output json
```

### Step 2 -- Discover Agents

```bash
uip cas agents list --output json
```

Or filter by folder:
```bash
uip cas agents list --folder-id <FOLDER_ID> --output json
```

### Step 3 -- Get Agent Details (optional)

```bash
uip cas agents get <AGENT_ID> --folder-id <FOLDER_ID> --output json
```

Returns name, description, process key, version, and welcome title.

### Step 4 -- Send a Single Message

```bash
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> -m "Your question here"
```

The agent's response streams to stdout.

### Step 5 -- Multi-Turn Conversation

Create a conversation explicitly:
```bash
CONV_ID=$(uip cas conversations create <AGENT_ID> --folder-id <FOLDER_ID> --output json | jq -r '.Data.Id')
```

Send messages on the same conversation:
```bash
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --conversation-id "$CONV_ID" -m "First question"
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --conversation-id "$CONV_ID" -m "Follow-up question"
```

The agent retains full context across turns -- tested up to 10 minutes with 2-minute idle gaps between messages.

## Key Concepts

### Data Model Hierarchy

```
Agent                          (a deployed conversational agent release)
  |-- Conversation             (a persistent, stateful chat thread)
        |-- Exchange           (one user-question + agent-response pair)
              |-- Message      (individual message within an exchange)
                    |-- ContentPart    (text/markdown content blocks)
                    |     |-- Citation (source references with URLs)
                    |-- ToolCall       (agent tool invocations)
```

### Conversation vs Session

- A **Conversation** is persistent (has a UUID, CRUD-managed, stores message history).
- A **Session** is a live WebSocket connection to a conversation (ephemeral, created by `chat`, destroyed on disconnect). Multiple sessions can use the same conversation sequentially -- each picks up where the last left off.

## Common Patterns

### Inspect a Past Conversation

```bash
# List recent conversations
uip cas conversations list --sort descending --output json

# List exchanges in a conversation
uip cas exchanges list <CONV_ID> --output json

# Get an exchange with its messages
uip cas exchanges get <CONV_ID> <EXCHANGE_ID> --output json

# Get a message with citations
uip cas messages get <CONV_ID> <EXCHANGE_ID> <MSG_ID> --citations --output json
```

### Upload a File Then Ask About It

```bash
# Create conversation
CONV_ID=$(uip cas conversations create <AGENT_ID> --folder-id <FOLDER_ID> --output json | jq -r '.Data.Id')

# Upload file
uip cas conversations attachments upload "$CONV_ID" --file ./report.pdf --output json

# Ask about the uploaded file
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --conversation-id "$CONV_ID" -m "Summarize the uploaded report"
```

### Give Feedback on a Response

```bash
# List exchanges to find the one to rate
uip cas exchanges list <CONV_ID> --output json

# Submit positive/negative feedback
uip cas exchanges feedback <CONV_ID> <EXCHANGE_ID> --rating positive --comment "Helpful answer" --output json
```

### Update User Context

Set user profile so agents have context about who they're talking to:
```bash
uip cas user update-settings --name "Jane Doe" --role "Developer" --department "Engineering" --output json
```

## Anti-Patterns

- **Never use interactive chat mode from an AI agent.** Always use `-m` flag. Interactive mode uses stdin readline designed for human terminals.
- **Never send multiple concurrent messages to the same conversation.** This causes interleaved responses and unhandled errors.
- **Don't assume a large message failed just because it's slow.** Messages over ~90 KB take longer and the client has no timeout. Wait before retrying, or upload large content as an attachment.
- **Never rely on `--log-level` for the chat command.** It is broken due to a naming conflict. Use `--verbose`.
- **Never skip the authentication check.** CAS commands fail with cryptic errors when not authenticated.
- **Never parse stderr for response content.** stdout has the response, stderr has metadata/debug output.

## Troubleshooting

| Error / Symptom | Cause | Solution |
|---|---|---|
| `Not logged in` or `Client Authorization Failed` | Missing or expired auth token | Run `uip login --output json` |
| Chat hangs after agent responds | Known SDK issue: socket.io reconnect loop | Process will eventually be killed; known issue being fixed |
| Chat hangs with no response for a long time | Large message payload (>90 KB) takes longer to process; client has no timeout | Wait longer, or upload large content as an attachment instead |
| Garbled / interleaved responses | Concurrent sessions on same conversation | Use one session per conversation at a time |
| `Error creating conversation` | Wrong agent-id or folder-id | Verify with `uip cas agents list --output json` |
| `--log-level Debug` has no effect on chat | Global CLI flag conflict | Use `--verbose` instead |
| `AGENT_INVALID_INPUT: No user message found` | Concurrent session race condition | Don't run parallel chats on the same conversation |

## Task Navigation

| I need to... | Read these |
|---|---|
| Discover available agents | Quick Start Steps 2-3 |
| Send a single message to an agent | Quick Start Step 4 |
| Have a multi-turn conversation | Quick Start Step 5 |
| Understand the chat WebSocket model | [references/chat-guide.md](references/chat-guide.md) |
| Manage conversations (CRUD) | [references/conversations-lifecycle-guide.md](references/conversations-lifecycle-guide.md) |
| Work with exchanges and messages | [references/conversations-lifecycle-guide.md](references/conversations-lifecycle-guide.md) |
| Upload attachments | [references/conversations-lifecycle-guide.md](references/conversations-lifecycle-guide.md) |
| Submit feedback | [references/conversations-lifecycle-guide.md](references/conversations-lifecycle-guide.md) |
| Manage user settings | [references/conversations-lifecycle-guide.md](references/conversations-lifecycle-guide.md) |
| Full CLI command reference | [references/cas-commands-reference.md](references/cas-commands-reference.md) |

## References

- **[CAS CLI Command Reference](references/cas-commands-reference.md)** -- Every `uip cas` command with parameters and examples
- **[Chat Guide](references/chat-guide.md)** -- WebSocket chat deep dive: modes, streaming, multi-turn, known limits
- **[Conversations Lifecycle Guide](references/conversations-lifecycle-guide.md)** -- Conversations, exchanges, messages, attachments, user settings

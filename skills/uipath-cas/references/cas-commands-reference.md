# CAS CLI Command Reference

Complete reference for all `uip cas` commands. Always use `--output json` for programmatic parsing (except `chat`, which streams text to stdout).

## Global Options

Every `uip` command accepts:

| Option | Description | Default |
|---|---|---|
| `--output <format>` | Output format: `table`, `json`, `yaml`, `plain` | `table` (interactive), `json` (non-interactive) |
| `--output-filter <expr>` | JMESPath expression to filter output | -- |
| `--log-level <level>` | Log level: `debug`, `info`, `warn`, `error` | `info` |
| `--log-file <path>` | Write logs to file instead of stderr | -- |

---

## Agents

### `uip cas agents list`

List all available conversational agents.

```bash
uip cas agents list [--folder-id <ID>] --output json
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--folder-id <id>` | string | No | Filter agents by folder ID |

**Response fields:** `Id`, `Name`, `Description`, `FolderId`, `ProcessKey`

### `uip cas agents get`

Get detailed information about a specific agent.

```bash
uip cas agents get <AGENT_ID> --folder-id <FOLDER_ID> --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<agent-id>` | number | Yes | Agent release ID (positional argument) |
| `--folder-id <id>` | string | Yes | Folder ID containing the agent |

**Response fields:** `Id`, `Name`, `Description`, `FolderId`, `ProcessKey`, `ProcessVersion`, `WelcomeTitle`

---

## Conversations

### `uip cas conversations create`

Create a new conversation with an agent.

```bash
uip cas conversations create <AGENT_ID> --folder-id <FOLDER_ID> [options] --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<agent-id>` | number | Yes | Agent release ID (positional argument) |
| `--folder-id <id>` | string | Yes | Folder ID containing the agent |
| `--label <label>` | string | No | Conversation label |
| `--autogenerate-label` | flag | No | Auto-generate a label from first message |
| `--trace-id <id>` | string | No | Trace ID for the conversation |
| `--run-as-me` | flag | No | Run the agent job as the current user |

**Response fields:** `Id`, `Label`, `CreatedTime`, `AgentId`

### `uip cas conversations list`

List all conversations.

```bash
uip cas conversations list [options] --output json
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--page-size <n>` | number | No | Number of conversations per page |
| `--sort <order>` | string | No | `ascending` or `descending` |
| `--cursor <token>` | string | No | Pagination cursor from previous response |

**Response fields:** `Id`, `Label`, `CreatedTime`, `LastActivityTime`, `NextCursor`

### `uip cas conversations get`

Get details for a specific conversation.

```bash
uip cas conversations get <CONVERSATION_ID> --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |

**Response fields:** `Id`, `Label`, `CreatedTime`, `UpdatedTime`, `LastActivityTime`, `AgentId`, `FolderId`

### `uip cas conversations update`

Update a conversation's properties.

```bash
uip cas conversations update <CONVERSATION_ID> [options] --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |
| `--label <label>` | string | No | New label |
| `--autogenerate-label` | flag | No | Auto-generate a label |
| `--job-key <key>` | string | No | Job key to associate |
| `--local-job-execution` | flag | No | Enable local job execution |

At least one option must be provided.

**Response fields:** `Id`, `Label`, `UpdatedTime`

### `uip cas conversations delete`

Delete a conversation.

```bash
uip cas conversations delete <CONVERSATION_ID> --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |

**Response fields:** `Id`, `Status` ("Deleted")

---

## Conversation Attachments

### `uip cas conversations attachments upload`

Upload a file attachment to a conversation.

```bash
uip cas conversations attachments upload <CONVERSATION_ID> --file <PATH> --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |
| `--file <path>` | string | Yes | Path to the file to upload |

**Response fields:** `ConversationId`, `FileName`, `MimeType`, `UploadUri`

### `uip cas conversations attachments get-uri`

Get a pre-signed upload URI for an attachment.

```bash
uip cas conversations attachments get-uri <CONVERSATION_ID> --file-name <NAME> --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |
| `--file-name <name>` | string | Yes | Name of the file |

**Response fields:** `ConversationId`, `FileName`, `UploadUri`, `UploadUrl`, `HttpVerb`, `RequiresAuth`

---

## Exchanges

### `uip cas exchanges list`

List exchanges (conversation turns) for a conversation.

```bash
uip cas exchanges list <CONVERSATION_ID> [options] --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |
| `--page-size <n>` | number | No | Number of exchanges per page |
| `--sort <order>` | string | No | `ascending` or `descending` |
| `--message-sort <order>` | string | No | Sort messages within exchanges |
| `--cursor <token>` | string | No | Pagination cursor |

**Response fields:** `Id`, `CreatedTime`, `UpdatedTime`, `MessageCount`, `FeedbackRating`, `NextCursor`

### `uip cas exchanges get`

Get exchange details with all messages.

```bash
uip cas exchanges get <CONVERSATION_ID> <EXCHANGE_ID> [options] --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |
| `<exchange-id>` | UUID | Yes | Exchange ID (positional argument) |
| `--message-sort <order>` | string | No | Sort messages: `ascending` or `descending` |

**Response fields:** Array of messages with `ExchangeId`, `MessageId`, `Role`, `ContentPartCount`, `ToolCallCount`, `FeedbackRating`

### `uip cas exchanges feedback`

Submit feedback (rating) for an exchange.

```bash
uip cas exchanges feedback <CONVERSATION_ID> <EXCHANGE_ID> --rating <RATING> [options] --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID (positional argument) |
| `<exchange-id>` | UUID | Yes | Exchange ID (positional argument) |
| `--rating <rating>` | string | Yes | `positive` or `negative` |
| `--comment <text>` | string | No | Optional feedback comment |

**Response fields:** `ConversationId`, `ExchangeId`, `Rating`, `Comment`, `Status`

---

## Messages

### `uip cas messages get`

Get a specific message with content parts.

```bash
uip cas messages get <CONVERSATION_ID> <EXCHANGE_ID> <MESSAGE_ID> [options] --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID |
| `<exchange-id>` | UUID | Yes | Exchange ID |
| `<message-id>` | UUID | Yes | Message ID |
| `--citations` | flag | No | Include detailed citation data |

**Without `--citations`:** `MessageId`, `Role`, `CreatedTime`, `UpdatedTime`, `ContentParts` (MIME types), `ToolCalls`, `CitationCount`

**With `--citations`:** Detailed citation data including `ContentPartId`, `MimeType`, `CitationId`, `Offset`, `Length`, source info

### `uip cas messages get-content-part`

Get the data for a specific content part.

```bash
uip cas messages get-content-part <CONVERSATION_ID> <EXCHANGE_ID> <MESSAGE_ID> <CONTENT_PART_ID> --output json
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<conversation-id>` | UUID | Yes | Conversation ID |
| `<exchange-id>` | UUID | Yes | Exchange ID |
| `<message-id>` | UUID | Yes | Message ID |
| `<content-part-id>` | UUID | Yes | Content part ID |

**Response fields:** `ContentPartId`, `IsInline`, `IsExternal`, `Data`

---

## User Settings

### `uip cas user get-settings`

Get the current user's profile and context settings.

```bash
uip cas user get-settings --output json
```

**Response fields:** `UserId`, `Name`, `Email`, `Role`, `Department`, `Company`, `Country`, `Timezone`

### `uip cas user update-settings`

Update user profile and context settings.

```bash
uip cas user update-settings [options] --output json
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--name <name>` | string | No | User name |
| `--email <email>` | string | No | Email address |
| `--role <role>` | string | No | User role |
| `--department <dept>` | string | No | Department |
| `--company <company>` | string | No | Company |
| `--country <country>` | string | No | Country |
| `--timezone <tz>` | string | No | Timezone |

At least one option must be provided.

**Response fields:** Same as `get-settings`

---

## Chat

### `uip cas chat`

Start a real-time WebSocket chat session with a conversational agent.

```bash
# Single-message mode (for AI agents / programmatic use)
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> -m "Your message"

# Resume a conversation
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --conversation-id <CONV_ID> -m "Follow-up"

# Interactive mode (human terminal use only)
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --verbose
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<agent-id>` | number | Yes | Agent release ID (positional argument) |
| `--folder-id <id>` | string | Yes | Folder ID containing the agent |
| `--conversation-id <id>` | UUID | No | Resume an existing conversation |
| `-m, --message <text>` | string | No | Single message (non-interactive mode) |
| `--verbose` | flag | No | Show tool calls and session events on stderr |
| `--log-level <level>` | string | No | **Broken** -- conflicts with global flag. Use `--verbose` |

**Output behavior:**
- **stdout:** Agent response text (streamed in real time)
- **stderr (with `--verbose`):** Session lifecycle, tool call names, label updates, citations

**Interactive mode commands:** `/quit` or `/exit` to end the session.

> **For AI agents:** Always use `-m` mode. Never attempt to drive the interactive readline prompt.

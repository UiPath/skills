# Conversations Lifecycle Guide

Managing conversations, exchanges, messages, attachments, and user settings through the `uip cas` CLI.

## Conversations

### Create a Conversation

```bash
uip cas conversations create <AGENT_ID> --folder-id <FOLDER_ID> --output json
```

Optional flags:
- `--label "My Chat"` -- set a human-readable label
- `--autogenerate-label` -- server auto-generates a label from the first message
- `--trace-id <ID>` -- associate a trace ID for observability
- `--run-as-me` -- run the agent job as the current authenticated user

**Example:**
```bash
uip cas conversations create 79090 --folder-id 666955 --label "Support Chat" --output json
```

**Response:**
```json
{
  "Result": "Success",
  "Code": "ConversationCreated",
  "Data": {
    "Id": "db4f5183-1fb3-4353-9517-54fa43a16553",
    "Label": "Support Chat",
    "CreatedTime": "2025-03-31T02:04:19.080Z",
    "AgentId": 79090
  }
}
```

### List Conversations

```bash
uip cas conversations list --output json
```

Supports pagination:
```bash
# First page
uip cas conversations list --page-size 10 --sort descending --output json

# Next page (use NextCursor from previous response)
uip cas conversations list --page-size 10 --cursor "<CURSOR_TOKEN>" --output json
```

### Get Conversation Details

```bash
uip cas conversations get <CONVERSATION_ID> --output json
```

Returns full details including `AgentId`, `FolderId`, `Label`, timestamps.

### Update a Conversation

```bash
uip cas conversations update <CONVERSATION_ID> --label "New Label" --output json
```

At least one option is required. Available options:
- `--label <label>` -- change the label
- `--autogenerate-label` -- auto-generate from content
- `--job-key <key>` -- associate a job key
- `--local-job-execution` -- enable local job execution

### Delete a Conversation

```bash
uip cas conversations delete <CONVERSATION_ID> --output json
```

Permanently removes the conversation and all its exchanges/messages.

---

## Attachments

### Upload a File

Upload a file to a conversation so the agent can reference it:

```bash
uip cas conversations attachments upload <CONVERSATION_ID> --file ./document.pdf --output json
```

The CLI validates the file exists before uploading.

**Response:**
```json
{
  "Result": "Success",
  "Code": "AttachmentUploaded",
  "Data": {
    "ConversationId": "db4f5183-...",
    "FileName": "document.pdf",
    "MimeType": "application/pdf",
    "UploadUri": "https://..."
  }
}
```

### Get Pre-Signed Upload URI

For custom upload workflows, generate a pre-signed URI:

```bash
uip cas conversations attachments get-uri <CONVERSATION_ID> --file-name "data.csv" --output json
```

Returns the upload URL, HTTP verb, and whether authentication is required.

### Attachment Workflow

```bash
# 1. Create conversation
CONV_ID=$(uip cas conversations create <AGENT_ID> --folder-id <FOLDER_ID> --output json | jq -r '.Data.Id')

# 2. Upload file
uip cas conversations attachments upload "$CONV_ID" --file ./report.pdf --output json

# 3. Ask the agent about the file
uip cas chat <AGENT_ID> --folder-id <FOLDER_ID> --conversation-id "$CONV_ID" -m "Summarize the uploaded report"
```

---

## Exchanges

An exchange represents one user-question + agent-response pair within a conversation.

### List Exchanges

```bash
uip cas exchanges list <CONVERSATION_ID> --output json
```

Supports pagination and sorting:
```bash
uip cas exchanges list <CONVERSATION_ID> --page-size 5 --sort descending --output json
```

Also supports message sorting within each exchange:
```bash
uip cas exchanges list <CONVERSATION_ID> --message-sort ascending --output json
```

### Get Exchange with Messages

```bash
uip cas exchanges get <CONVERSATION_ID> <EXCHANGE_ID> --output json
```

Returns an array of messages within the exchange, each with:
- `ExchangeId`, `MessageId`, `Role` (user/assistant)
- `ContentPartCount`, `ToolCallCount`, `FeedbackRating`

### Submit Feedback

Rate an agent response as positive or negative:

```bash
uip cas exchanges feedback <CONVERSATION_ID> <EXCHANGE_ID> --rating positive --output json

# With an optional comment:
uip cas exchanges feedback <CONVERSATION_ID> <EXCHANGE_ID> --rating negative --comment "Answer was inaccurate" --output json
```

The `--rating` must be `positive` or `negative`.

---

## Messages

Messages are the individual user or assistant messages within an exchange.

### Get a Message

```bash
uip cas messages get <CONVERSATION_ID> <EXCHANGE_ID> <MESSAGE_ID> --output json
```

Returns message metadata including role, timestamps, content parts (MIME types), tool calls, and citation count.

### Get a Message with Citations

```bash
uip cas messages get <CONVERSATION_ID> <EXCHANGE_ID> <MESSAGE_ID> --citations --output json
```

Returns detailed citation data for each content part:
- `ContentPartId`, `MimeType`
- `CitationId`, `Offset`, `Length`
- Source information (title, URL, page number)

### Get Content Part Data

Retrieve the actual data for a specific content part:

```bash
uip cas messages get-content-part <CONVERSATION_ID> <EXCHANGE_ID> <MESSAGE_ID> <CONTENT_PART_ID> --output json
```

Returns:
- `ContentPartId`, `IsInline`, `IsExternal`
- `Data` (the actual content if inline)

---

## User Settings

User settings provide context to agents about who they're talking to. Agents may use this information to personalize responses.

### Get Current Settings

```bash
uip cas user get-settings --output json
```

Returns: `UserId`, `Name`, `Email`, `Role`, `Department`, `Company`, `Country`, `Timezone`

### Update Settings

```bash
uip cas user update-settings --name "Jane Doe" --role "Developer" --department "Engineering" --timezone "America/New_York" --output json
```

Available fields: `--name`, `--email`, `--role`, `--department`, `--company`, `--country`, `--timezone`

At least one field must be provided.

---

## Common Inspection Workflow

To understand what happened in a past conversation:

```bash
# 1. List conversations to find the one you want
uip cas conversations list --sort descending --page-size 5 --output json

# 2. List exchanges in that conversation
uip cas exchanges list <CONVERSATION_ID> --sort ascending --output json

# 3. Get a specific exchange with its messages
uip cas exchanges get <CONVERSATION_ID> <EXCHANGE_ID> --output json

# 4. Get message details with citations
uip cas messages get <CONVERSATION_ID> <EXCHANGE_ID> <MESSAGE_ID> --citations --output json

# 5. Get the actual content of a content part
uip cas messages get-content-part <CONVERSATION_ID> <EXCHANGE_ID> <MESSAGE_ID> <CONTENT_PART_ID> --output json
```

## Pagination Pattern

List commands that return paginated results include a `NextCursor` field:

```bash
# First page
RESULT=$(uip cas conversations list --page-size 10 --output json)
CURSOR=$(echo "$RESULT" | jq -r '.Data.NextCursor // empty')

# Next page (if cursor is non-empty)
if [ -n "$CURSOR" ]; then
  uip cas conversations list --page-size 10 --cursor "$CURSOR" --output json
fi
```

The same pattern applies to `exchanges list`.

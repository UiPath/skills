# UiPath SDK Services Reference

Complete reference for all platform services available through the UiPath Python SDK.

## SDK Initialization

```python
from uipath import UiPath

# Initialize with environment variables (recommended)
sdk = UiPath()

# With explicit token
sdk = UiPath(base_url="https://cloud.uipath.com/...", secret="your_token")

# With client credentials
sdk = UiPath(
    client_id="your_client_id",
    client_secret="your_client_secret",
    scope="your_scope",
    base_url="https://cloud.uipath.com/..."
)
```

## Available Services

| Service | Property | Purpose |
|---------|----------|---------|
| Processes | `sdk.processes` | Start process executions |
| Jobs | `sdk.jobs` | Manage job lifecycle, attachments, output |
| Assets | `sdk.assets` | Retrieve and update assets and credentials |
| Attachments | `sdk.attachments` | Upload, download, delete attachments |
| Buckets | `sdk.buckets` | Cloud storage file operations |
| Queues | `sdk.queues` | Queue item and transaction management |
| Actions | `sdk.actions` | Create and retrieve human-in-the-loop actions |
| Context Grounding | `sdk.context_grounding` | RAG index management and search |
| Documents | `sdk.documents` | Document extraction and validation |
| Entities | `sdk.entities` | Data Service entity and record management |
| Connections | `sdk.connections` | Integration Service connections |
| LLM | `sdk.llm` | Chat completions via normalized LLM Gateway |
| LLM OpenAI | `sdk.llm_openai` | OpenAI-compatible chat and embeddings |
| Guardrails | `sdk.guardrails` | Evaluate guardrails on data |
| Folders | `sdk.folders` | Folder key resolution |
| Tasks | `sdk.tasks` | Action Center task management |
| AgentHub | `sdk.agenthub` | LLM model listing and system agent invocation |
| MCP | `sdk.mcp` | List and retrieve MCP servers |
| Resource Catalog | `sdk.resource_catalog` | Search and list tenant/folder resources |

All services support both **synchronous** and **asynchronous** methods (async methods have an `_async` suffix).

---

## Processes

Start process executions in UiPath Orchestrator.

```python
# Start a process by name
job = sdk.processes.invoke(
    name="MyProcess",
    input_arguments={"param1": "value1"},
    folder_path="MyFolder"            # optional
)

# Async variant
job = await sdk.processes.invoke_async(
    name="MyProcess",
    input_arguments={"param1": "value1"}
)
```

---

## Jobs

Manage job lifecycle, attachments, and output extraction.

```python
# Retrieve a job by key
job = sdk.jobs.retrieve(job_key="abc-123", folder_path="MyFolder")

# Extract output data (downloads from attachment if needed)
output = sdk.jobs.extract_output(job)

# Resume a paused job
sdk.jobs.resume(job_id="abc-123", payload={"approved": True})

# Create and link an attachment to a job
attachment_key = sdk.jobs.create_attachment(
    name="report.pdf",
    source_path="/path/to/report.pdf",
    job_key="abc-123"
)

# List attachments for a job
attachments = sdk.jobs.list_attachments(job_key=uuid.UUID("abc-123"))

# Retrieve API trigger payload
payload = sdk.jobs.retrieve_api_payload(inbox_id="inbox-123")
```

---

## Assets

Retrieve and update Orchestrator assets and credentials.

```python
# Retrieve an asset by name
asset = sdk.assets.retrieve(name="MyAsset", folder_path="MyFolder")
print(asset.value)

# Retrieve a credential
credential = sdk.assets.retrieve_credential(name="MyCredential")

# Update an asset value
sdk.assets.update(robot_asset=asset, folder_path="MyFolder")
```

---

## Attachments

Upload, download, and delete file attachments.

```python
import uuid

# Upload from file path
key = sdk.attachments.upload(
    name="data.csv",
    source_path="/path/to/data.csv"
)

# Upload from content
key = sdk.attachments.upload(
    name="notes.txt",
    content="Hello, world!"
)

# Download an attachment
path = sdk.attachments.download(
    key=uuid.UUID("abc-123"),
    destination_path="/path/to/download/"
)

# Delete an attachment
sdk.attachments.delete(key=uuid.UUID("abc-123"))
```

---

## Buckets

Cloud storage operations for files in UiPath buckets.

```python
# Retrieve bucket info
bucket = sdk.buckets.retrieve(name="MyBucket")

# Upload a file to a bucket
sdk.buckets.upload(
    name="MyBucket",
    blob_file_path="reports/output.csv",
    source_path="/local/path/output.csv"
)

# Upload content directly
sdk.buckets.upload(
    name="MyBucket",
    blob_file_path="data/result.json",
    content='{"status": "done"}',
    content_type="application/json"
)

# Download from a bucket
sdk.buckets.download(
    name="MyBucket",
    blob_file_path="reports/output.csv",
    destination_path="/local/download/"
)
```

---

## Queues

Manage queue items and transactions in Orchestrator.

```python
# Create a single queue item
sdk.queues.create_item(item={
    "Name": "MyQueue",
    "SpecificContent": {"order_id": "12345", "amount": 99.99}
})

# Create multiple items in bulk
sdk.queues.create_items(
    queue_name="MyQueue",
    items=[
        {"SpecificContent": {"order_id": "001"}},
        {"SpecificContent": {"order_id": "002"}}
    ],
    commit_type="AllOrNothing"
)

# Create a transaction item
sdk.queues.create_transaction_item(item={
    "Name": "MyQueue",
    "SpecificContent": {"task": "process_order"}
})

# Complete a transaction
sdk.queues.complete_transaction_item(
    transaction_key="txn-123",
    result={"IsSuccessful": True, "Output": {"status": "done"}}
)

# Update transaction progress
sdk.queues.update_progress_of_transaction_item(
    transaction_key="txn-123",
    progress="Processing step 3 of 5"
)

# List queue items
items = sdk.queues.list_items()
```

---

## Actions

Create and retrieve human-in-the-loop actions (Action Center).

```python
# Create an action for human review
action = sdk.actions.create(
    title="Review Invoice #1234",
    data={"invoice_id": "1234", "amount": 5000},
    app_name="InvoiceReview",
    assignee="user@example.com"
)

# Retrieve an action by key
action = sdk.actions.retrieve(action_key="action-key-123")
```

---

## Context Grounding

RAG (Retrieval-Augmented Generation) index management and semantic search.

```python
# Retrieve an existing index
index = sdk.context_grounding.retrieve(name="KnowledgeBase")

# Search within an index
results = sdk.context_grounding.search(
    name="KnowledgeBase",
    query="How do I reset my password?",
    number_of_results=5
)
for result in results:
    print(result.content, result.score)

# Create a new index
index = sdk.context_grounding.create_index(
    name="MyIndex",
    source={"type": "bucket", "bucketName": "docs-bucket"},
    description="Company documentation index"
)

# Add content to an index
sdk.context_grounding.add_to_index(
    name="MyIndex",
    blob_file_path="docs/guide.pdf",
    source_path="/local/guide.pdf"
)

# Trigger data ingestion
sdk.context_grounding.ingest_data(index=index)

# Delete an index
sdk.context_grounding.delete_index(index=index)
```

---

## Documents

Document Understanding - extract data and validate with human review.

```python
# Extract data from a document
extraction = sdk.documents.extract(
    project_name="InvoiceExtraction",
    tag="invoice",
    file_path="/path/to/invoice.pdf"
)

# Or extract from bytes/file object
extraction = sdk.documents.extract(
    project_name="InvoiceExtraction",
    tag="invoice",
    file=open("invoice.pdf", "rb")
)

# Create a validation action for human review
validation = sdk.documents.create_validation_action(
    action_title="Validate Invoice #1234",
    action_priority="Normal",
    action_catalog="InvoiceValidation",
    action_folder="Invoices",
    storage_bucket_name="doc-storage",
    storage_bucket_directory_path="validations/",
    extraction_response=extraction
)

# Get the validated result
result = sdk.documents.get_validation_result(validation_action=validation)
```

---

## Entities

Data Service entity and record management.

```python
# List all entities
entities = sdk.entities.list_entities()

# Retrieve an entity by key
entity = sdk.entities.retrieve(entity_key="Customers")

# List records with pagination
records = sdk.entities.list_records(
    entity_key="Customers",
    start=0,
    limit=50
)

# Insert records
response = sdk.entities.insert_records(
    entity_key="Customers",
    records=[
        {"Name": "Acme Corp", "Email": "info@acme.com"},
        {"Name": "Globex", "Email": "info@globex.com"}
    ]
)

# Update records
response = sdk.entities.update_records(
    entity_key="Customers",
    records=[{"Id": "rec-123", "Email": "new@acme.com"}]
)

# Delete records
response = sdk.entities.delete_records(
    entity_key="Customers",
    record_ids=["rec-123", "rec-456"]
)
```

---

## Connections

Integration Service connection management and token retrieval.

```python
# List connections
connections = sdk.connections.list(name="Salesforce")

# Retrieve connection details
connection = sdk.connections.retrieve(key="conn-key-123")

# Get an authentication token for a connection
token = sdk.connections.retrieve_token(
    key="conn-key-123",
    token_type="direct"
)

# Get API metadata for a connection
metadata = sdk.connections.metadata(
    element_instance_id=123,
    tool_path="/contacts"
)

# Retrieve event payload
payload = sdk.connections.retrieve_event_payload(event_args=event_args)
```

---

## LLM

Chat completions via UiPath's normalized LLM Gateway API.

```python
# Basic chat completion
response = sdk.llm.chat_completions(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Summarize this document."}
    ],
    model="gpt-4o-mini-2024-07-18",
    max_tokens=4096,
    temperature=0
)

# With structured output (Pydantic model)
from pydantic import BaseModel

class Summary(BaseModel):
    title: str
    key_points: list[str]

response = sdk.llm.chat_completions(
    messages=[{"role": "user", "content": "Summarize..."}],
    model="gpt-4o-mini-2024-07-18",
    response_format=Summary
)

# With tool definitions
response = sdk.llm.chat_completions(
    messages=[{"role": "user", "content": "What's the weather?"}],
    model="gpt-4o-mini-2024-07-18",
    tools=[tool_definition],
    tool_choice="auto"
)
```

---

## LLM OpenAI

OpenAI-compatible chat completions and embeddings.

```python
# Chat completion (OpenAI-compatible)
response = sdk.llm_openai.chat_completions(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="gpt-4o-mini-2024-07-18",
    max_tokens=4096,
    temperature=0
)

# Generate embeddings
embeddings = sdk.llm_openai.embeddings(
    input="The quick brown fox jumps over the lazy dog",
    embedding_model="text-embedding-ada-002"
)
```

---

## Guardrails

Evaluate guardrails on input data to enforce safety and compliance policies.

```python
# Evaluate a guardrail on a prompt
result = sdk.guardrails.evaluate(
    guardrail_name="ContentSafety",
    data={"prompt": "User message to validate"},
    folder_path="MyFolder"
)

# Async variant
result = await sdk.guardrails.evaluate_async(
    guardrail_name="ContentSafety",
    data={"prompt": "User message to validate"}
)
```

---

## Tasks

Action Center task management for human-in-the-loop workflows.

```python
# Create a task
task = sdk.tasks.create(
    title="Review document",
    data={"document_id": "doc-123"},
    app_name="DocumentReview",
    assignee="reviewer@company.com"
)

# Retrieve a task
task = sdk.tasks.retrieve(task_key="task-key-123")
```

---

## AgentHub

List available LLM models and invoke system agents.

```python
# List available LLM models
models = sdk.agenthub.list_models()

# Invoke a system agent
result = sdk.agenthub.invoke(
    agent_name="system-agent",
    input_data={"query": "Help me with this task"}
)
```

---

## MCP

List and retrieve Model Context Protocol (MCP) servers.

```python
# List available MCP servers
servers = sdk.mcp.list()

# Retrieve a specific MCP server
server = sdk.mcp.retrieve(name="my-mcp-server")
```

---

## Resource Catalog

Search and list tenant or folder resources.

```python
# Search for resources
resources = sdk.resource_catalog.search(query="invoice processing")

# List resources in a folder
resources = sdk.resource_catalog.list(folder_path="Finance")
```

---

## Folders

Resolve folder paths to folder keys.

```python
# Get folder key from path
folder_key = sdk.folders.retrieve_key(folder_path="Finance/Invoices")
```

---

## Common Patterns

### Folder Targeting

Most services accept optional `folder_key` or `folder_path` parameters to target a specific Orchestrator folder:

```python
# Using folder path
asset = sdk.assets.retrieve(name="MyAsset", folder_path="Finance/Invoices")

# Using folder key
asset = sdk.assets.retrieve(name="MyAsset", folder_key="abc-123-def")
```

### Async Usage

All services have async variants with the `_async` suffix:

```python
# Sync
asset = sdk.assets.retrieve(name="MyAsset")

# Async
asset = await sdk.assets.retrieve_async(name="MyAsset")
```

### Error Handling

```python
try:
    asset = sdk.assets.retrieve(name="NonExistent")
except Exception as e:
    print(f"Asset not found: {e}")
```

## Next Steps

- **Set up a project**: See [Project Setup](setup.md) for set up new or existing agent projects
- **Deploy**: See [Deployment](deployment.md) to publish your agent to UiPath Cloud

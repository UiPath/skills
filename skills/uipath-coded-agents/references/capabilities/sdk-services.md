# UiPath SDK Services Reference

Complete reference for all platform services available through the UiPath Python SDK.

## SDK Initialization

```python
from uipath.platform import UiPath

sdk = UiPath()  # Reads credentials from environment variables

# Or with explicit credentials
sdk = UiPath(base_url="https://cloud.uipath.com/...", secret="your_token")
sdk = UiPath(client_id="id", client_secret="secret", scope="scope", base_url="url")
```

> **CRITICAL: Never import or instantiate `UiPath()` at module level.** It requires auth credentials at construction time. Always create the instance inside a function or graph node — never at the top of the file. `uip codedagents init` imports your module to introspect it, and module-level `UiPath()` will fail.

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

All services support **synchronous** and **asynchronous** methods (async methods have an `_async` suffix).

---

## Processes

```python
job = sdk.processes.invoke(name="MyProcess", input_arguments={"param1": "value1"}, folder_path="MyFolder")
job = await sdk.processes.invoke_async(name="MyProcess", input_arguments={"param1": "value1"})
```

## Jobs

```python
job = sdk.jobs.retrieve(job_key="abc-123", folder_path="MyFolder")
output = sdk.jobs.extract_output(job)
sdk.jobs.resume(job_id="abc-123", payload={"approved": True})
attachment_key = sdk.jobs.create_attachment(name="report.pdf", source_path="/path/to/report.pdf", job_key="abc-123")
attachments = sdk.jobs.list_attachments(job_key=uuid.UUID("abc-123"))
payload = sdk.jobs.retrieve_api_payload(inbox_id="inbox-123")
```

## Assets

```python
asset = sdk.assets.retrieve(name="MyAsset", folder_path="MyFolder")
credential = sdk.assets.retrieve_credential(name="MyCredential")
sdk.assets.update(robot_asset=asset, folder_path="MyFolder")
```

## Attachments

```python
key = sdk.attachments.upload(name="data.csv", source_path="/path/to/data.csv")
key = sdk.attachments.upload(name="notes.txt", content="Hello, world!")
path = sdk.attachments.download(key=uuid.UUID("abc-123"), destination_path="/path/to/download/")
sdk.attachments.delete(key=uuid.UUID("abc-123"))
```

## Buckets

```python
bucket = sdk.buckets.retrieve(name="MyBucket")
sdk.buckets.upload(name="MyBucket", blob_file_path="reports/output.csv", source_path="/local/path/output.csv")
sdk.buckets.upload(name="MyBucket", blob_file_path="data/result.json", content='{"status": "done"}', content_type="application/json")
sdk.buckets.download(name="MyBucket", blob_file_path="reports/output.csv", destination_path="/local/download/")
```

## Queues

```python
sdk.queues.create_item(item={"Name": "MyQueue", "SpecificContent": {"order_id": "12345"}})
sdk.queues.create_items(queue_name="MyQueue", items=[{"SpecificContent": {"order_id": "001"}}], commit_type="AllOrNothing")
sdk.queues.create_transaction_item(item={"Name": "MyQueue", "SpecificContent": {"task": "process_order"}})
sdk.queues.complete_transaction_item(transaction_key="txn-123", result={"IsSuccessful": True, "Output": {"status": "done"}})
sdk.queues.update_progress_of_transaction_item(transaction_key="txn-123", progress="Processing step 3 of 5")
items = sdk.queues.list_items()
```

## Actions

```python
action = sdk.actions.create(title="Review Invoice", data={"invoice_id": "1234"}, app_name="InvoiceReview", assignee="user@example.com")
action = sdk.actions.retrieve(action_key="action-key-123")
```

## Context Grounding

```python
index = sdk.context_grounding.retrieve(name="KnowledgeBase")
results = sdk.context_grounding.search(name="KnowledgeBase", query="How do I reset my password?", number_of_results=5)
index = sdk.context_grounding.create_index(name="MyIndex", source={"type": "bucket", "bucketName": "docs-bucket"})
sdk.context_grounding.add_to_index(name="MyIndex", blob_file_path="docs/guide.pdf", source_path="/local/guide.pdf")
sdk.context_grounding.ingest_data(index=index)
sdk.context_grounding.delete_index(index=index)
```

## Documents

```python
extraction = sdk.documents.extract(project_name="InvoiceExtraction", tag="invoice", file_path="/path/to/invoice.pdf")
validation = sdk.documents.create_validation_action(
    action_title="Validate Invoice", action_priority="Normal", action_catalog="InvoiceValidation",
    action_folder="Invoices", storage_bucket_name="doc-storage",
    storage_bucket_directory_path="validations/", extraction_response=extraction
)
result = sdk.documents.get_validation_result(validation_action=validation)
```

## Entities

```python
entities = sdk.entities.list_entities()
entity = sdk.entities.retrieve(entity_key="Customers")
records = sdk.entities.list_records(entity_key="Customers", start=0, limit=50)
sdk.entities.insert_records(entity_key="Customers", records=[{"Name": "Acme", "Email": "info@acme.com"}])
sdk.entities.update_records(entity_key="Customers", records=[{"Id": "rec-123", "Email": "new@acme.com"}])
sdk.entities.delete_records(entity_key="Customers", record_ids=["rec-123"])
```

## Connections

```python
connections = sdk.connections.list(name="Salesforce")
connection = sdk.connections.retrieve(key="conn-key-123")
token = sdk.connections.retrieve_token(key="conn-key-123", token_type="direct")
metadata = sdk.connections.metadata(element_instance_id=123, tool_path="/contacts")
payload = sdk.connections.retrieve_event_payload(event_args=event_args)
```

## LLM

```python
response = sdk.llm.chat_completions(
    messages=[{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "Summarize this."}],
    model="gpt-4o-mini-2024-07-18", max_tokens=4096, temperature=0
)

# Structured output with Pydantic
response = sdk.llm.chat_completions(messages=[...], model="gpt-4o-mini-2024-07-18", response_format=MyPydanticModel)

# With tools
response = sdk.llm.chat_completions(messages=[...], model="gpt-4o-mini-2024-07-18", tools=[tool_def], tool_choice="auto")
```

## LLM OpenAI

```python
response = sdk.llm_openai.chat_completions(messages=[{"role": "user", "content": "Hello!"}], model="gpt-4o-mini-2024-07-18")
embeddings = sdk.llm_openai.embeddings(input="The quick brown fox", embedding_model="text-embedding-ada-002")
```

## Guardrails

```python
result = sdk.guardrails.evaluate(guardrail_name="ContentSafety", data={"prompt": "User message"}, folder_path="MyFolder")
```

## Tasks

```python
task = sdk.tasks.create(title="Review document", data={"document_id": "doc-123"}, app_name="DocumentReview", assignee="reviewer@company.com")
task = sdk.tasks.retrieve(task_key="task-key-123")
```

## AgentHub

```python
models = sdk.agenthub.list_models()
result = sdk.agenthub.invoke(agent_name="system-agent", input_data={"query": "Help me"})
```

## MCP

```python
servers = sdk.mcp.list()
server = sdk.mcp.retrieve(name="my-mcp-server")
```

## Resource Catalog

```python
resources = sdk.resource_catalog.search(query="invoice processing")
resources = sdk.resource_catalog.list(folder_path="Finance")
```

## Folders

```python
folder_key = sdk.folders.retrieve_key(folder_path="Finance/Invoices")
```

---

## Common Patterns

### Folder Targeting

Most services accept `folder_key` or `folder_path`:
```python
asset = sdk.assets.retrieve(name="MyAsset", folder_path="Finance/Invoices")
asset = sdk.assets.retrieve(name="MyAsset", folder_key="abc-123-def")
```

### Async Usage

All services have async variants with `_async` suffix:
```python
asset = await sdk.assets.retrieve_async(name="MyAsset")
```

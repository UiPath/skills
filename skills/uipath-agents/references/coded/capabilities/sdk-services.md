# UiPath SDK Services Reference

Reference for platform services available through the UiPath Python SDK.

## Initialization

```python
from uipath.platform import UiPath

# Create inside a function or graph node, never at module level.
sdk = UiPath()  # Reads credentials from environment variables
sdk = UiPath(base_url="https://cloud.uipath.com/...", secret="your_token")
sdk = UiPath(client_id="id", client_secret="secret", scope="scope", base_url="url")
```

**Never import or instantiate `UiPath()` at module level.** Construction requires authentication credentials, and `uip codedagent init` imports the module to introspect it. Create the instance inside a function or graph node. All services provide synchronous methods and asynchronous counterparts with an `_async` suffix.

## Services

| Service | Property | Purpose |
|---|---|---|
| Processes | `sdk.processes` | Start process executions |
| Jobs | `sdk.jobs` | Manage jobs, attachments, and output |
| Assets | `sdk.assets` | Retrieve and update assets and credentials |
| Attachments | `sdk.attachments` | Upload, download, and delete attachments |
| Buckets | `sdk.buckets` | Cloud storage file operations |
| Queues | `sdk.queues` | Queue item and transaction management |
| Context Grounding | `sdk.context_grounding` | RAG index management and search |
| Documents | `sdk.documents` | Document extraction and validation |
| Entities | `sdk.entities` | Data Service entities and records |
| Connections | `sdk.connections` | Integration Service connections |
| LLM | `sdk.llm` | Normalized LLM Gateway chat completions |
| LLM OpenAI | `sdk.llm_openai` | OpenAI-compatible chat and embeddings |
| Guardrails | `sdk.guardrails` | Evaluate guardrails on data |
| Folders | `sdk.folders` | Folder key resolution |
| Tasks | `sdk.tasks` | Action Center task management |
| AgentHub | `sdk.agenthub` | LLM discovery and system-agent invocation |
| MCP | `sdk.mcp` | List and retrieve MCP servers |
| Resource Catalog | `sdk.resource_catalog` | Search and list tenant/folder resources |

## Operations

### Processes and Jobs

```python
job = sdk.processes.invoke(name="MyProcess", input_arguments={"param1": "value1"}, folder_path="MyFolder")
job = await sdk.processes.invoke_async(name="MyProcess", input_arguments={"param1": "value1"})

job = sdk.jobs.retrieve(job_key="abc-123", folder_path="MyFolder")
output = sdk.jobs.extract_output(job)
sdk.jobs.resume(job_id="abc-123", payload={"approved": True})
attachment_key = sdk.jobs.create_attachment(name="report.pdf", source_path="/path/to/report.pdf", job_key="abc-123")
attachments = sdk.jobs.list_attachments(job_key=uuid.UUID("abc-123"))
payload = sdk.jobs.retrieve_api_payload(inbox_id="inbox-123")
```

### Assets, Attachments, and Buckets

```python
asset = sdk.assets.retrieve(name="MyAsset", folder_path="MyFolder")
credential = sdk.assets.retrieve_credential(name="MyCredential")
sdk.assets.update(robot_asset=asset, folder_path="MyFolder")

key = sdk.attachments.upload(name="data.csv", source_path="/path/to/data.csv")
key = sdk.attachments.upload(name="notes.txt", content="Hello, world!")
path = sdk.attachments.download(key=uuid.UUID("abc-123"), destination_path="/path/to/download/")
sdk.attachments.delete(key=uuid.UUID("abc-123"))

bucket = sdk.buckets.retrieve(name="MyBucket")
sdk.buckets.upload(name="MyBucket", blob_file_path="reports/output.csv", source_path="/local/path/output.csv")
sdk.buckets.upload(name="MyBucket", blob_file_path="data/result.json", content='{"status": "done"}', content_type="application/json")
sdk.buckets.download(name="MyBucket", blob_file_path="reports/output.csv", destination_path="/local/download/")
```

### Queues and Tasks

```python
sdk.queues.create_item(item={"Name": "MyQueue", "SpecificContent": {"order_id": "12345"}})
sdk.queues.create_items(queue_name="MyQueue", items=[{"SpecificContent": {"order_id": "001"}}], commit_type="AllOrNothing")
sdk.queues.create_transaction_item(item={"Name": "MyQueue", "SpecificContent": {"task": "process_order"}})
sdk.queues.complete_transaction_item(transaction_key="txn-123", result={"IsSuccessful": True, "Output": {"status": "done"}})
sdk.queues.update_progress_of_transaction_item(transaction_key="txn-123", progress="Processing step 3 of 5")
items = sdk.queues.list_items()

task = sdk.tasks.create(title="Review document", data={"document_id": "doc-123"}, app_name="DocumentReview", assignee="reviewer@company.com")
task = sdk.tasks.retrieve(action_key="task-key-123")
```

### Context Grounding and Documents

```python
index = sdk.context_grounding.retrieve(name="KnowledgeBase")
results = sdk.context_grounding.search(name="KnowledgeBase", query="How do I reset my password?", number_of_results=5)
index = sdk.context_grounding.create_index(name="MyIndex", source={"type": "bucket", "bucketName": "docs-bucket"})
sdk.context_grounding.add_to_index(name="MyIndex", blob_file_path="docs/guide.pdf", source_path="/local/guide.pdf")
sdk.context_grounding.ingest_data(index=index)
sdk.context_grounding.delete_index(index=index)

extraction = sdk.documents.extract(project_name="InvoiceExtraction", tag="invoice", file_path="/path/to/invoice.pdf")
validation = sdk.documents.create_validation_action(
    action_title="Validate Invoice", action_priority="Normal", action_catalog="InvoiceValidation",
    action_folder="Invoices", storage_bucket_name="doc-storage",
    storage_bucket_directory_path="validations/", extraction_response=extraction
)
result = sdk.documents.get_validation_result(validation_action=validation)
```

### Entities

```python
entities = sdk.entities.list_entities()
entity = sdk.entities.retrieve(entity_key="Customers")
records = sdk.entities.list_records(entity_key="Customers", start=0, limit=50)
sdk.entities.insert_records(entity_key="Customers", records=[{"Name": "Acme", "Email": "info@acme.com"}])
sdk.entities.update_records(entity_key="Customers", records=[{"Id": "rec-123", "Email": "new@acme.com"}])
sdk.entities.delete_records(entity_key="Customers", record_ids=["rec-123"])
```

### Connections

```python
connections = sdk.connections.list(name="Salesforce")
connection = sdk.connections.retrieve(key="conn-key-123")
token = sdk.connections.retrieve_token(key="conn-key-123", token_type="direct")
metadata = sdk.connections.metadata(element_instance_id=123, connector_key="uipath-salesforce", tool_path="/contacts")
payload = sdk.connections.retrieve_event_payload(event_args=event_args)
result = sdk.connections.invoke_activity(activity_metadata=meta, connection_id="conn-key-123", activity_input={"query": "site:uipath.com"})
result = await sdk.connections.invoke_activity_async(activity_metadata=meta, connection_id="conn-key-123", activity_input={...})
```

See [integration-service.md](integration-service.md) for the full discover-and-invoke flow.

### LLM Services

```python
response = sdk.llm.chat_completions(
    messages=[{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "Summarize this."}],
    model="gpt-4o-mini-2024-07-18", max_tokens=4096, temperature=0
)
response = sdk.llm.chat_completions(messages=[...], model="gpt-4o-mini-2024-07-18", response_format=MyPydanticModel)
response = sdk.llm.chat_completions(messages=[...], model="gpt-4o-mini-2024-07-18", tools=[tool_def], tool_choice="auto")

response = sdk.llm_openai.chat_completions(messages=[{"role": "user", "content": "Hello!"}], model="gpt-4o-mini-2024-07-18")
embeddings = sdk.llm_openai.embeddings(input="The quick brown fox", embedding_model="text-embedding-ada-002")
```

### Guardrails, AgentHub, MCP, Resource Catalog, and Folders

```python
result = sdk.guardrails.evaluate(guardrail_name="ContentSafety", data={"prompt": "User message"}, folder_path="MyFolder")

models = sdk.agenthub.get_available_llm_models()
# Each item exposes .model_name and .vendor
openai_model = next(m.model_name for m in models if m.vendor == "OpenAI")
job_key = sdk.agenthub.invoke_system_agent(agent_name="system-agent", entrypoint="main", input_arguments={"query": "Help me"})

servers = sdk.mcp.list()
server = sdk.mcp.retrieve(slug="my-mcp-server", folder_path="MyFolder")

resources = sdk.resource_catalog.search(query="invoice processing")
resources = sdk.resource_catalog.list(folder_path="Finance")

folder_key = sdk.folders.retrieve_key(folder_path="Finance/Invoices")
```

## Common Patterns

Most services accept `folder_key` or `folder_path`:

```python
asset = sdk.assets.retrieve(name="MyAsset", folder_path="Finance/Invoices")
asset = sdk.assets.retrieve(name="MyAsset", folder_key="abc-123-def")
```

Use the corresponding `_async` method when awaiting a service call:

```python
asset = await sdk.assets.retrieve_async(name="MyAsset")
```

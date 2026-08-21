## CLI Commands Reference

The UiPath Python SDK provides a comprehensive CLI for managing coded agents and automation projects. All commands should be executed with `uv run uipath <command>`.

### Command Overview

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `init` | Initialize agent project | Creating a new agent or updating schema |
| `run` | Execute agent | Running agent locally or testing |
| `eval` | Evaluate agent | Testing agent performance with evaluation sets |

---

### `uipath init`

**Description:** Initialize the project.

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--no-agents-md-override` | flag | false | Won't override existing .agent files and AGENTS.md file. |

**Usage Examples:**

```bash
# Initialize a new agent project
uv run uipath init

# Initialize with specific entrypoint
uv run uipath init main.py

# Initialize and infer bindings from code
uv run uipath init --infer-bindings
```

**When to use:** Run this command when you've modified the Input/Output models and need to regenerate the `uipath.json` schema file.

---

### `uipath run`

**Description:** Execute the project.

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `entrypoint` | No | N/A |
| `input` | No | N/A |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--resume` | flag | false | Resume execution from a previous state |
| `-f`, `--file` | value | `Sentinel.UNSET` | File path for the .json input |
| `--input-file` | value | `Sentinel.UNSET` | Alias for '-f/--file' arguments |
| `--output-file` | value | `Sentinel.UNSET` | File path where the output will be written |
| `--trace-file` | value | `Sentinel.UNSET` | File path where the trace spans will be written (JSON Lines format) |
| `--state-file` | value | `Sentinel.UNSET` | File path where the state file is stored for persisting execution state. If not provided, a temporary file will be used. |
| `--debug` | flag | false | Enable debugging with debugpy. The process will wait for a debugger to attach. |
| `--debug-port` | value | `5678` | Port for the debug server (default: 5678) |
| `--keep-state-file` | flag | false | Keep the temporary state file even when not resuming and no job id is provided |
| `--simulation` | value | none | Simulation config as a JSON object (same schema as simulation.json) |

**Usage Examples:**

```bash
# Run agent with inline JSON input
uv run uipath run main.py '{"query": "What is the weather?"}'

# Run agent with input from file
uv run uipath run main.py --file input.json

# Run agent and save output to file
uv run uipath run agent '{"task": "Process data"}' --output-file result.json

# Run agent with debugging enabled
uv run uipath run main.py '{"input": "test"}' --debug --debug-port 5678

# Resume agent execution from previous state
uv run uipath run --resume
```

**When to use:** Run this command to execute your agent locally for development, testing, or debugging. Use `--debug` flag to attach a debugger for step-by-step debugging.

---

### `uipath eval`

**Description:** Run an evaluation set against the agent.

    Args:
        entrypoint: Path to the agent script to evaluate (optional, will auto-discover if not specified)
        eval_set: Path to the evaluation set JSON file (optional, will auto-discover if not specified)
        eval_ids: Optional list of evaluation IDs
        eval_set_run_id: Custom evaluation set run ID (optional, will generate UUID if not specified)
        workers: Number of parallel workers for running evaluations
        no_report: Do not report the evaluation results
        enable_mocker_cache: Enable caching for LLM mocker responses
        report_coverage: Report evaluation coverage
        model_settings_id: Model settings ID to override agent settings
        trace_file: File path where traces will be written in JSONL format
        max_llm_concurrency: Maximum concurrent LLM requests
        input_overrides: Input field overrides mapping (direct field override with deep merge)
        resume: Resume execution from a previous suspended state
    

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `entrypoint` | No | N/A |
| `eval_set` | No | N/A |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--eval-set-run-id` | value | `Sentinel.UNSET` | Custom evaluation set run ID (if not provided, a UUID will be generated) |
| `--no-report` | flag | false | Do not report the evaluation results |
| `--workers` | value | `1` | Number of parallel workers for running evaluations (default: 1) |
| `--output-file` | value | `Sentinel.UNSET` | File path where the output will be written |
| `--enable-mocker-cache` | flag | false | Enable caching for LLM mocker responses |
| `--report-coverage` | flag | false | Report evaluation coverage |
| `--model-settings-id` | value | `"default"` | Model settings ID from evaluation set to override agent settings (default: 'default') |
| `--trace-file` | value | `Sentinel.UNSET` | File path where traces will be written in JSONL format |
| `--max-llm-concurrency` | value | `20` | Maximum concurrent LLM requests (default: 20) |
| `--resume` | flag | false | Resume execution from a previous suspended state |
| `--verbose` | flag | false | Include agent execution output (trace, result) in the output file |

**Usage Examples:**

```bash
# Run evaluation with auto-discovered files
uv run uipath eval

# Run evaluation with specific entrypoint and eval set
uv run uipath eval main.py eval_set.json

# Run evaluation without reporting results
uv run uipath eval --no-report

# Run evaluation with custom number of workers
uv run uipath eval --workers 4

# Save evaluation output to file
uv run uipath eval --output-file eval_results.json
```

**When to use:** Run this command to test your agent's performance against a predefined evaluation set. This helps validate agent behavior and measure quality metrics.

---

### Common Workflows

**1. Creating a New Agent:**
```bash
# Step 1: Initialize project
uv run uipath init

# Step 2: Run agent to test
uv run uipath run main.py '{"input": "test"}'

# Step 3: Evaluate agent performance
uv run uipath eval
```

**2. Development & Testing:**
```bash
# Run with debugging
uv run uipath run main.py '{"input": "test"}' --debug

# Test with input file
uv run uipath run main.py --file test_input.json --output-file test_output.json
```

**3. Schema Updates:**
```bash
# After modifying Input/Output models, regenerate schema
uv run uipath init --infer-bindings
```

### Configuration File (uipath.json)

The `uipath.json` file is automatically generated by `uipath init` and defines your agent's schema and bindings.

**Structure:**

```json
{
  "entryPoints": [
    {
      "filePath": "agent",
      "uniqueId": "uuid-here",
      "type": "agent",
      "input": {
        "type": "object",
        "properties": { ... },
        "description": "Input schema",
        "required": [ ... ]
      },
      "output": {
        "type": "object",
        "properties": { ... },
        "description": "Output schema",
        "required": [ ... ]
      }
    }
  ],
  "bindings": {
    "version": "2.0",
    "resources": []
  }
}
```

**When to Update:**

1. **After Modifying Input/Output Models**: Run `uv run uipath init --infer-bindings` to regenerate schemas
2. **Changing Entry Point**: Update `filePath` if you rename or move your main file
3. **Manual Schema Adjustments**: Edit `input.jsonSchema` or `output.jsonSchema` directly if needed
4. **Bindings Updates**: The `bindings` section maps the exported graph variable - update if you rename your graph

**Important Notes:**

- The `uniqueId` should remain constant for the same agent
- Always use `type: "agent"` for LangGraph agents
- The `jsonSchema` must match your Pydantic models exactly
- Re-run `uipath init --infer-bindings` instead of manual edits when possible


## Service Commands Reference

The UiPath CLI provides commands for interacting with UiPath platform services. These commands allow you to manage buckets, assets, jobs, and other resources.

### `uipath assets`

Manage UiPath assets.

    Assets are key-value pairs that store configuration data, credentials,
    and settings used by automation processes.

    \b
    Examples:
        # List all assets in a folder
        uipath assets list --folder-path "Shared"

        # List with filter
        uipath assets list --filter "ValueType eq 'Text'"

        # List with ordering
        uipath assets list --orderby "Name asc"
    

**Subcommands:**

**`uipath assets list`**

List assets in a folder.

    \b
    Examples:
        uipath assets list
        uipath assets list --folder-path "Shared"
        uipath assets list --filter "ValueType eq 'Text'"
        uipath assets list --filter "Name eq 'MyAsset'"
        uipath assets list --orderby "Name asc"
        uipath assets list --top 50 --skip 100
    

Options:
- `--filter`: OData $filter expression (default: `Sentinel.UNSET`)
- `--orderby`: OData $orderby expression (default: `Sentinel.UNSET`)
- `--top`: Maximum number of items to return (default: 100, max: 1000) (default: `100`)
- `--skip`: Number of items to skip (default: `0`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

---

### `uipath buckets`

Manage UiPath storage buckets and files.

Buckets are cloud storage containers for files used by automation processes.


Bucket Operations:
    list      - List all buckets
    create    - Create a new bucket
    delete    - Delete a bucket
    retrieve  - Get bucket details
    exists    - Check if bucket exists


File Operations (use 'buckets files' subcommand):
    files list     - List files in a bucket
    files search   - Search files using glob patterns
    files upload   - Upload a file to a bucket
    files download - Download a file from a bucket
    files delete   - Delete a file from a bucket
    files exists   - Check if a file exists


Examples:
    
    # Bucket operations with explicit folder
    uipath buckets list --folder-path "Shared"
    uipath buckets create my-bucket --description "Data storage"
    uipath buckets exists my-bucket
    uipath buckets delete my-bucket --confirm
    
    # Using environment variable for folder context
    export UIPATH_FOLDER_PATH="Shared"
    uipath buckets list
    uipath buckets create my-bucket --description "Data storage"
    
    # File operations
    uipath buckets files list my-bucket
    uipath buckets files search my-bucket "*.pdf"
    uipath buckets files upload my-bucket ./data.csv remote/data.csv
    uipath buckets files download my-bucket data.csv ./local.csv
    uipath buckets files delete my-bucket old-data.csv --confirm
    uipath buckets files exists my-bucket data.csv


**Subcommands:**

**`uipath buckets create`**

Create a new Bucket.

Examples:
    uipath buckets create my-resource
    uipath buckets create my-resource --folder-path Shared


Arguments:
- `name` (required): N/A

Options:
- `--description`: Bucket description
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets delete`**

Delete a bucket.

    
    Examples:
        uipath buckets delete my-bucket --confirm
        uipath buckets delete my-bucket --dry-run
    

Arguments:
- `name` (required): N/A

Options:
- `--confirm`: Skip confirmation prompt
- `--dry-run`: Show what would be deleted without deleting
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets exists`**

Check if a Bucket exists.

Examples:
    uipath buckets exists my-resource
    uipath buckets exists my-resource --folder-path Shared


Arguments:
- `name` (required): N/A

Options:
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

#### `uipath buckets files`

Manage files within buckets.

    
    Examples:
        
        # List files in a bucket
        uipath buckets files list my-bucket
        
        # Search for files with glob pattern
        uipath buckets files search my-bucket "*.pdf"
        
        # Upload a file
        uipath buckets files upload my-bucket ./data.csv remote/data.csv
        
        # Download a file
        uipath buckets files download my-bucket data.csv ./local.csv
        
        # Delete a file
        uipath buckets files delete my-bucket old-data.csv --confirm
        
        # Check if file exists
        uipath buckets files exists my-bucket data.csv
    

**`uipath buckets files delete`**

Delete a file from a bucket.

    
    Arguments:
        BUCKET_NAME: Name of the bucket
        FILE_PATH: Path to file in bucket

    
    Examples:
        uipath buckets files delete my-bucket old-data.csv --confirm
        uipath buckets files delete reports archive/old.pdf --dry-run
    

Arguments:
- `bucket_name` (required): N/A
- `file_path` (required): N/A

Options:
- `--confirm`: Skip confirmation prompt
- `--dry-run`: Show what would be deleted
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets files download`**

Download a file from a bucket.

    
    Arguments:
        BUCKET_NAME: Name of the bucket
        REMOTE_PATH: Path to file in bucket
        LOCAL_PATH: Local destination path

    
    Examples:
        uipath buckets files download my-bucket data.csv ./downloads/data.csv
        uipath buckets files download reports monthly/report.pdf ./report.pdf
    

Arguments:
- `bucket_name` (required): N/A
- `remote_path` (required): N/A
- `local_path` (required): N/A

Options:
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets files exists`**

Check if a file exists in a bucket.

    
    Arguments:
        BUCKET_NAME: Name of the bucket
        FILE_PATH: Path to file in bucket

    
    Examples:
        uipath buckets files exists my-bucket data.csv
        uipath buckets files exists reports monthly/report.pdf
    

Arguments:
- `bucket_name` (required): N/A
- `file_path` (required): N/A

Options:
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets files list`**

List files in a bucket.

    
    Arguments:
        BUCKET_NAME: Name of the bucket

    
    Examples:
        uipath buckets files list my-bucket
        uipath buckets files list my-bucket --prefix "data/"
        uipath buckets files list reports --limit 10 --format json
        uipath buckets files list my-bucket --all
    

Arguments:
- `bucket_name` (required): N/A

Options:
- `--prefix`: Filter files by prefix (default: ``)
- `--limit`: Maximum number of files to return (default: `Sentinel.UNSET`)
- `--offset`: Number of files to skip (default: `0`)
- `--all`: Fetch all files (auto-paginate)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets files search`**

Search for files using glob patterns.

    Uses the GetFiles API which supports glob patterns like *.pdf or data_*.csv.

    
    Arguments:
        BUCKET_NAME: Name of the bucket
        PATTERN: Glob pattern to match files (e.g., "*.pdf", "data_*.csv")

    
    Examples:
        uipath buckets files search my-bucket "*.pdf"
        uipath buckets files search reports "*.csv" --recursive
        uipath buckets files search my-bucket "data_*.json" --prefix "archive/"
    

Arguments:
- `bucket_name` (required): N/A
- `pattern` (required): N/A

Options:
- `--prefix`: Directory path to search in (default: ``)
- `--recursive`: Search subdirectories recursively
- `--limit`: Maximum number of files to return (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets files upload`**

Upload a file to a bucket.

    
    Arguments:
        BUCKET_NAME: Name of the bucket
        LOCAL_PATH: Local file to upload
        REMOTE_PATH: Destination path in bucket

    
    Examples:
        uipath buckets files upload my-bucket ./data.csv remote/data.csv
        uipath buckets files upload reports ./report.pdf monthly/report.pdf
    

Arguments:
- `bucket_name` (required): N/A
- `local_path` (required): N/A
- `remote_path` (required): N/A

Options:
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets list`**

List all Buckets.

Examples:
    uipath buckets list
    uipath buckets list --folder-path Shared


Options:
- `--limit`: Maximum number of items to return (default: `Sentinel.UNSET`)
- `--offset`: Number of items to skip (default: `0`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath buckets retrieve`**

Retrieve a bucket by name or key.

    
    Examples:
        uipath buckets retrieve --name "my-bucket"
        uipath buckets retrieve --key "abc-123-def-456" --format json
    

Options:
- `--name`: Bucket name (default: `Sentinel.UNSET`)
- `--key`: Bucket key (UUID) (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

---

### `uipath context-grounding`

Manage UiPath Context Grounding indexes.

    Context Grounding indexes store and search contextual information
    used to enhance AI-enabled automation processes.

    
    Two index types:
        Regular   - Persistent, backed by bucket or connection, created via 'create'
        Ephemeral - Temporary, no Orchestrator folder, created from local files via 'create-ephemeral'

    
    Examples:
        uipath context-grounding list --folder-path "Shared"
    

**Subcommands:**

#### `uipath context-grounding batch-transform`

Manage Batch Transform tasks.

    Batch Transform processes and transforms CSV files from context
    grounding indexes.

    
    Examples:
        uipath context-grounding batch-transform start --help
    

**`uipath context-grounding batch-transform download`**

Download a Batch Transform result file.

    
    Examples:
        uipath context-grounding batch-transform download --task-id abc-123 --output-file result.csv
    

Options:
- `--task-id`: ID of the Batch Transform task (default: `Sentinel.UNSET`)
- `--output-file`: Local destination path for the result file (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding batch-transform retrieve`**

Retrieve a Batch Transform task status.

    
    Examples:
        uipath context-grounding batch-transform retrieve --task-id abc-123-def-456
    

Options:
- `--task-id`: ID of the Batch Transform task (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding batch-transform start`**

Start a Batch Transform task on an index.

    The index must contain CSV files. Only one file is processed per task.

    
    Two ways to specify the index:
        Regular index:   --index-name + --folder-path
        Ephemeral index: --index-id

    
    --columns-file is a JSON array defining output columns:
        [
          {"name": "entity", "description": "Extracted entity name"},
          {"name": "category", "description": "Entity category"}
        ]

    
    Examples:
        uipath context-grounding batch-transform start --index-name my-index --task-name my-task --prompt "Extract" --columns-file cols.json
        uipath context-grounding batch-transform start --index-id abc-123 --task-name my-task --prompt "Extract" --columns-file cols.json
    

Options:
- `--index-name`: Name of the context grounding index (default: `Sentinel.UNSET`)
- `--index-id`: ID of the context grounding index (ephemeral indexes only) (default: `Sentinel.UNSET`)
- `--task-name`: Name for the Batch Transform task (default: `Sentinel.UNSET`)
- `--prompt`: Task prompt describing what to process (default: `Sentinel.UNSET`)
- `--columns-file`: JSON file defining output columns (see format above) (default: `Sentinel.UNSET`)
- `--target-file`: Specific file name to target in the index (default: `Sentinel.UNSET`)
- `--prefix`: Storage bucket folder path prefix for filtering files (default: `Sentinel.UNSET`)
- `--web-search`: Enable web search grounding
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding create`**

Create a new context grounding index (persistent).

    The created index lives in an Orchestrator folder. Ingestion must be
    triggered separately after creation.

    
    Two ways to specify the data source:
        --bucket-source   Bucket name for bucket-backed indexes
        --source-file     JSON file for connections (use 'source-schema' to see formats)

    
    Examples:
        uipath context-grounding create --index-name my-index --bucket-source my-bucket
        uipath context-grounding create --index-name my-index --source-file config.json
    

Options:
- `--index-name`: Name of the index to create (default: `Sentinel.UNSET`)
- `--source-file`: JSON file with connection source configuration (Google Drive, OneDrive, Dropbox, Confluence) (default: `Sentinel.UNSET`)
- `--bucket-source`: Bucket name for bucket-backed indexes (default: `Sentinel.UNSET`)
- `--description`: Description of the index (default: ``)
- `--extraction-strategy`: Extraction strategy (default: LLMV4) (default: `LLMV4`)
- `--file-type`: File type filter (e.g., 'pdf', 'txt') (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding create-ephemeral`**

Create an ephemeral index from local files (temporary).

    Uploads files as attachments and creates a temporary index. Reference it
    in other commands with --index-id (no folder, no name). Ingestion starts
    automatically. Poll with 'retrieve --index-id <id>' until
    lastIngestionStatus is Successful before starting a task.

    
    Supported file types:
        DeepRAG:  PDF, TXT
        BatchRAG: CSV

    
    Examples:
        uipath context-grounding create-ephemeral --usage DeepRAG --files doc1.pdf --files doc2.pdf
        uipath context-grounding create-ephemeral --usage BatchRAG --files data.csv
    

Options:
- `--usage`: Task type for the ephemeral index (default: `Sentinel.UNSET`)
- `--files`: Local file paths to upload as attachments (repeatable) (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

#### `uipath context-grounding deep-rag`

Manage Deep RAG tasks.

    Deep RAG performs multi-document research and synthesis on context
    grounding indexes.

    
    Examples:
        uipath context-grounding deep-rag start --help
    

**`uipath context-grounding deep-rag retrieve`**

Retrieve a Deep RAG task result (status, summary, citations).

    
    Examples:
        uipath context-grounding deep-rag retrieve --task-id abc-123-def-456
    

Options:
- `--task-id`: ID of the Deep RAG task (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding deep-rag start`**

Start a Deep RAG task on an index.

    
    Two ways to specify the index:
        Regular index:   --index-name + --folder-path
        Ephemeral index: --index-id

    
    Examples:
        uipath context-grounding deep-rag start --index-name my-index --folder-path Shared --task-name my-task --prompt "Summarize"
        uipath context-grounding deep-rag start --index-id abc-123 --task-name my-task --prompt "Summarize"
    

Options:
- `--index-name`: Name of the context grounding index (default: `Sentinel.UNSET`)
- `--index-id`: ID of the context grounding index (ephemeral indexes only) (default: `Sentinel.UNSET`)
- `--task-name`: Name for the Deep RAG task (default: `Sentinel.UNSET`)
- `--prompt`: Task prompt describing what to research (default: `Sentinel.UNSET`)
- `--glob-pattern`: Glob pattern to filter files in the index (default: **) (default: `**`)
- `--citation-mode`: Citation mode (default: Skip) (default: `Skip`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding delete`**

Delete a context grounding index.

    
    Examples:
        uipath context-grounding delete --index-name my-index --confirm
        uipath context-grounding delete --index-name my-index --dry-run
    

Options:
- `--index-name`: Name of the index to delete (default: `Sentinel.UNSET`)
- `--confirm`: Skip confirmation prompt
- `--dry-run`: Show what would be deleted without deleting
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding ingest`**

Trigger ingestion on a context grounding index.

    Ingestion runs asynchronously. Use 'retrieve' to poll lastIngestionStatus
    until it reaches Successful or Failed.

    
    Examples:
        uipath context-grounding ingest --index-name my-index --folder-path "Shared"
    

Options:
- `--index-name`: Name of the index to ingest (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding list`**

List all context grounding indexes.

    
    Examples:
        uipath context-grounding list --folder-path "Shared"
    

Options:
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding retrieve`**

Retrieve a context grounding index.

    
    Two ways to specify the index:
        Regular index:   --index-name + --folder-path
        Ephemeral index: --index-id

    
    Examples:
        uipath context-grounding retrieve --index-name my-index --folder-path "Shared"
        uipath context-grounding retrieve --index-id abc-123-def-456 --format json
    

Options:
- `--index-name`: Name of the index to retrieve (default: `Sentinel.UNSET`)
- `--index-id`: ID of the index to retrieve (ephemeral indexes only) (default: `Sentinel.UNSET`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding search`**

Search a context grounding index (regular indexes only).

    
    Examples:
        uipath context-grounding search --index-name my-index --query "What is the revenue?"
        uipath context-grounding search --index-name my-index --query "results" --limit 5
    

Options:
- `--index-name`: Name of the index to search (default: `Sentinel.UNSET`)
- `--query`: Search query in natural language (default: `Sentinel.UNSET`)
- `--limit`: Maximum number of results (default: 10) (default: `10`)
- `--threshold`: Minimum similarity threshold (default: 0.0) (default: `0.0`)
- `--search-mode`: Search mode (default: Semantic) (default: `Semantic`)
- `--folder-path`: Folder path (e.g., "Shared"). Can also be set via UIPATH_FOLDER_PATH environment variable. (default: `Sentinel.UNSET`)
- `--folder-key`: Folder key (UUID) (default: `Sentinel.UNSET`)
- `--format`: Output format (overrides global) (default: `Sentinel.UNSET`)
- `--output`, `-o`: Output file (overrides global) (default: `Sentinel.UNSET`)

**`uipath context-grounding source-schema`**

Show JSON source file formats for connection-backed indexes.

    Use this to see the required fields for --source-file when creating
    an index backed by Google Drive, OneDrive, Dropbox, or Confluence.

    
    Examples:
        uipath context-grounding source-schema --type google_drive
    

Options:
- `--type`: Show schema for a specific source type (omit to show all) (default: `Sentinel.UNSET`)

---


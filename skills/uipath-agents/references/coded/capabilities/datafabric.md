# Data Fabric Integration for Coded Agents

How to query and manage UiPath Data Fabric entities from coded agents. Two integration paths exist — choose based on the use case.

## Step 1: Discover Available Entities

Before choosing a path, discover what entities exist. Start with folder-scoped listing — most entities live in a specific folder (commonly `Shared`):

```bash
# List entities in the default Shared folder
uip df entities list --folder-path "Shared" --output table

# If the user specifies a different folder
uip df entities list --folder-path "<FolderName>" --output table

# Get full details for a specific entity (fields, types, IDs)
uip df entities get --name "<EntityName>" --folder-path "Shared"
```

Only fall back to `--include-folders` if the entity isn't found in the expected folder:

```bash
# Search across all folders (can return many results)
uip df entities list --include-folders --output table
```

Each entity in the output has:
- **`Id`** (UUID) — the entity identifier needed for `DataFabricEntityItem`
- **`Name`** — the entity name used in SDK calls (`entity_key`)
- **`FolderId`** (UUID) — the folder key needed for `DataFabricEntityItem`
- **`Fields`** — column names, types, and relationships

**Recommend an entity to the user** based on their use case. For example, if they ask about "customer orders," look for entities with names like `Orders`, `SalesOrder`, or similar. Show them the matching entities and their fields before proceeding.

## Step 2: Choose the Integration Path

| Path | Best for | Trade-off |
|------|----------|-----------|
| **SDK direct** (`sdk.entities`) | The query shape is known at build time — same filter, same fields every time | Reliable, no LLM cost, but you code every query |
| **`create_datafabric_tool`** | Users ask freeform questions the agent can't anticipate | Flexible, but adds an inner LLM call for SQL generation |

**Rule of thumb:** If the user describes a fixed operation (e.g. "look up orders by customer name"), use the SDK. If they say "users can ask anything" or "I can't predict the questions," use `create_datafabric_tool`.

**CRITICAL: For freeform/unpredictable queries, always use `create_datafabric_tool` from `uipath_langchain.agent.tools`.** Do NOT build a custom NL-to-SQL solution, do NOT use internal functions like `create_datafabric_query_tool`, and do NOT wrap raw SDK calls to handle freeform questions. The `create_datafabric_tool` factory handles schema resolution, SQL generation, error correction, and caching — reimplementing this is fragile and unsupported.

Both paths can coexist in a single agent — use SDK for known operations and `create_datafabric_tool` for open-ended exploration.

---

## Path 1: SDK Direct Access (`sdk.entities`)

Use the Python SDK's `EntitiesService` for deterministic CRUD operations. No LLM intermediary — the agent code specifies exactly what to fetch or write.

### Setup

```python
from uipath.platform import UiPath

# CRITICAL: Never instantiate at module level — always inside a function/node.
# Module-level UiPath() fails during `uip codedagent init` introspection.
sdk = UiPath()
```

### Reading Records

```python
# List with OData-style filter and pagination
records = await sdk.entities.list_records_async(
    entity_key="Orders",
    filter="Status eq 'Open'",
    select=["OrderId", "CustomerName", "Total"],
    orderby="CreatedTime desc",
    limit=50,
)

# Single record by ID
record = await sdk.entities.get_record_async(
    entity_key="Orders",
    record_id="abc-123",
)
```

### Structured Query with Filters

For complex filters, aggregations, and joins — use `retrieve_records` with typed filter objects:

```python
from uipath.platform.entities import (
    EntityQueryFilter,
    EntityQueryFilterGroup,
    EntityQuerySortOption,
    EntityAggregate,
    EntityAggregateFunction,
    LogicalOperator,
    QueryFilterOperator,
)

filter_group = EntityQueryFilterGroup(
    logical_operator=LogicalOperator.And,
    query_filters=[
        EntityQueryFilter(
            field_name="Status",
            operator=QueryFilterOperator.Equals,
            value="Open",
        ),
        EntityQueryFilter(
            field_name="Total",
            operator=QueryFilterOperator.GreaterThan,
            value="1000",
        ),
    ],
)

result = await sdk.entities.retrieve_records_async(
    entity_key="Orders",
    filter_group=filter_group,
    sort_options=[EntityQuerySortOption(field_name="Total", is_descending=True)],
    selected_fields=["OrderId", "CustomerName", "Total"],
    limit=20,
)

for record in result.items:
    print(record.id, record.model_extra)
```

### Aggregation

```python
result = await sdk.entities.retrieve_records_async(
    entity_key="Orders",
    aggregates=[
        EntityAggregate(
            function=EntityAggregateFunction.Sum,
            field="Total",
            alias="total_revenue",
        ),
        EntityAggregate(
            function=EntityAggregateFunction.Count,
            field="Id",
            alias="order_count",
        ),
    ],
    group_by=["Status"],
)
```

### Writing Records

```python
# Single insert (fires triggers)
record = await sdk.entities.insert_record_async(
    entity_key="Orders",
    data={"CustomerName": "Acme Corp", "Total": 5000, "Status": "Open"},
)

# Single update (fires triggers)
updated = await sdk.entities.update_record_async(
    entity_key="Orders",
    record_id=record.id,
    data={"Status": "Closed"},
)

# Single delete (fires triggers)
await sdk.entities.delete_record_async(entity_key="Orders", record_id=record.id)

# Batch insert (does NOT fire triggers)
batch_result = await sdk.entities.insert_records_async(
    entity_key="Orders",
    records=[
        {"CustomerName": "Acme", "Total": 5000},
        {"CustomerName": "Globex", "Total": 3000},
    ],
)
# Check batch_result.failure_records for errors
```

### File Attachments

```python
# Upload
await sdk.entities.upload_attachment(
    entity_id="<entity-uuid>",
    record_id="<record-uuid>",
    field_name="Invoice",
    file_path="/path/to/invoice.pdf",
)

# Download
content: bytes = await sdk.entities.download_attachment_async(
    entity_id="<entity-uuid>",
    record_id="<record-uuid>",
    field_name="Invoice",
)
```

### Wiring into a LangGraph Agent

Wrap SDK calls as LangChain tools so the agent can invoke them:

```python
from langchain_core.tools import tool
from uipath.platform import UiPath


@tool
async def get_open_orders(customer_name: str) -> str:
    """Get all open orders for a specific customer.

    Args:
        customer_name: The customer name to look up.
    """
    sdk = UiPath()
    # Escape single quotes for OData string literals (e.g. O'Brien → O''Brien)
    safe_name = customer_name.replace("'", "''")
    records = await sdk.entities.list_records_async(
        entity_key="Orders",
        filter=f"CustomerName eq '{safe_name}' and Status eq 'Open'",
        select=["OrderId", "Total", "CreatedTime"],
        limit=50,
    )
    if not records:
        return f"No open orders found for {customer_name}."
    lines = [f"- {r.model_extra['OrderId']}: ${r.model_extra['Total']}" for r in records]
    return f"Open orders for {customer_name}:\n" + "\n".join(lines)


@tool
async def close_order(order_id: str) -> str:
    """Mark an order as closed.

    Args:
        order_id: The record ID of the order to close.
    """
    sdk = UiPath()
    await sdk.entities.update_record_async(
        entity_key="Orders",
        record_id=order_id,
        data={"Status": "Closed"},
    )
    return f"Order {order_id} closed."
```

Then add to your agent graph:

```python
from uipath_langchain.agent import create_agent
from uipath_langchain.chat import UiPathChat

def _make_llm():
    """Lazy LLM factory — never call at module level."""
    return UiPathChat(model="gpt-4.1-mini-2025-04-14")

graph = create_agent(_make_llm(), tools=[get_open_orders, close_order], system_prompt="...")
```

---

## Path 2: DataFabric Tool (`create_datafabric_tool`)

Use `create_datafabric_tool` when end-users ask freeform questions that the agent can't anticipate at build time. This is the **only supported way** to add NL-to-SQL querying to a coded agent. The tool runs an inner LLM sub-graph that translates natural language to SQL, executes it against Data Fabric, and returns results.

### Required Import

```python
# This is the ONLY correct import. Do NOT use create_datafabric_query_tool
# or any other function from internal submodules.
from uipath_langchain.agent.tools import create_datafabric_tool
```

### Setup

Use the entity ID, name, and folder key from Step 1 discovery.

### Usage

```python
from uipath.platform.entities import DataFabricEntityItem
from uipath_langchain.agent.react.agent import create_agent
from uipath_langchain.agent.tools import create_datafabric_tool
from uipath_langchain.chat import UiPathChat


def _make_llm():
    """Lazy LLM factory — never call at module level."""
    return UiPathChat(model="gpt-4.1-mini-2025-04-14")


system_prompt = "Answer questions using only the configured Data Fabric entities."

llm = _make_llm()
datafabric_tool = create_datafabric_tool(
    llm=llm,
    name="query_orders",
    description="Query order and customer data from Data Fabric.",
    base_system_prompt=system_prompt,
    entities=[
        DataFabricEntityItem(
            id="1312e893-8295-f111-9b33-0022482a9eea",
            name="Orders",
            folder_key="379fec63-62b1-41ec-b2fc-718f8f7dda3c",
        ),
        DataFabricEntityItem(
            id="a1b2c3d4-5678-90ab-cdef-1234567890ab",
            name="Customers",
            folder_key="379fec63-62b1-41ec-b2fc-718f8f7dda3c",
        ),
    ],
)

graph = create_agent(llm, tools=[datafabric_tool], system_prompt=system_prompt)
```

### Key Design Constraint

**The same `system_prompt` must be passed to both `create_agent` and `create_datafabric_tool`.** The tool forwards it to the inner SQL-generation sub-graph so the agent's instructions apply consistently at both levels.

### How It Works Internally

1. Agent receives a freeform user question
2. Agent calls the `datafabric_tool` with a `user_query` string
3. Inner LLM sub-graph resolves entity schemas (lazy, cached after first call)
4. Inner LLM generates a SQL SELECT against the entity schemas
5. SQL executes against Data Fabric; errors loop back to the LLM for self-correction
6. Results return to the outer agent as text

### `create_datafabric_tool` Signature

```python
def create_datafabric_tool(
    *,
    llm: BaseChatModel,        # LLM for the inner SQL generation loop
    name: str,                  # Tool name exposed to the outer agent
    description: str,           # Tool description for agent tool selection
    entities: Sequence[DataFabricEntityItem],  # Entities available to query
    base_system_prompt: str,    # Forwarded to inner sub-graph
) -> BaseTool
```

### `DataFabricEntityItem` Fields

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `id` | `str` (UUID) | Yes | `uip df entities list` |
| `name` | `str` | Yes | Entity display name |
| `folder_key` | `str` (UUID) | Yes | `uip df entities list` or Orchestrator folder ID |
| `entity_key` | `str` | No | Technical entity identifier |
| `description` | `str` | No | Helps the LLM understand the entity's purpose |

---

## Combining Both Paths

A single agent can use both paths. Use SDK tools for known operations and the DataFabric tool for open-ended exploration:

```python
from langchain_core.tools import tool
from uipath.platform import UiPath
from uipath.platform.entities import DataFabricEntityItem
from uipath_langchain.agent import create_agent
from uipath_langchain.agent.tools import create_datafabric_tool
from uipath_langchain.chat import UiPathChat


# Deterministic tool — known query shape
@tool
async def close_order(order_id: str) -> str:
    """Mark an order as closed. Use when the user asks to close a specific order.

    Args:
        order_id: The record ID of the order.
    """
    sdk = UiPath()
    await sdk.entities.update_record_async(
        entity_key="Orders", record_id=order_id, data={"Status": "Closed"}
    )
    return f"Order {order_id} closed."


def _make_llm():
    """Lazy LLM factory — never call at module level."""
    return UiPathChat(model="gpt-4.1-mini-2025-04-14")


system_prompt = (
    "You are an order management assistant. "
    "Use query_orders for data questions. Use close_order to close orders."
)

llm = _make_llm()
# NL-to-SQL tool — freeform queries
query_tool = create_datafabric_tool(
    llm=llm,
    name="query_orders",
    description="Query order and customer data using natural language.",
    base_system_prompt=system_prompt,
    entities=[
        DataFabricEntityItem(
            id="1312e893-8295-f111-9b33-0022482a9eea",
            name="Orders",
            folder_key="379fec63-62b1-41ec-b2fc-718f8f7dda3c",
        ),
    ],
)

graph = create_agent(llm, tools=[query_tool, close_order], system_prompt=system_prompt)
```

---

## Gotchas

1. **Never instantiate `UiPath()` or `UiPathChat()` at module level** — they read auth credentials at construction time. `uip codedagent init` imports your module to introspect it, and module-level construction will fail. Wrap in a lazy factory function.

2. **For freeform queries, use `create_datafabric_tool` — not a custom solution.** Import it from `uipath_langchain.agent.tools`. Do NOT use `create_datafabric_query_tool` or any other internal function — those are implementation details and may change without notice.

3. **Single vs. batch trigger behavior** — `insert_record` / `update_record` / `delete_record` fire entity triggers. Batch variants (`insert_records`, `update_records`, `delete_records`) do **not**.

4. **SQL query constraints** — `query_entity_records` only accepts SELECT statements. Queries without WHERE must include LIMIT. Subqueries, UNION, WITH, and DML/DDL are forbidden.

5. **Entity schemas resolve lazily** in `create_datafabric_tool` — the first invocation fetches schemas from Data Fabric and caches them. Subsequent calls reuse the cache.

6. **Reserved field names** — `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime` are system fields and cannot be used as user field names.

## Comparison with Low-Code DataFabric Context

Low-code agents use `contextType: "datafabricentityset"` in `resource.json` — see [../../lowcode/capabilities/context/datafabric.md](../../lowcode/capabilities/context/datafabric.md). The coded agent paths above are the programmatic equivalent. The key differences:

| | Low-code | Coded (SDK) | Coded (Tool) |
|-|----------|-------------|--------------|
| Configuration | `resource.json` | Python code | `create_datafabric_tool()` call |
| Query flexibility | NL-to-SQL via built-in tool | Full programmatic control | NL-to-SQL via inner sub-graph |
| Write support | No | Yes (single + batch) | No (read-only SQL) |
| LLM cost per query | Yes | No | Yes |

## References

- [sdk-services.md](sdk-services.md) — Full SDK services reference
- [context-grounding.md](context-grounding.md) — Context Grounding (RAG over documents, separate from Data Fabric)
- [../../lowcode/capabilities/context/datafabric.md](../../lowcode/capabilities/context/datafabric.md) — Low-code DataFabric context
- Sample: `uipath-langchain-python/samples/datafabric-coded-agent/` — Working coded agent example

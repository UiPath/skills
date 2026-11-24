# Ontology Integration for Coded Agents

How to query a deployed UiPath ontology from a coded agent. An ontology describes a business domain as objects, properties and relationships, and maps them to the systems that hold the data. The agent asks in business terms; the Ontology service applies the mapping and reads the data.

Use this page when the agent must answer questions over a deployed ontology. To query Data Fabric entities directly, with no ontology, use [datafabric.md](datafabric.md). This page does not cover authoring or changing an ontology.

## Step 1: Discover the Ontology

The tool needs the ontology's id, which only the tenant returns. Discovery is auth-gated (`uip login status --output json` first). Do auth and discovery before Build, not after. "Scaffold only" does not skip this step: listing ontologies is read-only.

```bash
# List the deployed ontologies in a folder
uip ont list --folder-path "Shared" --output table

# Read one ontology (id, name, state, folder)
uip ont get "<ONTOLOGY_NAME>" --folder-path "Shared" --output json
```

Take from the output:
- **`id`** (UUID): the value for `ontology_id`.
- **`state`**: must be `DEPLOYED`. The tool refuses any other state on its first call.

Show the user the matching ontologies before proceeding. If several ontologies share a name across folders, confirm the folder with the user.

## Step 2: Add the Tool (`create_ontology_tool`)

`create_ontology_tool` is the only supported way to query an ontology from a coded agent. It runs an inner LLM sub-graph that reads the ontology, writes SQL over its business objects, runs the SQL on the Ontology service, and returns the rows.

### Required Import

```python
# This is the ONLY correct import. Do NOT use create_datafabric_ontology_tool
# or any other function from internal submodules.
from uipath_langchain.agent.tools import create_ontology_tool
```

### Usage

```python
from langchain_core.messages import SystemMessage
from uipath_langchain.agent.react.agent import create_agent
from uipath_langchain.agent.tools import create_ontology_tool
from uipath_langchain.chat import UiPathChat


def _make_llm():
    """Lazy LLM factory — never call at module level."""
    return UiPathChat(model="gpt-4.1-mini-2025-04-14")


system_prompt = "Answer questions using only the configured ontology."

llm = _make_llm()
ontology_tool = create_ontology_tool(
    llm=llm,
    name="query_invoice_processing",
    description="Query invoices, suppliers and payments.",
    ontology_id="a1b2c3d4-5678-90ab-cdef-1234567890ab",
    base_system_prompt=system_prompt,
)

graph = create_agent(llm, tools=[ontology_tool], messages=[SystemMessage(system_prompt)])
```

### Key Design Constraint

**The same instruction string must reach both levels: pass it as `messages=[SystemMessage(...)]` to `create_agent` and as `base_system_prompt` to `create_ontology_tool`.** The tool forwards it to the inner SQL-generation sub-graph so the agent's instructions apply at both levels.

### `create_ontology_tool` Signature

```python
def create_ontology_tool(
    *,
    llm: BaseChatModel,        # LLM for the inner SQL generation loop
    name: str,                  # Tool name exposed to the outer agent
    description: str,           # Tool description for agent tool selection
    ontology_id: str,           # Id of the deployed ontology (from Step 1)
    base_system_prompt: str,    # Forwarded to the inner sub-graph
) -> BaseTool
```

### How It Works Internally

1. The agent receives a freeform question and calls the tool with a `user_query` string.
2. On the first call, the tool reads the ontology from the Ontology service and checks it is `DEPLOYED`.
3. The tool grounds the inner LLM on the ontology's objects, properties and relationships (cached after the first call).
4. The inner LLM writes a SQL SELECT over the business objects.
5. The Ontology service maps the statement to the source data and runs it. A rejected statement loops back to the LLM for a bounded retry.
6. The rows return to the outer agent together with the SQL that produced them.

## Gotchas

1. **Never instantiate `UiPath()` or `UiPathChat()` at module level.** They read auth credentials at construction time, and `uip codedagent init` imports the module to introspect it. Wrap them in a lazy factory function.

2. **Use `create_ontology_tool`, not a custom solution.** Do NOT call the Ontology service routes by hand, and do NOT use `create_datafabric_ontology_tool`: that is the low-code adapter and it is feature-flag gated.

3. **The ontology is checked lazily.** A wrong id or an ontology that is not deployed fails the first tool call, not agent start-up or `uip codedagent init`. Run the agent once after wiring the id.

4. **Placeholder ids are a build failure, not a deferral.** Never ship `<ONTOLOGY_ID>` for the user to fill in later. Run Step 1 and paste the discovered id.

5. **One tool queries one ontology.** For several ontologies, create one tool per ontology with a distinct `name` and `description`.

6. **Read-only.** The tool runs SELECT statements only. It does not write records or run ontology operations.

7. **What the source system allows still applies.** A source that cannot count, aggregate or join returns an error for those statements. The inner LLM sees the error and retries, but it cannot answer a question the source cannot serve.

8. **Bindings are not discovered.** `uip codedagent init` does not emit an ontology binding for the id passed to the factory, so the ontology cannot be re-pointed at deploy time yet.

## Comparison with Low-Code Ontology Context

| | Low-code | Coded |
|-|----------|-------|
| Configuration | Ontology context added in Agent Builder (`contextType: "datafabricontology"`) | `create_ontology_tool()` call |
| Ontology reference | Picked in the Agent Builder resource picker | `ontology_id` from `uip ont list` |
| Feature flag | Requires `DataFabricOntologyEnabled` on the tenant | None |
| Query engine | Inner SQL sub-graph on the Ontology service | Same |
| Deploy-time re-pointing | Through the ontology binding | Not yet |

## References

- [datafabric.md](datafabric.md) — Data Fabric entities from coded agents
- [sdk-services.md](sdk-services.md) — Full SDK services reference
- Sample: `uipath-langchain-python/samples/ontology-coded-agent/` — Working coded agent example

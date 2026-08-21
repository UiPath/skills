## Required Agent Structure

**IMPORTANT**: All UiPath coded agents MUST follow this standard structure unless explicitly specified otherwise by the user.

### Required Components

Every agent implementation MUST include these three Pydantic models:

```python
from pydantic import BaseModel

class Input(BaseModel):
    """Define input fields that the agent accepts"""
    # Add your input fields here
    pass

class State(BaseModel):
    """Define the agent's internal state that flows between nodes"""
    # Add your state fields here
    pass

class Output(BaseModel):
    """Define output fields that the agent returns"""
    # Add your output fields here
    pass
```

### Required LLM Initialization

Unless the user explicitly requests a different LLM provider, always use `UiPathChat`:

```python
from uipath_langchain.chat import UiPathChat

llm = UiPathChat(model="gpt-4.1-mini-2025-04-14", temperature=0.7)
```

**Alternative LLMs** (only use if explicitly requested):
- `ChatOpenAI` from `langchain_openai`
- `ChatAnthropic` from `langchain_anthropic`
- Other LangChain-compatible LLMs

### Standard Agent Template

Every agent should follow this basic structure:

```python
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathChat
from pydantic import BaseModel

# 1. Define Input, State, and Output models
class Input(BaseModel):
    field: str

class State(BaseModel):
    field: str
    result: str = ""

class Output(BaseModel):
    result: str

# 2. Initialize UiPathChat LLM
llm = UiPathChat(model="gpt-4.1-mini-2025-04-14", temperature=0.7)

# 3. Define agent nodes (async functions)
async def process_node(state: State) -> State:
    response = await llm.ainvoke([HumanMessage(state.field)])
    return State(field=state.field, result=response.content)

async def output_node(state: State) -> Output:
    return Output(result=state.result)

# 4. Build the graph
builder = StateGraph(State, input=Input, output=Output)
builder.add_node("process", process_node)
builder.add_node("output", output_node)
builder.add_edge(START, "process")
builder.add_edge("process", "output")
builder.add_edge("output", END)

# 5. Compile the graph
graph = builder.compile()
```

**Key Rules**:
1. Always use async/await for all node functions
2. All nodes (except output) must accept and return `State`
3. The final output node must return `Output`
4. Use `StateGraph(State, input=Input, output=Output)` for initialization
5. Always compile with `graph = builder.compile()`

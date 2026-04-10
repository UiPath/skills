# Process and Job Invocation Guide

How to invoke external processes and monitor job execution in LangGraph agents using UiPath automation capabilities.

> **First time here?** Read [Interrupt and Resume Patterns](interrupt-resume.md) for a conceptual overview of how agent pausing and resumption works.

## Overview

**Process Invocation** enables agents to delegate work to external RPA processes, API calls, or other agents, then resume automatically.

## Core Models

1. **InvokeProcess** — Calls external processes and waits for completion
2. **WaitJob** — Monitors already-created job execution

## InvokeProcess

```python
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command
from uipath.platform.common import InvokeProcess

class GraphState(MessagesState):
    request: str
    process_result: dict | None = None

async def invoke_automation(state: GraphState) -> Command:
    process_output = interrupt(InvokeProcess(
        name="MyProcess",
        process_folder_path="MyFolderPath",
        input_arguments={
            "argument1": "value1",
            "argument2": state.get("request")
        }
    ))
    return Command(update={"process_result": process_output})

builder = StateGraph(GraphState)
builder.add_node("invoke", invoke_automation)
builder.add_edge(START, "invoke")
builder.add_edge("invoke", END)
graph = builder.compile()
```

### Parameters

```python
InvokeProcess(
    name="ProcessName",                    # Required: Exact process name in Orchestrator
    process_folder_path="FolderPath",      # Required: Folder path in Orchestrator
    input_arguments={"arg1": "value1"}     # Required: Input arguments dict
)
```

### Return Values

```python
{"status": "success|failed|faulted", "output_argument_1": "result_value", "error": "..."}
```

## WaitJob

Wait for a previously-created job to complete:

```python
from uipath.platform.common import WaitJob

async def wait_for_job(state: GraphState) -> Command:
    job_output = interrupt(WaitJob(job_id=state.get("external_job_id")))
    return Command(update={"job_result": job_output})
```

## Common Patterns

### Conditional Process Invocation

```python
async def conditional_automation(state: GraphState) -> Command:
    if state["request_type"] == "urgent":
        process_name, folder = "UrgentProcess", "SpecialHandling"
    else:
        process_name, folder = "StandardProcess", "StandardWorkflows"

    result = interrupt(InvokeProcess(
        name=process_name,
        process_folder_path=folder,
        input_arguments={"request_data": state["request_data"]}
    ))
    return Command(update={"automation_result": result})
```

### Agent-in-the-Loop

```python
async def delegate_to_process(state: GraphState) -> Command:
    llm = UiPathAzureChatOpenAI()
    analysis = await llm.ainvoke([
        SystemMessage(content="Analyze this request and extract parameters."),
        HumanMessage(content=state["request"])
    ])

    process_result = interrupt(InvokeProcess(
        name="RequestProcessor",
        process_folder_path="AutomationWorkflows",
        input_arguments={"analysis": analysis.content}
    ))

    final_response = await llm.ainvoke(state["messages"] + [
        ToolMessage(content=f"Process result: {process_result}", tool_call_id="process")
    ])
    return Command(update={"response": final_response.content})
```

## Best Practices

- **Atomic Processes**: Keep invoked processes focused on single tasks
- **Input Validation**: Validate arguments before invocation
- **Error Handling**: Handle process failures gracefully with try/except
- **Timeout Management**: Consider process execution time in agent flow
- **Result Validation**: Verify process results before continuing

## Troubleshooting

- **"Process not found"**: Verify process name and `process_folder_path` match Orchestrator exactly
- **"Invalid input arguments"**: Check argument names and types match process expectations
- **Job timeouts**: Check process execution time; consider using WaitJob pattern
- **Output parsing errors**: Verify process return types; add logging for debugging

## Reference

For detailed API documentation, see the [UiPath Process Invocation documentation](https://uipath.github.io/uipath-python/langchain/human_in_the_loop/).
